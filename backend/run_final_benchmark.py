#!/usr/bin/env python3
"""PromptGuard Ai — Final Benchmark Runner.

Executes the frozen 90-case research benchmark with deterministic resume safety.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Optional

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db import SessionLocal, init_db
from app.models import ExperimentRun
from app.schemas import AttackDifficulty, AttackFamily, ExperimentRunRequest
from app.services.attacks import generate_attack
from app.services.evaluator import evaluate_experiment_run, result_to_dict
from app.services.experiments import run_paired_experiment

MANIFEST_PATH = BACKEND_DIR / "benchmark_cases" / "manifest.jsonl"
RESULTS_DIR = BACKEND_DIR / "benchmark_results"
LEDGER_PATH = RESULTS_DIR / "ledger.json"


def validate_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Validate manifest schema and exact case distribution."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    cases: list[dict[str, Any]] = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                cases.append(json.loads(line_str))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no} of {manifest_path}") from exc

    if len(cases) != 90:
        raise ValueError(f"Expected exactly 90 manifest cases, found {len(cases)}")

    adversarial = [c for c in cases if c.get("attack_family") is not None]
    benign = [c for c in cases if c.get("attack_family") is None]

    if len(adversarial) != 48:
        raise ValueError(f"Expected 48 adversarial cases, found {len(adversarial)}")
    if len(benign) != 42:
        raise ValueError(f"Expected 42 benign cases, found {len(benign)}")

    families = {
        "direct_prompt_injection": 0,
        "system_prompt_canary_leakage": 0,
        "tool_misuse_manipulation": 0,
        "untrusted_code_text_injection": 0,
    }
    family_difficulties = {fam: {"easy": 0, "moderate": 0, "subtle": 0} for fam in families}
    tool_targets = {"admin-core": 0, "issue-999": 0, "src/secrets.py": 0}

    case_ids: set[str] = set()
    for case in adversarial:
        cid = case.get("case_id")
        if not cid or cid in case_ids:
            raise ValueError(f"Duplicate or missing case_id: {cid}")
        case_ids.add(cid)

        if not case.get("original_task"):
            raise ValueError(f"Case {cid} missing original_task")

        fam = case.get("attack_family")
        if fam not in families:
            raise ValueError(f"Case {cid} has unknown attack_family: {fam}")
        families[fam] += 1

        diff = case.get("difficulty")
        if diff not in family_difficulties[fam]:
            raise ValueError(f"Case {cid} has invalid difficulty: {diff}")
        family_difficulties[fam][diff] += 1

        if fam == "tool_misuse_manipulation":
            tgt = case.get("forbidden_target")
            if tgt not in tool_targets:
                raise ValueError(f"Case {cid} has invalid forbidden_target: {tgt}")
            tool_targets[tgt] += 1

    for fam, count in families.items():
        if count != 12:
            raise ValueError(f"Family {fam} count is {count}, expected 12")
        for diff, dcount in family_difficulties[fam].items():
            if dcount != 4:
                raise ValueError(f"Family {fam} {diff} count is {dcount}, expected 4")

    if tool_targets["admin-core"] != 4 or tool_targets["issue-999"] != 4 or tool_targets["src/secrets.py"] != 4:
        raise ValueError(f"Tool target balance incorrect: {tool_targets}")

    for case in benign:
        cid = case.get("case_id")
        if not cid or cid in case_ids:
            raise ValueError(f"Duplicate or missing case_id: {cid}")
        case_ids.add(cid)
        if not case.get("original_task"):
            raise ValueError(f"Case {cid} missing original_task")
        if case.get("difficulty") is not None:
            raise ValueError(f"Benign case {cid} must have difficulty=None")

    return cases


def load_ledger(ledger_path: Path, manifest_cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Load or initialize collection ledger."""
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger = json.load(f)
    else:
        ledger = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "cases": {},
        }

    cases_map: dict[str, Any] = ledger.setdefault("cases", {})
    for case in manifest_cases:
        cid = case["case_id"]
        if cid not in cases_map:
            cases_map[cid] = {
                "case_id": cid,
                "status": "pending",
                "family": case.get("attack_family"),
                "difficulty": case.get("difficulty"),
                "original_task": case["original_task"],
                "generated_attack_prompt": None,
                "generated_attack_hash": None,
                "experiment_id": None,
                "evaluation_completed": False,
                "generation_call_count": 0,
                "timestamps": {
                    "initialized_at": datetime.now(timezone.utc).isoformat(),
                },
                "operational_error": None,
            }

    return ledger


def save_ledger(ledger_path: Path, ledger: dict[str, Any]) -> None:
    """Safely persist ledger."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = ledger_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)
    temp_path.replace(ledger_path)


def get_collection_status(ledger: dict[str, Any], db_session) -> dict[str, Any]:
    """Compute collection summary counts."""
    cases = ledger.get("cases", {})
    total = len(cases)
    complete = 0
    in_progress = 0
    failed = 0
    adv_complete = 0
    benign_complete = 0

    for cid, rec in cases.items():
        status = rec.get("status")
        is_adv = rec.get("family") is not None
        exp_id = rec.get("experiment_id")
        has_eval = rec.get("evaluation_completed", False)

        if status == "completed" and has_eval:
            complete += 1
            if is_adv:
                adv_complete += 1
            else:
                benign_complete += 1
        elif rec.get("operational_error") is not None:
            failed += 1
        elif status == "attack_generated" or (exp_id and not has_eval):
            in_progress += 1

    remaining = total - complete
    db_row_count = db_session.query(ExperimentRun).count()

    return {
        "total": total,
        "complete": complete,
        "in_progress": in_progress,
        "failed": failed,
        "remaining": remaining,
        "adversarial_complete": adv_complete,
        "adversarial_total": 48,
        "benign_complete": benign_complete,
        "benign_total": 42,
        "active_db_rows": db_row_count,
    }


def print_status(status: dict[str, Any]) -> None:
    """Print formatted summary as specified in Part 9."""
    print("Final benchmark:")
    print(f"{status['total']} total\n")
    print(f"Complete: {status['complete']}")
    print(f"In progress: {status['in_progress']}")
    print(f"Failed operationally: {status['failed']}")
    print(f"Remaining: {status['remaining']}\n")
    print(f"Adversarial complete: {status['adversarial_complete']}/{status['adversarial_total']}")
    print(f"Benign complete: {status['benign_complete']}/{status['benign_total']}\n")
    print(f"Active DB rows: {status['active_db_rows']}")


async def process_case(
    case: dict[str, Any],
    ledger: dict[str, Any],
    ledger_path: Path,
    db,
) -> bool:
    """Process a single benchmark case with resume safety."""
    cid = case["case_id"]
    rec = ledger["cases"][cid]
    is_adversarial = case.get("attack_family") is not None

    exp_id = rec.get("experiment_id")
    row = db.get(ExperimentRun, exp_id) if exp_id else None

    if row is not None:
        if is_adversarial and rec.get("generated_attack_prompt"):
            if rec["generated_attack_prompt"] != row.approved_attack_prompt:
                raise RuntimeError(
                    f"FATAL: Ledger attack prompt != DB approved_attack_prompt for case {cid}! "
                    f"Ledger hash: {rec.get('generated_attack_hash')}"
                )

        if row.evaluation_json is not None:
            if rec.get("status") != "completed" or not rec.get("evaluation_completed"):
                rec["status"] = "completed"
                rec["evaluation_completed"] = True
                save_ledger(ledger_path, ledger)
            return True

        # State C: Experiment exists in DB but evaluation is missing
        print(f"[{cid}] Evaluating existing ExperimentRun {row.id}...")
        try:
            eval_result = evaluate_experiment_run(row)
            row.evaluation_json = json.dumps(result_to_dict(eval_result))
            db.commit()
            rec["status"] = "completed"
            rec["evaluation_completed"] = True
            rec.setdefault("timestamps", {})["evaluation_completed_at"] = datetime.now(timezone.utc).isoformat()
            save_ledger(ledger_path, ledger)
            print(f"[{cid}] Evaluation persisted successfully.")
            return True
        except Exception as exc:
            rec["operational_error"] = f"Evaluation failed: {exc}"
            save_ledger(ledger_path, ledger)
            raise

    if is_adversarial:
        # Check if attack already generated (State B)
        if rec.get("generated_attack_prompt"):
            attack_prompt = rec["generated_attack_prompt"]
            attack_hash = rec.get("generated_attack_hash") or hashlib.sha256(attack_prompt.encode("utf-8")).hexdigest()
            rec["generated_attack_hash"] = attack_hash
            print(f"[{cid}] Reusing existing saved attack prompt (hash: {attack_hash[:12]}...)")
        else:
            # State A: Generate attack once
            print(f"[{cid}] Generating attack prompt (Family: {case['attack_family']}, Difficulty: {case['difficulty']})...")
            fam = AttackFamily(case["attack_family"])
            diff = AttackDifficulty(case["difficulty"])
            try:
                gen_result = await generate_attack(
                    original_task=case["original_task"],
                    attack_family=fam,
                    difficulty=diff,
                )
            except Exception as exc:
                rec["operational_error"] = f"Attack generation failed: {exc}"
                save_ledger(ledger_path, ledger)
                raise

            attack_prompt = gen_result.attack_prompt
            rec["generated_attack_prompt"] = attack_prompt
            rec["generated_attack_hash"] = hashlib.sha256(attack_prompt.encode("utf-8")).hexdigest()
            rec["generation_call_count"] = rec.get("generation_call_count", 0) + 1
            rec["status"] = "attack_generated"
            rec.setdefault("timestamps", {})["attack_generated_at"] = datetime.now(timezone.utc).isoformat()

            # CRITICAL RULE: Persist exact generated attack prompt to ledger BEFORE starting paired experiment!
            save_ledger(ledger_path, ledger)
            print(f"[{cid}] Attack prompt saved to ledger (hash: {rec['generated_attack_hash'][:12]}...).")

        # Run paired experiment
        print(f"[{cid}] Running paired experiment (adversarial)...")
        exp_req = ExperimentRunRequest(
            original_task=case["original_task"],
            attack_prompt=attack_prompt,
            attack_family=AttackFamily(case["attack_family"]),
            generation_source="generated",
            attack_edited=False,
        )
        try:
            exp_resp = await run_paired_experiment(exp_req, db)
        except Exception as exc:
            rec["operational_error"] = f"Paired experiment execution failed: {exc}"
            save_ledger(ledger_path, ledger)
            raise

        rec["experiment_id"] = exp_resp.experiment_id
        rec.setdefault("timestamps", {})["experiment_completed_at"] = datetime.now(timezone.utc).isoformat()
        save_ledger(ledger_path, ledger)

        # Evaluate and persist
        row = db.get(ExperimentRun, exp_resp.experiment_id)
        if not row:
            raise RuntimeError(f"ExperimentRun {exp_resp.experiment_id} not found in DB immediately after run!")

        print(f"[{cid}] Evaluating paired experiment...")
        try:
            eval_result = evaluate_experiment_run(row)
            row.evaluation_json = json.dumps(result_to_dict(eval_result))
            db.commit()
        except Exception as exc:
            rec["operational_error"] = f"Evaluation failed: {exc}"
            save_ledger(ledger_path, ledger)
            raise

        rec["status"] = "completed"
        rec["evaluation_completed"] = True
        rec["operational_error"] = None
        rec.setdefault("timestamps", {})["evaluation_completed_at"] = datetime.now(timezone.utc).isoformat()
        save_ledger(ledger_path, ledger)
        print(f"[{cid}] Completed and persisted successfully.")
        return True

    else:
        # Benign control case: NO attack generation!
        print(f"[{cid}] Running benign paired experiment (no attack generation)...")
        rec["generation_call_count"] = 0
        exp_req = ExperimentRunRequest(
            original_task=case["original_task"],
            attack_prompt=case["original_task"],
            attack_family=None,
            generation_source="manual",
            attack_edited=False,
        )
        try:
            exp_resp = await run_paired_experiment(exp_req, db)
        except Exception as exc:
            rec["operational_error"] = f"Paired experiment execution failed: {exc}"
            save_ledger(ledger_path, ledger)
            raise

        rec["experiment_id"] = exp_resp.experiment_id
        rec.setdefault("timestamps", {})["experiment_completed_at"] = datetime.now(timezone.utc).isoformat()
        save_ledger(ledger_path, ledger)

        # Evaluate and persist
        row = db.get(ExperimentRun, exp_resp.experiment_id)
        if not row:
            raise RuntimeError(f"ExperimentRun {exp_resp.experiment_id} not found in DB immediately after run!")

        print(f"[{cid}] Evaluating benign experiment...")
        try:
            eval_result = evaluate_experiment_run(row)
            row.evaluation_json = json.dumps(result_to_dict(eval_result))
            db.commit()
        except Exception as exc:
            rec["operational_error"] = f"Evaluation failed: {exc}"
            save_ledger(ledger_path, ledger)
            raise

        rec["status"] = "completed"
        rec["evaluation_completed"] = True
        rec["operational_error"] = None
        rec.setdefault("timestamps", {})["evaluation_completed_at"] = datetime.now(timezone.utc).isoformat()
        save_ledger(ledger_path, ledger)
        print(f"[{cid}] Completed and persisted successfully.")
        return True


async def run_benchmark(
    manifest_cases: list[dict[str, Any]],
    ledger: dict[str, Any],
    ledger_path: Path,
    case_id: Optional[str] = None,
    family: Optional[str] = None,
    limit: Optional[int] = None,
) -> None:
    """Iterate and run benchmark cases according to CLI args."""
    init_db()
    db = SessionLocal()

    try:
        filtered_cases = manifest_cases
        if case_id:
            filtered_cases = [c for c in filtered_cases if c["case_id"] == case_id]
            if not filtered_cases:
                print(f"Error: Case ID {case_id} not found in manifest.")
                sys.exit(1)

        if family:
            if family.lower() == "benign":
                filtered_cases = [c for c in filtered_cases if c.get("attack_family") is None]
            else:
                filtered_cases = [c for c in filtered_cases if c.get("attack_family") == family]

        completed_in_this_run = 0
        for case in filtered_cases:
            cid = case["case_id"]
            rec = ledger["cases"][cid]

            # If already completed, check consistency and skip
            if rec.get("status") == "completed" and rec.get("evaluation_completed"):
                exp_id = rec.get("experiment_id")
                if exp_id:
                    row = db.get(ExperimentRun, exp_id)
                    if row and row.evaluation_json:
                        if case.get("attack_family") is not None and rec.get("generated_attack_prompt"):
                            if rec["generated_attack_prompt"] != row.approved_attack_prompt:
                                raise RuntimeError(
                                    f"FATAL: Ledger attack prompt != DB approved_attack_prompt for case {cid}!"
                                )
                        continue

            if limit is not None and completed_in_this_run >= limit:
                print(f"\nReached batch limit of {limit} cases. Stopping.")
                break

            print(f"\n--- Processing Case {cid} ({case.get('attack_family') or 'benign'}) ---")
            await process_case(case, ledger, ledger_path, db)
            completed_in_this_run += 1

        print(f"\nBatch finished. Completed {completed_in_this_run} cases in this run.")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="PromptGuard Ai Final Benchmark Runner")
    parser.add_argument("--status", action="store_true", help="Display benchmark collection status and exit")
    parser.add_argument("--case-id", type=str, default=None, help="Execute a single case by case_id")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases to execute")
    parser.add_argument("--resume", action="store_true", help="Resume collection from existing ledger")
    parser.add_argument("--family", type=str, default=None, help="Filter cases by attack family (or 'benign')")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="Path to manifest.jsonl")
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH, help="Path to ledger.json")

    args = parser.parse_args()

    manifest_cases = validate_manifest(args.manifest)
    ledger = load_ledger(args.ledger, manifest_cases)

    init_db()
    db = SessionLocal()
    try:
        if args.status:
            status = get_collection_status(ledger, db)
            print_status(status)
            return
    finally:
        db.close()

    if not (args.resume or args.case_id or args.limit is not None):
        print("No execution action specified. Use --status, --resume, --case-id, or --limit.")
        print("\nCurrent status:")
        init_db()
        db = SessionLocal()
        try:
            status = get_collection_status(ledger, db)
            print_status(status)
        finally:
            db.close()
        return

    asyncio.run(
        run_benchmark(
            manifest_cases=manifest_cases,
            ledger=ledger,
            ledger_path=args.ledger,
            case_id=args.case_id,
            family=args.family,
            limit=args.limit,
        )
    )

    init_db()
    db = SessionLocal()
    try:
        print("\nUpdated collection status:")
        status = get_collection_status(ledger, db)
        print_status(status)
    finally:
        db.close()


if __name__ == "__main__":
    main()
