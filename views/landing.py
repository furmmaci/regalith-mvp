"""
Landing page — shown before the company profile form.
"""

import streamlit as st


_VALUE_PROPS = [
    (
        "◈",
        "Mapped to your operating model",
        "Answer eight questions about your business. Regalith cross-references your licence type, "
        "products, and jurisdictions against every applicable article — no generic checklists.",
    ),
    (
        "⊞",
        "Covers DORA, PSD3 and MiCA end-to-end",
        "Full article-level coverage across the three regulations reshaping EU fintech — "
        "with severity ratings, deadlines, and the exact reason each obligation applies to you.",
    ),
    (
        "⊟",
        "Export a compliance obligations report",
        "Get a structured PDF of every obligation scoped to your company profile — "
        "ready to share with your legal team, auditors, or board.",
    ),
]

_REGS = [
    ("DORA", "Digital Operational Resilience Act", "#3d6af5", "rgba(61,106,245,0.10)"),
    ("PSD3", "Payment Services Directive 3",        "#e8a020", "rgba(232,160,32,0.10)"),
    ("MiCA", "Markets in Crypto-Assets Regulation", "#2db87a", "rgba(45,184,122,0.10)"),
]


def render():
    _, col, _ = st.columns([1, 2.4, 1])

    with col:
        # ── Brand wordmark ─────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center; padding:40px 0 36px 0;">
            <div style="display:inline-flex; align-items:center; gap:10px;
                        border:1px solid #1e2d4a; border-radius:6px;
                        padding:8px 18px; background:#0f1729; margin-bottom:36px;">
                <span style="font-size:18px; color:#3d6af5;">◈</span>
                <div style="text-align:left;">
                    <div style="font-size:13px; font-weight:700; color:#e8edf5;
                                letter-spacing:0.12em; text-transform:uppercase;
                                line-height:1.1;">Regalith</div>
                    <div style="font-size:8px; color:#4a6080; letter-spacing:0.16em;
                                text-transform:uppercase; margin-top:1px;">Regulatory Intelligence</div>
                </div>
            </div>

            <!-- Headline -->
            <h1 style="font-size:28px; font-weight:700; color:#e8edf5;
                       line-height:1.3; margin:0 0 16px 0; letter-spacing:-0.01em;">
                Know exactly which EU regulations<br>apply to your business
                <span style="color:#3d6af5;"> – in minutes.</span>
            </h1>
            <p style="font-size:14px; color:#5a7090; max-width:440px;
                      margin:0 auto 36px auto; line-height:1.7;">
                Purpose-built for fintech operators. Regalith maps DORA, PSD3 and MiCA
                directly onto your operating model and tells you what you actually need to do.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Value propositions ─────────────────────────────────────────────
        for icon, title, body in _VALUE_PROPS:
            st.markdown(f"""
            <div style="display:flex; gap:16px; align-items:flex-start;
                        padding:14px 18px; margin-bottom:8px;
                        background:#0f1729; border:1px solid #1e2d4a;
                        border-radius:6px;">
                <div style="width:32px; height:32px; border-radius:5px;
                            background:#0a1428; border:1px solid #1e2d4a;
                            display:flex; align-items:center; justify-content:center;
                            flex-shrink:0; font-size:15px; color:#3d6af5; margin-top:1px;">
                    {icon}
                </div>
                <div>
                    <div style="font-size:13px; font-weight:600; color:#c8d8e8;
                                margin-bottom:4px;">{title}</div>
                    <div style="font-size:12px; color:#4a6080; line-height:1.6;">{body}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        # ── CTA button ─────────────────────────────────────────────────────
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] + div .stButton > button,
        .rg-landing-cta .stButton > button {
            font-size: 14px !important;
            padding: 14px 28px !important;
            letter-spacing: 0.05em !important;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.button(
            "Analyse my regulatory exposure →",
            use_container_width=True,
            key="landing_cta",
        ):
            st.session_state["view"] = "onboarding"
            st.rerun()

        # ── Regulation badges ──────────────────────────────────────────────
        reg_badges = "".join(
            f"""<div style="flex:1; background:{bg}; border:1px solid {color};
                            border-radius:6px; padding:14px 12px; text-align:center;">
                    <div style="font-size:15px; font-weight:800; color:{color};
                                letter-spacing:0.06em; margin-bottom:4px;">{short}</div>
                    <div style="font-size:9px; color:#4a6080; line-height:1.4;
                                letter-spacing:0.03em;">{full}</div>
                </div>"""
            for short, full, color, bg in _REGS
        )

        st.markdown(f"""
        <div style="display:flex; gap:10px; margin-top:20px;">
            {reg_badges}
        </div>
        <div style="text-align:center; margin-top:20px;
                    font-size:10px; color:#2a3a50; letter-spacing:0.08em;">
            NOT LEGAL ADVICE · FOR INFORMATIONAL PURPOSES ONLY
        </div>
        <div style="height:40px;"></div>
        """, unsafe_allow_html=True)
