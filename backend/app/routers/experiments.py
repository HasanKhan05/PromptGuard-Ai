from fastapi import APIRouter, HTTPException

from ..db import SessionLocal
from ..schemas import ExperimentRunRequest, ExperimentRunResponse
from ..services.experiments import run_paired_experiment

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.post("/run", response_model=ExperimentRunResponse)
async def run_experiment(payload: ExperimentRunRequest) -> ExperimentRunResponse:
    db = SessionLocal()
    try:
        return await run_paired_experiment(payload, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        db.close()
