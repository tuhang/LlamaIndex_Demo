"""
教育RAG系统配置文件
"""
import os
from dotenv import load_dotenv
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # 向后兼容旧版本pydantic
    from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """系统配置类"""
    
    # OpenAI配置
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # 向量数据库配置
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
    
    # MCP服务配置
    mcp_database_url: Optional[str] = os.getenv("MCP_DATABASE_URL")
    mcp_api_key: Optional[str] = os.getenv("MCP_API_KEY")
    
    # Context7配置
    context7_api_key: Optional[str] = os.getenv("CONTEXT7_API_KEY")
    
    # 应用配置
    app_host: str = os.getenv("APP_HOST", "localhost")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # 数据目录
    knowledge_base_dir: str = os.getenv("KNOWLEDGE_BASE_DIR", "./data/knowledge_base")
    student_data_dir: str = os.getenv("STUDENT_DATA_DIR", "./data/student_data")
    
    # RAG系统配置
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-3.5-turbo"
    chunk_size: int = 512
    chunk_overlap: int = 50
    similarity_top_k: int = 5
    
    # 教案生成配置
    max_lesson_plans: int = 3  # 每次最多参考的优秀教案数量
    student_analysis_weight: float = 0.4  # 学情分析权重
    knowledge_base_weight: float = 0.6  # 知识库权重
    
    class Config:
        env_file = ".env"

# 全局配置实例
settings = Settings()

# 确保数据目录存在
os.makedirs(settings.knowledge_base_dir, exist_ok=True)
os.makedirs(settings.student_data_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True)