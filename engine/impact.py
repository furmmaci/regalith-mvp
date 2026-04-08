"""
Rule-based financial impact engine.
Takes a regulation record + company profile, returns a structured ImpactAssessment.
"""

HEADCOUNT_SCALES = {
    "<20": 0.25,
    "20–100": 0.60,
    "100–500": 1.00,
    "500+": 2.80,
}

VOLUME_SCALES = {
    "<1,000 / month": 0.20,
    "1,000–10,000 / month": 0.55,
    "10,000–100,000 / month": 1.00,
    "100,000+ / month": 3.20,
}

# Estimated annual revenue midpoints by headcount band (EUR)
REVENUE_MIDPOINTS = {
    "<20": 2_000_000,
    "20–100": 8_000_000,
    "100–500": 30_000_000,
    "500+": 120_000_000,
}

VARIANCE_LOW = 0.72
VARIANCE_HIGH = 1.38


def calculate_impact(regulation: dict, profile: dict) -> dict | None:
    fm = regulation.get("financial_model", {})
    if not fm:
        return None

    license_type = profile.get("license_type", "")
    applies_to = fm.get("applies_to", [])

    # Check applicability
    if applies_to and license_type not in applies_to:
        return None

    headcount = profile.get("headcount_range", "20–100")
    volume = profile.get("monthly_onboarding_volume", "1,000–10,000 / month")

    hs = HEADCOUNT_SCALES.get(headcount, 0.60)
    vs = VOLUME_SCALES.get(volume, 0.55)

    # Blended operational scale: headcount drives fixed costs, volume drives variable
    operational_scale = hs * 0.65 + vs * 0.35

    # Multipliers
    has_crypto = profile.get("has_crypto", False) and license_type in ("VASP",)
    has_remote = profile.get("has_remote_onboarding", True)

    crypto_mult = fm.get("crypto_multiplier", 1.0) if has_crypto else 1.0
    remote_mult = fm.get("remote_onboarding_multiplier", 1.0) if has_remote else 1.0

    total_mult = operational_scale * crypto_mult * remote_mult

    # --- Annual compliance cost ---
    base_annual = fm.get("base_annual_cost_eur", 50000) * total_mult
    annual_low = round(base_annual * VARIANCE_LOW / 1000) * 1000
    annual_high = round(base_annual * VARIANCE_HIGH / 1000) * 1000

    # --- One-time systems cost ---
    base_systems = fm.get("base_systems_cost_eur", 0) * hs  # volume doesn't scale systems
    systems_low = round(base_systems * VARIANCE_LOW / 1000) * 1000
    systems_high = round(base_systems * VARIANCE_HIGH / 1000) * 1000

    # --- Total first-year cost ---
    total_low = annual_low + systems_low
    total_high = annual_high + systems_high

    # --- Headcount ---
    base_hc = fm.get("base_headcount_fte", 1.0) * hs
    hc_low = max(0, round(base_hc * 0.7 * 10) / 10)
    hc_high = max(1, round(base_hc * 1.5 * 10) / 10)

    # --- EBITDA impact (as % of revenue) ---
    rev = REVENUE_MIDPOINTS.get(headcount, 8_000_000)
    ebitda_low = round(-(total_low / rev) * 100, 1)
    ebitda_high = round(-(total_high / rev) * 100, 1)

    # --- Conversion impact ---
    base_conv = fm.get("conversion_impact_pct", 0.0)
    conv_impact = round(base_conv * (vs ** 0.5), 1)  # diminishing returns at scale

    # --- Confidence ---
    confidence = _confidence(regulation)

    # --- Main mechanisms ---
    mechanisms = _mechanisms(regulation, profile, has_crypto, has_remote)

    # --- Compliance risk tier ---
    score = regulation.get("impact_score", 5.0)
    prob = regulation.get("enforcement_probability", 0.7)
    if score >= 8.0 and prob >= 0.90:
        compliance_risk = "High"
    elif score >= 6.0 or prob >= 0.80:
        compliance_risk = "Medium"
    else:
        compliance_risk = "Low"

    return {
        "annual_cost_low": annual_low,
        "annual_cost_high": annual_high,
        "systems_cost_low": systems_low,
        "systems_cost_high": systems_high,
        "total_first_year_low": total_low,
        "total_first_year_high": total_high,
        "headcount_low": hc_low,
        "headcount_high": hc_high,
        "ebitda_impact_low": ebitda_low,
        "ebitda_impact_high": ebitda_high,
        "conversion_impact_pct": conv_impact,
        "confidence": confidence,
        "compliance_risk": compliance_risk,
        "main_mechanisms": mechanisms,
        "applicable": True,
    }


def _confidence(regulation: dict) -> str:
    score = regulation.get("impact_score", 5.0)
    prob = regulation.get("enforcement_probability", 0.7)
    status = regulation.get("status", "")
    if status in ("In Force",) and prob >= 0.90:
        return "High"
    elif status in ("Enacted",) and prob >= 0.85:
        return "High"
    elif score >= 7.0 and prob >= 0.75:
        return "Medium"
    else:
        return "Low"


def _mechanisms(regulation: dict, profile: dict, has_crypto: bool, has_remote: bool) -> list[str]:
    mechs = []
    topic = regulation.get("topic", "")
    subtopic = regulation.get("subtopic", "")

    if "Onboarding" in subtopic or has_remote:
        mechs.append("Remote onboarding friction & redesign")
    if topic == "AML":
        mechs.append("Compliance headcount expansion")
    if has_crypto:
        mechs.append("Enhanced crypto monitoring & travel rule")
    if "systems_cost_eur" in regulation.get("financial_model", {}):
        base = regulation["financial_model"]["base_systems_cost_eur"]
        if base > 0:
            mechs.append("Systems implementation & vendor costs")
    mechs.append("AML policy, procedure & training uplift")
    if "Third-Party" in subtopic or "Outsourcing" in subtopic:
        mechs.append("Vendor oversight programme")

    return mechs[:4]


def aggregate_portfolio_impact(assessments: list[dict]) -> dict:
    """Sum up impact across all applicable regulations for portfolio-level view."""
    applicable = [a for a in assessments if a and a.get("applicable")]
    if not applicable:
        return {}

    return {
        "total_annual_low": sum(a["annual_cost_low"] for a in applicable),
        "total_annual_high": sum(a["annual_cost_high"] for a in applicable),
        "total_systems_low": sum(a["systems_cost_low"] for a in applicable),
        "total_systems_high": sum(a["systems_cost_high"] for a in applicable),
        "total_first_year_low": sum(a["total_first_year_low"] for a in applicable),
        "total_first_year_high": sum(a["total_first_year_high"] for a in applicable),
        "total_headcount_low": sum(a["headcount_low"] for a in applicable),
        "total_headcount_high": sum(a["headcount_high"] for a in applicable),
        "high_risk_count": sum(1 for a in applicable if a["compliance_risk"] == "High"),
        "applicable_count": len(applicable),
    }
