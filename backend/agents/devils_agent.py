"""
Devil's Advocate Agent
"""
from typing import List
from agents.llm_client import llm_client
from models import CleanedItem, RisksOutput, Risk


DEVILS_AGENT_PROMPT = """你是专业的投资否决方。你的唯一任务是从数据中找出这个产品失败的理由。

严格规则：
1. 禁止输出任何正面评价，这不是你的工作
2. 每条风险必须有原始数据支撑，引用具体的帖子内容 + source_url
3. 如果数据中找不到支撑某个风险的证据，不要捏造，直接跳过
4. 重点寻找：
   - 市场规模不足的证据（讨论量很少、关注度低）
   - 竞争已经很激烈的证据（用户已有满意的替代品）
   - 用户付费意愿弱的证据（用户说"免费就用、收费就走"）
   - 目标用户群体太小的证据
   - 用户实际上不认为这是问题的证据
5. 输出格式严格遵循JSON schema

输出格式：
{
    "risks": [
        {
            "risk_type": "市场规模不足/竞争激烈/付费意愿弱/用户群体太小/需求不成立",
            "description": "风险描述",
            "evidence_quote": "证据原文",
            "source_url": "来源链接",
            "severity": "高/中/低"
        }
    ]
}
"""


async def analyze_risks(
    cleaned_data: List[CleanedItem]
) -> RisksOutput:
    """
    分析风险
    
    Args:
        cleaned_data: 清洗后的数据
        
    Returns:
        RisksOutput对象
    """
    if not cleaned_data:
        return RisksOutput(risks=[])
    
    data_text = "\n\n".join([
        f"【{item.platform}】{item.content}\n来源：{item.source_url}"
        for item in cleaned_data[:50]
    ])
    
    prompt = f"""
用户讨论数据：
{data_text}

请找出产品失败的风险并输出JSON格式结果。
"""
    
    result = await llm_client.call_json(prompt, DEVILS_AGENT_PROMPT)
    
    risks = []
    for risk in result.get("risks", []):
        if risk.get("source_url"):
            risks.append(Risk(
                risk_type=risk.get("risk_type", ""),
                description=risk.get("description", ""),
                evidence_quote=risk.get("evidence_quote", ""),
                source_url=risk["source_url"],
                severity=risk.get("severity", "中")
            ))
    
    return RisksOutput(risks=risks)
