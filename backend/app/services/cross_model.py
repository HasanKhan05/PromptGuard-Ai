"""PromptGuard Ai — Cross-Model Benchmark Filtering Service.

Defines the partition rules for cross-generation model comparisons:
- EXCLUDES native-tool-dependent cases (all 12 tool_misuse_manipulation adversarial cases,
  and the 6 benign cases requiring native tools: BEN-033..BEN-038).
- INCLUDES all non-tool adversarial cases (12 DPI, 12 CAN, 12 DATA = 36 total)
- INCLUDES all non-tool benign controls (36 total).
"""
from __future__ import annotations

from typing import Any, Optional

NATIVE_TOOL_DEPENDENT_BENIGN_CASES: frozenset[str] = frozenset({
    "BEN-033",
    "BEN-034",
    "BEN-035",
    "BEN-036",
    "BEN-037",
    "BEN-038",
})


def is_tool_dependent_case(case_id: str, attack_family: Optional[str] = None) -> bool:
    """Return True if the case requires PromptGuard's native read-only tools."""
    if case_id.startswith("TOOL-") or attack_family == "tool_misuse_manipulation":
        return True
    if case_id in NATIVE_TOOL_DEPENDENT_BENIGN_CASES:
        return True
    return False


def partition_cross_model_cases(
    manifest_cases: list[dict[str, Any]]
) -> dict[str, Any]:
    """Partition manifest cases into comparable and excluded sets for cross-model study."""
    adversarial_comparable: list[dict[str, Any]] = []
    benign_comparable: list[dict[str, Any]] = []
    excluded_adversarial_ids: list[str] = []
    excluded_benign_ids: list[str] = []

    for case in manifest_cases:
        cid = case["case_id"]
        fam = case.get("attack_family")
        if is_tool_dependent_case(cid, fam):
            if fam is not None or cid.startswith("TOOL-"):
                excluded_adversarial_ids.append(cid)
            else:
                excluded_benign_ids.append(cid)
        else:
            if fam is not None:
                adversarial_comparable.append(case)
            else:
                benign_comparable.append(case)

    total_comparable = adversarial_comparable + benign_comparable
    total_excluded_ids = excluded_adversarial_ids + excluded_benign_ids

    return {
        "adversarial_comparable": adversarial_comparable,
        "benign_comparable": benign_comparable,
        "total_comparable": total_comparable,
        "excluded_adversarial_ids": excluded_adversarial_ids,
        "excluded_benign_ids": excluded_benign_ids,
        "total_excluded_ids": total_excluded_ids,
        "counts": {
            "adversarial_comparable": len(adversarial_comparable),
            "benign_comparable": len(benign_comparable),
            "total_comparable": len(total_comparable),
            "excluded_adversarial": len(excluded_adversarial_ids),
            "excluded_benign": len(excluded_benign_ids),
            "total_excluded": len(total_excluded_ids),
        },
    }
