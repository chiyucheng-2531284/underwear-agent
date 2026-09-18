import streamlit as st
import pandas as pd
import requests
import json

# 设置网页标题和布局
st.set_page_config(page_title="内衣类目双十一作战室", layout="wide")

st.title("👙 抖音电商内衣类目·双十一大促看板")
st.markdown("基于实时数据，AI 智能生成运营洞察与策略建议。")

# 读取数据 (注意路径，因为 app.py 在根目录，所以是 data/products.csv)
df = pd.read_csv("products.csv")
with open("faq.txt", "r", encoding="utf-8") as f:
# ================= 风险监控预警模块 =================
  st.subheader("🚨 双十一价格与库存监控预警")

# 1. 定义风险判断规则
df["是否破价"] = df["活动价"] > df["价格"]  # 活动价高于日常价，属于违规
df["是否断货风险"] = df["库存"] < 1000      # 库存小于1000，属于高风险

# 2. 筛选出有风险的商品
risky_products = df[df["是否破价"] | df["是否断货风险"]]

if not risky_products.empty:
    for index, row in risky_products.iterrows():
        if row["是否破价"]:
            st.error(f"⚠️ **{row['商品名']}** 涉嫌破价！日常价：{row['价格']}，活动价：{row['活动价']}，请立即联系商家修改！")
        if row["是否断货风险"]:
            st.warning(f"📦 **{row['商品名']}** 库存不足（仅剩 {row['库存']} 件），双十一大促可能断货，请提醒商家紧急补货！")
else:
    st.success("✅ 今日所有商品价格和库存正常，无风险。")

st.divider() # 加一条分割线，美观一点
# 用两列布局展示数据
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 爆款商品 TOP3")
    top3 = df.sort_values("销量", ascending=False).head(3)
    st.dataframe(top3[["商品名", "活动价", "销量", "GMV"]], use_container_width=True)

with col2:
    st.subheader("📈 赛道表现")
    category_summary = df.groupby("赛道", observed=True).agg(
        总销量=("销量", "sum"),
        总GMV=("GMV", "sum"),
        平均转化率=("转化率", "mean")
    ).reset_index()
    st.dataframe(category_summary, use_container_width=True)

st.divider()
# ================= 商家服务 Agent (智能问答) =================
st.divider()
st.subheader("💬 商家服务智能客服")
st.markdown("我可以帮你解答关于双十一规则、流量扶持、价格机制的问题。")

# 读取知识库
try:
    with open("data/faq.txt", "r", encoding="utf-8") as f:
        knowledge_base = f.read()
except Exception as e:
    knowledge_base = "暂无规则文档。"

# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 接收用户输入
if prompt := st.chat_input("请输入商家的问题，例如：双十一流量扶持怎么报名？"):
    # 显示用户提问
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成 AI 回答
    with st.chat_message("assistant"):
        with st.spinner("正在查阅平台规则..."):
            # 把知识库内容作为背景塞给大模型
            system_prompt = f"你是一个抖音电商内衣类目的官方运营。请根据以下平台规则文档，准确、专业地回答商家的问题。如果文档中没有答案，请礼貌地告知商家并建议联系人工客服。\n\n【平台规则文档】：\n{knowledge_base}"
            
            # 调用 DeepSeek
            # 替换原来的 DEEPSEEK_API_KEY = "sk-xxx"
            DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"] # 记得换！
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3  # 温度调低，保证回答严谨，不要瞎编
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    answer = response.json()["choices"][0]["message"]["content"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"调用失败，错误码：{response.status_code}")
            except Exception as e:
                st.error(f"网络出错：{e}")
# 生成报告的区域
st.subheader("🤖 AI 运营日报自动生成")

if st.button("🚀 一键生成今日运营日报"):
    with st.spinner("AI 正在读取数据并撰写日报，请稍候..."):
        # 构造 Prompt
        data_prompt = f"""
        今天是2026年10月21日，双十一预热期。以下是内衣类目昨日数据：
        商品明细：{df.to_dict('records')}
        
        请作为一名抖音电商内衣类目运营实习生，帮我写一份简短的运营日报。
        要求：
        1. 提炼核心赛道趋势；
        2. 指出哪些商品是爆款，哪些是潜力品；
        3. 给出2条大促策略优化建议。
        风格要求：专业、简练、结果导向。
        """
        
        # 调用 DeepSeek (换成你自己的 Key)
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
        
        # 这里做了防错处理
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                report = response.json()["choices"][0]["message"]["content"]
                st.success("日报生成成功！")
                st.markdown(report)
            else:
                st.error(f"调用失败，错误码：{response.status_code}。请检查 API Key 和余额。")
        except Exception as e:
            st.error(f"网络请求出错：{e}")
