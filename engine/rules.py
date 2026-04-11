"""
Curated article rules for DORA, MiCA, and PSD3.

Each ArticleRule is self-contained: it carries pre-written obligation_summary,
deadline, severity, an applicability condition, and a template for applies_because.
Rules work independently of fetched EUR-Lex data — fetched text is supplementary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

Severity = Literal["critical", "important", "informational"]


@dataclass
class ArticleRule:
    regulation_id: str          # DORA | MiCA | PSD3
    article_number: int
    article_label: str          # e.g. "Article 5 — Governance and organisation"
    obligation_summary: str     # ≤ 2 sentences; what the entity must do
    deadline: str
    severity: Severity
    applies_because: Callable[[dict], str]   # receives profile → returns 1 sentence
    condition: Callable[[dict], bool] | None = None  # None = applies to all in-scope entities


# ── Profile helpers ────────────────────────────────────────────────────────

def _lt(p: dict) -> str:
    return p.get("license_type", "regulated entity")

def _name(p: dict) -> str:
    return p.get("company_name", "Your company")

def _is_large(p: dict) -> bool:
    return p.get("headcount_range", "") in ("100–500", "500+")

def _is_outsourced(p: dict) -> bool:
    return p.get("kyc_aml_function", "") in ("Outsourced to vendor", "Hybrid")

def _has_remote(p: dict) -> bool:
    return p.get("has_remote_onboarding", False)

def _has_crypto(p: dict) -> bool:
    return p.get("has_crypto", False) or p.get("license_type", "") == "VASP"

def _has_retail(p: dict) -> bool:
    return "Retail B2C" in p.get("customer_segments", [])

def _has_trading(p: dict) -> bool:
    products = p.get("products", [])
    return any(x in products for x in ("Crypto exchange", "Payment gateway"))

def _has_custody(p: dict) -> bool:
    return "Crypto custody" in p.get("products", [])

def _has_payments(p: dict) -> bool:
    products = p.get("products", [])
    return any(x in products for x in (
        "E-wallet", "Card issuing", "Remittance / FX",
        "Payment gateway", "Open banking"
    ))


# ── DORA rules ─────────────────────────────────────────────────────────────

DORA_RULES: list[ArticleRule] = [
    ArticleRule(
        regulation_id="DORA",
        article_number=5,
        article_label="Article 5 — ICT risk management: governance and organisation",
        obligation_summary=(
            "The management body must define, approve, oversee, and bear responsibility for "
            "the entity's ICT risk management framework. At least one member of the management "
            "body must maintain sufficient knowledge of ICT risk to assess and monitor it effectively."
        ),
        deadline="17 January 2025",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} holds a {_lt(p)} licence, qualifying it as a financial "
            f"entity under DORA Article 2, and board-level ICT risk ownership is mandatory for all in-scope firms."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=6,
        article_label="Article 6 — ICT risk management framework",
        obligation_summary=(
            "Financial entities must implement a robust, documented, and board-approved ICT risk "
            "management framework covering identification, protection, detection, response, and recovery. "
            "The framework must be reviewed at least annually and after major ICT incidents."
        ),
        deadline="17 January 2025",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} is a {_lt(p)} and must establish an ICT risk management "
            f"framework meeting DORA's minimum requirements prior to the January 2025 application date."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=7,
        article_label="Article 7 — ICT systems, protocols and tools",
        obligation_summary=(
            "Entities must use ICT systems, protocols, and tools that are appropriate to the scale of "
            "their operations and proportionate to their ICT risk exposure. Systems must be sufficiently "
            "resilient to withstand operational stress and ICT incidents."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)}'s ICT infrastructure supporting {_lt(p)} services must meet "
            f"DORA's minimum standards for system resilience and operational continuity."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=8,
        article_label="Article 8 — Identification of ICT risks",
        obligation_summary=(
            "Entities must identify, classify, and document all ICT assets, functions, and third-party "
            "dependencies, and maintain an up-to-date inventory of ICT assets supporting critical functions. "
            "Risk assessments must be conducted at least annually."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must map all ICT assets and dependencies underpinning its "
            f"{_lt(p)} operations, including any third-party platforms and cloud services."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=9,
        article_label="Article 9 — Protection and prevention",
        obligation_summary=(
            "Entities must implement protection and prevention measures to minimise ICT risk, including "
            "access controls, patch management, data encryption, and network segmentation. "
            "Policies must be documented and tested regularly."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)}'s {_lt(p)} operations involve customer data and financial "
            f"transactions requiring protection measures proportionate to the firm's ICT risk profile."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=10,
        article_label="Article 10 — Detection of anomalous activity",
        obligation_summary=(
            "Entities must implement mechanisms to promptly detect anomalous activities including ICT "
            "incidents, and must allocate adequate resources and capabilities to monitor ICT systems "
            "and identify potential vulnerabilities."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must have continuous monitoring capability across its "
            f"ICT environment to detect incidents affecting {_lt(p)} service continuity."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=11,
        article_label="Article 11 — Response and recovery",
        obligation_summary=(
            "Entities must have documented ICT business continuity and disaster recovery plans, including "
            "defined recovery time and recovery point objectives. Plans must be tested at least annually "
            "and after major ICT-related incidents."
        ),
        deadline="17 January 2025",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must maintain documented and tested continuity plans covering "
            f"its critical {_lt(p)} operations, with defined RTOs and RPOs."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=12,
        article_label="Article 12 — Backup policies and restoration",
        obligation_summary=(
            "Entities must implement backup policies and procedures ensuring that ICT systems and data "
            "can be restored within defined timeframes. Backup integrity must be tested regularly, "
            "and backup systems must be logically or physically isolated from production."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)}'s {_lt(p)} systems and customer data must be protected "
            f"by tested backup and restoration capabilities meeting DORA's minimum standards."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=17,
        article_label="Article 17 — ICT-related incident management process",
        obligation_summary=(
            "Entities must establish and maintain a documented ICT incident management process covering "
            "detection, classification, containment, resolution, and post-incident review. "
            "A dedicated incident management function or role must be assigned."
        ),
        deadline="17 January 2025",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must have a formal incident management process in place "
            f"before the DORA application date, covering all ICT systems supporting {_lt(p)} services."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=18,
        article_label="Article 18 — Classification of ICT-related incidents",
        obligation_summary=(
            "Entities must classify ICT incidents using defined criteria including client impact, "
            "data loss, service duration, and geographic spread. A documented classification methodology "
            "must be maintained and applied consistently."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must apply DORA's incident classification criteria to "
            f"distinguish between major and non-major incidents affecting its {_lt(p)} services."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=19,
        article_label="Article 19 — Reporting of major ICT-related incidents",
        obligation_summary=(
            "Entities must report major ICT incidents to competent authorities via initial notification "
            "(within 4 hours of classification), an intermediate report, and a final report. "
            "Significant cyber threats must also be notified on a voluntary basis."
        ),
        deadline="17 January 2025",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} as a {_lt(p)} must have regulatory incident reporting "
            f"workflows in place, including defined escalation paths to the competent authority."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=24,
        article_label="Article 24 — General digital operational resilience testing",
        obligation_summary=(
            "Entities must conduct regular ICT resilience testing, including vulnerability assessments, "
            "network security tests, and scenario-based testing proportionate to their risk profile. "
            "Testing programmes must be reviewed at least annually."
        ),
        deadline="17 January 2025",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must establish a testing programme covering its critical "
            f"ICT systems, scaled appropriately to the size and complexity of its {_lt(p)} operations."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=26,
        article_label="Article 26 — Advanced testing: threat-led penetration testing (TLPT)",
        obligation_summary=(
            "Significant financial entities must conduct threat-led penetration testing (TLPT) "
            "every three years, using approved external testers. TLPT results must be shared with "
            "competent authorities."
        ),
        deadline="17 January 2025",
        severity="important",
        condition=_is_large,
        applies_because=lambda p: (
            f"Applies because {_name(p)}'s scale ({p.get('headcount_range','')}) may qualify it "
            f"as a significant entity under DORA, triggering mandatory TLPT obligations."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=28,
        article_label="Article 28 — General principles on ICT third-party risk management",
        obligation_summary=(
            "Entities must manage ICT third-party risk as an integral part of their ICT risk framework, "
            "maintaining a register of all ICT third-party service providers and assessing concentration risk. "
            "Contractual arrangements with providers must meet DORA's minimum requirements."
        ),
        deadline="17 January 2025",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} uses third-party ICT services — including "
            f"{'outsourced KYC/AML vendors and ' if _is_outsourced(p) else ''}cloud or SaaS platforms "
            f"— triggering DORA's third-party risk management obligations."
        ),
    ),
    ArticleRule(
        regulation_id="DORA",
        article_number=30,
        article_label="Article 30 — Key contractual provisions for ICT third-party agreements",
        obligation_summary=(
            "Contracts with ICT third-party service providers must include minimum provisions covering "
            "service level definitions, audit rights, data security standards, incident notification "
            "obligations, and exit provisions. Existing contracts must be reviewed for compliance."
        ),
        deadline="17 January 2025",
        severity="important",
        condition=_is_outsourced,
        applies_because=lambda p: (
            f"Applies because {_name(p)} has outsourced ICT functions ({p.get('kyc_aml_function','')}) "
            f"and must ensure all vendor contracts include DORA's mandatory contractual provisions."
        ),
    ),
]


# ── MiCA rules ─────────────────────────────────────────────────────────────

MICA_RULES: list[ArticleRule] = [
    ArticleRule(
        regulation_id="MiCA",
        article_number=59,
        article_label="Article 59 — Authorisation as a crypto-asset service provider",
        obligation_summary=(
            "Persons intending to provide crypto-asset services in the EU must be authorised as a CASP "
            "by their home member state competent authority prior to commencing services. "
            "Providing services without authorisation constitutes a regulatory breach."
        ),
        deadline="30 December 2024",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} offers crypto-asset services "
            f"({', '.join(p.get('products', [])[:2]) or 'crypto products'}) "
            f"and must hold a valid CASP authorisation under MiCA before operating in the EU."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=60,
        article_label="Article 60 — Application for authorisation as a CASP",
        obligation_summary=(
            "CASP applicants must submit a complete application to their competent authority including "
            "programme of operations, governance arrangements, capital proof, and ICT security policies. "
            "The competent authority must decide within 40 working days of a complete application."
        ),
        deadline="30 December 2024",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must file a complete CASP authorisation application, "
            f"and the application timeline means preparation should have commenced before Q3 2024."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=63,
        article_label="Article 63 — Governance and fit-and-proper requirements",
        obligation_summary=(
            "CASPs must have robust governance arrangements including clearly defined lines of responsibility, "
            "effective risk management, and internal control mechanisms. All members of the management "
            "body must meet fit-and-proper requirements assessed by the competent authority."
        ),
        deadline="30 December 2024",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)}'s management body members must demonstrate the requisite "
            f"knowledge, skills, and experience to manage a CASP providing "
            f"{', '.join(p.get('products', [])[:2]) or 'crypto-asset services'}."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=67,
        article_label="Article 67 — Minimum capital requirements for CASPs",
        obligation_summary=(
            "CASPs must maintain minimum own funds at all times, calibrated by service type: "
            "€50,000 for basic services, €125,000 for exchange or order execution, and €150,000 "
            "for custody services. Capital must be in the form of Common Equity Tier 1 instruments."
        ),
        deadline="30 December 2024",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} must maintain minimum own funds calibrated to the "
            f"specific crypto-asset services it provides, requiring capital planning before authorisation."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=70,
        article_label="Article 70 — Complaints handling",
        obligation_summary=(
            "CASPs must establish and maintain effective and transparent procedures for the prompt "
            "handling of client complaints, free of charge. Complaints must be responded to within "
            "15 business days, with a further 35 days for complex cases."
        ),
        deadline="30 December 2024",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} serves {', '.join(p.get('customer_segments', ['clients']))} "
            f"and must implement a MiCA-compliant complaints procedure covering its crypto-asset services."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=71,
        article_label="Article 71 — Conflicts of interest",
        obligation_summary=(
            "CASPs must identify, manage, and disclose conflicts of interest that may arise between "
            "the CASP, its management, shareholders, clients, and linked parties. "
            "A written conflicts of interest policy must be maintained and reviewed annually."
        ),
        deadline="30 December 2024",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} as a CASP must maintain a documented conflicts of interest "
            f"policy covering its management structure and the crypto-asset services it offers."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=72,
        article_label="Article 72 — Outsourcing of operational functions",
        obligation_summary=(
            "CASPs may outsource operational functions but remain fully responsible for compliance. "
            "Outsourcing must not impair governance, supervisory access, or service quality, "
            "and critical functions may not be outsourced in a way that impairs CASP operations."
        ),
        deadline="30 December 2024",
        severity="important",
        condition=_is_outsourced,
        applies_because=lambda p: (
            f"Applies because {_name(p)} outsources its {p.get('kyc_aml_function','KYC/AML')} function "
            f"and must ensure the arrangement meets MiCA's outsourcing requirements."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=75,
        article_label="Article 75 — Custody and administration of crypto-assets",
        obligation_summary=(
            "CASPs providing custody must segregate client crypto-assets from their own assets, "
            "maintain detailed records of each client's holdings, and implement security policies "
            "to prevent loss, theft, or misuse. Liability for loss is strict."
        ),
        deadline="30 December 2024",
        severity="critical",
        condition=_has_custody,
        applies_because=lambda p: (
            f"Applies because {_name(p)} provides crypto custody services, requiring strict "
            f"asset segregation and security measures under MiCA Article 75."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=76,
        article_label="Article 76 — Operation of a trading platform for crypto-assets",
        obligation_summary=(
            "CASPs operating trading platforms must adopt non-discriminatory rules for participation, "
            "implement market surveillance mechanisms, ensure fair and orderly trading, "
            "and publish pre- and post-trade data as specified by ESMA."
        ),
        deadline="30 December 2024",
        severity="important",
        condition=_has_trading,
        applies_because=lambda p: (
            f"Applies because {_name(p)} operates a crypto exchange or trading platform, "
            f"triggering MiCA's specific operating requirements for trading venues."
        ),
    ),
    ArticleRule(
        regulation_id="MiCA",
        article_number=92,
        article_label="Article 92 — Prohibition of market manipulation",
        obligation_summary=(
            "CASPs must not engage in or facilitate market manipulation of crypto-assets, including "
            "wash trading, spoofing, or dissemination of false information. "
            "Surveillance systems must detect and report suspected manipulation to competent authorities."
        ),
        deadline="30 December 2024",
        severity="critical",
        applies_because=lambda p: (
            f"Applies because {_name(p)} provides crypto-asset services and must implement "
            f"market surveillance controls to detect and prevent prohibited manipulation practices."
        ),
    ),
]


# ── PSD3 rules ─────────────────────────────────────────────────────────────

_PSD3_NOTE = " Note: PSD3 is at proposal stage — requirements may change before transposition."

PSD3_RULES: list[ArticleRule] = [
    ArticleRule(
        regulation_id="PSD3",
        article_number=8,
        article_label="Article 8 — Authorisation as a payment institution",
        obligation_summary=(
            "Payment institutions must obtain or renew authorisation under PSD3, which introduces "
            "revised capital, governance, and operational requirements compared to PSD2." + _PSD3_NOTE
        ),
        deadline="TBD — expected 2027",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} holds a {_lt(p)} licence and must assess whether "
            f"its current authorisation will require re-confirmation or upgrade under PSD3."
        ),
    ),
    ArticleRule(
        regulation_id="PSD3",
        article_number=45,
        article_label="Article 45 — Strong customer authentication (SCA)",
        obligation_summary=(
            "PSD3 retains and strengthens SCA requirements for electronic payment transactions, "
            "with revised exemptions and new requirements for authentication factor resilience. "
            "Payment service providers must implement updated SCA logic before the transposition deadline." + _PSD3_NOTE
        ),
        deadline="TBD — expected 2027",
        severity="critical",
        condition=_has_payments,
        applies_because=lambda p: (
            f"Applies because {_name(p)} processes electronic payments "
            f"({'with remote onboarding' if _has_remote(p) else 'for customers'}) "
            f"requiring SCA for each transaction under the revised PSD3 framework."
        ),
    ),
    ArticleRule(
        regulation_id="PSD3",
        article_number=50,
        article_label="Article 50 — Open banking and access to payment account data",
        obligation_summary=(
            "Account servicing payment service providers must provide open banking access "
            "to authorised third-party providers via a dedicated interface, with improved "
            "API performance standards and reduced grounds for blocking access." + _PSD3_NOTE
        ),
        deadline="TBD — expected 2027",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} as a {_lt(p)} must maintain or prepare for "
            f"open banking API obligations under PSD3's updated access-to-account framework."
        ),
    ),
    ArticleRule(
        regulation_id="PSD3",
        article_number=58,
        article_label="Article 58 — Liability for unauthorised payment transactions",
        obligation_summary=(
            "PSD3 revises the liability framework for unauthorised transactions, including "
            "clearer rules on liability where SCA was not applied and new provisions "
            "for authorised push payment (APP) fraud refund obligations." + _PSD3_NOTE
        ),
        deadline="TBD — expected 2027",
        severity="important",
        condition=_has_retail,
        applies_because=lambda p: (
            f"Applies because {_name(p)} serves retail consumers and will face revised "
            f"liability rules for unauthorised and fraudulently induced payment transactions under PSD3."
        ),
    ),
    ArticleRule(
        regulation_id="PSD3",
        article_number=85,
        article_label="Article 85 — Fraud reporting and data sharing",
        obligation_summary=(
            "Payment service providers must report fraud data to competent authorities and "
            "participate in fraud data-sharing schemes to support industry-wide detection. "
            "Minimum data fields and reporting formats will be specified by EBA." + _PSD3_NOTE
        ),
        deadline="TBD — expected 2027",
        severity="important",
        applies_because=lambda p: (
            f"Applies because {_name(p)} processes payment transactions and must contribute "
            f"to fraud reporting infrastructure under PSD3's updated data-sharing framework."
        ),
    ),
]


# ── Registry ────────────────────────────────────────────────────────────────

ALL_RULES: list[ArticleRule] = DORA_RULES + MICA_RULES + PSD3_RULES

# Regulation-level scope filters
REGULATION_SCOPE: dict[str, Callable[[dict], bool]] = {
    "DORA": lambda p: p.get("license_type") in ("EMI", "PI", "Bank", "Lending"),
    "MiCA": lambda p: (
        p.get("license_type") == "VASP" or p.get("has_crypto", False)
    ),
    "PSD3": lambda p: p.get("license_type") in ("EMI", "PI", "Bank"),
}

# Human-readable names
REGULATION_NAMES: dict[str, str] = {
    "DORA": "Digital Operational Resilience Act (DORA)",
    "MiCA": "Markets in Crypto-Assets Regulation (MiCA)",
    "PSD3": "Payment Services Directive 3 (PSD3 — proposal)",
}

# Keyword patterns for heuristic matching of non-curated articles
HEURISTIC_KEYWORDS: dict[str, list[str]] = {
    "remote_onboarding": [
        "remote", "non-face-to-face", "digital onboarding",
        "electronic identification", "online verification",
    ],
    "crypto_in_scope": [
        "crypto-asset", "virtual asset", "distributed ledger",
        "blockchain", "digital asset",
    ],
    "outsourced": [
        "outsourc", "third-party service provider", "cloud service",
        "subcontract",
    ],
    "retail": [
        "retail client", "consumer", "natural person", "end user",
    ],
    "payments": [
        "payment transaction", "fund transfer", "payment service",
        "electronic payment",
    ],
}
