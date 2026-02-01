# main.py
from fastapi import APIRouter, FastAPI
from app.services.analysis.plan_service import router as plan_router  # import the router

router = APIRouter(prefix="/plan")

# Mount the service router
