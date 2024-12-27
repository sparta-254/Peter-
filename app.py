import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
from telegram import Bot

# Telegram Bot API Setup
TELEGRAM_API_KEY = "7698456329:AAEwPn0U9FiNzA-jqsVOp_KLVqVvQx-BxIE"
TELEGRAM_CHAT_ID = "6891630125"

# Alpha Vantage API Setup
ALPHA_VANTAGE_API_KEY = "WYVEU8GX06DICZD4"

# Signal Configuration
SESSIONS = {
    "Morning": {"start_time": "06:25", "emoji": "🌤️"},
    "Afternoon": {"start_time": "12:25", "emoji": "☀️"},
    "Night": {"start_time": "18:25", "emoji": "🌙"},
    "Overnight": {"start_time": "00:25", "emoji": "🌑"},
}
TICKERS = ["USD", "JPY"]  # Example for USD/JPY
SIGNALS_PER_SESSION = 4
TIME_INTERVAL = "5min"  # Alpha Vantage interval (1min, 5min, etc.)
EXPIRATION = 5  # Expiration time in minutes
UTC_OFFSET = -4  # Adjust for UTC-4 timezone

# Fetch Forex Data
def fetch_forex_data(from_symbol, to_symbol, interval="5min"):
    try:
        url = (
            f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={from_symbol}"
            f"&to_symbol={to_symbol}&interval={interval}&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        response = requests.get(url)
        data = response.json()
        if "Time Series FX (5min)" in data:
            df = pd.DataFrame.from_dict(data["Time Series FX (5min)"], orient="index")
            df.columns = ["Open", "High", "Low", "Close"]
            df = df.astype(float)
            df.index = pd.to_datetime(df.index)
            return df
        else:
            print(f"Error fetching data: {data.get('Error Message', 'Unknown error')}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data for {from_symbol}/{to_symbol}: {e}")
        return pd.DataFrame()

# Generate Signal
def generate_signal(data):
    try:
        data["RSI"] = (
            100
            - (100 / (1 + (data["Close"].pct_change().rolling(14).mean() / data["Close"].pct_change().rolling(14).std())))
        )
        if data["RSI"].iloc[-1] > 70:
            return "SELL"
        elif data["RSI"].iloc[-1] < 30:
            return "BUY"
        return None
    except Exception as e:
        print(f"Error generating signal: {e}")
        return None

# Send Signal to Telegram
def send_telegram_signal(session_name, session_emoji, signal, from_symbol, to_symbol, time_now):
    bot = Bot(token=TELEGRAM_API_KEY)
    expiration_time = time_now + timedelta(minutes=EXPIRATION)
    martingale_times = [
        (time_now + timedelta(minutes=EXPIRATION * i)).strftime("%H:%M") for i in range(1, 3)
    ]
    message = (
        f"{session_emoji} {session_name.upper()} SESSION\n"
        f"🗓 {datetime.now().strftime('%A, %B %d, %Y')}\n"
        f"🇺🇸 {from_symbol}/{to_symbol} 🇯🇵 OTC\n"
        f"🕘 Expiration {EXPIRATION}M\n"
        f"⏺ Entry at {time_now.strftime('%H:%M')}\n"
        f"🟥 {signal} 🟩\n\n"
        f"🔽 Martingale levels\n"
        f"1️⃣ level at {martingale_times[0]}\n"
        f"2️⃣ level at {martingale_times[1]}"
    )
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Main Function
def main():
    # Adjust to UTC-4 timezone
    tz = pytz.timezone("Etc/GMT" + str(UTC_OFFSET))
    now = datetime.now(tz)

    for session_name, session_info in SESSIONS.items():
        session_start = now.replace(hour=int(session_info["start_time"].split(":")[0]), 
                                     minute=int(session_info["start_time"].split(":")[1]), second=0)
        if now >= session_start and (now - session_start).seconds < 3600:  # Check session timing
            print(f"Generating signals for {session_name} Session {session_info['emoji']}...")
            signals_sent = 0

            for _ in range(SIGNALS_PER_SESSION):
                for from_symbol, to_symbol in zip(TICKERS[:-1], TICKERS[1:]):
                    data = fetch_forex_data(from_symbol, to_symbol, interval=TIME_INTERVAL)
                    if data.empty:
                        print(f"No data available for {from_symbol}/{to_symbol}")
                        continue

                    signal = generate_signal(data)
                    if signal:
                        send_telegram_signal(session_name, session_info["emoji"], signal, from_symbol, to_symbol, now)
                        signals_sent += 1
                        time.sleep(60 * EXPIRATION)  # Wait before sending the next signal
                if signals_sent >= SIGNALS_PER_SESSION:
                    break

if __name__ == "__main__":
    main()
