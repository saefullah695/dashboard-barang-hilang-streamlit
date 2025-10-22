import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Dashboard Analisis Selisih Stok",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Fungsi untuk Memuat Data dari Google Sheets ---
# @st.cache_data adalah dekorator untuk cache data, agar tidak load ulang setiap interaksi
@st.cache_data
def load_data(spreadsheet_url, sheet_name):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Ambil kredensial dari secrets Streamlit Cloud
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception as e:
        st.error("Gagal memuat kredensial dari Streamlit Secrets. Pastikan sudah diatur dengan benar di tab Settings > Secrets.")
        st.error(e)
        return None

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    
    df = get_as_dataframe(worksheet, evaluate_formulas=True)
    
    # --- Preprocessing Data ---
    # Hapus baris yang mungkin kosong
    df.dropna(how='all', inplace=True)
    
    # Konversi tipe data
    df['Tanggal SO'] = pd.to_datetime(df['Tanggal SO'], errors='coerce')
    df['Selisih Qty (Pcs)'] = pd.to_numeric(df['Selisih Qty (Pcs)'], errors='coerce')
    df['Selisih Value (Rp)'] = pd.to_numeric(df['Selisih Value (Rp)'], errors='coerce')
    
    # Hapus baris dengan tanggal atau nilai yang tidak valid setelah konversi
    df.dropna(subset=['Tanggal SO', 'Selisih Qty (Pcs)', 'Selisih Value (Rp)'], inplace=True)
    
    return df

# --- Sidebar untuk Filter ---
st.sidebar.header("⚙️ Filter Data")

# Coba ambil URL dari secrets, jika tidak ada, tampilkan input teks
try:
    spreadsheet_url = st.secrets["spreadsheet"]["url"]
    # Tampilkan URL yang sedang digunakan sebagai informasi
    st.sidebar.info(f"✅ Menggunakan Spreadsheet Terdaftar")
except (KeyError, FileNotFoundError):
    spreadsheet_url = st.sidebar.text_input("Masukkan URL Google Spreadsheet")

sheet_name = st.sidebar.text_input(
    "Masukkan Nama Sheet (Worksheet)",
    value="Sheet1" # Ganti jika nama sheet Anda berbeda
)

# Jika URL sudah ada (dari secrets atau input), lanjutkan
if spreadsheet_url:
    df = load_data(spreadsheet_url, sheet_name)

    if df is not None and not df.empty:
        # --- Filter Berdasarkan Tanggal ---
        min_date = df['Tanggal SO'].min().to_pydatetime()
        max_date = df['Tanggal SO'].max().to_pydatetime()
        
        selected_date_range = st.sidebar.date_input(
            "Pilih Rentang Tanggal SO",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        # Filter Berdasarkan Tag
        all_tags = ['Semua'] + list(df['Tag'].unique())
        selected_tags = st.sidebar.multiselect(
            "Pilih Tag",
            options=all_tags,
            default=['Semua']
        )

        # --- Terapkan Filter ---
        # Filter Tanggal
        if len(selected_date_range) == 2:
            start_date = pd.to_datetime(selected_date_range[0])
            end_date = pd.to_datetime(selected_date_range[1])
            df_filtered = df[(df['Tanggal SO'] >= start_date) & (df['Tanggal SO'] <= end_date)]
        else:
            df_filtered = df.copy()

        # Filter Tag
        if 'Semua' not in selected_tags:
            df_filtered = df_filtered[df_filtered['Tag'].isin(selected_tags)]

        # --- Header Dashboard ---
        st.title("📊 Dashboard Analisis Selisih Stok")
        st.markdown("Dashboard ini menganalisis selisih kuantitas dan nilai stok berdasarkan data Sales Order (SO).")

        # --- Metrik Kunci (KPIs) ---
        st.subheader("🔑 Metrik Kunci (Berdasarkan Filter)")
        total_selisih_qty = df_filtered['Selisih Qty (Pcs)'].sum()
        total_selisih_value = df_filtered['Selisih Value (Rp)'].sum()
        total_produk_terdampak = df_filtered['PLU'].nunique()

        # --- Logika untuk Tag Terbesar dan Terkecil ---
        tag_variance = df_filtered.groupby('Tag')['Selisih Value (Rp)'].sum()

        if not tag_variance.empty:
            biggest_tag_name = tag_variance.idxmax()
            biggest_tag_value = tag_variance.max()
            
            smallest_tag_name = tag_variance.idxmin()
            smallest_tag_value = tag_variance.min()
        else:
            biggest_tag_name = "N/A"
            biggest_tag_value = 0
            smallest_tag_name = "N/A"
            smallest_tag_value = 0

        # --- Menampilkan KPI dalam 5 kolom ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Selisih Qty", f"{total_selisih_qty:,.0f} Pcs")
        col2.metric("Total Selisih Value", f"Rp {total_selisih_value:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Produk Terdampak", f"{total_produk_terdampak:,.0f}")
        
        # Menampilkan metrik baru dengan nilai selisih sebagai delta
        col4.metric("Tag Terbesar", biggest_tag_name, delta=f"Rp {biggest_tag_value:,.0f}")
        col5.metric("Tag Terkecil", smallest_tag_name, delta=f"Rp {smallest_tag_value:,.0f}")

        st.divider()

        # --- Visualisasi Data ---
        st.subheader("📈 Visualisasi Data")

        # 1. Top 10 Produk dengan Selisih Value Tertinggi
        st.markdown("**Top 10 Produk dengan Selisih Nilai (Rp) Tertinggi**")
        top_value_df = df_filtered.groupby(['PLU', 'DESCP'])['Selisih Value (Rp)'].sum().abs().sort_values(ascending=False).head(10).reset_index()
        fig_top_value = px.bar(
            top_value_df, 
            x='Selisih Value (Rp)', 
            y='DESCP',
            orientation='h',
            labels={'Selisih Value (Rp)': 'Total Selisih Nilai (Rp)', 'DESCP': 'Deskripsi Produk'},
            title='Top 10 Produk dengan Varians Nilai Terbesar'
        )
        fig_top_value.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top_value, use_container_width=True)

        # 2. Tren Selisih Harian
        st.markdown("**Tren Selisih Nilai Harian**")
        daily_trend_df = df_filtered.groupby(df_filtered['Tanggal SO'].dt.date)['Selisih Value (Rp)'].sum().reset_index()
        fig_trend = px.line(
            daily_trend_df, 
            x='Tanggal SO', 
            y='Selisih Value (Rp)',
            labels={'Tanggal SO': 'Tanggal', 'Selisih Value (Rp)': 'Total Selisih Nilai (Rp)'},
            title='Tren Varians Nilai Harian'
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # 3. Distribusi Selisih berdasarkan Tag
        st.markdown("**Distribusi Selisih Nilai berdasarkan Tag**")
        tag_distribution_df = df_filtered.groupby('Tag')['Selisih Value (Rp)'].sum().abs().reset_index()
        fig_pie = px.pie(
            tag_distribution_df, 
            values='Selisih Value (Rp)', 
            names='Tag',
            title='Proporsi Varians Nilai per Kategori (Tag)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # --- Tabel Data Detail ---
        st.subheader("📄 Tabel Data Detail")
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.warning("Silakan atur URL Google Spreadsheet di Streamlit Secrets (Cara 2) atau masukkan melalui sidebar.")
    st.info("**Cara Mendapatkan URL:** Buka Google Spreadsheet Anda, lalu salin URL dari browser.")
