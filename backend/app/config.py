"""
走云智能排菜系统 — 后端配置管理

使用环境变量或 .env 文件管理敏感配置。
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（位于 backend/ 目录下）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 项目根路径
BASE_DIR = Path(__file__).resolve().parent.parent

# === 大模型 API 配置 ===
LLM_API_URL: str = os.getenv(
    "LLM_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-max")

# === 数据路径 ===
DISH_LIBRARY_PATH: Path = BASE_DIR / "app" / "data" / "dish_library.json"

# === 服务配置 ===
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
