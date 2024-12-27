# Import Libraries
import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
from datetime import datetime

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
TELEGRAM_CHAT_ID = "6891630125"

# Trading Sessions
SESSIONS = {
    "Morning": {"start": 6, "end": 12},
    "Afternoon": {"start": 12, "end": 18},
    "Night": {"start": 18, "end": 24},
    "Overnight": {"start": 0, "end": 6},
}

# Fetch Data Function
def fetch_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)

        # Flatten multi-index columns, if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]

        # Rename columns for compatibility
        for col in data.columns:
            if "Close" in col:
                data = data.rename(columns={col: "Close"})
            elif "High" in col:
                data = data.rename(columns={col: "High"})
            elif "Low" in col:
                data = data.rename(columns={col: "Low"})
            elif "Open" in col:
                data = data.rename(columns={col: "Open"})
            elif "Volume" in col:
                data = data.rename(columns={col: "Volume"})

        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Signal Generation Function
def generate_signal(data, indicator):
    close_column = [col for col in data.columns if 'Close' in col]
    if not close_column:
        raise KeyError("'Close' column not found in the data.")
    close_column = close_column[0]

    # Generate signals based on the selected indicator
    signal = None
    if indicator == "RSI":
        data["RSI"] = ta.rsi(data[close_column], length=14)
        if data["RSI"].iloc[-1] > 70:
            signal = "SELL"
        elif data["RSI"].iloc[-1] < 30:
            signal = "BUY"
    elif indicator == "SMA":
        data["SMA"] = ta.sma(data[close_column], length=14)
        if data[close_column].iloc[-1] > data["SMA"].iloc[-1]:
            signal = "BUY"
        else:
            signal = "SELL"

    return signal

# Send Signal to Telegram
def send_telegram_signal(ticker, signal, session, timeframe, expiration_time):
    try:
        message = (
            f"🔔 **Trading Signal** 🔔\n"
            f"📈 Ticker: {ticker}\n"
            f"🕒 Session: {session}\n"
            f"📉 Signal: {signal}\n"
            f"⏳ Timeframe: {timeframe}\n"
            f"📅 Expiration: {expiration_time} mins\n"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            st.write("Signal sent to Telegram!")
        else:
            st.error("Failed to send signal to Telegram.")
    except Exception as e:
        st.error(f"Error sending Telegram message: {e}")

# Main Application
def main():
    st.title("Trading Signal Dashboard")

    # User Inputs
    ticker = st.sidebar.text_input("Enter Stock/Asset Ticker (e.g., AAPL, BTC-USD, EURJPY=X)", value="BTC-USD")
    timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "1d"])
    period = "5d" if timeframe in ["1m", "5m"] else "1mo"
    indicator = st.sidebar.selectbox("Select Indicator", ["RSI", "SMA"])

    # Fetch Data
    st.write(f"Fetching data for {ticker} with period '{period}' and interval '{timeframe}'...")
    data = fetch_data(ticker, period, timeframe)

    if data is not None:
        st.write("Data Sample:")
        st.dataframe(data.head())

        # Generate Signals for Each Session
        current_hour = datetime.utcnow().hour
        for session, times in SESSIONS.items():
            if times["start"] <= current_hour < times["end"]:
                signal = generate_signal(data, indicator)
                if signal:
                    send_telegram_signal(ticker, signal, session, timeframe, expiration_time=5)
                    st.write(f"Signal for {session}: {signal}")
                else:
                    st.write(f"No valid signal generated for {session}.")
    else:
        st.warning("No data available. Please check the ticker or timeframe.")

# Run the Application
if __name__ == "__main__":
    main()
