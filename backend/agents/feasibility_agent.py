"""
产品可行性Agent
"""
from typing import List
from agents.llm_client import llm_client
from models import CleanedItem, FeasibilityOutput, Competitor, CompetitorQuote


FEASIBILITY_AGENT_PROMPT = """你是产品可行性分析师。从以下原始数据中，找出用户提到的现有产品/解决方案，并分析这些产品是否真正解决了用户的问题。

规则：
1. 识别数据中出现的竞品名称，每个竞品单独分析
2. 对每个竞品，分别收集"解决了问题"和"没解决问题"的用户原文
3. 重点：挖掘用户对竞品的不满、绕过竞品的替代方法、换用其他产品的原因
4. 每条记录必须有source_url
5. 不要对竞品做主观评价，只呈现用户说了什么
6. 如果数据中无竞品信息，输出"数据中未发现竞品讨论"

输出格式：
{
    "verdict": "市场有空间/已被充分解决/数据不足",
    "competitors": [
        {
            "name": "竞品名称",
            "solved_quotes": [{"quote": "原文", "source_url": "链接"}],
            "unsolved_quotes": [{"quote": "原文", "source_url": "链接"}]
        }
    ]
}
"""


async def analyze_feasibility(
    cleaned_data: List[CleanedItem],
    solution: str,
    known_competitors: List[str]
) -> FeasibilityOutput:
    """
    分析产品可行性
    
    Args:
        cleaned_data: 清洗后的数据
        solution: 解决方案描述
        known_competitors: 已知竞品列表
        
    Returns:
        FeasibilityOutput对象
    """
    if not cleaned_data:
        return FeasibilityOutput(verdict="数据不足", competitors=[])
    
    data_text = "\n\n".join([
        f"【{item.platform}】{item.content}\n来源：{item.source_url}"
        for item in cleaned_data[:50]
    ])
    
    competitors_hint = f"已知竞品：{', '.join(known_competitors)}" if known_competitors else ""
    
    prompt = f"""
解决方案：{solution}
{competitors_hint}

用户讨论数据：
{data_text}

请分析竞品情况并输出JSON格式结果。
"""
    
    result = await llm_client.call_json(prompt, FEASIBILITY_AGENT_PROMPT)
    
    competitors = []
    for comp in result.get("competitors", []):
        solved = [
            CompetitorQuote(quote=q.get("quote", ""), source_url=q["source_url"])
            for q in comp.get("solved_quotes", []) if q.get("source_url")
        ]
        unsolved = [
            CompetitorQuote(quote=q.get("quote", ""), source_url=q["source_url"])
            for q in comp.get("unsolved_quotes", []) if q.get("source_url")
        ]
        
        competitors.append(Competitor(
            name=comp.get("name", ""),
            solved_quotes=solved,
            unsolved_quotes=unsolved
        ))
    
    return FeasibilityOutput(
        verdict=result.get("verdict", "数据不足"),
        competitors=competitors
    )
