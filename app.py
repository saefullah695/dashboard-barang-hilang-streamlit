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

# =========================================================
# ------------------- KONFIGURASI AWAL --------------------
# =========================================================
st.set_page_config(
    page_title="Dashboard Varians Stok Opname",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palet warna kekinian
COLOR_PRIMARY = "#6366F1"     # Indigo neon
COLOR_ACCENT = "#22D3EE"      # Cyan terang
COLOR_SUCCESS = "#34D399"     # Hijau pastel
COLOR_WARNING = "#FACC15"     # Kuning keemasan
COLOR_DANGER = "#F97316"      # Oranye sunset
COLOR_NEGATIVE = "#FB7185"    # Merah salmon
COLOR_BG = "#0F172A"          # Biru gelap
COLOR_CARD = "rgba(15, 23, 42, 0.65)"
COLOR_BORDER = "rgba(148, 163, 184, 0.28)"

PLOTLY_COLORWAY = [
    "#6366F1", "#22D3EE", "#34D399", "#F97316",
    "#FACC15", "#A855F7", "#38BDF8", "#FB7185", "#F472B6"
]

CUSTOM_CSS = """
<style>
:root {
    --color-primary: #6366F1;
    --color-accent: #22D3EE;
    --color-success: #34D399;
    --color-warning: #FACC15;
    --color-danger: #F97316;
    --color-negative: #FB7185;
    --color-bg: #0F172A;
    --color-bg-secondary: rgba(15, 23, 42, 0.75);
    --color-card: rgba(15, 23, 42, 0.65);
    --color-border: rgba(148, 163, 184, 0.28);
    --color-text: #E2E8F0;
    --color-text-muted: #94A3B8;
    --color-highlight: rgba(99, 102, 241, 0.22);
    --radius: 20px;
    --blur: 22px;
    --transition: 0.25s ease;
}

body {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--color-text);
    background: radial-gradient(circle at top left, rgba(99,102,241,0.18), transparent 55%),
                radial-gradient(circle at top right, rgba(34,211,238,0.18), transparent 55%),
                radial-gradient(circle at bottom, rgba(251,113,133,0.18), transparent 55%),
                var(--color-bg);
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

section.main > div {
    padding-top: 1.2rem;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--color-text) !important;
    letter-spacing: 0.01em;
}

.stTabs [role="tablist"] {
    gap: 0.75rem;
}

.stTabs [role="tab"] {
    padding: 0.85rem 1.35rem;
    background: rgba(99, 102, 241, 0.08);
    border-radius: var(--radius);
    border: 1px solid transparent;
    transition: var(--transition);
    color: var(--color-text-muted);
    font-weight: 600;
}

.stTabs [role="tab"]:hover {
    border-color: rgba(34, 211, 238, 0.4);
    color: var(--color-accent);
}

.stTabs [aria-selected="true"] {
    background: var(--color-card);
    border-color: rgba(99, 102, 241, 0.55);
    color: var(--color-text);
    box-shadow: 0 12px 30px -12px rgba(99, 102, 241, 0.6);
}

[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.85);
    border-right: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
}

[data-testid="stSidebar"] * {
    color: var(--color-text);
}

.stButton button, .stDownloadButton button {
    border-radius: 999px !important;
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(34,211,238,0.15));
    color: var(--color-text);
    border: 1px solid rgba(99,102,241,0.35);
    transition: var(--transition);
    font-weight: 600;
    letter-spacing: 0.03em;
}

.stButton button:hover, .stDownloadButton button:hover {
    border-color: rgba(34,211,238,0.55);
    background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(34,211,238,0.25));
    box-shadow: 0 12px 30px -14px rgba(34, 211, 238, 0.65);
}

.metric-grid {
    display: grid;
    gap: 1.2rem;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.metric-card {
    background: linear-gradient(160deg, rgba(99,102,241,0.16), rgba(15,23,42,0.6));
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    border: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 20px 45px -25px rgba(15, 23, 42, 0.9);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.metric-card::after {
    content: "";
    position: absolute;
    inset: -40% 30% auto auto;
    width: 180px;
    height: 180px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.28) 0%, transparent 60%);
    transform: rotate(35deg);
    opacity: 0.9;
}

.metric-card:hover {
    transform: translateY(-6px);
    border-color: rgba(34, 211, 238, 0.55);
    box-shadow: 0 24px 55px -28px rgba(34, 211, 238, 0.55);
}

.metric-card .metric-icon {
    font-size: 1.8rem;
    margin-bottom: 0.35rem;
}

.metric-card .metric-label {
    font-size: 0.78rem;
    letter-spacing: 0.26em;
    text-transform: uppercase;
    color: var(--color-text-muted);
    margin-bottom: 0.25rem;
}

.metric-card .metric-value {
    font-size: clamp(1.75rem, 3vw, 2.45rem);
    font-weight: 700;
    color: var(--color-text);
    margin: 0.15rem 0 0.5rem;
}

.metric-card .metric-delta {
    display: inline-flex;
    gap: 0.4rem;
    align-items: center;
    font-size: 0.95rem;
    font-weight: 600;
}

.delta-positive { color: var(--color-success); }
.delta-negative { color: var(--color-negative); }
.delta-neutral { color: var(--color-warning); }

.hero-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.32), rgba(37,99,235,0.18));
    border-radius: calc(var(--radius) * 1.1);
    border: 1px solid rgba(99, 102, 241, 0.38);
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.8rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 28px 60px -32px rgba(99, 102, 241, 0.65);
}

.hero-card::before {
    content: "";
    position: absolute;
    inset: 12% -25% auto auto;
    width: 260px;
    height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(34,211,238,0.35), transparent 65%);
    filter: blur(2px);
    opacity: 0.65;
    animation: pulseGlow 6s ease-in-out infinite alternate;
}

@keyframes pulseGlow {
    from { transform: scale(0.95); opacity: 0.55; }
    to { transform: scale(1.08); opacity: 0.85; }
}

.hero-card h1 {
    font-size: clamp(2rem, 3.5vw, 2.8rem);
    margin-bottom: 0.6rem;
}

.hero-card p {
    color: var(--color-text-muted);
    font-size: 1.02rem;
    max-width: 62ch;
    line-height: 1.65;
}

.insight-card {
    background: var(--color-card);
    border-radius: var(--radius);
    border: 1px solid rgba(99,102,241,0.28);
    padding: 1.2rem 1.35rem;
    backdrop-filter: blur(var(--blur));
    position: relative;
    overflow: hidden;
    transition: var(--transition);
}

.insight-card::after {
    content: "";
    position: absolute;
    inset: 65% -30% auto auto;
    width: 160px;
    height: 160px;
    background: radial-gradient(circle, rgba(99,102,241,0.22), transparent 65%);
    opacity: 0.55;
}

.insight-card strong {
    color: var(--color-accent);
}

.stDataFrame {
    border-radius: calc(var(--radius) * 0.9);
    border: 1px solid rgba(99,102,241,0.18);
    overflow: hidden;
}

[data-testid="stDataFrame"] div[role="table"] {
    border-radius: 0;
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
            colorway=PLOTLY_COLORWAY
        )
    )
    pio.templates["neon_glass"] = template
    px.defaults.template = "neon_glass"
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
    icon: str = "📌"
) -> None:
    delta_class = {
        "positive": "delta-positive",
        "negative": "delta-negative",
        "neutral": "delta-neutral"
    }.get(delta_type, "delta-neutral")

    delta_markup = ""
    if delta_label:
        delta_markup = f'<div class="metric-delta {delta_class}">{delta_label}</div>'

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_markup}
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
        color_continuous_scale=[COLOR_NEGATIVE, COLOR_ACCENT, COLOR_SUCCESS],
        labels={"Varians": label_metric, "DESCP": "Deskripsi Produk"},
        title=f"<b>Top {top_n} Produk dengan Varians {metric} Tertinggi</b>",
        height=520
    )
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        title_x=0.5,
        coloraxis_showscale=False
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
            title_x=0.5
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
            color_continuous_scale=[COLOR_NEGATIVE, COLOR_ACCENT, COLOR_SUCCESS],
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
        color_continuous_scale=[COLOR_NEGATIVE, COLOR_ACCENT, COLOR_SUCCESS],
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
        color_continuous_scale=[COLOR_NEGATIVE, "#94A3B8", COLOR_SUCCESS],
        color_continuous_midpoint=0,
        title="<b>Treemap Varians Nilai per Tag & Produk</b>",
        height=520
    )
    fig.update_layout(title_x=0.5, margin=dict(t=80, l=30, r=30, b=30))
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
        <br/><strong>📍 Lokasi:</strong> 2GC6 BAROS PANDEGLANG</p>
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

metric_container = st.container()
with metric_container:
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    render_metric_card(
        "Total Varians Nilai",
        format_currency(total_value),
        delta_label=f"{format_currency(positive_value)} ⬆︎ / {format_currency(negative_value)} ⬇︎",
        delta_type="neutral",
        icon="💰"
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
    "📊 Data Profiler",
    "🏆 Analisis Produk",
    "📈 Tren Waktu",
    "🏷️ Analisis Kategori",
    "🔍 Scatter Varians",
    "🗺️ Treemap"
])

with tabs[0]:
    st.subheader("📊 Statistik Dasar Dataset")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Baris", f"{filtered_df.shape[0]:,}".replace(",", "."))
        st.metric("Total Kolom", filtered_df.shape[1])
    with col2:
        st.metric(
            "Rentang Tanggal",
            f"{filtered_df['Tanggal Stock Opname'].min().date()} s/d {filtered_df['Tanggal Stock Opname'].max().date()}"
        )
        st.metric("Jumlah Tag Unik", filtered_df["Tag"].nunique())
    with col3:
        st.metric("PLU Unik", filtered_df["PLU"].nunique())
        mem_usage = filtered_df.memory_usage(deep=True).sum() / 1024
        st.metric("Penggunaan Memori", f"{mem_usage:.2f} KB")
    st.markdown("---")
    st.subheader("Tipe Data Kolom")
    st.dataframe(filtered_df.dtypes.to_frame("Tipe Data"), use_container_width=True)

with tabs[1]:
    st.plotly_chart(create_top_products_chart(filtered_df, metric_selection, top_n), use_container_width=True)

with tabs[2]:
    st.plotly_chart(create_trend_chart(filtered_df, metric_selection), use_container_width=True)

with tabs[3]:
    st.plotly_chart(create_tag_analysis_chart(filtered_df, metric_selection), use_container_width=True)

with tabs[4]:
    st.plotly_chart(create_scatter_chart(filtered_df), use_container_width=True)

with tabs[5]:
    st.plotly_chart(create_treemap_chart(filtered_df), use_container_width=True)

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

st.caption("© 2025 – Dashboard Varians Stok Opname • Dibangun dengan Streamlit + Plotly • Desain futuristic-glassmorphism")
