# main.py
import requests
import hmac
import hashlib
import base64
import datetime
import time
import json
import urllib.parse
import os

def get_timestamp():
    return datetime.datetime.utcnow().isoformat("T", "seconds") + "Z"

def sign(message, secret_key):
    return base64.b64encode(hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()).decode()

def get_headers(api_key, secret_key, passphrase, method, request_path, body=""):
    timestamp = get_timestamp()
    message = timestamp + method + request_path + body
    signature = sign(message, secret_key)
    return {
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }

def get_account_balance(api_key, secret_key, passphrase):
    url = "https://www.okx.com/api/v5/account/balance"
    headers = get_headers(api_key, secret_key, passphrase, "GET", "/api/v5/account/balance")
    response = requests.get(url, headers=headers)
    return response.json()

def send_wechat_message(webhook_url, content):
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    return response.json()

def load_reference():
    if not os.path.exists("ref_equity.json"):
        return None
    with open("ref_equity.json", "r") as f:
        return json.load(f)

def save_reference(equity, date_str):
    with open("ref_equity.json", "w") as f:
        json.dump({"date": date_str, "equity": equity}, f)

def main():
    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_SECRET_KEY")
    passphrase = os.getenv("OKX_PASSPHRASE")
    webhook_url = os.getenv("WECHAT_WEBHOOK")

    balance_data = get_account_balance(api_key, secret_key, passphrase)
    equity = float(balance_data['data'][0]['details'][0]['eq'])

    today = datetime.date.today().isoformat()
    ref = load_reference()

    if ref is None or ref['date'] != today:
        save_reference(equity, today)
        print("Initialized reference equity.")
        return

    ref_equity = float(ref['equity'])
    change = (equity - ref_equity) / ref_equity * 100

    message = None

    if change <= -5:
        message = f"⚡⚡⚡ 当前权益: {equity:.2f} USDT\n较今日初始回撤: {change:.2f}%\n>>> 已触及日内最大亏损 5%\n>>> 请立即停止交易！"
    elif -5 < change <= -4:
        message = f"⚠ 当前权益: {equity:.2f} USDT\n较今日初始回撤: {change:.2f}%\n>>> 回撤接近5%！猴哥注意风险，不要上头！"
    elif change >= 10:
        message = f"✨ 当前权益: {equity:.2f} USDT\n较今日初始增长: {change:.2f}%\n>>> 已盈利超 10%！谨慎！下一笔注意风险，不要自大！"

    if message:
        send_wechat_message(webhook_url, message)
    else:
        print(f"当前权益: {equity:.2f} USDT, 今日变化: {change:.2f}%，无推送。")

if __name__ == "__main__":
    main()
