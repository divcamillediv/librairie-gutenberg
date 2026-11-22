"""Moteur SIMULÉ (responsable : Camille) — étape 3 : « réponses simulées sur 10 livres ».

Ce module permet de développer et de démontrer l'interface sans attendre les
modules de Kenza (index, recherche) et de Nadine (PageRank, classement,
suggestions). Il n'est PAS le moteur du rendu final :

* pas d'index inversé : les textes sont parcourus et comptés en mémoire ;
* pas de stemming ni de stopwords ;
* PageRank et voisins lus dans data/sample/ (valeurs fictives) ;
* formule de classement provisoire.

Dès qu'une fonction réelle est implémentée, app/integration.py cesse
automatiquement d'appeler la simulation correspondante.
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter

from app.books.service import BookTextUnavailableError, book_service
from app.config import settings
from app.errors import InvalidRegexError

logger = logging.getLogger(__name__)

_TOKEN = re.compile(r"[a-z]+")

# Poids provisoires du score simulé (la vraie formule est à définir par Nadine).
_W_OCCURRENCES = 0.7
_W_PAGERANK = 0.3


def tokenize(text: str) -> list[str]:
    """Normalisation minimale de la simulation : minuscules + mots alphabétiques."""
    return _TOKEN.findall(text.lower())


class MockEngine:
    """Recherche, classement et suggestions simulés sur un petit nombre de livres."""

    def __init__(self) -> None:
        self._frequencies: dict[int, Counter] | None = None
        self._pagerank: dict[int, float] | None = None
        self._neighbors: dict[int, list[dict]] | None = None

    def reset(self) -> None:
        self._frequencies = self._pagerank = self._neighbors = None

    # ------------------------------------------------------------ données simulées
    def _freqs(self) -> dict[int, Counter]:
        """Fréquences des mots par livre, calculées une fois au premier appel."""
        if self._frequencies is None:
            ids = book_service.all_ids()
            if len(ids) > settings.mock_max_books:
                logger.warning(
                    "Simulation limitée aux %d premiers livres sur %d.",
                    settings.mock_max_books,
                    len(ids),
                )
                ids = ids[: settings.mock_max_books]
            frequencies: dict[int, Counter] = {}
            for book_id in ids:
                try:
                    frequencies[book_id] = Counter(tokenize(book_service.read_text(book_id)))
                except BookTextUnavailableError:
                    continue
            self._frequencies = frequencies
        return self._frequencies

    def _load_json(self, name: str) -> dict:
        path = settings.sample_dir / name
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _pageranks(self) -> dict[int, float]:
        if self._pagerank is None:
            self._pagerank = {int(k): float(v) for k, v in self._load_json("pagerank.json").items()}
        return self._pagerank

    def _neighbor_lists(self) -> dict[int, list[dict]]:
        if self._neighbors is None:
            self._neighbors = {int(k): v for k, v in self._load_json("neighbors.json").items()}
        return self._neighbors

    # ------------------------------------------------------------------ recherche
    def search(self, query: str) -> dict[int, int]:
        """book_id -> occurrences. Plusieurs mots : le livre doit tous les contenir."""
        terms = tokenize(query)
        if not terms:
            return {}
        matches: dict[int, int] = {}
        for book_id, counter in self._freqs().items():
            if all(counter[term] > 0 for term in terms):
                matches[book_id] = sum(counter[term] for term in terms)
        return matches

    def regex_search(self, pattern: str) -> dict[int, int]:
        """book_id -> occurrences cumulées des mots qui vérifient entièrement la RegEx."""
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise InvalidRegexError(f"Expression régulière invalide : {exc}") from exc

        frequencies = self._freqs()
        vocabulary = set().union(*frequencies.values()) if frequencies else set()
        matching_terms = {term for term in vocabulary if compiled.fullmatch(term)}
        matches: dict[int, int] = {}
        for book_id, counter in frequencies.items():
            occurrences = sum(counter[term] for term in matching_terms if term in counter)
            if occurrences:
                matches[book_id] = occurrences
        return matches

    # ----------------------------------------------------------------- classement
    def rank_results(self, results: dict[int, int]) -> list[dict]:
        """Classement provisoire : 0,7 × occurrences normalisées + 0,3 × PageRank normalisé."""
        if not results:
            return []
        pageranks = self._pageranks()
        default_pr = 1.0 / max(book_service.count(), 1)
        max_occurrences = max(results.values())
        max_pagerank = max((pageranks.get(i, default_pr) for i in results), default=default_pr)
        ranked = []
        for book_id, occurrences in results.items():
            pagerank = pageranks.get(book_id, default_pr)
            score = (
                _W_OCCURRENCES * occurrences / max_occurrences
                + _W_PAGERANK * pagerank / max_pagerank
            )
            ranked.append(
                {
                    "id": book_id,
                    "occurrences": occurrences,
                    "pagerank": round(pagerank, 6),
                    "score": round(score, 4),
                }
            )
        ranked.sort(key=lambda r: (-r["score"], r["id"]))
        return ranked

    # ---------------------------------------------------------------- suggestions
    def recommend(self, book_ids: list[int], exclude: set[int] | None = None, limit: int = 6) -> list[dict]:
        """Voisins (fictifs) des livres donnés, dédoublonnés, triés par similarité."""
        excluded = set(exclude or ()) | set(book_ids)
        best: dict[int, float] = {}
        for book_id in book_ids:
            for neighbor in self._neighbor_lists().get(book_id, []):
                neighbor_id, similarity = int(neighbor["id"]), float(neighbor["similarity"])
                if neighbor_id not in excluded and similarity > best.get(neighbor_id, 0.0):
                    best[neighbor_id] = similarity
        ordered = sorted(best.items(), key=lambda item: (-item[1], item[0]))[:limit]
        return [{"id": book_id, "similarity": similarity} for book_id, similarity in ordered]


mock_engine = MockEngine()
