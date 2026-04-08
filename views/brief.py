import streamlit as st
from datetime import date


def render(regulations, assessments, portfolio):
    profile = st.session_state.get("profile", {})
    company = profile.get("company_name", "Your Company")
    license_type = profile.get("license_type", "")
    today = date.today().strftime("%B %Y")

    annual_low = portfolio.get("total_annual_low", 0)
    annual_high = portfolio.get("total_annual_high", 0)
    fy_low = portfolio.get("total_first_year_low", 0)
    fy_high = portfolio.get("total_first_year_high", 0)
    hc_low = portfolio.get("total_headcount_low", 0)
    hc_high = portfolio.get("total_headcount_high", 0)
    applicable = portfolio.get("applicable_count", 0)
    high_risk = portfolio.get("high_risk_count", 0)

    def fmt(v):
        if abs(v) >= 1_000_000:
            return f"€{v/1_000_000:.1f}m"
        if abs(v) >= 1_000:
            return f"€{v/1_000:.0f}k"
        return f"€{int(v)}"

    # Derive headline
    headline = _generate_headline(profile, portfolio, regulations, assessments)

    st.markdown(f"""
    <div class="brief-header">
        <div class="brief-label">Executive brief</div>
        <div class="brief-title">{company} — Regulatory Impact Summary</div>
        <div class="brief-period">{today} · AML/KYC · EU & Poland · Prepared by Regalith Intelligence</div>
        <div class="brief-headline">{headline}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Portfolio summary metrics ────────────────────────────────────────
    st.markdown('<div class="rg-section-title">Portfolio exposure</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "Applicable regulations", f"{applicable}", "of monitored universe"),
        (c2, "High-risk developments", f"{high_risk}", "require immediate action"),
        (c3, "Est. annual cost", f"{fmt(annual_low)}–{fmt(annual_high)}", "recurring compliance spend"),
        (c4, "First-year total", f"{fmt(fy_low)}–{fmt(fy_high)}", f"incl. {fmt(portfolio.get('total_systems_low',0))}–{fmt(portfolio.get('total_systems_high',0))} implementation"),
    ]
    for col, label, val, sub in metrics:
        with col:
            st.markdown(f"""
            <div class="rg-kpi">
                <div class="rg-kpi-label">{label}</div>
                <div class="rg-kpi-value-sm">{val}</div>
                <div class="rg-kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Priority developments ────────────────────────────────────────────
    st.markdown('<div class="rg-section-title">Priority developments — management attention required</div>',
                unsafe_allow_html=True)

    scored = []
    for reg in regulations:
        a = assessments.get(reg["id"])
        if a and a.get("applicable"):
            score = reg.get("impact_score", 0) * reg.get("enforcement_probability", 0)
            scored.append((score, reg, a))
    scored.sort(key=lambda x: x[0], reverse=True)

    for rank, (score, reg, a) in enumerate(scored[:5], 1):
        urgency = reg.get("urgency", "low")
        risk = a.get("compliance_risk", "Medium")
        border_color = {"High": "#e84040", "Medium": "#e8a020", "Low": "#2db87a"}.get(risk, "#e8a020")
        item_class = {"High": "", "Medium": "medium", "Low": "low"}.get(risk, "medium")

        eff_date = reg.get("effective_date") or "—"
        annual_low_r = a.get("annual_cost_low", 0)
        annual_high_r = a.get("annual_cost_high", 0)
        hc_l = a.get("headcount_low", 0)
        hc_h = a.get("headcount_high", 0)

        cost_str = f"{fmt(annual_low_r)}–{fmt(annual_high_r)} annual" if annual_low_r else ""
        hc_str = f" · {hc_l:.0f}–{hc_h:.0f} FTE" if hc_h > 0 else ""

        desc = _priority_description(reg, a, profile)

        col_content, col_btn = st.columns([5, 1])
        with col_content:
            st.markdown(f"""
            <div class="brief-priority-item {item_class}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div class="brief-priority-title">{rank}. {reg.get("short_title","")} — {reg.get("subtopic","")}</div>
                    <div style="font-size:10px; color:#4a6080; margin-left:12px; flex-shrink:0;">
                        Effective {eff_date}
                    </div>
                </div>
                <div class="brief-priority-desc">{desc}</div>
                {f'<div style="font-size:11px; color:#5a7090; margin-top:6px; font-weight:600;">{cost_str}{hc_str}</div>' if cost_str else ''}
            </div>
            """, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            if st.button("Details →", key=f"brief_btn_{reg['id']}", use_container_width=True):
                st.session_state["view"] = "detail"
                st.session_state["selected_reg_id"] = reg["id"]
                st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Management focus ─────────────────────────────────────────────────
    st.markdown('<div class="rg-section-title">Recommended management focus</div>', unsafe_allow_html=True)

    actions = _management_actions(scored[:3], profile)
    for i, action in enumerate(actions, 1):
        st.markdown(f"""
        <div class="detail-section" style="margin-bottom:8px;">
            <div style="display:flex; gap:12px; align-items:flex-start;">
                <div style="font-size:18px; font-weight:700; color:#3d6af5;
                            min-width:24px; line-height:1.2;">{i}</div>
                <div>
                    <div style="font-size:13px; font-weight:600; color:#e8edf5; margin-bottom:4px;">
                        {action["title"]}
                    </div>
                    <div style="font-size:12px; color:#5a7090; line-height:1.6;">
                        {action["description"]}
                    </div>
                    <div style="margin-top:6px;">
                        <span class="badge badge-info">{action["owner"]}</span>
                        <span style="font-size:10px; color:#4a6080; margin-left:8px;">
                            {action["timing"]}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Footer ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:32px; padding-top:16px; border-top:1px solid #1e2d4a;
                font-size:10px; color:#2a3a50; text-align:center; letter-spacing:0.06em;">
        REGALITH INTELLIGENCE · REGULATORY IMPACT ANALYSIS · RANGES REFLECT MEDIUM CONFIDENCE ESTIMATES
    </div>
    """, unsafe_allow_html=True)


def _generate_headline(profile, portfolio, regulations, assessments) -> str:
    company = profile.get("company_name", "Your company")
    license_type = profile.get("license_type", "")
    applicable = portfolio.get("applicable_count", 0)
    high_risk = portfolio.get("high_risk_count", 0)
    annual_low = portfolio.get("total_annual_low", 0)
    annual_high = portfolio.get("total_annual_high", 0)

    def fmt(v):
        if v >= 1_000_000:
            return f"€{v/1_000_000:.1f}m"
        if v >= 1_000:
            return f"€{v/1_000:.0f}k"
        return f"€{int(v)}"

    if applicable == 0:
        return f"No material regulatory developments applicable to {company}'s current operating model were identified in this monitoring cycle."

    urgency_note = (
        f" {high_risk} development{'s require' if high_risk > 1 else ' requires'} immediate management attention."
        if high_risk > 0 else ""
    )

    return (
        f"{company} ({license_type}) is exposed to {applicable} applicable regulatory developments "
        f"in the current AML/KYC monitoring cycle. Estimated recurring annual compliance cost "
        f"impact ranges from {fmt(annual_low)} to {fmt(annual_high)} under a medium confidence scenario.{urgency_note} "
        f"The primary drivers are the EU AML legislative package (AMLR, AMLD6) and associated "
        f"supervisory expectations from EBA and KNF."
    )


def _priority_description(reg, assessment, profile) -> str:
    topic = reg.get("topic", "")
    subtopic = reg.get("subtopic", "")
    urgency = reg.get("urgency", "medium")
    risk = assessment.get("compliance_risk", "Medium")
    eff = reg.get("effective_date") or "a defined deadline"

    templates = {
        ("AML", "Customer Due Diligence"): (
            f"Introduces enhanced CDD and transaction monitoring obligations with direct application "
            f"from {eff}. Onboarding workflow redesign and compliance headcount expansion are likely required."
        ),
        ("AML", "Supervisory Framework"): (
            f"Upgrades supervisory governance expectations with effect from {eff}. "
            f"Internal AML governance structures and MLRO reporting must be formalised."
        ),
        ("AML", "Supervisory Authority"): (
            f"Establishes EU-level AML supervisory authority with binding technical standard issuance. "
            f"Cross-border fintechs should monitor scope thresholds for direct supervision."
        ),
        ("AML", "Crypto Asset Transfers"): (
            f"Mandates travel rule compliance for all crypto asset transfers. "
            f"A travel rule solution and unhosted wallet procedures are required immediately."
        ),
        ("AML", "Crypto Asset Services"): (
            f"Requires full CASP authorisation and AML programme equivalent to EMI standards by {eff}. "
            f"Unlicensed crypto operations must be remediated."
        ),
        ("KYC", "Risk Assessment"): (
            f"Requires documented customer risk scoring methodology aligned with EBA standards. "
            f"Supervisory inspections assess compliance with these guidelines."
        ),
        ("KYC", "Digital Identity & Onboarding"): (
            f"Sets technical standards for remote onboarding solutions. Vendor validation and "
            f"performance monitoring are mandatory for digital-first firms."
        ),
        ("AML", "Supervisory Enforcement"): (
            f"KNF has identified transaction monitoring and sanctions screening as 2025 inspection priorities. "
            f"Internal health check against these areas is recommended before mid-year."
        ),
        ("AML", "National Transposition"): (
            f"Updated Polish AML Act requirements are in force. AML policy, PEP screening, "
            f"and UBO verification procedures must reflect the 2023 amendments."
        ),
        ("KYC", "Third-Party Risk"): (
            f"Formalises oversight requirements for outsourced KYC/AML vendors. "
            f"Vendor contracts and performance monitoring programmes require review."
        ),
    }

    key = (topic, subtopic)
    return templates.get(key, (
        f"This development carries {risk.lower()} compliance risk and is effective {eff}. "
        f"Review against current operating model and assess remediation requirements."
    ))


def _management_actions(top_scored, profile) -> list[dict]:
    actions = []
    has_crypto = profile.get("has_crypto", False)
    has_remote = profile.get("has_remote_onboarding", True)

    actions.append({
        "title": "Initiate AMLR/AMLD6 gap analysis",
        "description": (
            "Commission a structured gap analysis against the EU AML legislative package "
            "(AMLR 2024/1624 and AMLD6 2024/1640) obligations. Prioritise onboarding workflow, "
            "transaction monitoring, and UBO verification. Effective date: July 2027 — "
            "remediation timelines require action by end of 2025."
        ),
        "owner": "Head of Compliance / MLRO",
        "timing": "Within 60 days",
    })

    if has_remote:
        actions.append({
            "title": "Validate remote onboarding solution against EBA standards",
            "description": (
                "Assess current digital identity verification solution against EBA/GL/2022/15 "
                "technical requirements. Request vendor compliance attestation. Implement "
                "performance monitoring for false acceptance and rejection rates. "
                "Review onboarding audit trail completeness."
            ),
            "owner": "Product / Compliance",
            "timing": "Within 45 days",
        })

    if has_crypto:
        actions.append({
            "title": "Implement travel rule compliance",
            "description": (
                "Select and integrate a travel rule compliance solution to meet TFR (EU) 2023/1113 "
                "requirements. Implement unhosted wallet risk procedures. Review crypto transfer "
                "product terms of service. Deadline: December 2024 — immediate action required."
            ),
            "owner": "CTO / Compliance",
            "timing": "Immediate",
        })
    else:
        actions.append({
            "title": "KNF inspection readiness review",
            "description": (
                "Conduct an internal AML health check against KNF 2025 supervisory priorities: "
                "transaction monitoring adequacy, sanctions screening coverage and refresh rates, "
                "and remote onboarding controls. Document findings and remediation plan for "
                "potential KNF review."
            ),
            "owner": "MLRO / Internal Audit",
            "timing": "Within 30 days",
        })

    if len(actions) < 3:
        actions.append({
            "title": "Update AML training programme",
            "description": (
                "Refresh AML/KYC staff training to reflect AMLD6 governance requirements and "
                "2023 Polish AML Act amendments. Ensure documented evidence of training completion "
                "is maintained for supervisory review."
            ),
            "owner": "Compliance / HR",
            "timing": "Within 90 days",
        })

    return actions[:4]
