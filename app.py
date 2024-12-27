# Import Libraries
import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
TELEGRAM_CHAT_ID = "6891630125"

# Function to Fetch Data
def fetch_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]
        data = data.rename(columns=lambda x: x.split("_")[-1])  # Standardize column names
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Generate Trading Signals
def generate_signals(data):
    signals = []
    
    # Ensure required columns exist
    if "Close" not in data.columns or "High" not in data.columns or "Low" not in data.columns:
        st.error("Missing required columns (High, Low, Close) in the data.")
        return signals
    
    # Add RSI Signal
    data["RSI"] = ta.rsi(data["Close"], length=14)
    if data["RSI"].iloc[-1] > 70:
        signals.append("SELL (RSI Overbought)")
    elif data["RSI"].iloc[-1] < 30:
        signals.append("BUY (RSI Oversold)")

    # Add SMA Signal
    data["SMA_50"] = ta.sma(data["Close"], length=50)
    data["SMA_200"] = ta.sma(data["Close"], length=200)
    if data["SMA_50"].iloc[-1] > data["SMA_200"].iloc[-1]:
        signals.append("BUY (SMA Golden Cross)")
    elif data["SMA_50"].iloc[-1] < data["SMA_200"].iloc[-1]:
        signals.append("SELL (SMA Death Cross)")

    # Add Stochastic Oscillator Signal (if data has High/Low/Close)
    if "High" in data.columns and "Low" in data.columns and "Close" in data.columns:
        stoch = ta.stoch(data["High"], data["Low"], data["Close"], k=14, d=3)
        if stoch is not None:
            data["Stoch_K"] = stoch["STOCHk_14_3_3"]
            data["Stoch_D"] = stoch["STOCHd_14_3_3"]
            if data["Stoch_K"].iloc[-1] > 80:
                signals.append("SELL (Stochastic Overbought)")
            elif data["Stoch_K"].iloc[-1] < 20:
                signals.append("BUY (Stochastic Oversold)")

    return signals

# Function to Send Signals to Telegram
def send_telegram_signal(ticker, signals):
    try:
        for signal in signals:
            message = f"🔔 **Trading Signal** 🔔\n📈 Ticker: {ticker}\n📉 Signal: {signal}\n⏳ Expiration: 5 mins\n"
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        st.error(f"Error sending Telegram message: {e}")

# Main Application
def main():
    st.title("Trading Signal Generator")

    # User Inputs
    ticker = st.sidebar.text_input("Enter Ticker (e.g., AAPL, BTC-USD, EURUSD=X):", value="AAPL")
    period = st.sidebar.selectbox("Select Data Period", ["1d", "5d", "1mo", "3mo"])
    interval = st.sidebar.selectbox("Select Data Interval", ["1m", "5m", "15m", "1h", "1d"])

    # Fetch Data
    data = fetch_data(ticker, period, interval)

    if data is not None:
        st.write(f"Data for {ticker}:")
        st.dataframe(data.head())

        # Generate Signals
        signals = generate_signals(data)
        if signals:
            send_telegram_signal(ticker, signals)
            st.success(f"Signals sent to Telegram: {', '.join(signals)}")
        else:
            st.warning("No signals generated.")
    else:
        st.warning("No data available. Please check the ticker or timeframe.")

if __name__ == "__main__":
    main()
