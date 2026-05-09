import streamlit as st
import base64
from PIL import Image
from database import (
    init_db,
    create_user,
    login_user,
    get_user,
    create_goal,
    get_active_goals,
    get_goal,
    deactivate_goal,
    user_can_access_goal,
    invite_partner,
    get_pending_invites,
    respond_to_invite,
    get_goal_members,
    get_pending_invitees,
    save_plan,
    get_plan_for_date,
    save_check_in,
    get_check_in_for_date,
    get_check_ins,
    compute_stats,
    maybe_adapt_difficulty,
    save_daily_mood,
    get_daily_mood,
    save_distraction,
    get_distractions,
    get_distraction_insights,
)
from ai_engine import (
    generate_daily_plan,
    generate_feedback,
    generate_distraction_insight,
    DIFFICULTY_LABELS,
)
from streak_card import generate_streak_card_png

try:
    _icon = Image.open("logo.png")
except Exception:
    _icon = "🎯"

st.set_page_config(
    page_title="ZeroSkip",
    page_icon=_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Serif+4:ital,wght@1,400;1,600&family=JetBrains+Mono:wght@400&display=swap');

:root {
    --bg:        #0A0A0C;
    --surface:   #121216;
    --surface-2: #16171C;
    --border:    #2A2C31;
    --border-soft:#1F2126;
    --ink:       #FFFFFF;
    --ink-dim:   #AEB0B6;
    --ink-faint: #686B73;
    --rose:      #FF6F91;
    --violet:    #B29CFF;
    --amber:     #F5A623;
    --teal:      #4FD1C5;
    --pink:      #FF8AB8;
    --blue:      #6FB1FF;
    --emerald:   #4ADE80;
    --serif:     'Source Serif 4', Georgia, serif;
    --sans:      'Inter', -apple-system, 'Helvetica Neue', sans-serif;
}

html, body, .stApp, [class*="css"] {
    background: var(--bg) !important;
    color: var(--ink) !important;
    font-family: var(--sans);
}
.stApp { background: var(--bg) !important; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1080px; }

/* Hide Streamlit chrome — but keep sidebar collapse button visible (mobile nav!) */
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
/* Always show the sidebar collapse/expand control on every screen size */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    z-index: 9999 !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--ink) !important;
    box-shadow: 0 4px 18px rgba(0,0,0,0.4);
}
@media (max-width: 768px) {
    .block-container { padding-top: 3.4rem !important; padding-left: 1.1rem !important; padding-right: 1.1rem !important; }
    .headline, .headline-italic { font-size: 32px !important; }
    .stat .value { font-size: 24px !important; }
    .notif { padding: 14px 16px 14px 20px !important; }
    .notif .em { font-size: 26px !important; }
    .notif .ttl { font-size: 14.5px !important; }
}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #08080A !important;
    border-right: 1px solid var(--border-soft);
}
[data-testid="stSidebar"] * { color: var(--ink-dim); }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--ink) !important; }

/* sidebar nav radio: clean stacked links */
[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 2px;
}
[data-testid="stSidebar"] [role="radiogroup"] > label {
    background: transparent;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 0;
    transition: background 0.12s;
    cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {
    background: rgba(255,255,255,0.04);
}
[data-testid="stSidebar"] [role="radiogroup"] > label[data-checked="true"],
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
    background: rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] > label p {
    color: var(--ink-dim) !important;
    font-size: 14px !important;
    font-weight: 500;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p {
    color: var(--ink) !important;
}

/* ── Typography ──────────────────────────────────────────── */
.eyebrow {
    font-size: 11px;
    font-weight: 600;
    color: var(--ink-faint);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 18px;
}
.headline {
    font-size: 44px;
    font-weight: 700;
    color: var(--ink);
    line-height: 1.05;
    margin: 0;
    letter-spacing: -0.02em;
}
.headline-italic {
    font-family: var(--serif);
    font-style: italic;
    font-weight: 400;
    font-size: 44px;
    color: var(--ink);
    line-height: 1.0;
    margin: 0 0 8px 0;
    letter-spacing: -0.01em;
}
.subhead {
    font-size: 15px;
    color: var(--ink-dim);
    line-height: 1.55;
    max-width: 720px;
    margin: 14px 0 28px 0;
}
.section-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--ink-faint);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin: 32px 0 14px 0;
    border-bottom: 1px solid var(--border-soft);
    padding-bottom: 10px;
}

/* ── Cards ───────────────────────────────────────────────── */
.card {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 12px;
}
.card-glow {
    background:
        radial-gradient(120% 80% at 0% 0%, rgba(178,156,255,0.18), transparent 55%),
        var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 12px;
}
.card-row { display: flex; align-items: center; gap: 14px; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.dot.rose    { background: var(--rose); }
.dot.violet  { background: var(--violet); }
.dot.amber   { background: var(--amber); }
.dot.teal    { background: var(--teal); }
.dot.pink    { background: var(--pink); }
.dot.blue    { background: var(--blue); }
.dot.emerald { background: var(--emerald); }
.dot.faint   { background: var(--ink-faint); }

.goal-title { font-size: 20px; font-weight: 700; color: var(--ink); letter-spacing:-0.01em; }
.goal-meta  { font-size: 12px; color: var(--ink-faint); letter-spacing: 0.06em; text-transform: uppercase; margin-top:4px;}
.goal-desc  { font-size: 14px; color: var(--ink-dim); line-height: 1.55; margin-top: 10px; }

.fn-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--ink-faint);
    font-style: italic;
}

/* ── Stat tiles ──────────────────────────────────────────── */
.stat {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 18px 18px;
}
.stat .label {
    font-size: 10px;
    color: var(--ink-faint);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.stat .value {
    font-size: 32px;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -0.02em;
    line-height: 1;
}
.stat .unit { font-size: 12px; color: var(--ink-faint); margin-left: 4px; }
.stat .value.green   { color: var(--emerald); }
.stat .value.amber   { color: var(--amber); }
.stat .value.rose    { color: var(--rose); }
.stat .value.violet  { color: var(--violet); }
.stat .value.teal    { color: var(--teal); }

/* ── Badges ──────────────────────────────────────────────── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border: 1px solid var(--border);
}
.badge.done    { color: var(--emerald); border-color: rgba(74,222,128,0.35); background: rgba(74,222,128,0.08); }
.badge.missed  { color: var(--rose);    border-color: rgba(255,111,145,0.35); background: rgba(255,111,145,0.08); }
.badge.pending { color: var(--amber);   border-color: rgba(245,166,35,0.35);  background: rgba(245,166,35,0.08); }
.badge.shared  { color: var(--violet);  border-color: rgba(178,156,255,0.35); background: rgba(178,156,255,0.08); }
.badge.owner   { color: var(--ink-dim); border-color: var(--border); background: transparent; }

/* ── Plan / Feedback boxes ───────────────────────────────── */
.panel {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-left: 3px solid var(--violet);
    border-radius: 12px;
    padding: 20px 22px;
    color: var(--ink-dim);
    font-size: 14.5px;
    line-height: 1.7;
}
.panel.amber  { border-left-color: var(--amber); }
.panel.rose   { border-left-color: var(--rose); }
.panel.teal   { border-left-color: var(--teal); }

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button, .stFormSubmitButton > button {
    background: var(--surface);
    color: var(--ink);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.02em;
    transition: all 0.12s;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #1d1e23;
    border-color: #3a3c42;
    color: var(--ink);
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
.stButton > button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--ink) !important;
    color: var(--bg) !important;
    border: 1px solid var(--ink) !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover,
.stButton > button[kind="primaryFormSubmit"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: #e8e8eb !important;
    color: var(--bg) !important;
}

/* ── Inputs ──────────────────────────────────────────────── */
input, textarea, select,
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    background: var(--surface) !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 1px var(--violet) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stRadio label {
    color: var(--ink-dim) !important;
    font-size: 12px !important;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
[data-baseweb="popover"] { background: var(--surface) !important; }

/* ── Tabs ────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--border-soft) !important;
    background: transparent !important;
    gap: 24px;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--ink-faint) !important;
    border: none !important;
    padding: 10px 0 14px 0 !important;
    font-size: 13px !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 600;
}
[aria-selected="true"][data-baseweb="tab"] { color: var(--ink) !important; }
[data-baseweb="tab-highlight"] { background: var(--ink) !important; height: 2px !important; }

/* ── Progress bars ───────────────────────────────────────── */
.stProgress > div > div > div { background: var(--ink) !important; }
.stProgress > div > div { background: var(--border-soft) !important; height: 4px !important; }

/* ── Expander ────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
}
[data-testid="stExpander"] summary { color: var(--ink) !important; }

/* ── Misc ────────────────────────────────────────────────── */
hr, .divider { border: none; border-top: 1px solid var(--border-soft); margin: 28px 0; }
a { color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }
.muted { color: var(--ink-faint); font-size: 12px; }

/* ── Auth screen ─────────────────────────────────────────── */
.auth-wrap {
    max-width: 440px; margin: 60px auto 0 auto; text-align: center;
}
.auth-brand {
    font-size: 36px; font-weight: 800; color: var(--ink);
    letter-spacing: -0.02em; margin-top: 22px;
}
.auth-brand .ital {
    font-family: var(--serif); font-style: italic; font-weight: 400; color: var(--ink-dim);
}
.auth-tag { font-size: 13px; color: var(--ink-faint); margin-top: 6px; letter-spacing: 0.04em; }

/* ── Buddy row ───────────────────────────────────────────── */
.buddy-row {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px;
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    background: var(--surface);
    margin-bottom: 8px;
}
.avatar {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700; color: var(--ink);
    background: linear-gradient(135deg, var(--violet), var(--rose));
    flex-shrink: 0;
}
.avatar.teal   { background: linear-gradient(135deg, var(--teal), var(--blue)); }
.avatar.amber  { background: linear-gradient(135deg, var(--amber), var(--rose)); }
.avatar.emerald{ background: linear-gradient(135deg, var(--emerald), var(--teal)); }
.buddy-name { font-size: 14px; font-weight: 600; color: var(--ink); }
.buddy-meta { font-size: 11px; color: var(--ink-faint); letter-spacing: 0.06em; text-transform: uppercase; }

/* ── Smart notification banner ───────────────────────────── */
.notif {
    position: relative;
    display: flex; align-items: flex-start; gap: 16px;
    background:
        radial-gradient(120% 100% at 0% 0%, rgba(178,156,255,0.14), transparent 55%),
        linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px 22px 18px 26px;
    margin: 6px 0 26px 0;
    overflow: hidden;
    animation: notifSlide 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
}
@keyframes notifSlide {
    from { opacity: 0; transform: translateY(-8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.notif::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; background: var(--violet);
}
.notif.emerald::before { background: var(--emerald); }
.notif.amber::before   { background: var(--amber); }
.notif.rose::before    { background: var(--rose); }
.notif.teal::before    { background: var(--teal); }
.notif .em {
    font-size: 30px; line-height: 1; flex-shrink: 0;
    filter: drop-shadow(0 0 12px rgba(178,156,255,0.25));
    animation: emojiPulse 2.6s ease-in-out infinite;
}
@keyframes emojiPulse {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.08) rotate(-3deg); }
}
.notif .ttl {
    font-size: 16.5px; font-weight: 700; color: var(--ink);
    letter-spacing: -0.01em; line-height: 1.3;
}
.notif .body {
    font-size: 13px; color: var(--ink-dim);
    line-height: 1.55; margin-top: 5px;
}
.notif .tag {
    display: inline-block;
    font-size: 10px; font-weight: 600;
    color: var(--ink-faint);
    letter-spacing: 0.18em; text-transform: uppercase;
    margin-bottom: 6px;
}

/* ── Mood / Energy chooser ───────────────────────────────── */
.mood-row {
    display: flex; gap: 12px; margin: 8px 0 6px 0;
    flex-wrap: wrap;
}
.mood-chip {
    flex: 1; min-width: 140px;
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 18px 18px;
    text-align: center;
    transition: all 0.15s;
}
.mood-chip .em { font-size: 28px; line-height: 1; margin-bottom: 8px; }
.mood-chip .lbl {
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--ink-dim);
}
.mood-chip .desc { font-size: 11px; color: var(--ink-faint); margin-top: 4px; }
.mood-chip.active.low    { border-color: var(--rose);    box-shadow: 0 0 0 1px var(--rose),    0 0 18px rgba(255,111,145,0.25); }
.mood-chip.active.normal { border-color: var(--violet);  box-shadow: 0 0 0 1px var(--violet),  0 0 18px rgba(178,156,255,0.25); }
.mood-chip.active.high   { border-color: var(--emerald); box-shadow: 0 0 0 1px var(--emerald), 0 0 18px rgba(74,222,128,0.25); }
.mood-chip.active .lbl   { color: var(--ink); }

/* ── Distraction insight panel ───────────────────────────── */
.distraction-bar-row {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 10px;
}
.distraction-bar-label {
    width: 130px; font-size: 12px; color: var(--ink-dim);
    letter-spacing: 0.04em; flex-shrink: 0;
}
.distraction-bar-track {
    flex: 1; height: 8px; background: rgba(255,255,255,0.05);
    border-radius: 999px; overflow: hidden;
}
.distraction-bar-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, var(--rose), var(--amber));
}
.distraction-count {
    width: 32px; text-align: right; font-size: 13px;
    color: var(--ink); font-weight: 600; flex-shrink: 0;
}

/* ── Time honesty delta pill ─────────────────────────────── */
.time-delta {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 600; letter-spacing: 0.04em;
    border: 1px solid var(--border);
    margin-top: 8px;
}
.time-delta.good { color: var(--emerald); border-color: rgba(74,222,128,0.4); background: rgba(74,222,128,0.08); }
.time-delta.bad  { color: var(--rose);    border-color: rgba(255,111,145,0.4); background: rgba(255,111,145,0.08); }
.time-delta.ok   { color: var(--ink-dim); }

/* ── Streak share card preview ───────────────────────────── */
.share-hint {
    font-size: 12px; color: var(--ink-faint);
    letter-spacing: 0.04em; margin-top: 10px;
}

/* ── Calendar heatmap ────────────────────────────────────── */
.cal-shell {
    background: var(--surface);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 22px 24px 18px 24px;
    overflow-x: auto;
}
.cal-grid-wrap { display: flex; gap: 10px; align-items: flex-start; }
.cal-daycol {
    display: flex; flex-direction: column; gap: 4px;
    padding-top: 22px;
    margin-right: 4px;
}
.cal-daycol .cal-daylabel {
    height: 14px; line-height: 14px;
    font-size: 10px; color: var(--ink-faint);
    letter-spacing: 0.1em;
}
.cal-grid {
    display: flex; gap: 4px;
    position: relative;
}
.cal-col { display: flex; flex-direction: column; gap: 4px; }
.cal-month {
    height: 18px;
    font-size: 10px; color: var(--ink-faint);
    letter-spacing: 0.16em; text-transform: uppercase;
    font-weight: 600;
    white-space: nowrap;
    overflow: visible;
}
.cal-cell {
    width: 14px; height: 14px;
    border-radius: 3px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.02);
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    cursor: default;
    position: relative;
}
.cal-cell:hover {
    transform: scale(1.55);
    z-index: 2;
}
.cal-cell.done {
    background: var(--emerald);
    border-color: rgba(74,222,128,0.4);
    box-shadow: 0 0 0 1px rgba(74,222,128,0.25), 0 0 10px rgba(74,222,128,0.35);
}
.cal-cell.missed {
    background: var(--rose);
    border-color: rgba(255,111,145,0.4);
    box-shadow: 0 0 0 1px rgba(255,111,145,0.22);
}
.cal-cell.today {
    box-shadow: 0 0 0 2px var(--ink), 0 0 14px rgba(255,255,255,0.5);
}
.cal-cell.future {
    background: transparent;
    border: 1px dashed rgba(255,255,255,0.07);
}
.cal-legend {
    display: flex; gap: 18px; align-items: center;
    margin-top: 16px;
    font-size: 11px; color: var(--ink-faint);
    letter-spacing: 0.08em; text-transform: uppercase;
    border-top: 1px solid var(--border-soft);
    padding-top: 14px;
}
.cal-legend .swatch {
    width: 12px; height: 12px; border-radius: 3px;
    display: inline-block; margin-right: 8px; vertical-align: middle;
}
.cal-legend .sw-done   { background: var(--emerald); box-shadow: 0 0 8px rgba(74,222,128,0.4); }
.cal-legend .sw-missed { background: var(--rose); }
.cal-legend .sw-empty  { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.04); }
.cal-summary {
    display: flex; gap: 28px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border-soft);
}
.cal-summary .item .num {
    font-size: 22px; font-weight: 700; color: var(--ink);
    letter-spacing: -0.01em; line-height: 1;
}
.cal-summary .item .num.green { color: var(--emerald); }
.cal-summary .item .num.rose  { color: var(--rose); }
.cal-summary .item .lbl {
    font-size: 10px; color: var(--ink-faint);
    letter-spacing: 0.16em; text-transform: uppercase;
    margin-top: 6px;
}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


CATEGORIES = ["Health & Fitness", "Learning", "Career", "Mindfulness", "Finance", "Other"]
DIFF_DOT = {1: "emerald", 2: "teal", 3: "amber", 4: "rose", 5: "violet"}
AVATAR_TONES = ["", "teal", "amber", "emerald"]

MOOD_OPTIONS = [
    ("low",    "🪫", "LOW",    "Easy mode today"),
    ("normal", "⚡", "NORMAL", "Run the standard play"),
    ("high",   "🔥", "HIGH",   "Push it harder"),
]
TIME_OF_DAY_OPTIONS = ["Morning", "Afternoon", "Evening", "Late night"]


def avatar_class_for(username: str) -> str:
    return AVATAR_TONES[sum(ord(c) for c in username) % len(AVATAR_TONES)]


def initials(username: str) -> str:
    return (username[:1] + username[-1:]).upper() if username else "?"


def page_intro(eyebrow: str, headline: str, italic: str, subhead: str):
    st.markdown(
        f'<div class="eyebrow">{eyebrow}</div>'
        f'<div class="headline">{headline}</div>'
        f'<div class="headline-italic">{italic}</div>'
        f'<div class="subhead">{subhead}</div>',
        unsafe_allow_html=True,
    )


def section(label: str):
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# SMART NOTIFICATIONS — emoji-driven nudges based on behavior
# ──────────────────────────────────────────────────────────────
def get_smart_notification(stats, today_ci, check_ins, members, user_id, goal_id):
    """Returns dict {tone, emoji, tag, title, body} based on user state."""
    streak = stats.get("streak", 0)
    rate = stats.get("completion_rate", 0)
    missed = stats.get("missed_days", 0)

    # Find buddy who already checked in today (if any)
    buddy_done = None
    for m in members:
        if m["id"] == user_id:
            continue
        their_ci = get_check_in_for_date(goal_id, m["id"])
        if their_ci and their_ci["completed"]:
            buddy_done = m["username"]
            break

    # ── Already checked in today ─────────────────────────────
    if today_ci and today_ci["completed"]:
        if streak >= 30:
            return {"tone":"emerald","emoji":"🏆","tag":"LEGENDARY",
                    "title":f"{streak} days. You're in rare air.",
                    "body":"Top 1% of consistency, statistically. Don't look down — keep climbing."}
        if streak >= 14:
            return {"tone":"emerald","emoji":"🔥","tag":"ON FIRE",
                    "title":f"{streak} days strong. Momentum is yours.",
                    "body":"You've crossed the hard part. Habits take 2 weeks to wire — you're past it."}
        if streak >= 7:
            return {"tone":"emerald","emoji":"⚡","tag":"LOCKED IN",
                    "title":f"One full week. {streak} days down.",
                    "body":"This is where most people quit. You're not most people."}
        if streak >= 3:
            return {"tone":"emerald","emoji":"🚀","tag":"TAKING OFF",
                    "title":f"{streak} days. Engine's warm.",
                    "body":"Three days is the dangerous one. You cleared it. Ride the wave."}
        return {"tone":"emerald","emoji":"✅","tag":"DONE FOR TODAY",
                "title":"Today is locked in. Come back tomorrow.",
                "body":"That's how streaks are built — one boring, beautiful repetition at a time."}

    # ── Logged today but missed ──────────────────────────────
    if today_ci and not today_ci["completed"]:
        return {"tone":"amber","emoji":"💪","tag":"COMEBACK MODE",
                "title":"Today slipped. That's data, not failure.",
                "body":"One miss doesn't delete the work. Tomorrow's check-in is where the comeback starts."}

    # ── Pending check-in today ───────────────────────────────
    if streak >= 14:
        return {"tone":"rose","emoji":"⚠️","tag":"STREAK AT RISK",
                "title":f"You're about to break a {streak}-day streak.",
                "body":"Don't ruin it now. Two minutes of effort beats restarting from zero."}
    if streak >= 7:
        return {"tone":"rose","emoji":"🔥","tag":"DON'T BLOW IT",
                "title":f"{streak}-day streak hangs on today.",
                "body":"You're past the hard part. Skipping today wipes a full week of momentum."}
    if streak >= 3:
        return {"tone":"amber","emoji":"🔥","tag":"KEEP IT ALIVE",
                "title":f"Your {streak}-day streak is on the line.",
                "body":"Today's check-in keeps it breathing. Skip and you're back to day one."}
    if buddy_done:
        return {"tone":"violet","emoji":"👀","tag":"BUDDY ALERT",
                "title":f"@{buddy_done} already checked in today.",
                "body":"You don't want to be the one holding the team back. Your turn."}
    if missed >= 3 and streak == 0:
        return {"tone":"violet","emoji":"🌱","tag":"FRESH START",
                "title":"Reset button. Today is day one — again.",
                "body":"Comebacks beat unbroken streaks. Just one check-in to start the engine."}
    if streak == 0 and rate == 0:
        return {"tone":"violet","emoji":"🎯","tag":"DAY ZERO",
                "title":"Plant the flag. Today is the start.",
                "body":"The first check-in is the hardest. Once you hit it, the rest gets easier."}
    return {"tone":"violet","emoji":"☀️","tag":"TODAY'S NUDGE",
            "title":"Today is unwritten. Make it count.",
            "body":"One check-in. Two minutes. That's all it takes to keep the rhythm going."}


def render_notification(notif):
    st.markdown(
        f'<div class="notif {notif["tone"]}">'
        f'<div class="em">{notif["emoji"]}</div>'
        f'<div style="flex:1">'
        f'<div class="tag">{notif["tag"]}</div>'
        f'<div class="ttl">{notif["title"]}</div>'
        f'<div class="body">{notif["body"]}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# CALENDAR HEATMAP — GitHub-style contribution grid
# ──────────────────────────────────────────────────────────────
def render_calendar_heatmap(check_ins, weeks=14):
    from datetime import date, timedelta
    today = date.today()

    status_by_date = {}
    for ci in check_ins:
        d = ci["check_in_date"]
        if not isinstance(d, str):
            d = d.isoformat()
        status_by_date[d] = "done" if ci["completed"] else "missed"

    # Start from Monday of (weeks-1) weeks ago
    total_days = weeks * 7
    start = today - timedelta(days=total_days - 1)
    while start.weekday() != 0:  # 0 = Monday
        start -= timedelta(days=1)

    # Build columns (each column = one week, top=Mon → bottom=Sun)
    end = today
    while end.weekday() != 6:
        end += timedelta(days=1)

    columns = []
    cur = start
    while cur <= end:
        col = [cur + timedelta(days=i) for i in range(7)]
        columns.append(col)
        cur += timedelta(days=7)

    # Month labels: identify column index where each new month begins
    month_starts = []  # list of (col_idx, label)
    last_month = None
    for idx, col in enumerate(columns):
        first = col[0]
        if first.month != last_month and first <= today:
            month_starts.append((idx, first.strftime("%b").upper()))
            last_month = first.month
    # Drop labels that crowd the next one (need ≥3 cols of breathing room).
    # Last label always kept — labels can overflow to the right freely.
    keep = []
    for i, (idx, label) in enumerate(month_starts):
        if i + 1 < len(month_starts):
            if month_starts[i + 1][0] - idx >= 3:
                keep.append((idx, label))
        else:
            keep.append((idx, label))
    keep_map = dict(keep)

    month_row_html = '<div class="cal-grid" style="margin-bottom:2px">'
    for idx in range(len(columns)):
        label = keep_map.get(idx, "")
        month_row_html += f'<div class="cal-month" style="width:14px">{label}</div>'
    month_row_html += '</div>'

    # Day cells
    cells_html = '<div class="cal-grid">'
    for col in columns:
        col_html = '<div class="cal-col">'
        for d in col:
            iso = d.isoformat()
            classes = ["cal-cell"]
            if d > today:
                classes.append("future")
                title = f"{d.strftime('%b %-d, %Y')} — Upcoming"
            else:
                status = status_by_date.get(iso)
                if status == "done":
                    classes.append("done")
                    title = f"{d.strftime('%b %-d, %Y')} — Completed"
                elif status == "missed":
                    classes.append("missed")
                    title = f"{d.strftime('%b %-d, %Y')} — Missed"
                else:
                    title = f"{d.strftime('%b %-d, %Y')} — No check-in"
            if d == today:
                classes.append("today")
            col_html += f'<div class="{" ".join(classes)}" title="{title}"></div>'
        col_html += '</div>'
        cells_html += col_html
    cells_html += '</div>'

    # Day-of-week sidebar (Mon, Wed, Fri)
    day_labels = ["Mon", "", "Wed", "", "Fri", "", ""]
    daycol_html = '<div class="cal-daycol">'
    for lbl in day_labels:
        daycol_html += f'<div class="cal-daylabel">{lbl}</div>'
    daycol_html += '</div>'

    # Summary numbers (across the displayed range only)
    range_dates = {(start + timedelta(days=i)).isoformat()
                   for i in range((today - start).days + 1)}
    done_count = sum(1 for d, s in status_by_date.items() if d in range_dates and s == "done")
    missed_count = sum(1 for d, s in status_by_date.items() if d in range_dates and s == "missed")
    days_in_range = (today - start).days + 1
    summary_html = (
        '<div class="cal-summary">'
        f'<div class="item"><div class="num green">{done_count}</div><div class="lbl">Completed</div></div>'
        f'<div class="item"><div class="num rose">{missed_count}</div><div class="lbl">Missed</div></div>'
        f'<div class="item"><div class="num">{days_in_range}</div><div class="lbl">Days tracked</div></div>'
        '</div>'
    )

    legend_html = (
        '<div class="cal-legend">'
        '<span><span class="swatch sw-done"></span>Completed</span>'
        '<span><span class="swatch sw-missed"></span>Missed</span>'
        '<span><span class="swatch sw-empty"></span>No check-in</span>'
        '</div>'
    )

    inner = (
        f'{summary_html}'
        f'<div class="cal-grid-wrap">'
        f'  {daycol_html}'
        f'  <div>{month_row_html}{cells_html}</div>'
        f'</div>'
        f'{legend_html}'
    )
    st.markdown(f'<div class="cal-shell">{inner}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────
def show_auth():
    try:
        with open("logo.png", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{img_b64}" width="92" style="border-radius:20px">'
    except Exception:
        logo_html = '<div style="font-size:48px">🎯</div>'

    st.markdown(
        f'<div class="auth-wrap">'
        f'<div>{logo_html}</div>'
        f'<div class="auth-brand">ZeroSkip<span class="ital">.</span></div>'
        f'<div class="auth-tag">DON\'T BREAK THE STREAK</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        tab1, tab2 = st.tabs(["LOG IN", "CREATE ACCOUNT"])
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    user = login_user(username, password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username")
                new_password = st.text_input("Choose a password", type="password")
                confirm = st.text_input("Confirm password", type="password")
                submitted2 = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if submitted2:
                if not new_username or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm:
                    st.error("Passwords don't match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        user = create_user(new_username, new_password)
                        st.session_state["user"] = user
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))


if "user" not in st.session_state:
    show_auth()
    st.stop()

user = st.session_state["user"]
user_id = user["id"]


# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        with open("logo.png", "rb") as f:
            sb_b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-top:6px;margin-bottom:18px">'
            f'<img src="data:image/png;base64,{sb_b64}" width="32" style="border-radius:8px">'
            f'<div style="font-size:18px;font-weight:800;color:#fff;letter-spacing:-0.01em">ZeroSkip</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown("## ZeroSkip")

    pending = get_pending_invites(user_id)
    inbox_label = f"Inbox ({len(pending)})" if pending else "Inbox"

    st.markdown('<div style="font-size:10px;color:#686B73;letter-spacing:0.18em;margin:14px 0 10px 4px;font-weight:600">NAVIGATE</div>', unsafe_allow_html=True)
    page = st.radio(
        "nav",
        ["Goals", "Today", "Progress", "AI Feedback", inbox_label],
        label_visibility="collapsed",
    )

    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
    st.markdown('<div style="border-top:1px solid #1F2126;margin: 0 -8px 14px -8px"></div>', unsafe_allow_html=True)

    goals = get_active_goals(user_id)
    own_count = sum(1 for g in goals if g["is_owner"])
    shared_count = len(goals) - own_count
    st.markdown(
        f'<div style="font-size:11px;color:#686B73;letter-spacing:0.06em;line-height:1.8">'
        f'<div>OWNED &nbsp;<span style="color:#AEB0B6">·</span>&nbsp; <b style="color:#fff">{own_count}</b></div>'
        f'<div>SHARED WITH YOU &nbsp;<span style="color:#AEB0B6">·</span>&nbsp; <b style="color:#fff">{shared_count}</b></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    av_class = avatar_class_for(user["username"])
    st.markdown(
        f'<div class="buddy-row" style="background:transparent;border:1px solid #1F2126;padding:10px 12px">'
        f'<div class="avatar {av_class}" style="width:30px;height:30px;font-size:11px">{initials(user["username"])}</div>'
        f'<div><div class="buddy-name" style="font-size:13px">{user["username"]}</div>'
        f'<div class="buddy-meta">SIGNED IN</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button("Log Out", use_container_width=True, key="logout_btn"):
        del st.session_state["user"]
        st.rerun()


# Normalize page label (strip the count from Inbox)
page_key = "Inbox" if page.startswith("Inbox") else page


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def goal_selector(goals, key="goal_select"):
    if not goals:
        st.markdown(
            '<div class="card" style="text-align:center;color:#686B73;padding:34px">'
            'No active goals yet. Head to <b style="color:#fff">Goals</b> to create one.'
            '</div>',
            unsafe_allow_html=True,
        )
        return None
    options = {}
    for g in goals:
        suffix = "" if g["is_owner"] else f"  ·  shared by @{g['owner_username']}"
        options[f"{g['title']}{suffix}"] = g["id"]
    label = st.selectbox("Select goal", list(options.keys()), key=key, label_visibility="collapsed")
    return options[label]


def stat_tile(label, value, unit="", color=""):
    return (
        f'<div class="stat">'
        f'<div class="label">{label}</div>'
        f'<div class="value {color}">{value}<span class="unit">{unit}</span></div>'
        f'</div>'
    )


def status_badge(completed_today, has_check_in):
    if not has_check_in:
        return '<span class="badge pending">Pending</span>'
    return '<span class="badge done">Completed</span>' if completed_today else '<span class="badge missed">Missed</span>'


# ──────────────────────────────────────────────────────────────
# PAGE: Goals
# ──────────────────────────────────────────────────────────────
def page_goals():
    page_intro(
        "01  /  YOUR GOALS",
        "What you're",
        "building toward.",
        "Create a goal, share it with a buddy, and let ZeroSkip handle the daily structure.",
    )

    with st.expander("＋  Create a new goal"):
        with st.form("create_goal_form"):
            title = st.text_input("Goal title", placeholder="e.g. Run 3x per week")
            description = st.text_area("Why does this matter?", placeholder="Optional — describe what success looks like.")
            category = st.selectbox("Category", CATEGORIES)
            submitted = st.form_submit_button("Create Goal", type="primary")
        if submitted:
            if not title.strip():
                st.error("Please enter a goal title.")
            else:
                create_goal(title.strip(), description.strip(), category, user_id)
                st.rerun()

    section("ACTIVE GOALS")

    goals = get_active_goals(user_id)
    if not goals:
        st.markdown(
            '<div class="card" style="text-align:center;color:#686B73;padding:40px">'
            'No goals yet. Create one above.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    for goal in goals:
        diff = goal["difficulty"]
        diff_label = DIFFICULTY_LABELS.get(diff, "?")
        dot_color = DIFF_DOT.get(diff, "faint")
        is_owner = bool(goal["is_owner"])
        members = get_goal_members(goal["id"])
        partner_count = len(members) - 1
        share_badge = (
            f'<span class="badge shared">Shared · {partner_count + 1} member{"s" if partner_count > 0 else ""}</span>'
            if partner_count > 0 else ""
        )
        owner_badge = (
            '<span class="badge owner">Owner</span>' if is_owner
            else f'<span class="badge owner">Shared by @{goal["owner_username"]}</span>'
        )

        col1, col2 = st.columns([6, 1.2])
        with col1:
            desc_html = (
                f'<div class="goal-desc">{goal["description"]}</div>'
                if goal.get("description") else ""
            )
            st.markdown(
                f'<div class="card-glow">'
                f'<div class="card-row" style="justify-content:space-between">'
                f'  <div class="card-row">'
                f'    <span class="dot {dot_color}"></span>'
                f'    <span class="goal-title">{goal["title"]}</span>'
                f'  </div>'
                f'  <div style="display:flex;gap:8px">{owner_badge}{share_badge}</div>'
                f'</div>'
                f'<div class="goal-meta">{goal.get("category","")} &nbsp;·&nbsp; {diff_label.upper()} LEVEL</div>'
                f'{desc_html}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
            if is_owner:
                if st.button("Manage", key=f"mng_{goal['id']}", use_container_width=True):
                    st.session_state["managing_goal"] = goal["id"]
                    st.rerun()

        # Manage panel (sharing + archive) only for owner of the goal
        if is_owner and st.session_state.get("managing_goal") == goal["id"]:
            with st.container():
                st.markdown('<div class="card" style="margin-top:-4px">', unsafe_allow_html=True)

                st.markdown('<div class="section-label" style="margin-top:0">PARTNERS</div>', unsafe_allow_html=True)
                for m in members:
                    av = avatar_class_for(m["username"])
                    you = " (you)" if m["id"] == user_id else ""
                    role_label = "OWNER" if m["role"] == "owner" else "PARTNER"
                    st.markdown(
                        f'<div class="buddy-row">'
                        f'<div class="avatar {av}">{initials(m["username"])}</div>'
                        f'<div><div class="buddy-name">@{m["username"]}{you}</div>'
                        f'<div class="buddy-meta">{role_label}</div></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                pending_invitees = get_pending_invitees(goal["id"])
                for un in pending_invitees:
                    av = avatar_class_for(un)
                    st.markdown(
                        f'<div class="buddy-row" style="opacity:0.6">'
                        f'<div class="avatar {av}">{initials(un)}</div>'
                        f'<div><div class="buddy-name">@{un}</div>'
                        f'<div class="buddy-meta">INVITED · AWAITING REPLY</div></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown('<div class="section-label" style="margin-top:18px">INVITE A PARTNER</div>', unsafe_allow_html=True)
                with st.form(f"invite_form_{goal['id']}"):
                    invitee = st.text_input("Username", placeholder="e.g. alex", key=f"inv_{goal['id']}")
                    sent = st.form_submit_button("Send invite", type="primary")
                if sent:
                    if not invitee.strip():
                        st.error("Enter a username.")
                    else:
                        try:
                            invite_partner(goal["id"], user_id, invitee.strip())
                            st.success(f"Invited @{invitee.strip().lower()}.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

                cA, cB, cC = st.columns([1, 1, 4])
                if cA.button("Done", key=f"done_{goal['id']}"):
                    st.session_state.pop("managing_goal", None)
                    st.rerun()
                if cB.button("Archive goal", key=f"arch_{goal['id']}"):
                    deactivate_goal(goal["id"])
                    st.session_state.pop("managing_goal", None)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# PAGE: Today
# ──────────────────────────────────────────────────────────────
def page_today():
    page_intro(
        "02  /  TODAY",
        "Show up.",
        "Mark it. Move on.",
        "Generate today's plan, log your check-in, and see how your buddies are doing.",
    )

    goals = get_active_goals(user_id)
    goal_id = goal_selector(goals, key="today_goal")
    if not goal_id:
        return

    goal = get_goal(goal_id)
    stats = compute_stats(goal_id, user_id)
    members = get_goal_members(goal_id)
    is_shared = len(members) > 1

    today_ci = get_check_in_for_date(goal_id, user_id)
    recent_check_ins = get_check_ins(goal_id, user_id, days=14)
    notif = get_smart_notification(stats, today_ci, recent_check_ins, members, user_id, goal_id)
    render_notification(notif)

    # ── Mood / Energy selector ─────────────────────────────
    section("HOW'S YOUR ENERGY TODAY?")
    current_mood = get_daily_mood(user_id)
    mood_cols = st.columns(len(MOOD_OPTIONS))
    for i, (key, em, label, desc) in enumerate(MOOD_OPTIONS):
        active = "active " + key if current_mood == key else ""
        with mood_cols[i]:
            if st.button(f"{em}  {label}", key=f"mood_{key}", use_container_width=True):
                save_daily_mood(user_id, key)
                st.rerun()
            st.markdown(
                f'<div class="muted" style="text-align:center;margin-top:-4px;font-size:11px">{desc}</div>',
                unsafe_allow_html=True,
            )
            if active:
                st.markdown(
                    f'<div class="time-delta {"good" if key=="high" else "ok" if key=="normal" else "bad"}" '
                    f'style="display:flex;justify-content:center;margin:6px auto 0 auto;width:fit-content">'
                    f'SELECTED</div>',
                    unsafe_allow_html=True,
                )

    section("YOUR STATS")
    c1, c2, c3 = st.columns(3)
    c1.markdown(stat_tile("Streak", stats["streak"], "d", "violet"), unsafe_allow_html=True)
    rate = stats["completion_rate"]
    c2.markdown(stat_tile("Completion", rate, "%",
                           "green" if rate >= 70 else "amber" if rate >= 40 else "rose"), unsafe_allow_html=True)
    c3.markdown(stat_tile("Consistency", stats["consistency_score"], "/100"), unsafe_allow_html=True)

    section("TODAY'S PLAN")
    existing_plan = get_plan_for_date(goal_id)
    if existing_plan:
        plan_html = existing_plan["plan_text"].replace("\n", "<br>")
        st.markdown(f'<div class="panel">{plan_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="muted" style="margin-bottom:12px">No plan generated yet for today.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Generate Plan with AI", type="primary"):
            with st.spinner("Building your plan..."):
                try:
                    plan_text = generate_daily_plan(goal, stats, mood_energy=current_mood)
                    save_plan(goal_id, plan_text)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    section("YOUR CHECK-IN")
    existing_ci = get_check_in_for_date(goal_id, user_id)
    if existing_ci and not st.session_state.get(f"editing_ci_{goal_id}"):
        badge = '<span class="badge done">Completed</span>' if existing_ci["completed"] else '<span class="badge missed">Missed</span>'
        note = f'<div style="font-size:13px;color:#AEB0B6;margin-top:8px">"{existing_ci["notes"]}"</div>' if existing_ci.get("notes") else ""

        # Time-honesty pill if both expected & actual are present
        time_html = ""
        ta = existing_ci.get("time_actual_min")
        te = existing_ci.get("time_expected_min")
        if ta is not None and te is not None and te > 0:
            ratio = ta / te
            if ratio >= 0.9:
                td_cls, td_text = "good", f"ON TIME · {ta}m / {te}m"
            elif ratio >= 0.5:
                td_cls, td_text = "ok", f"PARTIAL · {ta}m / {te}m"
            else:
                td_cls, td_text = "bad", f"SHORT · {ta}m / {te}m"
            time_html = f'<div class="time-delta {td_cls}" style="margin-top:10px;display:inline-flex">{td_text}</div>'

        mood_html = ""
        if existing_ci.get("mood_energy"):
            me = existing_ci["mood_energy"]
            em = {"low": "🪫", "normal": "⚡", "high": "🔥"}.get(me, "")
            mood_html = f'<div class="muted" style="margin-top:8px">ENERGY · {em} {me.upper()}</div>'

        st.markdown(f'<div class="card">{badge}{mood_html}{time_html}{note}</div>', unsafe_allow_html=True)
        if st.button("Edit check-in", key=f"edit_{goal_id}"):
            st.session_state[f"editing_ci_{goal_id}"] = True
            st.rerun()
    else:
        with st.form(f"check_in_form_{goal_id}"):
            completed = st.radio(
                "Did you complete today's task?",
                ["Yes, I did it!", "No, I missed it"],
                horizontal=True,
            )
            notes = st.text_input("Add a note (optional)", placeholder="What happened today?")
            st.markdown(
                '<div class="muted" style="margin-top:6px;margin-bottom:-4px">TIME HONESTY (optional)</div>',
                unsafe_allow_html=True,
            )
            tc1, tc2 = st.columns(2)
            with tc1:
                time_expected = st.number_input(
                    "Expected (min)", min_value=0, max_value=600, step=5, value=0,
                    help="How long you planned to spend",
                )
            with tc2:
                time_actual = st.number_input(
                    "Actual (min)", min_value=0, max_value=600, step=5, value=0,
                    help="How long you really spent",
                )
            submitted = st.form_submit_button("Save Check-In", type="primary")
        if submitted:
            is_done = completed.startswith("Yes")
            ta_val = int(time_actual) if time_actual > 0 else None
            te_val = int(time_expected) if time_expected > 0 else None
            save_check_in(
                goal_id, user_id, is_done, notes,
                mood_energy=current_mood,
                time_actual_min=ta_val,
                time_expected_min=te_val,
            )
            st.session_state.pop(f"editing_ci_{goal_id}", None)
            new_diff = maybe_adapt_difficulty(goal_id, user_id)
            if new_diff:
                direction = "up" if new_diff > goal["difficulty"] else "down"
                st.success(f"Saved. Difficulty adjusted {direction} to {DIFFICULTY_LABELS[new_diff]}.")
            st.rerun()

    # ── Distraction logger ─────────────────────────────────
    section("LOG A DISTRACTION")
    st.markdown(
        '<div class="muted" style="margin-bottom:8px">'
        'Slipped? Be honest. Patterns become visible only when you log them.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.form(f"distraction_form_{goal_id}", clear_on_submit=True):
        dc1, dc2 = st.columns([3, 2])
        with dc1:
            d_text = st.text_input(
                "What distracted you?",
                placeholder="e.g. scrolled instagram for 40 min",
                label_visibility="collapsed",
            )
        with dc2:
            d_when = st.selectbox(
                "When?", TIME_OF_DAY_OPTIONS, label_visibility="collapsed",
            )
        d_submit = st.form_submit_button("Log Distraction")
    if d_submit and d_text.strip():
        save_distraction(goal_id, user_id, d_text, d_when)
        st.toast("Logged. See patterns on the Progress page.", icon="📝")
        st.rerun()

    # Recent distractions (compact list)
    recent_distractions = get_distractions(goal_id, user_id, days=7)
    if recent_distractions:
        st.markdown(
            '<div class="muted" style="margin-top:14px;margin-bottom:6px">LAST 7 DAYS</div>',
            unsafe_allow_html=True,
        )
        for d in recent_distractions[:5]:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:14px;padding:8px 0;border-bottom:1px solid #1F2126">'
                f'<span style="color:#686B73;font-size:11px;width:90px;letter-spacing:0.04em">{d["log_date"]}</span>'
                f'<span class="badge missed">{d["time_of_day"]}</span>'
                f'<span style="color:#AEB0B6;font-size:13px">{d["distraction_text"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Share streak card ──────────────────────────────────
    if stats["streak"] > 0:
        section("SHARE YOUR STREAK")
        st.markdown(
            '<div class="share-hint" style="margin-bottom:10px">'
            f"You've been showing up for <b>{stats['streak']}</b> day{'s' if stats['streak']!=1 else ''}. "
            "Download the card and post it — accountability loves an audience."
            '</div>',
            unsafe_allow_html=True,
        )
        try:
            card_bytes = generate_streak_card_png(
                user["username"], stats["streak"], goal["title"],
            )
            st.download_button(
                label="Download Streak Card (PNG)",
                data=card_bytes,
                file_name=f"zeroskip-streak-{stats['streak']}d-{user['username']}.png",
                mime="image/png",
                type="primary",
            )
            st.image(card_bytes, width=320)
        except Exception as e:
            st.markdown(
                f'<div class="muted">Card unavailable: {e}</div>',
                unsafe_allow_html=True,
            )

    if is_shared:
        section("BUDDY STATUS · TODAY")
        for m in members:
            if m["id"] == user_id:
                continue
            their_ci = get_check_in_for_date(goal_id, m["id"])
            their_stats = compute_stats(goal_id, m["id"])
            badge_html = (
                '<span class="badge done">Completed</span>' if their_ci and their_ci["completed"]
                else '<span class="badge missed">Missed</span>' if their_ci
                else '<span class="badge pending">Pending</span>'
            )
            av = avatar_class_for(m["username"])
            st.markdown(
                f'<div class="buddy-row" style="justify-content:space-between">'
                f'<div style="display:flex;align-items:center;gap:12px">'
                f'<div class="avatar {av}">{initials(m["username"])}</div>'
                f'<div><div class="buddy-name">@{m["username"]}</div>'
                f'<div class="buddy-meta">STREAK · {their_stats["streak"]}D &nbsp;·&nbsp; {their_stats["completion_rate"]}% RATE</div></div>'
                f'</div>'
                f'<div>{badge_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────
# PAGE: Progress
# ──────────────────────────────────────────────────────────────
def page_progress():
    page_intro(
        "03  /  PROGRESS",
        "The numbers",
        "don't lie.",
        "Last 30 days. Your streak, completion rate, and consistency — versus your buddies.",
    )

    goals = get_active_goals(user_id)
    goal_id = goal_selector(goals, key="prog_goal")
    if not goal_id:
        return

    members = get_goal_members(goal_id)
    is_shared = len(members) > 1

    section("YOUR STATS")
    stats = compute_stats(goal_id, user_id)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_tile("Streak", stats["streak"], "d", "violet"), unsafe_allow_html=True)
    rate = stats["completion_rate"]
    rc = "green" if rate >= 70 else "amber" if rate >= 40 else "rose"
    c2.markdown(stat_tile("Completion", rate, "%", rc), unsafe_allow_html=True)
    score = stats["consistency_score"]
    sc = "green" if score >= 70 else "amber" if score >= 40 else "rose"
    c3.markdown(stat_tile("Consistency", score, "/100", sc), unsafe_allow_html=True)
    c4.markdown(stat_tile("Missed", stats["missed_days"], "d", "rose"), unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="muted" style="margin-bottom:6px">COMPLETION</div>', unsafe_allow_html=True)
    st.progress(min(100, int(stats["completion_rate"])))
    st.markdown('<div class="muted" style="margin-bottom:6px;margin-top:14px">CONSISTENCY</div>', unsafe_allow_html=True)
    st.progress(min(100, int(stats["consistency_score"])))

    if is_shared:
        section("HEAD TO HEAD")
        cols = st.columns(len(members))
        for i, m in enumerate(members):
            their_stats = compute_stats(goal_id, m["id"])
            av = avatar_class_for(m["username"])
            you_tag = ' <span class="muted" style="margin-left:6px">YOU</span>' if m["id"] == user_id else ""
            cols[i].markdown(
                f'<div class="card">'
                f'<div class="buddy-row" style="margin-bottom:10px">'
                f'<div class="avatar {av}" style="width:32px;height:32px;font-size:11px">{initials(m["username"])}</div>'
                f'<div class="buddy-name">@{m["username"]}{you_tag}</div></div>'
                f'<div class="muted">STREAK</div>'
                f'<div style="font-size:24px;font-weight:700;margin-bottom:8px">{their_stats["streak"]}<span class="unit" style="font-size:12px;color:#686B73"> days</span></div>'
                f'<div class="muted">COMPLETION</div>'
                f'<div style="font-size:18px;font-weight:600">{their_stats["completion_rate"]}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Distraction insights ──────────────────────────────
    section("DISTRACTION PATTERNS")
    insights = get_distraction_insights(goal_id, user_id, days=30)
    if insights["total"] == 0:
        st.markdown(
            '<div class="card" style="text-align:center;color:#686B73;padding:28px">'
            'No distractions logged in the last 30 days. Log them on the Today page when you slip — '
            'patterns and insights will appear here.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        top_sources = insights["top_sources"][:6]
        max_count = top_sources[0][1] if top_sources else 1
        st.markdown(
            f'<div class="muted" style="margin-bottom:8px">'
            f'TOP SOURCES · last 30d · {insights["total"]} total</div>',
            unsafe_allow_html=True,
        )
        rows_html = ""
        for label, count in top_sources:
            pct = int((count / max_count) * 100) if max_count else 0
            rows_html += (
                '<div class="distraction-bar-row">'
                f'<div class="distraction-bar-label">{label}</div>'
                '<div class="distraction-bar-track">'
                f'<div class="distraction-bar-fill" style="width:{pct}%"></div>'
                '</div>'
                f'<div class="distraction-count">{count}</div>'
                '</div>'
            )
        st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)

        # By time of day
        time_rows = insights.get("by_time", {})
        if time_rows:
            tmax = max(time_rows.values())
            tparts = ""
            for t_label, t_count in time_rows.items():
                tpct = int((t_count / tmax) * 100) if tmax else 0
                tparts += (
                    '<div class="distraction-bar-row">'
                    f'<div class="distraction-bar-label">{t_label}</div>'
                    '<div class="distraction-bar-track">'
                    f'<div class="distraction-bar-fill" style="width:{tpct}%"></div>'
                    '</div>'
                    f'<div class="distraction-count">{t_count}</div>'
                    '</div>'
                )
            st.markdown(
                '<div class="muted" style="margin-top:18px;margin-bottom:8px">WHEN IT HAPPENS</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="card">{tparts}</div>', unsafe_allow_html=True)

        # AI insight
        if st.button("Get AI Insight", key="distraction_ai_btn", type="primary"):
            with st.spinner("Reading your slip patterns..."):
                try:
                    di_recent = get_check_ins(goal_id, user_id, days=30)
                    insight_text = generate_distraction_insight(goal, insights, di_recent)
                    insight_html = insight_text.replace("\n", "<br>")
                    st.markdown(
                        f'<div class="panel teal" style="margin-top:12px">{insight_html}</div>',
                        unsafe_allow_html=True,
                    )
                except ValueError as e:
                    st.error(str(e))

    section("CALENDAR")
    cal_check_ins = get_check_ins(goal_id, user_id, days=120)
    if not cal_check_ins:
        st.markdown(
            '<div class="card" style="text-align:center;color:#686B73;padding:36px">'
            'No check-ins yet — your calendar will light up as you log days.'
            '</div>',
            unsafe_allow_html=True,
        )
        return
    render_calendar_heatmap(cal_check_ins, weeks=14)

    section("CHECK-IN HISTORY")
    check_ins = get_check_ins(goal_id, user_id, days=30)
    if not check_ins:
        st.markdown('<div class="muted">No recent check-ins.</div>', unsafe_allow_html=True)
        return
    for ci in check_ins:
        cls = "done" if ci["completed"] else "missed"
        label = "Completed" if ci["completed"] else "Missed"
        note_html = f'<span style="color:#686B73;font-size:12px;margin-left:12px">{ci["notes"]}</span>' if ci.get("notes") else ""
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:14px;padding:10px 0;border-bottom:1px solid #1F2126">'
            f'<span style="color:#686B73;font-size:12px;width:90px;letter-spacing:0.04em">{ci["check_in_date"]}</span>'
            f'<span class="badge {cls}">{label}</span>'
            f'{note_html}</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────
# PAGE: AI Feedback
# ──────────────────────────────────────────────────────────────
def page_ai_feedback():
    page_intro(
        "04  /  AI FEEDBACK",
        "Honest coaching.",
        "Built on your real data.",
        "Claude reads your last 14 days and tells you exactly where you're slipping — and what to fix.",
    )

    goals = get_active_goals(user_id)
    goal_id = goal_selector(goals, key="fb_goal")
    if not goal_id:
        return

    goal = get_goal(goal_id)
    stats = compute_stats(goal_id, user_id)
    check_ins = get_check_ins(goal_id, user_id, days=14)

    diff = goal["difficulty"]
    diff_label = DIFFICULTY_LABELS.get(diff, "?")

    section("AT A GLANCE")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_tile("Streak", stats["streak"], "d", "violet"), unsafe_allow_html=True)
    rate = stats["completion_rate"]
    rc = "green" if rate >= 70 else "amber" if rate >= 40 else "rose"
    c2.markdown(stat_tile("Completion", rate, "%", rc), unsafe_allow_html=True)
    score = stats["consistency_score"]
    sc = "green" if score >= 70 else "amber" if score >= 40 else "rose"
    c3.markdown(stat_tile("Consistency", score, "/100", sc), unsafe_allow_html=True)
    c4.markdown(
        f'<div class="stat"><div class="label">Difficulty</div>'
        f'<div class="value" style="font-size:20px;color:var(--{DIFF_DOT.get(diff,"violet")})">{diff_label}</div></div>',
        unsafe_allow_html=True,
    )

    if not check_ins:
        st.markdown(
            '<div class="card" style="margin-top:18px;color:#686B73">'
            'Complete at least one check-in to unlock AI feedback.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    if st.button("Get AI Feedback", type="primary"):
        with st.spinner("Analyzing your behavior patterns..."):
            try:
                feedback = generate_feedback(goal, stats, check_ins)
                fb_html = feedback.replace("\n", "<br>")
                st.markdown(f'<div class="panel teal" style="margin-top:18px">{fb_html}</div>', unsafe_allow_html=True)
            except ValueError as e:
                st.error(str(e))


# ──────────────────────────────────────────────────────────────
# PAGE: Inbox
# ──────────────────────────────────────────────────────────────
def page_inbox():
    page_intro(
        "05  /  INBOX",
        "Goal invitations,",
        "from your people.",
        "Accept to share a goal — both of you can check in independently and see each other's progress.",
    )

    invites = get_pending_invites(user_id)
    if not invites:
        st.markdown(
            '<div class="card" style="text-align:center;color:#686B73;padding:42px">'
            'No pending invites. To get one, ask a friend to share a goal with @<b style="color:#fff">' + user["username"] + '</b>.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    for inv in invites:
        av = avatar_class_for(inv["inviter_username"])
        desc = f'<div class="goal-desc">{inv["description"]}</div>' if inv.get("description") else ""
        st.markdown(
            f'<div class="card-glow">'
            f'<div class="card-row" style="justify-content:space-between">'
            f'<div class="card-row">'
            f'<div class="avatar {av}">{initials(inv["inviter_username"])}</div>'
            f'<div><div class="buddy-meta">@{inv["inviter_username"]} INVITED YOU</div>'
            f'<div class="goal-title">{inv["title"]}</div></div>'
            f'</div>'
            f'<span class="badge shared">Pending</span>'
            f'</div>'
            f'<div class="goal-meta" style="margin-top:8px">{inv.get("category", "")}</div>'
            f'{desc}'
            f'</div>',
            unsafe_allow_html=True,
        )
        a, b, _ = st.columns([1, 1, 4])
        if a.button("Accept", key=f"acc_{inv['invite_id']}", type="primary"):
            respond_to_invite(inv["invite_id"], user_id, accept=True)
            st.rerun()
        if b.button("Decline", key=f"dec_{inv['invite_id']}"):
            respond_to_invite(inv["invite_id"], user_id, accept=False)
            st.rerun()


if page_key == "Goals":
    page_goals()
elif page_key == "Today":
    page_today()
elif page_key == "Progress":
    page_progress()
elif page_key == "AI Feedback":
    page_ai_feedback()
elif page_key == "Inbox":
    page_inbox()
