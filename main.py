import os
import requests

API_KEY = os.environ.get("OKX_API_KEY")
SECRET_KEY = os.environ.get("OKX_SECRET_KEY")
PASSPHRASE = os.environ.get("OKX_PASSPHRASE")
WEBHOOK = os.environ.get("WECHAT_WEBHOOK")

def get_equity():
    # 模拟账户权益，测试推送用
    equity = 111  # ❗你可以改成 100 或 111 看不同触发效果
    return equity

def send_wechat_msg(content):
    try:
        response = requests.post(
            WEBHOOK,
            json={"msgtype": "text", "text": {"content": content}},
            timeout=10
        )
        if response.status_code != 200:
            print(f"❌ 发送失败，状态码: {response.status_code}")
            print("返回内容:", response.text)
        else:
            print("✅ 微信消息发送成功")
    except Exception as e:
        print(f"❌ 发送微信消息时出错: {e}")

def main():
    equity = get_equity()
    print(f"📊 当前账户权益: {equity}")

    if equity < 95:
        send_wechat_msg("⚠️ 警告：日内回撤超过 5%，停止交易！")
    elif equity < 96:
        send_wechat_msg("⚠️ 注意：日内回撤 4%-5%，小心风险！")
    elif equity > 110:
        send_wechat_msg("📈 盈利超过 10%，保持冷静，畏惧市场！")
    else:
        print("✅ 当前无异常，无需推送")

if __name__ == "__main__":
    main()
