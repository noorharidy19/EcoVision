from fastapi import APIRouter

from .plan_model import PlanModel

router = APIRouter(prefix="/plan")
plan_model = PlanModel("C:\\Users\\Hassan Hatem\\Downloads\\my_cad_model")

