import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
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

COLOR_PRIMARY = "#1f77b4"
COLOR_ACCENT = "#ff7f0e"
COLOR_POSITIVE = "#2ca02c"
COLOR_NEGATIVE = "#d62728"
COLOR_BG_GLASS = "rgba(15, 23, 42, 0.35)"

CUSTOM_CSS = """
<style>
:root {
    --text-color: #0f172a;
    --text-color-light: #64748b;
    --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #0f172a 100%);
    --glass-bg: rgba(15, 23, 42, 0.45);
    --border-color: rgba(148, 163, 184, 0.35);
    --shadow: 0 18px 45px rgba(15, 23, 42, 0.35);
    --radius: 18px;
}
body {
    background: var(--bg-gradient);
}
section.main > div {
    padding-top: 1rem;
}
h1, h2, h3, h4, h5, h6, .stTabs [role="tab"], .css-1629p8f, .css-16idsys {
    color: #f8fafc !important;
}
[data-testid="stMetricValue"] {
    font-weight: 700;
}
.metric-card {
    background: var(--glass-bg);
    padding: 1.5rem;
    border-radius: var(--radius);
    border: 1px solid var(--border-color);
    backdrop-filter: blur(10px);
    box-shadow: var(--shadow);
    height: 100%;
}
.metric-card .label {
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    color: var(--text-color-light);
}
.metric-card .value {
    font-size: clamp(1.6rem, 2.8vw, 2.4rem);
    font-weight: 700;
    color: #f8fafc;
    margin: 0.35rem 0;
}
.metric-card .delta {
    font-size: 0.95rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
}
.delta-positive {
    color: #34d399;
}
.delta-negative {
    color: #f87171;
}
.delta-neutral {
    color: #cbd5f5;
}
.stTabs [role="tab"] {
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    border-radius: 12px;
    background-color: rgba(15, 23, 42, 0.4);
    border: 1px solid transparent;
}
.stTabs [role="tab"]:hover {
    border: 1px solid rgba(148, 163, 184, 0.45);
}
.stTabs [aria-selected="true"] {
    background-color: rgba(15, 23, 42, 0.75);
    border-color: rgba(148, 163, 184, 0.65);
}
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.6);
    border-right: 1px solid rgba(148, 163, 184, 0.25);
}
.stCard {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(148, 163, 184, 0.35) !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


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
    icon: str = ""
) -> None:
    delta_class = {
        "positive": "delta-positive",
        "negative": "delta-negative",
        "neutral": "delta-neutral"
    }.get(delta_type, "delta-neutral")

    delta_markup = ""
    if delta_label:
        delta_markup = f'<div class="delta {delta_class}">{icon}{delta_label}</div>'

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{title}</div>
            <div class="value">{value}</div>
            {delta_markup}
        </div>
        """,
        unsafe_allow_html=True
    )


@st.cache_data(ttl=600)
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

    df["Tanggal Stock Opname"] = pd.to_datetime(df["Tanggal Stock Opname"], errors="coerce")
    for kolom_numerik in ["Selisih Qty (Pcs)", "Selisih Value (Rp)"]:
        if kolom_numerik in df.columns:
            df[kolom_numerik] = pd.to_numeric(df[kolom_numerik], errors="coerce")

    df.dropna(
        subset=[
            "Tanggal Stock Opname",
            "Selisih Qty (Pcs)",
            "Selisih Value (Rp)"
        ],
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


@st.cache_data(ttl=600)
def aggregate_tag_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Tag")["Selisih Value (Rp)"]
        .agg(["sum", "mean", "count"])
        .rename(columns={"sum": "Total Varians", "mean": "Rata-rata Varians", "count": "Jumlah PLU"})
        .sort_values(by="Total Varians", key=lambda x: x.abs(), ascending=False)
    )

# --- PENINGKATAN BARU: Fungsi Deteksi Outlier ---
@st.cache_data(ttl=600)
def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Mendeteksi outlier menggunakan metode IQR."""
    if column not in df.columns or df.empty:
        return pd.DataFrame()
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers.sort_values(by=column, ascending=False)


def create_top_products_chart(df: pd.DataFrame, metric: str, top_n: int) -> go.Figure:
    metric_column = "Selisih Value (Rp)" if metric == "Nilai (Rp)" else "Selisih Qty (Pcs)"
    label_metric = "Total Varians Nilai (Rp)" if metric == "Nilai (Rp)" else "Total Varians Kuantitas (Pcs)"

    top_products = (
        df.groupby(["PLU", "DESCP"])[metric_column]
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
            text="Varians tidak ditemukan untuk kriteria ini.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        return fig

    fig = px.bar(
        top_products,
        x="Varians",
        y="DESCP",
        orientation="h",
        color="Varians",
        color_continuous_scale=["#ef4444", "#22c55e"],
        labels={"Varians": label_metric, "DESCP": "Deskripsi Produk"},
        title=f"<b>Top {top_n} Produk dengan Varians {metric} Terbesar</b>",
        height=520
    )

    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        title_x=0.5,
        coloraxis_showscale=False,
    )
    fig.add_vline(x=0, line_width=1, line_color="#cbd5f5", line_dash="dash")
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
            text=f"Data hanya pada <b>{min_date.strftime('%d %B %Y')}</b><br>Tidak cukup untuk tren.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
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
            line=dict(color=COLOR_PRIMARY, width=2.5),
            marker=dict(size=7)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data["Tanggal Stock Opname"],
            y=trend_data["MA_7"],
            mode="lines",
            name="Moving Average (7 Hari)",
            line=dict(color=COLOR_ACCENT, width=3, dash="solid")
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
            color_continuous_scale=["#ef4444", "#22c55e"],
            labels={"Tanggal Stock Opname": "Periode", "Varians": label_y},
            title="<b>Tren Varians Bulanan</b>",
            height=480
        )
        fig.update_layout(title_x=0.5, coloraxis_showscale=False)
        fig.add_hline(y=0, line_width=1, line_color="#cbd5f5", line_dash="dash")

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
        color_continuous_scale=["#ef4444", "#22c55e"],
        labels={"Varians": label_metric, "Tag": "Kategori (Tag)"},
        title="<b>Varians per Kategori (Tag)</b>",
        height=520
    )
    fig.update_layout(title_x=0.5, yaxis=dict(categoryorder="total ascending"))
    fig.add_vline(x=0, line_width=1, line_color="#cbd5f5", line_dash="dash")
    return fig


def create_scatter_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="Selisih Qty (Pcs)",
        y="Selisih Value (Rp)",
        hover_data=["PLU", "DESCP", "Tag"],
        color="Tag",
        color_discrete_sequence=px.colors.qualitative.Safe,
        title="<b>Varians Kuantitas vs Nilai</b>",
        trendline="ols" if len(df) > 10 else None,
        height=520
    )
    fig.update_layout(title_x=0.5)
    fig.add_hline(y=0, line_width=1, line_color="#94a3b8", line_dash="dot")
    fig.add_vline(x=0, line_width=1, line_color="#94a3b8", line_dash="dot")
    return fig


def create_treemap_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Tidak ada data untuk treemap.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title="<b>Treemap Varians</b>", title_x=0.5)
        return fig

    fig = px.treemap(
        df,
        path=["Tag", "DESCP"],
        values="Varians Nilai Absolut",
        color="Selisih Value (Rp)",
        color_continuous_scale=["#ef4444", "#94a3b8", "#22c55e"],
        color_continuous_midpoint=0,
        title="<b>Treemap Varians Nilai per Tag & Produk</b>",
        height=520
    )
    fig.update_layout(title_x=0.5)
    return fig


def filter_dataframe(
    df: pd.DataFrame,
    date_range: Tuple[datetime, datetime],
    selected_tags: List[str],
    selected_direction: List[str]
) -> pd.DataFrame:
    filtered = df.copy()
    start_date, end_date = map(pd.to_datetime, date_range)
    filtered = filtered[
        (filtered["Tanggal Stock Opname"] >= start_date) &
        (filtered["Tanggal Stock Opname"] <= end_date)
    ]

    if selected_tags and "Semua" not in selected_tags:
        filtered = filtered[filtered["Tag"].isin(selected_tags)]

    if selected_direction and "Semua" not in selected_direction:
        filtered = filtered[filtered["Arah Varians"].isin(selected_direction)]

    return filtered

# --- PENINGKATAN BARU: Fungsi Wawasan yang Lebih Terstruktur ---
def highlight_insights(df: pd.DataFrame) -> None:
    if df.empty:
        return

    tag_summary = aggregate_tag_summary(df)
    top_tag = tag_summary.index[0]
    top_tag_value = tag_summary.iloc[0]["Total Varians"]
    contribution = tag_summary["Total Varians"].abs().iloc[0] / tag_summary["Total Varians"].abs().sum() * 100

    biggest_positive = df.sort_values("Selisih Value (Rp)", ascending=False).head(1)
    biggest_negative = df.sort_values("Selisih Value (Rp)").head(1)
    
    # --- PENINGKATAN BARU: Deteksi Outlier ---
    outliers_value = detect_outliers_iqr(df, "Selisih Value (Rp)")
    outlier_count = len(outliers_value)

    # --- PENINGKATAN BARU: Tampilan Wawasan yang Lebih Rapi ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**🏷️ Tag Dominan:** `{top_tag}`")
        st.markdown(f"Menyumbang **{format_currency(top_tag_value)}** ({contribution:.1f}% dari total)")
    with col2:
        st.markdown(f"**📈 Varians Positif Terbesar:** `{biggest_positive.iloc[0]['DESCP']}`")
        st.markdown(f"Nilai: **{format_currency(biggest_positive.iloc[0]['Selisih Value (Rp)'])}**")
    
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"**📉 Varians Negatif Terbesar:** `{biggest_negative.iloc[0]['DESCP']}`")
        st.markdown(f"Nilai: **{format_currency(biggest_negative.iloc[0]['Selisih Value (Rp)'])}**")
    with col4:
        st.markdown(f"**🚨 Data Pencilan (Outlier):** `{outlier_count}` produk")
        if outlier_count > 0:
            with st.expander("Lihat outlier"):
                st.dataframe(outliers_value[["PLU", "DESCP", "Selisih Value (Rp)"]], use_container_width=True)


# =========================================================
# ----------------------- SIDEBAR -------------------------
# =========================================================
with st.sidebar:
    st.header("🎛️ Kontrol Dashboard")
    st.markdown("Atur parameter untuk menyesuaikan analisis secara real-time.")
    st.divider()

    try:
        spreadsheet_url = st.secrets["spreadsheet"]["url"]
        st.success("✅ Terhubung ke Google Sheets via Secrets")
    except (KeyError, FileNotFoundError):
        spreadsheet_url = st.text_input("URL Google Spreadsheet", placeholder="https://docs.google.com/spreadsheets/d/...")
        st.caption("Masukkan URL jika tidak menggunakan `st.secrets`.")

    sheet_name = st.text_input("Nama Worksheet", value="Sheet1", help="Pastikan nama sheet sesuai dengan di Google Sheets.")

    st.markdown("---")
    metric_selection = st.radio(
        "Pilih Metrik Utama",
        options=["Nilai (Rp)", "Kuantitas (Pcs)"],
        horizontal=True
    )
    top_n = st.slider("Tampilkan Top Produk", min_value=5, max_value=30, value=10, step=1)
    
    # --- PENINGKATAN BARU: Tombol Reset Filter ---
    st.markdown("---")
    if st.button("🔄 Reset Semua Filter", use_container_width=True):
        # Ini akan mereset widget ke nilai defaultnya
        st.rerun()


# =========================================================
# ---------------------- MAIN APP -------------------------
# =========================================================
st.title("📈 Dashboard Analisis Varians Stok Opname")
st.caption("Pantau dinamika varians stok dengan visual dinamis, insight instan, dan pengalaman interaktif yang modern.")

if not spreadsheet_url.strip():
    st.warning("Masukkan URL Google Spreadsheet terlebih dahulu untuk memulai.")
    st.stop()

with st.spinner("Memuat dan memproses data..."):
    dataframe = load_data(spreadsheet_url, sheet_name)

if dataframe is None or dataframe.empty:
    st.error("Tidak ada data yang dapat diproses. Periksa kembali sumber data Anda.")
    st.stop()

min_date = dataframe["Tanggal Stock Opname"].min().to_pydatetime()
max_date = dataframe["Tanggal Stock Opname"].max().to_pydatetime()

available_tags = sorted(dataframe["Tag"].unique().tolist())
available_tags_display = ["Semua"] + available_tags

directions = ["Semua", "Positif", "Negatif", "Netral"]

# --- PENINGKATAN BARU: Menggunakan key untuk manajemen state filter ---
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
        default=["Semua"] if "Semua" in available_tags_display else [],
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
    st.warning("Filter saat ini tidak menghasilkan data. Sesuaikan parameter filter Anda atau gunakan tombol 'Reset Semua Filter'.")
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

col_kpi = st.columns(4)
with col_kpi[0]:
    render_metric_card(
        "Total Varians Nilai",
        format_currency(total_value),
        delta_label=f"{format_currency(positive_value)} 🔺 / {format_currency(negative_value)} 🔻",
        delta_type="neutral"
    )
with col_kpi[1]:
    render_metric_card(
        "Total Varians Kuantitas",
        f"{format_quantity(total_qty)} Pcs",
        delta_label=f"+{format_quantity(filtered_df['Selisih Qty (Pcs)'][filtered_df['Selisih Qty (Pcs)'] > 0].sum())} / "
                    f"{format_quantity(filtered_df['Selisih Qty (Pcs)'][filtered_df['Selisih Qty (Pcs)'] < 0].sum())}",
        delta_type="neutral"
    )
with col_kpi[2]:
    render_metric_card(
        "Produk Terdampak",
        f"{format_quantity(total_plu)} PLU"
    )
with col_kpi[3]:
    render_metric_card(
        "Rata-rata Varians Nilai per PLU",
        format_currency(total_value / total_plu if total_plu else 0)
    )

highlight_insights(filtered_df)
st.divider()

# =========================================================
# -------------------- VISUALISASI ------------------------
# =========================================================
# --- PENINGKATAN BARU: Menambahkan Tab Data Profiler ---
tab_profiler, tab_produk, tab_tren, tab_tag, tab_mendalam, tab_treemap = st.tabs([
    "📊 Data Profiler", "📊 Analisis Produk", "📈 Tren Waktu", "🏷️ Analisis Kategori", "🔍 Scatter Varians", "🗺️ Treemap"
])

with tab_profiler:
    st.subheader("📊 Statistik Dasar Dataset")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Baris", f"{filtered_df.shape[0]:,}")
        st.metric("Total Kolom", filtered_df.shape[1])
    with col2:
        st.metric("Rentang Tanggal", f"{filtered_df['Tanggal Stock Opname'].min().date()} s/d {filtered_df['Tanggal Stock Opname'].max().date()}")
        st.metric("Jumlah Tag Unik", filtered_df['Tag'].nunique())
    with col3:
        st.metric("PLU Unik", filtered_df['PLU'].nunique())
        st.metric("Memori Usage", f"{filtered_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    st.markdown("---")
    st.subheader("Tipe Data Kolom")
    st.dataframe(filtered_df.dtypes.to_frame('Tipe Data'), use_container_width=True)

with tab_produk:
    st.plotly_chart(create_top_products_chart(filtered_df, metric_selection, top_n), use_container_width=True)

with tab_tren:
    st.plotly_chart(create_trend_chart(filtered_df, metric_selection), use_container_width=True)

with tab_tag:
    st.plotly_chart(create_tag_analysis_chart(filtered_df, metric_selection), use_container_width=True)

with tab_mendalam:
    st.plotly_chart(create_scatter_chart(filtered_df), use_container_width=True)

with tab_treemap:
    st.plotly_chart(create_treemap_chart(filtered_df), use_container_width=True)

st.divider()

# =========================================================
# ------------------- TABEL & EKSPOR ----------------------
# =========================================================
with st.expander("📄 Lihat Data Detail & Unduh", expanded=False):
    df_display = filtered_df.copy()
    df_display["Tanggal Stock Opname"] = df_display["Tanggal Stock Opname"].dt.strftime("%Y-%m-%d")
    df_display["Selisih Qty (Pcs)"] = df_display["Selisih Qty (Pcs)"].apply(format_quantity)
    df_display["Selisih Value (Rp)"] = df_display["Selisih Value (Rp)"].apply(format_currency)
    df_display["Varians Nilai Absolut"] = df_display["Varians Nilai Absolut"].apply(format_currency)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Data (CSV)",
        data=csv_data,
        file_name=f"varians_stok_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

st.caption("© 2025 – Dashboard Varians Stok Opname • Dibangun dengan Streamlit + Plotly")
