"""Modèles Pydantic partagés : contrat JSON de l'API (voir docs/api_contract.md).

Toute modification de ces modèles doit être validée par l'équipe et reportée
dans docs/api_contract.md.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Book(BaseModel):
    """Métadonnées d'un livre (contrat commun, section 3 des instructions)."""

    id: int = Field(description="Identifiant unique stable (identifiant Gutenberg)")
    title: str
    author: str
    language: str = "en"
    word_count: int = Field(description="Nombre de mots avant filtrage des stopwords")
    file_path: str = Field(description="Chemin relatif du texte nettoyé")
    source_url: str = ""


class BookPage(BaseModel):
    """Liste paginée de livres."""

    total: int
    limit: int
    offset: int
    books: list[Book]


class BookText(BaseModel):
    """Une page du texte intégral d'un livre."""

    id: int
    title: str
    page: int = Field(description="Numéro de page, à partir de 1")
    page_size: int = Field(description="Taille cible d'une page, en caractères")
    total_pages: int
    text: str


class SearchResult(BaseModel):
    """Un livre dans la liste de résultats classés."""

    id: int
    title: str
    author: str
    occurrences: int = Field(description="Occurrences du mot-clé (ou des termes reconnus par la RegEx)")
    pagerank: float = Field(description="Centralité PageRank du livre dans le graphe de Jaccard")
    score: float = Field(description="Score combiné normalisé dans [0, 1]")


class Suggestion(BaseModel):
    """Un livre suggéré (voisin dans le graphe de Jaccard)."""

    id: int
    title: str
    author: str = ""
    similarity: float = Field(description="Similarité de Jaccard dans [0, 1]")


class BookSummary(BaseModel):
    """Livre trouvé par son titre ou son auteur (métadonnées de la base)."""

    id: int
    title: str
    author: str


class SearchResponse(BaseModel):
    """Réponse de /api/search et /api/search/advanced."""

    query: str
    mode: Literal["simple", "regex"]
    total: int = Field(description="Nombre total de livres correspondants")
    limit: int
    offset: int
    results: list[SearchResult]
    suggestions: list[Suggestion]
    title_matches: list[BookSummary] = Field(
        default_factory=list,
        description="Recherche simple : livres dont le titre ou l'auteur contient la requête "
        "(complément, hors classement)",
    )


class SimilarResponse(BaseModel):
    """Réponse de /api/books/{book_id}/similar."""

    book_id: int
    suggestions: list[Suggestion]


class ModuleStatus(BaseModel):
    """Origine des réponses : "real" (module de l'équipe) ou "mock" (simulation)."""

    search: str
    regex: str
    ranking: str
    recommendations: str


class Health(BaseModel):
    """Réponse de /api/health."""

    status: str
    books_loaded: int
    data_source: Literal["postgres", "corpus", "sample"]
    modules: ModuleStatus
