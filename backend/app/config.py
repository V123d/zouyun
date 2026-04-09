"""
走云智能排菜系统 — 后端配置管理

使用环境变量或 .env 文件管理敏感配置。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent

LLM_API_URL: str = os.getenv(
    "LLM_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-max")

HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
