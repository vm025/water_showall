"""Tracking Every Drop - landing page with visitor logging to Google Sheets."""
from contextlib import nullcontext
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Tracking Every Drop", page_icon="📊", layout="centered")

SHEET_NAME = "visitor2water"
IST = ZoneInfo("Asia/Kolkata")
HEADERS = ["Serial No", "IP Address", "Timestamp (IST)", "Button Clicked"]

LINKS = {
    "meter":    ("Water Meter Reading",   "https://meter-oct2026.streamlit.app/"),
    "tanker":   ("Tanker Arrival",        "https://tanker-water-dom.streamlit.app/"),
    "bwssb":    ("Consumption (BWSSB)",   "https://graph-2026.streamlit.app/"),
    "usage":    ("Tanker Usage",          "https://dashboard-wtanker.netlify.app/"),
}

# LOGGING flag lives in .streamlit/secrets.toml (defaults to False if missing)
try:
    LOGGING = bool(st.secrets.get("LOGGING", False))
except Exception:
    LOGGING = False

# ----------------------------------------------------------------------------
# Optional page-view analytics (community package: streamlit-analytics2)
# ----------------------------------------------------------------------------
if LOGGING:
    try:
        from importlib import import_module
        streamlit_analytics = import_module("streamlit_analytics2")
        analytics_ctx = streamlit_analytics.track()
    except Exception:
        analytics_ctx = nullcontext()
else:
    analytics_ctx = nullcontext()

# ----------------------------------------------------------------------------
# Helpers: visitor info + Google Sheet logging
# ----------------------------------------------------------------------------
def get_ip() -> str:
    """Best-effort visitor IP: proxy headers first, then the raw connection IP."""
    try:
        h = st.context.headers
        for name in ("X-Forwarded-For", "X-Real-Ip", "CF-Connecting-IP", "True-Client-IP"):
            val = (h.get(name) or "").split(",")[0].strip()
            if val:
                return val
    except Exception:
        pass
    try:
        ip = st.context.ip_address        # Streamlit >= 1.45; None on localhost
        if ip:
            return ip
    except Exception:
        pass
    return "unknown"


@st.cache_resource(show_spinner=False)
def get_sheet():
    import gspread
    from google.oauth2.service_account import Credentials

    info = dict(st.secrets["gcp_service_account"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    client = gspread.authorize(Credentials.from_service_account_info(info, scopes=scopes))
    try:
        # optional: SHEET_ID in secrets opens by ID (no Drive API needed)
        sheet_id = st.secrets.get("SHEET_ID", "")
        sh = client.open_by_key(sheet_id) if sheet_id else client.open(SHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        raise RuntimeError(
            f"Spreadsheet '{SHEET_NAME}' not found. Share it (Editor access) with "
            f"{info.get('client_email', 'the service account')} and check the name.")
    return sh.sheet1


def log_visit(button_label: str) -> None:
    """Append one row to the sheet. Never lets a logging error break the app."""
    if not LOGGING:
        return
    try:
        ws = get_sheet()
        col = ws.col_values(1)
        if not col:                       # empty sheet -> write header
            ws.append_row(HEADERS)
            col = [HEADERS[0]]
        serial = len(col)                 # header counts as 1, so next serial = len
        ts = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([serial, get_ip(), ts, button_label],
                      value_input_option="USER_ENTERED")
    except Exception as e:
        st.session_state["log_error"] = f"{type(e).__name__}: {e}"


# ----------------------------------------------------------------------------
# Styling  (black / gold / light magenta / orange)
# ----------------------------------------------------------------------------
GOLD, ORANGE, MAGENTA = "#D4AF37", "#E8872B", "#E7A6D9"

st.markdown(f"""
<style>
.stApp {{ background: radial-gradient(circle at top, #1b1410 0%, #000000 70%); }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2rem; max-width: 640px; }}

.app-title {{
    text-align:center; font-size:2.3rem; font-weight:800; letter-spacing:.5px;
    color:{GOLD}; margin-bottom:.1rem; text-shadow:0 0 14px rgba(212,175,55,.35);
}}
.app-tag {{ text-align:center; color:{MAGENTA}; margin-bottom:1.6rem; font-size:.95rem; }}

/* panels */
.st-key-panel1, .st-key-panel2 {{
    background:#111; border-radius:18px; padding:1.1rem 1.2rem 1.3rem;
}}
.st-key-panel1 {{ border:2px solid {ORANGE} !important; box-shadow:0 0 18px rgba(232,135,43,.18); }}
.st-key-panel2 {{ border:2px solid {MAGENTA} !important; box-shadow:0 0 18px rgba(231,166,217,.18); }}

.panel-title {{ font-size:1.45rem; font-weight:700; margin:0; }}
.p1 {{ color:{GOLD}; }}  .p2 {{ color:{MAGENTA}; }}
.sub {{ font-size:1rem; font-weight:700; margin:.2rem 0 1rem; }}
.sub-red  {{ color:#FF1A1A; }}
.sub-blue {{ color:#1E90FF; }}

/* keep the two buttons on one line, even on narrow phone screens */
.st-key-panel1 [data-testid="stHorizontalBlock"],
.st-key-panel2 [data-testid="stHorizontalBlock"] {{
    flex-wrap:nowrap !important; gap:.6rem !important;
}}
.st-key-panel1 [data-testid="stColumn"],
.st-key-panel2 [data-testid="stColumn"] {{
    flex:1 1 0 !important; min-width:0 !important; width:auto !important;
}}
.stButton > button {{ min-height:4rem; line-height:1.25; }}
.stButton > button p {{ white-space:normal; text-align:center; }}

/* buttons */
.stButton > button, .stLinkButton > a {{
    width:100%; padding:.8rem 1rem; border-radius:12px; font-weight:700;
    font-size:1.05rem; transition:transform .1s, filter .15s;
}}
.stButton > button:hover, .stLinkButton > a:hover {{ transform:translateY(-2px); filter:brightness(1.12); }}

.st-key-btn_meter button, .st-key-btn_tanker button {{
    background:#0B5559 !important; color:#fff !important; border:1.5px solid {GOLD} !important;
}}
.st-key-btn_bwssb button, .st-key-btn_usage button {{
    background:#B9A2E3 !important; color:#1a1030 !important; border:1.5px solid {ORANGE} !important;
}}
.st-key-fallback {{
    border:1px dashed {GOLD}; border-radius:12px; padding:.8rem; margin-top:1.2rem; background:#14110a;
}}
.st-key-fallback p {{ color:{GOLD}; }}
.st-key-fallback a {{ background:{GOLD} !important; color:#000 !important; border:none !important; }}
.foot {{ text-align:center; color:#7a7a7a; font-size:.75rem; margin-top:1.5rem; }}

@media (max-width:480px) {{
    .app-title {{ font-size:1.8rem; }}
    .panel-title {{ font-size:1.25rem; }}
    .stButton > button {{ font-size:.9rem; padding:.6rem .4rem; }}
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# App body
# ----------------------------------------------------------------------------
with analytics_ctx:
    st.markdown('<div class="app-title">💧 Tracking Every Drop</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-tag">Water resource monitoring made simple</div>', unsafe_allow_html=True)

    # log the page view once per browser session
    if not st.session_state.get("view_logged"):
        st.session_state["view_logged"] = True
        log_visit("Page view")

    def handle_click(key: str):
        label, url = LINKS[key]
        log_visit(label)
        st.session_state["pending"] = (label, url)

    # ---- Panel 1 ----
    with st.container(key="panel1", border=True):
        st.markdown('<p class="panel-title p1">Water Resource Management</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub sub-red">Only for the Security team</p>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2, gap="small")
        with col_a:
            if st.button(LINKS["meter"][0], key="btn_meter"):
                handle_click("meter")
        with col_b:
            if st.button(LINKS["tanker"][0], key="btn_tanker"):
                handle_click("tanker")

    st.write("")

    # ---- Panel 2 ----
    with st.container(key="panel2", border=True):
        st.markdown('<p class="panel-title p2">Dashboard (Graph)</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub sub-blue">For Other Users</p>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2, gap="small")
        with col_a:
            if st.button(LINKS["bwssb"][0], key="btn_bwssb"):
                handle_click("bwssb")
        with col_b:
            if st.button(LINKS["usage"][0], key="btn_usage"):
                handle_click("usage")

    # ---- Redirect (auto-open + guaranteed fallback link) ----
    if "pending" in st.session_state:
        label, url = st.session_state["pending"]
        # st.html is not iframed, so the script runs in the main page itself
        st.html(
            f"<script>try{{window.open('{url}','_blank');}}catch(e){{}}</script>",
            unsafe_allow_javascript=True,
        )
        with st.container(key="fallback"):
            st.markdown(f"If **{label}** didn't open automatically, tap below:")
            st.link_button(f"Open {label} ↗", url)

    if LOGGING and "log_error" in st.session_state:
        st.warning(f"Logging problem: {st.session_state['log_error']}")

    st.markdown('<div class="foot">Tracking Every Drop · Every litre counts</div>',
                unsafe_allow_html=True)