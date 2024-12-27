import requests
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
from telegram import Bot
import time

# Set your API key and chat details
ALPHA_API_KEY = "WYVEU8GX06DICZD4"  # Alpha Vantage API Key
API_KEY = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"  # Telegram Bot API Key
CHAT_ID = "6891630125"  # Telegram Chat ID

# Telegram Bot setup
bot = Bot(token=API_KEY)

# Timezone and sessions setup
EST = timezone("US/Eastern")
SESSIONS = {
    "Morning Session 🌤️": {"start": 6, "end": 12},
    "Afternoon Session ☀️": {"start": 12, "end": 18},
    "Night Session 🌙": {"start": 18, "end": 24},
    "Overnight Session 🌑": {"start": 0, "end": 6},
}

# Fetching market data
def fetch_data(symbol, interval, outputsize="compact"):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": interval,
        "apikey": ALPHA_API_KEY,
        "datatype": "json",
        "outputsize": outputsize,
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if "Time Series" not in response.text:
        raise ValueError(f"Error fetching data for {symbol}: {response.text}")

    timeseries_key = list(data.keys())[1]
    df = pd.DataFrame(data[timeseries_key]).T
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

# Generate trading signals
def generate_signals(data):
    data["Close"] = data["Close"].astype(float)
    data["RSI"] = (
        data["Close"].diff().apply(lambda x: max(x, 0)).rolling(window=14).mean()
        / data["Close"].diff().abs().rolling(window=14).mean()
        * 100
    )
    latest = data.iloc[-1]
    rsi = latest["RSI"]

    if rsi > 70:
        return "SELL"
    elif rsi < 30:
        return "BUY"
    else:
        return None

# Send message to Telegram
def send_telegram_message(session, symbol, signal, expiration_times):
    if not signal:
        return
    now = datetime.now(EST).strftime("%A, %B %d, %Y %H:%M %p")
    message = f"""
{session}
🗓 {now}
🇺🇸 {symbol}
🕘 Expiration 5M
⏺ Entry now
🟥 {signal} 🟩

🔽 Martingale levels:
1️⃣ level at {expiration_times[0]}
2️⃣ level at {expiration_times[1]}
"""
    bot.send_message(chat_id=CHAT_ID, text=message)

# Main function to run signals
def main():
    symbols = ["USD/JPY", "EUR/USD", "BTC/USD"]
    interval = "5min"

    while True:
        now = datetime.now(EST)
        for session, times in SESSIONS.items():
            if times["start"] <= now.hour < times["end"]:
                for symbol in symbols:
                    try:
                        data = fetch_data(symbol, interval)
                        signal = generate_signals(data)
                        expiration_times = [
                            (now + timedelta(minutes=5)).strftime("%H:%M"),
                            (now + timedelta(minutes=10)).strftime("%H:%M"),
                        ]
                        send_telegram_message(session, symbol, signal, expiration_times)
                    except Exception as e:
                        bot.send_message(chat_id=CHAT_ID, text=f"Error fetching data for {symbol}: {e}")
                break
        time.sleep(3600)  # Wait for 1 hour before generating signals for the next session

if __name__ == "__main__":
    main()
