# Import Libraries
import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests
from datetime import datetime, timedelta

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
TELEGRAM_CHAT_ID = "6891630125"

# Function to Fetch Data
def fetch_data(ticker, period, interval):
    try:
        # Adjust ticker format for Forex pairs if necessary
        if ticker.upper() in ["USD/JPY", "EUR/USD", "GBP/USD"]:
            ticker = ticker.replace("/", "") + "=X"
        
        data = yf.download(ticker, period=period, interval=interval)
        
        # Remove duplicate column names by appending a unique suffix
        data.columns = pd.Index([f"{col}_{i}" if data.columns.duplicated()[i] else col 
                                 for i, col in enumerate(data.columns)])
        
        # Standardize column names to remove suffixes for easier reference
        data.rename(columns=lambda x: x.split("_")[0], inplace=True)
        
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

    # Ensure sufficient data rows for calculations
    if len(data) < 15:
        st.error("Not enough data for signal calculations.")
        return signals

    # Add RSI Signal
    data["RSI"] = ta.rsi(data["Close"], length=14)
    data["RSI"].fillna(50, inplace=True)  # Replace NaN values with neutral RSI (50)
    
    if data["RSI"].iloc[-1] > 70:
        signals.append("SELL (RSI Overbought)")
    elif data["RSI"].iloc[-1] < 30:
        signals.append("BUY (RSI Oversold)")

    # Add SMA Signal
    data["SMA_50"] = ta.sma(data["Close"], length=50)
    data["SMA_200"] = ta.sma(data["Close"], length=200)
    if pd.notna(data["SMA_50"].iloc[-1]) and pd.notna(data["SMA_200"].iloc[-1]):
        if data["SMA_50"].iloc[-1] > data["SMA_200"].iloc[-1]:
            signals.append("BUY (SMA Golden Cross)")
        elif data["SMA_50"].iloc[-1] < data["SMA_200"].iloc[-1]:
            signals.append("SELL (SMA Death Cross)")

    # Add Stochastic Oscillator Signal
    stoch = ta.stoch(data["High"], data["Low"], data["Close"], k=14, d=3)
    if stoch is not None:
        data["Stoch_K"] = stoch["STOCHk_14_3_3"]
        data["Stoch_D"] = stoch["STOCHd_14_3_3"]
        if data["Stoch_K"].iloc[-1] > 80:
            signals.append("SELL (Stochastic Overbought)")
        elif data["Stoch_K"].iloc[-1] < 20:
            signals.append("BUY (Stochastic Oversold)")

    return signals

# Function to Format and Send Signals
def send_telegram_signal(session, emoji, ticker, signals, session_start_time):
    try:
        for signal in signals:
            expiration_time = session_start_time + timedelta(minutes=5)
            level1_time = expiration_time + timedelta(minutes=5)
            level2_time = level1_time + timedelta(minutes=5)
            
            message = (
                f"{emoji} {session.upper()} SESSION\n"
                f"🟢 STARTED\n"
                f"🗓 {datetime.now().strftime('%A, %B %d, %Y')}\n"
                f"🇺🇸 {ticker} OTC\n"
                f"🕘 Expiration 5M\n"
                f"⏺ Entry at {session_start_time.strftime('%H:%M')}\n"
                f"🟥 {signal.split(' ')[0]} 🟩\n\n"
                f"🔽 Martingale levels\n"
                f"1️⃣ level at {level1_time.strftime('%H:%M')}\n"
                f"2️⃣ level at {level2_time.strftime('%H:%M')}\n"
            )
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        st.error(f"Error sending Telegram message: {e}")

# Main Application
def main():
    st.title("Trading Signal Generator")
    
    # Session Times (UTC-4)
    session_schedule = {
        "morning": ("06:25", "🌤"),
        "afternoon": ("12:25", "☀️"),
        "night": ("18:25", "🌙"),
        "overnight": ("00:25", "🌑"),
    }
    
    # User Inputs
    ticker = st.sidebar.text_input("Enter Ticker (e.g., USD/JPY, BTC-USD, EURUSD=X):", value="USD/JPY")
    period = st.sidebar.selectbox("Select Data Period", ["1d", "5d", "1mo", "3mo"])
    interval = st.sidebar.selectbox("Select Data Interval", ["1m", "5m", "15m", "1h", "1d"])

    # Fetch Data
    data = fetch_data(ticker, period, interval)
    session_start_time = datetime.now()

    if data is not None:
        st.write(f"Data for {ticker}:")
        st.dataframe(data.head())

        for session, (start_time, emoji) in session_schedule.items():
            signals = generate_signals(data)
            
            # Convert session start time to datetime
            session_start_time = datetime.strptime(start_time, "%H:%M").replace(
                year=datetime.now().year, month=datetime.now().month, day=datetime.now().day
            )
            
            if signals:
                send_telegram_signal(session, emoji, ticker, signals[:4], session_start_time)
                st.success(f"{session.capitalize()} signals sent to Telegram.")
            else:
                st.warning(f"No signals generated for {session.capitalize()} session.")
    else:
        st.warning("No data available. Please check the ticker or timeframe.")

if __name__ == "__main__":
    main()
