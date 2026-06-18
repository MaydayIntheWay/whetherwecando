"""
API路由定义
"""
import uuid
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import (
    ProductInput, CleanedItem, SSEEvent,
    ValidationReport
)
from crawler import XiaohongshuCrawler, ZhihuCrawler, crawl_keywords_parallel
from cleaner import DataCleaner
from agents import (
    extract_keywords, analyze_demand,
    analyze_feasibility, analyze_differentiation,
    analyze_risks
)
from report import generate_report
from database.connection import fetch_one, execute_query

router = APIRouter()


@router.post("/api/validate")
async def create_validation(input_data: ProductInput):
    """创建验证任务"""
    task_id = str(uuid.uuid4())
    
    await execute_query(
        """
        INSERT INTO validation_tasks (id, status, created_at)
        VALUES ($1, 'pending', $2)
        """,
        task_id, datetime.now()
    )
    
    await execute_query(
        """
        INSERT INTO product_inputs (task_id, problem, solution, target_user, keywords)
        VALUES ($1, $2, $3, $4, $5)
        """,
        task_id, input_data.problem, input_data.solution,
        input_data.target_user, input_data.keywords
    )
    
    asyncio.create_task(run_validation(task_id, input_data))
    
    return {"task_id": task_id}


@router.get("/api/validate/stream")
async def stream_validation(task_id: str):
    """SSE流式返回验证进度"""
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            task = await fetch_one(
                "SELECT status FROM validation_tasks WHERE id = $1",
                task_id
            )
            
            if not task:
                yield _sse_event(SSEEvent(stage="error", message="任务不存在"))
                return
            
            while True:
                task = await fetch_one(
                    "SELECT status FROM validation_tasks WHERE id = $1",
                    task_id
                )
                
                if not task:
                    yield _sse_event(SSEEvent(stage="error", message="任务不存在"))
                    break
                
                status = task["status"]
                
                if status == "done":
                    report = await fetch_one(
                        "SELECT * FROM validation_reports WHERE task_id = $1",
                        task_id
                    )
                    if report:
                        yield _sse_event(SSEEvent(stage="done", message="完成"))
                    break
                
                if status == "error":
                    yield _sse_event(SSEEvent(stage="error", message="验证失败"))
                    break
                
                await asyncio.sleep(1)
                
        except Exception as e:
            yield _sse_event(SSEEvent(stage="error", message=str(e)))
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/api/report/{task_id}")
async def get_report(task_id: str):
    """获取验证报告"""
    report = await fetch_one(
        "SELECT * FROM validation_reports WHERE task_id = $1",
        task_id
    )
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return report


def _sse_event(event: SSEEvent) -> str:
    """格式化SSE事件"""
    import json
    return f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"


async def run_validation(task_id: str, input_data: ProductInput):
    """执行验证流程"""
    try:
        keywords = await extract_keywords(input_data)
        
        xhs_crawler = XiaohongshuCrawler()
        zhihu_crawler = ZhihuCrawler()
        
        xhs_task = crawl_keywords_parallel(xhs_crawler, keywords, 20, 2)
        zhihu_task = crawl_keywords_parallel(zhihu_crawler, keywords, 10, 2)
        
        xhs_data, zhihu_data = await asyncio.gather(xhs_task, zhihu_task)
        
        all_data = xhs_data + zhihu_data
        
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean(all_data)
        
        demand = await analyze_demand(cleaned_data, input_data.problem, input_data.target_user)
        feasibility = await analyze_feasibility(cleaned_data, input_data.solution, input_data.known_competitors)
        differentiation = await analyze_differentiation(cleaned_data)
        risks = await analyze_risks(cleaned_data)
        
        report = generate_report(
            task_id,
            {
                "problem": input_data.problem,
                "solution": input_data.solution,
                "target_user": input_data.target_user
            },
            cleaned_data,
            demand,
            feasibility,
            differentiation,
            risks
        )
        
        await _save_report(report)
        
        await execute_query(
            "UPDATE validation_tasks SET status = 'done' WHERE id = $1",
            task_id
        )
        
    except Exception as e:
        await execute_query(
            "UPDATE validation_tasks SET status = 'error' WHERE id = $1",
            task_id
        )
        print(f"验证失败: {e}")


async def _save_report(report: ValidationReport):
    """保存报告到数据库"""
    import json
    
    await execute_query(
        """
        INSERT INTO validation_reports 
        (task_id, verdict, verdict_reason, demand, feasibility, differentiation, risks, demand_heatmap, data_stats)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        report.task_id,
        report.verdict,
        report.verdict_reason,
        json.dumps(report.demand.model_dump()) if report.demand else None,
        json.dumps(report.feasibility.model_dump()) if report.feasibility else None,
        json.dumps(report.differentiation.model_dump()) if report.differentiation else None,
        json.dumps(report.risks.model_dump()) if report.risks else None,
        json.dumps(report.demand_heatmap) if report.demand_heatmap else None,
        json.dumps(report.data_stats) if report.data_stats else None
    )
