import os
import time
import hmac
import base64
import hashlib
import requests
from datetime import datetime, timezone
import random

# 从 GitHub Secrets 获取环境变量
API_KEY = os.environ.get("OKX_API_KEY", "").strip()
SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "").strip()
PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "").strip()
WEBHOOK = os.environ.get("WECHAT_WEBHOOK", "").strip()

# 文件路径
INIT_EQUITY_FILE = "init_equity.txt"
LAST_RESET_FILE = "last_reset.txt"

# 神的话语列表
bible_verses = [
    "耶和华是我的牧者，我必不致缺乏。 — 诗篇 23:1",
    "你们要靠主常常喜乐，我再说你们要喜乐。 — 腓立比书 4:4",
    "我靠着那加给我力量的，凡事都能做。 — 腓立比书 4:13",
    "耶和华必为你争战，你们只管静默，不要作声。 — 出埃及记 14:14",
    "神是我们的避难所和力量，是我们随时的帮助。 — 诗篇 46:1",
    "我知道我所信的是谁，也深信他能保守我所交付的，直到那日。 — 提摩太后书 1:12",
    "凡劳苦担重担的人，可以到我这里来，我就使你们得安息。 — 马太福音 11:28"
]

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


def read_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return f.read().strip()
    return None


def write_file(filepath, content):
    with open(filepath, "w") as f:
        f.write(str(content))


def send_random_bible_verse():
    verse = random.choice(bible_verses)
    send_wechat_msg(f"🌞 新的一天开始，好好交易，坚持不懈，加油！\n今天的神的话语是：\n{verse}")


def main():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    hour = now.hour

    equity = get_equity()
    if equity is None:
        send_wechat_msg("⚠️ 未能获取账户权益")
        return

    # 每天0点重置初始本金
    last_reset_day = read_file(LAST_RESET_FILE)
    if last_reset_day != today and hour == 0:
        write_file(INIT_EQUITY_FILE, equity)
        write_file(LAST_RESET_FILE, today)
        send_wechat_msg(f"📊 今日交易开始，初始本金为：{equity:.2f} USDT")
        return

    # 每天早上6点激励消息
    if hour == 6 and current_time.startswith("06:00"):
        send_random_bible_verse()
        return

    # 读取初始本金
    init_equity = read_file(INIT_EQUITY_FILE)
    if init_equity is None:
        return  # 等到 0 点再设置初始本金

    init_equity = float(init_equity)
    pnl_rate = (equity - init_equity) / init_equity * 100

    # 风控提醒
    if pnl_rate <= -5:
        send_wechat_msg("🚨 警告：猴哥你的日内回撤超过 5%，钟向阳命令你停止交易！")
    elif pnl_rate <= -4:
        send_wechat_msg("⚠️ 注意：日内回撤 4%-5%，请控制风险！")
    elif pnl_rate >= 10:
        send_wechat_msg("🎉 恭喜：猴哥盈利超过 10%，请保持冷静，继续稳扎稳打！")


if __name__ == "__main__":
    main()
