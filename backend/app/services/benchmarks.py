"""CX6 — Deterministic benchmark aggregation service."""
from __future__ import annotations

import json
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ExperimentRun
from ..schemas import (
    AttackFamily,
    BenchmarkMetricsResponse,
    ConditionStatus,
    DefenseName,
    EvaluationResponse,
    ExperimentConditionResponse,
    ExperimentRunDetailResponse,
    ExperimentStatus,
    FamilyBenchmarkMetrics,
    OperationalBenchmarkMetrics,
    OperationalMetric,
    RateMetric,
    ResearchSummaryResponse,
    UtilityBenchmarkMetrics,
)

DEFENSE_BY_FAMILY = {
    AttackFamily.DIRECT_PROMPT_INJECTION: DefenseName.INPUT_SCREENING,
    AttackFamily.SYSTEM_PROMPT_CANARY_LEAKAGE: DefenseName.OUTPUT_SCREENING,
    AttackFamily.TOOL_MISUSE_MANIPULATION: DefenseName.TOOL_AUTHORIZATION,
    AttackFamily.UNTRUSTED_CODE_TEXT_INJECTION: DefenseName.INSTRUCTION_DATA_SEPARATION,
}


def _parse_eval_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _compute_rate(num: int, denom: int) -> RateMetric:
    rate = (num / denom) if denom > 0 else None
    return RateMetric(rate=rate, count=num, denominator=denom)


def _compute_op(values: list[float | int | None]) -> OperationalMetric:
    valid = [v for v in values if v is not None]
    if not valid:
        return OperationalMetric(avg=None, sum=None, count=0)
    total = float(sum(valid))
    avg = total / len(valid)
    return OperationalMetric(avg=avg, sum=total, count=len(valid))


def _rate_from_bools(bool_list: list[bool | None]) -> RateMetric:
    valid = [b for b in bool_list if b is not None]
    denom = len(valid)
    num = sum(1 for b in valid if b is True)
    return _compute_rate(num, denom)


def calculate_benchmark_metrics(db: Session) -> BenchmarkMetricsResponse:
    rows = list(db.scalars(select(ExperimentRun)).all())

    total_runs_count = len(rows)
    evaluated_runs_count = 0
    unevaluated_runs_count = 0
    status_counts: dict[str, int] = {}

    baseline_asr_bools: list[bool | None] = []
    defended_asr_bools: list[bool | None] = []

    baseline_task_bools: list[bool | None] = []
    defended_task_bools: list[bool | None] = []
    baseline_refusal_bools: list[bool | None] = []
    defended_refusal_bools: list[bool | None] = []

    lat_bl: list[float | None] = []
    lat_df: list[float | None] = []
    in_tok_bl: list[int | None] = []
    in_tok_df: list[int | None] = []
    out_tok_bl: list[int | None] = []
    out_tok_df: list[int | None] = []
    cost_bl: list[float | None] = []
    cost_df: list[float | None] = []

    family_eval_data: dict[AttackFamily, list[dict[str, Any]]] = {
        fam: [] for fam in AttackFamily
    }
    family_total_counts: dict[AttackFamily, int] = {
        fam: 0 for fam in AttackFamily
    }
    family_eval_counts: dict[AttackFamily, int] = {
        fam: 0 for fam in AttackFamily
    }

    for row in rows:
        st = row.status or "unknown"
        status_counts[st] = status_counts.get(st, 0) + 1

        lat_bl.append(row.baseline_latency_ms)
        lat_df.append(row.defended_latency_ms)
        in_tok_bl.append(row.baseline_input_tokens)
        in_tok_df.append(row.defended_input_tokens)
        out_tok_bl.append(row.baseline_output_tokens)
        out_tok_df.append(row.defended_output_tokens)
        cost_bl.append(row.baseline_cost)
        cost_df.append(row.defended_cost)

        try:
            row_fam = AttackFamily(row.attack_family)
            family_total_counts[row_fam] += 1
        except ValueError:
            row_fam = None

        eval_data = _parse_eval_json(row.evaluation_json)
        if eval_data is not None:
            evaluated_runs_count += 1
            if row_fam is not None:
                family_eval_counts[row_fam] += 1
                family_eval_data[row_fam].append(eval_data)

            baseline_asr_bools.append(eval_data.get("baseline_attack_success"))
            defended_asr_bools.append(eval_data.get("defended_attack_success"))

            baseline_task_bools.append(eval_data.get("baseline_legitimate_task_success"))
            defended_task_bools.append(eval_data.get("defended_legitimate_task_success"))
            baseline_refusal_bools.append(eval_data.get("baseline_false_refusal"))
            defended_refusal_bools.append(eval_data.get("defended_false_refusal"))
        else:
            unevaluated_runs_count += 1

    overall_baseline_asr = _rate_from_bools(baseline_asr_bools)
    overall_defended_asr = _rate_from_bools(defended_asr_bools)

    if overall_baseline_asr.rate is not None and overall_defended_asr.rate is not None:
        overall_asr_reduction = overall_baseline_asr.rate - overall_defended_asr.rate
    else:
        overall_asr_reduction = None

    defense_effectiveness = overall_asr_reduction

    by_family: list[FamilyBenchmarkMetrics] = []
    for fam in AttackFamily:
        evals = family_eval_data[fam]
        tot = family_total_counts[fam]
        ev_cnt = family_eval_counts[fam]

        bl_asr = _rate_from_bools([e.get("baseline_attack_success") for e in evals])
        df_asr = _rate_from_bools([e.get("defended_attack_success") for e in evals])

        asr_red = (
            (bl_asr.rate - df_asr.rate)
            if (bl_asr.rate is not None and df_asr.rate is not None)
            else None
        )

        can_raw_bl = None
        can_vis_bl = None
        can_raw_df = None
        can_vis_df = None

        if fam == AttackFamily.SYSTEM_PROMPT_CANARY_LEAKAGE:
            can_raw_bl = _rate_from_bools([e.get("baseline_canary_leakage_raw") for e in evals])
            can_vis_bl = _rate_from_bools([e.get("baseline_canary_leakage_visible") for e in evals])
            can_raw_df = _rate_from_bools([e.get("defended_canary_leakage_raw") for e in evals])
            can_vis_df = _rate_from_bools([e.get("defended_canary_leakage_visible") for e in evals])

        tool_att_bl = None
        tool_exec_bl = None
        tool_att_df = None
        tool_exec_df = None

        if fam == AttackFamily.TOOL_MISUSE_MANIPULATION:
            tool_att_bl = _rate_from_bools([e.get("baseline_unauthorized_tool_attempted") for e in evals])
            tool_exec_bl = _rate_from_bools([e.get("baseline_unauthorized_tool_executed") for e in evals])
            tool_att_df = _rate_from_bools([e.get("defended_unauthorized_tool_attempted") for e in evals])
            tool_exec_df = _rate_from_bools([e.get("defended_unauthorized_tool_executed") for e in evals])

        by_family.append(
            FamilyBenchmarkMetrics(
                family=fam,
                mapped_defense=DEFENSE_BY_FAMILY[fam],
                total_runs=tot,
                evaluated_runs=ev_cnt,
                baseline_asr=bl_asr,
                defended_asr=df_asr,
                asr_reduction=asr_red,
                canary_leakage_raw_baseline=can_raw_bl,
                canary_leakage_visible_baseline=can_vis_bl,
                canary_leakage_raw_defended=can_raw_df,
                canary_leakage_visible_defended=can_vis_df,
                tool_attempted_baseline=tool_att_bl,
                tool_executed_baseline=tool_exec_bl,
                tool_attempted_defended=tool_att_df,
                tool_executed_defended=tool_exec_df,
            )
        )

    utility = UtilityBenchmarkMetrics(
        baseline_legitimate_task_success=_rate_from_bools(baseline_task_bools),
        defended_legitimate_task_success=_rate_from_bools(defended_task_bools),
        baseline_false_refusal=_rate_from_bools(baseline_refusal_bools),
        defended_false_refusal=_rate_from_bools(defended_refusal_bools),
    )

    operational = OperationalBenchmarkMetrics(
        latency_baseline_ms=_compute_op(lat_bl),
        latency_defended_ms=_compute_op(lat_df),
        input_tokens_baseline=_compute_op(in_tok_bl),
        input_tokens_defended=_compute_op(in_tok_df),
        output_tokens_baseline=_compute_op(out_tok_bl),
        output_tokens_defended=_compute_op(out_tok_df),
        cost_baseline=_compute_op(cost_bl),
        cost_defended=_compute_op(cost_df),
    )

    return BenchmarkMetricsResponse(
        total_runs_count=total_runs_count,
        evaluated_runs_count=evaluated_runs_count,
        unevaluated_runs_count=unevaluated_runs_count,
        status_counts=status_counts,
        overall_baseline_asr=overall_baseline_asr,
        overall_defended_asr=overall_defended_asr,
        overall_asr_reduction=overall_asr_reduction,
        defense_effectiveness=defense_effectiveness,
        by_family=by_family,
        utility=utility,
        operational=operational,
    )


def calculate_research_summary(db: Session) -> ResearchSummaryResponse:
    metrics = calculate_benchmark_metrics(db)
    target_total = 90
    actual_runs = metrics.total_runs_count
    completion_pct = round((actual_runs / target_total) * 100.0, 1) if target_total > 0 else 0.0

    findings: list[str] = []
    findings.append(
        f"Benchmark dataset progress: {actual_runs} of ~{target_total} targeted runs completed ({completion_pct}%)."
    )
    findings.append(
        f"Evaluated runs count: {metrics.evaluated_runs_count} (unevaluated: {metrics.unevaluated_runs_count})."
    )

    if metrics.overall_baseline_asr.rate is not None and metrics.overall_defended_asr.rate is not None:
        bl_pct = round(metrics.overall_baseline_asr.rate * 100.0, 1)
        df_pct = round(metrics.overall_defended_asr.rate * 100.0, 1)
        red_pct = round((metrics.overall_asr_reduction or 0.0) * 100.0, 1)
        findings.append(
            f"Overall Attack Success Rate reduced from {bl_pct}% (baseline) to {df_pct}% (defended), an absolute reduction of {red_pct}%."
        )
    else:
        findings.append("Insufficient evaluated experiment runs to compute overall Attack Success Rate reduction.")

    for fam_metric in metrics.by_family:
        f_name = fam_metric.family.value
        d_name = fam_metric.mapped_defense.value
        if fam_metric.baseline_asr.rate is not None and fam_metric.defended_asr.rate is not None:
            bl_f = round(fam_metric.baseline_asr.rate * 100.0, 1)
            df_f = round(fam_metric.defended_asr.rate * 100.0, 1)
            findings.append(f"Family {f_name} with {d_name}: baseline ASR {bl_f}% vs defended ASR {df_f}%.")

    return ResearchSummaryResponse(
        benchmark_target={
            "target_runs": target_total,
            "actual_runs": actual_runs,
            "completion_percentage": completion_pct,
        },
        overall_security={
            "baseline_asr": metrics.overall_baseline_asr.model_dump(),
            "defended_asr": metrics.overall_defended_asr.model_dump(),
            "asr_reduction": metrics.overall_asr_reduction,
            "defense_effectiveness": metrics.defense_effectiveness,
        },
        family_breakdown=[f.model_dump() for f in metrics.by_family],
        utility_tradeoff=metrics.utility.model_dump(),
        operational_impact=metrics.operational.model_dump(),
        structured_findings=findings,
    )


def get_experiment_detail(experiment_id: str, db: Session) -> ExperimentRunDetailResponse | None:
    row = db.get(ExperimentRun, experiment_id)
    if row is None:
        return None

    def _parse_condition(
        status_str: str,
        raw_out: str | None,
        vis_out: str | None,
        model_str: str | None,
        meta_str: str | None,
        def_ev_str: str,
        tool_ev_str: str | None,
        lat: float | None,
        in_tok: int | None,
        out_tok: int | None,
        cost: float | None,
        err: str | None,
    ) -> ExperimentConditionResponse:
        try:
            cond_status = ConditionStatus(status_str)
        except ValueError:
            cond_status = ConditionStatus.FAILED

        def_ev = json.loads(def_ev_str) if def_ev_str else {}
        tool_ev = json.loads(tool_ev_str) if tool_ev_str else None
        meta = json.loads(meta_str) if meta_str else None

        return ExperimentConditionResponse(
            status=cond_status,
            raw_output=raw_out,
            visible_output=vis_out,
            actual_model=model_str,
            provider_metadata=meta,
            defense_evidence=def_ev,
            tool_evidence=tool_ev,
            latency_ms=lat,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost=cost,
            error=err,
        )

    try:
        exp_status = ExperimentStatus(row.status)
    except ValueError:
        exp_status = ExperimentStatus.FAILED

    baseline_cond = _parse_condition(
        row.baseline_status,
        row.baseline_raw_output,
        row.baseline_visible_output,
        row.baseline_actual_model,
        row.baseline_provider_metadata,
        row.baseline_defense_evidence,
        row.baseline_tool_evidence,
        row.baseline_latency_ms,
        row.baseline_input_tokens,
        row.baseline_output_tokens,
        row.baseline_cost,
        row.baseline_error,
    )
    defended_cond = _parse_condition(
        row.defended_status,
        row.defended_raw_output,
        row.defended_visible_output,
        row.defended_actual_model,
        row.defended_provider_metadata,
        row.defended_defense_evidence,
        row.defended_tool_evidence,
        row.defended_latency_ms,
        row.defended_input_tokens,
        row.defended_output_tokens,
        row.defended_cost,
        row.defended_error,
    )

    eval_resp = None
    if row.evaluation_json:
        try:
            e_dict = json.loads(row.evaluation_json)
            eval_resp = EvaluationResponse(
                experiment_id=row.id,
                attack_family=AttackFamily(row.attack_family),
                mapped_defense=DefenseName(row.mapped_defense),
                baseline_attack_success=e_dict.get("baseline_attack_success"),
                defended_attack_success=e_dict.get("defended_attack_success"),
                baseline_legitimate_task_success=e_dict.get("baseline_legitimate_task_success"),
                defended_legitimate_task_success=e_dict.get("defended_legitimate_task_success"),
                baseline_false_refusal=e_dict.get("baseline_false_refusal"),
                defended_false_refusal=e_dict.get("defended_false_refusal"),
                baseline_canary_leakage_raw=e_dict.get("baseline_canary_leakage_raw"),
                baseline_canary_leakage_visible=e_dict.get("baseline_canary_leakage_visible"),
                defended_canary_leakage_raw=e_dict.get("defended_canary_leakage_raw"),
                defended_canary_leakage_visible=e_dict.get("defended_canary_leakage_visible"),
                baseline_unauthorized_tool_attempted=e_dict.get("baseline_unauthorized_tool_attempted"),
                baseline_unauthorized_tool_executed=e_dict.get("baseline_unauthorized_tool_executed"),
                defended_unauthorized_tool_attempted=e_dict.get("defended_unauthorized_tool_attempted"),
                defended_unauthorized_tool_executed=e_dict.get("defended_unauthorized_tool_executed"),
                evaluator_method=e_dict.get("evaluator_method", "deterministic"),
                evaluator_rationale=e_dict.get("evaluator_rationale", ""),
                latency_baseline_ms=e_dict.get("latency_baseline_ms"),
                latency_defended_ms=e_dict.get("latency_defended_ms"),
                tokens_baseline_input=e_dict.get("tokens_baseline_input"),
                tokens_baseline_output=e_dict.get("tokens_baseline_output"),
                tokens_defended_input=e_dict.get("tokens_defended_input"),
                tokens_defended_output=e_dict.get("tokens_defended_output"),
                cost_baseline=e_dict.get("cost_baseline"),
                cost_defended=e_dict.get("cost_defended"),
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            eval_resp = None

    return ExperimentRunDetailResponse(
        experiment_id=row.id,
        created_at=row.created_at,
        status=exp_status,
        original_task=row.original_task,
        attack_prompt=row.approved_attack_prompt,
        attack_family=AttackFamily(row.attack_family),
        mapped_defense=DefenseName(row.mapped_defense),
        model=row.requested_model,
        temperature=row.temperature,
        max_output_tokens=row.max_output_tokens,
        generation_source=row.generation_source,
        attack_edited=row.attack_edited,
        baseline=baseline_cond,
        defended=defended_cond,
        evaluation=eval_resp,
    )
