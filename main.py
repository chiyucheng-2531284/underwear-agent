import pandas as pd
import requests
import json

# ================= 1. 基础数据分析 =================
df = pd.read_csv("products.csv")

# 价格带划分
df["价格带"] = pd.cut(
    df["活动价"],
    bins=[0, 49, 99, 149, 199, 9999],
    labels=["0-49", "50-99", "100-149", "150-199", "200+"]
)

# 生成核心数据摘要
top_products = df.sort_values("销量", ascending=False).head(3).to_dict("records")
category_summary = df.groupby("赛道", observed=True).agg(
    总销量=("销量", "sum"),
    总GMV=("GMV", "sum"),
    平均转化率=("转化率", "mean")
).to_dict("index")

# 将数据转成文字，喂给大模型
data_prompt = f"""
今天是2026年10月21日，双十一预热期。以下是内衣类目昨日数据：
【爆款Top3】：{top_products}
【各赛道表现】：{category_summary}

请作为一名抖音电商内衣类目运营实习生，帮我写一份简短的运营日报。
要求：
1. 提炼核心赛道趋势（保暖内衣、文胸等）；
2. 指出哪些商品是爆款，哪些是潜力品；
3. 给出2条大促策略优化建议。
风格要求：专业、简练、结果导向。
"""

# ================= 2. 调用大模型 =================
# ！！！注意：把下面的 sk-xxxx 替换成你刚才申请到的 API Key！！！
# 替换原来的 DEEPSEEK_API_KEY = "sk-xxx"
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]

url = "https://api.deepseek.com/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
}
payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "你是一个资深的抖音电商内衣类目运营专家。"},
        {"role": "user", "content": data_prompt}
    ],
    "temperature": 0.7
}

print("正在让大模型生成运营日报，请稍等...\n")

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    result = response.json()
    report = result["choices"][0]["message"]["content"]
    print("=" * 50)
    print("📝 今日内衣类目双十一运营日报")
    print("=" * 50)
    print(report)
else:
    print("调用失败，错误码：", response.status_code)
    print(response.text)