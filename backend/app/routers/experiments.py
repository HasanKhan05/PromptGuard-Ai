import json

from fastapi import APIRouter, HTTPException

from ..db import SessionLocal
from ..models import ExperimentRun
from ..schemas import EvaluationResponse, ExperimentRunRequest, ExperimentRunResponse
from ..services.evaluator import evaluate_experiment_run, result_to_dict
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


@router.post("/{experiment_id}/evaluate", response_model=EvaluationResponse)
def evaluate_experiment(experiment_id: str) -> EvaluationResponse:
    db = SessionLocal()
    try:
        row = db.get(ExperimentRun, experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id!r} not found.")
        result = evaluate_experiment_run(row)
        row.evaluation_json = json.dumps(result_to_dict(result))
        db.commit()
        from ..schemas import AttackFamily, DefenseName
        return EvaluationResponse(
            experiment_id=experiment_id,
            attack_family=AttackFamily(row.attack_family),
            mapped_defense=DefenseName(row.mapped_defense),
            attack_success=result.attack_success,
            benign_success=result.benign_success,
            false_refusal=result.false_refusal,
            canary_leakage_raw=result.canary_leakage_raw,
            canary_leakage_visible=result.canary_leakage_visible,
            unauthorized_tool_attempted=result.unauthorized_tool_attempted,
            unauthorized_tool_executed=result.unauthorized_tool_executed,
            evaluator_method=result.evaluator_method,
            evaluator_rationale=result.evaluator_rationale,
            latency_baseline_ms=result.latency_baseline_ms,
            latency_defended_ms=result.latency_defended_ms,
            tokens_baseline_input=result.tokens_baseline_input,
            tokens_baseline_output=result.tokens_baseline_output,
            tokens_defended_input=result.tokens_defended_input,
            tokens_defended_output=result.tokens_defended_output,
            cost_baseline=result.cost_baseline,
            cost_defended=result.cost_defended,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        db.close()

