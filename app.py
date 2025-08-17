import os
import requests
import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# Environment variables from GitHub Secrets / Render
CMC_KEY = os.getenv("COINMARKETCAP_API_KEY")
TAAPI_KEY = os.getenv("TAAPI_API_KEY")
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY")
COINMARKETCAL_KEY = os.getenv("COINMARKETCAL_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

current_signals = []

def get_cryptos():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
    params = {"limit": 200, "convert": "USD"}
    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        coins = r.json().get("data", [])
    except Exception as e:
        print(f"CMC API error: {e}")
        return []
    filtered = [
        c for c in coins
        if 0.001 <= c["quote"]["USD"]["price"] <= 100
        and 1e7 <= c["quote"]["USD"]["market_cap"] <= 5e9
        and c["quote"]["USD"]["volume_24h"] > 1e7
        and 0.02 <= c["quote"]["USD"]["percent_change_24h"] <= 0.20
    ]
    return filtered

def get_ta(ticker):
    url = "https://api.taapi.io/rsi"
    params = {
        "secret": TAAPI_KEY,
        "exchange": "binance",
        "symbol": f"{ticker}/USDT",
        "interval": "1h"
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        return {"rsi": r.json().get("value")}
    except Exception as e:
        print(f"TAAPI error for {ticker}: {e}")
        return None

def get_reddit_sentiment(ticker):
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": "crypto-scanner-app/0.1"}
    try:
        r = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers)
        r.raise_for_status()
        token = r.json().get("access_token")
        if not token:
            return {"mentions": 0, "engagement": 0, "sentiment": 0}
        headers["Authorization"] = f"bearer {token}"
        url = f"https://oauth.reddit.com/search?q={ticker}&limit=100"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        posts = resp.json().get("data", {}).get("children", [])
        mentions = len(posts)
        upvotes = sum(p["data"].get("score", 0) for p in posts)
        sentiment = round(upvotes / (mentions or 1) / 100, 2) if mentions else 0
        return {"mentions": mentions, "engagement": upvotes, "sentiment": sentiment}
    except Exception as e:
        print(f"Reddit API error: {e}")
        return {"mentions": 0, "engagement": 0, "sentiment": 0}

def get_catalyst(ticker):
    headers = {"x-api-key": COINMARKETCAL_KEY}
    url = f"https://developers.coinmarketcal.com/v1/events?coins={ticker}"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        events = r.json().get("body", [])
        if events:
            event = events[0]
            return {"event": event.get("title", ""), "link": event.get("source", "")}
    except Exception as e:
        print(f"CoinMarketCal error: {e}")
    return {}

def ai_score(price_momentum, volume_spike, sentiment, technicals, catalyst):
    score = (
        0.25 * price_momentum +
        0.20 * volume_spike +
        0.20 * sentiment +
        0.25 * technicals +
        0.10 * catalyst
    )
    return round(score, 2)

def send_telegram_alert(signal):
    msg = f"""🚨 Signal Alert: {signal['ticker']}
Score: {signal['ai_score']}/100
Validation: {signal['validation']}

📊 Technicals
Price: ${signal['price']:.2f}
RSI: {signal['technicals']['rsi']}

🎯 Risk Management
Entry: ${signal['risk_management']['entry']:.2f}
TP: ${signal['risk_management']['tp']:.2f}
SL: ${signal['risk_management']['sl']:.2f}
R/R: {signal['risk_management']['risk_reward_ratio']}

🗣 Sentiment
Mentions: {signal['sentiment']['mentions']}
Engagement: {signal['sentiment']['engagement']}
Sentiment Score: {signal['sentiment']['sentiment']}

🔗 Links
📈 [Chart]({signal['links']['chart']})
📰 [News]({signal['links']['news']})
📅 [Catalyst]({signal['links']['catalyst']})

⏰ Time: {signal['timestamp']}
"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=data)
        if not resp.ok:
            print(f"Telegram send error: {resp.text}")
    except Exception as e:
        print(f"Telegram exception: {e}")

def scan():
    global current_signals
    candidates = get_cryptos()
    signals = []
    for coin in candidates:
        symbol = coin["symbol"]
        price = coin["quote"]["USD"]["price"]
        change = coin["quote"]["USD"]["percent_change_24h"]
        volume = coin["quote"]["USD"]["volume_24h"]
        ta = get_ta(symbol)
        if not ta or not ta.get("rsi"):
            continue
        reddit = get_reddit_sentiment(symbol)
        catalyst = get_catalyst(symbol)
        if (
            50 <= ta["rsi"] <= 70
            and reddit["mentions"] >= 10
            and reddit["engagement"] >= 100
            and reddit["sentiment"] >= 0.6
        ):
            score = ai_score(
                change * 100,
                volume / 1e7,
                reddit["sentiment"],
                ta["rsi"] / 100,
                1 if catalyst else 0
            )
            validation = f"RSI {ta['rsi']} + Volume spike + Reddit buzz → Setup"
            risk_entry = price
            risk_tp = price * 1.05
            risk_sl = price * 0.97
            rr_ratio = round((risk_tp - price) / (price - risk_sl), 2)
            signal = {
                "ticker": symbol,
                "price": price,
                "ai_score": score,
                "validation": validation,
                "technicals": ta,
                "risk_management": {
                    "entry": risk_entry,
                    "tp": risk_tp,
                    "sl": risk_sl,
                    "risk_reward_ratio": rr_ratio
                },
                "sentiment": reddit,
                "catalyst": catalyst,
                "links": {
                    "chart": f"https://www.tradingview.com/symbols/{symbol}USD/",
                    "news": f"https://cryptopanic.com/news/{symbol}",
                    "catalyst": catalyst.get("link", "")
                },
                "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            }
            signals.append(signal)
            send_telegram_alert(signal)
    current_signals = signals
    return signals

@app.route("/signals", methods=["GET"])
def get_signals():
    return jsonify(current_signals)

@app.route("/scan", methods=["POST"])
def manual_scan():
    signals = scan()
    return jsonify({"message": f"Scan complete. {len(signals)} signals found.", "signals": signals})

@app.route("/")
def home():
    return "Crypto Scanner API Running"

if __name__ == "__main__":
    scan()  # run scan on app start
    app.run(host="0.0.0.0", port=8000)
