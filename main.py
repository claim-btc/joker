import os
import time
import hmac
import base64
import hashlib
import requests
from datetime import datetime, timezone

# 从 GitHub Secrets 获取环境变量
API_KEY = os.environ.get("OKX_API_KEY", "").strip()
SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "").strip()
PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "").strip()
WEBHOOK = os.environ.get("WECHAT_WEBHOOK", "").strip()

# 记录初始本金
INIT_EQUITY_FILE = "init_equity.txt"
LAST_UPDATE_FILE = "last_update.txt"

def get_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def generate_signature(timestamp, method, request_path, body, secret_key):
    message = f"{timestamp}{method}{request_path}{body}"
    mac = hmac.new(secret_key.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def get_equity():
    method = 'GET'
    request_path = '/api/v5/account/balance?ccy=USDT'
    url = 'https://www.okx.com' + request_path
    body = ''
    timestamp = get_timestamp()
    sign = generate_signature(timestamp, method, request_path, body, SECRET_KEY)

    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        try:
            equity = float(data["data"][0]["details"][0]["eq"])
            return equity
        except Exception as e:
            print("解析失败:", e)
            return None
    else:
        print("请求失败:", response.status_code, response.text)
        return None

def send_wechat_msg(content):
    try:
        response = requests.post(WEBHOOK, json={"msgtype": "text", "text": {"content": content}})
        response.raise_for_status()
    except Exception as e:
        print("推送失败:", e)

def read_init_equity():
    if os.path.exists(INIT_EQUITY_FILE):
        with open(INIT_EQUITY_FILE, "r") as f:
            return float(f.read().strip())
    return None

def write_init_equity(equity):
    with open(INIT_EQUITY_FILE, "w") as f:
        f.write(str(equity))

def read_last_update_day():
    if os.path.exists(LAST_UPDATE_FILE):
        with open(LAST_UPDATE_FILE, "r") as f:
            return f.read().strip()
    return None

def write_last_update_day(day_str):
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(day_str)

def main():
    now = datetime.now()
    current_day = now.strftime("%Y-%m-%d")
    hour = now.hour

    equity = get_equity()
    if equity is None:
        send_wechat_msg("⚠️ 未能获取账户权益")
        return

    last_update_day = read_last_update_day()
    if last_update_day != current_day:
        write_init_equity(equity)
        write_last_update_day(current_day)
        send_wechat_msg(f"📊 今日交易开始，初始本金为：{equity:.2f} USDT")
        return

    init_equity = read_init_equity()
    if init_equity is None:
        init_equity = equity
        write_init_equity(equity)
        send_wechat_msg(f"📊 系统首次启动，记录初始本金：{equity:.2f} USDT")
        return

    pnl_rate = (equity - init_equity) / init_equity * 100

    if hour == 0:
        send_wechat_msg(f"🌙 今日交易结束，请好好休息复盘。\n当前本金：{equity:.2f} USDT\n今日盈亏率：{pnl_rate:.2f}%")

    if hour == 6:
        send_wechat_msg("🌞 新的一天开始，好好交易，坚持不懈，加油！")

    if pnl_rate <= -5:
        send_wechat_msg("🚨 警告：日内回撤超过 5%，建议停止交易！")
    elif pnl_rate <= -4:
        send_wechat_msg("⚠️ 注意：日内回撤 4%-5%，请控制风险！")
    elif pnl_rate >= 10:
        send_wechat_msg("🎉 恭喜：盈利超过 10%，请保持冷静，继续稳扎稳打！")

if __name__ == "__main__":
    main()
