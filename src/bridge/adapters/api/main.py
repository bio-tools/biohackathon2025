"""
FastAPI app definition and lifespan setup for the bridge service.
Initializes logging and mounts the routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bridge.logging import setup_logging

from .routers import biotools_to_github, github_to_biotools

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize registry and any global resources at app startup."""
    setup_logging("api")
    logger.info("Starting FastAPI application")
    yield


app = FastAPI(
    title="GitHub ⇄ bio.tools bridge",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# routes
app.include_router(github_to_biotools.router, prefix="/github-to-biotools")
app.include_router(biotools_to_github.router, prefix="/biotools-to-github")
