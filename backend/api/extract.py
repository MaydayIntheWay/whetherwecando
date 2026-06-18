"""
关键词提取API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from models import ProductInput
from agents import extract_from_idea, extract_keywords

router = APIRouter()


class RawIdeaInput(BaseModel):
    raw_idea: str


@router.post("/api/extract/keywords")
async def extract_keywords_api(input_data: ProductInput):
    """提取关键词"""
    keywords = await extract_keywords(input_data)
    return {"keywords": keywords}


@router.post("/api/extract/idea")
async def extract_idea_api(input_data: RawIdeaInput):
    """从自然语言提取结构化字段"""
    result = await extract_from_idea(input_data.raw_idea)
    keywords = await extract_keywords(result)
    return {
        "problem": result.problem,
        "solution": result.solution,
        "target_user": result.target_user,
        "keywords": keywords
    }
