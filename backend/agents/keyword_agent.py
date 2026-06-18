"""
关键词提取Agent
"""
from typing import List
from agents.llm_client import llm_client
from models import ProductInput


async def extract_from_idea(raw_idea: str) -> ProductInput:
    """
    从自然语言灵感提取结构化字段
    
    Args:
        raw_idea: 自然语言描述
        
    Returns:
        ProductInput对象
    """
    prompt = f"""
请从以下产品灵感描述中提取信息，输出JSON格式：
{{
    "problem": "用户观察到的痛点",
    "solution": "可能的解决方案",
    "target_user": "目标用户描述",
    "keywords": ["关键词1", "关键词2", ...]
}}

提取规则：
1. keywords提取5-8个中文搜索关键词
2. 若某字段信息不足，输出空字符串
3. 不要捏造信息

用户描述：{raw_idea}
"""
    
    result = await llm_client.call_json(prompt)
    
    return ProductInput(
        problem=result.get("problem", ""),
        solution=result.get("solution", ""),
        target_user=result.get("target_user", ""),
        keywords=result.get("keywords", [])
    )


async def extract_keywords(input_data: ProductInput) -> List[str]:
    """
    从ProductInput提取搜索关键词
    
    Args:
        input_data: 产品输入
        
    Returns:
        关键词列表
    """
    if input_data.keywords:
        return input_data.keywords
    
    prompt = f"""
从以下产品描述中提取5-8个中文搜索关键词，输出JSON数组格式：
["关键词1", "关键词2", ...]

痛点：{input_data.problem}
解法：{input_data.solution}
目标用户：{input_data.target_user}
"""
    
    result = await llm_client.call_json(prompt)
    
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "keywords" in result:
        return result["keywords"]
    
    return []


async def parse_prd(raw_prd: str) -> ProductInput:
    """
    解析PRD文档
    
    Args:
        raw_prd: PRD文本
        
    Returns:
        ProductInput对象
    """
    prompt = f"""
请从以下PRD文档中提取信息，输出JSON格式：
{{
    "problem": "痛点描述",
    "solution": "解决方案",
    "target_user": "目标用户",
    "known_competitors": ["竞品1", "竞品2"]
}}

PRD内容：{raw_prd}
"""
    
    result = await llm_client.call_json(prompt)
    
    return ProductInput(
        problem=result.get("problem", ""),
        solution=result.get("solution", ""),
        target_user=result.get("target_user", ""),
        known_competitors=result.get("known_competitors", [])
    )
