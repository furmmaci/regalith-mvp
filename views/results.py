"""
Post-onboarding results dashboard.
Shown immediately after profile submission (step 2 of 2).
"""

from __future__ import annotations

import json

import streamlit as st

from engine.mapper import map_profile_summary


_SEV_COLOR = {
    "critical":      ("#e84040", "rgba(232,64,64,0.12)",  "rgba(232,64,64,0.28)"),
    "important":     ("#e8a020", "rgba(232,160,32,0.12)", "rgba(232,160,32,0.28)"),
    "informational": ("#6b8ef5", "rgba(61,106,245,0.10)", "rgba(61,106,245,0.24)"),
}
_REG_COLOR = {"DORA": "#3d6af5", "MiCA": "#2db87a", "PSD3": "#e8a020"}


# ── Cache mapping by profile (avoids recompute on filter change) ───────────
@st.cache_data(show_spinner=False)
def _get_summary(profile_json: str) -> dict:
    return map_profile_summary(json.loads(profile_json))


def render():
    profile  = st.session_state.get("profile", {})
    company  = profile.get("company_name", "Your company")
    lt       = profile.get("license_type", "")

    # ── Compute mappings ───────────────────────────────────────────────────
    with st.spinner("Mapping obligations…"):
        profile_json = json.dumps(profile, sort_keys=True)
        summary = _get_summary(profile_json)

    records  = summary.get("records", [])
    total    = summary.get("total", 0)
    critical = summary.get("critical", 0)
    important= summary.get("important", 0)
    info     = summary.get("informational", 0)
    by_reg   = summary.get("by_regulation", {})
    active_regs = [r for r, c in by_reg.items() if c > 0]

    # ── Step completion indicator ──────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:center;
                gap:0; margin: 0 auto 28px; max-width:320px;">
        <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
            <div style="width:28px; height:28px; border-radius:50%;
                        background:#1e2d4a; color:#2db87a;
                        font-size:13px; font-weight:700;
                        display:flex; align-items:center; justify-content:center;">
                ✓
            </div>
            <div style="font-size:10px; font-weight:600; color:#2db87a;
                        letter-spacing:0.08em; text-transform:uppercase;">
                Company profile
            </div>
        </div>
        <div style="flex:1; height:2px; background:#2db87a;
                    margin: 0 12px; margin-bottom:20px;"></div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
            <div style="width:28px; height:28px; border-radius:50%;
                        background:#2db87a; color:#0a0f1e;
                        font-size:13px; font-weight:700;
                        display:flex; align-items:center; justify-content:center;">
                ✓
            </div>
            <div style="font-size:10px; font-weight:600; color:#2db87a;
                        letter-spacing:0.08em; text-transform:uppercase;">
                Intelligence layer
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary header ─────────────────────────────────────────────────────
    reg_scope_str = " · ".join(
        f'<span style="color:{_REG_COLOR.get(r,"#8a9bb8")}; font-weight:700;">{r} ({by_reg[r]})</span>'
        for r in active_regs
    )

    st.markdown(f"""
    <div style="background:#0f1729; border:1px solid #1e2d4a; border-top:3px solid #3d6af5;
                border-radius:6px; padding:24px 28px; margin-bottom:20px;">
        <div style="font-size:10px; font-weight:600; color:#3d6af5;
                    letter-spacing:0.18em; text-transform:uppercase; margin-bottom:8px;">
            REGALITH INTELLIGENCE
        </div>
        <div style="font-size:22px; font-weight:700; color:#e8edf5; margin-bottom:4px;">
            {company}
        </div>
        <div style="font-size:13px; color:#5a7090; margin-bottom:16px;">
            {lt} · {", ".join(profile.get("jurisdictions", []))}
        </div>
        <div style="font-size:15px; color:#a8bbd0; line-height:1.6;">
            <strong style="color:#e8edf5;">{total} obligations</strong> identified
            across <strong style="color:#e8edf5;">{len(active_regs)} regulation{"s" if len(active_regs)!=1 else ""}</strong>:
            {reg_scope_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI strip ──────────────────────────────────────────────────────────
    cols = st.columns(3 + len(active_regs))
    kpis = [
        ("Critical",      str(critical),  "#e84040"),
        ("Important",     str(important), "#e8a020"),
        ("Informational", str(info),      "#6b8ef5"),
    ]
    for r in active_regs:
        kpis.append((r, str(by_reg[r]), _REG_COLOR.get(r, "#8a9bb8")))

    for col, (label, val, color) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class="rg-kpi">
                <div class="rg-kpi-label">{label}</div>
                <div class="rg-kpi-value" style="color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Filters ────────────────────────────────────────────────────────────
    col_reg, col_sev, col_search = st.columns([2, 2, 5])
    with col_reg:
        reg_filter = st.selectbox(
            "Regulation", ["All"] + active_regs, label_visibility="visible"
        )
    with col_sev:
        sev_filter = st.selectbox(
            "Severity", ["All", "Critical", "Important", "Informational"],
            label_visibility="visible"
        )
    with col_search:
        search = st.text_input(
            "Search", placeholder="Search article, obligation text…",
            label_visibility="collapsed"
        )

    # Apply filters
    filtered = records
    if reg_filter != "All":
        filtered = [r for r in filtered if r["regulation_id"] == reg_filter]
    if sev_filter != "All":
        filtered = [r for r in filtered if r["severity"] == sev_filter.lower()]
    if search:
        q = search.lower()
        filtered = [r for r in filtered if
                    q in r["article_label"].lower()
                    or q in r["obligation_summary"].lower()
                    or q in r["regulation_id"].lower()]

    st.markdown(
        f'<div style="font-size:11px; color:#4a6080; margin-bottom:10px;">'
        f'{len(filtered)} of {total} obligations shown</div>',
        unsafe_allow_html=True,
    )

    # ── Obligations table ──────────────────────────────────────────────────
    _render_table(filtered)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Action row ─────────────────────────────────────────────────────────
    col_pdf, col_dash, col_spacer = st.columns([2, 2, 4])

    with col_pdf:
        try:
            from utils.pdf_report import generate_pdf
            pdf_bytes = generate_pdf(profile, records)
            filename  = f"regalith-obligations-{company.lower().replace(' ','_')}.pdf"
            st.download_button(
                label="Download PDF report ↓",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"PDF generation failed: {exc}")

    with col_dash:
        if st.button("Enter intelligence layer →", use_container_width=True):
            st.session_state["view"] = "overview"
            st.rerun()


# ── Table renderer ──────────────────────────────────────────────────────────

def _render_table(records: list[dict]) -> None:
    if not records:
        st.markdown("""
        <div class="detail-section" style="text-align:center; padding:32px; color:#4a6080;">
            No obligations match the current filters.
        </div>""", unsafe_allow_html=True)
        return

    # Build HTML table
    rows_html = ""
    for rec in records:
        sev   = rec["severity"]
        color, bg, border = _SEV_COLOR.get(sev, ("#8a9bb8","rgba(0,0,0,0)","rgba(0,0,0,0.1)"))
        reg   = rec["regulation_id"]
        rc    = _REG_COLOR.get(reg, "#8a9bb8")

        # Obligation: article label as title, first sentence of summary as body
        label = rec.get("article_label", rec["article_reference"])
        # strip leading "Article N — " to keep column compact
        label_short = label.split(" — ", 1)[-1] if " — " in label else label
        first_sentence = rec["obligation_summary"].split(". ")[0] + "."

        rows_html += f"""
        <tr>
            <td style="white-space:nowrap;">
                <span style="display:inline-block; font-size:10px; font-weight:700;
                             letter-spacing:0.06em; color:{rc}; padding:2px 7px;
                             background:rgba(0,0,0,0.2); border-radius:3px;">{reg}</span>
            </td>
            <td style="white-space:nowrap; color:#6b8ef5; font-size:12px; font-weight:600;">
                {rec['article_reference']}
            </td>
            <td>
                <div style="font-size:12px; font-weight:600; color:#c8d8e8;
                            margin-bottom:3px;">{label_short}</div>
                <div style="font-size:11px; color:#5a7090; line-height:1.5;">{first_sentence}</div>
            </td>
            <td style="white-space:nowrap; font-size:11px; color:#5a7090;">
                {_fmt_deadline(rec['deadline'])}
            </td>
            <td>
                <span style="display:inline-block; font-size:10px; font-weight:700;
                             letter-spacing:0.06em; text-transform:uppercase;
                             padding:3px 8px; border-radius:3px;
                             background:{bg}; color:{color}; border:1px solid {border};">
                    {sev}
                </span>
            </td>
        </tr>"""

    table_html = f"""
    <div style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse; font-size:13px;">
        <thead>
            <tr style="border-bottom:1px solid #1e2d4a;">
                <th style="padding:10px 12px; text-align:left; font-size:10px;
                           font-weight:600; color:#4a6080; letter-spacing:0.12em;
                           text-transform:uppercase; background:#070c1a;
                           white-space:nowrap;">Regulation</th>
                <th style="padding:10px 12px; text-align:left; font-size:10px;
                           font-weight:600; color:#4a6080; letter-spacing:0.12em;
                           text-transform:uppercase; background:#070c1a;
                           white-space:nowrap;">Article</th>
                <th style="padding:10px 12px; text-align:left; font-size:10px;
                           font-weight:600; color:#4a6080; letter-spacing:0.12em;
                           text-transform:uppercase; background:#070c1a;
                           min-width:320px;">Obligation</th>
                <th style="padding:10px 12px; text-align:left; font-size:10px;
                           font-weight:600; color:#4a6080; letter-spacing:0.12em;
                           text-transform:uppercase; background:#070c1a;
                           white-space:nowrap;">Deadline</th>
                <th style="padding:10px 12px; text-align:left; font-size:10px;
                           font-weight:600; color:#4a6080; letter-spacing:0.12em;
                           text-transform:uppercase; background:#070c1a;">Severity</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)


def _fmt_deadline(dl: str) -> str:
    if "TBD" in dl or "expected" in dl:
        return "TBD ~2027"
    if "January 2025" in dl:
        return "17 Jan 2025"
    if "December 2024" in dl:
        return "30 Dec 2024"
    return dl[:20]
