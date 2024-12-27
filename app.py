import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import requests

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
TELEGRAM_CHAT_ID = "6891630125"

# Market Sessions (UTC-4)
SESSIONS = {
    "Morning Session 🌤️": {"start": "06:25", "interval": 60, "signals": 4},
    "Afternoon Session ☀️": {"start": "12:25", "interval": 60, "signals": 4},
    "Night Session 🌙": {"start": "18:25", "interval": 60, "signals": 4},
    "Overnight Session 🌑": {"start": "00:25", "interval": 60, "signals": 4},
}

# Function to fetch market data
def fetch_data(ticker, period="5d", interval="5m"):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1=0&period2=9999999999&interval={interval}&events=history"
        data = pd.read_csv(url)
        data.rename(columns={"Adj Close": "Close"}, inplace=True)
        return data
    except Exception as e:
        st.warning(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# Function to generate trading signals
def generate_signals(data):
    signals = []
    if len(data) < 15:
        st.warning("Not enough data for generating signals.")
        return signals

    try:
        # Calculate RSI
        data["RSI"] = ta.rsi(data["Close"], length=14)
        if data["RSI"].iloc[-1] > 70:
            signals.append("SELL (RSI Overbought)")
        elif data["RSI"].iloc[-1] < 30:
            signals.append("BUY (RSI Oversold)")

        # Calculate SMA Crossovers
        data["SMA_50"] = ta.sma(data["Close"], length=50)
        data["SMA_200"] = ta.sma(data["Close"], length=200)
        if data["SMA_50"].iloc[-1] > data["SMA_200"].iloc[-1]:
            signals.append("BUY (SMA Golden Cross)")
        elif data["SMA_50"].iloc[-1] < data["SMA_200"].iloc[-1]:
            signals.append("SELL (SMA Death Cross)")
    except Exception as e:
        st.warning(f"Error generating signals: {e}")

    return signals

# Function to send signals to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.success("Signal sent to Telegram.")
        else:
            st.error(f"Failed to send signal: {response.text}")
    except Exception as e:
        st.error(f"Error sending signal to Telegram: {e}")

# Generate session signals
def generate_session_signals(session_name, start_time, interval, signals_per_session):
    utc_offset = -4
    current_time = datetime.utcnow() + timedelta(hours=utc_offset)
    session_start = datetime.strptime(start_time, "%H:%M").replace(
        year=current_time.year, month=current_time.month, day=current_time.day
    )

    if current_time >= session_start:
        st.write(f"Generating signals for {session_name}...")
        for i in range(signals_per_session):
            signal_time = session_start + timedelta(minutes=i * interval)
            if current_time >= signal_time:
                ticker = "USD/JPY=X"  # Example ticker, replace with your desired symbol
                data = fetch_data(ticker)
                signals = generate_signals(data)
                if signals:
                    signal_message = f"""
{session_name}
🗓 Date: {current_time.strftime('%A, %B %d, %Y')}
🇺🇸 USD/JPY OTC
🕘 Expiration 5M
⏺ Entry at {signal_time.strftime('%H:%M')}
🟥 {signals[0]} 🟩
🔽 Martingale levels
1️⃣ level at {(signal_time + timedelta(minutes=5)).strftime('%H:%M')}
2️⃣ level at {(signal_time + timedelta(minutes=10)).strftime('%H:%M')}
"""
                    send_telegram_message(signal_message)

# Main Function
def main():
    st.title("Trading Signal Generator")

    # Iterate through sessions
    for session_name, session_info in SESSIONS.items():
        generate_session_signals(
            session_name,
            session_info["start"],
            session_info["interval"],
            session_info["signals"],
        )

if __name__ == "__main__":
    main()
