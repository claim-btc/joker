import os
import requests
import time

API_KEY = os.environ.get("OKX_API_KEY", "").strip()
SECRET_KEY = os.environ.get("OKX_SECRET_KEY", "").strip()
PASSPHRASE = os.environ.get("OKX_PASSPHRASE", "").strip()
WEBHOOK = os.environ.get("WECHAT_WEBHOOK", "").strip()

def get_equity():
    url = "https://www.okx.com/api/v5/account/balance"  # 实际的OKX API URL
    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": SECRET_KEY,  # 如果需要签名，请按照API文档进行签名
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }

    # 发起请求并检查响应
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败，会抛出异常
        data = response.json()
        print("响应数据:", data)  # 打印返回的数据，查看其结构
        
        # 检查 'data' 键并提取余额
        if "data" in data and len(data["data"]) > 0:
            # 请根据返回数据的实际结构修改 'totalEq' 为正确的键名
            equity = float(data["data"][0].get("totalEq", 0))  # 如果找不到 totalEq，则默认返回 0
            return equity
        else:
            print("未能获取数据：'data' 键不存在或为空")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{e}")
        return None

def send_wechat_msg(content):
    try:
        response = requests.post(WEBHOOK, json={"msgtype": "text", "text": {"content": content}})
        response.raise_for_status()  # 如果请求失败，会抛出异常
    except requests.exceptions.RequestException as e:
        print(f"发送微信消息失败：{e}")

def main():
    # 模拟每日检测逻辑
    equity = get_equity()
    if equity is None:
        print("未能获取账户权益")
        return
    
    print(f"当前账户权益：{equity}")
    
    # 示例逻辑
    if equity < 95:
        send_wechat_msg("警告：日内回撤超过 5%，停止交易！")
    elif equity < 96:
        send_wechat_msg("注意：日内回撤 4%-5%，小心风险！")
    elif equity > 110:
        send_wechat_msg("提醒：盈利超过 10%，保持冷静！")

if __name__ == "__main__":
    main()
