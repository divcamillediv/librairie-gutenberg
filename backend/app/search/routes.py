"""Routes /api/search : recherche simple et recherche avancée (RegEx).

Câblage FastAPI réalisé par Camille. La logique de recherche elle-même est dans
simple_search.py et regex_search.py (Kenza) ; le classement et les suggestions
viennent des modules de Nadine, tous appelés via app/integration.py.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app import integration
from app.books.service import book_service
from app.config import settings
from app.errors import InvalidRegexError
from app.books.schemas import BookSummary, SearchResponse, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])


def _build_response(query: str, mode: str, matches: dict[int, int], limit: int, offset: int) -> SearchResponse:
    """Classe les correspondances, pagine, enrichit et ajoute les suggestions."""
    ranked = [row for row in integration.rank(matches) if book_service.find(row["id"])]
    page = ranked[offset : offset + limit]

    results = []
    for row in page:
        book = book_service.get(row["id"])
        results.append(
            SearchResult(
                id=book["id"],
                title=book["title"],
                author=book["author"],
                occurrences=row["occurrences"],
                pagerank=row["pagerank"],
                score=row["score"],
            )
        )

    # Suggestions : voisins Jaccard des 2-3 meilleurs résultats, hors livres déjà affichés.
    top_ids = [row["id"] for row in ranked[: settings.suggestions_top_k]]
    displayed = {row["id"] for row in page}
    suggestions = (
        integration.suggest(top_ids, exclude=displayed, limit=settings.suggestions_limit)
        if top_ids
        else []
    )
    return SearchResponse(
        query=query,
        mode=mode,
        total=len(ranked),
        limit=limit,
        offset=offset,
        results=results,
        suggestions=suggestions,
    )


@router.get("", response_model=SearchResponse, summary="Recherche par mot-clé")
def search(
    q: str = Query("", description="Mot-clé recherché dans l'index du contenu des livres"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SearchResponse:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="La requête est vide.")
    if len(query) > settings.max_query_length:
        raise HTTPException(
            status_code=400,
            detail=f"La requête dépasse {settings.max_query_length} caractères.",
        )
    response = _build_response(query, "simple", integration.search_simple(query), limit, offset)
    # Complément : livres dont le titre ou l'auteur correspond, affichés à part du classement.
    # Les livres déjà affichés dans les résultats de la page ne sont pas répétés.
    if offset == 0:
        shown = {r.id for r in response.results}
        response.title_matches = [
            BookSummary(id=b["id"], title=b["title"], author=b["author"])
            for b in book_service.match_metadata(query, limit=5 + len(shown))
            if b["id"] not in shown
        ][:5]
    return response


@router.get("/advanced", response_model=SearchResponse, summary="Recherche avancée par RegEx")
def advanced_search(
    regex: str = Query("", description="Expression régulière appliquée aux termes indexés"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SearchResponse:
    pattern = regex.strip()
    if not pattern:
        raise HTTPException(status_code=400, detail="L'expression régulière est vide.")
    if len(pattern) > settings.max_regex_length:
        raise HTTPException(
            status_code=400,
            detail=f"L'expression régulière dépasse {settings.max_regex_length} caractères.",
        )
    try:
        matches = integration.search_regex(pattern)
    except InvalidRegexError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _build_response(pattern, "regex", matches, limit, offset)
