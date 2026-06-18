"""
MediaCrawler配置文件生成器
"""
import os
from pathlib import Path
from typing import Optional


class MediaCrawlerConfigGenerator:
    def __init__(self):
        self.config_template = '''
# -*- coding: utf-8 -*-
# MediaCrawler临时配置文件 - 由系统自动生成

# 平台配置
PLATFORM = "{platform}"
XHS_INTERNATIONAL = False

# 关键词配置
KEYWORDS = "{keyword}"

# 登录配置
LOGIN_TYPE = "cookie"
COOKIES = "{cookie}"

# 爬取配置
CRAWLER_TYPE = "search"
CRAWLER_MAX_NOTES_COUNT = {max_count}

# 浏览器配置
HEADLESS = True
ENABLE_CDP_MODE = False
SAVE_LOGIN_STATE = False

# 数据保存配置
SAVE_DATA_OPTION = "jsonl"
SAVE_DATA_PATH = "{output_dir}"

# 代理配置
ENABLE_IP_PROXY = False

# 其他配置
START_PAGE = 1
ENABLE_GET_COMMENTS = False
ENABLE_GET_SUB_COMMENTS = False
CRAWLER_DOWNLOAD_MEDIA = False
'''
    
    def generate_config(
        self,
        platform: str,
        keyword: str,
        cookie: str,
        max_count: int,
        output_dir: str
    ) -> str:
        platform_code = self._get_platform_code(platform)
        
        config_content = self.config_template.format(
            platform=platform_code,
            keyword=keyword,
            cookie=cookie,
            max_count=max_count,
            output_dir=output_dir
        )
        
        config_path = Path(output_dir) / "media_crawler_config.py"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return str(config_path)
    
    def _get_platform_code(self, platform: str) -> str:
        platform_map = {
            'xiaohongshu': 'xhs',
            'xhs': 'xhs',
            'zhihu': 'zhihu'
        }
        
        platform_lower = platform.lower()
        if platform_lower not in platform_map:
            raise ValueError(f"不支持的平台：{platform}，支持的平台：xiaohongshu, zhihu")
        
        return platform_map[platform_lower]
    
    def validate_config(self, config_path: str) -> bool:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_fields = [
                'PLATFORM',
                'KEYWORDS',
                'LOGIN_TYPE',
                'COOKIES',
                'CRAWLER_TYPE',
                'SAVE_DATA_OPTION',
                'SAVE_DATA_PATH'
            ]
            
            for field in required_fields:
                if field not in content:
                    return False
            
            return True
        except Exception:
            return False
    
    def generate_env_config(self, config_path: str) -> dict:
        return {
            'MEDIA_CRAWLER_CONFIG': config_path
        }
    
    def get_output_filename(self, platform: str) -> str:
        platform_code = self._get_platform_code(platform)
        return f"{platform_code}_search.jsonl"


config_generator = MediaCrawlerConfigGenerator()
