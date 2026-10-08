import pandas as pd
import plotly.express as px
import streamlit as st

_TIME_KEYS = ("date", "month", "年", "月", "日", "time", "季度")


def _looks_like_time(series: pd.Series) -> bool:
    name = str(series.name).lower()
    return any(k in name for k in _TIME_KEYS) or pd.api.types.is_datetime64_any_dtype(series)


def render_result(df: pd.DataFrame):
    """根据结果形状自动选择合适的可视化方式"""
    if df is None or df.empty:
        st.info("查询结果为空")
        return

    rows, cols = df.shape

    # 单值 → 指标卡
    if rows == 1 and cols == 1:
        st.metric(label=str(df.columns[0]), value=df.iloc[0, 0])
        return

    # 两列 → 自动柱状 / 折线
    if cols == 2 and rows <= 60:
        x, y = df.columns
        if pd.api.types.is_numeric_dtype(df[y]):
            if _looks_like_time(df[x]):
                st.plotly_chart(px.line(df, x=x, y=y, markers=True),
                                use_container_width=True)
            else:
                st.plotly_chart(px.bar(df, x=x, y=y), use_container_width=True)
            return

    # 默认表格
    st.dataframe(df, use_container_width=True)