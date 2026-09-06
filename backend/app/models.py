from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class ChatRun(Base):
    __tablename__ = "chat_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    requested_model: Mapped[str] = mapped_column(String(160), nullable=False)
    actual_model: Mapped[str | None] = mapped_column(String(160), nullable=True)


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    original_task: Mapped[str] = mapped_column(Text, nullable=False)
    approved_attack_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    attack_family: Mapped[str] = mapped_column(String(80), nullable=False)
    mapped_defense: Mapped[str] = mapped_column(String(80), nullable=False)
    generation_source: Mapped[str] = mapped_column(String(40), nullable=False)
    attack_edited: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requested_model: Mapped[str] = mapped_column(String(160), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    defense_version: Mapped[str] = mapped_column(String(40), nullable=False)
    tool_schema_version: Mapped[str] = mapped_column(String(40), nullable=False)

    baseline_status: Mapped[str] = mapped_column(String(20), nullable=False)
    baseline_raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_visible_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_actual_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    baseline_provider_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_defense_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_tool_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    defended_status: Mapped[str] = mapped_column(String(20), nullable=False)
    defended_raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    defended_visible_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    defended_actual_model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    defended_provider_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    defended_defense_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    defended_tool_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    defended_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    defended_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    defended_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    defended_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    defended_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    evaluation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
