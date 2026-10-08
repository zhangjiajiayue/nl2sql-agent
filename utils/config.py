import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_KEY = os.getenv("OPENAI_API_KEY", "")
    BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
    DB_PATH = os.getenv("DB_PATH", "data/sales.db")