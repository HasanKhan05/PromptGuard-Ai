from pathlib import Path

from app.db import engine


def test_backend_tests_do_not_bind_to_the_active_research_database():
    active_research_db = Path(__file__).resolve().parents[1] / "promptguard.db"
    assert Path(engine.url.database).resolve() != active_research_db
