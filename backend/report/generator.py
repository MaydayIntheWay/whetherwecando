"""
报告生成模块
"""
from datetime import datetime
from typing import List, Dict, Any
from models import (
    CleanedItem, ValidationReport,
    DemandOutput, FeasibilityOutput,
    DifferentiationOutput, RisksOutput
)
from agents import judge


def generate_report(
    task_id: str,
    input_summary: Dict[str, Any],
    cleaned_data: List[CleanedItem],
    demand: DemandOutput,
    feasibility: FeasibilityOutput,
    differentiation: DifferentiationOutput,
    risks: RisksOutput
) -> ValidationReport:
    """
    生成验证报告
    
    Args:
        task_id: 任务ID
        input_summary: 输入摘要
        cleaned_data: 清洗后的数据
        demand: 需求分析结果
        feasibility: 产品可行性结果
        differentiation: 差异化分析结果
        risks: 风险分析结果
        
    Returns:
        ValidationReport对象
    """
    verdict, verdict_reason = judge(demand, feasibility, differentiation, risks)
    
    demand_heatmap = _generate_heatmap(cleaned_data)
    data_stats = _generate_stats(cleaned_data)
    
    return ValidationReport(
        task_id=task_id,
        created_at=datetime.now().isoformat(),
        input_summary=input_summary,
        verdict=verdict,
        verdict_reason=verdict_reason,
        demand=demand,
        feasibility=feasibility,
        differentiation=differentiation,
        risks=risks,
        demand_heatmap=demand_heatmap,
        data_stats=data_stats
    )


def _generate_heatmap(items: List[CleanedItem]) -> Dict[str, int]:
    """生成需求热力图"""
    heatmap: Dict[str, int] = {}
    for item in items:
        heatmap[item.platform] = heatmap.get(item.platform, 0) + 1
    return heatmap


def _generate_stats(items: List[CleanedItem]) -> Dict[str, Any]:
    """生成数据统计"""
    platforms = list(set(item.platform for item in items))
    
    return {
        "total_posts_crawled": len(items),
        "platforms": platforms,
        "crawled_at": datetime.now().isoformat()
    }
