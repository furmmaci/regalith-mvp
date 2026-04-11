CSS = """
<style>
/* ── Hide Streamlit dev artifacts ───────────────────────── */
[data-testid="stToolbar"]       { display: none !important; }
[data-testid="stDecoration"]    { display: none !important; }
[data-testid="stStatusWidget"]  { display: none !important; }
#MainMenu                       { visibility: hidden !important; }
footer                          { visibility: hidden !important; }

/* ── Base ───────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Remove default Streamlit padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

/* ── Brand header ────────────────────────────────────────── */
.rg-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 0 24px 0;
    border-bottom: 1px solid #1e2d4a;
    margin-bottom: 20px;
}
.rg-brand-name {
    font-size: 18px;
    font-weight: 700;
    color: #e8edf5;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.rg-brand-sub {
    font-size: 10px;
    color: #4a6080;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 1px;
}

/* ── Section titles ─────────────────────────────────────── */
.rg-section-title {
    font-size: 11px;
    font-weight: 600;
    color: #4a6080;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 12px;
    margin-top: 4px;
}
.rg-page-title {
    font-size: 22px;
    font-weight: 600;
    color: #e8edf5;
    margin-bottom: 4px;
}
.rg-page-subtitle {
    font-size: 13px;
    color: #5a7090;
    margin-bottom: 24px;
}

/* ── KPI cards ──────────────────────────────────────────── */
.rg-kpi {
    background: #0f1729;
    border: 1px solid #1e2d4a;
    border-radius: 6px;
    padding: 16px 18px;
    min-height: 88px;
}
.rg-kpi-label {
    font-size: 10px;
    font-weight: 600;
    color: #4a6080;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.rg-kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #e8edf5;
    line-height: 1;
}
.rg-kpi-value-sm {
    font-size: 18px;
    font-weight: 700;
    color: #e8edf5;
    line-height: 1;
}
.rg-kpi-sub {
    font-size: 11px;
    color: #4a6080;
    margin-top: 4px;
}
.rg-kpi-red .rg-kpi-value { color: #e84040; }
.rg-kpi-amber .rg-kpi-value { color: #e8a020; }
.rg-kpi-blue .rg-kpi-value { color: #3d6af5; }
.rg-kpi-green .rg-kpi-value { color: #2db87a; }

/* ── Severity badges ────────────────────────────────────── */
.badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 3px;
    line-height: 1.4;
}
.badge-high   { background: rgba(232,64,64,0.12);   color: #e84040; border: 1px solid rgba(232,64,64,0.25); }
.badge-medium { background: rgba(232,160,32,0.12);  color: #e8a020; border: 1px solid rgba(232,160,32,0.25); }
.badge-low    { background: rgba(45,184,122,0.12);  color: #2db87a; border: 1px solid rgba(45,184,122,0.25); }
.badge-info   { background: rgba(61,106,245,0.12);  color: #6b8ef5; border: 1px solid rgba(61,106,245,0.25); }
.badge-neutral{ background: rgba(90,112,144,0.12);  color: #8a9bb8; border: 1px solid rgba(90,112,144,0.2); }

/* ── Development cards ──────────────────────────────────── */
.dev-card {
    background: #0f1729;
    border: 1px solid #1e2d4a;
    border-radius: 6px;
    padding: 16px 18px;
    margin-bottom: 8px;
}
.dev-card-title {
    font-size: 14px;
    font-weight: 600;
    color: #e8edf5;
    margin-bottom: 6px;
    line-height: 1.4;
}
.dev-card-meta {
    font-size: 11px;
    color: #5a7090;
    margin-bottom: 10px;
}
.dev-card-summary {
    font-size: 12px;
    color: #8a9bb8;
    line-height: 1.6;
    margin-bottom: 12px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.dev-card-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.dev-card-score {
    font-size: 11px;
    font-weight: 600;
    color: #5a7090;
    text-align: right;
}

/* ── Impact score bar ───────────────────────────────────── */
.impact-bar-wrap {
    background: #1e2d4a;
    border-radius: 2px;
    height: 4px;
    width: 100%;
    margin-top: 8px;
}
.impact-bar-fill {
    height: 4px;
    border-radius: 2px;
}
.impact-bar-red    { background: #e84040; }
.impact-bar-amber  { background: #e8a020; }
.impact-bar-green  { background: #2db87a; }

/* ── Detail view ────────────────────────────────────────── */
.detail-header {
    background: #0f1729;
    border: 1px solid #1e2d4a;
    border-radius: 6px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.detail-title {
    font-size: 18px;
    font-weight: 700;
    color: #e8edf5;
    margin-bottom: 8px;
    line-height: 1.4;
}
.detail-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 11px;
    color: #5a7090;
    margin-bottom: 12px;
}
.detail-meta-item strong {
    color: #8a9bb8;
}

.detail-section {
    background: #0f1729;
    border: 1px solid #1e2d4a;
    border-radius: 6px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.detail-section-title {
    font-size: 10px;
    font-weight: 600;
    color: #4a6080;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1a2640;
}
.detail-text {
    font-size: 13px;
    color: #a8bbd0;
    line-height: 1.7;
}

/* ── Impact financials ──────────────────────────────────── */
.impact-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 8px 0;
    border-bottom: 1px solid #0f1d35;
    font-size: 13px;
}
.impact-row:last-child { border-bottom: none; }
.impact-row-label { color: #5a7090; }
.impact-row-value { color: #e8edf5; font-weight: 600; font-variant-numeric: tabular-nums; }
.impact-row-value.negative { color: #e84040; }
.impact-row-value.moderate { color: #e8a020; }

/* ── Obligations list ───────────────────────────────────── */
.obligation-item {
    display: flex;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid #0f1d35;
    font-size: 13px;
    color: #a8bbd0;
    line-height: 1.5;
}
.obligation-item:last-child { border-bottom: none; }
.obligation-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #3d6af5;
    margin-top: 6px;
    flex-shrink: 0;
}

/* ── Action items ───────────────────────────────────────── */
.action-item {
    display: flex;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #0f1d35;
}
.action-item:last-child { border-bottom: none; }
.action-text {
    font-size: 13px;
    color: #a8bbd0;
    line-height: 1.5;
    flex: 1;
}

/* ── Executive Brief ────────────────────────────────────── */
.brief-header {
    background: #0f1729;
    border: 1px solid #1e2d4a;
    border-top: 3px solid #3d6af5;
    border-radius: 6px;
    padding: 24px 28px;
    margin-bottom: 16px;
}
.brief-label {
    font-size: 10px;
    font-weight: 600;
    color: #4a6080;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.brief-title {
    font-size: 20px;
    font-weight: 700;
    color: #e8edf5;
    margin-bottom: 6px;
}
.brief-period {
    font-size: 12px;
    color: #5a7090;
}
.brief-headline {
    font-size: 14px;
    color: #a8bbd0;
    line-height: 1.6;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid #1a2640;
}
.brief-priority-item {
    background: #0a1220;
    border: 1px solid #1e2d4a;
    border-left: 3px solid #e84040;
    border-radius: 4px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.brief-priority-item.medium { border-left-color: #e8a020; }
.brief-priority-item.low    { border-left-color: #2db87a; }
.brief-priority-title { font-size: 13px; font-weight: 600; color: #e8edf5; margin-bottom: 4px; }
.brief-priority-desc  { font-size: 12px; color: #5a7090; line-height: 1.5; }

/* ── Divider ────────────────────────────────────────────── */
.rg-divider {
    border: none;
    border-top: 1px solid #1e2d4a;
    margin: 20px 0;
}

/* ── Nav sidebar ────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #070c1a !important;
    border-right: 1px solid #1e2d4a !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

/* ── Streamlit overrides ─────────────────────────────────── */
div[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
}
.stSelectbox label, .stMultiSelect label, .stTextInput label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #4a6080 !important;
}
div[data-testid="stForm"] {
    background: #0f1729;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
    padding: 24px;
}
.stButton > button {
    background: #3d6af5 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.04em !important;
    border-radius: 4px !important;
    padding: 10px 20px !important;
}
.stButton > button:hover {
    background: #2d55d0 !important;
}

/* ── Onboarding CTA — high contrast ────────────────────── */
[data-testid="stForm"] .stButton > button {
    background: #ffffff !important;
    color: #0a0f1e !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    padding: 14px 24px !important;
    border-radius: 4px !important;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.15) !important;
}
[data-testid="stForm"] .stButton > button:hover {
    background: #e8edf5 !important;
    color: #0a0f1e !important;
}

/* Secondary / ghost button */
.stButton.secondary > button {
    background: transparent !important;
    border: 1px solid #1e2d4a !important;
    color: #8a9bb8 !important;
}

/* Expander */
details summary {
    font-size: 12px;
    color: #5a7090;
}
</style>
"""
