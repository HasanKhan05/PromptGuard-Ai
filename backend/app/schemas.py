from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)
    model: str | None = Field(default=None, max_length=160)


class HealthResponse(BaseModel):
    status: str
    omniroute_configured: bool
    database: str
