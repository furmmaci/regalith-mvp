import streamlit as st


def render(regulations, assessments):
    st.markdown("""
    <div class="rg-page-title">Regulatory developments</div>
    <div class="rg-page-subtitle">AML/KYC monitoring — EU & Poland</div>
    """, unsafe_allow_html=True)

    # ── Filters ──────────────────────────────────────────────────────────
    col_search, col_topic, col_jur, col_urgency = st.columns([3, 2, 2, 2])

    with col_search:
        search = st.text_input("Search", placeholder="Search title, institution, subtopic…", label_visibility="collapsed")
    with col_topic:
        topics = ["All"] + sorted(set(r.get("topic", "") for r in regulations))
        topic_filter = st.selectbox("Topic", topics, label_visibility="visible")
    with col_jur:
        juris = ["All"] + sorted(set(r.get("jurisdiction", "") for r in regulations))
        jur_filter = st.selectbox("Jurisdiction", juris, label_visibility="visible")
    with col_urgency:
        urgency_filter = st.selectbox("Urgency", ["All", "High", "Medium", "Low"], label_visibility="visible")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Apply filters ────────────────────────────────────────────────────
    filtered = regulations
    if search:
        q = search.lower()
        filtered = [r for r in filtered if
                    q in r.get("title", "").lower() or
                    q in r.get("source_institution", "").lower() or
                    q in r.get("subtopic", "").lower() or
                    q in r.get("summary", "").lower()]
    if topic_filter != "All":
        filtered = [r for r in filtered if r.get("topic") == topic_filter]
    if jur_filter != "All":
        filtered = [r for r in filtered if r.get("jurisdiction") == jur_filter]
    if urgency_filter != "All":
        filtered = [r for r in filtered if r.get("urgency", "").lower() == urgency_filter.lower()]

    # Sort: high urgency + high impact first
    filtered.sort(key=lambda r: (
        {"high": 2, "medium": 1, "low": 0}.get(r.get("urgency", "low"), 0),
        r.get("impact_score", 0)
    ), reverse=True)

    st.markdown(f'<div style="font-size:11px; color:#4a6080; margin-bottom:12px;">'
                f'{len(filtered)} development{"s" if len(filtered) != 1 else ""} shown</div>',
                unsafe_allow_html=True)

    # ── Cards ────────────────────────────────────────────────────────────
    for reg in filtered:
        _render_card(reg, assessments.get(reg["id"]))


def _render_card(reg, assessment):
    urgency = reg.get("urgency", "low")
    badge_class = f"badge-{urgency}"
    source_type = reg.get("source_type", "")
    status = reg.get("status", "")
    jurisdiction = reg.get("jurisdiction", "")
    impact_score = reg.get("impact_score", 0.0)
    eff_date = reg.get("effective_date") or reg.get("publication_date", "—")

    status_class = {
        "In Force": "badge-high",
        "Enacted": "badge-info",
        "Active": "badge-high",
        "Draft": "badge-neutral",
        "Consultation": "badge-neutral",
    }.get(status, "badge-neutral")

    applicable = assessment and assessment.get("applicable")
    risk = assessment.get("compliance_risk", "") if applicable else ""
    risk_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(risk, "")

    bar_width = int(impact_score * 10)
    bar_color = "impact-bar-red" if impact_score >= 7.5 else ("impact-bar-amber" if impact_score >= 5 else "impact-bar-green")

    summary_snippet = reg.get("summary", "")[:180] + "…"

    # Card HTML
    col_card, col_btn = st.columns([5, 1])
    with col_card:
        st.markdown(f"""
        <div class="dev-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div class="dev-card-title" style="flex:1; padding-right:16px;">
                    {reg.get("title", "")}
                </div>
                <div style="text-align:right; flex-shrink:0;">
                    <div style="font-size:11px; color:#4a6080;">Impact score</div>
                    <div style="font-size:18px; font-weight:700; color:#e8edf5;">{impact_score:.1f}</div>
                </div>
            </div>
            <div class="dev-card-meta">
                {reg.get("source_institution", "")} ·
                Effective {eff_date} ·
                {jurisdiction}
            </div>
            <div class="dev-card-summary">{summary_snippet}</div>
            <div class="dev-card-badges">
                <span class="badge {badge_class}">{urgency}</span>
                <span class="badge {status_class}">{status}</span>
                <span class="badge badge-neutral">{source_type}</span>
                {f'<span class="badge {risk_class}">{risk} risk</span>' if applicable and risk else ''}
                {f'<span class="badge badge-neutral">{reg.get("subtopic","")}</span>' if reg.get("subtopic") else ''}
            </div>
            <div class="impact-bar-wrap">
                <div class="impact-bar-fill {bar_color}" style="width:{bar_width}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_btn:
        st.markdown("<div style='height:52px'></div>", unsafe_allow_html=True)
        if st.button("Details →", key=f"feed_{reg['id']}", use_container_width=True):
            st.session_state["view"] = "detail"
            st.session_state["selected_reg_id"] = reg["id"]
            st.rerun()
