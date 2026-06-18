"""
裁判节点 - 汇总四个Agent输出，生成最终结论
"""
from models import (
    DemandOutput, FeasibilityOutput, 
    DifferentiationOutput, RisksOutput
)


def judge(
    demand: DemandOutput,
    feasibility: FeasibilityOutput,
    differentiation: DifferentiationOutput,
    risks: RisksOutput
) -> tuple[str, str]:
    """
    裁判节点判断逻辑
    
    Args:
        demand: 需求分析结果
        feasibility: 产品可行性结果
        differentiation: 差异化分析结果
        risks: 风险分析结果
        
    Returns:
        (verdict, reason) - 结论和理由
    """
    high_risks = [r for r in risks.risks if r.severity == "高"]
    
    if demand.verdict == "无数据支持":
        return "Stop", "数据中未发现相关需求讨论，无法验证需求真实性。"
    
    if len(high_risks) >= 3:
        return "Stop", f"发现{len(high_risks)}个高风险因素，包括：{high_risks[0].risk_type}。建议放弃该方向。"
    
    if demand.score >= 60 and feasibility.verdict == "市场有空间":
        gap_count = len(differentiation.gaps)
        risk_count = len(risks.risks)
        return "Go", f"需求强度{demand.score}分，市场存在空间。发现{gap_count}个差异化维度和{risk_count}个风险点。建议推进并关注风险。"
    
    if demand.score >= 40 and feasibility.verdict != "已被充分解决":
        return "Pivot", f"需求强度{demand.score}分，但市场格局需调整。建议优化方向后重新验证。"
    
    if feasibility.verdict == "已被充分解决":
        return "Stop", "市场已被充分解决，用户对现有产品满意度较高。"
    
    return "Pivot", "需求和市场情况不明确，建议调整方向后重新验证。"
