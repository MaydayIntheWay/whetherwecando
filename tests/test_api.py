"""
API集成测试
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """健康检查接口测试"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Idea可行性验证工具 API"
    
    def test_health(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestValidateEndpoint:
    """验证接口测试"""
    
    def test_create_validation_with_form(self):
        """测试表单方式创建验证"""
        response = client.post(
            "/api/validate",
            json={
                "problem": "测试痛点",
                "solution": "测试解决方案",
                "target_user": "测试用户",
                "keywords": ["关键词1", "关键词2"]
            }
        )
        assert response.status_code == 200
        assert "task_id" in response.json()
    
    def test_create_validation_with_raw_data(self):
        """测试自然语言方式创建验证"""
        response = client.post(
            "/api/validate",
            json={
                "raw_data": "我想做一个帮助开发者验证产品想法的工具"
            }
        )
        assert response.status_code == 200
        assert "task_id" in response.json()
    
    def test_create_validation_empty(self):
        """测试空数据创建验证"""
        response = client.post(
            "/api/validate",
            json={}
        )
        assert response.status_code == 200
        assert "task_id" in response.json()


class TestReportEndpoint:
    """报告接口测试"""
    
    def test_get_report_not_found(self):
        """测试获取不存在的报告"""
        response = client.get("/api/report/non-existent-id")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
