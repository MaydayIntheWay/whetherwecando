"""
需求可行性Agent
"""
from typing import List
from agents.llm_client import llm_client
from models import CleanedItem, DemandOutput, DemandSignal


DEMAND_AGENT_PROMPT = """你是需求验证分析师。从以下来自中文社交平台的原始数据中，判断用户是否存在产品描述中提到的痛点。

规则：
1. 只引用原文片段，禁止推断或补充用户没说过的内容
2. 统计同一痛点被提及的帖子数量（频次越高，需求越真实）
3. 评估情绪强度：用户是随口一提还是强烈抱怨
4. 每条结论必须标注source_url和platform
5. 如果数据中找不到相关痛点，输出"数据不支持"，禁止捏造
6. 输出格式严格遵循JSON schema

输出格式：
{
    "score": 0-100的整数,
    "verdict": "强/弱/无数据支持",
    "signals": [
        {
            "quote": "原文摘录",
            "source_url": "来源链接",
            "platform": "平台",
            "engagement": 互动数,
            "emotion_intensity": "强烈/一般/轻微"
        }
    ]
}
"""


async def analyze_demand(
    cleaned_data: List[CleanedItem],
    problem: str,
    target_user: str
) -> DemandOutput:
    """
    分析需求可行性
    
    Args:
        cleaned_data: 清洗后的数据
        problem: 痛点描述
        target_user: 目标用户
        
    Returns:
        DemandOutput对象
    """
    if not cleaned_data:
        return DemandOutput(score=0, verdict="无数据支持", signals=[])
    
    data_text = "\n\n".join([
        f"【{item.platform}】{item.content}\n来源：{item.source_url}\n互动：{item.engagement}"
        for item in cleaned_data[:50]
    ])
    
    prompt = f"""
产品痛点：{problem}
目标用户：{target_user}

用户讨论数据：
{data_text}

请分析这些数据中是否存在该痛点，并输出JSON格式结果。
"""
    
    result = await llm_client.call_json(prompt, DEMAND_AGENT_PROMPT)
    
    signals = []
    for sig in result.get("signals", []):
        if sig.get("source_url"):
            signals.append(DemandSignal(
                quote=sig.get("quote", ""),
                source_url=sig["source_url"],
                platform=sig.get("platform", "unknown"),
                engagement=sig.get("engagement", 0),
                emotion_intensity=sig.get("emotion_intensity", "一般")
            ))
    
    return DemandOutput(
        score=result.get("score", 0),
        verdict=result.get("verdict", "无数据支持"),
        signals=signals
    )
