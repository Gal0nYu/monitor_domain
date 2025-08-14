import requests
import time
import json
import os
from datetime import datetime

# ================== 配置区（请根据实际情况修改）==================
API_URL = "http://xxxxxxxx.com/api"
FLYBOOK_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxxxxxxx"  # 替换为你的飞书机器人 Webhook
CHECK_INTERVAL = 60  # 检查间隔（秒）
HISTORY_FILE = "domain_history.json"  # 本地记录已处理的域名
# ================================================================

def send_to_feishu(title, content):
    """发送消息到飞书群机器人"""
    headers = {"Content-Type": "application/json"}
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [
                        [
                            {
                                "tag": "text",
                                "text": content
                            }
                        ]
                    ]
                }
            }
        }
    }
    try:
        resp = requests.post(FLYBOOK_WEBHOOK_URL, headers=headers, json=data, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] 飞书发送失败: {resp.text}")
        else:
            print(f"[INFO] 飞书消息发送成功: {title}")
    except Exception as e:
        print(f"[ERROR] 飞书发送异常: {e}")

def load_history():
    """加载历史域名记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(domains):
    """保存域名历史"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(domains, f, ensure_ascii=False, indent=2)

def fetch_domains():
    """获取当前域名列表"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(API_URL, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] 请求失败: {resp.status_code}")
            return None

        # 尝试解析 JSON
        try:
            data = resp.json()
            if isinstance(data, list):
                return data  # 假设返回的是域名列表
            elif isinstance(data, dict) and 'domains' in data:
                return data['domains']
            else:
                print("[ERROR] 返回数据格式不符合预期")
                return None
        except json.JSONDecodeError:
            print("[ERROR] 返回内容不是合法 JSON")
            print("返回内容预览:", resp.text[:200])
            return None

    except Exception as e:
        print(f"[ERROR] 请求异常: {e}")
        return None

def main():
    print("✅ 域名监控脚本已启动...")
    send_to_feishu("域名监控", "域名监控脚本已成功启动，开始监听新域名。")

    # 加载历史记录
    known_domains = set(load_history())
    print(f"[INFO] 已加载 {len(known_domains)} 个历史域名")

    while True:
        try:
            domains = fetch_domains()
            if domains is None:
                time.sleep(CHECK_INTERVAL)
                continue

            new_domains = [d for d in domains if d not in known_domains]
            if new_domains:
                print(f"[NEW] 发现 {len(new_domains)} 个新域名: {new_domains}")
                msg = f"发现 {len(new_domains)} 个新域名：\n" + "\n".join(new_domains)
                send_to_feishu("🚨 发现新域名", msg)
                # 更新历史记录
                known_domains.update(new_domains)
                save_history(list(known_domains))
            else:
                print(f"[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 无新域名")

        except KeyboardInterrupt:
            print("\n[INFO] 脚本已退出")
            break
        except Exception as e:
            print(f"[ERROR] 主循环异常: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
