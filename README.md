# 📈 Stocky AI Dashboard

Stocky AI is a premium, real-time financial dashboard built with **Streamlit**, **yfinance**, and **Plotly**. It provides investors with a comprehensive suite of tools to track the market, analyze specific stocks, and manage their portfolio.

## 🚀 Features

- **📊 Interactive Dashboard**: High-level view of major indices (S&P 500, NASDAQ, DOW) and a 30-day performance chart.
- **💰 P&L Calculator**: Quick calculation of portfolio gains/losses based on buy price and shares.
- **📋 Market Watchlist**: Custom watchlist with real-time price updates and 7-day trend sparklines.
- **🔍 Detailed Analysis**: Professional-grade candlestick charts with volume and moving average overlays.
- **💡 Market Insights**: Sentiment analysis using the VIX Volatility Index and live financial news via GNews API.
- **🎨 Premium UI**: Sleek dark mode with custom CSS, rounded metric cards, and smooth transitions.

## 🛠️ Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.8+ installed.

### 2. Installation
Clone the repository and install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. API Configuration
To enable live news on the Market Insights page:
1. Get a free API key at [gnews.io](https://gnews.io).
2. Create a `.streamlit/secrets.toml` file in the project root.
3. Add your key:
   ```toml
   GNEWS_API_KEY = "your_key_here"
   ```

### 4. Running the App
Execute the following command:
```bash
streamlit run app.py
```

## ☁️ Deployment

This app is optimized for **Streamlit Community Cloud**. 
1. Push your code to a GitHub repository.
2. Connect the repository to Streamlit Cloud.
3. Add your `GNEWS_API_KEY` in the Streamlit Cloud Dashboard secrets section.

---
Built with ❤️ by Antigravity
