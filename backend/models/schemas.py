"""
Pydantic数据模型定义
"""
from typing import Optional
from pydantic import BaseModel, Field


class ProductInput(BaseModel):
    """产品输入表单"""
    problem: str = Field(default="", description="用户观察到的痛点")
    solution: str = Field(default="", description="解决方案描述")
    target_user: str = Field(default="", description="目标用户")
    known_competitors: list[str] = Field(default_factory=list, description="已知竞品")
    business_model: str = Field(default="", description="商业模式")
    keywords: list[str] = Field(default_factory=list, description="搜索关键词")
    raw_prd: str = Field(default="", description="PRD原文")
    raw_idea: str = Field(default="", description="自然语言灵感描述")


class CleanedItem(BaseModel):
    """清洗后的数据项"""
    content: str = Field(..., description="内容正文")
    source_url: str = Field(..., description="来源链接")
    platform: str = Field(..., description="来源平台")
    engagement: int = Field(default=0, description="互动数")
    emotion_intensity: str = Field(default="一般", description="情绪强度")


class DemandSignal(BaseModel):
    """需求信号"""
    quote: str = Field(..., description="原始用户发言摘录")
    source_url: str = Field(..., description="来源链接")
    platform: str = Field(..., description="来源平台")
    engagement: int = Field(default=0, description="互动数")
    emotion_intensity: str = Field(default="一般", description="情绪强度")


class CompetitorQuote(BaseModel):
    """竞品引用"""
    quote: str = Field(..., description="用户原文")
    source_url: str = Field(..., description="来源链接")


class Competitor(BaseModel):
    """竞品信息"""
    name: str = Field(..., description="竞品名称")
    solved_quotes: list[CompetitorQuote] = Field(default_factory=list, description="已解决引用")
    unsolved_quotes: list[CompetitorQuote] = Field(default_factory=list, description="未解决引用")


class DifferentiationGap(BaseModel):
    """差异化维度"""
    dimension: str = Field(..., description="维度名称")
    complaint_count: int = Field(default=0, description="抱怨频次")
    representative_quotes: list[CompetitorQuote] = Field(default_factory=list, description="代表性引用")


class Risk(BaseModel):
    """风险项"""
    risk_type: str = Field(..., description="风险类型")
    description: str = Field(..., description="风险描述")
    evidence_quote: str = Field(..., description="证据原文")
    source_url: str = Field(..., description="来源链接")
    severity: str = Field(default="中", description="严重程度")


class SSEEvent(BaseModel):
    """SSE事件"""
    stage: str = Field(..., description="当前阶段")
    platform: Optional[str] = Field(default=None, description="平台")
    count: Optional[int] = Field(default=None, description="数量")
    agent: Optional[str] = Field(default=None, description="Agent名称")
    message: Optional[str] = Field(default=None, description="消息")
