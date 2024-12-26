import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import requests

# Telegram Bot Configuration
BOT_TOKEN = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
CHAT_ID = "6891630125"

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

        # Debug: Show raw data
        if data.empty:
            st.error("Data fetched is empty. Please check the ticker or timeframe.")
            return None

        # Flatten multi-index columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() for col in data.columns]

        # Rename columns dynamically
        column_mapping = {f"{col}_{ticker}": col for col in ["Close", "High", "Low", "Open", "Volume"]}
        data = data.rename(columns=column_mapping)

        # Ensure the required columns exist
        required_columns = ["Close", "High", "Low", "Open", "Volume"]
        for col in required_columns:
            if col not in data.columns:
                st.error(f"'{col}' column not found in the data after renaming. Data columns are: {data.columns}")
                return None

        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Send Signal to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.write("Signal sent to Telegram!")
        else:
            st.error(f"Failed to send signal. Error: {response.text}")
    except Exception as e:
        st.error(f"Error sending message to Telegram: {e}")

# Fetch the data
data = fetch_data(ticker, period, timeframe)

if data is not None:
    st.write("Raw Data Sample:")
    st.dataframe(data.tail())

    # Calculate Indicators and Generate Signals
    try:
        if "Close" in data.columns:
            # Calculate selected indicator
            signal = None
            if indicator == "SMA":
                data["SMA"] = ta.sma(data["Close"], length=14)
                st.line_chart(data[["Close", "SMA"]])
                if data["Close"].iloc[-1] > data["SMA"].iloc[-1]:
                    signal = f"BUY signal for {ticker} - Current Price: {data['Close'].iloc[-1]}"
                elif data["Close"].iloc[-1] < data["SMA"].iloc[-1]:
                    signal = f"SELL signal for {ticker} - Current Price: {data['Close'].iloc[-1]}"
            elif indicator == "EMA":
                data["EMA"] = ta.ema(data["Close"], length=14)
                st.line_chart(data[["Close", "EMA"]])
                if data["Close"].iloc[-1] > data["EMA"].iloc[-1]:
                    signal = f"BUY signal for {ticker} - Current Price: {data['Close'].iloc[-1]}"
                elif data["Close"].iloc[-1] < data["EMA"].iloc[-1]:
                    signal = f"SELL signal for {ticker} - Current Price: {data['Close'].iloc[-1]}"
            elif indicator == "RSI":
                data["RSI"] = ta.rsi(data["Close"], length=14)
                st.line_chart(data[["RSI"]])
                if data["RSI"].iloc[-1] > 70:
                    signal = f"SELL signal for {ticker} - RSI: {data['RSI'].iloc[-1]}"
                elif data["RSI"].iloc[-1] < 30:
                    signal = f"BUY signal for {ticker} - RSI: {data['RSI'].iloc[-1]}"
            elif indicator == "MACD":
                macd = ta.macd(data["Close"], fast=12, slow=26, signal=9)
                if macd is not None:
                    data["MACD"] = macd["MACD_12_26_9"]
                    data["Signal"] = macd["MACDs_12_26_9"]
                    st.line_chart(data[["MACD", "Signal"]])
                    if data["MACD"].iloc[-1] > data["Signal"].iloc[-1]:
                        signal = f"BUY signal for {ticker} - MACD: {data['MACD'].iloc[-1]}"
                    elif data["MACD"].iloc[-1] < data["Signal"].iloc[-1]:
                        signal = f"SELL signal for {ticker} - MACD: {data['MACD'].iloc[-1]}"
            elif indicator == "Bollinger Bands":
                bollinger = ta.bbands(data["Close"], length=20, std=2.0)
                if bollinger is not None:
                    data["Bollinger High"] = bollinger["BBU_20_2.0"]
                    data["Bollinger Low"] = bollinger["BBL_20_2.0"]
                    st.line_chart(data[["Close", "Bollinger High", "Bollinger Low"]])
                    if data["Close"].iloc[-1] > data["Bollinger High"].iloc[-1]:
                        signal = f"SELL signal for {ticker} - Current Price: {data['Close'].iloc[-1]}"
                    elif data["Close"].iloc[-1] < data["Bollinger Low"].iloc[-1]:
                        signal = f"BUY signal for {ticker} - Current Price: {data['Close'].iloc[-1]}"

            # Send signal to Telegram
            if signal:
                send_telegram_message(signal)
            else:
                st.info("No trading signal generated at this time.")
        else:
            st.error("No 'Close' column found in the data. Unable to calculate indicators.")
    except Exception as e:
        st.error(f"Error calculating indicators: {e}")
else:
    st.warning("No data available. Please check the ticker or timeframe.")
