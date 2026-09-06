from fastapi import APIRouter

from ..db import SessionLocal
from ..schemas import ResearchSummaryResponse
from ..services.benchmarks import calculate_research_summary

router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("", response_model=ResearchSummaryResponse)
@router.get("/", response_model=ResearchSummaryResponse)
def get_research() -> ResearchSummaryResponse:
    db = SessionLocal()
    try:
        return calculate_research_summary(db)
    finally:
        db.close()
