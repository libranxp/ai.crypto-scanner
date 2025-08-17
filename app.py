import os
import requests
import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# Read all API keys and tokens from environment variables (set in GitHub Secrets or your server env)
CMC_KEY = os.getenv("COINMARKETCAP_API_KEY")
TAAPI_KEY = os.getenv("TAAPI_API_KEY")
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY")
COINMARKETCAL_KEY = os.getenv("COINMARKETCAL_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

current_signals = []

# Your full scanner functions here: get_cryptos, get_ta, get_reddit_sentiment, get_catalyst, ai_score, send_telegram_alert, scan (use previous detailed code)

# (Due to length, reuse the full implementation sent previously for these functions)

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
    scan()  # optional initial scan on startup
    app.run(host="0.0.0.0", port=8000)
