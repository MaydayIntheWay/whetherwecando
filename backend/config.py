"""
配置管理模块
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置(从环境变量加载)"""
    
    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    
    # 数据库
    database_url: str = "postgresql://postgres:postgres@localhost:5432/whetherwecando"
    
    # MediaCrawler
    cookie_path: str = "./cache/cookies"
    cache_path: str = "./cache"
    crawler_encryption_key: str = ""
    
    # 服务
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 日志
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()


def ensure_cache_dirs():
    """确保缓存目录存在"""
    Path(settings.cookie_path).mkdir(parents=True, exist_ok=True)
    Path(settings.cache_path).mkdir(parents=True, exist_ok=True)
