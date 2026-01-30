# api/plan.py

from fastapi import APIRouter
from app.services.analysis.plan_service import generate_2d_plan

router = APIRouter(prefix="/plans", tags=["2D Plan"])

@router.post("/generate")
def generate_plan(desc: str):
    return {
        "plan": generate_2d_plan(desc)
    }
