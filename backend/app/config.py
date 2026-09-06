import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _as_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _as_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    omniroute_base_url: str = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
    omniroute_api_key: str = os.getenv("OMNIROUTE_API_KEY", "")
    normal_assistant_model: str = os.getenv("NORMAL_ASSISTANT_MODEL", "auto/best-coding")
    normal_max_output_tokens: int = _as_int("NORMAL_MAX_OUTPUT_TOKENS", 1200)
    normal_temperature: float = _as_float("NORMAL_TEMPERATURE", 0.2)
    eligibility_max_output_tokens: int = _as_int("ELIGIBILITY_MAX_OUTPUT_TOKENS", 1200)
    attack_generation_max_output_tokens: int = _as_int("ATTACK_GENERATION_MAX_OUTPUT_TOKENS", 500)
    experiment_model: str = os.getenv("EXPERIMENT_MODEL", "gemini/gemini-3.1-flash-lite")
    experiment_temperature: float = _as_float("EXPERIMENT_TEMPERATURE", 0.2)
    experiment_max_output_tokens: int = _as_int("EXPERIMENT_MAX_OUTPUT_TOKENS", 800)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./promptguard.db")
    cors_origins: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if item.strip()
    )


@lru_cache

def get_settings() -> Settings:
    return Settings()
