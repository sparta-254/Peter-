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

# OTC Currency Symbols
OTC_SYMBOLS = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", 
    "USDCAD=X", "EURJPY=X", "GBPJPY=X"
]

# Fetch Data Function
def fetch_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]
        for col in data.columns:
            if "Close" in col:
                data = data.rename(columns={col: "Close"})
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Generate Signals
def generate_signals(data):
    signals = []
    
    if "Close" in data.columns:
        # RSI Signal
        data["RSI"] = ta.rsi(data["Close"], length=14)
        if data["RSI"].iloc[-1] > 70:
            signals.append("SELL (RSI Overbought)")
        elif data["RSI"].iloc[-1] < 30:
            signals.append("BUY (RSI Oversold)")

        # SMA Signal
        data["SMA_50"] = ta.sma(data["Close"], length=50)
        data["SMA_200"] = ta.sma(data["Close"], length=200)
        if data["SMA_50"].iloc[-1] > data["SMA_200"].iloc[-1]:
            signals.append("BUY (SMA Golden Cross)")
        elif data["SMA_50"].iloc[-1] < data["SMA_200"].iloc[-1]:
            signals.append("SELL (SMA Death Cross)")

        # EMA Signal
        data["EMA_12"] = ta.ema(data["Close"], length=12)
        data["EMA_26"] = ta.ema(data["Close"], length=26)
        if data["EMA_12"].iloc[-1] > data["EMA_26"].iloc[-1]:
            signals.append("BUY (EMA Crossover)")
        elif data["EMA_12"].iloc[-1] < data["EMA_26"].iloc[-1]:
            signals.append("SELL (EMA Crossover)")

        # MACD Signal
        macd = ta.macd(data["Close"], fast=12, slow=26, signal=9)
        if macd is not None:
            data["MACD"] = macd["MACD_12_26_9"]
            data["Signal_Line"] = macd["MACDs_12_26_9"]
            if data["MACD"].iloc[-1] > data["Signal_Line"].iloc[-1]:
                signals.append("BUY (MACD Bullish Crossover)")
            elif data["MACD"].iloc[-1] < data["Signal_Line"].iloc[-1]:
                signals.append("SELL (MACD Bearish Crossover)")

        # Bollinger Bands Signal
        bollinger = ta.bbands(data["Close"], length=20, std=2.0)
        if bollinger is not None:
            data["BB_Upper"] = bollinger["BBU_20_2.0"]
            data["BB_Lower"] = bollinger["BBL_20_2.0"]
            if data["Close"].iloc[-1] >= data["BB_Upper"].iloc[-1]:
                signals.append("SELL (Price Above Upper Bollinger Band)")
            elif data["Close"].iloc[-1] <= data["BB_Lower"].iloc[-1]:
                signals.append("BUY (Price Below Lower Bollinger Band)")

        # Stochastic Oscillator Signal
        stoch = ta.stoch(data["High"], data["Low"], data["Close"], k=14, d=3)
        if stoch is not None:
            data["Stoch_K"] = stoch["STOCHk_14_3_3"]
            data["Stoch_D"] = stoch["STOCHd_14_3_3"]
            if data["Stoch_K"].iloc[-1] > 80:
                signals.append("SELL (Stochastic Overbought)")
            elif data["Stoch_K"].iloc[-1] < 20:
                signals.append("BUY (Stochastic Oversold)")

    return signals

# Send Signals to Telegram
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
    st.title("Advanced Trading Signal Dashboard")

    # User Inputs
    ticker = st.sidebar.selectbox("Select Ticker (Forex/OTC)", OTC_SYMBOLS + ["AAPL", "BTC-USD"])
    timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "1d"])
    period = "5d" if timeframe in ["1m", "5m"] else "1mo"

    # Fetch Data
    st.write(f"Fetching data for {ticker}...")
    data = fetch_data(ticker, period, timeframe)

    if data is not None:
        st.write("Data Sample:")
        st.dataframe(data.head())

        # Generate Signals
        signals = generate_signals(data)
        if signals:
            send_telegram_signal(ticker, signals)
            st.write(f"Signals Sent: {', '.join(signals)}")
        else:
            st.write("No valid signals generated.")
    else:
        st.warning("No data available. Please check the ticker or timeframe.")

if __name__ == "__main__":
    main()
