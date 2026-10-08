"""一键生成示例数据库：customers / products / orders 三张表"""
import os
import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "sales.db")


def create_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;

    CREATE TABLE customers (
        customer_id   INTEGER PRIMARY KEY,
        name          TEXT NOT NULL,
        city          TEXT NOT NULL,
        register_date TEXT NOT NULL
    );
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name       TEXT NOT NULL,
        category   TEXT NOT NULL,
        price      REAL NOT NULL
    );
    CREATE TABLE orders (
        order_id   INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product_id  INTEGER NOT NULL,
        quantity    INTEGER NOT NULL,
        order_date  TEXT NOT NULL
    );
    """)

    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]
    surnames = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄"]
    givens = ["伟", "芳", "娜", "敏", "静", "磊", "强", "洋"]

    customers = []
    for i in range(1, 201):
        name = random.choice(surnames) + random.choice(givens)
        city = random.choice(cities)
        reg = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))
        customers.append((i, name, city, reg.strftime("%Y-%m-%d")))
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)

    categories = {
        "电子产品": ["智能手机", "笔记本电脑", "平板电脑", "蓝牙耳机", "智能手表"],
        "服饰": ["T恤", "牛仔裤", "羽绒服", "运动鞋", "帽子"],
        "食品": ["坚果礼盒", "咖啡豆", "茶叶", "巧克力", "牛奶"],
        "家居": ["台灯", "靠垫", "收纳箱", "花瓶", "毛毯"],
    }
    products, pid = [], 1
    for cat, items in categories.items():
        for it in items:
            products.append((pid, it, cat, round(random.uniform(20, 8000), 2)))
            pid += 1
    cur.executemany("INSERT INTO products VALUES (?,?,?,?)", products)

    orders = []
    for oid in range(1, 2001):
        od = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))
        orders.append((
            oid, random.randint(1, 200), random.randint(1, len(products)),
            random.randint(1, 5), od.strftime("%Y-%m-%d"),
        ))
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f"✅ 示例数据库已生成：{DB_PATH}")


if __name__ == "__main__":
    create_db()