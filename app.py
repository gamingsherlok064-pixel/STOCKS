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

    /* News Cards */
    .news-card { background-color: #1c2128; padding: 1.2rem; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 1rem; border-left: 5px solid #7F77DD; transition: all 0.2s; }
    .news-card:hover { border-color: #7F77DD; transform: translateX(5px); }
    .news-title { font-weight: 700; font-size: 1.1rem; margin-bottom: 0.4rem; color: #ffffff; }
    .news-meta { font-size: 0.8rem; color: #8b949e; }
    a { text-decoration: none; }

    /* Summary Bar */
    .summary-bar { display: flex; justify-content: space-around; background-color: #1c2128; padding: 1rem; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 2rem; }
    .gainer { color: #23d333; font-weight: 700; } .loser { color: #ff4b4b; font-weight: 700; }
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
    
    st.markdown("---")
    if new_page == "Watchlist":
        st.subheader("Manage List")
        t_add = st.text_input("Ticker Symbol", placeholder="e.g. BTC-USD").upper()
        if st.button("Add to Watchlist") and t_add:
            if t_add not in st.session_state.watchlist:
                st.session_state.watchlist.append(t_add)
                st.toast(f"Added {t_add}")
                st.rerun()

# --- DASHBOARD PAGE ---
if new_page == "Dashboard":
    st.title("📊 Market Dashboard")
    with st.spinner("Loading market data..."):
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
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("📈 S&P 500 Performance (30 Days)")
            sp_hist = get_ticker_history("^GSPC", "1mo")
            if not sp_hist.empty:
                fig = px.line(sp_hist, y='Close', template='plotly_dark')
                fig.update_traces(line=dict(color='#7F77DD', width=3), fill='tozeroy')
                fig.update_xaxes(showgrid=True, gridcolor='#30363d')
                fig.update_yaxes(showgrid=True, gridcolor='#30363d')
                fig.update_layout(xaxis_title="", yaxis_title="Price", height=450, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
        with col_right:
            st.subheader("💰 P&L Calculator")
            c_tick = st.text_input("Ticker", value="AAPL").upper()
            c_shares = st.number_input("Shares", value=10, min_value=1)
            c_buy = st.number_input("Buy Price ($)", value=150.0)
            if c_tick:
                info = get_ticker_info(c_tick)
                if info:
                    curr = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                    pnl = (curr - c_buy) * c_shares
                    p_pct = (pnl / (c_buy * c_shares)) * 100 if c_buy != 0 else 0
                    st.metric("Net Profit / Loss", f"${pnl:,.2f}", f"{p_pct:+.2f}%")

# --- WATCHLIST PAGE ---
elif new_page == "Watchlist":
    st.title("📋 Market Watchlist")
    with st.spinner("Updating watchlist..."):
        data_rows = []
        g, l = 0, 0
        for symbol in st.session_state.watchlist:
            info = get_ticker_info(symbol)
            hist = get_ticker_history(symbol, "7d")
            if info and not hist.empty:
                curr = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
                prev = info.get('previousClose', curr)
                chg = curr - prev
                pct = (chg / prev) * 100
                if chg > 0: g += 1
                elif chg < 0: l += 1
                data_rows.append({"Ticker": symbol, "Price": curr, "Change (%)": pct, "7D Trend": hist['Close'].tolist()})
        
        if data_rows:
            st.markdown(f"<div class='summary-bar'><div class='gainer'>Gainers: {g}</div><div class='loser'>Losers: {l}</div></div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(data_rows), column_config={"Price": st.column_config.NumberColumn(format="$%.2f"), "Change (%)": st.column_config.NumberColumn(format="%+.2f%%"), "7D Trend": st.column_config.LineChartColumn()}, hide_index=True, use_container_width=True)
            
            st.markdown("### Remove Tickers")
            rm_cols = st.columns(len(st.session_state.watchlist) if st.session_state.watchlist else 1)
            for i, sym in enumerate(st.session_state.watchlist):
                if rm_cols[i % len(rm_cols)].button(f"🗑️ {sym}", key=f"rm_{sym}"):
                    st.session_state.watchlist.remove(sym)
                    st.rerun()

# --- STOCK LOOKUP PAGE ---
elif new_page == "Stock Lookup":
    ticker_input = st.text_input("Enter Ticker Symbol", value="AAPL").upper()
    if ticker_input:
        with st.spinner(f"Analyzing {ticker_input}..."):
            info = get_ticker_info(ticker_input)
            if info:
                st.title(info.get('longName', ticker_input))
                m1, m2, m3, m4 = st.columns(4)
                curr_p = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                prev_c = info.get('previousClose', curr_p)
                day_chg_pct = ((curr_p - prev_c) / prev_c) * 100
                
                m1.metric("Current Price", f"${curr_p:,.2f}")
                m2.metric("Day Change (%)", f"{day_chg_pct:+.2f}%", f"{day_chg_pct:+.2f}%")
                m3.metric("Market Cap", format_large(info.get('marketCap', 0)))
                with m4:
                    st.markdown("<p style='color:#8b949e; font-size:0.9rem; margin-bottom:0.4rem;'>52-Week Range</p>", unsafe_allow_html=True)
                    l52 = info.get('fiftyTwoWeekLow', 0); h52 = info.get('fiftyTwoWeekHigh', 0)
                    st.markdown(f"<div class='range-box'><span class='range-low'>{l52:,.2f}</span><span style='color:#8b949e;'> — </span><span class='range-high'>{h52:,.2f}</span></div>", unsafe_allow_html=True)
                
                st.markdown("---")
                ctrl_c1, ctrl_c2 = st.columns([2, 1])
                with ctrl_c1:
                    period = st.radio("Time Range", ["1D", "5D", "1M", "3M", "6M", "1Y"], index=5, horizontal=True)
                with ctrl_c2:
                    show_ma = st.checkbox("📊 Show Moving Averages (20-day & 50-day)", value=True)
                
                p_map = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
                hist = get_ticker_history(ticker_input, p_map[period])
                if not hist.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="OHLC", increasing_line_color='#23d333', decreasing_line_color='#ff4b4b'))
                    if show_ma:
                        hist_ma = get_ticker_history(ticker_input, "2y")
                        hist_ma['MA20'] = hist_ma['Close'].rolling(window=20).mean()
                        hist_ma['MA50'] = hist_ma['Close'].rolling(window=50).mean()
                        ma_vis = hist_ma.loc[hist.index[0]:hist.index[-1]]
                        fig.add_trace(go.Scatter(x=ma_vis.index, y=ma_vis['MA20'], name="MA 20", line=dict(color='#FFD700', width=1.5)))
                        fig.add_trace(go.Scatter(x=ma_vis.index, y=ma_vis['MA50'], name="MA 50", line=dict(color='#FF8C00', width=1.5, dash='dash')))
                    fig.update_layout(template='plotly_dark', height=600, xaxis_rangeslider_visible=False, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), margin=dict(t=50, b=10, l=10, r=10), xaxis=dict(showgrid=True, gridcolor='#30363d'), yaxis=dict(showgrid=True, gridcolor='#30363d', title="Price (USD)"))
                    st.plotly_chart(fig, use_container_width=True)
            else: st.error("Invalid Ticker Symbol.")

# --- MARKET PULSE PAGE ---
elif new_page == "Market Pulse":
    st.title("⚡ Market Pulse")
    with st.spinner("Updating pulse..."):
        col_n, col_p = st.columns([1, 1])
        with col_n:
            st.subheader("📰 Market News")
            try: api_key = st.secrets.get("GNEWS_API_KEY", "")
            except: api_key = ""
            if api_key and api_key != "YOUR_API_KEY_HERE":
                try:
                    r = requests.get(f"https://gnews.io/api/v4/search?q=stock%20market&token={api_key}").json()
                    for art in r.get('articles', [])[:8]:
                        st.markdown(f"<a href='{art['url']}' target='_blank'><div class='news-card'><div class='news-title'>{art['title']}</div><div class='news-meta'>{art['source']['name']} • {art['publishedAt'][:10]}</div></div></a>", unsafe_allow_html=True)
                except: st.error("Failed to load news.")
            else:
                st.info("Live news requires an API Key. Showing trending topics:")
                trending = ["Fed signals interest rate hold", "Tech sector rallies on strong forecasts", "Retail spending shows resilience"]
                for t in trending:
                    st.markdown(f"<div class='news-card'><div class='news-title'>{t}</div><div class='news-meta'>Market Trend • Today</div></div>", unsafe_allow_html=True)

        with col_p:
            st.subheader("🔥 Sector Heatmap")
            sects = {"XLK": "Tech", "XLF": "Finance", "XLE": "Energy", "XLV": "Health", "XLY": "Consumer"}
            hm_d = []
            for t, n in sects.items():
                hist = get_ticker_history(t, "2d")
                if len(hist) >= 2:
                    c = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    hm_d.append({"Sector": n, "Change": c, "Parent": "Market"})
            if hm_d:
                f_hm = px.treemap(pd.DataFrame(hm_d), path=['Parent', 'Sector'], values=[1]*len(hm_d), color='Change', color_continuous_scale='RdYlGn', range_color=[-3, 3])
                f_hm.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='#0e1117')
                st.plotly_chart(f_hm, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🏆 Market Movers")
            movers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
            m_d = []
            for s in movers:
                hist = get_ticker_history(s, "2d")
                if len(hist) >= 2:
                    c = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    m_d.append({"Ticker": s, "Change (%)": c})
            if m_d:
                df_m = pd.DataFrame(m_d).sort_values("Change (%)", ascending=False)
                c1, c2 = st.columns(2)
                with c1: st.caption("Top Gainers"); st.dataframe(df_m.head(3), hide_index=True)
                with c2: st.caption("Top Losers"); st.dataframe(df_m.tail(3).iloc[::-1], hide_index=True)

# Footer
st.markdown("<div class='footer'>Data from Yahoo Finance • Refreshed every 5 min • Built with ❤️ by Antigravity</div>", unsafe_allow_html=True)
