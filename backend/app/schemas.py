from enum import Enum

from pydantic import BaseModel, Field, model_validator


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
