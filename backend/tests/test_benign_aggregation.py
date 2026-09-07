import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.models import ExperimentRun
from app.db import SessionLocal, init_db

def test_benign_aggregation():
    init_db()
    db = SessionLocal()
    db.query(ExperimentRun).delete()
    db.commit()
    
    # Insert a dummy benign run directly into db
    run = ExperimentRun(
        id="test-benign-123",
        status="completed",
        original_task="benign task",
        approved_attack_prompt="benign task",
        attack_family=None,
        mapped_defense="all_layered_defense",
        generation_source="manual",
        attack_edited=False,
        requested_model="gemini",
        temperature=0.0,
        max_output_tokens=100,
        system_prompt_version="cx1-v1",
        defense_version="cx3-v1",
        tool_schema_version="cx3-v1",
        baseline_status="completed",
        baseline_raw_output="baseline",
        baseline_visible_output="baseline",
        baseline_defense_evidence="{}",
        defended_status="completed",
        defended_raw_output="defended",
        defended_visible_output="defended",
        defended_defense_evidence="{}",
        evaluation_json=json.dumps({
            "baseline_legitimate_task_success": True,
            "defended_legitimate_task_success": True,
            "baseline_false_refusal": False,
            "defended_false_refusal": False,
        })
    )
    db.add(run)
    db.commit()
    
    with TestClient(app) as test_client:
        response = test_client.get("/api/benchmarks")
        assert response.status_code == 200
        data = response.json()
        
        # Test benchmark metrics endpoint
        assert data["total_runs_count"] == 1
        assert data["utility"]["baseline_legitimate_task_success"]["count"] == 1
        assert data["utility"]["baseline_legitimate_task_success"]["rate"] == 1.0
        
        # Test research summary
        summary_resp = test_client.get("/api/research")
        assert summary_resp.status_code == 200
        
        # Test get experiment
        exp_resp = test_client.get("/api/runs/test-benign-123")
        assert exp_resp.status_code == 200
        assert exp_resp.json()["attack_family"] is None
