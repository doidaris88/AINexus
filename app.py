import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Pengaturan Halaman
st.set_page_config(page_title="AI-Energy Nexus Tracker", layout="wide")

# CSS untuk menyembunyikan branding Streamlit dan merapikan tampilan
hide_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_style, unsafe_allow_html=True)

st.title(" Perbandingan Fundamental AI-Energy Nexus")
st.write("Data ditarik secara online dari Yahoo Finance (Latest Available Data)")

# 1. Pilihan Input
col1, col2 = st.columns(2)
with col1:
    # Default diarahkan ke aset fokus Anda
    selected_assets = st.multiselect(
        "Pilih Saham Tersedia:", 
        options=["AVGO", "PLTR", "VST", "NVDA", "AES", "MRVL", "VRT"], 
        default=["VST", "PLTR"]
    )
    custom_tickers = st.text_input(" Tambahkan Ticker Lain (pisahkan koma):", "")

with col2:
    metric_choice = st.selectbox(
        "Pilih Metrik Fundamental:", 
        ["Net Income", "Total Revenue", "Operating Income"]
    )

# Gabungkan Ticker
final_assets = selected_assets.copy()
if custom_tickers:
    custom_list = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
    final_assets.extend(custom_list)
    final_assets = list(set(final_assets))

# 2. Fungsi Ambil Data Fundamental (Selalu Online)
@st.cache_data(ttl=3600) # Data disimpan di memori selama 1 jam saja agar tetap segar
def get_financial_data(tickers, metric):
    df_combined = pd.DataFrame()
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # Menarik data terbaru secara online
            financials = stock.financials
            if financials is not None and not financials.empty:
                if metric in financials.index:
                    data = financials.loc[metric]
                    data.index = pd.to_datetime(data.index).year
                    df_combined[ticker] = data
        except Exception:
            continue
            
    if not df_combined.empty:
        return df_combined.dropna().sort_index()
    return pd.DataFrame()

# 3. Fungsi Ambil Benchmark S&P 500 (Online)
@st.cache_data(ttl=3600)
def get_sp500_benchmark(years):
    sp500 = yf.Ticker("^GSPC")
    hist = sp500.history(period="10y")
    if not hist.empty:
        sp500_yearly = hist.resample('YE').last()['Close']
        sp500_yearly.index = sp500_yearly.index.year
        return sp500_yearly[sp500_yearly.index.isin(years)]
    return pd.Series()

# Eksekusi Plotting
if final_assets:
    with st.spinner('Menghubungkan ke Yahoo Finance...'):
        fund_data = get_financial_data(final_assets, metric_choice)
        
        if not fund_data.empty:
            years = fund_data.index.tolist()
            sp500_data = get_sp500_benchmark(years)
            
            # Normalisasi ke 0% (Base Year)
            norm_fund = pd.DataFrame()
            for col in fund_data.columns:
                first_val = fund_data[col].iloc[0]
                if first_val != 0:
                    norm_fund[col] = (fund_data[col] / abs(first_val) - 1) * 100
            
            # Persentase S&P 500
            if not sp500_data.empty:
                norm_sp500 = (sp500_data / sp500_data.iloc[0] - 1) * 100
            
            # Pembuatan Grafik
            fig = go.Figure()
            
            # Line Saham (Warna Otomatis)
            for col in norm_fund.columns:
                fig.add_trace(go.Scatter(
                    x=norm_fund.index, y=norm_fund[col], 
                    name=f"{col}", mode='lines+markers'
                ))
            
            # Line Benchmark S&P 500 (Warna Merah Terang agar terlihat di background putih)
            if not sp500_data.empty:
                fig.add_trace(go.Scatter(
                    x=norm_sp500.index, y=norm_sp500,
                    name="S&P 500 (Benchmark)",
                    mode='lines',
                    line=dict(color='#FF4B4B', width=4, dash='dot') # Merah Terang Tebal
                ))
            
            fig.update_layout(
                title=f"Pertumbuhan {metric_choice} vs Pasar (%)",
                template="plotly_white", # Tema Putih sesuai permintaan
                hovermode="x unified",
                xaxis=dict(tickmode='linear', gridcolor='lightgrey'),
                yaxis=dict(gridcolor='lightgrey', title="Pertumbuhan %")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(fund_data.style.format("{:,.0f}"))
        else:
            st.error("Data tidak tersedia atau ticker salah.")
