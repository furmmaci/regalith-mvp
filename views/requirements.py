import streamlit as st
from engine.mapper import map_profile_summary


_SEVERITY_COLOR = {
    "critical":      ("#e84040", "rgba(232,64,64,0.10)",  "rgba(232,64,64,0.25)"),
    "important":     ("#e8a020", "rgba(232,160,32,0.10)", "rgba(232,160,32,0.25)"),
    "informational": ("#6b8ef5", "rgba(61,106,245,0.08)", "rgba(61,106,245,0.20)"),
}

_REG_COLOR = {
    "DORA": "#3d6af5",
    "MiCA": "#2db87a",
    "PSD3": "#e8a020",
}


def render():
    profile = st.session_state.get("profile", {})
    company = profile.get("company_name", "Your company")

    st.markdown(f"""
    <div class="rg-page-title">Regulatory requirements</div>
    <div class="rg-page-subtitle">{company} — article-level obligation mapping</div>
    """, unsafe_allow_html=True)

    with st.spinner("Mapping profile against regulations…"):
        summary = map_profile_summary(profile)

    records = summary.get("records", [])
    total = summary.get("total", 0)

    if total == 0:
        st.markdown("""
        <div class="detail-section" style="text-align:center; padding:40px;">
            <div style="font-size:14px; color:#4a6080;">
                No applicable regulations found for this profile.<br>
                Try adjusting your company profile settings.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Summary bar ────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    by_reg = summary.get("by_regulation", {})

    metrics = [
        (c1, "Total requirements", str(total), "#e8edf5"),
        (c2, "Critical", str(summary.get("critical", 0)), "#e84040"),
        (c3, "Important", str(summary.get("important", 0)), "#e8a020"),
        (c4, "Informational", str(summary.get("informational", 0)), "#6b8ef5"),
        (c5, "Regulations in scope",
         str(sum(1 for v in by_reg.values() if v > 0)), "#2db87a"),
    ]
    for col, label, val, color in metrics:
        with col:
            st.markdown(f"""
            <div class="rg-kpi">
                <div class="rg-kpi-label">{label}</div>
                <div class="rg-kpi-value" style="color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Filters ────────────────────────────────────────────────────────────
    col_sev, col_reg, col_src, col_search = st.columns([2, 2, 2, 4])
    with col_sev:
        sev_filter = st.selectbox(
            "Severity", ["All", "Critical", "Important", "Informational"],
            label_visibility="visible"
        )
    with col_reg:
        active_regs = ["All"] + [r for r, c in by_reg.items() if c > 0]
        reg_filter = st.selectbox("Regulation", active_regs, label_visibility="visible")
    with col_src:
        src_filter = st.selectbox(
            "Source", ["All", "Curated", "Heuristic"], label_visibility="visible"
        )
    with col_search:
        search = st.text_input(
            "Search", placeholder="Search obligation text, article reference…",
            label_visibility="collapsed"
        )

    # Apply filters
    filtered = records
    if sev_filter != "All":
        filtered = [r for r in filtered if r["severity"] == sev_filter.lower()]
    if reg_filter != "All":
        filtered = [r for r in filtered if r["regulation_id"] == reg_filter]
    if src_filter != "All":
        filtered = [r for r in filtered if r["source"] == src_filter.lower()]
    if search:
        q = search.lower()
        filtered = [r for r in filtered if
                    q in r["article_label"].lower()
                    or q in r["obligation_summary"].lower()
                    or q in r["article_reference"].lower()
                    or q in r["applies_because"].lower()]

    st.markdown(
        f'<div style="font-size:11px; color:#4a6080; margin-bottom:12px;">'
        f'{len(filtered)} requirement{"s" if len(filtered) != 1 else ""} shown</div>',
        unsafe_allow_html=True,
    )

    # ── Requirement cards ──────────────────────────────────────────────────
    for rec in filtered:
        _render_card(rec)


def _render_card(rec: dict):
    sev = rec["severity"]
    color, bg, border = _SEVERITY_COLOR.get(sev, ("#8a9bb8", "rgba(0,0,0,0)", "rgba(0,0,0,0.1)"))
    reg_color = _REG_COLOR.get(rec["regulation_id"], "#5a7090")
    src_badge = (
        '<span class="badge badge-info">curated</span>'
        if rec["source"] == "curated"
        else '<span class="badge badge-neutral">heuristic</span>'
    )
    excerpt = rec.get("article_text_excerpt", "")

    with st.container():
        st.markdown(f"""
        <div style="background:#0f1729; border:1px solid #1e2d4a;
                    border-left: 3px solid {color};
                    border-radius:6px; padding:16px 18px; margin-bottom:8px;">

            <!-- Header row -->
            <div style="display:flex; justify-content:space-between;
                        align-items:flex-start; margin-bottom:10px;">
                <div style="flex:1; padding-right:16px;">
                    <div style="font-size:10px; font-weight:600; color:{reg_color};
                                letter-spacing:0.1em; text-transform:uppercase;
                                margin-bottom:4px;">
                        {rec['regulation_id']} · {rec['article_reference']}
                    </div>
                    <div style="font-size:14px; font-weight:600; color:#e8edf5;
                                line-height:1.4;">
                        {rec['article_label']}
                    </div>
                </div>
                <div style="display:flex; flex-direction:column; align-items:flex-end;
                            gap:4px; flex-shrink:0;">
                    <span style="display:inline-block; font-size:10px; font-weight:700;
                                 letter-spacing:0.08em; text-transform:uppercase;
                                 padding:3px 9px; border-radius:3px;
                                 background:{bg}; color:{color};
                                 border:1px solid {border};">
                        {sev}
                    </span>
                    {src_badge}
                </div>
            </div>

            <!-- ID + Deadline row -->
            <div style="display:flex; gap:20px; font-size:11px; color:#4a6080;
                        margin-bottom:12px;">
                <div><strong style="color:#5a7090;">ID</strong> {rec['requirement_id']}</div>
                <div><strong style="color:#5a7090;">Deadline</strong> {rec['deadline']}</div>
            </div>

            <!-- Obligation -->
            <div style="margin-bottom:10px;">
                <div style="font-size:10px; font-weight:600; color:#4a6080;
                            letter-spacing:0.1em; text-transform:uppercase;
                            margin-bottom:4px;">Obligation</div>
                <div style="font-size:13px; color:#a8bbd0; line-height:1.65;">
                    {rec['obligation_summary']}
                </div>
            </div>

            <!-- Applies because -->
            <div style="background:#0a1220; border:1px solid #1a2840;
                        border-radius:4px; padding:10px 12px;">
                <div style="font-size:10px; font-weight:600; color:#4a6080;
                            letter-spacing:0.1em; text-transform:uppercase;
                            margin-bottom:4px;">Why it applies</div>
                <div style="font-size:12px; color:#7a9ab8; line-height:1.6;
                            font-style:italic;">
                    {rec['applies_because']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # EUR-Lex article text — collapsed by default
        if excerpt:
            with st.expander(f"EUR-Lex source text — {rec['article_reference']}", expanded=False):
                st.markdown(f"""
                <div style="font-size:12px; color:#5a7090; line-height:1.7;
                            font-family: monospace; white-space: pre-wrap;">
{excerpt}{'…' if len(excerpt) >= 400 else ''}
                </div>
                """, unsafe_allow_html=True)
