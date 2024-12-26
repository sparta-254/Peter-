# Install required libraries
# pip install streamlit pandas numpy pandas_ta yfinance

import streamlit as st
import pandas as pd
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
        st.write(f"Fetching data for {ticker} with period '{period}' and interval '{interval}'...")
        data = yf.download(ticker, period=period, interval=interval)
        
        # Debug: Display raw data structure and column names
        st.write("Raw data structure:", data)
        st.write("Columns in data:", data.columns.tolist())

        # Flatten multi-index columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]
        
        # Ensure "Close" column exists
        if "Close" not in data.columns:
            st.error("No 'Close' column in the data. Unable to calculate indicators.")
            return None
        
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Fetch the data
data = fetch_data(ticker, period, timeframe)

if data is not None and not data.empty:
    st.write("Raw Data Sample:")
    st.dataframe(data.head())

    # Calculate Indicators
    try:
        if "Close" in data.columns:
            # Calculate indicators
            if indicator == "SMA":
                data["SMA"] = ta.sma(data["Close"], length=14)
                st.line_chart(data[["Close", "SMA"]])
            elif indicator == "EMA":
                data["EMA"] = ta.ema(data["Close"], length=14)
                st.line_chart(data[["Close", "EMA"]])
            elif indicator == "RSI":
                data["RSI"] = ta.rsi(data["Close"], length=14)
                st.line_chart(data[["RSI"]])
            elif indicator == "MACD":
                macd = ta.macd(data["Close"], fast=12, slow=26, signal=9)
                if macd is not None:
                    data["MACD"] = macd["MACD_12_26_9"]
                    data["Signal"] = macd["MACDs_12_26_9"]
                    st.line_chart(data[["MACD", "Signal"]])
            elif indicator == "Bollinger Bands":
                bollinger = ta.bbands(data["Close"], length=20, std=2.0)
                if bollinger is not None:
                    data["Bollinger High"] = bollinger["BBU_20_2.0"]
                    data["Bollinger Low"] = bollinger["BBL_20_2.0"]
                    st.line_chart(data[["Close", "Bollinger High", "Bollinger Low"]])

            # Display the full data with calculated indicators
            st.subheader("Processed Data")
            st.dataframe(data.tail())
        else:
            st.error("No 'Close' column found in data. Unable to calculate indicators.")
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
else:
    st.warning("No data available. Please check the ticker or timeframe.")
