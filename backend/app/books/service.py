"""Accès aux métadonnées et au texte intégral des livres (responsable : Camille).

Les métadonnées sont chargées une seule fois au démarrage. Si le corpus réel
(data/metadata/books.json, produit par Kenza) est absent, on se rabat sur les
10 livres simulés de data/sample/ pour que l'interface reste navigable.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class BookNotFoundError(LookupError):
    """Identifiant de livre inconnu."""


class BookTextUnavailableError(LookupError):
    """Le livre existe mais son fichier texte est introuvable."""


class PageOutOfRangeError(LookupError):
    """Numéro de page au-delà de la dernière page du livre."""


def _split_offsets(text: str, page_size: int) -> list[tuple[int, int]]:
    """Découpe `text` en pages d'environ `page_size` caractères.

    On coupe de préférence sur un saut de ligne, sinon sur une espace, pour ne
    jamais couper un mot en deux. Retourne la liste des bornes (début, fin).
    """
    offsets: list[tuple[int, int]] = []
    start, length = 0, len(text)
    while start < length:
        end = min(start + page_size, length)
        if end < length:
            floor = start + page_size // 2  # ne pas produire de page trop courte
            cut = text.rfind("\n", floor, end)
            if cut == -1:
                cut = text.rfind(" ", floor, end)
            if cut != -1:
                end = cut + 1
        offsets.append((start, end))
        start = end
    return offsets or [(0, 0)]


class BookService:
    """Catalogue en mémoire + lecture paginée des textes."""

    def __init__(self) -> None:
        self._books: dict[int, dict] = {}
        self._order: list[int] = []
        self._metadata_words: dict[int, tuple[set[str], set[str]]] | None = None
        self.source: str = "sample"

    # ------------------------------------------------------------------ chargement
    def load(self) -> None:
        """Charge les métadonnées une seule fois au démarrage.

        Ordre de priorité :
        1. PostgreSQL, si POSTGRES_PASSWORD est défini et la base joignable ;
        2. data/metadata/books.json, s'il existe ;
        3. les 10 livres simulés de data/sample/.
        """
        raw, origin = self._load_from_postgres(), "PostgreSQL"
        if raw is not None:
            self.source = "postgres"
        elif settings.metadata_file.exists():
            path = settings.metadata_file
            raw, origin, self.source = json.loads(path.read_text(encoding="utf-8")), str(path), "corpus"
        else:
            path = settings.sample_metadata_file
            logger.warning("Corpus réel absent : utilisation des livres simulés (%s).", path)
            raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
            origin, self.source = str(path), "sample"

        self._books = {int(book["id"]): self._normalize(book) for book in raw}
        self._order = sorted(self._books, key=lambda i: (self._books[i]["title"].lower(), i))
        self._metadata_words = None
        self._read_text.cache_clear()
        self._page_offsets.cache_clear()
        logger.info("%d livres chargés depuis %s", len(self._books), origin)

    @staticmethod
    def _load_from_postgres() -> list[dict] | None:
        """Métadonnées depuis PostgreSQL, ou None si la base n'est pas configurée ou joignable."""
        if not settings.use_postgres:
            return None
        try:
            from app.config.database import load_books_from_postgres

            books = load_books_from_postgres()
        except Exception as exc:  # pilote absent, base arrêtée, mot de passe faux, table absente...
            logger.error("PostgreSQL indisponible (%s) : repli sur les fichiers.", exc)
            return None
        if not books:
            logger.error("La table books de PostgreSQL est vide : repli sur les fichiers.")
            return None
        return books

    @staticmethod
    def _normalize(book: dict) -> dict:
        """Complète une ligne de métadonnées pour respecter le contrat de l'API."""
        book_id = int(book["id"])
        return {
            "id": book_id,
            "title": book.get("title") or f"Livre {book_id}",
            "author": book.get("author") or "",
            "language": book.get("language") or "en",
            "word_count": int(book.get("word_count") or 0),
            "file_path": book["file_path"],
            "source_url": book.get("source_url") or f"https://www.gutenberg.org/ebooks/{book_id}",
        }

    # ---------------------------------------------------------------- métadonnées
    def count(self) -> int:
        return len(self._books)

    def all_ids(self) -> list[int]:
        return list(self._order)

    def list(self, limit: int, offset: int) -> tuple[int, list[dict]]:
        """Retourne (total, livres de la page), triés par titre."""
        ids = self._order[offset : offset + limit]
        return len(self._order), [self._books[i] for i in ids]

    def match_metadata(self, query: str, limit: int = 5) -> list[dict]:
        """Livres dont le titre ou l'auteur contient tous les mots utiles de la requête.

        Même nettoyage que l'index (minuscules, lettres seulement, sans stopwords).
        Les titres qui contiennent les mots passent avant les auteurs, puis ordre alphabétique.
        """
        from app.search.nettoyage import decouper_mots, supprimer_stopwords
        from app.search.stopwords import STOPWORDS_ANGLAIS

        words = supprimer_stopwords(decouper_mots(query), STOPWORDS_ANGLAIS)
        if not words:
            return []
        if self._metadata_words is None:
            self._metadata_words = {
                book_id: (set(decouper_mots(book["title"])), set(decouper_mots(book["author"])))
                for book_id, book in self._books.items()
            }
        matches = []
        for book_id in self._order:
            title_words, author_words = self._metadata_words[book_id]
            if all(w in title_words for w in words):
                matches.append((0, book_id))
            elif all(w in title_words or w in author_words for w in words):
                matches.append((1, book_id))
        matches.sort(key=lambda m: m[0])  # tri stable : l'ordre alphabétique est conservé
        return [self._books[book_id] for _, book_id in matches[:limit]]

    def find(self, book_id: int) -> dict | None:
        return self._books.get(book_id)

    def get(self, book_id: int) -> dict:
        book = self._books.get(book_id)
        if book is None:
            raise BookNotFoundError(book_id)
        return book

    # ---------------------------------------------------------------------- texte
    def text_path(self, book_id: int) -> Path:
        return settings.resolve_data_path(self.get(book_id)["file_path"])

    @lru_cache(maxsize=16)
    def _read_text(self, book_id: int) -> str:
        try:
            path = self.text_path(book_id)
            return path.read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError) as exc:
            raise BookTextUnavailableError(book_id) from exc

    @lru_cache(maxsize=64)
    def _page_offsets(self, book_id: int, page_size: int) -> list[tuple[int, int]]:
        return _split_offsets(self._read_text(book_id), page_size)

    def read_text(self, book_id: int) -> str:
        """Texte intégral nettoyé d'un livre."""
        return self._read_text(book_id)

    def text_page(self, book_id: int, page: int, page_size: int) -> dict:
        """Une page du texte : {id, title, page, page_size, total_pages, text}."""
        book = self.get(book_id)
        offsets = self._page_offsets(book_id, page_size)
        if page > len(offsets):
            raise PageOutOfRangeError(page)
        start, end = offsets[page - 1]
        return {
            "id": book_id,
            "title": book["title"],
            "page": page,
            "page_size": page_size,
            "total_pages": len(offsets),
            "text": self._read_text(book_id)[start:end],
        }


# Instance unique partagée par les routeurs (chargée dans le lifespan de main.py).
book_service = BookService()
