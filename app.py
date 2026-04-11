import json
import threading
import streamlit as st
from pathlib import Path

from engine.impact import calculate_impact, aggregate_portfolio_impact
from utils.styles import CSS
from views import onboarding, overview, feed, detail, brief, requirements
from data.fetcher import check_and_refresh, get_fetch_status


# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Regalith Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS, unsafe_allow_html=True)


# ── EUR-Lex background refresh (non-blocking) ─────────────────────────────
def _background_refresh():
    try:
        check_and_refresh()
        from engine.mapper import invalidate_cache
        invalidate_cache()
    except Exception:
        pass

if "eurlex_refresh_started" not in st.session_state:
    st.session_state["eurlex_refresh_started"] = True
    t = threading.Thread(target=_background_refresh, daemon=True)
    t.start()


# ── Data loading ─────────────────────────────────────────────────────────
@st.cache_data
def load_regulations():
    path = Path(__file__).parent / "data" / "regulations.json"
    return json.loads(path.read_text(encoding="utf-8"))


regulations = load_regulations()


# ── Session state defaults ────────────────────────────────────────────────
if "view" not in st.session_state:
    st.session_state["view"] = "onboarding"
if "selected_reg_id" not in st.session_state:
    st.session_state["selected_reg_id"] = None


# ── Impact calculation (recomputed when profile changes) ──────────────────
def compute_assessments(profile):
    assessments = {}
    for reg in regulations:
        assessments[reg["id"]] = calculate_impact(reg, profile)
    return assessments


profile = st.session_state.get("profile")
assessments = compute_assessments(profile) if profile else {}
portfolio = aggregate_portfolio_impact(list(assessments.values())) if profile else {}


# ── Onboarding gate ───────────────────────────────────────────────────────
if not profile:
    onboarding.render()
    st.stop()


# ── Sidebar navigation ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="rg-brand">
        <div>
            <div class="rg-brand-name">Regalith</div>
            <div class="rg-brand-sub">Regulatory Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    company = profile.get("company_name", "")
    license_type = profile.get("license_type", "")
    st.markdown(f"""
    <div style="background:#070c1a; border:1px solid #1e2d4a; border-radius:5px;
                padding:10px 12px; margin-bottom:20px;">
        <div style="font-size:12px; font-weight:600; color:#e8edf5; margin-bottom:2px;">
            {company}
        </div>
        <div style="font-size:10px; color:#4a6080;">{license_type} · {", ".join(profile.get("jurisdictions", []))}</div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("overview", "◈  Overview"),
        ("feed", "≡  Developments"),
        ("requirements", "⊞  Requirements"),
        ("brief", "⊟  Executive Brief"),
    ]

    current_view = st.session_state.get("view", "overview")
    if current_view == "detail":
        current_view = "feed"
    if current_view not in ("overview", "feed", "requirements", "brief"):
        current_view = "overview"

    for view_key, label in nav_items:
        is_active = current_view == view_key
        btn_style = (
            "background:#1a2a4a; color:#e8edf5; border:1px solid #3d6af5;"
            if is_active else
            "background:transparent; color:#5a7090; border:1px solid transparent;"
        )
        if st.button(
            label,
            key=f"nav_{view_key}",
            use_container_width=True,
        ):
            st.session_state["view"] = view_key
            st.rerun()

    st.markdown("<hr class='rg-divider'>", unsafe_allow_html=True)

    # Portfolio snapshot in sidebar
    applicable_count = portfolio.get("applicable_count", 0)
    high_risk_count = portfolio.get("high_risk_count", 0)

    st.markdown(f"""
    <div style="font-size:10px; color:#4a6080; letter-spacing:0.1em;
                text-transform:uppercase; margin-bottom:8px;">Coverage</div>
    <div style="display:flex; justify-content:space-between; font-size:12px;
                color:#8a9bb8; padding:4px 0;">
        <span>Applicable</span>
        <span style="font-weight:600; color:#e8edf5;">{applicable_count}</span>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px;
                color:#8a9bb8; padding:4px 0;">
        <span>High risk</span>
        <span style="font-weight:600; color:{'#e84040' if high_risk_count > 0 else '#2db87a'};">
            {high_risk_count}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='rg-divider'>", unsafe_allow_html=True)

    # EUR-Lex source status
    st.markdown("""
    <div style="font-size:10px; color:#4a6080; letter-spacing:0.1em;
                text-transform:uppercase; margin-bottom:8px;">EUR-Lex sources</div>
    """, unsafe_allow_html=True)

    fetch_status = get_fetch_status()
    for reg_id, s in fetch_status.items():
        if s.get("fetched"):
            age = s.get("age_days", 0)
            count = s.get("article_count", 0)
            stale = s.get("stale", False)
            dot_color = "#e8a020" if stale else "#2db87a"
            label = f"~{age}d ago" if age > 0 else "today"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        font-size:11px; color:#8a9bb8; padding:3px 0;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:6px; height:6px; border-radius:50%;
                                background:{dot_color}; flex-shrink:0;"></div>
                    {reg_id}
                </div>
                <div style="color:#4a6080;">{count} art · {label}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        font-size:11px; color:#4a6080; padding:3px 0;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:6px; height:6px; border-radius:50%;
                                background:#2a3a50; flex-shrink:0;"></div>
                    {reg_id}
                </div>
                <div>fetching…</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='rg-divider'>", unsafe_allow_html=True)

    if st.button("⟲  Edit profile", use_container_width=True, key="nav_reset"):
        del st.session_state["profile"]
        st.session_state["view"] = "onboarding"
        st.rerun()


# ── Main content ──────────────────────────────────────────────────────────
view = st.session_state.get("view", "overview")

if view == "overview":
    overview.render(regulations, assessments, portfolio)

elif view == "feed":
    feed.render(regulations, assessments)

elif view == "detail":
    reg_id = st.session_state.get("selected_reg_id")
    reg = next((r for r in regulations if r["id"] == reg_id), None)
    if reg:
        detail.render(reg, assessments.get(reg_id))
    else:
        st.session_state["view"] = "feed"
        st.rerun()

elif view == "requirements":
    requirements.render()

elif view == "brief":
    brief.render(regulations, assessments, portfolio)
