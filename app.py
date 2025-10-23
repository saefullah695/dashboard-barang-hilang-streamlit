import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
from typing import Optional, Tuple, List
import numpy as np
from scipy import stats
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import google.generativeai as genai
import json
import time
from streamlit_lottie import st_lottie
import requests

# =========================================================
# ------------------- KONFIGURASI AWAL --------------------
# =========================================================
st.set_page_config(
    page_title="Dashboard Varians Stok Opname",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palet warna profesional yang lebih ditingkatkan
COLOR_PRIMARY = "#4F46E5"     # Indigo
COLOR_SECONDARY = "#7C3AED"   # Violet
COLOR_ACCENT = "#06B6D4"      # Cyan
COLOR_SUCCESS = "#10B981"     # Emerald
COLOR_WARNING = "#F59E0B"     # Amber
COLOR_DANGER = "#EF4444"      # Red
COLOR_INFO = "#3B82F6"        # Blue
COLOR_BG = "#0F172A"          # Dark Blue
COLOR_CARD = "rgba(15, 23, 42, 0.75)"
COLOR_BORDER = "rgba(148, 163, 184, 0.15)"
COLOR_HOVER = "rgba(99, 102, 241, 0.15)"

PLOTLY_COLORWAY = [
    "#4F46E5", "#7C3AED", "#06B6D4", "#10B981", "#F59E0B",
    "#EF4444", "#3B82F6", "#EC4899", "#8B5CF6", "#14B8A6"
]

CUSTOM_CSS = """
<style>
:root {
    --color-primary: #4F46E5;
    --color-secondary: #7C3AED;
    --color-accent: #06B6D4;
    --color-success: #10B981;
    --color-warning: #F59E0B;
    --color-danger: #EF4444;
    --color-info: #3B82F6;
    --color-bg: #0F172A;
    --color-bg-secondary: rgba(15, 23, 42, 0.85);
    --color-card: rgba(15, 23, 42, 0.75);
    --color-border: rgba(148, 163, 184, 0.15);
    --color-text: #E2E8F0;
    --color-text-muted: #94A3B8;
    --color-highlight: rgba(99, 102, 241, 0.15);
    --radius: 16px;
    --blur: 20px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

body {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--color-text);
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    background-attachment: fixed;
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

section.main > div {
    padding-top: 1.5rem;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--color-text) !important;
    font-weight: 700;
    letter-spacing: -0.025em;
}

.stTabs [role="tablist"] {
    gap: 0.5rem;
    background: rgba(15, 23, 42, 0.5);
    padding: 0.5rem;
    border-radius: var(--radius);
    border: 1px solid var(--color-border);
}

.stTabs [role="tab"] {
    padding: 0.75rem 1.25rem;
    background: transparent;
    border-radius: calc(var(--radius) - 4px);
    border: 1px solid transparent;
    transition: var(--transition);
    color: var(--color-text-muted);
    font-weight: 600;
    position: relative;
    overflow: hidden;
}

.stTabs [role="tab"]:hover {
    background: var(--color-highlight);
    color: var(--color-accent);
}

.stTabs [aria-selected="true"] {
    background: var(--color-primary);
    color: white;
    box-shadow: 0 4px 12px -2px rgba(79, 70, 229, 0.4);
}

[data-testid="stSidebar"] {
    background: var(--color-bg-secondary);
    border-right: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
}

[data-testid="stSidebar"] * {
    color: var(--color-text);
}

.stButton button, .stDownloadButton button {
    border-radius: 8px !important;
    background: var(--color-primary);
    color: white;
    border: 1px solid var(--color-primary);
    transition: var(--transition);
    font-weight: 600;
    letter-spacing: 0.025em;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.stButton button:hover, .stDownloadButton button:hover {
    background: var(--color-secondary);
    border-color: var(--color-secondary);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

.metric-grid {
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.metric-card {
    background: var(--color-card);
    border-radius: var(--radius);
    padding: 1.5rem;
    border: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.metric-card .metric-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    display: inline-block;
    padding: 0.5rem;
    background: var(--color-highlight);
    border-radius: 8px;
}

.metric-card .metric-label {
    font-size: 0.875rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--color-text-muted);
    margin-bottom: 0.5rem;
}

.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text);
    margin: 0.25rem 0 0.5rem;
}

.metric-card .metric-delta {
    display: inline-flex;
    gap: 0.25rem;
    align-items: center;
    font-size: 0.875rem;
    font-weight: 600;
}

.delta-positive { color: var(--color-success); }
.delta-negative { color: var(--color-danger); }
.delta-neutral { color: var(--color-warning); }

.hero-card {
    background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
    border-radius: var(--radius);
    padding: 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.hero-card::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    animation: float 20s infinite linear;
}

@keyframes float {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.hero-card h1 {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    color: white;
}

.hero-card p {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.125rem;
    max-width: 65ch;
    line-height: 1.6;
}

.insight-card {
    background: var(--color-card);
    border-radius: var(--radius);
    border: 1px solid var(--color-border);
    padding: 1.5rem;
    backdrop-filter: blur(var(--blur));
    position: relative;
    overflow: hidden;
    transition: var(--transition);
}

.insight-card:hover {
    border-color: var(--color-primary);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.insight-card strong {
    color: var(--color-accent);
}

.stDataFrame {
    border-radius: var(--radius);
    border: 1px solid var(--color-border);
    overflow: hidden;
}

[data-testid="stDataFrame"] div[role="table"] {
    border-radius: 0;
}

.chart-container {
    background: var(--color-card);
    border-radius: var(--radius);
    border: 1px solid var(--color-border);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.feature-card {
    background: var(--color-card);
    border-radius: var(--radius);
    padding: 1.5rem;
    border: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
    margin-bottom: 1rem;
    transition: var(--transition);
}

.feature-card:hover {
    transform: translateY(-3px);
    border-color: var(--color-primary);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.feature-card h4 {
    color: var(--color-primary);
    margin-bottom: 0.5rem;
}

.feature-card p {
    color: var(--color-text-muted);
    font-size: 0.9rem;
    margin-bottom: 0;
}

.ai-response {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(79, 70, 229, 0.1));
    border-radius: var(--radius);
    border: 1px solid rgba(6, 182, 212, 0.2);
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(var(--blur));
}

.ai-response h4 {
    color: var(--color-accent);
    margin-bottom: 0.75rem;
}

.ai-response p {
    color: var(--color-text);
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 0;
}

.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
}

.status-success {
    background: rgba(16, 185, 129, 0.1);
    color: var(--color-success);
}

.status-warning {
    background: rgba(245, 158, 11, 0.1);
    color: var(--color-warning);
}

.status-danger {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-danger);
}

.filter-section {
    background: var(--color-card);
    border-radius: var(--radius);
    padding: 1.5rem;
    border: 1px solid var(--color-border);
    margin-bottom: 1.5rem;
}

.export-button {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    z-index: 999;
}

.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 200px;
    background-color: var(--color-bg);
    color: var(--color-text);
    text-align: center;
    border-radius: 6px;
    padding: 8px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -100px;
    opacity: 0;
    transition: opacity 0.3s;
    border: 1px solid var(--color-border);
    font-size: 0.875rem;
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}

@media (max-width: 768px) {
    .metric-grid {
        grid-template-columns: 1fr;
    }
    
    .hero-card h1 {
        font-size: 1.875rem;
    }
    
    .export-button {
        bottom: 1rem;
        right: 1rem;
    }
}

.loading-animation {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100px;
}

.loading-spinner {
    width: 50px;
    height: 50px;
    border: 5px solid rgba(79, 70, 229, 0.2);
    border-radius: 50%;
    border-top-color: var(--color-primary);
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================================================
# ----------------- KONFIGURASI PLOTLY --------------------
# =========================================================
def configure_plotly_theme() -> None:
    template = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, 'Segoe UI', sans-serif", color="#E2E8F0"),
            title=dict(font=dict(size=22, family="Inter, 'Segoe UI', sans-serif", color="#F8FAFC")),
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0.35)",
            legend=dict(
                bgcolor="rgba(15, 23, 42, 0.6)",
                bordercolor="rgba(148, 163, 184, 0.25)",
                borderwidth=1,
                font=dict(size=13)
            ),
            margin=dict(l=60, r=40, t=80, b=60),
            xaxis=dict(gridcolor="rgba(148,163,184,0.22)", zerolinecolor="rgba(148,163,184,0.32)"),
            yaxis=dict(gridcolor="rgba(148,163,184,0.22)", zerolinecolor="rgba(148,163,184,0.32)"),
            colorway=PLOTLY_COLORWAY,
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.8)", font_size=13, font_family="Inter")
        )
    )
    pio.templates["professional"] = template
    px.defaults.template = "professional"
    px.defaults.color_discrete_sequence = PLOTLY_COLORWAY

configure_plotly_theme()

# =========================================================
# ------------------- FUNGSI UTILITAS ---------------------
# =========================================================
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

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
    icon: str = "📌",
    status: Optional[str] = None
) -> None:
    delta_class = {
        "positive": "delta-positive",
        "negative": "delta-negative",
        "neutral": "delta-neutral"
    }.get(delta_type, "delta-neutral")

    delta_markup = ""
    if delta_label:
        delta_markup = f'<div class="metric-delta {delta_class}">{delta_label}</div>'

    status_markup = ""
    if status:
        status_class = {
            "success": "status-success",
            "warning": "status-warning",
            "danger": "status-danger"
        }.get(status, "status-success")
        status_markup = f'<div class="status-indicator {status_class}">{status}</div>'

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_markup}
            {status_markup}
        </div>
        """,
        unsafe_allow_html=True
    )

@st.cache_data(ttl=600, show_spinner=False)
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
        st.error(f"Gagal memuat data: {exc}")
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
        st.error("Kolom 'Tanggal Stock Opname' tidak ditemukan pada sheet.")
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
            text="Varians tidak ditemukan.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Top Produk</b>", title_x=0.5)
        return fig

    fig = px.bar(
        top_products,
        x="Varians",
        y="DESCP",
        orientation="h",
        color="Varians",
        color_continuous_scale=[COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS],
        labels={"Varians": label_metric, "DESCP": "Deskripsi Produk"},
        title=f"<b>Top {top_n} Produk dengan Varians {metric} Tertinggi</b>",
        height=520
    )
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        title_x=0.5,
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.8)", font_size=13)
    )
    fig.add_vline(x=0, line_width=1, line_color="rgba(148,163,184,0.35)", line_dash="dot")
    return fig

def create_trend_chart(df: pd.DataFrame, metric: str) -> go.Figure:
    metric_column = "Selisih Value (Rp)" if metric == "Nilai (Rp)" else "Selisih Qty (Pcs)"
    label_y = "Total Varians Nilai (Rp)" if metric == "Nilai (Rp)" else "Total Varians Kuantitas (Pcs)"
    min_date = df["Tanggal Stock Opname"].min()
    max_date = df["Tanggal Stock Opname"].max()
    date_range = (max_date - min_date).days

    if min_date.date() == max_date.date():
        fig = go.Figure()
        fig.add_annotation(
            text=f"Data hanya tersedia pada <b>{min_date.strftime('%d %B %Y')}</b>",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(title="<b>Tren Varians</b>", title_x=0.5)
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
            line=dict(color=COLOR_PRIMARY, width=3),
            marker=dict(size=6)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data["Tanggal Stock Opname"],
            y=trend_data["MA_7"],
            mode="lines",
            name="Moving Average (7 Hari)",
            line=dict(color=COLOR_ACCENT, width=3, dash="dot")
        ))
        fig.update_layout(
            title="<b>Tren Varians Harian</b>",
            xaxis_title="Tanggal",
            yaxis_title=label_y,
            title_x=0.5,
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.8)", font_size=13)
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
            color_continuous_scale=[COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS],
            labels={"Tanggal Stock Opname": "Periode", "Varians": label_y},
            title="<b>Tren Varians Bulanan</b>",
            height=480
        )
        fig.update_layout(title_x=0.5, coloraxis_showscale=False)
        fig.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.35)", line_dash="dot")

    return fig

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
        color_continuous_scale=[COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS],
        labels={"Varians": label_metric, "Tag": "Kategori (Tag)"},
        title="<b>Varians per Kategori (Tag)</b>",
        height=520
    )
    fig.update_layout(title_x=0.5, yaxis=dict(categoryorder="total ascending"))
    fig.add_vline(x=0, line_width=1, line_color="rgba(148,163,184,0.32)", line_dash="dot")
    return fig

def create_scatter_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="Selisih Qty (Pcs)",
        y="Selisih Value (Rp)",
        hover_data=["PLU", "DESCP", "Tag"],
        color="Tag",
        color_discrete_sequence=PLOTLY_COLORWAY,
        title="<b>Varians Kuantitas vs Nilai</b>",
        trendline="ols" if len(df) > 10 else None,
        height=520
    )
    fig.update_layout(title_x=0.5)
    fig.add_hline(y=0, line_width=1, line_color="rgba(148,163,184,0.32)", line_dash="dot")
    fig.add_vline(x=0, line_width=1, line_color="rgba(148,163,184,0.32)", line_dash="dot")
    return fig

def create_treemap_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Tidak ada data untuk treemap.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Treemap Varians</b>", title_x=0.5)
        return fig
    fig = px.treemap(
        df,
        path=["Tag", "DESCP"],
        values="Varians Nilai Absolut",
        color="Selisih Value (Rp)",
        color_continuous_scale=[COLOR_DANGER, "#94A3B8", COLOR_SUCCESS],
        color_continuous_midpoint=0,
        title="<b>Treemap Varians Nilai per Tag & Produk</b>",
        height=520
    )
    fig.update_layout(title_x=0.5, margin=dict(t=80, l=30, r=30, b=30))
    return fig

def create_sunburst_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Tidak ada data untuk sunburst.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Sunburst Varians</b>", title_x=0.5)
        return fig
    
    # Aggregate data for sunburst
    sunburst_data = df.groupby(["Tag", "Arah Varians"]).agg({
        "Selisih Value (Rp)": "sum",
        "Varians Nilai Absolut": "sum"
    }).reset_index()
    
    fig = px.sunburst(
        sunburst_data,
        path=["Tag", "Arah Varians"],
        values="Varians Nilai Absolut",
        color="Selisih Value (Rp)",
        color_continuous_scale=[COLOR_DANGER, "#94A3B8", COLOR_SUCCESS],
        color_continuous_midpoint=0,
        title="<b>Sunburst Varians per Kategori</b>",
        height=520
    )
    fig.update_layout(title_x=0.5)
    return fig

def create_pie_chart(df: pd.DataFrame, column: str) -> go.Figure:
    if column not in df.columns or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Kolom '{column}' tidak ditemukan atau data kosong.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title=f"<b>Distribusi {column}</b>", title_x=0.5)
        return fig
    
    pie_data = df[column].value_counts().reset_index()
    pie_data.columns = [column, "Count"]
    
    fig = px.pie(
        pie_data,
        values="Count",
        names=column,
        title=f"<b>Distribusi {column}</b>",
        color_discrete_sequence=PLOTLY_COLORWAY,
        height=500
    )
    fig.update_layout(title_x=0.5)
    return fig

def create_heatmap(df: pd.DataFrame, x_col: str, y_col: str, value_col: str) -> go.Figure:
    if any(col not in df.columns for col in [x_col, y_col, value_col]) or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Kolom yang diperlukan tidak ditemukan atau data kosong.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Heatmap</b>", title_x=0.5)
        return fig
    
    # Create pivot table for heatmap
    heatmap_data = df.pivot_table(
        values=value_col,
        index=y_col,
        columns=x_col,
        aggfunc="sum",
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdBu',
        zmid=0,
        text=heatmap_data.round(0).values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=f"<b>Heatmap {value_col} per {x_col} dan {y_col}</b>",
        title_x=0.5,
        xaxis_title=x_col,
        yaxis_title=y_col
    )
    
    return fig

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

def render_insight_card(title: str, value: str, description: str, icon: str = "✨") -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <h4>{icon} {title}</h4>
            <p><strong>{value}</strong></p>
            <p style="color: var(--color-text-muted); margin-bottom: 0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def highlight_insights(df: pd.DataFrame) -> None:
    if df.empty:
        return

    tag_summary = aggregate_tag_summary(df)
    biggest_positive = df[df["Selisih Value (Rp)"] > 0].sort_values("Selisih Value (Rp)", ascending=False).head(1)
    biggest_negative = df[df["Selisih Value (Rp)"] < 0].sort_values("Selisih Value (Rp)").head(1)
    outliers_value = detect_outliers_iqr(df, "Selisih Value (Rp)")
    outlier_count = len(outliers_value)

    col1, col2 = st.columns(2, gap="large")
    with col1:
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
                description=f"Menyumbang {format_currency(top_tag_value)} • {kontribusi:.1f}% dari total varians.",
                icon="🏷️"
            )
        else:
            render_insight_card(
                title="Tag Dominan",
                value="Tidak tersedia",
                description="Pastikan data memiliki kolom Tag.",
                icon="🏷️"
            )

        if not biggest_positive.empty:
            row = biggest_positive.iloc[0]
            render_insight_card(
                title="Varians Positif Tertinggi",
                value=row["DESCP"],
                description=f"Selisih nilai {format_currency(row['Selisih Value (Rp)'])} • {format_quantity(row['Selisih Qty (Pcs)'])} pcs.",
                icon="📈"
            )
        else:
            render_insight_card(
                title="Varians Positif Tertinggi",
                value="Belum ada varians positif",
                description="Data positif tidak ditemukan untuk filter saat ini.",
                icon="📈"
            )

    with col2:
        if not biggest_negative.empty:
            row = biggest_negative.iloc[0]
            render_insight_card(
                title="Varians Negatif Terbesar",
                value=row["DESCP"],
                description=f"Selisih nilai {format_currency(row['Selisih Value (Rp)'])} • {format_quantity(row['Selisih Qty (Pcs)'])} pcs.",
                icon="📉"
            )
        else:
            render_insight_card(
                title="Varians Negatif Terbesar",
                value="Belum ada varians negatif",
                description="Data negatif tidak ditemukan untuk filter saat ini.",
                icon="📉"
            )

        render_insight_card(
            title="Deteksi Outlier",
            value=f"{outlier_count} produk",
            description="Gunakan insight ini untuk audit mendalam terhadap varians ekstrem.",
            icon="🚨"
        )

        if outlier_count > 0:
            with st.expander("Lihat detail outlier"):
                st.dataframe(
                    outliers_value[["PLU", "DESCP", "Selisih Value (Rp)", "Selisih Qty (Pcs)", "Tag"]],
                    use_container_width=True
                )

# =========================================================
# ------------------- FUNGSI DATA PROFILING -----------------
# =========================================================
def create_distribution_chart(df: pd.DataFrame, column: str) -> go.Figure:
    fig = go.Figure()
    
    # Histogram
    fig.add_trace(go.Histogram(
        x=df[column],
        nbinsx=30,
        name='Distribusi',
        marker_color=COLOR_PRIMARY,
        opacity=0.7
    ))
    
    # Mean line
    mean_val = df[column].mean()
    fig.add_vline(
        x=mean_val, 
        line_width=2, 
        line_dash="dash", 
        line_color=COLOR_ACCENT,
        annotation_text=f"Mean: {mean_val:.2f}",
        annotation_position="top right"
    )
    
    # Median line
    median_val = df[column].median()
    fig.add_vline(
        x=median_val, 
        line_width=2, 
        line_dash="dash", 
        line_color=COLOR_WARNING,
        annotation_text=f"Median: {median_val:.2f}",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title=f"<b>Distribusi {column}</b>",
        xaxis_title=column,
        yaxis_title="Frekuensi",
        title_x=0.5,
        showlegend=False
    )
    
    return fig

def create_box_plot(df: pd.DataFrame, column: str) -> go.Figure:
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=df[column],
        name=column,
        marker_color=COLOR_PRIMARY,
        boxpoints='outliers'
    ))
    
    fig.update_layout(
        title=f"<b>Box Plot {column}</b>",
        yaxis_title=column,
        title_x=0.5,
        showlegend=False
    )
    
    return fig

def create_correlation_matrix(df: pd.DataFrame) -> go.Figure:
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Tidak ada kolom numerik untuk analisis korelasi.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Matriks Korelasi</b>", title_x=0.5)
        return fig
    
    # Calculate correlation matrix
    corr_matrix = numeric_df.corr()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="<b>Matriks Korelasi</b>",
        title_x=0.5,
        width=600,
        height=500
    )
    
    return fig

def create_data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    # Create a data quality report
    report = pd.DataFrame({
        'Kolom': df.columns,
        'Tipe Data': df.dtypes.values,
        'Total Nilai Non-Null': df.count().values,
        'Total Nilai Null': df.isnull().sum().values,
        '% Nilai Null': (df.isnull().sum() / len(df) * 100).round(2).values,
        'Total Nilai Unik': df.nunique().values,
        'Nilai Paling Sering': [df[col].mode()[0] if not df[col].mode().empty else '-' for col in df.columns]
    })
    
    return report

def create_feature_importance_chart(df: pd.DataFrame) -> go.Figure:
    # Simple feature importance based on correlation with target variable
    target_col = "Selisih Value (Rp)"
    
    if target_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Kolom target '{target_col}' tidak ditemukan.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Importance Fitur</b>", title_x=0.5)
        return fig
    
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if target_col not in numeric_df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Kolom target '{target_col}' bukan numerik.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Importance Fitur</b>", title_x=0.5)
        return fig
    
    # Calculate correlation with target
    corr_with_target = numeric_df.corr()[target_col].abs().sort_values(ascending=False)
    
    # Remove target itself
    corr_with_target = corr_with_target.drop(target_col)
    
    # Create bar chart
    fig = go.Figure(data=go.Bar(
        x=corr_with_target.values,
        y=corr_with_target.index,
        orientation='h',
        marker_color=COLOR_PRIMARY
    ))
    
    fig.update_layout(
        title="<b>Importance Fitur (Korelasi dengan Varians Nilai)</b>",
        xaxis_title="Korelasi Absolut",
        yaxis_title="Fitur",
        title_x=0.5,
        height=400
    )
    
    return fig

def create_time_series_decomposition(df: pd.DataFrame) -> go.Figure:
    # Simple time series decomposition
    if "Tanggal Stock Opname" not in df.columns or "Selisih Value (Rp)" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Kolom tanggal atau nilai tidak ditemukan.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Dekomposisi Time Series</b>", title_x=0.5)
        return fig
    
    # Group by date
    ts_data = df.groupby(df["Tanggal Stock Opname"].dt.date)["Selisih Value (Rp)"].sum().reset_index()
    
    if len(ts_data) < 14:  # Need at least 2 weeks for meaningful decomposition
        fig = go.Figure()
        fig.add_annotation(
            text="Data tidak cukup untuk dekomposisi time series (minimal 14 hari).",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(color="#CBD5F5", size=16)
        )
        fig.update_layout(title="<b>Dekomposisi Time Series</b>", title_x=0.5)
        return fig
    
    # Create figure with subplots
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=("Data Asli", "Tren", "Musiman", "Residual"),
        vertical_spacing=0.05
    )
    
    # Original data
    fig.add_trace(
        go.Scatter(x=ts_data["Tanggal Stock Opname"], y=ts_data["Selisih Value (Rp)"],
                  mode='lines', name='Data Asli', line=dict(color=COLOR_PRIMARY)),
        row=1, col=1
    )
    
    # Trend (simple moving average)
    window = min(7, len(ts_data) // 3)
    ts_data["Trend"] = ts_data["Selisih Value (Rp)"].rolling(window=window, center=True).mean()
    fig.add_trace(
        go.Scatter(x=ts_data["Tanggal Stock Opname"], y=ts_data["Trend"],
                  mode='lines', name='Tren', line=dict(color=COLOR_ACCENT)),
        row=2, col=1
    )
    
    # Seasonality (simplified - day of week pattern)
    if len(ts_data) >= 14:
        ts_data["DayOfWeek"] = pd.to_datetime(ts_data["Tanggal Stock Opname"]).dt.dayofweek
        seasonal_pattern = ts_data.groupby("DayOfWeek")["Selisih Value (Rp)"].mean()
        ts_data["Seasonal"] = ts_data["DayOfWeek"].map(seasonal_pattern)
        fig.add_trace(
            go.Scatter(x=ts_data["Tanggal Stock Opname"], y=ts_data["Seasonal"],
                      mode='lines', name='Musiman', line=dict(color=COLOR_SUCCESS)),
            row=3, col=1
        )
    
    # Residual
    if "Seasonal" in ts_data.columns:
        ts_data["Residual"] = ts_data["Selisih Value (Rp)"] - ts_data["Trend"] - ts_data["Seasonal"]
    else:
        ts_data["Residual"] = ts_data["Selisih Value (Rp)"] - ts_data["Trend"]
    
    fig.add_trace(
        go.Scatter(x=ts_data["Tanggal Stock Opname"], y=ts_data["Residual"],
                  mode='lines', name='Residual', line=dict(color=COLOR_WARNING)),
        row=4, col=1
    )
    
    fig.update_layout(
        title="<b>Dekomposisi Time Series Varians Nilai</b>",
        title_x=0.5,
        height=800,
        showlegend=False
    )
    
    return fig

# =========================================================
# ------------------- FUNGSI GEMINI AI --------------------
# =========================================================
def configure_gemini():
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        # Menggunakan model gemini-2.0-flash yang Anda sebutkan
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model
    except Exception as e:
        st.error(f"Gagal mengkonfigurasi Gemini API: {e}")
        return None

def generate_data_insights(df: pd.DataFrame, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model tidak tersedia."
    
    # Prepare data summary
    total_records = len(df)
    date_range = f"{df['Tanggal Stock Opname'].min().date()} hingga {df['Tanggal Stock Opname'].max().date()}"
    total_variance_value = df["Selisih Value (Rp)"].sum()
    total_variance_qty = df["Selisih Qty (Pcs)"].sum()
    top_tags = df.groupby("Tag")["Selisih Value (Rp)"].sum().abs().sort_values(ascending=False).head(3).index.tolist()
    
    # Get top positive and negative variance products
    top_positive = df[df["Selisih Value (Rp)"] > 0].sort_values("Selisih Value (Rp)", ascending=False).head(3)
    top_negative = df[df["Selisih Value (Rp)"] < 0].sort_values("Selisih Value (Rp)").head(3)
    
    # Create prompt for Gemini
    prompt = f"""
    Analisis data varians stok opname berikut dan berikan insight yang berharga:
    
    Ringkasan Data:
    - Total Records: {total_records}
    - Periode Data: {date_range}
    - Total Varians Nilai: {format_currency(total_variance_value)}
    - Total Varians Kuantitas: {format_quantity(total_variance_qty)} pcs
    - Top 3 Tag dengan Varians Tertinggi: {', '.join(top_tags)}
    
    Produk dengan Varians Positif Tertinggi:
    {top_positive[['DESCP', 'Selisih Value (Rp)', 'Selisih Qty (Pcs)']].to_string(index=False)}
    
    Produk dengan Varians Negatif Terbesar:
    {top_negative[['DESCP', 'Selisih Value (Rp)', 'Selisih Qty (Pcs)']].to_string(index=False)}
    
    Berikan analisis mendalam tentang:
    1. Pola atau tren yang menonjol dari data varians stok
    2. Kemungkinan penyebab varians positif dan negatif
    3. Area yang perlu mendapat perhatian khusus
    4. Rekomendasi tindakan untuk mengurangi varians negatif
    5. Strategi untuk memanfaatkan produk dengan varians positif
    
    Jawab dalam bahasa Indonesia dengan gaya profesional namun mudah dipahami.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan saat menghasilkan insight: {e}"

def answer_data_question(df: pd.DataFrame, question: str, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model tidak tersedia."
    
    # Prepare data summary
    data_summary = df.head(10).to_string()
    
    # Create prompt for Gemini
    prompt = f"""
    Berdasarkan data varians stok opname berikut:
    
    {data_summary}
    
    Jawab pertanyaan ini dengan bahasa Indonesia: "{question}"
    
    Jika jawaban memerlukan analisis lebih dari 10 baris data pertama, berikan jawaban berdasarkan pola umum yang terlihat dari data.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan saat menjawab pertanyaan: {e}"

def generate_recommendations(df: pd.DataFrame, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model tidak tersedia."
    
    # Identify problematic areas
    negative_variance = df[df["Selisih Value (Rp)"] < 0]
    outliers = detect_outliers_iqr(df, "Selisih Value (Rp)")
    
    # Create prompt for Gemini
    prompt = f"""
    Berdasarkan data varians stok opname, berikan rekomendasi bisnis yang spesifik dan actionable:
    
    Informasi Penting:
    - Total produk dengan varians negatif: {len(negative_variance)} dari {len(df)} produk
    - Total nilai varians negatif: {format_currency(negative_variance['Selisih Value (Rp)'].sum())}
    - Jumlah outlier yang terdeteksi: {len(outliers)}
    
    Berikan 5 rekomendasi prioritas yang dapat diimplementasikan untuk:
    1. Mengurangi varians stok negatif
    2. Meningkatkan akurasi stok opname
    3. Mengoptimalkan proses inventory management
    4. Mengidentifikasi area yang perlu audit lebih lanjut
    5. Meningkatkan profitabilitas terkait manajemen stok
    
    Jawab dalam bahasa Indonesia dengan format daftar yang jelas dan actionable.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan saat menghasilkan rekomendasi: {e}"

# =========================================================
# ----------------------- SIDEBAR -------------------------
# =========================================================
with st.sidebar:
    st.header("🎛️ Kontrol Dashboard")
    st.caption("Atur parameter analitik secara real-time untuk melihat varians stok dari berbagai sudut.")

    st.divider()

    try:
        spreadsheet_url = st.secrets["spreadsheet"]["url"]
        st.success("✅ Terhubung ke Google Sheets via Secrets")
    except (KeyError, FileNotFoundError):
        spreadsheet_url = st.text_input(
            "URL Google Spreadsheet",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Masukkan URL jika tidak menggunakan st.secrets."
        )
        st.caption("Tip: Simpan kredensial pada `st.secrets` untuk koneksi otomatis.")

    sheet_name = st.text_input(
        "Nama Worksheet",
        value="Sheet1",
        help="Pastikan nama worksheet sesuai dengan di Google Sheets."
    )

    st.markdown("---")

    metric_selection = st.radio(
        "Pilih Metrik Utama",
        options=["Nilai (Rp)", "Kuantitas (Pcs)"],
        horizontal=True
    )
    top_n = st.slider(
        "Tampilkan Top Produk",
        min_value=5,
        max_value=30,
        value=10,
        step=1
    )

    st.markdown("---")

    if st.button("🔄 Reset Semua Filter", use_container_width=True):
        for key in ("date_range", "tags", "direction"):
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

# =========================================================
# ---------------------- MAIN APP -------------------------
# =========================================================
st.markdown(
    """
    <div class="hero-card">
        <h1>📈 Dashboard Analisis Varians Stok Opname</h1>
        <p>Menghadirkan visual interaktif dan insight instan untuk memantau dinamika varians stok secara komprehensif.
        <br/><strong>📍 Toko:</strong> 2GC6 BAROS PANDEGLANG</p>
    </div>
    """,
    unsafe_allow_html=True
)

if not spreadsheet_url.strip():
    st.warning("Masukkan URL Google Spreadsheet terlebih dahulu untuk memulai.")
    st.stop()

with st.spinner("Memuat dan memproses data dari Google Sheets..."):
    dataframe = load_data(spreadsheet_url, sheet_name)

if dataframe is None or dataframe.empty:
    st.error("Tidak ada data yang dapat diproses. Periksa kembali sumber data Anda.")
    st.stop()

# Initialize Gemini model
gemini_model = configure_gemini()

min_date = dataframe["Tanggal Stock Opname"].min().to_pydatetime()
max_date = dataframe["Tanggal Stock Opname"].max().to_pydatetime()
available_tags = sorted(dataframe["Tag"].unique().tolist())
available_tags_display = ["Semua"] + available_tags
directions = ["Semua", "Positif", "Negatif", "Netral"]

with st.sidebar:
    st.subheader("🧮 Filter")
    selected_date_range = st.date_input(
        "Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range"
    )
    selected_tags = st.multiselect(
        "Filter Tag",
        options=available_tags_display,
        default=["Semua"],
        key="tags"
    )
    selected_direction = st.multiselect(
        "Arah Varians",
        options=directions,
        default=["Semua"],
        key="direction"
    )

filtered_df = filter_dataframe(
    dataframe,
    date_range=selected_date_range,
    selected_tags=selected_tags,
    selected_direction=selected_direction
)

if filtered_df.empty:
    st.warning("Filter saat ini tidak menghasilkan data. Sesuaikan parameter filter atau gunakan tombol 'Reset Semua Filter'.")
    st.stop()

# =========================================================
# --------------------- RINGKASAN KPI ---------------------
# =========================================================
st.subheader("🔑 Ringkasan Eksekutif")

total_qty = filtered_df["Selisih Qty (Pcs)"].sum()
total_value = filtered_df["Selisih Value (Rp)"].sum()
total_plu = filtered_df["PLU"].nunique()
positive_value = filtered_df.loc[filtered_df["Selisih Value (Rp)"] > 0, "Selisih Value (Rp)"].sum()
negative_value = filtered_df.loc[filtered_df["Selisih Value (Rp)"] < 0, "Selisih Value (Rp)"].sum()
positive_qty = filtered_df.loc[filtered_df["Selisih Qty (Pcs)"] > 0, "Selisih Qty (Pcs)"].sum()
negative_qty = filtered_df.loc[filtered_df["Selisih Qty (Pcs)"] < 0, "Selisih Qty (Pcs)"].sum()

# Determine status based on variance
if total_value > 0:
    variance_status = "success"
elif total_value < 0:
    variance_status = "danger"
else:
    variance_status = "warning"

metric_container = st.container()
with metric_container:
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    render_metric_card(
        "Total Varians Nilai",
        format_currency(total_value),
        delta_label=f"{format_currency(positive_value)} ⬆︎ / {format_currency(negative_value)} ⬇︎",
        delta_type="neutral",
        icon="💰",
        status=variance_status
    )
    render_metric_card(
        "Total Varians Kuantitas",
        f"{format_quantity(total_qty)} Pcs",
        delta_label=f"+{format_quantity(positive_qty)} ⬆︎ / {format_quantity(negative_qty)} ⬇︎",
        delta_type="neutral",
        icon="📦"
    )
    render_metric_card(
        "Produk Terdampak",
        f"{format_quantity(total_plu)} PLU",
        icon="🛒"
    )
    render_metric_card(
        "Rata-rata Varians Nilai per PLU",
        format_currency(total_value / total_plu if total_plu else 0),
        icon="📊"
    )
    st.markdown('</div>', unsafe_allow_html=True)

highlight_insights(filtered_df)
st.divider()

# =========================================================
# -------------------- VISUALISASI ------------------------
# =========================================================
tabs = st.tabs([
    "🔍 Analisis Data Mendalam",
    "🤖 Analisis AI",
    "🏆 Analisis Produk",
    "📈 Tren Waktu",
    "🏷️ Analisis Kategori",
    "🔍 Scatter Varians",
    "🗺️ Treemap",
    "☀️ Sunburst",
    "📊 Distribusi",
    "🔥 Heatmap"
])

with tabs[0]:
    st.subheader("🔍 Analisis Data Mendalam")
    
    # Data Quality Report
    with st.expander("📋 Laporan Kualitas Data", expanded=True):
        quality_report = create_data_quality_report(filtered_df)
        st.dataframe(quality_report, use_container_width=True)
    
    # Distribution Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_distribution_chart(filtered_df, "Selisih Value (Rp)"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_distribution_chart(filtered_df, "Selisih Qty (Pcs)"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Box Plots
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_box_plot(filtered_df, "Selisih Value (Rp)"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_box_plot(filtered_df, "Selisih Qty (Pcs)"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Correlation Matrix
    st.markdown('<div class="correlation-matrix">', unsafe_allow_html=True)
    st.plotly_chart(create_correlation_matrix(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Feature Importance
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_feature_importance_chart(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Time Series Decomposition
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_time_series_decomposition(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Statistical Summary
    with st.expander("📊 Ringkasan Statistik", expanded=False):
        numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns
        stats_summary = filtered_df[numeric_cols].describe().T
        stats_summary['skew'] = filtered_df[numeric_cols].skew()
        stats_summary['kurtosis'] = filtered_df[numeric_cols].kurtosis()
        st.dataframe(stats_summary, use_container_width=True)

with tabs[1]:
    st.subheader("🤖 Analisis AI dengan Gemini")
    
    if gemini_model is None:
        st.error("Model Gemini tidak tersedia. Pastikan API key sudah dikonfigurasi dengan benar.")
    else:
        # AI Insights Section
        st.markdown("### 🧠 Insight Cerdas dari Data")
        
        if st.button("🔍 Generate Insight", type="primary"):
            with st.spinner("Menganalisis data dengan AI..."):
                insights = generate_data_insights(filtered_df, gemini_model)
                
                st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                st.markdown(insights)
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Q&A Section
        st.markdown("### ❓ Tanya Jawab tentang Data")
        
        question = st.text_input("Ajukan pertanyaan tentang data varians stok:", 
                                placeholder="Contoh: Produk apa yang paling sering mengalami varians negatif?")
        
        if st.button("Kirim Pertanyaan") and question:
            with st.spinner("Mencari jawaban..."):
                answer = answer_data_question(filtered_df, question, gemini_model)
                
                st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                st.markdown(f"**Pertanyaan:** {question}")
                st.markdown(f"**Jawaban:** {answer}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Recommendations Section
        st.markdown("### 💡 Rekomendasi Bisnis")
        
        if st.button("📋 Generate Rekomendasi", type="primary"):
            with st.spinner("Menghasilkan rekomendasi..."):
                recommendations = generate_recommendations(filtered_df, gemini_model)
                
                st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                st.markdown(recommendations)
                st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.plotly_chart(create_top_products_chart(filtered_df, metric_selection, top_n), use_container_width=True)

with tabs[3]:
    st.plotly_chart(create_trend_chart(filtered_df, metric_selection), use_container_width=True)

with tabs[4]:
    st.plotly_chart(create_tag_analysis_chart(filtered_df, metric_selection), use_container_width=True)

with tabs[5]:
    st.plotly_chart(create_scatter_chart(filtered_df), use_container_width=True)

with tabs[6]:
    st.plotly_chart(create_treemap_chart(filtered_df), use_container_width=True)

with tabs[7]:
    st.plotly_chart(create_sunburst_chart(filtered_df), use_container_width=True)

with tabs[8]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_pie_chart(filtered_df, "Tag"), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_pie_chart(filtered_df, "Arah Varians"), use_container_width=True)

with tabs[9]:
    st.plotly_chart(create_heatmap(filtered_df, "Tag", "Arah Varians", "Selisih Value (Rp)"), use_container_width=True)

st.divider()

# =========================================================
# ------------------- TABEL DETAIL ------------------------
# =========================================================
with st.expander("📄 Lihat Data Detail", expanded=False):
    df_display = filtered_df.copy()
    df_display["Tanggal Stock Opname"] = df_display["Tanggal Stock Opname"].dt.strftime("%Y-%m-%d")
    df_display["Selisih Qty (Pcs)"] = df_display["Selisih Qty (Pcs)"].apply(format_quantity)
    df_display["Selisih Value (Rp)"] = df_display["Selisih Value (Rp)"].apply(format_currency)
    df_display["Varians Nilai Absolut"] = df_display["Varians Nilai Absolut"].apply(format_currency)
    df_display["Varians Qty Absolut"] = df_display["Varians Qty Absolut"].apply(format_quantity)
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# Export button
csv = filtered_df.to_csv(index=False)
b64 = base64.b64encode(csv.encode()).decode()
href = f'<a href="data:file/csv;base64,{b64}" download="varians_stok_opname.csv" class="export-button"><button class="stButton">📥 Export Data</button></a>'
st.markdown(href, unsafe_allow_html=True)

st.caption("© 2025 – Dashboard Varians Stok Opname • Dibangun dengan Streamlit + Plotly • Desain profesional modern")
