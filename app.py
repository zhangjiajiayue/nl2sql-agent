import streamlit as st

from agent.chain import answer_question
from agent.sql_executor import get_schema
from utils.config import Config
from utils.viz import render_result

st.set_page_config(page_title="自然语言数据分析 Agent", page_icon="📊", layout="wide")

st.title("📊 自然语言数据分析 Agent")
st.caption("用中文提问 → 自动生成 SQL → 查询数据库 → 返回结论与图表")

EXAMPLES = [
    "一共有多少位客户？",
    "销售额最高的前 5 个产品是什么？",
    "各城市的客户数量分布",
    "2024 年每个月的订单总金额趋势",
    "各类别产品的平均价格",
]

with st.sidebar:
    st.header("⚙️ 配置")
    st.write(f"数据库：`{Config.DB_PATH}`")
    st.write(f"模型：`{Config.MODEL}`")
    with st.expander("查看数据库 Schema"):
        st.code(get_schema(Config.DB_PATH), language="sql")
    st.markdown("**示例问题**")
    for e in EXAMPLES:
        if st.button(e, use_container_width=True):
            st.session_state.question = e

if "question" not in st.session_state:
    st.session_state.question = ""

question = st.text_input("请输入你的问题：", value=st.session_state.question)

if st.button("开始分析", type="primary") and question:
    with st.spinner("正在分析中..."):
        try:
            res = answer_question(question, Config.DB_PATH)
            st.markdown("### 💡 分析结论")
            st.write(res["answer"])
            if res.get("retries", 0) > 0:
                st.caption(f"🔁 初次生成的 SQL 执行出错，已自动修正 {res['retries']} 次后成功")
            st.markdown("### 📈 可视化结果")
            render_result(res["df"])
            with st.expander("🔍 生成的 SQL"):
                st.code(res["sql"], language="sql")
            with st.expander("📋 原始数据"):
                st.dataframe(res["df"], use_container_width=True)
        except Exception as e:
            st.error(f"出错了：{e}")