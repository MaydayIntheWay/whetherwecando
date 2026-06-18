"""
市场差异性Agent
"""
from typing import List
from agents.llm_client import llm_client
from models import CleanedItem, DifferentiationOutput, DifferentiationGap, CompetitorQuote


DIFFERENTIATION_AGENT_PROMPT = """你是市场差异化分析师。从以下竞品用户评价数据中，聚类找出用户对现有产品反复抱怨的维度。

规则：
1. 只从数据中提取，禁止给出"你应该这样差异化"的建议
2. 输出的是"现有产品在XX维度上用户反馈最差"的事实陈述
3. 按抱怨频次从高到低排序
4. 每个维度附上2-3条代表性原文引用，附source_url
5. 维度示例：价格、功能完整性、易用性、客服响应、中文支持、数据准确性等
6. 不超过5个差异化维度，聚焦最显著的

输出格式：
{
    "gaps": [
        {
            "dimension": "维度名称",
            "complaint_count": 抱怨频次,
            "representative_quotes": [{"quote": "原文", "source_url": "链接"}]
        }
    ]
}
"""


async def analyze_differentiation(
    cleaned_data: List[CleanedItem]
) -> DifferentiationOutput:
    """
    分析市场差异性
    
    Args:
        cleaned_data: 清洗后的数据
        
    Returns:
        DifferentiationOutput对象
    """
    if not cleaned_data:
        return DifferentiationOutput(gaps=[])
    
    data_text = "\n\n".join([
        f"【{item.platform}】{item.content}\n来源：{item.source_url}"
        for item in cleaned_data[:50]
    ])
    
    prompt = f"""
用户讨论数据：
{data_text}

请分析用户抱怨维度并输出JSON格式结果。
"""
    
    result = await llm_client.call_json(prompt, DIFFERENTIATION_AGENT_PROMPT)
    
    gaps = []
    for gap in result.get("gaps", [])[:5]:
        quotes = [
            CompetitorQuote(quote=q.get("quote", ""), source_url=q["source_url"])
            for q in gap.get("representative_quotes", []) if q.get("source_url")
        ]
        
        gaps.append(DifferentiationGap(
            dimension=gap.get("dimension", ""),
            complaint_count=gap.get("complaint_count", 0),
            representative_quotes=quotes
        ))
    
    return DifferentiationOutput(gaps=gaps)
