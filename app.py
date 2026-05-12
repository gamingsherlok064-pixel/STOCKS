import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import time
import requests

# Page Configuration
st.set_page_config(
    page_title="Stocky | AI Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CACHED DATA FETCHING ---
@st.cache_data(ttl=300)
def get_ticker_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return dict(ticker.info)
    except: return None

@st.cache_data(ttl=300)
def get_ticker_history(symbol, period="1y", interval="1d"):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period, interval=interval)
    except: return pd.DataFrame()

# Initialize Session State
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { color: #ffffff !important; }
    
    [data-testid="stMetric"] { background-color: #1c2128; padding: 1.2rem; border-radius: 12px; border: 1px solid #30363d; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.9rem !important; }
    
    .stButton>button { background-color: #7F77DD; color: white; border-radius: 8px; border: none; padding: 0.5rem 2rem; font-weight: 600; }
    .stTextInput>div>div>input { background-color: #0d1117; color: white; border: 1px solid #30363d; border-radius: 8px; }
    
    h1, h2, h3 { color: #ffffff !important; font-family: 'Inter', sans-serif; }
    .footer { text-align: center; color: #8b949e; padding: 2rem; border-top: 1px solid #30363d; margin-top: 4rem; }
    
    /* Range Box Styling */
    .range-box { background-color: #161b22; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #30363d; display: inline-block; }
    .range-low { color: #23d333; font-weight: 600; font-size: 1.2rem; }
    .range-high { color: #ffffff; font-weight: 600; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# Helper: format large numbers
def format_large(num):
    if num >= 1e12: return f"${num/1e12:.2f}T"
    elif num >= 1e9: return f"${num/1e9:.2f}B"
    return f"${num:,.0f}"

# Navigation
with st.sidebar:
    st.title("🚀 Stocky AI")
    new_page = st.radio("Navigation", ["Dashboard", "Watchlist", "Stock Lookup", "Market Pulse"])
    if new_page != st.session_state.current_page:
        st.success(f"Navigated to {new_page}")
        st.session_state.current_page = new_page

# --- DASHBOARD PAGE ---
if new_page == "Dashboard":
    st.title("📊 Market Dashboard")
    with st.spinner("Loading dashboard..."):
        indices = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "DOW", "BTC-USD": "Bitcoin"}
        cols = st.columns(len(indices))
        for i, (sym, name) in enumerate(indices.items()):
            hist = get_ticker_history(sym, "2d")
            if not hist.empty:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[0]
                pct = ((curr - prev) / prev) * 100
                cols[i].metric(name, f"{curr:,.2f}", f"{pct:+.2f}%")
        
        st.markdown("---")
        sp_hist = get_ticker_history("^GSPC", "1mo")
        if not sp_hist.empty:
            fig = px.line(sp_hist, y='Close', template='plotly_dark')
            fig.update_traces(line=dict(color='#7F77DD', width=3), fill='tozeroy')
            fig.update_xaxes(showgrid=True, gridcolor='#30363d')
            fig.update_yaxes(showgrid=True, gridcolor='#30363d')
            fig.update_layout(xaxis_title="", yaxis_title="Price", height=450)
            st.plotly_chart(fig, use_container_width=True)

# --- STOCK LOOKUP PAGE ---
elif new_page == "Stock Lookup":
    # Search Bar
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        ticker_input = st.text_input("Enter Ticker Symbol", value="AAPL").upper()
    
    if ticker_input:
        with st.spinner(f"Analyzing {ticker_input}..."):
            info = get_ticker_info(ticker_input)
            if info:
                # Header
                st.title(info.get('longName', ticker_input))
                
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                curr_p = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                prev_c = info.get('previousClose', curr_p)
                day_chg_pct = ((curr_p - prev_c) / prev_c) * 100
                
                m1.metric("Current Price", f"${curr_p:,.2f}")
                m2.metric("Day Change (%)", f"{day_chg_pct:+.2f}%", f"{day_chg_pct:+.2f}%")
                m3.metric("Market Cap", format_large(info.get('marketCap', 0)))
                
                # 52-Week Range Custom Metric
                with m4:
                    st.markdown("<p style='color:#8b949e; font-size:0.9rem; margin-bottom:0.4rem;'>52-Week Range</p>", unsafe_allow_html=True)
                    low52 = info.get('fiftyTwoWeekLow', 0)
                    high52 = info.get('fiftyTwoWeekHigh', 0)
                    st.markdown(f"""
                        <div class="range-box">
                            <span class="range-low">{low52:,.2f}</span>
                            <span style="color:#8b949e;"> — </span>
                            <span class="range-high">{high52:,.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Controls Row
                ctrl_col1, ctrl_col2 = st.columns([2, 1])
                with ctrl_col1:
                    period = st.radio("Time Range", ["1D", "5D", "1M", "3M", "6M", "1Y"], index=5, horizontal=True)
                with ctrl_col2:
                    show_ma = st.checkbox("📊 Show Moving Averages (20-day & 50-day)", value=True)
                
                # Data Fetching for Chart
                period_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
                hist = get_ticker_history(ticker_input, period_map[period])
                
                if not hist.empty:
                    fig = go.Figure()
                    
                    # Candlestick
                    fig.add_trace(go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                        name="OHLC", increasing_line_color='#23d333', decreasing_line_color='#ff4b4b'
                    ))
                    
                    # Moving Averages
                    if show_ma:
                        # We need more history to calculate MAs accurately for short periods
                        hist_ma = get_ticker_history(ticker_input, "2y")
                        hist_ma['MA20'] = hist_ma['Close'].rolling(window=20).mean()
                        hist_ma['MA50'] = hist_ma['Close'].rolling(window=50).mean()
                        
                        # Filter to match the visible range
                        ma_visible = hist_ma.loc[hist.index[0]:hist.index[-1]]
                        
                        fig.add_trace(go.Scatter(x=ma_visible.index, y=ma_visible['MA20'], name="MA 20", line=dict(color='#FFD700', width=1.5)))
                        fig.add_trace(go.Scatter(x=ma_visible.index, y=ma_visible['MA50'], name="MA 50", line=dict(color='#FF8C00', width=1.5, dash='dash')))
                    
                    fig.update_layout(
                        template='plotly_dark',
                        height=600,
                        xaxis_rangeslider_visible=False,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                        margin=dict(t=50, b=10, l=10, r=10),
                        xaxis=dict(showgrid=True, gridcolor='#30363d'),
                        yaxis=dict(showgrid=True, gridcolor='#30363d', title="Price (USD)")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Historical data unavailable for this period.")
            else:
                st.error("Invalid Ticker Symbol.")

# --- OTHER PAGES ---
elif new_page == "Watchlist":
    st.title("📋 Market Watchlist")
    # (Existing Watchlist logic...)
    data_rows = []
    for s in st.session_state.watchlist:
        i = get_ticker_info(s)
        h = get_ticker_history(s, "7d")
        if i and not h.empty:
            cp = i.get('currentPrice') or i.get('regularMarketPrice', 0)
            pc = i.get('previousClose', cp)
            pct = ((cp - pc) / pc) * 100
            data_rows.append({"Ticker": s, "Price": cp, "Change (%)": pct, "7D Trend": h['Close'].tolist()})
    if data_rows:
        st.dataframe(pd.DataFrame(data_rows), column_config={"Price": st.column_config.NumberColumn(format="$%.2f"), "Change (%)": st.column_config.NumberColumn(format="%+.2f%%"), "7D Trend": st.column_config.LineChartColumn()}, hide_index=True, use_container_width=True)

elif new_page == "Market Pulse":
    st.title("⚡ Market Pulse")
    # (Existing Pulse logic...)
    st.info("Market Pulse summary and Movers...")

# Footer
st.markdown("<div class='footer'>Data from Yahoo Finance • Built with Streamlit & ❤️ by Antigravity</div>", unsafe_allow_html=True)