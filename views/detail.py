import streamlit as st


def render(reg, assessment):
    # ── Back navigation ──────────────────────────────────────────────────
    if st.button("← Back to Developments"):
        st.session_state["view"] = "feed"
        st.rerun()

    urgency = reg.get("urgency", "low")
    badge_class = f"badge-{urgency}"
    status = reg.get("status", "")
    jurisdiction = reg.get("jurisdiction", "")
    source_type = reg.get("source_type", "")
    eff_date = reg.get("effective_date") or "—"
    pub_date = reg.get("publication_date", "—")
    prob = reg.get("enforcement_probability", 0.0)
    impact_score = reg.get("impact_score", 0.0)

    status_class = {
        "In Force": "badge-high",
        "Enacted": "badge-info",
        "Active": "badge-high",
    }.get(status, "badge-neutral")

    applicable = assessment and assessment.get("applicable")
    risk = assessment.get("compliance_risk", "") if applicable else "—"
    risk_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(risk, "badge-neutral")

    # ── Header ───────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="detail-header">
        <div class="detail-title">{reg.get("title","")}</div>
        <div class="detail-meta-row">
            <div class="detail-meta-item"><strong>Source</strong> {reg.get("source_institution","")}</div>
            <div class="detail-meta-item"><strong>Type</strong> {source_type}</div>
            <div class="detail-meta-item"><strong>Published</strong> {pub_date}</div>
            <div class="detail-meta-item"><strong>Effective</strong> {eff_date}</div>
            <div class="detail-meta-item"><strong>Jurisdiction</strong> {jurisdiction}</div>
            <div class="detail-meta-item"><strong>Enf. probability</strong> {int(prob*100)}%</div>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
            <span class="badge {badge_class}">{urgency} urgency</span>
            <span class="badge {status_class}">{status}</span>
            <span class="badge badge-neutral">{reg.get("topic","")}</span>
            <span class="badge badge-neutral">{reg.get("subtopic","")}</span>
            {f'<span class="badge {risk_class}">{risk} compliance risk</span>' if applicable else ''}
            <span style="margin-left:auto; font-size:22px; font-weight:700; color:#e8edf5;">
                {impact_score:.1f}
                <span style="font-size:11px; color:#4a6090; font-weight:400;"> / 10</span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two-column layout ────────────────────────────────────────────────
    col_main, col_side = st.columns([3, 2])

    with col_main:
        # Executive summary
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-section-title">Executive summary</div>
            <div class="detail-text">{reg.get("summary","")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Business impact
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-section-title">Business impact</div>
            <div class="detail-text">{reg.get("business_impact","")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Operational impact
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-section-title">Operational impact</div>
            <div class="detail-text">{reg.get("operational_impact","")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Obligations
        obligations = reg.get("obligations", [])
        if obligations:
            items_html = "".join(
                f'<div class="obligation-item"><div class="obligation-dot"></div><div>{o}</div></div>'
                for o in obligations
            )
            st.markdown(f"""
            <div class="detail-section">
                <div class="detail-section-title">Key obligations</div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

        # Recommendations
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-section-title">Recommended actions</div>
            <div class="detail-text">{reg.get("recommendations","")}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_side:
        # Affected entities
        entities = reg.get("affected_entities", [])
        entity_badges = " ".join(f'<span class="badge badge-info">{e}</span>' for e in entities)
        st.markdown(f"""
        <div class="detail-section">
            <div class="detail-section-title">Affected entity types</div>
            <div style="display:flex; flex-wrap:wrap; gap:6px;">{entity_badges}</div>
        </div>
        """, unsafe_allow_html=True)

        # Financial impact
        if applicable and assessment:
            _render_financial_impact(assessment)
        else:
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">Financial impact</div>
                <div class="detail-text" style="color:#4a6080;">
                    This regulation does not appear applicable to your company profile.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Source link
        source_url = reg.get("source_url", "")
        if source_url:
            st.markdown(f"""
            <div class="detail-section">
                <div class="detail-section-title">Source</div>
                <div style="font-size:12px;">
                    <a href="{source_url}" target="_blank"
                       style="color:#3d6af5; text-decoration:none; word-break:break-all;">
                        {source_url}
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_financial_impact(a: dict):
    def fmt(v):
        if abs(v) >= 1_000_000:
            return f"€{v/1_000_000:.1f}m"
        if abs(v) >= 1_000:
            return f"€{v/1_000:.0f}k"
        return f"€{int(v)}"

    def fmt_pct(v):
        return f"{v:.1f}%"

    annual_low = a.get("annual_cost_low", 0)
    annual_high = a.get("annual_cost_high", 0)
    sys_low = a.get("systems_cost_low", 0)
    sys_high = a.get("systems_cost_high", 0)
    fy_low = a.get("total_first_year_low", 0)
    fy_high = a.get("total_first_year_high", 0)
    hc_low = a.get("headcount_low", 0)
    hc_high = a.get("headcount_high", 0)
    ebitda_low = a.get("ebitda_impact_low", 0)
    ebitda_high = a.get("ebitda_impact_high", 0)
    conv = a.get("conversion_impact_pct", 0)
    confidence = a.get("confidence", "Medium")
    risk = a.get("compliance_risk", "Medium")
    mechanisms = a.get("main_mechanisms", [])

    conf_color = {"High": "#2db87a", "Medium": "#e8a020", "Low": "#5a7090"}.get(confidence, "#e8a020")
    risk_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(risk, "badge-medium")

    rows = [
        ("Annual compliance cost", f"{fmt(annual_low)} – {fmt(annual_high)}", "negative" if annual_low > 100000 else "moderate"),
        ("One-time systems cost", f"{fmt(sys_low)} – {fmt(sys_high)}", "moderate"),
        ("First-year total cost", f"{fmt(fy_low)} – {fmt(fy_high)}", "negative"),
        ("Additional headcount", f"{hc_low:.1f} – {hc_high:.1f} FTE", "moderate"),
        ("EBITDA impact", f"{fmt_pct(ebitda_low)} to {fmt_pct(ebitda_high)}", "negative"),
        ("Conversion impact", f"{fmt_pct(conv)}" if conv < 0 else "Minimal", "moderate" if conv < -1 else ""),
    ]

    rows_html = "".join(
        f'<div class="impact-row">'
        f'<div class="impact-row-label">{label}</div>'
        f'<div class="impact-row-value {cls}">{val}</div>'
        f'</div>'
        for label, val, cls in rows
    )

    mechs_html = "".join(
        f'<div class="obligation-item"><div class="obligation-dot" style="background:#e8a020"></div><div>{m}</div></div>'
        for m in mechanisms
    )

    st.markdown(f"""
    <div class="detail-section">
        <div class="detail-section-title">Financial impact estimate</div>
        {rows_html}
        <div style="display:flex; justify-content:space-between; align-items:center;
                    margin-top:12px; padding-top:10px; border-top:1px solid #1a2640;">
            <div style="font-size:10px; color:#4a6080; text-transform:uppercase; letter-spacing:0.1em;">
                Confidence
            </div>
            <div style="font-size:12px; font-weight:600; color:{conf_color};">{confidence}</div>
        </div>
    </div>
    <div class="detail-section">
        <div class="detail-section-title">Main cost mechanisms</div>
        {mechs_html}
    </div>
    """, unsafe_allow_html=True)
