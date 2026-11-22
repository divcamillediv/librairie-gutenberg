"""Couche d'intégration (responsable : Camille) — étape C4 du plan.

Unique point de contact entre les routes FastAPI et les modules de l'équipe :

* Kenza  : app.search.simple_search.search, app.search.regex_search.regex_search
* Nadine : app.ranking.ranking_service.rank_results,
           app.recommendations.recommendation_service.recommend

Tant qu'une de ces fonctions n'existe pas encore (fichier squelette) ou lève
NotImplementedError (TODO non réalisé), ou que le fichier pré-calculé dont elle
dépend n'a pas pu être chargé (index, graphe, PageRank absent ou illisible), la
réponse provient du moteur simulé (app/mocks.py), et /api/health l'indique. Aucun fichier de Kenza ou de Nadine
n'a donc besoin d'être modifié pour que l'application tourne.

Les identifiants renvoyés par les modules sont convertis en entiers : un module
peut renvoyer des identifiants Gutenberg sous forme de chaînes ("2701").
"""
from __future__ import annotations

import importlib
import logging
from typing import Callable

from app.books.service import book_service
from app.config import settings
from app.mocks import mock_engine

logger = logging.getLogger(__name__)

# Origine des réponses par module : "real" ou "mock" (exposé par /api/health).
module_status: dict[str, str] = {
    "search": "mock",
    "regex": "mock",
    "ranking": "mock",
    "recommendations": "mock",
}


class _NotAvailable(Exception):
    """Fonction absente du module (squelette) ou module introuvable."""


def _resolve(module_name: str, function_name: str) -> Callable:
    """Retourne app.<module_name>.<function_name>, ou lève _NotAvailable."""
    try:
        module = importlib.import_module(f"app.{module_name}")
    except ImportError as exc:
        raise _NotAvailable(f"app.{module_name}") from exc
    function = getattr(module, function_name, None)
    if not callable(function):
        raise _NotAvailable(f"app.{module_name}.{function_name}")
    return function


# Fichiers pré-calculés chargés au démarrage, et modules qui en dépendent.
artifacts_loaded: dict[str, bool] = {"index": False, "graph": False, "pagerank": False}
_REQUIRES = {
    "search": "index",
    "regex": "index",
    "ranking": "pagerank",
    "recommendations": "graph",
}


def _call(name: str, target: tuple[str, str], mock: Callable, *args, **kwargs):
    """Appelle la fonction réelle ; bascule sur la simulation si elle est absente, en TODO,
    ou si le fichier pré-calculé dont elle dépend n'est pas chargé."""
    if not artifacts_loaded[_REQUIRES[name]]:
        module_status[name] = "mock"
        return mock(*args, **kwargs)
    try:
        real = _resolve(*target)
        result = real(*args, **kwargs)
    except (_NotAvailable, NotImplementedError):
        module_status[name] = "mock"
        return mock(*args, **kwargs)
    module_status[name] = "real"
    return result


_SEARCH = ("search.simple_search", "search")
_REGEX = ("search.regex_search", "regex_search")
_RANK = ("ranking.ranking_service", "rank_results")
_RECOMMEND = ("recommendations.recommendation_service", "recommend")


# ------------------------------------------------------------------------ démarrage
def startup() -> None:
    """Charge une seule fois les fichiers pré-calculés (index, graphe, PageRank)."""
    mock_engine.reset()
    loaders = [
        ("index", "index inversé (Kenza)", ("search.inverted_index", "load_index"), settings.indexes_dir),
        ("graph", "graphe de Jaccard (Nadine)", ("recommendations.graph_builder", "load_graph"), settings.graphs_dir),
        ("pagerank", "PageRank (Nadine)", ("ranking.pagerank", "load_pagerank"), settings.graphs_dir),
    ]
    for key, label, target, directory in loaders:
        artifacts_loaded[key] = False
        try:
            _resolve(*target)(directory)
        except (_NotAvailable, NotImplementedError):
            logger.warning("Non implémenté, simulation utilisée : %s", label)
        except FileNotFoundError as exc:
            logger.warning("Fichier absent (%s), simulation utilisée : %s", exc.filename, label)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # Fichier illisible ou au mauvais format : l'API démarre quand même.
            logger.error("Chargement impossible (%s), simulation utilisée : %s", exc, label)
        else:
            artifacts_loaded[key] = True
            logger.info("Chargé : %s", label)

    # Sondes : déterminent dès le démarrage quels modules sont réels.
    _call("search", _SEARCH, mock_engine.search, "probe")
    _call("regex", _REGEX, mock_engine.regex_search, "probe")
    _call("ranking", _RANK, mock_engine.rank_results, {})
    _call("recommendations", _RECOMMEND, mock_engine.recommend, [])
    logger.info("État des modules : %s", module_status)


# ------------------------------------------------------------------------- services
def _int_keys(matches: dict) -> dict[int, int]:
    return {int(book_id): int(count) for book_id, count in matches.items()}


def search_simple(query: str) -> dict[int, int]:
    """Mot-clé -> {book_id: occurrences}."""
    return _int_keys(_call("search", _SEARCH, mock_engine.search, query))


def search_regex(pattern: str) -> dict[int, int]:
    """RegEx -> {book_id: occurrences}. Peut lever InvalidRegexError."""
    return _int_keys(_call("regex", _REGEX, mock_engine.regex_search, pattern))


def rank(results: dict[int, int]) -> list[dict]:
    """{book_id: occurrences} -> [{id, occurrences, pagerank, score}] trié par score décroissant."""
    rows = _call("ranking", _RANK, mock_engine.rank_results, results)
    return [{**row, "id": int(row["id"])} for row in rows]


def suggest(book_ids: list[int], exclude: set[int] | None = None, limit: int = 6) -> list[dict]:
    """Voisins Jaccard enrichis des métadonnées : [{id, title, author, similarity}]."""
    raw = _call("recommendations", _RECOMMEND, mock_engine.recommend, book_ids, exclude=exclude, limit=limit)
    suggestions, seen = [], set()
    for item in raw:
        book = book_service.find(int(item["id"]))
        if book is None or book["id"] in seen:  # identifiant inconnu ou doublon
            continue
        seen.add(book["id"])
        suggestions.append(
            {
                "id": book["id"],
                "title": book["title"],
                "author": book["author"],
                "similarity": round(float(item["similarity"]), 4),
            }
        )
    return suggestions
