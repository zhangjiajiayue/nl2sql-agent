from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils.config import Config
from agent.prompts import SQL_SYSTEM_PROMPT, ANSWER_SYSTEM_PROMPT
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


def answer_question(question: str, db_path: str) -> dict:
    """核心流程：问题 → SQL → 查询 → 结论"""
    schema = get_schema(db_path)
    sql_chain, answer_chain = _build_chains()

    raw_sql = sql_chain.invoke({"schema": schema, "question": question})
    sql = clean_sql(raw_sql)
    df = run_sql(db_path, sql)

    preview = "(空结果)" if df.empty else df.head(50).to_markdown(index=False)
    answer = answer_chain.invoke({
        "question": question, "sql": sql, "result": preview,
    })

    return {"sql": sql, "df": df, "answer": answer}