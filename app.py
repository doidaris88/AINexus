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
        "Pilih Saham Tersedia:", 
        options=["AVGO", "PLTR", "VST", "NVDA", "AAPL", "MSFT", "AMD"], 
        default=["AVGO", "PLTR"]
    )
    # --- FITUR BARU: Tambah Ticker Manual ---
    custom_tickers = st.text_input("➕ Tambahkan Ticker Lain (pisahkan koma, cth: TSLA, INTC):", "")

with col2:
    metric_choice = st.selectbox(
        "Pilih Metrik Fundamental:", 
        ["Net Income", "Total Revenue", "Operating Income"]
    )

# Menggabungkan pilihan dari dropdown dengan ketikan manual
final_assets = selected_assets.copy()
if custom_tickers:
    # Membersihkan spasi dan mengubah huruf menjadi kapital secara otomatis
    custom_list = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
    final_assets.extend(custom_list)
    # Menghapus duplikat jika Anda mengetik ticker yang sama dengan di dropdown
    final_assets = list(set(final_assets))

# 2. Fungsi untuk Mengambil Data Fundamental Tahunan dengan Error Handling
@st.cache_data
def get_financial_data(tickers, metric):
    df_combined = pd.DataFrame()
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            financials = stock.financials
            
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
            
    if not df_combined.empty:
        df_combined = df_combined.dropna(axis=1, how='all')
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

if final_assets:
    with st.spinner('Menarik data dari server...'):
        fund_data = get_financial_data(final_assets, metric_choice)
        
        if not fund_data.empty:
            years = fund_data.index.tolist()
            sp500_data = get_sp500_benchmark(years)
            
            # NORMALISASI: Hindari pembagian dengan nol
            norm_fund = pd.DataFrame()
            for col in fund_data.columns:
                first_val = fund_data[col].iloc[0]
                if first_val != 0 and pd.notna(first_val):
                    norm_fund[col] = (fund_data[col] / abs(first_val) - 1) * 100
                else:
                     norm_fund[col] = 0
                     
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
