"""
Agent模块单元测试
"""
import pytest
from agents import judge
from models import (
    DemandOutput, DemandSignal,
    FeasibilityOutput, Competitor,
    DifferentiationOutput, DifferentiationGap,
    RisksOutput, Risk
)


class TestJudgeNode:
    """裁判节点测试"""
    
    def test_judge_stop_no_data(self):
        """测试Stop - 无数据支持"""
        demand = DemandOutput(score=0, verdict="无数据支持", signals=[])
        feasibility = FeasibilityOutput(verdict="数据不足", competitors=[])
        differentiation = DifferentiationOutput(gaps=[])
        risks = RisksOutput(risks=[])
        
        verdict, reason = judge(demand, feasibility, differentiation, risks)
        
        assert verdict == "Stop"
        assert "未发现相关需求" in reason
    
    def test_judge_stop_high_risks(self):
        """测试Stop - 高风险"""
        demand = DemandOutput(score=70, verdict="强", signals=[])
        feasibility = FeasibilityOutput(verdict="市场有空间", competitors=[])
        differentiation = DifferentiationOutput(gaps=[])
        risks = RisksOutput(risks=[
            Risk(risk_type="竞争激烈", description="", evidence_quote="", source_url="url1", severity="高"),
            Risk(risk_type="付费意愿弱", description="", evidence_quote="", source_url="url2", severity="高"),
            Risk(risk_type="市场规模不足", description="", evidence_quote="", source_url="url3", severity="高"),
        ])
        
        verdict, reason = judge(demand, feasibility, differentiation, risks)
        
        assert verdict == "Stop"
        assert "高风险" in reason
    
    def test_judge_go(self):
        """测试Go - 推进"""
        demand = DemandOutput(score=75, verdict="强", signals=[
            DemandSignal(quote="test", source_url="url1", platform="xhs", engagement=100, emotion_intensity="强烈")
        ])
        feasibility = FeasibilityOutput(verdict="市场有空间", competitors=[])
        differentiation = DifferentiationOutput(gaps=[
            DifferentiationGap(dimension="价格", complaint_count=10, representative_quotes=[])
        ])
        risks = RisksOutput(risks=[
            Risk(risk_type="竞争激烈", description="", evidence_quote="", source_url="url1", severity="中")
        ])
        
        verdict, reason = judge(demand, feasibility, differentiation, risks)
        
        assert verdict == "Go"
        assert "75分" in reason
    
    def test_judge_pivot(self):
        """测试Pivot - 调整方向"""
        demand = DemandOutput(score=45, verdict="弱", signals=[])
        feasibility = FeasibilityOutput(verdict="数据不足", competitors=[])
        differentiation = DifferentiationOutput(gaps=[])
        risks = RisksOutput(risks=[])
        
        verdict, reason = judge(demand, feasibility, differentiation, risks)
        
        assert verdict == "Pivot"
    
    def test_judge_stop_solved(self):
        """测试Stop - 已被充分解决"""
        demand = DemandOutput(score=60, verdict="强", signals=[])
        feasibility = FeasibilityOutput(verdict="已被充分解决", competitors=[])
        differentiation = DifferentiationOutput(gaps=[])
        risks = RisksOutput(risks=[])
        
        verdict, reason = judge(demand, feasibility, differentiation, risks)
        
        assert verdict == "Stop"
        assert "已被充分解决" in reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
