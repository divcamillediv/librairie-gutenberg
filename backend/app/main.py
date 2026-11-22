"""Instance FastAPI et montage des routeurs (responsable : Camille).

Lancement en développement :
    cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Documentation interactive générée automatiquement : http://localhost:8000/docs
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import integration
from app.books.routes import router as books_router
from app.books.service import book_service
from app.config import settings
from app.books.schemas import Health
from app.search.routes import router as search_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Tout est chargé UNE fois ici ; rien n'est reconstruit à chaque requête."""
    book_service.load()
    integration.startup()
    yield


app = FastAPI(
    title="DAAR Projet 2 — Moteur de recherche de bibliothèque",
    description="Recherche par mot-clé et RegEx, classement PageRank, suggestions Jaccard.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=Health, tags=["health"], summary="État du backend")
def health() -> Health:
    return Health(
        status="ok",
        books_loaded=book_service.count(),
        data_source=book_service.source,
        modules=integration.module_status,
    )


app.include_router(search_router)
app.include_router(books_router)
