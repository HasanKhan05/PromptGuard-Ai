from fastapi import APIRouter, HTTPException
from openai import APIError

from ..schemas import (
    AttackEligibilityRequest,
    AttackEligibilityResponse,
    AttackGenerationRequest,
    AttackGenerationResult,
)
from ..services.attacks import AttackModelOutputError, assess_eligibility, generate_attack

router = APIRouter(prefix="/api/attacks", tags=["attacks"])


@router.post("/eligibility", response_model=AttackEligibilityResponse)
async def eligibility(payload: AttackEligibilityRequest) -> AttackEligibilityResponse:
    try:
        return await assess_eligibility(payload.original_task)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (AttackModelOutputError, APIError) as exc:
        raise HTTPException(status_code=502, detail="Unable to obtain a valid eligibility analysis.") from exc


@router.post("/generate", response_model=AttackGenerationResult)
async def generate(payload: AttackGenerationRequest) -> AttackGenerationResult:
    try:
        return await generate_attack(payload.original_task, payload.attack_family)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (AttackModelOutputError, APIError) as exc:
        raise HTTPException(status_code=502, detail="Unable to obtain a valid generated attack.") from exc
