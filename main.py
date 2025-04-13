import os
import requests
import time
import hmac
import hashlib
import base64
import datetime

# 获取 API 和 Webhook 配置
API_KEY = os.environ.get("OKX_API_KEY")
SECRET_KEY = os.environ.get("OKX_SECRET_KEY")
PASSPHRASE = os.environ.get("OKX_PASSPHRASE")
WEBHOOK = os.environ.get("WECHAT_WEBHOOK")

BASE_URL = "https://www.okx.com"

# 构造 OKX 签名
def generate_okx_headers(method, path, body=""):
    timestamp = datetime.datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    pre_hash = f"{timestamp}{method}{path}{body}"
    signature = base64.b64encode(
        hmac.new(SECRET_KEY.encode(), pre_hash.encode(), hashlib.sha256).digest()
    ).decode()

    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }

# 获取账户权益（U本位合约账户）
def get_equity():
    method = "GET"
    path = "/api/v5/account/account-position-risk"
    url = BASE_URL + path

    headers = generate_okx_headers(method, path)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data["code"] == "0":
            equity = float(data["data"][0]["totalEq"])
            return equity
        else:
            print("❌ 获取权益数据失败:", data["msg"])
    else:
        print("❌ 请求失败:", response.text)

    return None  # 获取失败返回 None

# 发送微信机器人消息
def send_wechat_msg(content):
    if WEBHOOK:
        try:
            res = requests.post(WEBHOOK, json={"msgtype": "text", "text": {"content": content}})
            if res.status_code != 200:
                print("❌ 发送失败:", res.text)
        except Exception as e:
            print("❌ 发送微信消息时出错:", str(e))
    else:
        print("❌ 未设置 WEBHOOK 环境变量")

# 主函数逻辑
def main():
    equity = get_equity()
    if equity is None:
        send_wechat_msg("⚠️ 无法获取账户权益，请检查API设置")
        return

    print(f"📊 当前账户权益: {equity}")
    if equity < 95:
        send_wechat_msg(f"📉 当前权益：{equity} USDT\n警告：日内回撤超过 5%，停止交易！")
    elif equity < 96:
        send_wechat_msg(f"⚠️ 当前权益：{equity} USDT\n注意：日内回撤 4%-5%，小心风险！")
    elif equity > 110:
        send_wechat_msg(f"🚀 当前权益：{equity} USDT\n提醒：盈利超过 10%，保持冷静！")

if __name__ == "__main__":
    main()
