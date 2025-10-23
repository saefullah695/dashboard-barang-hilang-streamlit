import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
from scipy import stats
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import google.generativeai as genai
import json
import logging
import time
from functools import wraps
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# ------------------- KONFIGURASI AWAL --------------------
# =========================================================
st.set_page_config(
    page_title="Dashboard Varians Stok Opname",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palet warna profesional dengan kontras tinggi
COLOR_SCHEME = {
    "primary": "#3B82F6",      # Blue-500 - Biru profesional
    "secondary": "#8B5CF6",    # Violet-500 - Ungu elegant
    "accent": "#06B6D4",       # Cyan-500 - Cyan fresh
    "success": "#10B981",      # Emerald-500 - Hijau sukses
    "warning": "#F59E0B",      # Amber-500 - Kuning warning
    "error": "#EF4444",        # Red-500 - Merah error
    "info": "#3B82F6",         # Blue-500 - Info
    "neutral": "#6B7280",      # Gray-500 - Netral
    
    # Background colors
    "bg_primary": "#0F172A",   # Slate-900
    "bg_secondary": "#1E293B", # Slate-800
    "bg_card": "#334155",      # Slate-700
    "bg_surface": "#475569",   # Slate-600
    
    # Text colors
    "text_primary": "#F8FAFC",   # Slate-50
    "text_secondary": "#E2E8F0", # Slate-200
    "text_muted": "#94A3B8",     # Slate-400
    
    # Border and subtle colors
    "border": "#475569",         # Slate-600
    "border_light": "#64748B",   # Slate-500
    "shadow": "rgba(0, 0, 0, 0.25)",
}

PLOTLY_COLORWAY = [
    "#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", 
    "#EF4444", "#06B6D4", "#EC4899", "#84CC16", "#F97316"
]

ENHANCED_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --primary: #3B82F6;
    --secondary: #8B5CF6;
    --accent: #06B6D4;
    --success: #10B981;
    --warning: #F59E0B;
    --error: #EF4444;
    --info: #3B82F6;
    --neutral: #6B7280;
    
    --bg-primary: #0F172A;
    --bg-secondary: #1E293B;
    --bg-card: #334155;
    --bg-surface: #475569;
    
    --text-primary: #F8FAFC;
    --text-secondary: #E2E8F0;
    --text-muted: #94A3B8;
    
    --border: #475569;
    --border-light: #64748B;
    --shadow: rgba(0, 0, 0, 0.25);
    
    --radius: 16px;
    --radius-lg: 24px;
    --radius-xl: 32px;
    --spacing: 1.5rem;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --blur: 20px;
}

/* Reset dan Base Styles */
* {
    box-sizing: border-box;
}

body, html {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Main App Container */
.stApp {
    background: transparent;
}

[data-testid="stAppViewContainer"] {
    background: transparent;
    padding: 0;
}

section.main > div {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.2;
    margin-bottom: 1rem;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }
h4 { font-size: 1.25rem; }

p {
    color: var(--text-secondary);
    margin-bottom: 1rem;
}

.stMarkdown p {
    font-size: 0.95rem;
    line-height: 1.65;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
    border-right: 2px solid var(--border);
    backdrop-filter: blur(var(--blur));
}

[data-testid="stSidebar"] .stMarkdown {
    padding: 0.5rem;
}

[data-testid="stSidebar"] h2 {
    color: var(--primary) !important;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border);
}

[data-testid="stSidebar"] h3 {
    color: var(--accent) !important;
    font-size: 1.1rem;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    border-radius: var(--radius-xl);
    padding: 3rem 2.5rem;
    margin-bottom: 3rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 25px 50px -12px var(--shadow);
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -30%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    color: white !important;
    margin-bottom: 1rem;
    line-height: 1.1;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.hero-subtitle {
    font-size: 1.2rem;
    color: rgba(255,255,255,0.9) !important;
    margin-bottom: 0;
    font-weight: 400;
}

.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 50px;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 1rem;
    backdrop-filter: blur(10px);
}

/* KPI Cards Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border-radius: var(--radius-lg);
    padding: 2rem;
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
    transition: var(--transition);
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 10px 25px -5px var(--shadow);
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: var(--primary);
    box-shadow: 0 20px 40px -10px var(--shadow);
}

.metric-card::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, var(--primary), var(--secondary), var(--accent));
    border-radius: var(--radius-lg);
    z-index: -1;
    opacity: 0;
    transition: var(--transition);
}

.metric-card:hover::after {
    opacity: 1;
}

.metric-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    filter: drop-shadow(0 2px 4px var(--shadow));
}

.metric-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.1;
}

.metric-delta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
}

.delta-positive { color: var(--success); }
.delta-negative { color: var(--error); }
.delta-neutral { color: var(--warning); }

/* Insight Cards */
.insights-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.insight-card {
    background: var(--bg-card);
    border-radius: var(--radius);
    padding: 1.5rem;
    border: 1px solid var(--border);
    position: relative;
    transition: var(--transition);
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 4px 15px -3px var(--shadow);
}

.insight-card:hover {
    transform: translateY(-2px);
    border-color: var(--accent);
    box-shadow: 0 10px 25px -5px var(--shadow);
}

.insight-card h4 {
    color: var(--accent) !important;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.insight-card .insight-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.insight-card .insight-description {
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.5;
}

/* Chart Containers */
.chart-container {
    background: var(--bg-card);
    border-radius: var(--radius);
    padding: 1.5rem;
    border: 1px solid var(--border);
    margin-bottom: 2rem;
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 4px 15px -3px var(--shadow);
    transition: var(--transition);
}

.chart-container:hover {
    border-color: var(--primary);
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--bg-secondary);
    padding: 0.5rem;
    border-radius: var(--radius);
    border: 1px solid var(--border);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: var(--radius);
    color: var(--text-muted);
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    transition: var(--transition);
    border: 1px solid transparent;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--bg-card);
    color: var(--text-secondary);
    border-color: var(--border-light);
}

.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
    border-color: var(--primary) !important;
    box-shadow: 0 4px 12px -2px rgba(59, 130, 246, 0.5);
}

/* Button Styling */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    color: white;
    border: none;
    border-radius: var(--radius);
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: var(--transition);
    box-shadow: 0 4px 15px -3px rgba(59, 130, 246, 0.4);
    position: relative;
    overflow: hidden;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px -5px rgba(59, 130, 246, 0.6);
}

.stButton > button::before, .stDownloadButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.stButton > button:hover::before, .stDownloadButton > button:hover::before {
    left: 100%;
}

/* Input Styling */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stMultiselect > div > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div:focus,
.stMultiselect > div > div > div:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
}

/* Slider Styling */
.stSlider > div > div > div > div {
    background: var(--primary) !important;
}

/* DataFrame Styling */
.stDataFrame {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
    background: var(--bg-card);
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary) !important;
    font-weight: 600;
}

.streamlit-expanderContent {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 var(--radius) var(--radius);
}

/* AI Response Styling */
.ai-response {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin: 1rem 0;
    position: relative;
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 4px 15px -3px rgba(6, 182, 212, 0.3);
}

.ai-response::before {
    content: '🤖';
    position: absolute;
    top: -10px;
    left: 1rem;
    background: var(--accent);
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
}

/* Loading and Spinner */
.stSpinner {
    color: var(--primary) !important;
}

/* Success/Warning/Error Messages */
.stSuccess {
    background: linear-gradient(135deg, var(--success), #059669) !important;
    border: none !important;
    color: white !important;
    border-radius: var(--radius) !important;
}

.stWarning {
    background: linear-gradient(135deg, var(--warning), #D97706) !important;
    border: none !important;
    color: white !important;
    border-radius: var(--radius) !important;
}

.stError {
    background: linear-gradient(135deg, var(--error), #DC2626) !important;
    border: none !important;
    color: white !important;
    border-radius: var(--radius) !important;
}

/* Divider */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 2rem 0;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;
    }
    
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    
    .insights-grid {
        grid-template-columns: 1fr;
    }
    
    .metric-card,
    .insight-card,
    .chart-container {
        padding: 1rem;
    }
}

/* Animation Classes */
.fade-in {
    animation: fadeIn 0.6s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.slide-up {
    animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
    from { transform: translateY(30px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--border-light);
}

/* Footer */
.footer {
    margin-top: 3rem;
    padding: 2rem;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.9rem;
    border-top: 1px solid var(--border);
    background: var(--bg-secondary);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.footer strong {
    color: var(--primary);
}

/* Status Indicators */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 600;
}

.status-connected {
    background: rgba(16, 185, 129, 0.2);
    color: var(--success);
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-error {
    background: rgba(239, 68, 68, 0.2);
    color: var(--error);
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.status-warning {
    background: rgba(245, 158, 11, 0.2);
    color: var(--warning);
    border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Custom Tooltip */
.custom-tooltip {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 10px 25px -5px var(--shadow) !important;
    backdrop-filter: blur(var(--blur));
}

/* New: Progress Bar */
.progress-bar {
    height: 8px;
    background: var(--bg-surface);
    border-radius: 4px;
    overflow: hidden;
    margin: 1rem 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    border-radius: 4px;
    transition: width 0.3s ease;
}

/* New: Alert Box */
.alert-box {
    padding: 1rem;
    border-radius: var(--radius);
    margin: 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.alert-info {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: var(--primary);
}

.alert-success {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: var(--success);
}

.alert-warning {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: var(--warning);
}

.alert-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: var(--error);
}
</style>
"""

st.markdown(ENHANCED_CSS, unsafe_allow_html=True)

# =========================================================
# ----------------- KONFIGURASI PLOTLY --------------------
# =========================================================
def configure_plotly_theme() -> None:
    template = go.layout.Template(
        layout=go.Layout(
            font=dict(
                family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", 
                color=COLOR_SCHEME["text_secondary"],
                size=12
            ),
            title=dict(
                font=dict(
                    size=20, 
                    family="Inter, sans-serif", 
                    color=COLOR_SCHEME["text_primary"],
                    weight="bold"
                ),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor="rgba(51, 65, 85, 0)",
            plot_bgcolor="rgba(30, 41, 59, 0.8)",
            legend=dict(
                bgcolor="rgba(51, 65, 85, 0.9)",
                bordercolor=COLOR_SCHEME["border"],
                borderwidth=1,
                font=dict(size=11, color=COLOR_SCHEME["text_secondary"])
            ),
            margin=dict(l=60, r=40, t=80, b=60),
            xaxis=dict(
                gridcolor=COLOR_SCHEME["border"], 
                zerolinecolor=COLOR_SCHEME["border_light"],
                tickcolor=COLOR_SCHEME["text_muted"],
                linecolor=COLOR_SCHEME["border"]
            ),
            yaxis=dict(
                gridcolor=COLOR_SCHEME["border"], 
                zerolinecolor=COLOR_SCHEME["border_light"],
                tickcolor=COLOR_SCHEME["text_muted"],
                linecolor=COLOR_SCHEME["border"]
            ),
            colorway=PLOTLY_COLORWAY
        )
    )
    pio.templates["professional_dark"] = template
    px.defaults.template = "professional_dark"
    px.defaults.color_discrete_sequence = PLOTLY_COLORWAY

configure_plotly_theme()

# =========================================================
# ------------------- FUNGSI UTILITAS ---------------------
# =========================================================
def format_currency(value: float) -> str:
    try:
        return f"Rp {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Rp 0"

def format_quantity(value: float) -> str:
    try:
        return f"{value:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"

def render_metric_card(
    title: str,
    value: str,
    delta_label: Optional[str] = None,
    delta_type: str = "neutral",
    icon: str = "📊"
) -> None:
    delta_class = {
        "positive": "delta-positive",
        "negative": "delta-negative",
        "neutral": "delta-neutral"
    }.get(delta_type, "delta-neutral")

    delta_markup = ""
    if delta_label:
        delta_markup = f'<div class="metric-delta {delta_class}">{delta_markup}</div>'

    st.markdown(
        f"""
        <div class="metric-card fade-in">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_markup}
        </div>
        """,
        unsafe_allow_html=True
    )

# New: Performance monitoring decorator
def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

# Enhanced error handling decorator
def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            st.error(f"❌ Terjadi kesalahan: {str(e)}")
            return None
    return wrapper

@st.cache_data(ttl=600, show_spinner=False)
@monitor_performance
@handle_errors
def load_data(spreadsheet_url: str, sheet_name: str) -> Optional[pd.DataFrame]:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(sheet_name)
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
    except Exception as exc:
        st.error(f"❌ Gagal memuat data: {exc}")
        return None

    df.dropna(axis=0, how="all", inplace=True)
    df.columns = df.columns.str.strip()

    rename_map = {
        "Tanggal SO": "Tanggal Stock Opname",
        "Selisih Qty": "Selisih Qty (Pcs)",
        "Selisih Value": "Selisih Value (Rp)"
    }
    df.rename(columns=rename_map, inplace=True)

    if "Tanggal Stock Opname" not in df.columns:
        st.error("❌ Kolom 'Tanggal Stock Opname' tidak ditemukan pada sheet.")
        return None

    df["Tanggal Stock Opname"] = pd.to_datetime(df["Tanggal Stock Opname"], errors="coerce", dayfirst=True)

    for kolom in ["Selisih Qty (Pcs)", "Selisih Value (Rp)"]:
        if kolom in df.columns:
            df[kolom] = pd.to_numeric(df[kolom], errors="coerce")

    df.dropna(
        subset=["Tanggal Stock Opname", "Selisih Qty (Pcs)", "Selisih Value (Rp)"],
        inplace=True
    )

    if "Tag" in df.columns:
        df["Tag"] = df["Tag"].replace("", "Tidak Terdefinisi").fillna("Tidak Terdefinisi")
    else:
        df["Tag"] = "Tidak Terdefinisi"

    df["Varians Nilai Absolut"] = df["Selisih Value (Rp)"].abs()
    df["Varians Qty Absolut"] = df["Selisih Qty (Pcs)"].abs()
    df["Arah Varians"] = df["Selisih Value (Rp)"].apply(
        lambda val: "Positif" if val > 0 else ("Negatif" if val < 0 else "Netral")
    )

    return df

@st.cache_data(ttl=600, show_spinner=False)
@monitor_performance
def aggregate_tag_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby("Tag")["Selisih Value (Rp)"]
        .agg(["sum", "mean", "count"])
        .rename(columns={"sum": "Total Varians", "mean": "Rata-rata Varians", "count": "Jumlah PLU"})
        .sort_values(by="Total Varians", key=lambda x: x.abs(), ascending=False)
    )

@st.cache_data(ttl=600, show_spinner=False)
@monitor_performance
def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns or df.empty:
        return pd.DataFrame()
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers.sort_values(by=column, ascending=False)

@monitor_performance
def create_top_products_chart(df: pd.DataFrame, metric: str, top_n: int) -> go.Figure:
    metric_column = "Selisih Value (Rp)" if metric == "Nilai (Rp)" else "Selisih Qty (Pcs)"
    label_metric = "Total Varians Nilai (Rp)" if metric == "Nilai (Rp)" else "Total Varians Kuantitas (Pcs)"

    top_products = (
        df.groupby(["PLU", "DESCP"], dropna=False)[metric_column]
        .sum()
        .to_frame("Varians")
        .assign(Varians_Absolut=lambda x: x["Varians"].abs())
        .sort_values(by="Varians_Absolut", ascending=False)
        .head(top_n)
        .reset_index()
    )

    if top_products.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ Data varians tidak ditemukan",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color=COLOR_SCHEME["text_muted"], size=16)
        )
        fig.update_layout(
            title=f"<b>Top {top_n} Produk dengan Varians {metric} Tertinggi</b>", 
            title_x=0.5,
            height=500
        )
        return fig

    fig = px.bar(
        top_products,
        x="Varians",
        y="DESCP",
        orientation="h",
        color="Varians",
        color_continuous_scale=["#EF4444", "#6B7280", "#10B981"],
        labels={"Varians": label_metric, "DESCP": "Deskripsi Produk"},
        title=f"<b>🏆 Top {top_n} Produk dengan Varians {metric} Tertinggi</b>",
        height=max(500, top_n * 40)
    )
    
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        title_x=0.5,
        coloraxis_showscale=False,
        plot_bgcolor="rgba(30, 41, 59, 0.3)"
    )
    
    fig.add_vline(
        x=0, 
        line_width=2, 
        line_color=COLOR_SCHEME["border_light"], 
        line_dash="dash"
    )
    
    return fig

@monitor_performance
def create_trend_chart(df: pd.DataFrame, metric: str) -> go.Figure:
    metric_column = "Selisih Value (Rp)" if metric == "Nilai (Rp)" else "Selisih Qty (Pcs)"
    label_y = "Total Varians Nilai (Rp)" if metric == "Nilai (Rp)" else "Total Varians Kuantitas (Pcs)"
    min_date = df["Tanggal Stock Opname"].min()
    max_date = df["Tanggal Stock Opname"].max()
    date_range = (max_date - min_date).days

    if min_date.date() == max_date.date():
        fig = go.Figure()
        fig.add_annotation(
            text=f"📅 Data hanya tersedia pada <b>{min_date.strftime('%d %B %Y')}</b>",
            xref="paper", yref="paper", 
            x=0.5, y=0.5, 
            showarrow=False,
            font=dict(color=COLOR_SCHEME["text_secondary"], size=16)
        )
        fig.update_layout(
            title="<b>📈 Analisis Tren Varians</b>", 
            title_x=0.5,
            height=500
        )
        return fig

    if date_range < 45:
        trend_data = (
            df.groupby(df["Tanggal Stock Opname"].dt.date)[metric_column]
            .sum()
            .rename("Varians")
            .to_frame()
            .reset_index()
        )
        trend_data["MA_7"] = trend_data["Varians"].rolling(7, min_periods=1).mean()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data["Tanggal Stock Opname"],
            y=trend_data["Varians"],
            mode="lines+markers",
            name="Varians Harian",
            line=dict(color=COLOR_SCHEME["primary"], width=3),
            marker=dict(size=8, color=COLOR_SCHEME["primary"])
        ))
        
        fig.add_trace(go.Scatter(
            x=trend_data["Tanggal Stock Opname"],
            y=trend_data["MA_7"],
            mode="lines",
            name="Moving Average (7 Hari)",
            line=dict(color=COLOR_SCHEME["accent"], width=2, dash="dot")
        ))
        
        fig.update_layout(
            title="<b>📈 Tren Varians Harian</b>",
            xaxis_title="Tanggal",
            yaxis_title=label_y,
            title_x=0.5,
            height=500,
            hovermode='x unified'
        )
    else:
        trend_data = (
            df.groupby(df["Tanggal Stock Opname"].dt.to_period("M"))[metric_column]
            .sum()
            .rename("Varians")
            .to_frame()
            .reset_index()
        )
        trend_data["Tanggal Stock Opname"] = trend_data["Tanggal Stock Opname"].dt.to_timestamp()
        
        fig = px.bar(
            trend_data,
            x="Tanggal Stock Opname",
            y="Varians",
            color="Varians",
            color_continuous_scale=["#EF4444", "#6B7280", "#10B981"],
            labels={"Tanggal Stock Opname": "Periode", "Varians": label_y},
            title="<b>📊 Tren Varians Bulanan</b>",
            height=500
        )
        
        fig.update_layout(
            title_x=0.5, 
            coloraxis_showscale=False,
            plot_bgcolor="rgba(30, 41, 59, 0.3)"
        )
        
        fig.add_hline(
            y=0, 
            line_width=2, 
            line_color=COLOR_SCHEME["border_light"], 
            line_dash="dash"
        )

    return fig

@monitor_performance
def create_tag_analysis_chart(df: pd.DataFrame, metric: str) -> go.Figure:
    metric_column = "Selisih Value (Rp)" if metric == "Nilai (Rp)" else "Selisih Qty (Pcs)"
    label_metric = "Total Varians Nilai (Rp)" if metric == "Nilai (Rp)" else "Total Varians Kuantitas (Pcs)"

    tag_analysis = (
        df.groupby("Tag")[metric_column]
        .sum()
        .rename("Varians")
        .to_frame()
        .assign(Varians_Absolut=lambda x: x["Varians"].abs())
        .sort_values(by="Varians_Absolut", ascending=False)
        .reset_index()
    )

    fig = px.bar(
        tag_analysis,
        x="Varians",
        y="Tag",
        orientation="h",
        color="Varians",
        color_continuous_scale=["#EF4444", "#6B7280", "#10B981"],
        labels={"Varians": label_metric, "Tag": "Kategori (Tag)"},
        title="<b>🏷️ Analisis Varians per Kategori</b>",
        height=max(500, len(tag_analysis) * 50)
    )
    
    fig.update_layout(
        title_x=0.5, 
        yaxis=dict(categoryorder="total ascending"),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(30, 41, 59, 0.3)"
    )
    
    fig.add_vline(
        x=0, 
        line_width=2, 
        line_color=COLOR_SCHEME["border_light"], 
        line_dash="dash"
    )
    
    return fig

@monitor_performance
def create_scatter_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="Selisih Qty (Pcs)",
        y="Selisih Value (Rp)",
        hover_data=["PLU", "DESCP", "Tag"],
        color="Tag",
        color_discrete_sequence=PLOTLY_COLORWAY,
        title="<b>🔍 Analisis Korelasi: Kuantitas vs Nilai</b>",
        trendline="ols" if len(df) > 10 else None,
        height=550
    )
    
    fig.update_layout(
        title_x=0.5,
        plot_bgcolor="rgba(30, 41, 59, 0.3)"
    )
    
    fig.add_hline(
        y=0, 
        line_width=1, 
        line_color=COLOR_SCHEME["border_light"], 
        line_dash="dot"
    )
    
    fig.add_vline(
        x=0, 
        line_width=1, 
        line_color=COLOR_SCHEME["border_light"], 
        line_dash="dot"
    )
    
    return fig

@monitor_performance
def create_treemap_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ Tidak ada data untuk visualisasi treemap",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color=COLOR_SCHEME["text_muted"], size=16)
        )
        fig.update_layout(
            title="<b>🗺️ Treemap Varians</b>", 
            title_x=0.5,
            height=550
        )
        return fig
    
    fig = px.treemap(
        df,
        path=["Tag", "DESCP"],
        values="Varians Nilai Absolut",
        color="Selisih Value (Rp)",
        color_continuous_scale=["#EF4444", "#94A3B8", "#10B981"],
        color_continuous_midpoint=0,
        title="<b>🗺️ Treemap: Distribusi Varians per Tag & Produk</b>",
        height=550
    )
    
    fig.update_layout(
        title_x=0.5, 
        margin=dict(t=80, l=30, r=30, b=30)
    )
    
    return fig

@monitor_performance
def filter_dataframe(
    df: pd.DataFrame,
    date_range: Tuple[datetime, datetime],
    selected_tags: List[str],
    selected_direction: List[str]
) -> pd.DataFrame:
    filtered = df.copy()
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0] if date_range else datetime.today()

    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    filtered = filtered[
        (filtered["Tanggal Stock Opname"] >= start_ts) &
        (filtered["Tanggal Stock Opname"] <= end_ts)
    ]

    if selected_tags and "Semua" not in selected_tags:
        filtered = filtered[filtered["Tag"].isin(selected_tags)]

    if selected_direction and "Semua" not in selected_direction:
        filtered = filtered[filtered["Arah Varians"].isin(selected_direction)]

    return filtered

def render_insight_card(title: str, value: str, description: str, icon: str = "💡") -> None:
    st.markdown(
        f"""
        <div class="insight-card slide-up">
            <h4>{icon} {title}</h4>
            <div class="insight-value">{value}</div>
            <div class="insight-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

@monitor_performance
def highlight_insights(df: pd.DataFrame) -> None:
    if df.empty:
        return

    tag_summary = aggregate_tag_summary(df)
    biggest_positive = df[df["Selisih Value (Rp)"] > 0].sort_values("Selisih Value (Rp)", ascending=False).head(1)
    biggest_negative = df[df["Selisih Value (Rp)"] < 0].sort_values("Selisih Value (Rp)").head(1)
    outliers_value = detect_outliers_iqr(df, "Selisih Value (Rp)")
    outlier_count = len(outliers_value)

    st.markdown('<div class="insights-grid">', unsafe_allow_html=True)
    
    if not tag_summary.empty:
        top_tag = tag_summary.index[0]
        top_tag_value = tag_summary.iloc[0]["Total Varians"]
        kontribusi = (
            tag_summary["Total Varians"].abs().iloc[0] /
            tag_summary["Total Varians"].abs().sum() * 100
        )
        render_insight_card(
            title="Tag Dominan",
            value=f"{top_tag}",
            description=f"Menyumbang {format_currency(top_tag_value)} • Kontribusi {kontribusi:.1f}% dari total varians",
            icon="🏷️"
        )
    else:
        render_insight_card(
            title="Tag Dominan",
            value="Data tidak tersedia",
            description="Pastikan data memiliki kolom Tag yang valid",
            icon="🏷️"
        )

    if not biggest_positive.empty:
        row = biggest_positive.iloc[0]
        render_insight_card(
            title="Varians Positif Tertinggi",
            value=row["DESCP"],
            description=f"Selisih: {format_currency(row['Selisih Value (Rp)'])} • Qty: {format_quantity(row['Selisih Qty (Pcs)'])} pcs",
            icon="📈"
        )
    else:
        render_insight_card(
            title="Varians Positif Tertinggi",
            value="Tidak ada data positif",
            description="Belum ditemukan varians positif pada filter saat ini",
            icon="📈"
        )

    if not biggest_negative.empty:
        row = biggest_negative.iloc[0]
        render_insight_card(
            title="Varians Negatif Terbesar",
            value=row["DESCP"],
            description=f"Selisih: {format_currency(row['Selisih Value (Rp)'])} • Qty: {format_quantity(row['Selisih Qty (Pcs)'])} pcs",
            icon="📉"
        )
    else:
        render_insight_card(
            title="Varians Negatif Terbesar",
            value="Tidak ada data negatif",
            description="Belum ditemukan varians negatif pada filter saat ini",
            icon="📉"
        )

    render_insight_card(
        title="Deteksi Anomali",
        value=f"{outlier_count} produk",
        description="Produk dengan varians ekstrem yang memerlukan investigasi lebih lanjut",
        icon="🚨"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if outlier_count > 0:
        with st.expander("🔍 Lihat Detail Anomali", expanded=False):
            st.dataframe(
                outliers_value[["PLU", "DESCP", "Selisih Value (Rp)", "Selisih Qty (Pcs)", "Tag"]].head(10),
                use_container_width=True
            )

# =========================================================
# ------------------- FUNGSI DATA PROFILING -----------------
# =========================================================
@monitor_performance
def create_distribution_chart(df: pd.DataFrame, column: str) -> go.Figure:
    fig = go.Figure()
    
    # Histogram
    fig.add_trace(go.Histogram(
        x=df[column],
        nbinsx=30,
        name='Distribusi',
        marker_color=COLOR_SCHEME["primary"],
        opacity=0.8
    ))
    
    # Mean line
    mean_val = df[column].mean()
    fig.add_vline(
        x=mean_val, 
        line_width=2, 
        line_dash="dash", 
        line_color=COLOR_SCHEME["accent"],
        annotation_text=f"Mean: {mean_val:.2f}",
        annotation_position="top right"
    )
    
    # Median line
    median_val = df[column].median()
    fig.add_vline(
        x=median_val, 
        line_width=2, 
        line_dash="dash", 
        line_color=COLOR_SCHEME["warning"],
        annotation_text=f"Median: {median_val:.2f}",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title=f"<b>📊 Distribusi {column}</b>",
        xaxis_title=column,
        yaxis_title="Frekuensi",
        title_x=0.5,
        showlegend=False,
        height=400,
        plot_bgcolor="rgba(30, 41, 59, 0.3)"
    )
    
    return fig

@monitor_performance
def create_box_plot(df: pd.DataFrame, column: str) -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=df[column],
        name=column,
        marker_color=COLOR_SCHEME["secondary"],
        boxpoints='outliers',
        fillcolor="rgba(139, 92, 246, 0.3)"
    ))
    
    fig.update_layout(
        title=f"<b>📦 Box Plot {column}</b>",
        yaxis_title=column,
        title_x=0.5,
        showlegend=False,
        height=400,
        plot_bgcolor="rgba(30, 41, 59, 0.3)"
    )
    
    return fig

@monitor_performance
def create_correlation_matrix(df: pd.DataFrame) -> go.Figure:
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ Tidak ada kolom numerik untuk analisis korelasi",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color=COLOR_SCHEME["text_muted"], size=16)
        )
        fig.update_layout(
            title="<b>🔗 Matriks Korelasi</b>", 
            title_x=0.5,
            height=500
        )
        return fig
    
    corr_matrix = numeric_df.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10, "color": "white"},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="<b>🔗 Matriks Korelasi Antar Variabel</b>",
        title_x=0.5,
        width=600,
        height=500
    )
    
    return fig

@monitor_performance
def create_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    report = pd.DataFrame({
        'Kolom': df.columns,
        'Tipe Data': df.dtypes.values,
        'Total Non-Null': df.count().values,
        'Total Null': df.isnull().sum().values,
        '% Null': (df.isnull().sum() / len(df) * 100).round(2).values,
        'Unique Values': df.nunique().values,
        'Most Frequent': [df[col].mode()[0] if not df[col].mode().empty else '-' for col in df.columns]
    })
    
    return report

# =========================================================
# ------------------- FUNGSI GEMINI AI --------------------
# =========================================================
def configure_gemini():
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model
    except Exception as e:
        st.error(f"❌ Gagal mengkonfigurasi Gemini AI: {e}")
        return None

@monitor_performance
def generate_data_insights(df: pd.DataFrame, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model AI tidak tersedia."
    
    # Prepare comprehensive data summary
    total_records = len(df)
    date_range = f"{df['Tanggal Stock Opname'].min().date()} hingga {df['Tanggal Stock Opname'].max().date()}"
    total_variance_value = df["Selisih Value (Rp)"].sum()
    total_variance_qty = df["Selisih Qty (Pcs)"].sum()
    top_tags = df.groupby("Tag")["Selisih Value (Rp)"].sum().abs().sort_values(ascending=False).head(3).index.tolist()
    
    # Get statistical insights
    avg_variance = df["Selisih Value (Rp)"].mean()
    std_variance = df["Selisih Value (Rp)"].std()
    positive_count = len(df[df["Selisih Value (Rp)"] > 0])
    negative_count = len(df[df["Selisih Value (Rp)"] < 0])
    
    top_positive = df[df["Selisih Value (Rp)"] > 0].sort_values("Selisih Value (Rp)", ascending=False).head(3)
    top_negative = df[df["Selisih Value (Rp)"] < 0].sort_values("Selisih Value (Rp)").head(3)
    
    prompt = f"""
    Sebagai ahli analisis inventory dan data scientist, berikan insight mendalam dari data varians stok opname berikut:
    
    📊 RINGKASAN DATA:
    - Total Records: {total_records}
    - Periode: {date_range}
    - Total Varians Nilai: {format_currency(total_variance_value)}
    - Total Varians Kuantitas: {format_quantity(total_variance_qty)} pcs
    - Rata-rata Varians: {format_currency(avg_variance)}
    - Standar Deviasi: {format_currency(std_variance)}
    - Produk dengan Varians Positif: {positive_count} ({positive_count/total_records*100:.1f}%)
    - Produk dengan Varians Negatif: {negative_count} ({negative_count/total_records*100:.1f}%)
    - Top 3 Tag: {', '.join(top_tags)}
    
    🔝 PRODUK VARIANS POSITIF TERTINGGI:
    {top_positive[['DESCP', 'Selisih Value (Rp)', 'Tag']].to_string(index=False) if not top_positive.empty else "Tidak ada"}
    
    ⚠️ PRODUK VARIANS NEGATIF TERBESAR:
    {top_negative[['DESCP', 'Selisih Value (Rp)', 'Tag']].to_string(index=False) if not top_negative.empty else "Tidak ada"}
    
    Berikan analisis komprehensif meliputi:
    
    1. 📈 ANALISIS POLA & TREN
    - Identifikasi pola varians yang menonjol
    - Tren positif/negatif dan signifikansinya
    - Distribusi varians antar kategori
    
    2. 🔍 ROOT CAUSE ANALYSIS
    - Kemungkinan penyebab utama varians negatif
    - Faktor yang berkontribusi pada varians positif
    - Analisis tag/kategori yang bermasalah
    
    3. 💡 STRATEGIC INSIGHTS
    - Area prioritas untuk perhatian manajemen
    - Peluang optimasi dari varians positif
    - Risk assessment dari varians negatif
    
    4. 🎯 ACTIONABLE RECOMMENDATIONS
    - 3 tindakan prioritas untuk mengurangi varians negatif
    - Strategi untuk mempertahankan varians positif
    - Saran peningkatan proses stok opname
    
    Jawab dalam bahasa Indonesia dengan format yang terstruktur dan professional. Gunakan bullet points untuk kemudahan membaca.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Terjadi kesalahan saat menghasilkan insight: {e}"

@monitor_performance
def answer_data_question(df: pd.DataFrame, question: str, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model AI tidak tersedia."
    
    # Enhanced data context
    data_summary = f"""
    Dataset memiliki {len(df)} records dengan periode {df['Tanggal Stock Opname'].min().date()} hingga {df['Tanggal Stock Opname'].max().date()}.
    
    Kolom utama: {', '.join(df.columns.tolist())}
    
    Sample data (5 baris pertama):
    {df.head(5)[['PLU', 'DESCP', 'Selisih Value (Rp)', 'Selisih Qty (Pcs)', 'Tag']].to_string()}
    
    Statistik ringkas:
    - Total Varians Nilai: {format_currency(df['Selisih Value (Rp)'].sum())}
    - Rata-rata Varians: {format_currency(df['Selisih Value (Rp)'].mean())}
    - Jumlah unik PLU: {df['PLU'].nunique()}
    - Jumlah Tag: {df['Tag'].nunique()}
    """
    
    prompt = f"""
    Berdasarkan data varians stok opname berikut:
    
    {data_summary}
    
    Jawab pertanyaan berikut dengan detail dan berikan insight tambahan jika memungkinkan:
    
    PERTANYAAN: "{question}"
    
    Berikan jawaban yang:
    - Akurat berdasarkan data yang tersedia
    - Dilengkapi dengan angka/statistik konkret
    - Memberikan context bisnis yang relevan
    - Menyertakan rekomendasi jika diperlukan
    
    Jawab dalam bahasa Indonesia dengan format yang mudah dipahami.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Terjadi kesalahan: {e}"

@monitor_performance
def generate_recommendations(df: pd.DataFrame, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model AI tidak tersedia."
    
    # Detailed analysis for recommendations
    negative_variance = df[df["Selisih Value (Rp)"] < 0]
    positive_variance = df[df["Selisih Value (Rp)"] > 0]
    outliers = detect_outliers_iqr(df, "Selisih Value (Rp)")
    
    # Tag-wise analysis
    tag_performance = df.groupby("Tag")["Selisih Value (Rp)"].agg(['sum', 'mean', 'count']).round(2)
    worst_tags = tag_performance[tag_performance['sum'] < 0].sort_values('sum').head(3)
    best_tags = tag_performance[tag_performance['sum'] > 0].sort_values('sum', ascending=False).head(3)
    
    prompt = f"""
    Sebagai konsultan manajemen inventory yang berpengalaman, berikan rekomendasi strategis berdasarkan analisis varians stok opname:
    
    📊 SITUASI CURRENT STATE:
    - Total produk dengan varians negatif: {len(negative_variance)} dari {len(df)} ({len(negative_variance)/len(df)*100:.1f}%)
    - Total nilai varians negatif: {format_currency(negative_variance['Selisih Value (Rp)'].sum())}
    - Total produk dengan varians positif: {len(positive_variance)} ({len(positive_variance)/len(df)*100:.1f}%)
    - Total nilai varians positif: {format_currency(positive_variance['Selisih Value (Rp)'].sum())}
    - Jumlah outlier terdeteksi: {len(outliers)} produk
    
    🏷️ PERFORMA TAG/KATEGORI:
    Worst performing tags: {worst_tags.to_string() if not worst_tags.empty else "Tidak ada"}
    Best performing tags: {best_tags.to_string() if not best_tags.empty else "Tidak ada"}
    
    Berikan rekomendasi komprehensif dalam format berikut:
    
    🎯 IMMEDIATE ACTIONS (0-30 hari):
    [3-4 tindakan segera yang dapat diimplementasi]
    
    📋 SHORT-TERM INITIATIVES (1-3 bulan):
    [3-4 inisiatif jangka pendek untuk perbaikan sistem]
    
    🚀 LONG-TERM STRATEGY (3-12 bulan):
    [2-3 strategi jangka panjang untuk transformasi inventory management]
    
    💡 PROCESS IMPROVEMENT:
    [Saran perbaikan proses stok opname dan kontrol inventory]
    
    📊 KPI & MONITORING:
    [Key metrics yang harus dipantau dan target yang realistis]
    
    💰 EXPECTED BENEFITS:
    [Estimasi benefit finansial dan operasional yang dapat dicapai]
    
    Setiap rekomendasi harus:
    - Spesifik dan actionable
    - Disertai reasoning yang jelas
    - Mempertimbangkan implementability
    - Fokus pada ROI dan impact bisnis
    
    Jawab dalam bahasa Indonesia dengan format yang terstruktur dan professional.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Terjadi kesalahan saat menghasilkan rekomendasi: {e}"

# =========================================================
# ------------------- NEW FEATURES -------------------------
# =========================================================

# New: Performance metrics tracking
def track_performance_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Track various performance metrics for the dashboard"""
    metrics = {
        "data_load_time": time.time(),
        "total_records": len(df),
        "date_range_days": (df["Tanggal Stock Opname"].max() - df["Tanggal Stock Opname"].min()).days,
        "unique_products": df["PLU"].nunique(),
        "unique_tags": df["Tag"].nunique(),
        "total_variance_value": df["Selisih Value (Rp)"].sum(),
        "total_variance_qty": df["Selisih Qty (Pcs)"].sum(),
        "positive_variance_pct": len(df[df["Selisih Value (Rp)"] > 0]) / len(df) * 100,
        "negative_variance_pct": len(df[df["Selisih Value (Rp)"] < 0]) / len(df) * 100,
    }
    return metrics

# New: Alert system for critical issues
def check_for_alerts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Check for critical issues that need attention"""
    alerts = []
    
    # Check for high negative variance
    negative_threshold = -1000000  # Rp 1 juta
    high_negative = df[df["Selisih Value (Rp)"] < negative_threshold]
    if not high_negative.empty:
        alerts.append({
            "type": "error",
            "title": "Varians Negatif Tinggi",
            "message": f"{len(high_negative)} produk memiliki varians negatif lebih dari {format_currency(negative_threshold)}",
            "data": high_negative[["PLU", "DESCP", "Selisih Value (Rp)"]].head(5)
        })
    
    # Check for outliers
    outliers = detect_outliers_iqr(df, "Selisih Value (Rp)")
    if len(outliers) > len(df) * 0.1:  # More than 10% outliers
        alerts.append({
            "type": "warning",
            "title": "Banyak Outlier Terdeteksi",
            "message": f"{len(outliers)} produk ({len(outliers)/len(df)*100:.1f}%) terdeteksi sebagai outlier",
            "data": None
        })
    
    # Check for data quality issues
    null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if null_percentage > 5:  # More than 5% null values
        alerts.append({
            "type": "warning",
            "title": "Kualitas Data Rendah",
            "message": f"{null_percentage:.1f}% data memiliki nilai null",
            "data": None
        })
    
    return alerts

# New: Advanced filtering options
def render_advanced_filters(df: pd.DataFrame) -> Dict[str, Any]:
    """Render advanced filtering options"""
    with st.expander("🔍 Advanced Filters", expanded=False):
        # Value range filter - PERBAIKAN DI SINI
        min_value = float(df["Selisih Value (Rp)"].min())
        max_value = float(df["Selisih Value (Rp)"].max())
        
        # Ensure min_value < max_value and both are finite
        if not np.isfinite(min_value) or not np.isfinite(max_value) or min_value >= max_value:
            # Set default values if there's an issue with the data
            min_value = -1000000.0
            max_value = 1000000.0
        
        # Round to reasonable values for the slider
        min_value = round(min_value, -4)  # Round to nearest 10,000
        max_value = round(max_value, -4)  # Round to nearest 10,000
        
        # Ensure we have a reasonable range
        if max_value - min_value < 10000:
            min_value -= 5000
            max_value += 5000
        
        value_range = st.slider(
            "Rentang Varians Nilai (Rp)",
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value),
            step=10000
        )
        
        # Quantity range filter
        min_qty = int(df["Selisih Qty (Pcs)"].min())
        max_qty = int(df["Selisih Qty (Pcs)"].max())
        
        # Ensure min_qty < max_qty and both are finite
        if not np.isfinite(min_qty) or not np.isfinite(max_qty) or min_qty >= max_qty:
            # Set default values if there's an issue with the data
            min_qty = -100
            max_qty = 100
        
        # Ensure we have a reasonable range
        if max_qty - min_qty < 10:
            min_qty -= 5
            max_qty += 5
        
        qty_range = st.slider(
            "Rentang Varians Kuantitas (Pcs)",
            min_value=min_qty,
            max_value=max_qty,
            value=(min_qty, max_qty),
            step=1
        )
        
        # Product search
        search_term = st.text_input("Cari Produk (PLU atau Deskripsi)")
        
        # Sort options
        sort_by = st.selectbox(
            "Urutkan berdasarkan",
            options=["Tanggal Stock Opname", "Selisih Value (Rp)", "Selisih Qty (Pcs)", "Varians Nilai Absolut"],
            index=1
        )
        
        sort_order = st.radio(
            "Urutan",
            options=["Ascending", "Descending"],
            horizontal=True
        )
        
        return {
            "value_range": value_range,
            "qty_range": qty_range,
            "search_term": search_term,
            "sort_by": sort_by,
            "sort_order": sort_order
        }

# New: Apply advanced filters
def apply_advanced_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply advanced filters to the dataframe"""
    filtered_df = df.copy()
    
    # Apply value range filter
    min_val, max_val = filters["value_range"]
    filtered_df = filtered_df[
        (filtered_df["Selisih Value (Rp)"] >= min_val) &
        (filtered_df["Selisih Value (Rp)"] <= max_val)
    ]
    
    # Apply quantity range filter
    min_qty, max_qty = filters["qty_range"]
    filtered_df = filtered_df[
        (filtered_df["Selisih Qty (Pcs)"] >= min_qty) &
        (filtered_df["Selisih Qty (Pcs)"] <= max_qty)
    ]
    
    # Apply search filter
    if filters["search_term"]:
        search_term = filters["search_term"].lower()
        filtered_df = filtered_df[
            filtered_df["PLU"].astype(str).str.lower().str.contains(search_term) |
            filtered_df["DESCP"].astype(str).str.lower().str.contains(search_term)
        ]
    
    # Apply sorting
    sort_by = filters["sort_by"]
    ascending = filters["sort_order"] == "Ascending"
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
    
    return filtered_df

# New: Export functionality
def export_data(df: pd.DataFrame, format_type: str = "csv") -> bytes:
    """Export data in different formats"""
    if format_type == "csv":
        return df.to_csv(index=False).encode('utf-8')
    elif format_type == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Stock Variance')
        return output.getvalue()
    elif format_type == "json":
        return df.to_json(orient='records').encode('utf-8')
    return b""

# =========================================================
# ----------------------- SIDEBAR -------------------------
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: var(--primary); margin-bottom: 0.5rem;">🎛️ Control Center</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0;">Configure dashboard parameters</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Connection Status
    try:
        spreadsheet_url = st.secrets["spreadsheet"]["url"]
        st.markdown(
            '<div class="status-indicator status-connected">✅ Connected to Google Sheets</div>', 
            unsafe_allow_html=True
        )
    except (KeyError, FileNotFoundError):
        spreadsheet_url = st.text_input(
            "🔗 URL Google Spreadsheet",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Masukkan URL Google Sheets yang berisi data stok opname"
        )
        if not spreadsheet_url:
            st.markdown(
                '<div class="status-indicator status-warning">⚠️ URL Required</div>', 
                unsafe_allow_html=True
            )

    sheet_name = st.text_input(
        "📄 Nama Worksheet",
        value="Sheet1",
        help="Nama worksheet di Google Sheets (case sensitive)"
    )

    st.markdown("---")

    st.markdown("### ⚙️ Configuration")
    
    metric_selection = st.radio(
        "📊 Primary Metric",
        options=["Nilai (Rp)", "Kuantitas (Pcs)"],
        horizontal=True
    )
    
    top_n = st.slider(
        "🔝 Top Products to Display",
        min_value=5,
        max_value=30,
        value=10,
        step=1,
        help="Number of top products to show in charts"
    )

    st.markdown("---")

    if st.button("🔄 Reset All Filters", use_container_width=True, type="secondary"):
        for key in ("date_range", "tags", "direction", "advanced_filters"):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# =========================================================
# ---------------------- MAIN APP -------------------------
# =========================================================

# Hero Section
st.markdown(
    """
    <div class="hero-section fade-in">
        <div class="hero-title">📊 Stock Variance Analytics Dashboard</div>
        <div class="hero-subtitle">
            Advanced analytics dan AI-powered insights untuk monitoring varians stok opname secara real-time.
            Transformasi data menjadi strategic intelligence untuk optimasi inventory management.
        </div>
        <div class="hero-badge">🏪 Toko: 2GC6 BAROS PANDEGLANG</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Validation
if not spreadsheet_url.strip():
    st.warning("⚠️ Silakan masukkan URL Google Spreadsheet untuk memulai analisis.")
    st.stop()

# Data Loading
with st.spinner("🔄 Loading and processing data from Google Sheets..."):
    dataframe = load_data(spreadsheet_url, sheet_name)

if dataframe is None or dataframe.empty:
    st.error("❌ Tidak dapat memproses data. Periksa kembali koneksi dan format data.")
    st.stop()

# Initialize Gemini AI
gemini_model = configure_gemini()
if gemini_model:
    st.sidebar.markdown(
        '<div class="status-indicator status-connected">🤖 Gemini AI Ready</div>', 
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        '<div class="status-indicator status-error">❌ AI Unavailable</div>', 
        unsafe_allow_html=True
    )

# Track performance metrics
performance_metrics = track_performance_metrics(dataframe)

# Check for alerts
alerts = check_for_alerts(dataframe)

# Display alerts if any
if alerts:
    st.markdown("### 🚨 Alerts & Notifications")
    for alert in alerts:
        alert_class = f"alert-{alert['type']}"
        st.markdown(
            f"""
            <div class="alert-box {alert_class}">
                <span><strong>{alert['title']}</strong></span>
                <span>{alert['message']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if alert['data'] is not None:
            st.dataframe(alert['data'], use_container_width=True)

# Filter Controls
min_date = dataframe["Tanggal Stock Opname"].min().to_pydatetime()
max_date = dataframe["Tanggal Stock Opname"].max().to_pydatetime()
available_tags = sorted(dataframe["Tag"].unique().tolist())
available_tags_display = ["Semua"] + available_tags
directions = ["Semua", "Positif", "Negatif", "Netral"]

with st.sidebar:
    st.markdown("### 🎯 Filters")
    
    selected_date_range = st.date_input(
        "📅 Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range",
        help="Select date range for analysis"
    )
    
    selected_tags = st.multiselect(
        "🏷️ Filter by Tags",
        options=available_tags_display,
        default=["Semua"],
        key="tags",
        help="Select specific product categories"
    )
    
    selected_direction = st.multiselect(
        "🎯 Variance Direction",
        options=directions,
        default=["Semua"],
        key="direction",
        help="Filter by variance direction"
    )

# Apply Filters
filtered_df = filter_dataframe(
    dataframe,
    date_range=selected_date_range,
    selected_tags=selected_tags,
    selected_direction=selected_direction
)

# Advanced Filters - PERBAIKAN DI SINI
# Cek apakah filtered_df kosong sebelum membuat advanced filters
if not filtered_df.empty:
    advanced_filters = render_advanced_filters(filtered_df)
    filtered_df = apply_advanced_filters(filtered_df, advanced_filters)
else:
    st.warning("⚠️ Filter tidak menghasilkan data. Silakan sesuaikan parameter filter.")
    st.stop()

if filtered_df.empty:
    st.warning("⚠️ Filter tidak menghasilkan data. Silakan sesuaikan parameter filter.")
    st.stop()

# =========================================================
# --------------------- KPI DASHBOARD ---------------------
# =========================================================
st.markdown("## 📈 Executive Summary")

# Calculate KPIs
total_qty = filtered_df["Selisih Qty (Pcs)"].sum()
total_value = filtered_df["Selisih Value (Rp)"].sum()
total_plu = filtered_df["PLU"].nunique()
positive_value = filtered_df.loc[filtered_df["Selisih Value (Rp)"] > 0, "Selisih Value (Rp)"].sum()
negative_value = filtered_df.loc[filtered_df["Selisih Value (Rp)"] < 0, "Selisih Value (Rp)"].sum()
positive_qty = filtered_df.loc[filtered_df["Selisih Qty (Pcs)"] > 0, "Selisih Qty (Pcs)"].sum()
negative_qty = filtered_df.loc[filtered_df["Selisih Qty (Pcs)"] < 0, "Selisih Qty (Pcs)"].sum()

# Render KPI Cards
st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)

render_metric_card(
    "Total Variance Value",
    format_currency(total_value),
    delta_label=f"↗️ {format_currency(positive_value)} | ↘️ {format_currency(negative_value)}",
    delta_type="neutral",
    icon="💰"
)

render_metric_card(
    "Total Variance Quantity",
    f"{format_quantity(total_qty)} Pcs",
    delta_label=f"↗️ {format_quantity(positive_qty)} | ↘️ {format_quantity(negative_qty)}",
    delta_type="neutral",
    icon="📦"
)

render_metric_card(
    "Products Analyzed",
    f"{format_quantity(total_plu)} SKUs",
    delta_label=f"Unique products in dataset",
    delta_type="neutral",
    icon="🛒"
)

render_metric_card(
    "Average Variance per SKU",
    format_currency(total_value / total_plu if total_plu else 0),
    delta_label="Mean variance impact",
    delta_type="neutral",
    icon="📊"
)

st.markdown('</div>', unsafe_allow_html=True)

# Key Insights
st.markdown("## 🔍 Key Insights")
highlight_insights(filtered_df)

st.markdown("---")

# =========================================================
# -------------------- MAIN ANALYTICS ---------------------
# =========================================================

tab_labels = [
    "🤖 AI Insights", 
    "🏆 Product Analysis", 
    "📈 Trend Analysis", 
    "🏷️ Category Analysis", 
    "🔍 Correlation", 
    "🗺️ Distribution Map",
    "📊 Data Profiling"
]

tabs = st.tabs(tab_labels)

with tabs[0]:  # AI Insights
    st.markdown("### 🤖 AI-Powered Analysis")
    
    if gemini_model is None:
        st.error("❌ Model Gemini tidak tersedia. Pastikan API key sudah dikonfigurasi dengan benar.")
        st.info("💡 Untuk menggunakan fitur AI, tambahkan Gemini API key di Streamlit secrets.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧠 Generate Smart Insights", type="primary", use_container_width=True):
                with st.spinner("🔍 AI sedang menganalisis data..."):
                    insights = generate_data_insights(filtered_df, gemini_model)
                    
                    st.markdown('<div class="ai-response fade-in">', unsafe_allow_html=True)
                    st.markdown("### 💡 AI Analysis Results")
                    st.markdown(insights)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("📋 Generate Strategic Recommendations", type="secondary", use_container_width=True):
                with st.spinner("💡 Generating strategic recommendations..."):
                    recommendations = generate_recommendations(filtered_df, gemini_model)
                    
                    st.markdown('<div class="ai-response fade-in">', unsafe_allow_html=True)
                    st.markdown("### 🎯 Strategic Recommendations")
                    st.markdown(recommendations)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Q&A Section
        st.markdown("### ❓ Ask Questions About Your Data")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            question = st.text_input(
                "Ask anything about your stock variance data:",
                placeholder="e.g., What are the main causes of negative variance?",
                key="ai_question"
            )
        
        with col2:
            ask_button = st.button("🚀 Ask AI", type="primary", use_container_width=True)
        
        if ask_button and question:
            with st.spinner("🤔 AI is thinking..."):
                answer = answer_data_question(filtered_df, question, gemini_model)
                
                st.markdown('<div class="ai-response slide-up">', unsafe_allow_html=True)
                st.markdown(f"**Q:** {question}")
                st.markdown(f"**A:** {answer}")
                st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:  # Product Analysis
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(
        create_top_products_chart(filtered_df, metric_selection, top_n), 
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:  # Trend Analysis
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(
        create_trend_chart(filtered_df, metric_selection), 
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[3]:  # Category Analysis
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(
        create_tag_analysis_chart(filtered_df, metric_selection), 
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[4]:  # Correlation
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_scatter_chart(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[5]:  # Distribution Map
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_treemap_chart(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[6]:  # Data Profiling
    st.markdown("### 📊 Data Quality & Profiling")
    
    # Data Quality Report
    with st.expander("📋 Data Quality Report", expanded=True):
        quality_report = create_data_quality_report(filtered_df)
        st.dataframe(quality_report, use_container_width=True)
    
    # Distribution Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(
            create_distribution_chart(filtered_df, "Selisih Value (Rp)"), 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(
            create_box_plot(filtered_df, "Selisih Value (Rp)"), 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(
            create_distribution_chart(filtered_df, "Selisih Qty (Pcs)"), 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(
            create_box_plot(filtered_df, "Selisih Qty (Pcs)"), 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Correlation Matrix
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_correlation_matrix(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# -------------------- DATA TABLE -------------------------
# =========================================================
st.markdown("---")

with st.expander("📄 Detailed Data View", expanded=False):
    # Prepare display data
    df_display = filtered_df.copy()
    df_display["Tanggal Stock Opname"] = df_display["Tanggal Stock Opname"].dt.strftime("%Y-%m-%d")
    df_display["Selisih Qty (Pcs)"] = df_display["Selisih Qty (Pcs)"].apply(format_quantity)
    df_display["Selisih Value (Rp)"] = df_display["Selisih Value (Rp)"].apply(format_currency)
    df_display["Varians Nilai Absolut"] = df_display["Varians Nilai Absolut"].apply(format_currency)
    df_display["Varians Qty Absolut"] = df_display["Varians Qty Absolut"].apply(format_quantity)
    
    # Display options
    col1, col2, col3 = st.columns(3)
    with col1:
        show_all = st.checkbox("Show All Records", value=False)
    with col2:
        if not show_all:
            max_rows = st.number_input("Max Rows", min_value=10, max_value=1000, value=100)
        else:
            max_rows = len(df_display)
    with col3:
        export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
        if st.button("📥 Export Data"):
            data = export_data(filtered_df, export_format.lower())
            st.download_button(
                label=f"Download {export_format}",
                data=data,
                file_name=f"stock_variance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format.lower()}",
                mime=f"application/{export_format.lower()}"
            )
    
    st.dataframe(
        df_display.head(max_rows) if not show_all else df_display, 
        use_container_width=True, 
        hide_index=True
    )
    
    if not show_all and len(df_display) > max_rows:
        st.info(f"Showing {max_rows} of {len(df_display)} records. Check 'Show All Records' to see complete data.")

# =========================================================
# ----------------------- FOOTER ---------------------------
# =========================================================
st.markdown(
    """
    <div class="footer">
        <strong>Stock Variance Analytics Dashboard</strong><br>
        Powered by Streamlit • Plotly • Gemini AI<br>
        <em>Transforming inventory data into strategic insights</em><br><br>
        © 2025 - Professional Analytics Suite
    </div>
    """,
    unsafe_allow_html=True
)
