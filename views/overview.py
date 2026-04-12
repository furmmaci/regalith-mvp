import streamlit as st
import plotly.graph_objects as go

from data.legislative_monitor import get_radar_data, DOSSIERS


def render(regulations, assessments, portfolio):
    profile = st.session_state.get("profile", {})
    company = profile.get("company_name", "Your Company")

    st.markdown(f"""
    <div class="rg-page-title">{company}</div>
    <div class="rg-page-subtitle">Regulatory impact overview — AML/KYC · EU & Poland</div>
    """, unsafe_allow_html=True)

    # ── KPI Row ─────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    applicable_count = portfolio.get("applicable_count", 0)
    high_risk_count = portfolio.get("high_risk_count", 0)
    annual_low = portfolio.get("total_annual_low", 0)
    annual_high = portfolio.get("total_annual_high", 0)
    fy_low = portfolio.get("total_first_year_low", 0)
    fy_high = portfolio.get("total_first_year_high", 0)

    with k1:
        st.markdown(f"""
        <div class="rg-kpi">
            <div class="rg-kpi-label">Applicable developments</div>
            <div class="rg-kpi-value">{applicable_count}</div>
            <div class="rg-kpi-sub">of {len(regulations)} monitored</div>
        </div>""", unsafe_allow_html=True)

    with k2:
        color_class = "rg-kpi-red" if high_risk_count >= 2 else "rg-kpi-amber"
        st.markdown(f"""
        <div class="rg-kpi {color_class}">
            <div class="rg-kpi-label">High compliance risk</div>
            <div class="rg-kpi-value">{high_risk_count}</div>
            <div class="rg-kpi-sub">developments</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="rg-kpi rg-kpi-amber">
            <div class="rg-kpi-label">Est. annual compliance cost</div>
            <div class="rg-kpi-value-sm">€{_fmt(annual_low)}–{_fmt(annual_high)}</div>
            <div class="rg-kpi-sub">recurring, medium confidence</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="rg-kpi">
            <div class="rg-kpi-label">Est. first-year total cost</div>
            <div class="rg-kpi-value-sm">€{_fmt(fy_low)}–{_fmt(fy_high)}</div>
            <div class="rg-kpi-sub">incl. implementation</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Impact / Urgency Matrix + Priority Queue ─────────────────────────
    col_matrix, col_priority = st.columns([3, 2])

    with col_matrix:
        st.markdown('<div class="rg-section-title">Impact vs Urgency Matrix</div>', unsafe_allow_html=True)
        _render_matrix(regulations, assessments)

    with col_priority:
        st.markdown('<div class="rg-section-title">Priority queue</div>', unsafe_allow_html=True)
        _render_priority_queue(regulations, assessments)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Distribution panels ──────────────────────────────────────────────
    col_topic, col_jur = st.columns(2)

    with col_topic:
        st.markdown('<div class="rg-section-title">By regulatory topic</div>', unsafe_allow_html=True)
        _render_distribution_chart(regulations, "topic")

    with col_jur:
        st.markdown('<div class="rg-section-title">By jurisdiction</div>', unsafe_allow_html=True)
        _render_distribution_chart(regulations, "jurisdiction")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Regulatory Radar ─────────────────────────────────────────────────
    st.markdown('<div class="rg-section-title">Regulatory Radar</div>', unsafe_allow_html=True)
    _render_radar(profile)


def _fmt(val: float) -> str:
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}m"
    if val >= 1_000:
        return f"{val/1_000:.0f}k"
    return str(int(val))


def _render_matrix(regulations, assessments):
    reg_map = {r["id"]: r for r in regulations}
    xs, ys, labels, colors, sizes, ids = [], [], [], [], [], []

    urgency_map = {"high": 0.85, "medium": 0.5, "low": 0.2}
    color_map = {"High": "#e84040", "Medium": "#e8a020", "Low": "#2db87a"}

    for reg_id, assessment in assessments.items():
        if not assessment or not assessment.get("applicable"):
            continue
        reg = reg_map.get(reg_id)
        if not reg:
            continue
        x = urgency_map.get(reg.get("urgency", "medium"), 0.5)
        y = reg.get("impact_score", 5.0) / 10
        xs.append(x + (hash(reg_id) % 8 - 4) * 0.015)  # slight jitter
        ys.append(y + (hash(reg_id[::-1]) % 8 - 4) * 0.015)
        labels.append(reg.get("short_title", reg_id))
        colors.append(color_map.get(assessment.get("compliance_risk", "Medium"), "#e8a020"))
        sizes.append(14)
        ids.append(reg_id)

    fig = go.Figure()

    # Quadrant shading
    fig.add_shape(type="rect", x0=0.67, x1=1.0, y0=0.67, y1=1.0,
                  fillcolor="rgba(232,64,64,0.05)", line_color="rgba(232,64,64,0.1)")
    fig.add_shape(type="rect", x0=0.0, x1=0.67, y0=0.0, y1=0.67,
                  fillcolor="rgba(45,184,122,0.03)", line_color="rgba(45,184,122,0.08)")

    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers+text",
        text=labels,
        textposition="top center",
        textfont=dict(size=9, color="#8a9bb8"),
        marker=dict(color=colors, size=sizes, opacity=0.9,
                    line=dict(color="#0a0f1e", width=1.5)),
        hovertemplate="<b>%{text}</b><extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0f1729",
        margin=dict(l=40, r=20, t=20, b=40),
        height=280,
        font=dict(family="Inter", color="#8a9bb8", size=10),
        xaxis=dict(
            title="Urgency", range=[0, 1], showgrid=True,
            gridcolor="#1a2640", zeroline=False,
            tickvals=[0.2, 0.5, 0.85], ticktext=["Low", "Medium", "High"],
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title="Impact", range=[0, 1], showgrid=True,
            gridcolor="#1a2640", zeroline=False,
            tickvals=[0.2, 0.5, 0.85], ticktext=["Low", "Medium", "High"],
            tickfont=dict(size=9),
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_priority_queue(regulations, assessments):
    scored = []
    for reg in regulations:
        a = assessments.get(reg["id"])
        if a and a.get("applicable"):
            score = reg.get("impact_score", 0) * reg.get("enforcement_probability", 0)
            scored.append((score, reg, a))

    scored.sort(key=lambda x: x[0], reverse=True)

    for i, (score, reg, a) in enumerate(scored[:5]):
        urgency = reg.get("urgency", "low")
        badge_class = f"badge-{urgency}"
        risk = a.get("compliance_risk", "Medium")
        risk_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(risk, "badge-medium")
        short = reg.get("short_title", reg.get("title", "")[:25])
        eff_date = reg.get("effective_date", "—")

        st.markdown(f"""
        <div class="dev-card" style="padding:12px 14px; cursor:default;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                <div class="dev-card-title" style="font-size:13px; flex:1;">{short}</div>
                <div style="margin-left:8px; flex-shrink:0;">
                    <span class="badge {risk_class}">{risk}</span>
                </div>
            </div>
            <div style="display:flex; gap:8px; align-items:center;">
                <span class="badge {badge_class}">{urgency}</span>
                <span style="font-size:10px; color:#4a6080;">Effective: {eff_date}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("View details", key=f"pq_{reg['id']}", use_container_width=True):
            st.session_state["view"] = "detail"
            st.session_state["selected_reg_id"] = reg["id"]
            st.rerun()


def _render_distribution_chart(regulations, field):
    from collections import Counter
    counts = Counter(r.get(field, "Other") for r in regulations)
    labels = list(counts.keys())
    values = list(counts.values())

    colors = ["#3d6af5", "#2db87a", "#e8a020", "#e84040", "#6b8ef5", "#5a7090"]

    fig = go.Figure(go.Bar(
        x=values, y=labels,
        orientation="h",
        marker=dict(color=colors[:len(labels)], opacity=0.85),
        text=values,
        textposition="auto",
        textfont=dict(size=10, color="#e8edf5"),
    ))

    fig.update_layout(
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0f1729",
        height=200,
        margin=dict(l=0, r=10, t=8, b=8),
        font=dict(family="Inter", color="#8a9bb8", size=10),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        bargap=0.35,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Regulatory Radar ────────────────────────────────────────────────────────

def _render_radar(profile: dict) -> None:
    """Render legislative monitoring cards filtered to company profile."""
    license_type = profile.get("license_type", "")
    has_crypto   = profile.get("has_crypto", False)

    try:
        radar = get_radar_data()
    except Exception:
        st.markdown(
            '<div style="color:#4a6080; font-size:12px; padding:16px;">Radar data unavailable.</div>',
            unsafe_allow_html=True,
        )
        return

    # Filter dossiers relevant to this profile
    relevant = []
    for key, entry in radar.items():
        scope = entry.get("scope", [])
        if license_type in scope or (has_crypto and "VASP" in scope):
            relevant.append((key, entry))

    if not relevant:
        st.markdown(
            '<div style="color:#4a6080; font-size:12px; padding:16px;">'
            'No tracked dossiers match your current profile.</div>',
            unsafe_allow_html=True,
        )
        return

    # Render in a grid: 2 columns
    pairs = [relevant[i:i+2] for i in range(0, len(relevant), 2)]

    _STATUS_LABEL = {
        "red":   ("ACTIVE", "#e84040", "rgba(232,64,64,0.12)"),
        "amber": ("IN PROGRESS", "#e8a020", "rgba(232,160,32,0.12)"),
        "blue":  ("ADVANCING", "#3d6af5", "rgba(61,106,245,0.12)"),
        "gray":  ("MONITORING", "#5a7090", "rgba(90,112,144,0.10)"),
    }

    for pair in pairs:
        cols = st.columns(2)
        for col, (key, entry) in zip(cols, pair):
            with col:
                sc          = entry.get("status_class", "gray")
                label, fc, bg = _STATUS_LABEL.get(sc, _STATUS_LABEL["gray"])
                color       = entry.get("color", "#5a7090")
                pct         = entry.get("progress_pct", 0)
                title       = entry.get("title", key)
                short       = entry.get("short", key)
                description = entry.get("description", "")
                stage       = entry.get("current_stage", "—")
                last_update = entry.get("last_update", "—")
                next_ms     = entry.get("next_milestone", "—")
                expected    = entry.get("expected_date", "TBD")

                pct_safe = max(0, min(100, pct))

                st.markdown(f"""
                <div style="background:#0f1729; border:1px solid #1e2d4a;
                            border-left:3px solid {color};
                            border-radius:6px; padding:16px 18px; margin-bottom:12px;">

                    <!-- Header row -->
                    <div style="display:flex; justify-content:space-between;
                                align-items:flex-start; margin-bottom:10px;">
                        <div>
                            <span style="font-size:10px; font-weight:700; letter-spacing:0.12em;
                                         color:{color}; text-transform:uppercase;">{short}</span>
                            <div style="font-size:13px; font-weight:600; color:#c8d8e8;
                                        margin-top:3px; line-height:1.35;">{title}</div>
                        </div>
                        <span style="font-size:9px; font-weight:700; letter-spacing:0.1em;
                                     text-transform:uppercase; padding:3px 8px; border-radius:3px;
                                     background:{bg}; color:{fc}; white-space:nowrap;
                                     margin-left:10px; flex-shrink:0;">{label}</span>
                    </div>

                    <!-- Description -->
                    <div style="font-size:11px; color:#5a7090; margin-bottom:12px;
                                line-height:1.5;">{description}</div>

                    <!-- Progress bar -->
                    <div style="margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between;
                                    font-size:9px; color:#4a6080; margin-bottom:4px;">
                            <span>Legislative progress</span>
                            <span>{pct_safe}%</span>
                        </div>
                        <div style="background:#1a2640; border-radius:2px; height:4px;">
                            <div style="background:{color}; width:{pct_safe}%; height:4px;
                                        border-radius:2px;"></div>
                        </div>
                    </div>

                    <!-- Status grid -->
                    <div style="display:grid; grid-template-columns:1fr 1fr;
                                gap:8px; font-size:11px;">
                        <div>
                            <div style="color:#4a6080; font-size:9px; text-transform:uppercase;
                                        letter-spacing:0.08em; margin-bottom:2px;">Current stage</div>
                            <div style="color:#8a9bb8; line-height:1.4;">{stage}</div>
                        </div>
                        <div>
                            <div style="color:#4a6080; font-size:9px; text-transform:uppercase;
                                        letter-spacing:0.08em; margin-bottom:2px;">Last update</div>
                            <div style="color:#8a9bb8;">{last_update}</div>
                        </div>
                        <div>
                            <div style="color:#4a6080; font-size:9px; text-transform:uppercase;
                                        letter-spacing:0.08em; margin-bottom:2px;">Next milestone</div>
                            <div style="color:#a8bbd0; line-height:1.4;">{next_ms}</div>
                        </div>
                        <div>
                            <div style="color:#4a6080; font-size:9px; text-transform:uppercase;
                                        letter-spacing:0.08em; margin-bottom:2px;">Expected</div>
                            <div style="color:{fc}; font-weight:600;">{expected}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
