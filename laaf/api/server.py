"""
LAAF FastAPI server — REST API + Web Dashboard.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import laaf
from laaf.api.routes import health, scans, reports, techniques

_DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"


def create_app() -> FastAPI:
    app = FastAPI(
        title="LAAF — Logic-layer Automated Attack Framework",
        description=(
            "Enterprise REST API for LPCI red-teaming. "
            "Reference: Atta et al., Qorvex Research, 2026."
        ),
        version=laaf.__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router)
    app.include_router(scans.router)
    app.include_router(reports.router)
    app.include_router(techniques.router)

    # Static files + Jinja2 templates for dashboard
    static_dir = _DASHBOARD_DIR / "static"
    templates_dir = _DASHBOARD_DIR / "templates"

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))

        @app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
        async def dashboard(request: Request):
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "version": laaf.__version__},
            )
    else:
        @app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
        async def dashboard_fallback():
            return HTMLResponse("<h1>Dashboard templates not found. Run from repo root.</h1>")

    return app
