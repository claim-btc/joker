import os
import requests
import time

API_KEY = os.environ.get("OKX_API_KEY")
SECRET_KEY = os.environ.get("OKX_SECRET_KEY")
PASSPHRASE = os.environ.get("OKX_PASSPHRASE")
WEBHOOK = os.environ.get("WECHAT_WEBHOOK")

def get_equity():
    return 100.0  # 模拟返回值

def send_wechat_msg(content):
    requests.post(WEBHOOK, json={"msgtype": "text", "text": {"content": content}})

def main():
    # 模拟每日检测逻辑
    equity = get_equity()
    # 示例逻辑
    if equity < 95:
        send_wechat_msg("警告：日内回撤超过 5%，停止交易！")
    elif equity < 96:
        send_wechat_msg("注意：日内回撤 4%-5%，小心风险！")
    elif equity > 110:
        send_wechat_msg("提醒：盈利超过 10%，保持冷静！")

if __name__ == "__main__":
    main()
