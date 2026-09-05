from sqlalchemy import inspect, select

from app.db import SessionLocal, engine, init_db
from app.models import ChatRun


def test_db_initialization_and_table_creation():
    init_db()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "chat_runs" in tables


def test_minimal_chat_run_storage():
    init_db()
    db = SessionLocal()
    try:
        row = ChatRun(
            prompt="test prompt",
            response="test response",
            requested_model="auto/best-coding",
            actual_model="gemini/gemini-3.1-flash-lite",
        )
        db.add(row)
        db.commit()

        stored = db.scalar(select(ChatRun).where(ChatRun.id == row.id))
        assert stored is not None
        assert stored.prompt == "test prompt"
        assert stored.response == "test response"
        assert stored.requested_model == "auto/best-coding"
        assert stored.actual_model == "gemini/gemini-3.1-flash-lite"
        assert stored.created_at is not None

        db.delete(stored)
        db.commit()
    finally:
        db.close()

