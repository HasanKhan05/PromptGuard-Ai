from fastapi import APIRouter

from ..config import get_settings
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        omniroute_configured=bool(settings.omniroute_api_key),
        database="sqlite" if settings.database_url.startswith("sqlite") else "configured",
    )
