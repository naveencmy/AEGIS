from backend.app.api.routes_query import router as query_router
from backend.app.api.routes_ingest import router as ingest_router
from backend.app.api.routes_intel import router as intel_router
from backend.app.api.routes_health import router as health_router

__all__ = ["query_router", "ingest_router", "intel_router", "health_router"]
