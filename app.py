"""
FireHox WhatsApp Outreach Tool - Professional Streamlit UI
FIXED: Singleton Lock Issue with Open-Close-Reopen Architecture
3-Step Wizard: Connection → Upload & Clean → Send Campaign
"""

import streamlit as st
import pandas as pd
import os
import time
import random
import subprocess
import sys
from datetime import datetime
from whatsapp_engine import WhatsAppBot

# ==================== CLOUD DEPLOYMENT FIX ====================
def install_playwright_browsers():
    """Ensure Playwright browsers are installed on Streamlit Cloud."""
    try:
        # Check if we are running in a cloud environment (typically Linux)
        if sys.platform.startswith("linux"):
            # We don't want to run this every time, so we check for a marker or cache
            # Streamlit Cloud cache is usually in ~/.cache/ms-playwright
            marker_file = "/tmp/playwright_installed.txt"
            if not os.path.exists(marker_file):
                with st.spinner("🚀 First-time Setup: Installing WhatsApp Engine components... (May take 1 minute)"):
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                    # Note: 'install-deps' requires sudo, which we don't have.
                    # System deps are handled by packages.txt
                    with open(marker_file, "w") as f:
                        f.write("Installed")
                st.success("✅ Engine components installed successfully!")
    except Exception as e:
        st.error(f"⚠️ Setup Error: {str(e)}")

# Run the installer at startup
install_playwright_browsers()
import io

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="FireHox WhatsApp Outreach",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CUSTOM CSS - MODERN DARK THEME ====================
st.markdown("""
<style>
    /* ========== GOOGLE FONT ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* ========== DESIGN TOKENS ========== */
    :root {
        --bg-primary: #141414;
        --bg-surface: #1E1E1E;
        --bg-elevated: #2A2A2A;
        --bg-input: #1A1A1A;
        --text-primary: #FAFAFA;
        --text-secondary: #A0A0A0;
        --text-muted: #666666;
        --accent: #FAFAFA;
        --accent-dim: #888888;
        --border: #333333;
        --border-light: #2A2A2A;
        --success: #4ADE80;
        --success-bg: rgba(74, 222, 128, 0.10);
        --error: #F87171;
        --error-bg: rgba(248, 113, 113, 0.10);
        --warning: #FBBF24;
        --warning-bg: rgba(251, 191, 36, 0.10);
        --info: #60A5FA;
        --info-bg: rgba(96, 165, 250, 0.10);
        --radius: 8px;
        --radius-lg: 12px;
    }

    /* ========== GLOBAL — Removed !important to prevent breaking icon fonts ========== */
    * { 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
    }

    /* Target specific Streamlit elements for typography to avoid breaking icons */
    .stApp, .stMarkdown, p, div, span, label, input, button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* EXPLICITLY do not force Inter on icons */
    [data-testid="stIcon"] *, 
    [class*="icon"] *,
    svg, svg * {
        font-family: inherit !important;
    }

    .stApp { background: var(--bg-primary) !important; }

    .main .block-container {
        padding: 2rem 2.5rem;
        max-width: 1200px;
        background-color: var(--bg-primary) !important;
    }

    /* ========== TYPOGRAPHY — Scoped to avoid bleeding into buttons/alerts ========== */
    .stMarkdown p, .stMarkdown span, .stMarkdown li,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    .stText, [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li {
        color: var(--text-primary) !important;
    }

    /* Labels for inputs */
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] p {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    small { color: var(--text-secondary) !important; }
    code { color: var(--text-primary) !important; background: var(--bg-elevated) !important; border-radius: 4px; padding: 2px 6px; }

    /* ========== HEADER ========== */
    .main-header {
        font-size: 2.8rem;
        font-weight: 900;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        background: none !important;
        text-align: center;
        margin-bottom: 0.25rem;
        letter-spacing: -1.5px;
        line-height: 1.1;
    }

    .sub-header {
        text-align: center;
        color: var(--text-secondary) !important;
        font-size: 1.05rem;
        font-weight: 500;
        margin-bottom: 2rem;
        letter-spacing: 0.3px;
    }

    .step-header {
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--text-primary) !important;
        margin: 2rem 0 1.25rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--border);
        letter-spacing: -0.5px;
    }

    /* ========== STEP INDICATORS ========== */
    .step-indicator {
        padding: 0.85rem 1.25rem;
        border-radius: var(--radius);
        text-align: center;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        letter-spacing: 0.3px;
        transition: all 0.25s ease;
    }

    .step-active {
        background: var(--text-primary) !important;
        color: var(--bg-primary) !important;
        -webkit-text-fill-color: var(--bg-primary) !important;
    }

    .step-inactive {
        background: var(--bg-surface) !important;
        color: var(--text-muted) !important;
        -webkit-text-fill-color: var(--text-muted) !important;
        border: 1px solid var(--border);
    }

    /* ========== STATUS BOXES ========== */
    .info-box {
        background: var(--info-bg) !important;
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        border-left: 4px solid var(--info);
        margin: 1.25rem 0;
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .info-box strong { color: var(--info) !important; font-weight: 700; }

    .warning-box {
        background: var(--warning-bg) !important;
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        border-left: 4px solid var(--warning);
        margin: 1.25rem 0;
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .warning-box strong { color: var(--warning) !important; font-weight: 700; }

    .success-box {
        background: var(--success-bg) !important;
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        border-left: 4px solid var(--success);
        margin: 1.25rem 0;
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .success-box strong { color: var(--success) !important; font-weight: 700; }

    .error-box {
        background: var(--error-bg) !important;
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        border-left: 4px solid var(--error);
        margin: 1.25rem 0;
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        line-height: 1.8;
    }
    .error-box strong { color: var(--error) !important; font-weight: 700; }

    /* ========== DETECTION BOX ========== */
    .detection-box {
        background: var(--bg-surface) !important;
        padding: 1rem 1.25rem;
        border-radius: var(--radius);
        border-left: 3px solid var(--accent-dim);
        margin-bottom: 0.75rem;
    }
    .detection-box strong { color: var(--text-primary) !important; }
    .detection-box small { color: var(--text-secondary) !important; }

    /* ========== BUTTONS — Using Streamlit's actual data-testid selectors ========== */
    /* Default button style (dark surface) */
    .stButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-minimal"] {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 2rem !important;
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        letter-spacing: 0.3px !important;
    }

    .stButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background: var(--bg-elevated) !important;
        border-color: var(--text-secondary) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }

    /* PRIMARY button — white bg, BLACK text */
    button[data-testid="baseButton-primary"] {
        background: var(--text-primary) !important;
        color: var(--bg-primary) !important;
        border: 1px solid var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 2rem !important;
        border-radius: var(--radius) !important;
        box-shadow: none !important;
        letter-spacing: 0.3px !important;
    }

    /* Force ALL text inside primary button to be dark */
    button[data-testid="baseButton-primary"] *,
    button[data-testid="baseButton-primary"] p,
    button[data-testid="baseButton-primary"] span,
    button[data-testid="baseButton-primary"] div {
        color: var(--bg-primary) !important;
        -webkit-text-fill-color: var(--bg-primary) !important;
    }

    button[data-testid="baseButton-primary"]:hover {
        background: #E0E0E0 !important;
        border-color: #E0E0E0 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }

    /* Disabled buttons */
    .stButton > button:disabled,
    button[data-testid="baseButton-primary"]:disabled,
    button[data-testid="baseButton-secondary"]:disabled {
        background: var(--bg-surface) !important;
        color: var(--text-muted) !important;
        border-color: var(--border) !important;
        opacity: 0.5 !important;
        transform: none !important;
    }

    button[data-testid="baseButton-primary"]:disabled *,
    button[data-testid="baseButton-primary"]:disabled span,
    button[data-testid="baseButton-primary"]:disabled p {
        color: var(--text-muted) !important;
        -webkit-text-fill-color: var(--text-muted) !important;
    }

    /* ========== PROGRESS BAR ========== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--text-secondary) 0%, var(--text-primary) 100%) !important;
        height: 6px;
        border-radius: 3px;
    }

    .stProgress > div > div > div {
        background: var(--bg-elevated) !important;
        border-radius: 3px;
    }

    /* ========== METRICS ========== */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    [data-testid="stMetricDelta"] {
        color: var(--success) !important;
    }

    [data-testid="stMetric"] {
        background: var(--bg-surface) !important;
        padding: 1rem 1.25rem !important;
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--border) !important;
    }

    /* ========== DATAFRAME ========== */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg);
        overflow: hidden;
    }

    .dataframe {
        border: none !important;
        border-radius: var(--radius-lg);
        overflow: hidden;
        font-size: 0.9rem;
    }

    .dataframe th {
        background-color: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        padding: 10px 14px !important;
        border-bottom: 1px solid var(--border) !important;
    }

    .dataframe td {
        padding: 8px 14px !important;
        color: var(--text-primary) !important;
        background-color: var(--bg-surface) !important;
        border-bottom: 1px solid var(--border-light) !important;
    }

    .dataframe tr:hover td {
        background-color: var(--bg-elevated) !important;
    }

    /* ========== FILE UPLOADER ========== */
    [data-testid="stFileUploader"] {
        background-color: var(--bg-surface) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-lg);
        padding: 2rem;
        transition: border-color 0.2s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--text-secondary) !important;
    }

    [data-testid="stFileUploader"] label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    [data-testid="stFileUploader"] small {
        color: var(--text-secondary) !important;
    }

    [data-testid="stFileUploader"] button {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }

    /* ========== SELECT / TEXT INPUT ========== */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextInput"] > div > div > input,
    [data-baseweb="select"] > div,
    [data-baseweb="input"] input {
        background-color: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }

    [data-testid="stSelectbox"] label,
    [data-testid="stTextInput"] label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    /* Selected value text inside select */
    [data-baseweb="select"] [data-testid="stMarkdownContainer"],
    [data-baseweb="select"] span,
    [data-baseweb="select"] div[class*="valueContainer"] * {
        color: var(--text-primary) !important;
    }

    /* Dropdown menu */
    [data-baseweb="popover"] {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
    }

    [data-baseweb="menu"] {
        background: var(--bg-surface) !important;
    }

    [role="option"] {
        color: var(--text-primary) !important;
    }

    [role="option"]:hover,
    [aria-selected="true"] {
        background: var(--bg-elevated) !important;
    }

    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-surface);
        border-radius: var(--radius);
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1rem;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
    }

    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* ========== DIVIDER ========== */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: var(--border);
    }

    /* ========== STREAMLIT ALERTS — Ensure readable text ========== */
    [data-testid="stAlert"] {
        border-radius: var(--radius) !important;
        font-weight: 500 !important;
        border: none !important;
    }

    /* Success alert */
    [data-testid="stAlert"][data-baseweb] .st-emotion-cache-1sno8jx,
    .stSuccess, div[data-testid="stNotification"][data-type="success"] {
        background-color: var(--success-bg) !important;
        border-left: 3px solid var(--success) !important;
    }
    .stSuccess p, [data-testid="stNotification"][data-type="success"] p,
    .stSuccess div, .stSuccess span {
        color: var(--success) !important;
    }

    /* Info alert */
    .stInfo, div[data-testid="stNotification"][data-type="info"] {
        background-color: var(--info-bg) !important;
        border-left: 3px solid var(--info) !important;
    }
    .stInfo p, [data-testid="stNotification"][data-type="info"] p,
    .stInfo div, .stInfo span {
        color: var(--info) !important;
    }

    /* Warning alert */
    .stWarning, div[data-testid="stNotification"][data-type="warning"] {
        background-color: var(--warning-bg) !important;
        border-left: 3px solid var(--warning) !important;
    }
    .stWarning p, [data-testid="stNotification"][data-type="warning"] p,
    .stWarning div, .stWarning span {
        color: var(--warning) !important;
    }

    /* Error alert */
    .stError, div[data-testid="stNotification"][data-type="error"] {
        background-color: var(--error-bg) !important;
        border-left: 3px solid var(--error) !important;
    }
    .stError p, [data-testid="stNotification"][data-type="error"] p,
    .stError div, .stError span {
        color: var(--error) !important;
    }

    /* ========== ALERT ICONS — Re-enabled and styled properly ========== */
    [data-testid="stAlert"] svg {
        fill: currentColor !important;
    }

    /* ========== EXPANDER — Simplified to prevent layout break ========== */
    [data-testid="stExpander"] {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        margin-bottom: 1rem !important;
    }

    [data-testid="stExpander"] summary {
        color: var(--text-primary) !important;
        padding: 0.5rem 1rem !important;
    }

    [data-testid="stExpander"] summary:hover {
        background-color: var(--bg-elevated) !important;
    }

    /* Let Streamlit handle the internal flex of the summary, just fix the text colors */
    [data-testid="stExpander"] summary div[data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
        margin: 0 !important;
        font-weight: 600 !important;
    }

    [data-testid="stExpanderDetails"] {
        border-top: 1px solid var(--border) !important;
        padding: 1.5rem !important;
        background-color: var(--bg-primary) !important;
    }

    /* ========== METRICS PREVENT OVERLAP ========== */
    [data-testid="stMetricValue"] {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* ========== SPINNER ========== */
    .stSpinner > div {
        border-top-color: var(--text-primary) !important;
    }

    .stSpinner > div > span {
        color: var(--text-secondary) !important;
    }

    /* ========== DOWNLOAD BUTTON ========== */
    [data-testid="stDownloadButton"] > button {
        background: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }

    [data-testid="stDownloadButton"] > button:hover {
        background: var(--bg-elevated) !important;
        border-color: var(--text-secondary) !important;
    }

    [data-testid="stDownloadButton"] > button span,
    [data-testid="stDownloadButton"] > button p {
        color: var(--text-primary) !important;
    }

    /* ========== FOOTER ========== */
    .footer-text {
        text-align: center;
        color: var(--text-muted) !important;
        font-size: 0.85rem;
        padding: 1.5rem;
        margin-top: 3rem;
        border-top: 1px solid var(--border);
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    .footer-text strong { color: var(--text-secondary) !important; font-weight: 500; }

    /* ========== LIVE CONSOLE ========== */
    .live-console {
        background-color: #0A0A0A !important;
        padding: 1.25rem;
        border-radius: var(--radius-lg);
        font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace !important;
        font-size: 0.85rem;
        line-height: 1.7;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid var(--border);
        margin: 1.25rem 0;
    }

    .console-success { color: var(--success) !important; }
    .console-error { color: var(--error) !important; }
    .console-info { color: var(--info) !important; }
    .console-warning { color: var(--warning) !important; }

    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] { background: var(--bg-surface) !important; }

    /* ========== TOOLTIP ========== */
    [data-testid="stTooltipIcon"] { color: var(--text-muted) !important; }

    /* ========== HELP TEXT / CAPTION ========== */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: var(--text-muted) !important;
    }

    /* ========== SELECTBOX ARROW ========== */
    [data-baseweb="select"] svg {
        fill: var(--text-secondary) !important;
    }

    /* ========== CHECKBOX / RADIO ========== */
    [data-testid="stCheckbox"] label span,
    [data-testid="stRadio"] label span {
        color: var(--text-primary) !important;
    }

    /* ========== COLUMN GAPS — Prevent overlap ========== */
    [data-testid="stHorizontalBlock"] {
        gap: 1rem !important;
    }

    [data-testid="stColumn"] {
        padding: 0 0.25rem !important;
    }

    /* ========== SUBHEADER ========== */
    .stSubheader, [data-testid="stSubheader"] {
        color: var(--text-primary) !important;
    }

    /* ========== BOTTOM TOOLBAR (Streamlit branding) ========== */
    footer, [data-testid="stToolbar"],
    .viewerBadge_container__r5tak {
        background: var(--bg-primary) !important;
    }

    /* ========== HEADER TOOLBAR (top-right) ========== */
    [data-testid="stToolbar"] button {
        color: var(--text-secondary) !important;
    }

    [data-testid="stHeader"] {
        background: var(--bg-primary) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE INITIALIZATION ====================
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'bot' not in st.session_state:
    st.session_state.bot = None
if 'browser_ready' not in st.session_state:
    st.session_state.browser_ready = False
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'data_report' not in st.session_state:
    st.session_state.data_report = None
if 'campaign_results' not in st.session_state:
    st.session_state.campaign_results = None
if 'campaign_running' not in st.session_state:
    st.session_state.campaign_running = False

# ==================== HEADER ====================
st.markdown('<h1 class="main-header">📱 FireHox WhatsApp Outreach</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Professional WhatsApp Marketing Automation with Anti-Ban Protection</p>', unsafe_allow_html=True)

# ==================== DEVICE DETECTION ====================
st.markdown("""
<script>
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
if (isMobile) {
    const root = window.parent.document.querySelector('.stApp');
    if (root) {
        root.innerHTML = `
            <div style="background-color: #141414; color: #FAFAFA; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 2rem; font-family: 'Inter', sans-serif;">
                <h1 style="font-size: 4rem; margin-bottom: 1rem;">🖥️</h1>
                <h2 style="font-weight: 800; font-size: 1.8rem; margin-bottom: 1rem;">Desktop Access Only</h2>
                <p style="color: #A0A0A0; font-size: 1rem; line-height: 1.6; max-width: 400px;">
                    This automation tool requires a desktop-grade browser to run the WhatsApp engine. 
                    Please access this link from your <strong>Windows, Mac, or Linux computer</strong>.
                </p>
                <div style="margin-top: 2rem; padding: 1rem; border: 1px solid #333; border-radius: 8px; background: #1E1E1E;">
                    <small style="color: #666;">Mobile devices are not supported for automation engines.</small>
                </div>
            </div>
        `;
    }
}
</script>
""", unsafe_allow_html=True)

# Also show a Streamlit-native warning in case JS is slow to load
st.warning("🖥️ **System Note:** This tool is designed for **Desktop Use Only**. Mobile browser automation is not supported.")

# ==================== PROGRESS INDICATORS ====================
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.step >= 1:
        st.markdown('<div class="step-indicator step-active">✅ Step 1: Connection</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-indicator step-inactive">⏳ Step 1: Connection</div>', unsafe_allow_html=True)

with col2:
    if st.session_state.step >= 2:
        st.markdown('<div class="step-indicator step-active">✅ Step 2: Upload & Clean</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-indicator step-inactive">⏳ Step 2: Upload & Clean</div>', unsafe_allow_html=True)

with col3:
    if st.session_state.step >= 3:
        st.markdown('<div class="step-indicator step-active">✅ Step 3: Send Campaign</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-indicator step-inactive">⏳ Step 3: Send Campaign</div>', unsafe_allow_html=True)

st.divider()

# ==================== STEP 1: CONNECTION (OPEN-CLOSE ARCHITECTURE) ====================
if st.session_state.step == 1:
    st.markdown('<h2 class="step-header">Step 1: Initialize & Login</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>📋 How This Works (Open-Close-Reopen Architecture):</strong><br><br>
        1️⃣ Click <strong>"🚀 Initialize & Login"</strong> below<br>
        2️⃣ A browser window will open automatically<br>
        3️⃣ <strong>Scan the QR code</strong> with your phone (if first time)<br>
        4️⃣ Wait for your chats to load completely<br>
        5️⃣ Click <strong>"✅ Login Complete"</strong> - <strong>The browser will close automatically</strong><br>
        6️⃣ Your login is now saved! Proceed to Step 2<br><br>
        <strong>⚠️ Important:</strong> The browser MUST close after login to release the lock. This is normal behavior!
    </div>
    """, unsafe_allow_html=True)
    
    # Troubleshooting section
    with st.expander("🔧 Troubleshooting - Click if you see errors"):
        st.markdown("""
        <div style="color: #FAFAFA; line-height: 1.8;">
        <strong>Common Issues & Solutions:</strong><br><br>
        
        <strong>1. "Browser is locked" Error:</strong><br>
        • Close ALL Chromium browser windows manually<br>
        • Wait 5 seconds<br>
        • Click "🔄 Reset Session" below<br>
        • Try again<br><br>
        
        <strong>2. "Chromium browser not found" Error:</strong><br>
        • Open terminal/command prompt<br>
        • Run: <code>playwright install chromium</code><br>
        • Wait for installation to complete<br>
        • Try again<br><br>
        
        <strong>3. QR Code Not Appearing:</strong><br>
        • Reset the session using the button below<br>
        • Launch browser again<br>
        • Make sure WhatsApp Web is not blocked by firewall<br><br>
        
        <strong>4. Browser Closes Immediately:</strong><br>
        • Check your internet connection<br>
        • Try resetting the session<br>
        • Ensure no antivirus is blocking Playwright
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚀 Initialize & Login", type="primary", width="stretch"):
            with st.spinner("🔄 Launching browser..."):
                bot = WhatsAppBot()
                success, message, page = bot.launch_browser()
                
                if success:
                    st.session_state.bot = bot
                    st.success(message)
                    
                    # ==================== CLOUD QR DISPLAY ====================
                    if sys.platform.startswith("linux"):
                        st.info("☁️ Headless Cloud Mode: Displaying Browser View below...")
                        qr_placeholder = st.empty()
                        status_text = st.empty()
                        
                        # Loop to show live browser view (QR Code) for 120 seconds
                        # This allows the user to scan the QR code since the browser is hidden
                        start_time = time.time()
                        SCAN_TIMEOUT = 120
                        
                        while time.time() - start_time < SCAN_TIMEOUT:
                            if not st.session_state.bot or not st.session_state.bot.page:
                                break
                            
                            try:
                                # Check if already logged in (chat list visible)
                                if st.session_state.bot.page.locator('div[data-testid="chat-list"]').count() > 0:
                                    qr_placeholder.empty()
                                    status_text.success("✅ Login detected! You can now click 'Login Complete'.")
                                    break
                                
                                # Take screenshot of current page (QR code should be there)
                                screenshot = st.session_state.bot.page.screenshot()
                                qr_placeholder.image(screenshot, caption="📸 Scan this QR Code with your phone", width=500)
                                
                                remaining = int(SCAN_TIMEOUT - (time.time() - start_time))
                                status_text.info(f"⏳ Waiting for scan... ({remaining}s remaining)")
                                time.sleep(1.5)
                            except Exception:
                                break
                    # ==========================================================

                    st.markdown("""
                    <div class="warning-box">
                        <strong>⚠️ Next Steps:</strong><br><br>
                        • <strong>Keep the browser window open</strong><br>
                        • Scan QR code if you see one<br>
                        • Wait for all chats to load<br>
                        • Then click <strong>"✅ Login Complete"</strong> below
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Display error with proper formatting
                    error_lines = message.split('\n')
                    error_html = '<br>'.join(error_lines)
                    st.markdown(f'<div class="error-box"><strong>Error:</strong><br>{error_html}</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("✅ Login Complete - Close Browser", type="secondary", width="stretch"):
            if st.session_state.bot:
                with st.spinner("🔍 Verifying login (this should be quick)..."):
                    # Verify login with shorter timeout (15 seconds)
                    logged_in, msg = st.session_state.bot.verify_login(timeout=15)
                    
                    if logged_in:
                        # CRITICAL: Close browser to release lock
                        st.session_state.bot.close_browser()
                        
                        st.session_state.browser_ready = True
                        st.session_state.bot = None  # Clear bot instance
                        st.session_state.step = 2
                        
                        st.success("✅ Login verified! Browser closed. Your session is saved!")
                        st.info("🔒 The browser has been closed to release the lock. You can now proceed to Step 2.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                        st.markdown("""
                        <div class="warning-box">
                            <strong>💡 Quick Fix:</strong><br><br>
                            If you can see your WhatsApp chats in the browser window, 
                            just use the <strong>"⚡ Skip Verification"</strong> button below instead!
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Browser is open but session state was lost (app restarted)
                st.markdown("""
                <div class="error-box">
                    <strong>❌ Session Lost</strong><br><br>
                    The app was restarted and lost connection to the browser.<br><br>
                    <strong>Solution:</strong><br>
                    1. Close the existing browser window manually<br>
                    2. Click "🚀 Initialize & Login" again<br><br>
                    <strong>OR</strong><br><br>
                    If you can see your WhatsApp chats, use the <strong>"⚡ Skip Verification"</strong> button below to proceed directly!
                </div>
                """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 Reset Session", width="stretch"):
            with st.spinner("🔄 Resetting session..."):
                bot = WhatsAppBot()
                success, msg = bot.reset_session()
                if success:
                    st.success(msg)
                    st.session_state.bot = None
                    st.session_state.browser_ready = False
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
    
    # Emergency bypass button
    st.markdown("---")
    st.markdown("""
    <div class="warning-box">
        <strong>⚡ Emergency Bypass:</strong><br><br>
        If verification keeps failing but you can SEE your WhatsApp chats in the browser window, 
        click the button below to skip verification and proceed directly to Step 2.
    </div>
    """, unsafe_allow_html=True)
    
    col_bypass1, col_bypass2, col_bypass3 = st.columns([1, 1, 1])
    with col_bypass2:
        if st.button("⚡ Skip Verification & Proceed to Step 2", type="primary", width="stretch"):
            if st.session_state.bot:
                # Close browser to release lock
                st.session_state.bot.close_browser()
                
                st.session_state.browser_ready = True
                st.session_state.bot = None  # Clear bot instance
                st.session_state.step = 2
                
                st.success("✅ Skipped verification! Browser closed. Proceeding to Step 2...")
                st.warning("⚠️ Your login session has been saved!")
                time.sleep(1)
                st.rerun()
            else:
                # Browser is open but session state was lost
                # Just proceed to Step 2 and tell user to close browser manually
                st.session_state.browser_ready = True
                st.session_state.step = 2
                
                st.success("✅ Proceeding to Step 2...")
                st.warning("⚠️ Please close the browser window manually before proceeding to Step 3!")
                time.sleep(1)
                st.rerun()

# ==================== STEP 2: UPLOAD & CLEAN (NO BROWSER) ====================
elif st.session_state.step == 2:
    st.markdown('<h2 class="step-header">Step 2: Upload & Clean Lead Data</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>📋 File Requirements:</strong><br><br>
        ✅ Supports <strong>CSV (.csv)</strong> and <strong>Excel (.xlsx)</strong> files<br>
        ✅ Must contain a column with <strong>phone numbers</strong> (e.g., "Phone", "Mobile", "Contact")<br>
        ✅ Should contain a column with <strong>business names</strong> (e.g., "Name", "Business", "Company")<br>
        ✅ Phone numbers can be in any format - we'll clean them automatically<br>
        ✅ Supports international formats and defaults to India (+91)
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📤 Upload Your Lead Data (CSV or Excel)", type=['csv', 'xlsx'], help="Upload your lead list file (CSV or Excel format)")
    
    if uploaded_file is not None:
        try:
            # Handle different file types
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                # Read CSV with encoding fallback for Excel/Windows-formatted files
                try:
                    df = pd.read_csv(uploaded_file)
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin1')
            
            st.success(f"✅ File uploaded successfully! Found **{len(df)} rows** and **{len(df.columns)} columns**.")
            
            # Column Prediction Logic
            phone_keywords = ['phone', 'mobile', 'number', 'whatsapp', 'contact']
            name_keywords = ['business', 'name', 'company', 'lead', 'client']
            
            # Predict Phone
            pred_phone = next((c for c in df.columns if any(k == c.lower() for k in phone_keywords)), None)
            if not pred_phone:
                pred_phone = next((c for c in df.columns if any(k in c.lower() for k in phone_keywords)), df.columns[0])
            
            # Predict Name (Exclude Unnamed)
            valid_name_cols = [c for c in df.columns if 'unnamed' not in c.lower()]
            pred_name = next((c for c in valid_name_cols if c.lower() in ['business name', 'name', 'business', 'company name']), None)
            if not pred_name and valid_name_cols:
                pred_name = next((c for c in valid_name_cols if any(k in c.lower() for k in name_keywords)), valid_name_cols[0])
            elif not pred_name:
                pred_name = df.columns[0]

            st.markdown("""
            <div class="detection-box">
                <strong>🔍 Intelligent Column Detection</strong><br>
                <small>We've predicted your columns below. Please verify or change them if incorrect.</small>
            </div>
            """, unsafe_allow_html=True)
            
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                final_phone_col = st.selectbox("📞 Select Phone Number Column", df.columns, index=list(df.columns).index(pred_phone) if pred_phone in df.columns else 0)
            with col_sel2:
                final_name_col = st.selectbox("👤 Select Business Name Column", df.columns, index=list(df.columns).index(pred_name) if pred_name in df.columns else 0)

            # Show raw data preview
            with st.expander("📄 View Uploaded Data Preview"):
                st.dataframe(df.head(10), width="stretch")
            
            # Country Code Input
            col_code, col_btn = st.columns([1, 2])
            with col_code:
                default_code = st.text_input("🌍 Default Country Code", value="+91", help="Code to add if missing (e.g. +1 for US)")
                # Validate country code format
                import re
                if not re.match(r'^\+\d{1,3}$', default_code):
                    st.warning("⚠️ Country code should be '+' followed by 1-3 digits (e.g. +91, +1, +44)")
            
            # Clean data button
            with col_btn:
                st.write("") # Spacer
                st.write("") # Spacer
                clean_clicked = st.button("🧹 Clean & Validate Data", type="primary", width="stretch")
            if clean_clicked:
                with st.spinner("🔄 Cleaning and validating phone numbers..."):
                    # Call clean_data as a static method with user-selected columns
                    cleaned_df, report = WhatsAppBot.clean_data(
                        df, 
                        default_country_code=default_code,
                        phone_col=final_phone_col,
                        name_col=final_name_col
                    )
                    
                    if cleaned_df is not None and not cleaned_df.empty:
                        st.session_state.cleaned_data = cleaned_df
                        st.session_state.data_report = report
                        
                        # Display report
                        st.markdown('<div class="success-box"><strong>✅ Data Cleaning Complete!</strong></div>', unsafe_allow_html=True)
                        
                        # Metrics in columns
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("📊 Total Rows", report['total_rows'])
                        with col2:
                            st.metric("✅ Valid Rows", report['valid_rows'], delta=f"+{report['valid_rows']}")
                        with col3:
                            st.metric("❌ Invalid Rows", report['invalid_rows'])
                        with col4:
                            st.metric("🗑️ Removed Rows", report['removed_rows'])
                        
                        # Additional info
                        st.info(f"📞 Phone Column: **{report['phone_column']}** | 👤 Name Column: **{report['name_column']}**")
                        
                        # Show cleaned data
                        st.markdown("### 📋 Cleaned Data Preview")
                        st.dataframe(cleaned_df.head(20), width="stretch")
                        
                        # Download cleaned data
                        csv_buffer = io.StringIO()
                        cleaned_df.to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="📥 Download Cleaned Data (CSV)",
                            data=csv_buffer.getvalue(),
                            file_name="cleaned_leads.csv",
                            mime="text/csv"
                        )
                        
                    else:
                        error_msg = report.get('error', 'Unknown error occurred')
                        st.markdown(f'<div class="error-box"><strong>{error_msg}</strong></div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
    
    # Navigation buttons
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("◀️ Back to Connection", width="stretch"):
            st.session_state.step = 1
            st.rerun()
    
    with col2:
        if st.session_state.cleaned_data is not None:
            if st.button("▶️ Proceed to Campaign", type="primary", width="stretch"):
                st.session_state.step = 3
                st.rerun()
        else:
            st.button("▶️ Proceed to Campaign", disabled=True, width="stretch")

# ==================== STEP 3: SEND CAMPAIGN (REOPEN ARCHITECTURE) ====================
elif st.session_state.step == 3:
    st.markdown('<h2 class="step-header">Step 3: Launch Outreach Campaign</h2>', unsafe_allow_html=True)
    
    if st.session_state.cleaned_data is None:
        st.error("❌ No cleaned data found. Please go back to Step 2.")
        if st.button("◀️ Back to Upload", width="stretch"):
            st.session_state.step = 2
            st.rerun()
    else:
        df = st.session_state.cleaned_data
        total_leads = len(df)
        
        # Campaign summary
        estimated_min = total_leads * 1.5
        estimated_max = total_leads * 2
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Leads", total_leads)
        with col2:
            st.metric("⏱️ Est. Time (Min)", f"{estimated_min:.0f} min")
        with col3:
            st.metric("⏱️ Est. Time (Max)", f"{estimated_max:.0f} min")
        
        st.markdown("""
        <div class="info-box">
            <strong>✅ Final Safety Check:</strong><br><br>
            1. <strong>Do NOT interact</strong> with the browser while it's running.<br>
            2. The tool uses a <strong>'Human-Like'</strong> typing delay (not instant paste).<br>
            3. Messages are <strong>randomized</strong> with 4 high-converting templates.<br>
            4. If the process stops, just click 'Start Campaign' again to resume.
        </div>
        """, unsafe_allow_html=True)
        st.subheader("Step 3: Launch Campaign 🚀")
        
        # Message Preview Section
        with st.expander("📝 View Message Templates (Read-Only)"):
            st.info("💡 The tool will randomly select one of these high-converting templates for each lead to avoid spam detection.")
            preview_name = "Global Solutions Inc."
            preview_bot = WhatsAppBot()
            
            tabs = st.tabs(["Template 1", "Template 2", "Template 3", "Template 4"])
            with tabs[0]:
                st.code(preview_bot.generate_message(preview_name), language='markdown')
            with tabs[1]:
                st.code(preview_bot.generate_message(preview_name), language='markdown')
            with tabs[2]:
                st.code(preview_bot.generate_message(preview_name), language='markdown')
            with tabs[3]:
                st.code(preview_bot.generate_message(preview_name), language='markdown')
        
        # Start campaign button
        if st.session_state.campaign_results is None and not st.session_state.campaign_running:
            st.markdown("""
            <div class="warning-box">
                <strong>⚠️ Important Safety Notes:</strong><br><br>
                • The tool will <strong>launch a FRESH browser</strong> using your saved login<br>
                • <strong>DO NOT</strong> close the browser during the campaign<br>
                • <strong>DO NOT</strong> use WhatsApp Web manually during the campaign<br>
                • The process will take time - <strong>be patient</strong><br>
                • The browser will close automatically when done
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Start Campaign", type="primary", width="stretch"):
                    st.session_state.campaign_running = True
                    st.rerun()
            
            with col2:
                if st.button("◀️ Back to Upload", width="stretch"):
                    st.session_state.step = 2
                    st.rerun()
        
        # Campaign execution
        if st.session_state.campaign_running and st.session_state.campaign_results is None:
            # Initialize results
            results = []
            
            # Progress containers
            progress_bar = st.progress(0)
            status_container = st.container()
            
            # Metrics using st.empty() to avoid stacking on each iteration
            metrics_cols = st.columns(3)
            metric_sent = metrics_cols[0].empty()
            metric_failed = metrics_cols[1].empty()
            metric_progress = metrics_cols[2].empty()
            
            # Live console
            st.markdown("### 🖥️ Live Console")
            console_container = st.empty()
            console_logs = []
            
            # CRITICAL: Launch FRESH browser with cleanup
            with status_container:
                st.info("🔄 Launching fresh browser with saved login...")
            
            bot = WhatsAppBot()
            
            # Force cleanup before launching
            cleanup_success, cleanup_msg = bot.force_browser_cleanup()
            if not cleanup_success:
                st.error(f"❌ {cleanup_msg}")
                st.session_state.campaign_running = False
                st.stop()
            
            # Launch fresh browser
            success, message, page = bot.launch_browser()
            
            if not success:
                st.error(f"❌ {message}")
                st.session_state.campaign_running = False
                st.stop()
            
            with status_container:
                st.success("✅ Browser launched! Waiting for WhatsApp to load...")
            
            # Wait for WhatsApp to load
            time.sleep(5)
            
            # Counters
            sent_count = 0
            failed_count = 0
            
            # Campaign loop
            for seq_idx, (idx, row) in enumerate(df.iterrows()):
                name = row['Name']
                phone = row['Phone']
                
                # Update progress
                progress = (seq_idx + 1) / total_leads
                progress_bar.progress(progress)
                
                with status_container:
                    st.info(f"📤 **Sending to:** {name} ({phone}) - **{seq_idx + 1}/{total_leads}**")
                
                # Generate personalized message
                message = bot.generate_message(name)
                
                # Send message
                status, timestamp = bot.send_message(phone, message)
                
                # Update counters
                if "Sent" in status or "✅" in status:
                    sent_count += 1
                    log_class = "console-success"
                    log_msg = f"[{timestamp}] ✅ SUCCESS: {name} ({phone})"
                else:
                    failed_count += 1
                    log_class = "console-error"
                    log_msg = f"[{timestamp}] ❌ FAILED: {name} ({phone}) - {status}"
                
                # Add to console logs
                console_logs.append(f'<span class="{log_class}">{log_msg}</span>')
                
                # Update console (show last 10 logs)
                console_html = '<div class="live-console">' + '<br>'.join(console_logs[-10:]) + '</div>'
                console_container.markdown(console_html, unsafe_allow_html=True)
                
                # Log result
                results.append({
                    'Name': name,
                    'Phone': phone,
                    'Status': status,
                    'Timestamp': timestamp
                })
                
                # Update metrics (using st.empty placeholders to avoid stacking)
                metric_sent.metric("✅ Sent", sent_count)
                metric_failed.metric("❌ Failed", failed_count)
                metric_progress.metric("📊 Progress", f"{seq_idx + 1}/{total_leads}")
                
                # Anti-ban delay (except for last message)
                if seq_idx < total_leads - 1:
                    with status_container:
                        countdown_placeholder = st.empty()
                        
                        # Capture placeholder in default arg to avoid stale closure
                        def update_countdown(remaining, _ph=countdown_placeholder):
                            mins = remaining // 60
                            secs = remaining % 60
                            _ph.warning(f"⏳ **Cooling down...** {mins}m {secs}s remaining (Anti-Ban Protection)")
                        
                        bot.wait_with_countdown(60, 120, update_countdown)
                        countdown_placeholder.empty()
            
            # CRITICAL: Close browser to release lock
            with status_container:
                st.info("🔒 Closing browser to release lock...")
            
            bot.close_browser()
            
            # Campaign complete
            st.session_state.campaign_results = pd.DataFrame(results)
            st.session_state.campaign_running = False
            progress_bar.progress(1.0)
            
            with status_container:
                st.success("🎉 **Campaign Complete! Browser closed.**")
            
            st.rerun()
        
        # Show results if campaign is complete
        if st.session_state.campaign_results is not None:
            results_df = st.session_state.campaign_results
            
            st.markdown('<div class="success-box"><strong>🎉 Campaign Completed Successfully!</strong></div>', unsafe_allow_html=True)
            
            # Results metrics
            sent_count = len(results_df[results_df['Status'].str.contains('Sent|✅', na=False)])
            failed_count = len(results_df) - sent_count
            success_rate = (sent_count / len(results_df) * 100) if len(results_df) > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Processed", len(results_df))
            with col2:
                st.metric("✅ Successfully Sent", sent_count)
            with col3:
                st.metric("❌ Failed", failed_count)
            with col4:
                st.metric("📈 Success Rate", f"{success_rate:.1f}%")
            
            # Show results table
            st.markdown("### 📋 Campaign Results")
            st.dataframe(results_df, width="stretch")
            
            # Download results
            col1, col2 = st.columns(2)
            
            with col1:
                csv_buffer = io.StringIO()
                results_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download Campaign Report (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"campaign_report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                if st.button("🔄 Start New Campaign", type="primary", width="stretch"):
                    st.session_state.step = 1
                    st.session_state.cleaned_data = None
                    st.session_state.data_report = None
                    st.session_state.campaign_results = None
                    st.session_state.campaign_running = False
                    st.rerun()

# ==================== FOOTER ====================
st.divider()
st.markdown("""
<div class="footer-text">
    <strong>FireHox WhatsApp Outreach Tool v4.0 (Singleton Lock Fixed)</strong> | Built with Streamlit & Playwright | Use Responsibly
</div>
""", unsafe_allow_html=True)
