"""
配置管理 - 类似 Java 的 application.yml
从 .env 文件读取配置
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    """项目配置（类似 Java 的 @ConfigurationProperties）"""

    # LLM 配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # Embedding 配置
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "")

    # 向量数据库
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

    # 知识库目录
    KNOWLEDGE_DIR: str = os.getenv("KNOWLEDGE_DIR", "./data/knowledge")


settings = Settings()
