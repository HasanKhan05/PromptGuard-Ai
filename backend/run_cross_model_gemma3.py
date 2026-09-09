#!/usr/bin/env python3
"""PromptGuard Ai — Resilient Final Gemma 3 12B (2025) Cross-Model Benchmark Runner.

Offline-safe runner:
1. Generates and persists baseline model response immediately.
2. Generates and persists defended model response immediately.
3. Attempts evaluation:
   - On success, persists evaluation.
   - On transient network/evaluator errors, marks evaluation as PENDING and continues to the next case.
4. Supports --evaluate-pending to evaluate stored responses without regenerating outputs.
5. Detached background execution safe on Windows.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import sys
from typing import Any, Optional
from uuid import uuid4

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, ExperimentRun
from app.schemas import AttackFamily, ConditionStatus, DefenseName, ExperimentRunRequest
from app.services.cross_model import partition_cross_model_cases
from app.services.evaluator import result_to_dict
from app.services.experiments import (
    DEFENSE_VERSION,
    SYSTEM_PROMPT_VERSION,
    TOOL_SCHEMA_VERSION,
    _json_or_none,
    _make_spec,
    _run_condition,
    get_experiment_client,
)
from app.services.ollama import is_ollama_model
from app.services.resilience import (
    EvaluationStatus,
    evaluate_with_resilience,
    is_transient_evaluator_error,
)

FROZEN_DIR = BACKEND_DIR / "benchmark_results" / "final_90"
GEMMA3_DIR = BACKEND_DIR / "benchmark_results" / "cross_model" / "gemma3_12b"
GEMMA3_DB_PATH = GEMMA3_DIR / "gemma3_12b.db"
GEMMA3_LEDGER_PATH = GEMMA3_DIR / "ledger.json"

PREFLIGHT_DIR = BACKEND_DIR / "benchmark_results" / "cross_model" / "gemma3_12b_preflight"
PREFLIGHT_DB_PATH = PREFLIGHT_DIR / "preflight.db"
PREFLIGHT_LEDGER_PATH = PREFLIGHT_DIR / "preflight_ledger.json"

MODEL_TAG = "gemma3:12b"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 800
NUM_CTX = 4096


def get_db_session(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def load_ledger(ledger_path: Path) -> dict[str, Any]:
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "benchmark": "PromptGuard Ai — Cross-Model Benchmark (Gemma 3 12B)",
        "model": MODEL_TAG,
        "temperature": TEMPERATURE,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "num_ctx": NUM_CTX,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cases": {},
    }


def save_ledger(ledger_path: Path, ledger: dict[str, Any]):
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def get_comparable_cases() -> list[dict[str, Any]]:
    manifest_path = FROZEN_DIR / "manifest_final_90.jsonl"
    cases = [json.loads(line) for line in open(manifest_path, "r", encoding="utf-8") if line.strip()]
    partition = partition_cross_model_cases(cases)
    comparable = [c for c in cases if c["case_id"] not in partition["total_excluded_ids"]]
    assert len(comparable) == 72, f"Expected 72 comparable cases, got {len(comparable)}"
    return comparable


async def process_single_case(
    case_idx: int,
    total_cases: int,
    case: dict[str, Any],
    frozen_ledger: dict[str, Any],
    ledger: dict[str, Any],
    ledger_path: Path,
    db: Any,
    client: Any,
) -> bool:
    """Execute one case with immediate per-condition persistence and offline-safe evaluation."""
    case_id = case["case_id"]
    fam_str = case.get("attack_family")
    fam_enum = AttackFamily(fam_str) if fam_str else None
    diff_str = case.get("difficulty")
    orig_task = case["original_task"]

    if fam_enum is not None:
        frozen_case = frozen_ledger.get(case_id, {})
        attack_prompt = frozen_case.get("generated_attack_prompt")
        assert attack_prompt, f"Missing frozen attack prompt for {case_id}"
    else:
        attack_prompt = orig_task

    req = ExperimentRunRequest(
        original_task=orig_task,
        attack_prompt=attack_prompt,
        attack_family=fam_enum,
        model=MODEL_TAG,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        generation_source="generated",
        attack_edited=False,
    )
    spec = _make_spec(req)

    ledger_entry = ledger["cases"].get(case_id)
    existing_row = None
    if ledger_entry and "experiment_id" in ledger_entry:
        eid = ledger_entry["experiment_id"]
        existing_row = db.query(ExperimentRun).filter_by(id=eid).first()

    if not existing_row:
        existing_row = (
            db.query(ExperimentRun)
            .filter_by(original_task=orig_task, approved_attack_prompt=attack_prompt)
            .first()
        )

    # If completely evaluated and valid, skip immediately
    if (
        existing_row
        and existing_row.baseline_status == "completed"
        and existing_row.defended_status == "completed"
        and existing_row.evaluation_json
        and "PENDING" not in existing_row.evaluation_json
    ):
        if not ledger_entry or not ledger_entry.get("evaluation_completed"):
            ledger["cases"][case_id] = {
                "case_id": case_id,
                "family": fam_str,
                "difficulty": diff_str,
                "experiment_id": existing_row.id,
                "status": "completed",
                "evaluation_status": "completed",
                "evaluation_completed": True,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            save_ledger(ledger_path, ledger)
        return False

    print(f"\n--- [{case_idx}/{total_cases}] Processing Case {case_id} ({fam_str or 'benign'}) ---")

    # 1. Initialize DB row if not present
    if not existing_row:
        exp_id = str(uuid4())
        row = ExperimentRun(
            id=exp_id,
            status="in_progress",
            original_task=spec.original_task,
            approved_attack_prompt=spec.attack_prompt,
            attack_family=spec.attack_family.value if spec.attack_family else None,
            mapped_defense=spec.mapped_defense.value,
            generation_source=spec.generation_source,
            attack_edited=spec.attack_edited,
            requested_model=spec.model,
            temperature=spec.temperature,
            max_output_tokens=spec.max_output_tokens,
            system_prompt_version=SYSTEM_PROMPT_VERSION,
            defense_version=DEFENSE_VERSION,
            tool_schema_version=TOOL_SCHEMA_VERSION,
            baseline_status="pending",
            baseline_defense_evidence='{"enabled": false}',
            defended_status="pending",
            defended_defense_evidence='{"enabled": true}',
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    else:
        row = existing_row
        exp_id = row.id

    # 2. Local Baseline Generation -> Persist immediately
    if row.baseline_status != "completed":
        print(f"[{case_id}] Executing baseline condition on {MODEL_TAG}...")
        baseline = await _run_condition(client, spec, defense_enabled=False)
        if baseline.status != ConditionStatus.COMPLETED:
            row.baseline_status = baseline.status.value
            row.baseline_error = baseline.error
            db.commit()
            raise RuntimeError(f"Baseline generation failed on {case_id}: {baseline.error}")

        row.baseline_status = baseline.status.value
        row.baseline_raw_output = baseline.raw_output
        row.baseline_visible_output = baseline.visible_output
        row.baseline_actual_model = baseline.actual_model
        row.baseline_provider_metadata = _json_or_none(baseline.provider_metadata)
        row.baseline_defense_evidence = json.dumps(baseline.defense_evidence)
        row.baseline_tool_evidence = _json_or_none(baseline.tool_evidence)
        row.baseline_latency_ms = baseline.latency_ms
        row.baseline_input_tokens = baseline.input_tokens
        row.baseline_output_tokens = baseline.output_tokens
        row.baseline_cost = baseline.cost
        db.commit()
        print(f"[{case_id}] Baseline saved ({row.baseline_tokens_summary() if hasattr(row, 'baseline_tokens_summary') else f'in:{row.baseline_input_tokens}/out:{row.baseline_output_tokens}'}).")
    else:
        print(f"[{case_id}] Baseline already completed. Reusing saved output.")

    # 3. Local Defended Generation -> Persist immediately
    if row.defended_status != "completed":
        print(f"[{case_id}] Executing defended condition on {MODEL_TAG}...")
        defended = await _run_condition(client, spec, defense_enabled=True)
        if defended.status != ConditionStatus.COMPLETED:
            row.defended_status = defended.status.value
            row.defended_error = defended.error
            db.commit()
            raise RuntimeError(f"Defended generation failed on {case_id}: {defended.error}")

        row.defended_status = defended.status.value
        row.defended_raw_output = defended.raw_output
        row.defended_visible_output = defended.visible_output
        row.defended_actual_model = defended.actual_model
        row.defended_provider_metadata = _json_or_none(defended.provider_metadata)
        row.defended_defense_evidence = json.dumps(defended.defense_evidence)
        row.defended_tool_evidence = _json_or_none(defended.tool_evidence)
        row.defended_latency_ms = defended.latency_ms
        row.defended_input_tokens = defended.input_tokens
        row.defended_output_tokens = defended.output_tokens
        row.defended_cost = defended.cost
        row.status = "completed"
        db.commit()
        print(f"[{case_id}] Defended saved ({f'in:{row.defended_input_tokens}/out:{row.defended_output_tokens}'}). Both local outputs complete.")
    else:
        print(f"[{case_id}] Defended already completed. Reusing saved output.")

    # Update ledger with model completion state
    ledger["cases"][case_id] = {
        "case_id": case_id,
        "family": fam_str,
        "difficulty": diff_str,
        "experiment_id": exp_id,
        "status": "generation_completed",
        "evaluation_status": "pending",
        "evaluation_completed": False,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    save_ledger(ledger_path, ledger)

    # 4. Resilient Evaluation Attempt
    print(f"[{case_id}] Attempting evaluation...")
    status, eval_res, rationale = evaluate_with_resilience(row)

    if status == EvaluationStatus.COMPLETED and eval_res is not None:
        eval_dict = result_to_dict(eval_res)
        row.evaluation_json = json.dumps(eval_dict)
        db.commit()
        ledger["cases"][case_id]["status"] = "completed"
        ledger["cases"][case_id]["evaluation_status"] = "completed"
        ledger["cases"][case_id]["evaluation_completed"] = True
        ledger["cases"][case_id]["evaluator_method"] = eval_res.evaluator_method
        save_ledger(ledger_path, ledger)
        print(f"[{case_id}] Evaluated successfully ({eval_res.evaluator_method}): {rationale[:70]}...")
    elif status == EvaluationStatus.PENDING:
        row.evaluation_json = json.dumps({"status": "PENDING", "reason": rationale})
        db.commit()
        ledger["cases"][case_id]["status"] = "generation_completed"
        ledger["cases"][case_id]["evaluation_status"] = "pending"
        ledger["cases"][case_id]["evaluation_completed"] = False
        ledger["cases"][case_id]["evaluator_reason"] = rationale
        save_ledger(ledger_path, ledger)
        print(f"[{case_id}] Transient evaluator issue: {rationale[:70]}... Marked as EVALUATION_PENDING. Continuing to next case.")
    else:
        raise RuntimeError(f"Fatal evaluation failure on {case_id}: {rationale}")

    return True


async def evaluate_pending_cases(ledger_path: Path, db_path: Path):
    """Scan all cases that have completed model outputs and evaluate any pending ones."""
    print("=== Scanning for Pending Evaluations ===")
    ledger = load_ledger(ledger_path)
    db = get_db_session(db_path)

    evaluated_count = 0
    still_pending = 0

    try:
        for cid, entry in ledger["cases"].items():
            if entry.get("evaluation_completed"):
                continue

            eid = entry.get("experiment_id")
            if not eid:
                continue

            row = db.query(ExperimentRun).filter_by(id=eid).first()
            if not row or row.baseline_status != "completed" or row.defended_status != "completed":
                continue

            print(f"\n[Evaluate-Pending] Evaluating Case {cid}...")
            status, eval_res, rationale = evaluate_with_resilience(row)

            if status == EvaluationStatus.COMPLETED and eval_res is not None:
                eval_dict = result_to_dict(eval_res)
                row.evaluation_json = json.dumps(eval_dict)
                db.commit()
                entry["status"] = "completed"
                entry["evaluation_status"] = "completed"
                entry["evaluation_completed"] = True
                entry["evaluator_method"] = eval_res.evaluator_method
                save_ledger(ledger_path, ledger)
                evaluated_count += 1
                print(f"[{cid}] Successfully evaluated: {rationale[:70]}...")
            elif status == EvaluationStatus.PENDING:
                still_pending += 1
                print(f"[{cid}] Still pending: {rationale[:70]}...")
            else:
                raise RuntimeError(f"Fatal evaluation failure on {cid}: {rationale}")

        print(f"\n=== Evaluate-Pending Finished: Evaluated {evaluated_count}, Still Pending {still_pending} ===")
    finally:
        db.close()


async def run_preflight():
    print(f"=== Starting Quick Technical Preflight for {MODEL_TAG} ===")
    assert is_ollama_model(MODEL_TAG), f"{MODEL_TAG} must be recognized as Ollama model"

    preflight_cases = ["DPI-E01", "CAN-E01", "DATA-E01", "BEN-001", "BEN-019"]
    manifest_cases = {c["case_id"]: c for c in get_comparable_cases()}
    frozen_ledger = json.load(open(FROZEN_DIR / "ledger_final_90.json", "r", encoding="utf-8"))["cases"]

    db = get_db_session(PREFLIGHT_DB_PATH)
    ledger = load_ledger(PREFLIGHT_LEDGER_PATH)
    client = get_experiment_client(MODEL_TAG)

    try:
        for idx, cid in enumerate(preflight_cases, 1):
            case = manifest_cases[cid]
            await process_single_case(
                case_idx=idx,
                total_cases=5,
                case=case,
                frozen_ledger=frozen_ledger,
                ledger=ledger,
                ledger_path=PREFLIGHT_LEDGER_PATH,
                db=db,
                client=client,
            )
        print("\n=== PREFLIGHT ALL 5 CASES PASSED SUCCESSFULLY ===")
    finally:
        db.close()


async def run_benchmark(limit: Optional[int] = None, resume: bool = True):
    assert is_ollama_model(MODEL_TAG), f"{MODEL_TAG} must be recognized as Ollama model"
    comparable_cases = get_comparable_cases()
    ledger = load_ledger(GEMMA3_LEDGER_PATH)
    db = get_db_session(GEMMA3_DB_PATH)
    client = get_experiment_client(MODEL_TAG)
    frozen_ledger = json.load(open(FROZEN_DIR / "ledger_final_90.json", "r", encoding="utf-8"))["cases"]

    completed_in_run = 0
    try:
        for idx, case in enumerate(comparable_cases, 1):
            cid = case["case_id"]
            entry = ledger["cases"].get(cid)

            # Skip if fully evaluated and resume is True
            if (
                resume
                and entry
                and entry.get("status") == "completed"
                and entry.get("evaluation_completed")
            ):
                continue

            if limit is not None and completed_in_run >= limit:
                print(f"Reached limit of {limit} cases. Stopping.")
                break

            did_work = await process_single_case(
                case_idx=idx,
                total_cases=72,
                case=case,
                frozen_ledger=frozen_ledger,
                ledger=ledger,
                ledger_path=GEMMA3_LEDGER_PATH,
                db=db,
                client=client,
            )
            if did_work:
                completed_in_run += 1

        print(f"\nBenchmark loop finished. Executed {completed_in_run} cases in this run.")

        # If any evaluations remain pending, attempt to resolve them
        has_pending = any(not e.get("evaluation_completed") for e in ledger["cases"].values())
        if has_pending:
            print("\nAttempting to resolve any remaining pending evaluations...")
            await evaluate_pending_cases(GEMMA3_LEDGER_PATH, GEMMA3_DB_PATH)

    finally:
        db.close()


def print_status():
    comparable_cases = get_comparable_cases()
    ledger = load_ledger(GEMMA3_LEDGER_PATH)
    db = get_db_session(GEMMA3_DB_PATH)

    target_cases = len(comparable_cases)
    baseline_generated = 0
    defended_generated = 0
    generation_complete_pairs = 0
    evaluated = 0
    evaluation_pending = 0
    operational_failures = 0

    for case in comparable_cases:
        cid = case["case_id"]
        entry = ledger["cases"].get(cid, {})
        eid = entry.get("experiment_id")

        if eid:
            row = db.query(ExperimentRun).filter_by(id=eid).first()
            if row:
                if row.baseline_status == "completed":
                    baseline_generated += 1
                elif row.baseline_status == "failed":
                    operational_failures += 1

                if row.defended_status == "completed":
                    defended_generated += 1
                elif row.defended_status == "failed":
                    operational_failures += 1

                if row.baseline_status == "completed" and row.defended_status == "completed":
                    generation_complete_pairs += 1

                if entry.get("evaluation_completed") and row.evaluation_json and "PENDING" not in row.evaluation_json:
                    evaluated += 1
                elif entry.get("evaluation_status") == "pending" or (row.evaluation_json and "PENDING" in row.evaluation_json):
                    evaluation_pending += 1

    db_rows = db.query(ExperimentRun).count()
    db.close()

    print("=== Gemma 3 12B Cross-Model Benchmark Status ===")
    print(f"Target cases:              {target_cases}")
    print(f"Baseline generated:        {baseline_generated}/{target_cases}")
    print(f"Defended generated:        {defended_generated}/{target_cases}")
    print(f"Generation-complete pairs: {generation_complete_pairs}/{target_cases}")
    print(f"Evaluated:                 {evaluated}/{target_cases}")
    print(f"Evaluation pending:        {evaluation_pending}")
    print(f"Operational failures:      {operational_failures}")
    print(f"Active DB rows:            {db_rows}")


def analyze_results() -> dict[str, Any]:
    comparable_cases = get_comparable_cases()
    ledger = load_ledger(GEMMA3_LEDGER_PATH)
    db = get_db_session(GEMMA3_DB_PATH)

    cases_by_id = {c["case_id"]: c for c in comparable_cases}
    records = []

    for cid, case in cases_by_id.items():
        entry = ledger["cases"].get(cid)
        if not entry or not entry.get("experiment_id"):
            continue
        eid = entry["experiment_id"]
        row = db.query(ExperimentRun).filter_by(id=eid).first()
        if not row or not row.evaluation_json or "PENDING" in row.evaluation_json:
            continue
        ev = json.loads(row.evaluation_json)
        records.append({
            "case_id": cid,
            "family": case.get("attack_family"),
            "difficulty": case.get("difficulty"),
            "baseline_attack_success": ev.get("baseline_attack_success"),
            "defended_attack_success": ev.get("defended_attack_success"),
            "baseline_legitimate_task_success": ev.get("baseline_legitimate_task_success"),
            "defended_legitimate_task_success": ev.get("defended_legitimate_task_success"),
            "baseline_false_refusal": ev.get("baseline_false_refusal"),
            "defended_false_refusal": ev.get("defended_false_refusal"),
            "baseline_canary_leakage_raw": ev.get("baseline_canary_leakage_raw"),
            "baseline_canary_leakage_visible": ev.get("baseline_canary_leakage_visible"),
            "defended_canary_leakage_raw": ev.get("defended_canary_leakage_raw"),
            "defended_canary_leakage_visible": ev.get("defended_canary_leakage_visible"),
            "evaluator_method": ev.get("evaluator_method"),
            "baseline_latency_ms": row.baseline_latency_ms,
            "defended_latency_ms": row.defended_latency_ms,
            "baseline_input_tokens": row.baseline_input_tokens,
            "baseline_output_tokens": row.baseline_output_tokens,
            "defended_input_tokens": row.defended_input_tokens,
            "defended_output_tokens": row.defended_output_tokens,
        })
    db.close()

    assert len(records) == 72, f"Expected 72 completed evaluations for analysis, found {len(records)}"

    adv_records = [r for r in records if r["family"] is not None]
    ben_records = [r for r in records if r["family"] is None]

    b_adv_success = sum(1 for r in adv_records if r["baseline_attack_success"] is True)
    d_adv_success = sum(1 for r in adv_records if r["defended_attack_success"] is True)
    n_adv = len(adv_records)
    b_asr = b_adv_success / n_adv if n_adv else 0.0
    d_asr = d_adv_success / n_adv if n_adv else 0.0
    asr_reduction = b_asr - d_asr

    families = ["direct_prompt_injection", "system_prompt_canary_leakage", "untrusted_code_text_injection"]
    family_stats = {}
    for fam in families:
        f_cases = [r for r in adv_records if r["family"] == fam]
        n_f = len(f_cases)
        b_s = sum(1 for r in f_cases if r["baseline_attack_success"] is True)
        d_s = sum(1 for r in f_cases if r["defended_attack_success"] is True)
        family_stats[fam] = {
            "n": n_f,
            "baseline_success": b_s,
            "baseline_asr": b_s / n_f if n_f else 0.0,
            "defended_success": d_s,
            "defended_asr": d_s / n_f if n_f else 0.0,
            "reduction": (b_s - d_s) / n_f if n_f else 0.0,
        }

    difficulties = ["easy", "moderate", "subtle"]
    diff_stats = {}
    for diff in difficulties:
        d_cases = [r for r in adv_records if r["difficulty"] == diff]
        n_d = len(d_cases)
        b_s = sum(1 for r in d_cases if r["baseline_attack_success"] is True)
        d_s = sum(1 for r in d_cases if r["defended_attack_success"] is True)
        diff_stats[diff] = {
            "n": n_d,
            "baseline_success": b_s,
            "baseline_asr": b_s / n_d if n_d else 0.0,
            "defended_success": d_s,
            "defended_asr": d_s / n_d if n_d else 0.0,
            "reduction": (b_s - d_s) / n_d if n_d else 0.0,
        }

    can_cases = [r for r in adv_records if r["family"] == "system_prompt_canary_leakage"]
    can_stats = {
        "n": len(can_cases),
        "baseline_raw_count": sum(1 for r in can_cases if r["baseline_canary_leakage_raw"] is True),
        "baseline_visible_count": sum(1 for r in can_cases if r["baseline_canary_leakage_visible"] is True),
        "defended_raw_count": sum(1 for r in can_cases if r["defended_canary_leakage_raw"] is True),
        "defended_visible_count": sum(1 for r in can_cases if r["defended_canary_leakage_visible"] is True),
    }

    n_ben = len(ben_records)
    b_legit = sum(1 for r in ben_records if r["baseline_legitimate_task_success"] is True)
    d_legit = sum(1 for r in ben_records if r["defended_legitimate_task_success"] is True)
    b_refusal = sum(1 for r in ben_records if r["baseline_false_refusal"] is True)
    d_refusal = sum(1 for r in ben_records if r["defended_false_refusal"] is True)

    ben_stats = {
        "n": n_ben,
        "baseline_legit_count": b_legit,
        "baseline_legit_rate": b_legit / n_ben if n_ben else 0.0,
        "defended_legit_count": d_legit,
        "defended_legit_rate": d_legit / n_ben if n_ben else 0.0,
        "baseline_refusal_count": b_refusal,
        "baseline_refusal_rate": b_refusal / n_ben if n_ben else 0.0,
        "defended_refusal_count": d_refusal,
        "defended_refusal_rate": d_refusal / n_ben if n_ben else 0.0,
    }

    def stat_summary(vals):
        v = [x for x in vals if x is not None]
        if not v:
            return {"mean": None, "median": None}
        return {"mean": statistics.mean(v), "median": statistics.median(v)}

    telemetry = {
        "baseline_latency_ms": stat_summary([r["baseline_latency_ms"] for r in records]),
        "defended_latency_ms": stat_summary([r["defended_latency_ms"] for r in records]),
        "baseline_input_tokens": stat_summary([r["baseline_input_tokens"] for r in records]),
        "defended_input_tokens": stat_summary([r["defended_input_tokens"] for r in records]),
        "baseline_output_tokens": stat_summary([r["baseline_output_tokens"] for r in records]),
        "defended_output_tokens": stat_summary([r["defended_output_tokens"] for r in records]),
    }

    analysis_doc = {
        "model": MODEL_TAG,
        "total_records": len(records),
        "adversarial_records": n_adv,
        "benign_records": n_ben,
        "overall_security": {
            "baseline_attack_successes": b_adv_success,
            "baseline_asr": b_asr,
            "defended_attack_successes": d_adv_success,
            "defended_asr": d_asr,
            "absolute_asr_reduction": asr_reduction,
        },
        "by_family": family_stats,
        "by_difficulty": diff_stats,
        "canary_details": can_stats,
        "benign_utility": ben_stats,
        "telemetry": telemetry,
    }

    analysis_path = GEMMA3_DIR / "analysis_summary.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis_doc, f, indent=2)

    return analysis_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PromptGuard Ai — Resilient Gemma 3 12B Cross-Model Benchmark Runner")
    parser.add_argument("--preflight", action="store_true", help="Run 5-case preflight and exit")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of cases to run in this invocation")
    parser.add_argument("--resume", action="store_true", default=True, help="Skip completed cases and continue missing generations/evaluations")
    parser.add_argument("--evaluate-pending", action="store_true", help="Scan and evaluate any cases with pending evaluations")
    parser.add_argument("--status", action="store_true", help="Print detailed collection status and exit")
    parser.add_argument("--analyze", action="store_true", help="Run analysis on completed results and print summary")
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.analyze:
        doc = analyze_results()
        print(json.dumps(doc, indent=2))
    elif args.evaluate_pending:
        asyncio.run(evaluate_pending_cases(GEMMA3_LEDGER_PATH, GEMMA3_DB_PATH))
    elif args.preflight:
        asyncio.run(run_preflight())
    else:
        asyncio.run(run_benchmark(limit=args.limit, resume=args.resume))
