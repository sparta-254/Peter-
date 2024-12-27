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

        # Flatten MultiIndex columns (if any) and handle duplicate column names
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]
        else:
            data.columns = [col if col not in data.columns[:i] else f"{col}_{i}" 
                            for i, col in enumerate(data.columns)]
        
        # Rename columns to standard format
        data.columns = [col.split("_")[0] for col in data.columns]
        
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Generate Trading Signals
def generate_signals(data):
    signals = []
    
    # Ensure required columns exist
    if not all(col in data.columns for col in ["Close", "High", "Low"]):
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
    
    # Handle NaN/None values in SMA columns
    if data["SMA_50"].isnull().any() or data["SMA_200"].isnull().any():
        st.warning("Insufficient data to calculate SMA indicators. Signals may be incomplete.")
    else:
        # Compare SMA values only if they are valid
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
        st.write(f"Fetched data columns:\n{data.columns.tolist()}")
        st.write(f"Data for {ticker}:")
        st.write(data.head())  # Display data safely

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
