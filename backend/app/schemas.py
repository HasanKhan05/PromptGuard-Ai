from enum import Enum

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    model: str | None = Field(default=None, max_length=160)


class HealthResponse(BaseModel):
    status: str
    omniroute_configured: bool
    database: str


class AttackFamily(str, Enum):
    DIRECT_PROMPT_INJECTION = "direct_prompt_injection"
    SYSTEM_PROMPT_CANARY_LEAKAGE = "system_prompt_canary_leakage"
    TOOL_MISUSE_MANIPULATION = "tool_misuse_manipulation"
    UNTRUSTED_CODE_TEXT_INJECTION = "untrusted_code_text_injection"


class EligibilityStatus(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AttackEligibilityRequest(BaseModel):
    original_task: str = Field(min_length=1, max_length=20_000)


class AttackEligibilityItem(BaseModel):
    family: AttackFamily
    status: EligibilityStatus
    reason: str = Field(min_length=1, max_length=300)


class AttackEligibilityResponse(BaseModel):
    results: list[AttackEligibilityItem]

    @model_validator(mode="after")
    def contains_each_fixed_family_once(self):
        families = [item.family for item in self.results]
        if len(families) != len(AttackFamily) or set(families) != set(AttackFamily):
            raise ValueError("Eligibility output must contain each fixed attack family exactly once.")
        return self


class AttackGenerationRequest(BaseModel):
    original_task: str = Field(min_length=1, max_length=20_000)
    attack_family: AttackFamily


class AttackGenerationResult(BaseModel):
    attack_family: AttackFamily
    attack_prompt: str = Field(min_length=1, max_length=25_000)


class DefenseName(str, Enum):
    INPUT_SCREENING = "input_screening"
    OUTPUT_SCREENING = "output_screening"
    TOOL_AUTHORIZATION = "tool_authorization_least_privilege"
    INSTRUCTION_DATA_SEPARATION = "instruction_data_separation"


class ConditionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ExperimentRunRequest(BaseModel):
    original_task: str = Field(min_length=1, max_length=20_000)
    attack_prompt: str = Field(min_length=1, max_length=25_000)
    attack_family: AttackFamily
    model: str | None = Field(default=None, min_length=1, max_length=160)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, ge=1, le=8_000)
    generation_source: Literal["generated", "edited_generated", "manual"] = "edited_generated"
    attack_edited: bool = True

    @field_validator("model")
    @classmethod
    def requires_pinned_model(cls, value: str | None) -> str | None:
        if value is not None and value.casefold().startswith("auto/"):
            raise ValueError("Controlled experiments require an exact pinned model, not auto/*.")
        return value


class ExperimentConditionResponse(BaseModel):
    status: ConditionStatus
    raw_output: str | None = None
    visible_output: str | None = None
    actual_model: str | None = None
    provider_metadata: dict[str, Any] | None = None
    defense_evidence: dict[str, Any]
    tool_evidence: dict[str, Any] | None = None
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None
    error: str | None = None


class ExperimentRunResponse(BaseModel):
    experiment_id: str
    created_at: datetime
    status: ExperimentStatus
    original_task: str
    attack_prompt: str
    attack_family: AttackFamily
    mapped_defense: DefenseName
    model: str
    temperature: float
    max_output_tokens: int
    generation_source: str
    attack_edited: bool
    baseline: ExperimentConditionResponse
    defended: ExperimentConditionResponse


class EvaluationResponse(BaseModel):
    experiment_id: str
    attack_family: AttackFamily
    mapped_defense: DefenseName
    attack_success: bool | None
    benign_success: bool | None
    false_refusal: bool | None
    canary_leakage_raw: bool | None
    canary_leakage_visible: bool | None
    unauthorized_tool_attempted: bool | None
    unauthorized_tool_executed: bool | None
    evaluator_method: str
    evaluator_rationale: str
    latency_baseline_ms: float | None
    latency_defended_ms: float | None
    tokens_baseline_input: int | None
    tokens_baseline_output: int | None
    tokens_defended_input: int | None
    tokens_defended_output: int | None
    cost_baseline: float | None
    cost_defended: float | None
