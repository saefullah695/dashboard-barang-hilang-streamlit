import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- Konfigurasi Tema dan Halaman ---
st.set_page_config(
    page_title="Dashboard Varians Stok Opname",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Definisi Warna Tema ---
COLOR_PRIMARY = "#1f77b4"  # Biru profesional
COLOR_NEGATIVE = "#d62728" # Merah untuk selisih negatif
COLOR_POSITIVE = "#2ca02c" # Hijau untuk selisih positif

# --- Fungsi untuk Memuat Data dari Google Sheets ---
@st.cache_data(ttl=600) # Cache selama 10 menit
def load_data(spreadsheet_url, sheet_name):
    """Memuat dan memproses data dari Google Sheets."""
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(sheet_name)
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return None

    # --- Preprocessing Data ---
    df.dropna(how='all', inplace=True)
    # Ganti nama kolom untuk konsistensi
    df.rename(columns={
        'Tanggal SO': 'Tanggal Stock Opname'
    }, inplace=True)

    # Konversi tipe data
    df['Tanggal Stock Opname'] = pd.to_datetime(df['Tanggal Stock Opname'], errors='coerce')
    df['Selisih Qty (Pcs)'] = pd.to_numeric(df['Selisih Qty (Pcs)'], errors='coerce')
    df['Selisih Value (Rp)'] = pd.to_numeric(df['Selisih Value (Rp)'], errors='coerce')
    
    df.dropna(subset=['Tanggal Stock Opname', 'Selisih Qty (Pcs)', 'Selisih Value (Rp)'], inplace=True)
    
    return df

# --- Fungsi untuk Membuat Grafik ---
def create_top_products_chart(df):
    """Membuat grafik batang untuk 10 produk dengan varians nilai terbesar."""
    top_products = df.groupby(['PLU', 'DESCP'])['Selisih Value (Rp)'].sum().abs().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(
        top_products, 
        x='Selisih Value (Rp)', 
        y='DESCP',
        orientation='h',
        labels={'Selisih Value (Rp)': 'Total Varians Nilai (Rp)', 'DESCP': 'Deskripsi Produk'},
        title='<b>Top 10 Produk dengan Varians Nilai Terbesar</b>',
        color_discrete_sequence=[COLOR_PRIMARY]
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, title_x=0.5)
    return fig

def create_trend_chart(df):
    """Membuat grafik tren varians yang adaptif (harian atau bulanan) berdasarkan data."""
    if df.empty:
        return go.Figure().add_annotation(text="Tidak ada data untuk ditampilkan.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

    # Tentukan granularity berdasarkan rentang data
    min_date = df['Tanggal Stock Opname'].min()
    max_date = df['Tanggal Stock Opname'].max()
    
    # Jika data hanya dalam satu hari, tampilkan pesan
    if min_date.date() == max_date.date():
        fig = go.Figure()
        fig.add_annotation(
            text=f"Data hanya tersedia untuk satu hari: <b>{min_date.strftime('%d %B %Y')}</b><br>Tidak ada tren yang dapat ditampilkan.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16)
        )
        return fig

    # Jika data kurang dari 45 hari, gunakan granularity harian
    if (max_date - min_date).days < 45:
        trend_data = df.groupby(df['Tanggal Stock Opname'].dt.date)['Selisih Value (Rp)'].sum().reset_index()
        trend_data['Moving Average (7 Hari)'] = trend_data['Selisih Value (Rp)'].rolling(window=7, min_periods=1).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['Tanggal Stock Opname'], 
            y=trend_data['Selisih Value (Rp)'], 
            mode='lines+markers',
            name='Varians Harian',
            line=dict(color=COLOR_PRIMARY)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data['Tanggal Stock Opname'], 
            y=trend_data['Moving Average (7 Hari)'], 
            mode='lines',
            name='Rata-rata Bergerak (7 Hari)',
            line=dict(color='orange', width=3)
        ))
        title = '<b>Tren Varians Nilai Harian</b>'
        xaxis_title = 'Tanggal'
    # Jika data lebih dari 45 hari, gunakan granularity bulanan
    else:
        trend_data = df.groupby(df['Tanggal Stock Opname'].dt.to_period('M'))['Selisih Value (Rp)'].sum().reset_index()
        trend_data['Tanggal Stock Opname'] = trend_data['Tanggal Stock Opname'].dt.to_timestamp()

        fig = px.bar(
            trend_data,
            x='Tanggal Stock Opname',
            y='Selisih Value (Rp)',
            labels={'Tanggal Stock Opname': 'Bulan', 'Selisih Value (Rp)': 'Total Varians Nilai (Rp)'},
            title='<b>Tren Varians Nilai Bulanan</b>',
            color_discrete_sequence=[COLOR_PRIMARY]
        )
        title = '<b>Tren Varians Nilai Bulanan</b>'
        xaxis_title = 'Bulan'

    fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title='Total Varians Nilai (Rp)', title_x=0.5)
    return fig

def create_tag_analysis_chart(df):
    """Membuat grafik batang untuk analisis varians per Tag."""
    tag_analysis = df.groupby('Tag')['Selisih Value (Rp)'].sum().abs().sort_values(ascending=False).reset_index()
    fig = px.bar(
        tag_analysis, 
        x='Selisih Value (Rp)', 
        y='Tag',
        orientation='h',
        labels={'Selisih Value (Rp)': 'Total Varians Nilai (Rp)', 'Tag': 'Kategori (Tag)'},
        title='<b>Varians Nilai per Kategori (Tag)</b>',
        color_discrete_sequence=[COLOR_PRIMARY]
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, title_x=0.5)
    return fig

def create_scatter_chart(df):
    """Membuat grafik scatter untuk menganalisis hubungan varians kuantitas dan nilai."""
    fig = px.scatter(
        df, 
        x='Selisih Qty (Pcs)', 
        y='Selisih Value (Rp)',
        hover_data=['PLU', 'DESCP'],
        color='Tag',
        title='<b>Analisis Hubungan Varians Kuantitas vs Nilai</b>'
    )
    fig.update_layout(title_x=0.5)
    return fig

# --- Sidebar untuk Filter ---
with st.sidebar:
    st.header("🎛️ Kontrol Dashboard")
    st.markdown("---")
    
    try:
        spreadsheet_url = st.secrets["spreadsheet"]["url"]
        st.success("✅ Terhubung ke Sumber Data")
    except (KeyError, FileNotFoundError):
        spreadsheet_url = st.text_input("Masukkan URL Google Spreadsheet", type="default")
        st.info("Masukkan URL jika tidak menggunakan Streamlit Secrets.")

    sheet_name = st.text_input("Nama Sheet (Worksheet)", value="Sheet1")

if spreadsheet_url and sheet_name:
    df = load_data(spreadsheet_url, sheet_name)

    if df is not None and not df.empty:
        # --- Filter Berdasarkan Tanggal dan Tag ---
        min_date = df['Tanggal Stock Opname'].min().to_pydatetime()
        max_date = df['Tanggal Stock Opname'].max().to_pydatetime()
        
        with st.sidebar:
            st.markdown("**Filter Data**")
            selected_date_range = st.date_input(
                "Rentang Tanggal Stock Opname",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            all_tags = ['Semua'] + list(df['Tag'].unique())
            selected_tags = st.multiselect("Filter berdasarkan Tag", options=all_tags, default=['Semua'])

        # --- Terapkan Filter ---
        df_filtered = df.copy()
        if len(selected_date_range) == 2:
            start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
            df_filtered = df_filtered[(df_filtered['Tanggal Stock Opname'] >= start_date) & (df_filtered['Tanggal Stock Opname'] <= end_date)]
        if 'Semua' not in selected_tags:
            df_filtered = df_filtered[df_filtered['Tag'].isin(selected_tags)]

        # --- Header Dashboard ---
        st.title("📈 Dashboard Analisis Varians Stok Opname")
        st.markdown("Analisis mendalam terhadap selisih stok fisik dan sistem pada proses **Stock Opname**. Dashboard ini memberikan wawasan kunci untuk identifikasi masalah dan pengambilan keputusan.")

        # --- Metrik Kunci (KPIs) ---
        st.subheader("🔑 Ringkasan Eksekutif")
        total_selisih_qty = df_filtered['Selisih Qty (Pcs)'].sum()
        total_selisih_value = df_filtered['Selisih Value (Rp)'].sum()
        total_produk_terdampak = df_filtered['PLU'].nunique()
        
        # Warna untuk delta
        delta_qty_color = "normal" if total_selisih_qty == 0 else ("inverse" if total_selisih_qty < 0 else "normal")
        delta_value_color = "normal" if total_selisih_value == 0 else ("inverse" if total_selisih_value < 0 else "normal")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Varians Kuantitas", f"{total_selisih_qty:,.0f} Pcs", delta=f"{abs(total_selisih_qty):,.0f} Pcs", delta_color=delta_qty_color)
        col2.metric("Total Varians Nilai", f"Rp {total_selisih_value:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"Rp {abs(total_selisih_value):,.0f}".replace(",", "X").replace(".", ",").replace("X", "."), delta_color=delta_value_color)
        col3.metric("Produk Terdampak", f"{total_produk_terdampak:,.0f} PLU") # <-- PERUBAHAN DI SINI

        # --- Wawasan Cerdas ---
        if not df_filtered.empty:
            tag_variance = df_filtered.groupby('Tag')['Selisih Value (Rp)'].sum().abs()
            biggest_tag = tag_variance.idxmax()
            biggest_tag_contribution = (tag_variance.max() / tag_variance.sum()) * 100
            
            st.info(f"🧠 **Wawasan Cerdas:** Kategori **'{biggest_tag}'** menyumbang **{biggest_tag_contribution:.1f}%** dari total varians nilai. Fokus pada kategori ini dapat memberikan dampak perbaikan terbesar.")

        st.divider()

        # --- Visualisasi Data dengan Tabs ---
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Analisis Produk", "📈 Tren Waktu", "🏷️ Analisis Kategori", "🔍 Analisis Mendalam"])
        
        with tab1:
            st.plotly_chart(create_top_products_chart(df_filtered), use_container_width=True)

        with tab2:
            st.plotly_chart(create_trend_chart(df_filtered), use_container_width=True)
            
        with tab3:
            st.plotly_chart(create_tag_analysis_chart(df_filtered), use_container_width=True)

        with tab4:
            st.plotly_chart(create_scatter_chart(df_filtered), use_container_width=True)

        st.divider()

        # --- Tabel Data Detail dengan Download ---
        with st.expander("📄 Lihat Tabel Data Detail", expanded=False):
            # Format angka untuk ditampilkan di tabel
            df_display = df_filtered.copy()
            df_display['Selisih Qty (Pcs)'] = df_display['Selisih Qty (Pcs)'].map('{:,.0f}'.format)
            df_display['Selisih Value (Rp)'] = df_display['Selisih Value (Rp)'].map('Rp {:,.0f}'.format).replace(",", "X").replace(".", ",").replace("X", ".")
            df_display['Tanggal Stock Opname'] = df_display['Tanggal Stock Opname'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(df_display, use_container_width=True)

            # Tombol Download
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Data yang Difilter (CSV)",
                data=csv,
                file_name=f'data_varians_stok_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv',
            )
    else:
        st.error("Tidak dapat memuat data. Periksa kembali URL, nama sheet, dan koneksi internet Anda.")
else:
    st.warning("Silakan atur URL dan nama sheet di sidebar untuk memulai.")
