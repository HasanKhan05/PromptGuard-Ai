import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import ExperimentRun
from app.schemas import ExperimentRunRequest, DefenseName
from app.services.experiments import run_paired_experiment
from app.services.defenses import CANARY_VALUE

def completion(content: str | None, *, model: str = "gemini/gemini-3.1-flash-lite", tool_call=None):
    message = MagicMock()
    message.content = content
    message.tool_calls = [] if tool_call is None else [tool_call]
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    response.model = model
    return response

def test_benign_persistence():
    init_db()
    
    async def run():
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(
            side_effect=[completion("baseline"), completion("defended")]
        )
        with patch("app.services.experiments.get_client", return_value=client):
            db = SessionLocal()
            request = ExperimentRunRequest(
                original_task="Explain python lists.",
                attack_prompt="Explain python lists.",
                attack_family=None,
                generation_source="manual",
                attack_edited=False,
                model="gemini/gemini-3.1-flash-lite",
                temperature=0.0,
                max_output_tokens=100
            )
            response = await run_paired_experiment(request, db)
            
            # verify it persisted
            row = db.execute(select(ExperimentRun).where(ExperimentRun.id == response.experiment_id)).scalar_one_or_none()
            assert row is not None
            assert row.attack_family is None
            assert row.mapped_defense == "all_layered_defense"
            assert row.baseline_status == "completed"
            assert row.defended_status == "completed"
    
    asyncio.run(run())
