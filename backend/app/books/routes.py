"""Routes /api/books : catalogue, métadonnées, lecture et livres similaires."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app import integration
from app.books.service import (
    BookNotFoundError,
    BookTextUnavailableError,
    PageOutOfRangeError,
    book_service,
)
from app.config import settings
from app.books.schemas import Book, BookPage, BookText, SimilarResponse

router = APIRouter(prefix="/api/books", tags=["books"])


def _get_or_404(book_id: int) -> dict:
    try:
        return book_service.get(book_id)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail=f"Livre {book_id} introuvable.")


@router.get("", response_model=BookPage, summary="Livres paginés")
def list_books(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> BookPage:
    total, books = book_service.list(limit, offset)
    return BookPage(total=total, limit=limit, offset=offset, books=books)


@router.get("/{book_id}", response_model=Book, summary="Métadonnées d'un livre")
def get_book(book_id: int) -> dict:
    return _get_or_404(book_id)


@router.get("/{book_id}/text", response_model=BookText, summary="Texte intégral paginé")
def get_book_text(
    book_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(4000, ge=500, le=20000, description="Caractères par page"),
) -> dict:
    _get_or_404(book_id)
    try:
        return book_service.text_page(book_id, page, page_size)
    except BookTextUnavailableError:
        raise HTTPException(
            status_code=404, detail=f"Le texte du livre {book_id} n'est pas disponible."
        )
    except PageOutOfRangeError:
        raise HTTPException(status_code=404, detail=f"La page {page} n'existe pas pour ce livre.")


@router.get("/{book_id}/similar", response_model=SimilarResponse, summary="Voisins recommandés")
def get_similar_books(
    book_id: int,
    limit: int = Query(settings.suggestions_limit, ge=1, le=20),
) -> SimilarResponse:
    _get_or_404(book_id)
    suggestions = integration.suggest([book_id], exclude={book_id}, limit=limit)
    return SimilarResponse(book_id=book_id, suggestions=suggestions)
