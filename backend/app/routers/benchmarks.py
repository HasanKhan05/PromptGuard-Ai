from fastapi import APIRouter

from ..db import SessionLocal
from ..schemas import BenchmarkMetricsResponse
from ..services.benchmarks import calculate_benchmark_metrics

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("", response_model=BenchmarkMetricsResponse)
@router.get("/", response_model=BenchmarkMetricsResponse)
def get_benchmarks() -> BenchmarkMetricsResponse:
    db = SessionLocal()
    try:
        return calculate_benchmark_metrics(db)
    finally:
        db.close()
