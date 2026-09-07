import json
import pytest
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent.parent / "benchmark_cases" / "manifest.jsonl"
METADATA_PATH = Path(__file__).parent.parent / "benchmark_cases" / "metadata.json"

def test_manifest_exists():
    assert MANIFEST_PATH.exists()
    assert METADATA_PATH.exists()

def test_manifest_counts_and_schema():
    cases = []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            cases.append(json.loads(line))
            
    assert len(cases) == 90
    
    adversarial = [c for c in cases if c.get("attack_family") is not None]
    benign = [c for c in cases if c.get("attack_family") is None]
    
    assert len(adversarial) == 48
    assert len(benign) == 42
    
    # Check adversarial distribution
    families = {
        "direct_prompt_injection": 0,
        "system_prompt_canary_leakage": 0,
        "tool_misuse_manipulation": 0,
        "untrusted_code_text_injection": 0
    }
    
    family_difficulties = {
        "direct_prompt_injection": {"easy": 0, "moderate": 0, "subtle": 0},
        "system_prompt_canary_leakage": {"easy": 0, "moderate": 0, "subtle": 0},
        "tool_misuse_manipulation": {"easy": 0, "moderate": 0, "subtle": 0},
        "untrusted_code_text_injection": {"easy": 0, "moderate": 0, "subtle": 0}
    }
    
    case_ids = set()
    
    for case in adversarial:
        assert case["case_id"] not in case_ids
        case_ids.add(case["case_id"])
        
        assert "original_task" in case and case["original_task"]
        
        fam = case["attack_family"]
        assert fam in families
        families[fam] += 1
        
        diff = case["difficulty"]
        assert diff in family_difficulties[fam]
        family_difficulties[fam][diff] += 1
        
        if fam == "tool_misuse_manipulation":
            assert case.get("forbidden_target") in ["admin-core", "issue-999", "src/secrets.py"]

    for fam, count in families.items():
        assert count == 12
        for diff, dcount in family_difficulties[fam].items():
            assert dcount == 4
        
    for case in benign:
        assert case["case_id"] not in case_ids
        case_ids.add(case["case_id"])
        assert "original_task" in case and case["original_task"]
        assert case["difficulty"] is None

