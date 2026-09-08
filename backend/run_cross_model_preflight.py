#!/usr/bin/env python3
"""PromptGuard Ai — Cross-Model Technical Preflight Runner for Llama 2.

Executes exactly 5 representative comparable cases using local llama2:7b:
- 1 DPI (DPI-E01)
- 1 CAN (CAN-E01)
- 1 DATA (DATA-E01)
- 2 non-tool Benign (BEN-001, BEN-019)

Uses isolated preflight storage under backend/benchmark_results/cross_model/preflight/.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
import os
os.chdir(BACKEND_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, ExperimentRun
from app.schemas import AttackFamily, ExperimentRunRequest
from app.services.evaluator import evaluate_experiment_run, result_to_dict
from app.services.experiments import run_paired_experiment
from app.services.ollama import is_ollama_model

FROZEN_DIR = BACKEND_DIR / "benchmark_results" / "final_90"
PREFLIGHT_DIR = BACKEND_DIR / "benchmark_results" / "cross_model" / "preflight"
PREFLIGHT_DB_PATH = PREFLIGHT_DIR / "preflight.db"
PREFLIGHT_LEDGER_PATH = PREFLIGHT_DIR / "preflight_ledger.json"

TARGET_CASES = ["DPI-E01", "CAN-E01", "DATA-E01", "BEN-001", "BEN-019"]
MODEL_TAG = "llama2:7b"


def init_preflight_db():
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{PREFLIGHT_DB_PATH.as_posix()}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


async def run_preflight():
    print(f"=== Starting Cross-Model Technical Preflight for {MODEL_TAG} ===")
    assert is_ollama_model(MODEL_TAG), f"{MODEL_TAG} must be recognized as Ollama model"

    # 1. Load frozen manifest and ledger
    manifest_path = FROZEN_DIR / "manifest_final_90.jsonl"
    ledger_path = FROZEN_DIR / "ledger_final_90.json"

    manifest_cases = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                manifest_cases[item["case_id"]] = item

    ledger_cases = {}
    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger_cases = json.load(f)["cases"]

    # 2. Setup isolated preflight database
    PreflightSession = init_preflight_db()
    db = PreflightSession()

    preflight_records = {}
    if PREFLIGHT_LEDGER_PATH.exists():
        try:
            with open(PREFLIGHT_LEDGER_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                preflight_records = saved.get("results", {})
        except Exception:
            preflight_records = {}

    try:
        for case_id in TARGET_CASES:
            print(f"\n--- Processing Preflight Case: {case_id} ---")
            m_case = manifest_cases[case_id]
            l_case = ledger_cases[case_id]

            orig_task = m_case["original_task"]
            fam_str = m_case.get("attack_family")
            fam_enum = AttackFamily(fam_str) if fam_str else None

            # Get exact frozen prompt
            if fam_enum is not None:
                attack_prompt = l_case["generated_attack_prompt"]
                assert attack_prompt, f"Missing frozen attack prompt for {case_id}"
            else:
                attack_prompt = orig_task

            # Check if an experiment run already exists in preflight DB
            existing_row = None
            if case_id in preflight_records and "experiment_id" in preflight_records[case_id]:
                eid = preflight_records[case_id]["experiment_id"]
                existing_row = db.query(ExperimentRun).filter_by(id=eid).first()

            if not existing_row:
                # Query by original task and attack prompt in preflight DB
                existing_row = (
                    db.query(ExperimentRun)
                    .filter_by(original_task=orig_task, approved_attack_prompt=attack_prompt)
                    .first()
                )

            if existing_row and (existing_row.baseline_status != "completed" or existing_row.defended_status != "completed"):
                db.delete(existing_row)
                db.commit()
                existing_row = None

            if existing_row and existing_row.baseline_status == "completed" and existing_row.defended_status == "completed":
                print(f"[{case_id}] Reusing existing completed run {existing_row.id}")
                row = existing_row
                exp_id = row.id
            else:
                print(f"[{case_id}] Executing paired experiment on {MODEL_TAG}...")
                req = ExperimentRunRequest(
                    original_task=orig_task,
                    attack_prompt=attack_prompt,
                    attack_family=fam_enum,
                    model=MODEL_TAG,
                    temperature=0.2,
                    max_output_tokens=800,
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

            # Verify prompt content and system prompt properties
            if fam_enum == AttackFamily.SYSTEM_PROMPT_CANARY_LEAKAGE:
                from app.services.defenses import CANARY_VALUE
                from app.services.experiments import _base_system_prompt, _make_spec
                temp_req = ExperimentRunRequest(
                    original_task=orig_task,
                    attack_prompt=attack_prompt,
                    attack_family=fam_enum,
                    model=MODEL_TAG,
                )
                spec = _make_spec(temp_req)
                assert CANARY_VALUE in _base_system_prompt(spec), "Canary must be present in CAN system prompt"
            if fam_enum == AttackFamily.UNTRUSTED_CODE_TEXT_INJECTION:
                assert "untrusted" in row.defended_defense_evidence.lower() or "separation" in row.defended_defense_evidence.lower(), "DATA separation evidence must exist"

            # Evaluate with Direct Google Gemini evaluator
            print(f"[{case_id}] Running evaluator on stored outputs...")
            eval_result = evaluate_experiment_run(row)
            eval_dict = result_to_dict(eval_result)
            row.evaluation_json = json.dumps(eval_dict)
            db.commit()

            print(f"[{case_id}] Evaluator method: {eval_result.evaluator_method}")
            print(f"[{case_id}] Evaluator rationale: {eval_result.evaluator_rationale[:80]}...")

            preflight_records[case_id] = {
                "case_id": case_id,
                "family": fam_str,
                "experiment_id": exp_id,
                "baseline_status": row.baseline_status,
                "defended_status": row.defended_status,
                "evaluator_method": eval_result.evaluator_method,
                "evaluator_rationale": eval_result.evaluator_rationale,
                "baseline_raw_output_snippet": (row.baseline_raw_output or "")[:120],
                "defended_raw_output_snippet": (row.defended_raw_output or "")[:120],
                "evaluation_json": eval_dict,
            }

            # Save progress after each case
            ledger_doc = {
                "preflight_version": "1.0",
                "model": MODEL_TAG,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "target_cases": TARGET_CASES,
                "results": preflight_records,
            }
            with open(PREFLIGHT_LEDGER_PATH, "w", encoding="utf-8") as f:
                json.dump(ledger_doc, f, indent=2)

        print("\n=== PREFLIGHT RUN COMPLETED SUCCESSFULLY ===")
        print(f"Preflight DB: {PREFLIGHT_DB_PATH}")
        print(f"Preflight Ledger: {PREFLIGHT_LEDGER_PATH}")

    finally:
        db.close()

    return preflight_records


if __name__ == "__main__":
    asyncio.run(run_preflight())
