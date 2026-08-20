"""
TamperTrace — FastAPI application entry point.

Configures CORS for the React frontend, registers API routers, and
provides a ``GET /healthz`` health-check endpoint.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.schemas.analysis import HealthResponse

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

app = FastAPI(
    title="TamperTrace API",
    description="Document tampering detection — forensic analysis service.",
    version=__version__,
)

# ── CORS ───────────────────────────────────────────────────────────────
# Allow the React dev servers (Vite default + CRA default).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(analyze_router)


# ── Health check ───────────────────────────────────────────────────────
@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["health"],
    summary="Service health check",
)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


# ── Frontend Serving ───────────────────────────────────────────────────
# Serve the static files from the React build folder
frontend_dist = os.path.join(os.path.dirname(__file__), "../../frontend/dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=f"{frontend_dist}/assets"), name="assets")
    
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str):
        # Route all non-API traffic to the React index.html
        if catchall.startswith("api/"):
            return {"error": "API route not found"}
        return FileResponse(f"{frontend_dist}/index.html")