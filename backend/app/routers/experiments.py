import json

from fastapi import APIRouter, HTTPException

from ..db import SessionLocal
from ..models import ExperimentRun
from ..schemas import EvaluationResponse, ExperimentRunDetailResponse, ExperimentRunRequest, ExperimentRunResponse
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
            baseline_attack_success=result.baseline_attack_success,
            defended_attack_success=result.defended_attack_success,
            baseline_legitimate_task_success=result.baseline_legitimate_task_success,
            defended_legitimate_task_success=result.defended_legitimate_task_success,
            baseline_false_refusal=result.baseline_false_refusal,
            defended_false_refusal=result.defended_false_refusal,
            baseline_canary_leakage_raw=result.baseline_canary_leakage_raw,
            baseline_canary_leakage_visible=result.baseline_canary_leakage_visible,
            defended_canary_leakage_raw=result.defended_canary_leakage_raw,
            defended_canary_leakage_visible=result.defended_canary_leakage_visible,
            baseline_unauthorized_tool_attempted=result.baseline_unauthorized_tool_attempted,
            baseline_unauthorized_tool_executed=result.baseline_unauthorized_tool_executed,
            defended_unauthorized_tool_attempted=result.defended_unauthorized_tool_attempted,
            defended_unauthorized_tool_executed=result.defended_unauthorized_tool_executed,
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


@router.get("/{experiment_id}", response_model=ExperimentRunDetailResponse)
def get_experiment(experiment_id: str) -> ExperimentRunDetailResponse:
    from ..schemas import ExperimentRunDetailResponse
    from ..services.benchmarks import get_experiment_detail

    db = SessionLocal()
    try:
        detail = get_experiment_detail(experiment_id, db)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Experiment {experiment_id!r} not found.")
        return detail
    finally:
        db.close()



