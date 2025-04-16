import os
import time
import hmac
import base64
import hashlib
import requests
import random
from datetime import datetime, timedelta

# 获取 GitHub Secrets 中的环境变量
API_KEY = os.environ.get("OKX_API_KEY", "").strip()
SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "").strip()
PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "").strip()
WEBHOOK = os.environ.get("WECHAT_WEBHOOK", "").strip()

# 本地文件路径
INIT_EQUITY_FILE = "init_equity.txt"
LAST_RESET_FILE = "last_reset.txt"

# 神的话语
SCRIPTURES = [
    "凡事都有定期，天下万务都有定时。——传道书 3:1",
    "你当刚强壮胆，不要惧怕，也不要惊惶，因为你无论往哪里去，耶和华你的神必与你同在。——约书亚记 1:9",
    "凡劳苦担重担的人可以到我这里来，我就使你们得安息。——马太福音 11:28",
    "我留下平安给你们，我将我的平安赐给你们。——约翰福音 14:27",
    "神是我们的避难所，是我们的力量，是我们在患难中随时的帮助。——诗篇 46:1"
]

def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

def get_timestamp():
    return datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'

def generate_signature(timestamp, method, request_path, body, secret_key):
    message = f"{timestamp}{method}{request_path}{body or ''}"
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
    print(f"接口响应状态码: {response.status_code}")
    print(f"接口响应内容: {response.text}")

    if response.status_code == 200:
        try:
            data = response.json()
            equity = float(data["data"][0]["details"][0]["eq"])
            return equity
        except Exception as e:
            print("解析失败:", e)
            return None
    else:
        print("请求失败:", response.status_code, response.text)
        return None

def get_today_withdrawal_auto():
    method = 'GET'
    request_path = '/api/v5/asset/bills?ccy=USDT&type=withdraw'
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

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("提现记录获取失败", response.status_code, response.text)
            return 0.0

        data = response.json()
        today = get_beijing_time().strftime("%Y-%m-%d")
        total_withdrawal = 0.0

        for record in data.get("data", []):
            ts = int(record["ts"]) / 1000
            date_str = datetime.utcfromtimestamp(ts + 8 * 3600).strftime("%Y-%m-%d")
            if date_str == today:
                amt = float(record.get("amt", "0"))
                total_withdrawal += amt

        print(f"✅ 今天的自动识别提现总额: {total_withdrawal} USDT")
        return total_withdrawal

    except Exception as e:
        print("自动获取提现金额失败:", e)
        return 0.0

def send_wechat_msg(content):
    try:
        print("发送消息内容:", content)
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

def main():
    now = get_beijing_time()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    hour = now.hour
    minute = now.minute

    equity = get_equity()
    if equity is None:
        send_wechat_msg("⚠️ 未能获取账户权益，请检查 API 设置或账户余额是否为 USDT")
        return

    # 设置初始本金（00:00 ~ 00:04）
    last_reset_day = read_file(LAST_RESET_FILE)
    if last_reset_day != today and hour == 0 and minute < 5:
        write_file(INIT_EQUITY_FILE, equity)
        write_file(LAST_RESET_FILE, today)
        send_wechat_msg(f"📊 今日交易开始，初始本金为：{equity:.2f} USDT")
        return

    # 早上激励语（06:00 ~ 06:04）
    if hour == 6 and minute < 5:
        verse = random.choice(SCRIPTURES)
        send_wechat_msg(f"🌞 新的一天开始，好好交易，坚持不懈，加油！\n📖 神的话语：{verse}")
        return

    init_equity = read_file(INIT_EQUITY_FILE)
    if init_equity is None:
        return

    init_equity = float(init_equity)
    withdrawals_today = get_today_withdrawal_auto()
    adjusted_init_equity = init_equity - withdrawals_today
    if adjusted_init_equity <= 0:
        send_wechat_msg("⚠️ 回撤计算失败：调整后的初始本金 ≤ 0，可能是连续大额提现，请检查账户！")
        return

    pnl_rate = (equity - adjusted_init_equity) / adjusted_init_equity * 100

    if pnl_rate <= -5:
        send_wechat_msg("🚨 警告：日内回撤超过 5%，建议停止交易！")
    elif pnl_rate <= -4:
        send_wechat_msg("⚠️ 注意：日内回撤 4%-5%，请控制风险！")
    elif pnl_rate >= 10:
        send_wechat_msg("🎉 恭喜：盈利超过 10%，请保持冷静，继续稳扎稳打！")

if __name__ == "__main__":
    main()
