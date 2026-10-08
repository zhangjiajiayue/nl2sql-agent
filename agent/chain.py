import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.config import Config
from agent.prompts import (
    SQL_SYSTEM_PROMPT,
    ANSWER_SYSTEM_PROMPT,
    FIX_SQL_SYSTEM_PROMPT,
)
from agent.sql_executor import clean_sql, run_sql, get_schema


def _llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=Config.MODEL,
        api_key=Config.API_KEY,
        base_url=Config.BASE_URL,
        temperature=temperature,
    )


def _build_chains():
    llm = _llm()

    sql_prompt = ChatPromptTemplate.from_messages([
        ("system", SQL_SYSTEM_PROMPT),
        ("human", "数据库 Schema：\n{schema}\n\n用户问题：{question}\n\n请输出 SQL："),
    ])
    sql_chain = sql_prompt | llm | StrOutputParser()

    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", ANSWER_SYSTEM_PROMPT),
        ("human",
         "用户问题：{question}\n\nSQL：{sql}\n\n"
         "查询结果（前 50 行）：\n{result}\n\n请用中文给出分析结论："),
    ])
    answer_chain = answer_prompt | llm | StrOutputParser()

    return sql_chain, answer_chain


def _build_fix_chain():
    """根据报错信息修正 SQL 的链路"""
    fix_prompt = ChatPromptTemplate.from_messages([
        ("system", FIX_SQL_SYSTEM_PROMPT),
        ("human",
         "数据库 Schema：\n{schema}\n\n"
         "用户问题：{question}\n\n"
         "出错的 SQL：\n{sql}\n\n"
         "错误信息：\n{error}\n\n请输出修正后的 SQL："),
    ])
    return fix_prompt | _llm() | StrOutputParser()


def answer_question(question: str, db_path: str, max_retries: int = 2) -> dict:
    """核心流程：问题 → SQL → 执行（失败则自动修正重试）→ 结论"""
    schema = get_schema(db_path)
    sql_chain, answer_chain = _build_chains()
    fix_chain = _build_fix_chain()

    # 第一次生成 SQL
    sql = clean_sql(sql_chain.invoke({"schema": schema, "question": question}))

    df = None
    last_error = None
    retries = 0

    # 执行，失败则让 LLM 修正后重试
    for attempt in range(max_retries + 1):
        try:
            df = run_sql(db_path, sql)
            retries = attempt
            break
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                fixed_raw = fix_chain.invoke({
                    "schema": schema,
                    "question": question,
                    "sql": sql,
                    "error": last_error,
                })
                sql = clean_sql(fixed_raw)

    # 重试完仍然失败
    if df is None:
        return {
            "sql": sql,
            "df": pd.DataFrame(),
            "answer": f"抱歉，SQL 执行多次仍然失败：{last_error}",
            "retries": max_retries,
        }

    preview = "(空结果)" if df.empty else df.head(50).to_markdown(index=False)
    answer = answer_chain.invoke({
        "question": question, "sql": sql, "result": preview,
    })

    return {"sql": sql, "df": df, "answer": answer, "retries": retries}