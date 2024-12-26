import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# App Title
st.title("Trading Signal Dashboard")

# User Inputs
ticker = st.text_input("Enter Stock Ticker:", value="AAPL")
period = st.selectbox("Select Period:", options=["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=1)
interval = st.selectbox("Select Interval:", options=["1m", "5m", "15m", "1h", "1d"], index=3)

# Fetch Data
try:
    st.info(f"Fetching data for {ticker} with period '{period}' and interval '{interval}'...")
    data = yf.download(tickers=ticker, period=period, interval=interval)
    if data.empty:
        st.error(f"No data found for {ticker}. Please check the ticker or timeframe.")
    else:
        st.success("Data fetched successfully!")
        
        # Preprocess Data
        data.reset_index(inplace=True)
        data["Datetime"] = data["Datetime"].astype(str)
        
        # Add Indicators
        data["SMA"] = ta.sma(data["Close"], length=14)
        data["RSI"] = ta.rsi(data["Close"], length=14)
        macd = ta.macd(data["Close"], fast=12, slow=26, signal=9)
        data["MACD"] = macd["MACD_12_26_9"]
        data["Signal_Line"] = macd["MACDs_12_26_9"]
        
        # Display Chart
        st.line_chart(data[["Close", "SMA"]])
        
        # Display Processed Data
        st.subheader("Processed Data")
        st.dataframe(data[["Datetime", "Close", "High", "Low", "SMA", "RSI", "MACD", "Signal_Line"]])

        # Trading Signals
        st.subheader("Trading Signals")
        latest_close = data["Close"].iloc[-1]
        latest_sma = data["SMA"].iloc[-1]
        latest_rsi = data["RSI"].iloc[-1]
        latest_macd = data["MACD"].iloc[-1]
        latest_signal_line = data["Signal_Line"].iloc[-1]

        # SMA Signal
        if latest_close > latest_sma:
            st.success(f"Buy Signal: Price ({latest_close}) is above SMA ({latest_sma})")
        elif latest_close < latest_sma:
            st.error(f"Sell Signal: Price ({latest_close}) is below SMA ({latest_sma})")
        else:
            st.info("Neutral Signal: Price equals SMA")

        # RSI Signal
        if latest_rsi < 30:
            st.success(f"RSI ({latest_rsi}): Oversold - Buy Signal")
        elif latest_rsi > 70:
            st.error(f"RSI ({latest_rsi}): Overbought - Sell Signal")
        else:
            st.info(f"RSI ({latest_rsi}): Neutral")

        # MACD Signal
        if latest_macd > latest_signal_line:
            st.success(f"MACD: Bullish Crossover - Buy Signal")
        elif latest_macd < latest_signal_line:
            st.error(f"MACD: Bearish Crossover - Sell Signal")
        else:
            st.info("MACD: Neutral")

except Exception as e:
    st.error(f"Error calculating indicators: {e}")
