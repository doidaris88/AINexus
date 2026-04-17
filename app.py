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
        options=["AVGO", "PLTR", "VST", "NVDA", "AAPL"], 
        default=["AVGO", "PLTR"]
    )
with col2:
    metric_choice = st.selectbox(
        "Pilih Metrik Fundamental:", 
        ["Net Income", "Total Revenue", "Total Assets", "Operating Income"]
    )

# 2. Fungsi untuk Mengambil Data Fundamental Tahunan
@st.cache_data
def get_financial_data(tickers, metric):
    df_combined = pd.DataFrame()
    
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        # Ambil laporan keuangan tahunan (Income Statement / Balance Sheet)
        if metric in ["Net Income", "Total Revenue", "Operating Income"]:
            financials = stock.financials
        else:
            financials = stock.balance_sheet
            
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
