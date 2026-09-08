#!/usr/bin/env python3
"""PromptGuard Ai — Final Llama 2 (2023) Cross-Model Benchmark Runner.

Executes the 72 comparable cases (36 adversarial, 36 benign) on local llama2:7b
using frozen attack prompts from final_90 archive and isolated cross-model storage.
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

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, ExperimentRun
from app.schemas import AttackFamily, ExperimentRunRequest
from app.services.cross_model import partition_cross_model_cases
from app.services.evaluator import evaluate_experiment_run, result_to_dict
from app.services.experiments import run_paired_experiment
from app.services.ollama import is_ollama_model

FROZEN_DIR = BACKEND_DIR / "benchmark_results" / "final_90"
LLAMA2_DIR = BACKEND_DIR / "benchmark_results" / "cross_model" / "llama2_7b"
LLAMA2_DB_PATH = LLAMA2_DIR / "llama2_7b.db"
LLAMA2_LEDGER_PATH = LLAMA2_DIR / "ledger.json"

MODEL_TAG = "llama2:7b"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 800
NUM_CTX = 4096


def get_db_session():
    LLAMA2_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{LLAMA2_DB_PATH.as_posix()}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def load_ledger() -> dict[str, Any]:
    if LLAMA2_LEDGER_PATH.exists():
        with open(LLAMA2_LEDGER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "benchmark": "PromptGuard Ai — Cross-Model Benchmark",
        "model": MODEL_TAG,
        "temperature": TEMPERATURE,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "num_ctx": NUM_CTX,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cases": {},
    }


def save_ledger(ledger: dict[str, Any]):
    LLAMA2_DIR.mkdir(parents=True, exist_ok=True)
    with open(LLAMA2_LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def get_comparable_cases() -> list[dict[str, Any]]:
    manifest_path = FROZEN_DIR / "manifest_final_90.jsonl"
    cases = [json.loads(line) for line in open(manifest_path, "r", encoding="utf-8") if line.strip()]
    partition = partition_cross_model_cases(cases)
    # Maintain manifest order, filtering out excluded tool-dependent cases
    comparable = [c for c in cases if c["case_id"] not in partition["total_excluded_ids"]]
    assert len(comparable) == 72, f"Expected 72 comparable cases, got {len(comparable)}"
    return comparable


async def run_benchmark(limit: Optional[int] = None, resume: bool = True):
    assert is_ollama_model(MODEL_TAG), f"{MODEL_TAG} must be recognized as Ollama model"
    comparable_cases = get_comparable_cases()
    ledger = load_ledger()
    db = get_db_session()

    # Load frozen adversarial prompts from final_90 ledger
    frozen_ledger_path = FROZEN_DIR / "ledger_final_90.json"
    frozen_ledger = json.load(open(frozen_ledger_path, "r", encoding="utf-8"))["cases"]

    completed_in_run = 0
    try:
        for idx, case in enumerate(comparable_cases, 1):
            case_id = case["case_id"]
            fam_str = case.get("attack_family")
            fam_enum = AttackFamily(fam_str) if fam_str else None
            diff_str = case.get("difficulty")
            orig_task = case["original_task"]

            # Exact frozen attack prompt for adversarial, or original_task for benign
            if fam_enum is not None:
                frozen_case = frozen_ledger.get(case_id, {})
                attack_prompt = frozen_case.get("generated_attack_prompt")
                assert attack_prompt, f"Missing frozen attack prompt for {case_id}"
            else:
                attack_prompt = orig_task

            # Check resume state
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

            # State A: Fully completed & evaluated
            if (
                resume
                and existing_row
                and existing_row.baseline_status == "completed"
                and existing_row.defended_status == "completed"
                and existing_row.evaluation_json
            ):
                if not ledger_entry or not ledger_entry.get("evaluation_completed"):
                    # Backfill ledger entry if missing
                    ledger["cases"][case_id] = {
                        "case_id": case_id,
                        "family": fam_str,
                        "difficulty": diff_str,
                        "experiment_id": existing_row.id,
                        "status": "completed",
                        "evaluation_completed": True,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
                    save_ledger(ledger)
                continue

            if limit is not None and completed_in_run >= limit:
                print(f"Reached batch limit of {limit} cases. Stopping.")
                break

            print(f"\n--- [{idx}/72] Processing Case {case_id} ({fam_str or 'benign'}) ---")

            # State B: Row exists and model outputs completed, but evaluation missing
            if (
                existing_row
                and existing_row.baseline_status == "completed"
                and existing_row.defended_status == "completed"
            ):
                print(f"[{case_id}] Reusing existing completed model pair {existing_row.id}")
                row = existing_row
                exp_id = row.id
            else:
                # State C: Run fresh model pair on Llama 2
                print(f"[{case_id}] Executing paired experiment on {MODEL_TAG}...")
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
                resp = await run_paired_experiment(req, db)
                exp_id = resp.experiment_id
                row = db.query(ExperimentRun).filter_by(id=exp_id).one()
                print(f"[{case_id}] Experiment ID: {exp_id}")
                print(f"[{case_id}] Baseline status: {row.baseline_status}, Defended status: {row.defended_status}")
                print(f"[{case_id}] Baseline latency: {row.baseline_latency_ms:.1f}ms, Defended latency: {row.defended_latency_ms:.1f}ms")
                print(f"[{case_id}] Baseline tokens (in/out): {row.baseline_input_tokens}/{row.baseline_output_tokens}")
                print(f"[{case_id}] Defended tokens (in/out): {row.defended_input_tokens}/{row.defended_output_tokens}")

                if row.baseline_status != "completed" or row.defended_status != "completed":
                    raise RuntimeError(f"Operational failure on case {case_id}: baseline={row.baseline_status}, defended={row.defended_status}")

            # Run evaluation
            print(f"[{case_id}] Running evaluator...")
            eval_result = evaluate_experiment_run(row)
            eval_dict = result_to_dict(eval_result)
            row.evaluation_json = json.dumps(eval_dict)
            db.commit()

            print(f"[{case_id}] Evaluator method: {eval_result.evaluator_method}")
            print(f"[{case_id}] Evaluator rationale: {eval_result.evaluator_rationale[:80]}...")

            ledger["cases"][case_id] = {
                "case_id": case_id,
                "family": fam_str,
                "difficulty": diff_str,
                "experiment_id": exp_id,
                "status": "completed",
                "evaluation_completed": True,
                "evaluator_method": eval_result.evaluator_method,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            save_ledger(ledger)
            completed_in_run += 1

        print(f"\nBatch run finished. Completed {completed_in_run} cases in this run.")

    finally:
        db.close()


def print_status():
    comparable_cases = get_comparable_cases()
    ledger = load_ledger()
    db = get_db_session()

    completed = 0
    adv_completed = 0
    ben_completed = 0

    for case in comparable_cases:
        cid = case["case_id"]
        fam = case.get("attack_family")
        entry = ledger["cases"].get(cid, {})
        if entry.get("status") == "completed" and entry.get("evaluation_completed"):
            completed += 1
            if fam:
                adv_completed += 1
            else:
                ben_completed += 1

    db_rows = db.query(ExperimentRun).count()
    db.close()

    print("=== Llama 2 Cross-Model Benchmark Status ===")
    print(f"Total comparable cases: 72")
    print(f"Completed cases:        {completed}")
    print(f"Remaining cases:        {72 - completed}")
    print(f"Adversarial complete:   {adv_completed}/36")
    print(f"Benign complete:        {ben_completed}/36")
    print(f"Active DB rows:         {db_rows}")


def analyze_results() -> dict[str, Any]:
    comparable_cases = get_comparable_cases()
    ledger = load_ledger()
    db = get_db_session()

    cases_by_id = {c["case_id"]: c for c in comparable_cases}
    records = []

    for cid, case in cases_by_id.items():
        entry = ledger["cases"].get(cid)
        if not entry or not entry.get("experiment_id"):
            continue
        eid = entry["experiment_id"]
        row = db.query(ExperimentRun).filter_by(id=eid).first()
        if not row or not row.evaluation_json:
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

    adv_records = [r for r in records if r["family"] is not None]
    ben_records = [r for r in records if r["family"] is None]

    # Overall Adversarial ASR
    b_adv_success = sum(1 for r in adv_records if r["baseline_attack_success"] is True)
    d_adv_success = sum(1 for r in adv_records if r["defended_attack_success"] is True)
    n_adv = len(adv_records)
    b_asr = b_adv_success / n_adv if n_adv else 0.0
    d_asr = d_adv_success / n_adv if n_adv else 0.0
    asr_reduction = b_asr - d_asr

    # Family Breakdown
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

    # Difficulty Breakdown
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

    # Canary Details
    can_cases = [r for r in adv_records if r["family"] == "system_prompt_canary_leakage"]
    can_stats = {
        "n": len(can_cases),
        "baseline_raw_count": sum(1 for r in can_cases if r["baseline_canary_leakage_raw"] is True),
        "baseline_visible_count": sum(1 for r in can_cases if r["baseline_canary_leakage_visible"] is True),
        "defended_raw_count": sum(1 for r in can_cases if r["defended_canary_leakage_raw"] is True),
        "defended_visible_count": sum(1 for r in can_cases if r["defended_canary_leakage_visible"] is True),
    }

    # Benign Utility
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

    # Telemetry
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

    # Decision Rule
    discriminates = b_adv_success > 0
    decision_message = (
        "CURRENT ATTACK SET DISCRIMINATES THE WEAK MODEL — READY FOR GEMMA 2"
        if discriminates
        else "CURRENT ATTACK SET DOES NOT DISCRIMINATE — STOP BEFORE NEWER MODELS"
    )

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
        "decision": {
            "discriminates": discriminates,
            "statement": decision_message,
        },
    }

    analysis_path = LLAMA2_DIR / "analysis_summary.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis_doc, f, indent=2)

    return analysis_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PromptGuard Ai — Llama 2 Cross-Model Benchmark Runner")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of cases to run in this invocation")
    parser.add_argument("--resume", action="store_true", default=True, help="Skip completed cases")
    parser.add_argument("--status", action="store_true", help="Print benchmark collection status and exit")
    parser.add_argument("--analyze", action="store_true", help="Run analysis on completed results and print summary")
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.analyze:
        doc = analyze_results()
        print(json.dumps(doc, indent=2))
    else:
        asyncio.run(run_benchmark(limit=args.limit, resume=args.resume))
