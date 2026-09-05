from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import ChatRun


def test_minimal_chat_run_storage():
    init_db()
    db = SessionLocal()
    try:
        row = ChatRun(
            prompt="test prompt",
            response="test response",
            requested_model="test/model",
            actual_model="test/model",
        )
        db.add(row)
        db.commit()
        stored = db.scalar(select(ChatRun).where(ChatRun.id == row.id))
        assert stored is not None
        assert stored.response == "test response"
        db.delete(row)
        db.commit()
    finally:
        db.close()
