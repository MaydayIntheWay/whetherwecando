"""
报告数据模型
"""
from typing import Optional
from pydantic import BaseModel, Field
from models.schemas import (
    DemandSignal, Competitor, DifferentiationGap, Risk
)


class DemandOutput(BaseModel):
    """需求可行性输出"""
    score: int = Field(..., ge=0, le=100, description="需求强度分")
    verdict: str = Field(..., description="需求判断")
    signals: list[DemandSignal] = Field(default_factory=list, description="需求信号")


class FeasibilityOutput(BaseModel):
    """产品可行性输出"""
    verdict: str = Field(..., description="可行性判断")
    competitors: list[Competitor] = Field(default_factory=list, description="竞品列表")


class DifferentiationOutput(BaseModel):
    """市场差异性输出"""
    gaps: list[DifferentiationGap] = Field(default_factory=list, description="差异化维度")


class RisksOutput(BaseModel):
    """风险输出"""
    risks: list[Risk] = Field(default_factory=list, description="风险列表")


class ValidationReport(BaseModel):
    """验证报告"""
    task_id: str = Field(..., description="任务ID")
    created_at: str = Field(..., description="创建时间")
    input_summary: dict = Field(..., description="输入摘要")
    verdict: str = Field(..., description="综合结论")
    verdict_reason: str = Field(..., description="结论理由")
    demand: Optional[DemandOutput] = Field(default=None, description="需求分析")
    feasibility: Optional[FeasibilityOutput] = Field(default=None, description="产品分析")
    differentiation: Optional[DifferentiationOutput] = Field(default=None, description="差异化分析")
    risks: Optional[RisksOutput] = Field(default=None, description="风险分析")
    demand_heatmap: Optional[dict] = Field(default=None, description="需求热力图")
    data_stats: Optional[dict] = Field(default=None, description="数据统计")
