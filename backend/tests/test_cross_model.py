"""Tests for cross-model dataset partitioning and storage isolation."""
import json
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, ExperimentRun
from app.services.cross_model import (
    is_tool_dependent_case,
    NATIVE_TOOL_DEPENDENT_BENIGN_CASES,
    partition_cross_model_cases,
)


def test_native_tool_dependent_benign_cases_exact():
    # Exactly 6 verified benign cases require PromptGuard native tools
    expected = {"BEN-033", "BEN-034", "BEN-035", "BEN-036", "BEN-037", "BEN-038"}
    assert NATIVE_TOOL_DEPENDENT_BENIGN_CASES == expected


def test_is_tool_dependent_case():
    assert is_tool_dependent_case("TOOL-E01", "tool_misuse_manipulation") is True
    assert is_tool_dependent_case("TOOL-M02", None) is True
    assert is_tool_dependent_case("BEN-033", None) is True
    assert is_tool_dependent_case("BEN-038", None) is True

    # Non-tool cases
    assert is_tool_dependent_case("DPI-E01", "direct_prompt_injection") is False
    assert is_tool_dependent_case("CAN-E01", "system_prompt_canary_leakage") is False
    assert is_tool_dependent_case("DATA-E01", "untrusted_code_text_injection") is False
    assert is_tool_dependent_case("BEN-001", None) is False
    assert is_tool_dependent_case("BEN-019", None) is False
    assert is_tool_dependent_case("BEN-042", None) is False


def test_partition_cross_model_cases_on_frozen_manifest():
    manifest_path = Path("benchmark_results/final_90/manifest_final_90.jsonl")
    if not manifest_path.exists():
        manifest_path = Path("benchmark_cases/manifest.jsonl")

    cases = [json.loads(line) for line in open(manifest_path, "r", encoding="utf-8") if line.strip()]
    assert len(cases) == 90

    partition = partition_cross_model_cases(cases)

    # Required counts:
    # 36 adversarial (12 DPI + 12 CAN + 12 DATA)
    # 36 benign (42 total benign - 6 tool-dependent)
    # 72 total comparable cases
    # 18 total excluded cases (12 TOOL + 6 BEN)
    assert partition["counts"]["adversarial_comparable"] == 36
    assert partition["counts"]["benign_comparable"] == 36
    assert partition["counts"]["total_comparable"] == 72
    assert partition["counts"]["excluded_adversarial"] == 12
    assert partition["counts"]["excluded_benign"] == 6
    assert partition["counts"]["total_excluded"] == 18

    # Verify excluded benign cases
    assert set(partition["excluded_benign_ids"]) == {"BEN-033", "BEN-034", "BEN-035", "BEN-036", "BEN-037", "BEN-038"}

    # Verify excluded adversarial cases are all TOOL cases
    for cid in partition["excluded_adversarial_ids"]:
        assert cid.startswith("TOOL-")


def test_storage_isolation_separate_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="cross-model-test-"))
    isolated_db_file = temp_dir / "cross_model_test.db"
    engine = create_engine(f"sqlite:///{isolated_db_file.as_posix()}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    db = Session()
    count = db.query(ExperimentRun).count()
    assert count == 0
    db.close()

    assert isolated_db_file.exists()
