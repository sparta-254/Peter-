import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time
from datetime import datetime, timedelta
import requests

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
TELEGRAM_CHAT_ID = "6891630125"

# Trading Sessions
sessions = {
    "Morning": (6, 12),
    "Afternoon": (12, 18),
    "Night": (18, 24),
    "OverNight": (0, 6)
}

# Fetch Data Function
def fetch_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Generate Signals Function
def generate_signal(data):
    data["RSI"] = ta.rsi(data["Close"], length=14)
    data["SMA"] = ta.sma(data["Close"], length=14)
    signal = None

    if data["RSI"].iloc[-1] > 70:
        signal = "SELL"
    elif data["RSI"].iloc[-1] < 30:
        signal = "BUY"

    return signal

# Telegram Message Sender
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Error sending message: {e}")

# Determine Current Session
def get_current_session():
    now = datetime.now()
    for session, (start_hour, end_hour) in sessions.items():
        start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        if start <= now < end:
            return session
    return None

# Main Logic
tickers = ["EURJPY=X", "USDJPY=X"]  # Add more currency pairs or OTC tickers
session_signals = {session: [] for session in sessions.keys()}

while True:
    current_session = get_current_session()
    if current_session:
        for ticker in tickers:
            data = fetch_data(ticker, "5d", "1m")
            if data is not None:
                signal = generate_signal(data)
                if signal:
                    # Generate signal details
                    expiration = datetime.now() + timedelta(minutes=5)
                    martingale1 = expiration + timedelta(minutes=5)
                    martingale2 = martingale1 + timedelta(minutes=5)

                    message = f"""
{ticker}

OTC

Expiration 5M

Entry at {datetime.now().strftime('%H:%M')}

{signal}

Martingale levels
1 level at {martingale1.strftime('%H:%M')}
2 level at {martingale2.strftime('%H:%M')}
"""

                    # Check for duplicate signals
                    if len(session_signals[current_session]) < 7 and message not in session_signals[current_session]:
                        session_signals[current_session].append(message)
                        send_telegram_message(message)
    time.sleep(300)  # Sleep for 5 minutes before fetching again
