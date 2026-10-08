import re
import sqlite3
import pandas as pd

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|"
    r"ATTACH|DETACH|PRAGMA|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def clean_sql(text: str) -> str:
    """从 LLM 输出中提取纯 SQL 语句"""
    text = (text or "").strip()
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1)
    return text.strip().rstrip(";").strip()


def validate_sql(sql: str) -> bool:
    """安全校验：只允许单条只读查询"""
    if not sql:
        raise ValueError("SQL 为空")
    if ";" in sql:
        raise ValueError("禁止多语句执行")
    if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError("只允许 SELECT / WITH 查询")
    if _FORBIDDEN.search(sql):
        raise ValueError("检测到危险关键字，已拦截")
    return True


def run_sql(db_path: str, sql: str) -> pd.DataFrame:
    validate_sql(sql)
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def get_schema(db_path: str, sample_rows: int = 3) -> str:
    """读取数据库结构 + 少量示例数据，用于喂给 LLM"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = [r[0] for r in cur.fetchall()]
    parts = []
    for t in tables:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = cur.fetchall()
        col_defs = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        parts.append(f"表 {t} ({col_defs})")
        cur.execute(f"SELECT * FROM '{t}' LIMIT {sample_rows}")
        rows = cur.fetchall()
        if rows:
            parts.append(f"  示例数据：{rows}")
    conn.close()
    return "\n".join(parts)