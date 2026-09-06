from fastapi import APIRouter, HTTPException

from ..db import SessionLocal
from ..schemas import ExperimentRunDetailResponse
from ..services.benchmarks import get_experiment_detail

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{run_id}", response_model=ExperimentRunDetailResponse)
def get_run(run_id: str) -> ExperimentRunDetailResponse:
    db = SessionLocal()
    try:
        detail = get_experiment_detail(run_id, db)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found.")
        return detail
    finally:
        db.close()
