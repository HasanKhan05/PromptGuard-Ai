"""PromptGuard Ai — Resilience service for cross-model benchmarking.

Handles offline-safe local generation, transient evaluator error classification,
and evaluation-pending state tracking.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Union

from ..models import ExperimentRun
from ..schemas import AttackFamily
from .evaluator import EvaluationResult, evaluate_experiment_run


class EvaluationStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"


def is_transient_evaluator_error(error: Union[Exception, str]) -> bool:
    """Classify whether an evaluator error is a transient connectivity/network/server failure.

    Transient:
    - Network connection / DNS / socket errors
    - Connection timeouts, read timeouts
    - HTTP 503, 502, 504, 500
    - HTTP 429 / rate limits / resource exhausted

    Fatal (non-transient):
    - HTTP 401 / 403 / authentication / invalid API key
    - Malformed payload / bad request / 400
    - Programming exceptions / schema errors
    """
    err_str = str(error).casefold()

    fatal_markers = [
        "401", "unauthorized", "api_key_invalid", "invalid_api_key",
        "403", "permission_denied", "forbidden", "invalid_argument",
        "bad request", "400",
    ]
    for marker in fatal_markers:
        if marker in err_str:
            return False

    transient_markers = [
        "503", "unavailable", "high demand", "spikes in demand",
        "500", "internal server error", "502", "bad gateway", "504", "gateway timeout",
        "429", "resource_exhausted", "resourceexhausted", "rate limit", "too many requests",
        "connectionerror", "connecterror", "connecttimeout", "readtimeout", "timeout",
        "timed out", "network", "getaddrinfo", "dns", "remoteprotocolerror",
        "remotedisconnected", "connection reset", "connection refused",
        "llm evaluator unavailable", "temporary", "temporary failure in name resolution",
        "service unavailable",
    ]
    for marker in transient_markers:
        if marker in err_str:
            return True

    return False


def evaluate_with_resilience(
    row: ExperimentRun,
) -> tuple[EvaluationStatus, Optional[EvaluationResult], str]:
    """Attempt evaluation with resilient offline-safe classification.

    - Deterministic cases (CAN) evaluate locally without internet.
    - Semantic cases (DPI, DATA, BENIGN) that fail due to transient network/evaluator issues
      are classified as EvaluationStatus.PENDING, allowing local generation to proceed.
    - Fatal errors (auth, programming errors) are classified as EvaluationStatus.FAILED.
    """
    is_canary = row.attack_family == AttackFamily.SYSTEM_PROMPT_CANARY_LEAKAGE.value

    try:
        eval_result = evaluate_experiment_run(row)
    except Exception as exc:  # noqa: BLE001
        if is_transient_evaluator_error(exc):
            return EvaluationStatus.PENDING, None, f"Transient evaluator exception: {exc}"
        return EvaluationStatus.FAILED, None, f"Fatal evaluator exception: {exc}"

    # Deterministic evaluations are always complete locally
    if is_canary or eval_result.evaluator_method == "deterministic":
        # Check if deterministic was actually applied or if an error was masked
        if not is_canary and "llm evaluator unavailable" in eval_result.evaluator_rationale.casefold():
            if is_transient_evaluator_error(eval_result.evaluator_rationale):
                return EvaluationStatus.PENDING, None, eval_result.evaluator_rationale
            return EvaluationStatus.FAILED, None, eval_result.evaluator_rationale
        return EvaluationStatus.COMPLETED, eval_result, eval_result.evaluator_rationale

    # Check semantic results
    if row.attack_family is None:
        # Benign control
        if (
            eval_result.baseline_legitimate_task_success is None
            or eval_result.defended_legitimate_task_success is None
        ):
            if is_transient_evaluator_error(eval_result.evaluator_rationale):
                return EvaluationStatus.PENDING, None, eval_result.evaluator_rationale
            return EvaluationStatus.FAILED, None, eval_result.evaluator_rationale
    elif row.attack_family in {
        AttackFamily.DIRECT_PROMPT_INJECTION.value,
        AttackFamily.UNTRUSTED_CODE_TEXT_INJECTION.value,
    }:
        if eval_result.baseline_attack_success is None:
            if is_transient_evaluator_error(eval_result.evaluator_rationale):
                return EvaluationStatus.PENDING, None, eval_result.evaluator_rationale
            return EvaluationStatus.FAILED, None, eval_result.evaluator_rationale

    return EvaluationStatus.COMPLETED, eval_result, eval_result.evaluator_rationale
