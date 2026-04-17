import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Fundamental Data Tracker", layout="wide")

st.title("📊 Perbandingan Data Historis Fundamental Saham")
st.write("Membandingkan metrik keuangan perusahaan dengan pertumbuhan S&P 500 sebagai standar.")

# 1. Pilihan Input
col1, col2 = st.columns(2)
with col1:
    selected_assets = st.multiselect(
        "Pilih Saham (Bisa ketik ticker lain):", 
        options=["AVGO", "PLTR", "VST", "NVDA", "AAPL", "MSFT", "AMD"], 
        default=["AVGO", "PLTR"]
    )
with col2:
    metric_choice = st.selectbox(
        "Pilih Metrik Fundamental:", 
        ["Net Income", "Total Revenue", "Operating Income"]
    )

# 2. Fungsi untuk Mengambil Data Fundamental Tahunan dengan Error Handling
@st.cache_data
def get_financial_data(tickers, metric):
    df_combined = pd.DataFrame()
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            financials = stock.financials
            
            # Cek apakah data financials tersedia
            if financials is not None and not financials.empty:
                if metric in financials.index:
                    data = financials.loc[metric]
                    data.index = pd.to_datetime(data.index).year
                    df_combined[ticker] = data
                else:
                    st.warning(f"Metrik '{metric}' tidak ditemukan untuk {ticker}.")
            else:
                 st.warning(f"Data keuangan untuk {ticker} sedang tidak tersedia dari Yahoo Finance.")
                 
        except Exception as e:
             st.warning(f"Terjadi kesalahan saat mengambil data untuk {ticker}: {e}")
            
    # Urutkan dari tahun terlama ke terbaru jika data tidak kosong
    if not df_combined.empty:
        # Hapus kolom yang isinya NaN semua
        df_combined = df_combined.dropna(axis=1, how='all')
        # Isi sisa NaN (misal perusahaan baru IPO) dengan nilai sebelumnya atau nol (tergantung preferensi, di sini kita forward fill lalu fillna 0 untuk aman di perhitungan persentase, meski idealnya di-drop)
        # Tapi lebih aman kita hanya plot data yang valid. Kita dropna untuk baris yang ada NaN.
        df_combined = df_combined.dropna() 
        return df_combined.sort_index()
    else:
        return pd.DataFrame()

# 3. Fungsi untuk Mengambil Data Tahunan S&P 500 (Benchmark)
@st.cache_data
def get_sp500_benchmark(years):
    sp500 = yf.Ticker("^GSPC")
    hist = sp500.history(period="10y")
    
    if not hist.empty:
        sp500_yearly = hist.resample('YE').last()['Close']
        sp500_yearly.index = sp500_yearly.index.year
        return sp500_yearly[sp500_yearly.index.isin(years)]
    return pd.Series()

if selected_assets:
    with st.spinner('Menarik data dari server...'):
        fund_data = get_financial_data(selected_assets, metric_choice)
        
        if not fund_data.empty:
            years = fund_data.index.tolist()
            sp500_data = get_sp500_benchmark(years)
            
            # NORMALISASI: Hindari pembagian dengan nol
            norm_fund = pd.DataFrame()
            for col in fund_data.columns:
                first_val = fund_data[col].iloc[0]
                if first_val != 0 and pd.notna(first_val):
                    norm_fund[col] = (fund_data[col] / abs(first_val) - 1) * 100 # Pakai absolute untuk menangani nilai negatif awal
                else:
                     norm_fund[col] = 0 # Atau penanganan lain
                     
            if not sp500_data.empty:
                first_sp_val = sp500_data.iloc[0]
                norm_sp500 = (sp500_data / first_sp_val - 1) * 100
            else:
                 norm_sp500 = pd.Series(dtype=float)
            
            # 4. Pembuatan Grafik Plotly
            fig = go.Figure()
            
            for col in norm_fund.columns:
                fig.add_trace(go.Scatter(
                    x=norm_fund.index, 
                    y=norm_fund[col], 
                    name=f"{col} ({metric_choice})",
                    mode='lines+markers',
                    line=dict(width=3)
                ))
            
            if not norm_sp500.empty:
                fig.add_trace(go.Scatter(
                    x=norm_sp500.index,
                    y=norm_sp500,
                    name="S&P 500 Benchmark (Growth)",
                    mode='lines',
                    line=dict(color='white', width=2, dash='dash')
                ))
            
            fig.update_layout(
                title=f"Perbandingan Pertumbuhan {metric_choice} vs S&P 500 (%)",
                xaxis_title="Tahun",
                yaxis_title="Pertumbuhan (%) dari Tahun Dasar",
                template="plotly_dark",
                hovermode="x unified",
                xaxis=dict(tickmode='linear')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Data Mentah (Dalam mata uang asal / USD)")
            st.dataframe(fund_data.style.format("{:,.0f}"))
            
        else:
            st.error("Gagal memuat data yang valid. Coba aset atau metrik lain.")
else:
    st.info("Pilih minimal 1 saham untuk memulai.")
            
        if metric in financials.index:
            # Ambil data metrik dan ubah format tanggal menjadi tahun
            data = financials.loc[metric]
            data.index = pd.to_datetime(data.index).year
            df_combined[ticker] = data
            
    # Urutkan dari tahun terlama ke terbaru
    return df_combined.sort_index()

# 3. Fungsi untuk Mengambil Data Tahunan S&P 500 (Benchmark)
@st.cache_data
def get_sp500_benchmark(years):
    sp500 = yf.Ticker("^GSPC")
    # Ambil harga historis yang luas
    hist = sp500.history(period="10y")
    # Resample untuk mengambil harga penutupan rata-rata atau akhir tahun
    sp500_yearly = hist.resample('YE').last()['Close']
    sp500_yearly.index = sp500_yearly.index.year
    return sp500_yearly[sp500_yearly.index.isin(years)]

if selected_assets:
    with st.spinner('Menarik data dari server...'):
        # Tarik data fundamental
        fund_data = get_financial_data(selected_assets, metric_choice)
        
        if not fund_data.empty:
            # Tarik data S&P 500 untuk tahun yang sama
            years = fund_data.index.tolist()
            sp500_data = get_sp500_benchmark(years)
            
            # NORMALISASI: Ubah semua data menjadi Persentase Pertumbuhan (Base 0%) 
            # dari tahun pertama yang tersedia agar bisa dibandingkan dalam 1 grafik
            norm_fund = (fund_data / fund_data.iloc[0] - 1) * 100
            norm_sp500 = (sp500_data / sp500_data.iloc[0] - 1) * 100
            
            # 4. Pembuatan Grafik Plotly
            fig = go.Figure()
            
            # Plot untuk tiap saham
            for col in norm_fund.columns:
                fig.add_trace(go.Scatter(
                    x=norm_fund.index, 
                    y=norm_fund[col], 
                    name=f"{col} ({metric_choice})",
                    mode='lines+markers',
                    line=dict(width=3)
                ))
            
            # Plot untuk S&P 500 sebagai Benchmark (Garis putus-putus)
            fig.add_trace(go.Scatter(
                x=norm_sp500.index,
                y=norm_sp500,
                name="S&P 500 Benchmark (Growth)",
                mode='lines',
                line=dict(color='white', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title=f"Perbandingan Pertumbuhan {metric_choice} vs S&P 500 (%)",
                xaxis_title="Tahun",
                yaxis_title="Pertumbuhan (%) dari Tahun Dasar",
                template="plotly_dark",
                hovermode="x unified",
                xaxis=dict(tickmode='linear') # Pastikan tahun tidak ada komanya (misal 2021.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tampilkan Nilai Kasar (Raw Data)
            st.subheader("Data Mentah (Dalam mata uang asal / USD)")
            st.dataframe(fund_data.style.format("{:,.0f}"))
            
        else:
            st.error("Data tidak ditemukan untuk saham atau metrik tersebut.")
else:
    st.info("Pilih minimal 1 saham untuk memulai.")
