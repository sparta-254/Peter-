# Import required libraries
import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time
import requests

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
CHAT_ID = "6891630125"  # Replace with your chat ID

# Streamlit App Configuration
st.title("Real-Time Trading Signal Dashboard")
st.sidebar.header("Settings")

# User Inputs
tickers = st.sidebar.text_area("Enter Asset Tickers (comma-separated, e.g., AAPL, BTC-USD, EURUSD=X)", value="AAPL, BTC-USD")
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "1d"])
indicator = st.sidebar.multiselect("Select Indicators", ["SMA", "EMA", "RSI", "MACD", "Bollinger Bands"])
update_interval = st.sidebar.slider("Update Interval (seconds)", 10, 3600, 60)

# Adjust period dynamically based on the selected timeframe
if timeframe == "1m":
    period = "5d"
else:
    period = "1mo"

# Fetch Live Data
def fetch_data(ticker, period, interval):
    try:
        st.write(f"Fetching data for {ticker} with period '{period}' and interval '{interval}'...")
        data = yf.download(ticker, period=period, interval=interval)

        # Flatten multi-index columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]

        # Ensure 'Close' column exists
        if f"Close_{ticker}" not in data.columns:
            st.error(f"'Close' column not found in the data for {ticker}.")
            return None

        # Rename columns for simplicity
        data = data.rename(columns={
            f"Close_{ticker}": "Close",
            f"High_{ticker}": "High",
            f"Low_{ticker}": "Low",
            f"Open_{ticker}": "Open",
            f"Volume_{ticker}": "Volume"
        })

        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Generate Trading Signals
def generate_signals(data, indicator_list):
    signals = {}
    try:
        if "Close" in data.columns:
            if "SMA" in indicator_list:
                data["SMA"] = ta.sma(data["Close"], length=14)
                signals["SMA"] = data[["Close", "SMA"]].iloc[-1]
            if "EMA" in indicator_list:
                data["EMA"] = ta.ema(data["Close"], length=14)
                signals["EMA"] = data[["Close", "EMA"]].iloc[-1]
            if "RSI" in indicator_list:
                data["RSI"] = ta.rsi(data["Close"], length=14)
                signals["RSI"] = data["RSI"].iloc[-1]
            if "MACD" in indicator_list:
                macd = ta.macd(data["Close"], fast=12, slow=26, signal=9)
                if macd is not None:
                    data["MACD"] = macd["MACD_12_26_9"]
                    data["Signal"] = macd["MACDs_12_26_9"]
                    signals["MACD"] = data[["MACD", "Signal"]].iloc[-1]
            if "Bollinger Bands" in indicator_list:
                bollinger = ta.bbands(data["Close"], length=20, std=2.0)
                if bollinger is not None:
                    data["Bollinger High"] = bollinger["BBU_20_2.0"]
                    data["Bollinger Low"] = bollinger["BBL_20_2.0"]
                    signals["Bollinger Bands"] = data[["Close", "Bollinger High", "Bollinger Low"]].iloc[-1]

        return signals
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
        return None

# Send Signals to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=params)
        if response.status_code == 200:
            st.success("Signal sent to Telegram!")
        else:
            st.error(f"Failed to send message. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error sending message to Telegram: {e}")

# Main App Logic
tickers_list = [ticker.strip() for ticker in tickers.split(",")]
while True:
    for ticker in tickers_list:
        data = fetch_data(ticker, period, timeframe)
        if data is not None:
            signals = generate_signals(data, indicator)
            if signals:
                for name, signal in signals.items():
                    message = f"Trading Signal for {ticker} ({name}):\n{signal.to_string()}"
                    send_telegram_message(message)
    time.sleep(update_interval)
