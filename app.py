# Install required libraries
# pip install streamlit pandas numpy ta yfinance

import streamlit as st
import pandas as pd
import numpy as np
import pandas_ta as ta  # For technical indicators
import yfinance as yf   # For fetching live market data

# Streamlit App Configuration
st.title("Trading Signal Dashboard")
st.sidebar.header("Settings")

# User Inputs
ticker = st.sidebar.text_input("Enter Stock/Asset Ticker (e.g., AAPL, BTC-USD)", value="AAPL")
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "1d"])
indicator = st.sidebar.selectbox("Select Indicator", ["SMA", "EMA", "RSI", "MACD", "Bollinger Bands"])

# Adjust period dynamically based on the selected timeframe
if timeframe == "1m":
    period = "5d"  # Use 5 days for 1-minute interval
else:
    period = "1mo"  # Default to 1 month for other intervals

# Fetch Live Data
@st.cache_data
def fetch_data(ticker, period, interval):
    try:
        # Download data
        data = yf.download(ticker, period=period, interval=interval)
        
        # Check if data is empty
        if data.empty:
            st.warning(f"No data found for {ticker}. The ticker might be invalid or delisted.")
            return None
        
        # Ensure required column 'Close' exists
        if "Close" not in data.columns:
            st.error(f"Data for {ticker} does not contain 'Close' prices.")
            return None
        
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Fetch the data
data = fetch_data(ticker, period, timeframe)

if data is not None:
    st.write("Raw Data Sample:")
    st.dataframe(data.head())

    # Calculate Indicators
    try:
        if "Close" in data.columns:
            data["SMA"] = ta.sma(data["Close"], length=14)
            data["EMA"] = ta.ema(data["Close"], length=14)
            data["RSI"] = ta.rsi(data["Close"], length=14)

            macd = ta.macd(data["Close"])
            if macd is not None:
                data["MACD"] = macd["MACD_12_26_9"]
                data["Signal"] = macd["MACDs_12_26_9"]
            else:
                data["MACD"], data["Signal"] = np.nan, np.nan

            bollinger = ta.bbands(data["Close"])
            if bollinger is not None:
                data["Bollinger High"] = bollinger["BBU_20_2.0"]
                data["Bollinger Low"] = bollinger["BBL_20_2.0"]
            else:
                data["Bollinger High"], data["Bollinger Low"] = np.nan, np.nan
        else:
            st.error("No 'Close' column found in data. Unable to calculate indicators.")

        # Display Data
        st.subheader(f"Price Data for {ticker}")
        st.dataframe(data.tail())

        # Plot Selected Indicator
        st.subheader(f"{indicator} Indicator Chart")
        if indicator == "SMA":
            st.line_chart(data[["Close", "SMA"]])
        elif indicator == "EMA":
            st.line_chart(data[["Close", "EMA"]])
        elif indicator == "RSI":
            st.line_chart(data[["RSI"]])
        elif indicator == "MACD":
            st.line_chart(data[["MACD", "Signal"]])
        elif indicator == "Bollinger Bands":
            st.line_chart(data[["Close", "Bollinger High", "Bollinger Low"]])

        # Signal Output
        st.subheader("Trading Signals")
        if indicator == "RSI":
            latest_rsi = data["RSI"].iloc[-1]
            if latest_rsi < 30:
                st.success("Buy Signal (Oversold)")
            elif latest_rsi > 70:
                st.error("Sell Signal (Overbought)")
            else:
                st.info("Neutral Signal")
        elif indicator == "MACD":
            latest_macd = data["MACD"].iloc[-1]
            latest_signal = data["Signal"].iloc[-1]
            if latest_macd > latest_signal:
                st.success("Buy Signal (MACD > Signal Line)")
            else:
                st.error("Sell Signal (MACD < Signal Line)")
        else:
            st.info("Signal generation only available for RSI and MACD.")
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
else:
    st.warning("No data available. Please check the ticker or timeframe.")
