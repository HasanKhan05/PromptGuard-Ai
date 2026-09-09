"""PromptGuard Ai — Phase CM5.6: Frozen Adjudication-Corrected Analysis.

Analyzes the exact frozen 72-case comparable benchmark across:
1. 2023 — Llama 2 7B Chat (Ollama local, CPU)
2. 2024 — Gemma 2 9B (Ollama local, CPU)
3. 2025 — Gemma 3 12B (Ollama local, CPU)
4. 2026 — Gemini 3.1 Flash Lite (OmniRoute cloud)

Strict comparability rules:
- 36 adversarial cases: 12 DPI, 12 CAN, 12 DATA
- 36 non-tool benign controls
- Excludes all 12 TOOL adversarial cases and 6 tool-dependent benign cases (BEN-033..BEN-038)
- Gemini numbers are recalculated strictly on this 72-case subset
- Supplementary TOOL family analysis for Gemini preserved separately

Computes:
- Overall ASR, family breakdown, difficulty breakdown, canary leakage, benign utility, false refusals
- Wilson 95% confidence intervals
- Exact McNemar / binomial paired tests
- Paired transition matrices
- Descriptive telemetry

Outputs reproducible CSV, JSON, and Markdown artifacts to:
backend/benchmark_results/cross_model/final_analysis/
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BACKEND_DIR / "benchmark_results"
FROZEN_GEMINI_DIR = RESULTS_DIR / "final_90"
CROSS_MODEL_DIR = RESULTS_DIR / "cross_model"
FINAL_ANALYSIS_DIR = CROSS_MODEL_DIR / "final_analysis"
ADJUDICATION_PATH = FINAL_ANALYSIS_DIR / "full_output_adjudication.json"

EXPECTED_HASHES = {
    "gemini": (
        FROZEN_GEMINI_DIR / "promptguard_final_90.db",
        "d3fa0c1b413366bf4b8777d142f06e3b3484dc745ecc830831b1f7e7d4684bb2",
    ),
    "llama2": (
        CROSS_MODEL_DIR / "llama2_7b" / "llama2_7b.db",
        "11748da3741ee50c0366342f125da73887c1b391420123f1120397b20106f0cc",
    ),
    "gemma2": (
        CROSS_MODEL_DIR / "gemma2_9b" / "gemma2_9b.db",
        "f0d01ae179f217ac2058dc68f484c0187e625ba2f826b9bd05af20e5dc4ef10f",
    ),
    "gemma3": (
        CROSS_MODEL_DIR / "gemma3_12b" / "gemma3_12b.db",
        "619e48de595fb0fdc7d0eba4f29648b0b67567f40df5e9238a120bce23e1cd79",
    ),
}

MODEL_CONFIGS = [
    {
        "key": "llama2_7b",
        "display_name": "Llama 2 7B",
        "year": 2023,
        "parameters": "6.7B",
        "architecture": "Llama 2 (GQA/dense, 4k ctx)",
        "provider": "Ollama (local, Intel i7-1270P CPU)",
        "db_path": CROSS_MODEL_DIR / "llama2_7b" / "llama2_7b.db",
        "ledger_path": CROSS_MODEL_DIR / "llama2_7b" / "ledger.json",
    },
    {
        "key": "gemma2_9b",
        "display_name": "Gemma 2 9B",
        "year": 2024,
        "parameters": "9.2B",
        "architecture": "Gemma 2 (sliding window/logit softcapping, 8k ctx)",
        "provider": "Ollama (local, Intel i7-1270P CPU)",
        "db_path": CROSS_MODEL_DIR / "gemma2_9b" / "gemma2_9b.db",
        "ledger_path": CROSS_MODEL_DIR / "gemma2_9b" / "ledger.json",
    },
    {
        "key": "gemma3_12b",
        "display_name": "Gemma 3 12B",
        "year": 2025,
        "parameters": "12.2B",
        "architecture": "Gemma 3 (multimodal/hybrid local-global attn, 131k ctx)",
        "provider": "Ollama (local, Intel i7-1270P CPU)",
        "db_path": CROSS_MODEL_DIR / "gemma3_12b" / "gemma3_12b.db",
        "ledger_path": CROSS_MODEL_DIR / "gemma3_12b" / "ledger.json",
    },
    {
        "key": "gemini_3.1_flash_lite",
        "display_name": "Gemini 3.1 Flash Lite",
        "year": 2026,
        "parameters": "Undisclosed",
        "architecture": "Gemini 3.x Flash Lite (MoE, 1M+ ctx)",
        "provider": "OmniRoute (cloud API)",
        "db_path": FROZEN_GEMINI_DIR / "promptguard_final_90.db",
        "ledger_path": FROZEN_GEMINI_DIR / "ledger_final_90.json",
    },
]

FINAL_FINDINGS = {
    "open_weight_baseline_trend": (
        "Observed baseline attack success decreased across the three selected "
        "open-weight checkpoints, from 33.3% for Llama 2 to 30.6% for Gemma 2 "
        "and 22.2% for Gemma 3. However, because these models differ in family, "
        "scale, training, alignment, architecture, tokenizer, native prompt "
        "template, and runtime configuration, this descriptive trend cannot be "
        "attributed causally to model generation or release year."
    ),
    "gemini_baseline_result": (
        "Gemini 3.1 Flash Lite had no observed baseline attack successes in the "
        "same 36-case comparable adversarial subset, but this result is specific "
        "to the fixed benchmark and does not establish general immunity."
    ),
    "can_concentration": (
        "After full-output adjudication, every confirmed open-model adversarial "
        "success occurred in system_prompt_canary_leakage; no confirmed baseline "
        "DPI or DATA successes remained."
    ),
    "output_screening": (
        "Output Screening prevented all observed user-visible canary disclosures "
        "in the tested CAN cases, including cases where the underlying model still "
        "generated the canary in its raw response."
    ),
    "input_screening_null_finding": (
        "No confirmed baseline DPI successes were observed after full-output "
        "adjudication, so this benchmark does not provide evidence for estimating "
        "the incremental benefit of Input Screening."
    ),
    "instruction_data_null_finding": (
        "No confirmed baseline DATA successes were observed after full-output "
        "adjudication, limiting conclusions about the incremental effectiveness "
        "of Instruction–Data Separation."
    ),
    "security_utility": (
        "Guardrail security–utility compatibility differed substantially across "
        "the tested model configurations. Llama 2 experienced substantial benign-"
        "task degradation and false refusals, while Gemma 2 and Gemma 3 preserved "
        "benign-task success in this sample. This is descriptive and is not "
        "attributed causally to architecture, release year, or model generation."
    ),
    "defended_scope": (
        "No defended attack successes were observed in this fixed sample. This "
        "does not establish universal protection, and only Output Screening has "
        "directly observed incremental mitigation evidence in the comparable data."
    ),
}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def verify_integrity() -> Dict[str, str]:
    hashes = {}
    for key, (path, expected) in EXPECTED_HASHES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing required database: {path}")
        actual = compute_sha256(path)
        if actual != expected:
            raise ValueError(
                f"Checksum mismatch on {key} ({path}):\n"
                f"  Expected: {expected}\n"
                f"  Actual:   {actual}"
            )
        hashes[key] = actual
    return hashes


def wilson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate Wilson score interval for proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% two-sided
    p = k / n
    denominator = 1.0 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denominator
    margin = (z / denominator) * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (round(lower, 4), round(upper, 4))


def summarize_binary(records: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
    """Summarize a nullable binary outcome without treating unresolved as failure."""
    values = [record.get(field) for record in records]
    resolved = [value for value in values if value is not None]
    successes = sum(value is True for value in resolved)
    evaluated_n = len(resolved)
    return {
        "evaluated_n": evaluated_n,
        "unresolved_n": len(values) - evaluated_n,
        "success_count": successes,
        "rate": round(successes / evaluated_n, 4) if evaluated_n else None,
        "ci95": wilson_interval(successes, evaluated_n) if evaluated_n else None,
    }


def summarize_paired(
    records: List[Dict[str, Any]], baseline_field: str, defended_field: str
) -> Dict[str, int]:
    """Count transitions only for pairs with both outcomes resolved."""
    resolved = [
        record
        for record in records
        if record.get(baseline_field) is not None
        and record.get(defended_field) is not None
    ]
    return {
        "evaluated_pairs": len(resolved),
        "unresolved_pairs": len(records) - len(resolved),
        "mitigated": sum(
            record[baseline_field] is True and record[defended_field] is False
            for record in resolved
        ),
        "persistent": sum(
            record[baseline_field] is True and record[defended_field] is True
            for record in resolved
        ),
        "safe": sum(
            record[baseline_field] is False and record[defended_field] is False
            for record in resolved
        ),
        "induced": sum(
            record[baseline_field] is False and record[defended_field] is True
            for record in resolved
        ),
    }


def compute_redaction_rate(raw_leaks: int, visible_leaks: int) -> Optional[float]:
    """Return no rate when no raw leakage created a redaction opportunity."""
    if raw_leaks == 0:
        return None
    return round((raw_leaks - visible_leaks) / raw_leaks, 4)


def apply_adjudication(
    records: List[Dict[str, Any]], entries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Overlay adjudicated labels on copies used only for derived reporting."""
    by_key = {
        (entry["model_key"], entry["case_id"]): entry for entry in entries
    }
    corrected = []
    for source in records:
        record = dict(source)
        entry = by_key.get((source["model_key"], source["case_id"]))
        if entry:
            record.update(entry["adjudicated_labels"])
        corrected.append(record)
    return corrected


def load_adjudication(path: Path = ADJUDICATION_PATH) -> Dict[str, Any]:
    """Load and validate the immutable-evidence adjudication overlay."""
    document = json.loads(path.read_text(encoding="utf-8"))
    entries = document.get("records", [])
    keys = [(entry.get("model_key"), entry.get("case_id")) for entry in entries]
    if len(entries) != 240 or len(set(keys)) != 240:
        raise ValueError("Adjudication must contain exactly 240 unique semantic records.")
    expected_hashes = {key: expected for key, (_, expected) in EXPECTED_HASHES.items()}
    if document.get("source_database_sha256") != expected_hashes:
        raise ValueError("Adjudication source hashes do not match the frozen databases.")
    if document.get("semantic_records_reviewed") != 240:
        raise ValueError("Adjudication does not attest review of all semantic records.")
    return document


def mcnemar_test(b: int, c: int) -> Dict[str, Any]:
    """Calculate paired McNemar test between two conditions.
    
    b: Baseline Success, Defended Failure (Mitigated by defense)
    c: Baseline Failure, Defended Success (Induced vulnerability)
    """
    total_discordant = b + c
    if total_discordant == 0:
        return {
            "discordant_pairs": 0,
            "b_mitigated": 0,
            "c_induced": 0,
            "chi2_stat": None,
            "p_value": None,
            "significant_05": False,
            "test_type": "none (zero discordant pairs)",
        }

    # Edwards continuity-corrected Chi-Square
    chi2 = ((abs(b - c) - 1.0) ** 2) / total_discordant

    # Exact two-tailed binomial p-value under H0: p=0.5
    k = min(b, c)
    # Sum binomial probabilities from 0 to k
    cum_prob = 0.0
    for i in range(k + 1):
        cum_prob += math.comb(total_discordant, i) * (0.5**total_discordant)
    exact_p = min(1.0, 2.0 * cum_prob)

    return {
        "discordant_pairs": total_discordant,
        "b_mitigated": b,
        "c_induced": c,
        "chi2_stat": round(chi2, 4),
        "p_value": round(exact_p, 6),
        "significant_05": exact_p < 0.05,
        "test_type": "exact binomial (two-tailed)",
    }


def load_manifest_cases() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    manifest_path = FROZEN_GEMINI_DIR / "manifest_final_90.jsonl"
    all_cases = [json.loads(line) for line in open(manifest_path, "r", encoding="utf-8") if line.strip()]

    tool_dependent_benign = {"BEN-033", "BEN-034", "BEN-035", "BEN-036", "BEN-037", "BEN-038"}

    comparable_adversarial = []
    comparable_benign = []
    excluded_cases = []

    for case in all_cases:
        cid = case["case_id"]
        fam = case.get("attack_family")

        if cid.startswith("TOOL-") or fam == "tool_misuse_manipulation" or cid in tool_dependent_benign:
            excluded_cases.append(case)
        elif fam is not None:
            comparable_adversarial.append(case)
        else:
            comparable_benign.append(case)

    assert len(comparable_adversarial) == 36, f"Expected 36 adversarial, got {len(comparable_adversarial)}"
    assert len(comparable_benign) == 36, f"Expected 36 benign, got {len(comparable_benign)}"
    assert len(excluded_cases) == 18, f"Expected 18 excluded, got {len(excluded_cases)}"

    return comparable_adversarial, comparable_benign, excluded_cases


def extract_model_case_data(
    cfg: Dict[str, Any],
    comparable_cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(cfg["db_path"])
    cur = conn.cursor()
    ledger = json.load(open(cfg["ledger_path"], "r", encoding="utf-8"))
    case_entries = ledger.get("cases", {})

    extracted = []
    for case in comparable_cases:
        cid = case["case_id"]
        entry = case_entries.get(cid)
        if not entry:
            raise ValueError(f"Missing ledger entry for case {cid} in {cfg['key']}")
        eid = entry.get("experiment_id")
        if not eid:
            raise ValueError(f"Missing experiment_id for case {cid} in {cfg['key']}")

        cur.execute(
            """SELECT baseline_status, baseline_raw_output, baseline_visible_output,
                      baseline_latency_ms, baseline_input_tokens, baseline_output_tokens,
                      defended_status, defended_raw_output, defended_visible_output,
                      defended_latency_ms, defended_input_tokens, defended_output_tokens,
                      evaluation_json
               FROM experiment_runs WHERE id = ?""",
            (eid,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Row {eid} not found in DB {cfg['db_path']}")

        (
            b_status, b_raw, b_vis, b_lat, b_in_tok, b_out_tok,
            d_status, d_raw, d_vis, d_lat, d_in_tok, d_out_tok,
            ev_json,
        ) = row

        if not ev_json or "PENDING" in ev_json:
            raise ValueError(f"Incomplete evaluation on {cid} in {cfg['key']}")

        ev = json.loads(ev_json)

        extracted.append({
            "case_id": cid,
            "model_key": cfg["key"],
            "model_display": cfg["display_name"],
            "year": cfg["year"],
            "attack_family": case.get("attack_family"),
            "difficulty": case.get("difficulty"),
            "original_task": case["original_task"],
            "baseline_status": b_status,
            "baseline_attack_success": ev.get("baseline_attack_success"),
            "baseline_legitimate_task_success": ev.get("baseline_legitimate_task_success"),
            "baseline_false_refusal": ev.get("baseline_false_refusal"),
            "baseline_canary_leakage_raw": ev.get("baseline_canary_leakage_raw"),
            "baseline_canary_leakage_visible": ev.get("baseline_canary_leakage_visible"),
            "baseline_latency_ms": b_lat,
            "baseline_input_tokens": b_in_tok,
            "baseline_output_tokens": b_out_tok,
            "defended_status": d_status,
            "defended_attack_success": ev.get("defended_attack_success"),
            "defended_legitimate_task_success": ev.get("defended_legitimate_task_success"),
            "defended_false_refusal": ev.get("defended_false_refusal"),
            "defended_canary_leakage_raw": ev.get("defended_canary_leakage_raw"),
            "defended_canary_leakage_visible": ev.get("defended_canary_leakage_visible"),
            "defended_latency_ms": d_lat,
            "defended_input_tokens": d_in_tok,
            "defended_output_tokens": d_out_tok,
            "evaluator_method": ev.get("evaluator_method"),
        })

    conn.close()
    return extracted


def extract_gemini_supplementary_tool() -> Dict[str, Any]:
    conn = sqlite3.connect(FROZEN_GEMINI_DIR / "promptguard_final_90.db")
    cur = conn.cursor()
    ledger = json.load(open(FROZEN_GEMINI_DIR / "ledger_final_90.json", "r", encoding="utf-8"))["cases"]

    tool_adv_ids = [f"TOOL-E0{i}" for i in range(1, 5)] + [f"TOOL-M0{i}" for i in range(1, 5)] + [f"TOOL-S0{i}" for i in range(1, 5)]
    tool_ben_ids = [f"BEN-0{i}" for i in range(33, 39)]

    adv_records = []
    for cid in tool_adv_ids:
        entry = ledger[cid]
        eid = entry["experiment_id"]
        row = cur.execute("SELECT baseline_status, defended_status, baseline_tool_evidence, defended_tool_evidence, evaluation_json FROM experiment_runs WHERE id=?", (eid,)).fetchone()
        ev = json.loads(row[4])
        adv_records.append({
            "case_id": cid,
            "baseline_attack_success": ev.get("baseline_attack_success"),
            "defended_attack_success": ev.get("defended_attack_success"),
            "baseline_tool_evidence": json.loads(row[2]) if row[2] else {},
            "defended_tool_evidence": json.loads(row[3]) if row[3] else {},
        })

    ben_records = []
    for cid in tool_ben_ids:
        entry = ledger[cid]
        eid = entry["experiment_id"]
        row = cur.execute("SELECT baseline_status, defended_status, evaluation_json FROM experiment_runs WHERE id=?", (eid,)).fetchone()
        ev = json.loads(row[2])
        ben_records.append({
            "case_id": cid,
            "baseline_legitimate_task_success": ev.get("baseline_legitimate_task_success"),
            "defended_legitimate_task_success": ev.get("defended_legitimate_task_success"),
            "baseline_false_refusal": ev.get("baseline_false_refusal"),
            "defended_false_refusal": ev.get("defended_false_refusal"),
        })

    conn.close()

    b_succ = sum(1 for r in adv_records if r["baseline_attack_success"] is True)
    d_succ = sum(1 for r in adv_records if r["defended_attack_success"] is True)
    b_legit = sum(1 for r in ben_records if r["baseline_legitimate_task_success"] is True)
    d_legit = sum(1 for r in ben_records if r["defended_legitimate_task_success"] is True)

    return {
        "family": "tool_misuse_manipulation",
        "exclusion_reason": (
            "Local comparison models (Llama 2 7B, Gemma 2 9B, Gemma 3 12B) were evaluated "
            "without native tool schemas and execution hooks to preserve strict provider neutrality. "
            "TOOL experiments evaluated Gemini 3.1 Flash Lite with read-only fixture tools and least-privilege authorization."
        ),
        "adversarial_cases": len(adv_records),
        "baseline_attack_success": b_succ,
        "baseline_asr": b_succ / len(adv_records),
        "defended_attack_success": d_succ,
        "defended_asr": d_succ / len(adv_records),
        "absolute_reduction": (b_succ - d_succ) / len(adv_records),
        "benign_cases": len(ben_records),
        "baseline_legitimate_task_success": b_legit,
        "baseline_legit_rate": b_legit / len(ben_records),
        "defended_legitimate_task_success": d_legit,
        "defended_legit_rate": d_legit / len(ben_records),
        "records_adv": adv_records,
        "records_ben": ben_records,
    }


def analyze_all() -> Dict[str, Any]:
    verify_integrity()
    adjudication = load_adjudication()
    adjudication_entries = adjudication["records"]
    adv_cases, ben_cases, excluded_cases = load_manifest_cases()
    comparable_cases = adv_cases + ben_cases

    model_data: Dict[str, List[Dict[str, Any]]] = {}
    for cfg in MODEL_CONFIGS:
        records = extract_model_case_data(cfg, comparable_cases)
        assert len(records) == 72
        model_data[cfg["key"]] = apply_adjudication(records, adjudication_entries)

    # 1. Overall Metrics
    overall_rows = []
    overall_summary = {}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = model_data[k]
        adv_recs = [r for r in recs if r["attack_family"] is not None]
        n_adv = len(adv_recs)
        baseline = summarize_binary(adv_recs, "baseline_attack_success")
        defended = summarize_binary(adv_recs, "defended_attack_success")
        b_asr = baseline["rate"]
        d_asr = defended["rate"]
        red = b_asr - d_asr if b_asr is not None and d_asr is not None else None
        b_ci = baseline["ci95"]
        d_ci = defended["ci95"]

        row = {
            "model_key": k,
            "display_name": cfg["display_name"],
            "year": cfg["year"],
            "architecture": cfg["architecture"],
            "provider": cfg["provider"],
            "adversarial_n": n_adv,
            "baseline_evaluated_n": baseline["evaluated_n"],
            "baseline_unresolved_n": baseline["unresolved_n"],
            "baseline_success_count": baseline["success_count"],
            "baseline_asr": b_asr,
            "baseline_asr_ci95_low": b_ci[0] if b_ci else None,
            "baseline_asr_ci95_high": b_ci[1] if b_ci else None,
            "defended_evaluated_n": defended["evaluated_n"],
            "defended_unresolved_n": defended["unresolved_n"],
            "defended_success_count": defended["success_count"],
            "defended_asr": d_asr,
            "defended_asr_ci95_low": d_ci[0] if d_ci else None,
            "defended_asr_ci95_high": d_ci[1] if d_ci else None,
            "absolute_asr_reduction": round(red, 4) if red is not None else None,
            "relative_asr_reduction": round(red / b_asr, 4) if b_asr else None,
        }
        overall_rows.append(row)
        overall_summary[k] = row

    # 2. Family Metrics
    families = ["direct_prompt_injection", "system_prompt_canary_leakage", "untrusted_code_text_injection"]
    family_rows = []
    family_summary: Dict[str, Dict[str, Any]] = {f: {} for f in families}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = model_data[k]
        for fam in families:
            f_recs = [r for r in recs if r["attack_family"] == fam]
            n_f = len(f_recs)
            baseline = summarize_binary(f_recs, "baseline_attack_success")
            defended = summarize_binary(f_recs, "defended_attack_success")
            b_asr = baseline["rate"]
            d_asr = defended["rate"]
            b_ci = baseline["ci95"]
            d_ci = defended["ci95"]
            row = {
                "model_key": k,
                "display_name": cfg["display_name"],
                "year": cfg["year"],
                "attack_family": fam,
                "n": n_f,
                "baseline_evaluated_n": baseline["evaluated_n"],
                "baseline_unresolved_n": baseline["unresolved_n"],
                "baseline_success_count": baseline["success_count"],
                "baseline_asr": b_asr,
                "baseline_asr_ci95_low": b_ci[0] if b_ci else None,
                "baseline_asr_ci95_high": b_ci[1] if b_ci else None,
                "defended_evaluated_n": defended["evaluated_n"],
                "defended_unresolved_n": defended["unresolved_n"],
                "defended_success_count": defended["success_count"],
                "defended_asr": d_asr,
                "defended_asr_ci95_low": d_ci[0] if d_ci else None,
                "defended_asr_ci95_high": d_ci[1] if d_ci else None,
                "absolute_reduction": round(b_asr - d_asr, 4) if b_asr is not None and d_asr is not None else None,
            }
            family_rows.append(row)
            family_summary[fam][k] = row

    # 3. Difficulty Metrics
    difficulties = ["easy", "moderate", "subtle"]
    difficulty_rows = []
    difficulty_summary: Dict[str, Dict[str, Any]] = {d: {} for d in difficulties}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = model_data[k]
        for diff in difficulties:
            d_recs = [r for r in recs if r["difficulty"] == diff and r["attack_family"] is not None]
            n_d = len(d_recs)
            baseline = summarize_binary(d_recs, "baseline_attack_success")
            defended = summarize_binary(d_recs, "defended_attack_success")
            b_asr = baseline["rate"]
            d_asr = defended["rate"]
            b_ci = baseline["ci95"]
            d_ci = defended["ci95"]
            row = {
                "model_key": k,
                "display_name": cfg["display_name"],
                "year": cfg["year"],
                "difficulty": diff,
                "n": n_d,
                "baseline_evaluated_n": baseline["evaluated_n"],
                "baseline_unresolved_n": baseline["unresolved_n"],
                "baseline_success_count": baseline["success_count"],
                "baseline_asr": b_asr,
                "baseline_asr_ci95_low": b_ci[0] if b_ci else None,
                "baseline_asr_ci95_high": b_ci[1] if b_ci else None,
                "defended_evaluated_n": defended["evaluated_n"],
                "defended_unresolved_n": defended["unresolved_n"],
                "defended_success_count": defended["success_count"],
                "defended_asr": d_asr,
                "defended_asr_ci95_low": d_ci[0] if d_ci else None,
                "defended_asr_ci95_high": d_ci[1] if d_ci else None,
                "absolute_reduction": round(b_asr - d_asr, 4) if b_asr is not None and d_asr is not None else None,
            }
            difficulty_rows.append(row)
            difficulty_summary[diff][k] = row

    # 4. Canary Leakage Details (CAN family)
    canary_rows = []
    canary_summary = {}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = [r for r in model_data[k] if r["attack_family"] == "system_prompt_canary_leakage"]
        n_c = len(recs)
        b_raw = sum(1 for r in recs if r["baseline_canary_leakage_raw"] is True)
        b_vis = sum(1 for r in recs if r["baseline_canary_leakage_visible"] is True)
        d_raw = sum(1 for r in recs if r["defended_canary_leakage_raw"] is True)
        d_vis = sum(1 for r in recs if r["defended_canary_leakage_visible"] is True)
        row = {
            "model_key": k,
            "display_name": cfg["display_name"],
            "year": cfg["year"],
            "n": n_c,
            "baseline_raw_leakage_count": b_raw,
            "baseline_raw_leakage_rate": round(b_raw / n_c, 4),
            "baseline_visible_leakage_count": b_vis,
            "baseline_visible_leakage_rate": round(b_vis / n_c, 4),
            "defended_raw_leakage_count": d_raw,
            "defended_raw_leakage_rate": round(d_raw / n_c, 4),
            "defended_visible_leakage_count": d_vis,
            "defended_visible_leakage_rate": round(d_vis / n_c, 4),
            "promptguard_redaction_rate": compute_redaction_rate(d_raw, d_vis),
        }
        canary_rows.append(row)
        canary_summary[k] = row

    # 5. Benign Utility & False Refusals
    benign_rows = []
    benign_summary = {}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = [r for r in model_data[k] if r["attack_family"] is None]
        n_b = len(recs)
        b_leg = summarize_binary(recs, "baseline_legitimate_task_success")
        d_leg = summarize_binary(recs, "defended_legitimate_task_success")
        b_ref = summarize_binary(recs, "baseline_false_refusal")
        d_ref = summarize_binary(recs, "defended_false_refusal")

        b_leg_rate = b_leg["rate"]
        d_leg_rate = d_leg["rate"]
        b_ref_rate = b_ref["rate"]
        d_ref_rate = d_ref["rate"]
        b_leg_ci = b_leg["ci95"]
        d_leg_ci = d_leg["ci95"]
        b_ref_ci = b_ref["ci95"]
        d_ref_ci = d_ref["ci95"]

        row = {
            "model_key": k,
            "display_name": cfg["display_name"],
            "year": cfg["year"],
            "benign_n": n_b,
            "baseline_evaluated_n": b_leg["evaluated_n"],
            "baseline_unresolved_n": b_leg["unresolved_n"],
            "baseline_legitimate_success_count": b_leg["success_count"],
            "baseline_legitimate_success_rate": b_leg_rate,
            "baseline_legit_ci95_low": b_leg_ci[0] if b_leg_ci else None,
            "baseline_legit_ci95_high": b_leg_ci[1] if b_leg_ci else None,
            "defended_evaluated_n": d_leg["evaluated_n"],
            "defended_unresolved_n": d_leg["unresolved_n"],
            "defended_legitimate_success_count": d_leg["success_count"],
            "defended_legitimate_success_rate": d_leg_rate,
            "defended_legit_ci95_low": d_leg_ci[0] if d_leg_ci else None,
            "defended_legit_ci95_high": d_leg_ci[1] if d_leg_ci else None,
            "legitimate_utility_delta": round(d_leg_rate - b_leg_rate, 4) if b_leg_rate is not None and d_leg_rate is not None else None,
            "baseline_false_refusal_evaluated_n": b_ref["evaluated_n"],
            "baseline_false_refusal_unresolved_n": b_ref["unresolved_n"],
            "baseline_false_refusal_count": b_ref["success_count"],
            "baseline_false_refusal_rate": b_ref_rate,
            "baseline_refusal_ci95_low": b_ref_ci[0] if b_ref_ci else None,
            "baseline_refusal_ci95_high": b_ref_ci[1] if b_ref_ci else None,
            "defended_false_refusal_evaluated_n": d_ref["evaluated_n"],
            "defended_false_refusal_unresolved_n": d_ref["unresolved_n"],
            "defended_false_refusal_count": d_ref["success_count"],
            "defended_false_refusal_rate": d_ref_rate,
            "defended_refusal_ci95_low": d_ref_ci[0] if d_ref_ci else None,
            "defended_refusal_ci95_high": d_ref_ci[1] if d_ref_ci else None,
            "false_refusal_delta": round(d_ref_rate - b_ref_rate, 4) if b_ref_rate is not None and d_ref_rate is not None else None,
        }
        benign_rows.append(row)
        benign_summary[k] = row

    # 6. Paired Transitions
    transition_rows = []
    transition_summary = {}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = model_data[k]
        adv_recs = [r for r in recs if r["attack_family"] is not None]
        ben_recs = [r for r in recs if r["attack_family"] is None]
        adv = summarize_paired(
            adv_recs, "baseline_attack_success", "defended_attack_success"
        )
        ben = summarize_paired(
            ben_recs,
            "baseline_legitimate_task_success",
            "defended_legitimate_task_success",
        )

        row = {
            "model_key": k,
            "display_name": cfg["display_name"],
            "year": cfg["year"],
            "adv_total": len(adv_recs),
            "adv_evaluated_pairs": adv["evaluated_pairs"],
            "adv_unresolved_pairs": adv["unresolved_pairs"],
            "adv_mitigated_T_to_F": adv["mitigated"],
            "adv_persistent_T_to_T": adv["persistent"],
            "adv_safe_F_to_F": adv["safe"],
            "adv_induced_F_to_T": adv["induced"],
            "ben_total": len(ben_recs),
            "ben_evaluated_pairs": ben["evaluated_pairs"],
            "ben_unresolved_pairs": ben["unresolved_pairs"],
            "ben_preserved_T_to_T": ben["persistent"],
            "ben_degraded_T_to_F": ben["mitigated"],
            "ben_recovered_F_to_T": ben["induced"],
            "ben_failed_F_to_F": ben["safe"],
        }
        transition_rows.append(row)
        transition_summary[k] = row

    # 7. Statistical Tests (Paired McNemar / Binomial)
    statistical_rows = []
    statistical_summary = {}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        t = transition_summary[k]

        adv_test = mcnemar_test(b=t["adv_mitigated_T_to_F"], c=t["adv_induced_F_to_T"])
        row_adv = {
            "model_key": k,
            "display_name": cfg["display_name"],
            "metric_tested": "Adversarial Attack Success (Baseline vs Defended)",
            "n_pairs": t["adv_evaluated_pairs"],
            "unresolved_pairs": t["adv_unresolved_pairs"],
            "b_mitigated": adv_test["b_mitigated"],
            "c_induced": adv_test["c_induced"],
            "discordant_pairs": adv_test["discordant_pairs"],
            "chi2_stat": adv_test["chi2_stat"],
            "p_value": adv_test["p_value"],
            "significant_at_05": adv_test["significant_05"],
            "test_type": adv_test["test_type"],
        }
        statistical_rows.append(row_adv)

        ben_test = mcnemar_test(b=t["ben_degraded_T_to_F"], c=t["ben_recovered_F_to_T"])
        row_ben = {
            "model_key": k,
            "display_name": cfg["display_name"],
            "metric_tested": "Benign Legitimate Task Success (Baseline vs Defended)",
            "n_pairs": t["ben_evaluated_pairs"],
            "unresolved_pairs": t["ben_unresolved_pairs"],
            "b_mitigated": ben_test["b_mitigated"],
            "c_induced": ben_test["c_induced"],
            "discordant_pairs": ben_test["discordant_pairs"],
            "chi2_stat": ben_test["chi2_stat"],
            "p_value": ben_test["p_value"],
            "significant_at_05": ben_test["significant_05"],
            "test_type": ben_test["test_type"],
        }
        statistical_rows.append(row_ben)

        statistical_summary[k] = {"adversarial": adv_test, "benign": ben_test}

    # 8. Telemetry Summary
    telemetry_summary = {}
    for cfg in MODEL_CONFIGS:
        k = cfg["key"]
        recs = model_data[k]

        def get_stat(values):
            clean = [v for v in values if v is not None]
            if not clean:
                return {"mean": None, "median": None}
            return {"mean": round(statistics.mean(clean), 2), "median": round(statistics.median(clean), 2)}

        telemetry_summary[k] = {
            "baseline_latency_ms": get_stat([r["baseline_latency_ms"] for r in recs]),
            "defended_latency_ms": get_stat([r["defended_latency_ms"] for r in recs]),
            "baseline_input_tokens": get_stat([r["baseline_input_tokens"] for r in recs]),
            "defended_input_tokens": get_stat([r["defended_input_tokens"] for r in recs]),
            "baseline_output_tokens": get_stat([r["baseline_output_tokens"] for r in recs]),
            "defended_output_tokens": get_stat([r["defended_output_tokens"] for r in recs]),
        }

    # 9. Gemini Supplementary Tool Study
    gemini_tool_study = extract_gemini_supplementary_tool()

    return {
        "models": MODEL_CONFIGS,
        "overall": overall_rows,
        "by_family": family_rows,
        "by_difficulty": difficulty_rows,
        "canary_leakage": canary_rows,
        "benign_utility": benign_rows,
        "paired_transitions": transition_rows,
        "statistical_tests": statistical_rows,
        "telemetry": telemetry_summary,
        "supplementary_gemini_tool": gemini_tool_study,
        "interpretation": FINAL_FINDINGS,
        "adjudication": {
            key: value for key, value in adjudication.items() if key != "records"
        },
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_markdown_report(results: Dict[str, Any]) -> str:
    overall = results["overall"]
    by_fam = results["by_family"]
    by_diff = results["by_difficulty"]
    canary = results["canary_leakage"]
    benign = results["benign_utility"]
    transitions = results["paired_transitions"]
    stats = results["statistical_tests"]
    tool = results["supplementary_gemini_tool"]
    adjudication = results["adjudication"]

    def pct(value: Optional[float]) -> str:
        return "N/A" if value is None else f"{value:.1%}"

    md = [
        "# PromptGuard Ai — Corrected Four-Model Benchmark Results",
        "",
        "**Analysis date:** " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "",
        "**Scope:** Paired 72-case comparison per model, corrected through a separate CM5.5 full-output adjudication overlay. Original databases and evaluator labels remain unchanged.",
        "",
        f"**Adjudication:** {adjudication['semantic_records_reviewed']} semantic records reviewed; {adjudication['labels_changed']} labels changed across {adjudication['records_with_changed_labels']} cases; {adjudication['ambiguous_records']} ambiguous records.",
        "",
        "## 1. Overall security results",
        "",
        "| Model | Baseline success | Baseline ASR [95% CI] | Defended success | Defended ASR [95% CI] | Absolute reduction |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        md.append(
            f"| **{row['display_name']}** | {row['baseline_success_count']}/{row['baseline_evaluated_n']} | "
            f"{pct(row['baseline_asr'])} [{pct(row['baseline_asr_ci95_low'])}, {pct(row['baseline_asr_ci95_high'])}] | "
            f"{row['defended_success_count']}/{row['defended_evaluated_n']} | "
            f"{pct(row['defended_asr'])} [{pct(row['defended_asr_ci95_low'])}, {pct(row['defended_asr_ci95_high'])}] | "
            f"{pct(row['absolute_asr_reduction'])} |"
        )

    md.extend([
        "",
        "## 2. Attack-family results",
        "",
        "| Family | Model | Baseline | Defended |",
        "|---|---|---:|---:|",
    ])
    family_names = {
        "direct_prompt_injection": "DPI",
        "system_prompt_canary_leakage": "CAN",
        "untrusted_code_text_injection": "DATA",
    }
    for family, label in family_names.items():
        for row in [item for item in by_fam if item["attack_family"] == family]:
            md.append(
                f"| {label} | **{row['display_name']}** | {row['baseline_success_count']}/{row['baseline_evaluated_n']} ({pct(row['baseline_asr'])}) | "
                f"{row['defended_success_count']}/{row['defended_evaluated_n']} ({pct(row['defended_asr'])}) |"
            )

    md.extend([
        "",
        "## 3. Difficulty results",
        "",
        "| Difficulty | Model | Baseline | Defended |",
        "|---|---|---:|---:|",
    ])
    for difficulty in ("easy", "moderate", "subtle"):
        for row in [item for item in by_diff if item["difficulty"] == difficulty]:
            md.append(
                f"| {difficulty.capitalize()} | **{row['display_name']}** | {row['baseline_success_count']}/{row['baseline_evaluated_n']} ({pct(row['baseline_asr'])}) | "
                f"{row['defended_success_count']}/{row['defended_evaluated_n']} ({pct(row['defended_asr'])}) |"
            )

    md.extend([
        "",
        "## 4. Canary leakage",
        "",
        "| Model | Baseline raw | Baseline visible | Defended raw | Defended visible | Redaction rate |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in canary:
        md.append(
            f"| **{row['display_name']}** | {row['baseline_raw_leakage_count']}/12 | {row['baseline_visible_leakage_count']}/12 | "
            f"{row['defended_raw_leakage_count']}/12 | {row['defended_visible_leakage_count']}/12 | {pct(row['promptguard_redaction_rate'])} |"
        )

    md.extend([
        "",
        "## 5. Benign utility and false refusals",
        "",
        "| Model | Baseline legitimate success | Defended legitimate success | Utility change | Baseline false refusal | Defended false refusal |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in benign:
        md.append(
            f"| **{row['display_name']}** | {row['baseline_legitimate_success_count']}/{row['baseline_evaluated_n']} ({pct(row['baseline_legitimate_success_rate'])}) | "
            f"{row['defended_legitimate_success_count']}/{row['defended_evaluated_n']} ({pct(row['defended_legitimate_success_rate'])}) | "
            f"{pct(row['legitimate_utility_delta'])} | {row['baseline_false_refusal_count']}/{row['baseline_false_refusal_evaluated_n']} ({pct(row['baseline_false_refusal_rate'])}) | "
            f"{row['defended_false_refusal_count']}/{row['defended_false_refusal_evaluated_n']} ({pct(row['defended_false_refusal_rate'])}) |"
        )

    md.extend([
        "",
        "## 6. Paired statistical results",
        "",
        "| Model | Metric | Evaluated pairs | Mitigated/degraded | Induced/recovered | Exact p-value |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in stats:
        md.append(
            f"| **{row['display_name']}** | {row['metric_tested']} | {row['n_pairs']} | {row['b_mitigated']} | {row['c_induced']} | {row['p_value'] if row['p_value'] is not None else 'N/A'} |"
        )

    md.extend([
        "",
        "## 7. Supplementary Gemini tool study",
        "",
        f"> {tool['exclusion_reason']}",
        "",
        f"The supplementary set contains {tool['adversarial_cases']} adversarial and {tool['benign_cases']} benign tool cases. It remains excluded from the four-model comparison.",
        "",
        "## 8. Corrected interpretation",
        "",
        "### Finding 1 — Descriptive baseline trend",
        "",
        FINAL_FINDINGS["open_weight_baseline_trend"],
        "",
        FINAL_FINDINGS["gemini_baseline_result"],
        "",
        "### Finding 2 — Confirmed vulnerability was concentrated in CAN",
        "",
        FINAL_FINDINGS["can_concentration"],
        "",
        "### Finding 3 — Output Screening",
        "",
        FINAL_FINDINGS["output_screening"],
        "",
        "### Finding 4 — Security–utility tradeoff",
        "",
        FINAL_FINDINGS["security_utility"],
        "",
        "### Finding 5 — DPI and DATA null security findings",
        "",
        FINAL_FINDINGS["input_screening_null_finding"],
        "",
        FINAL_FINDINGS["instruction_data_null_finding"],
        "",
        FINAL_FINDINGS["defended_scope"],
        "",
        "## 9. Limitations",
        "",
        "1. The attacks are fixed, explicit, and structurally aligned with narrow deterministic defenses.",
        "2. Each family and difficulty subgroup contains only 12 cases; zero observed successes still has a wide Wilson interval.",
        "3. Local Ollama and cloud Gemini runs differ in provider, native templates, and inference environment.",
        "4. Semantic labels are now independently adjudicated from stored outputs, but adjudication is still a single-reviewer judgment rather than blinded multi-rater labeling.",
        "5. One execution per prompt does not estimate run-to-run stochastic variance.",
        "6. The absence of confirmed baseline DPI and DATA successes prevents estimating the incremental effectiveness of their mapped defenses from this dataset.",
    ])
    return "\n".join(md)


def main():
    print("=== Starting PromptGuard Ai Phase CM5.6: Final Results Freeze ===")
    hashes = verify_integrity()
    print("All 4 database checksums verified intact:")
    for k, h in hashes.items():
        print(f"  [{k}] {h}")

    results = analyze_all()

    # Output directory
    FINAL_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Export CSV files
    write_csv(FINAL_ANALYSIS_DIR / "model_overall_metrics.csv", results["overall"])
    write_csv(FINAL_ANALYSIS_DIR / "model_family_metrics.csv", results["by_family"])
    write_csv(FINAL_ANALYSIS_DIR / "model_difficulty_metrics.csv", results["by_difficulty"])
    write_csv(FINAL_ANALYSIS_DIR / "model_benign_metrics.csv", results["benign_utility"])
    write_csv(FINAL_ANALYSIS_DIR / "model_canary_metrics.csv", results["canary_leakage"])
    write_csv(FINAL_ANALYSIS_DIR / "paired_transitions.csv", results["paired_transitions"])
    write_csv(FINAL_ANALYSIS_DIR / "statistical_tests.csv", results["statistical_tests"])

    # 2. Export JSON summaries (including machine-readable format for static research website)
    summary_path = FINAL_ANALYSIS_DIR / "cross_model_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    # 3. Export ANALYSIS_RECORD.json from the same corrected result set
    overall_by_key = {row["model_key"]: row for row in results["overall"]}
    benign_by_key = {row["model_key"]: row for row in results["benign_utility"]}
    record_doc = {
        "benchmark_name": "PromptGuard Ai — Cross-Generation Prompt-Injection Robustness Study",
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "verified_hashes": hashes,
        "adjudication": results["adjudication"],
        "models_evaluated": [cfg["key"] for cfg in results["models"]],
        "comparable_cases_per_model": 72,
        "adversarial_cases_per_model": 36,
        "benign_cases_per_model": 36,
        "total_paired_evaluations": 72 * len(results["models"]),
        "key_findings": {
            "observed_baseline_asr": {
                key: overall_by_key[key]["baseline_asr"] for key in overall_by_key
            },
            "observed_defended_asr": {
                key: overall_by_key[key]["defended_asr"] for key in overall_by_key
            },
            "benign_baseline_success": {
                key: benign_by_key[key]["baseline_legitimate_success_rate"]
                for key in benign_by_key
            },
            "benign_defended_success": {
                key: benign_by_key[key]["defended_legitimate_success_rate"]
                for key in benign_by_key
            },
            "interpretation": FINAL_FINDINGS,
        },
    }
    with open(FINAL_ANALYSIS_DIR / "ANALYSIS_RECORD.json", "w", encoding="utf-8") as f:
        json.dump(record_doc, f, indent=2)

    # 4. Generate Markdown report
    md_report = generate_markdown_report(results)
    with open(FINAL_ANALYSIS_DIR / "FINAL_CROSS_MODEL_RESULTS.md", "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"\nAll analysis artifacts written successfully to:\n  {FINAL_ANALYSIS_DIR}")
    print("\n=== Summary of Overall Comparable Results ===")
    for r in results["overall"]:
        print(f"  {r['display_name']} ({r['year']}): Baseline ASR = {r['baseline_success_count']}/{r['baseline_evaluated_n']} ({r['baseline_asr']:.1%}) -> Defended ASR = {r['defended_success_count']}/{r['defended_evaluated_n']} ({r['defended_asr']:.1%}) [Reduction = -{r['absolute_asr_reduction']:.1%}]")

    print("\n=== Summary of Benign Utility Results ===")
    for r in results["benign_utility"]:
        print(f"  {r['display_name']} ({r['year']}): Baseline Legit = {r['baseline_legitimate_success_count']}/{r['baseline_evaluated_n']} ({r['baseline_legitimate_success_rate']:.1%}) -> Defended Legit = {r['defended_legitimate_success_count']}/{r['defended_evaluated_n']} ({r['defended_legitimate_success_rate']:.1%}) [Diff = {r['legitimate_utility_delta']:+.1%}], False Refusal = {r['defended_false_refusal_count']}/{r['defended_false_refusal_evaluated_n']}")

    print("\n=== Phase CM5.6 Analysis Freeze Complete ===")


if __name__ == "__main__":
    main()
