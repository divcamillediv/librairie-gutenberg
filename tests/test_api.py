"""Tests de l'API FastAPI (responsable : Camille).

Ces tests vérifient le CONTRAT (codes HTTP, forme des réponses, pagination,
erreurs) sur le jeu d'exemple de 10 livres simulés. Ils restent valables quand
les vrais modules de recherche et de classement remplacent la simulation.

    pytest tests/test_api.py
"""
import time

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """API isolée sur le jeu d'exemple de 10 livres.

    Les fichiers du corpus réel (métadonnées, index, graphe, PageRank) sont
    remplacés par des emplacements vides : les tests donnent le même résultat
    sur une machine qui a le corpus complet et dans la CI qui ne l'a pas.
    """
    empty = tmp_path_factory.mktemp("no-corpus")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "use_postgres", False)
        mp.setattr(settings, "metadata_file", empty / "books.json")
        mp.setattr(settings, "indexes_dir", empty)
        mp.setattr(settings, "graphs_dir", empty)
        # Le bloc `with` déclenche le lifespan : chargement des données au démarrage.
        with TestClient(app) as test_client:
            yield test_client


# --------------------------------------------------------------------------- santé
def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["books_loaded"] == 10
    assert body["data_source"] == "sample"
    assert set(body["modules"]) == {"search", "regex", "ranking", "recommendations"}


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200


# -------------------------------------------------------------------------- livres
def test_books_pagination(client):
    first = client.get("/api/books", params={"limit": 4, "offset": 0}).json()
    second = client.get("/api/books", params={"limit": 4, "offset": 4}).json()
    assert first["total"] >= 10
    assert len(first["books"]) == 4
    assert {b["id"] for b in first["books"]}.isdisjoint(b["id"] for b in second["books"])


def test_books_invalid_pagination(client):
    assert client.get("/api/books", params={"limit": 0}).status_code == 422
    assert client.get("/api/books", params={"offset": -1}).status_code == 422


def test_book_metadata_follows_contract(client):
    book = client.get("/api/books/2701").json()
    assert set(book) == {"id", "title", "author", "language", "word_count", "file_path", "source_url"}
    assert book["id"] == 2701
    assert not book["file_path"].startswith("/")  # jamais de chemin absolu


def test_book_not_found(client):
    response = client.get("/api/books/999999999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_book_text_is_readable_and_paginated(client):
    first = client.get("/api/books/2701/text", params={"page": 1, "page_size": 500}).json()
    assert first["total_pages"] > 1
    assert first["text"].strip()
    # Les pages recollées redonnent le texte complet.
    pages = [
        client.get("/api/books/2701/text", params={"page": p, "page_size": 500}).json()["text"]
        for p in range(1, first["total_pages"] + 1)
    ]
    full = client.get("/api/books/2701/text", params={"page_size": 20000}).json()["text"]
    assert "".join(pages) == full


def test_book_text_errors(client):
    assert client.get("/api/books/999999999/text").status_code == 404
    assert client.get("/api/books/2701/text", params={"page": 9999}).status_code == 404
    assert client.get("/api/books/2701/text", params={"page": 0}).status_code == 422


def test_similar_books(client):
    body = client.get("/api/books/2701/similar").json()
    ids = [s["id"] for s in body["suggestions"]]
    assert body["book_id"] == 2701
    assert 2701 not in ids
    assert len(ids) == len(set(ids))
    assert all(0.0 <= s["similarity"] <= 1.0 for s in body["suggestions"])
    assert client.get("/api/books/999999999/similar").status_code == 404


# ----------------------------------------------------------------------- recherche
def test_search_word_present_only_in_body(client):
    """« harpooner » n'apparaît dans aucun titre : seul le contenu permet de trouver le livre."""
    body = client.get("/api/search", params={"q": "harpooner"}).json()
    assert body["mode"] == "simple"
    assert body["total"] == 1
    assert body["results"][0]["id"] == 2701


def test_search_result_contract_and_order(client):
    body = client.get("/api/search", params={"q": "ship"}).json()
    assert body["total"] >= 2
    for result in body["results"]:
        assert set(result) == {"id", "title", "author", "occurrences", "pagerank", "score"}
        assert result["occurrences"] >= 1
        assert 0.0 <= result["score"] <= 1.0
    scores = [r["score"] for r in body["results"]]
    assert scores == sorted(scores, reverse=True)


def test_search_suggestions_have_no_duplicates(client):
    body = client.get("/api/search", params={"q": "whale"}).json()
    suggested = [s["id"] for s in body["suggestions"]]
    assert suggested, "le jeu d'exemple doit produire des suggestions"
    assert len(suggested) == len(set(suggested))
    assert set(suggested).isdisjoint(r["id"] for r in body["results"])


def test_search_is_case_insensitive(client):
    lower = client.get("/api/search", params={"q": "whale"}).json()
    upper = client.get("/api/search", params={"q": "WHALE"}).json()
    assert [r["id"] for r in lower["results"]] == [r["id"] for r in upper["results"]]


def test_search_unknown_term(client):
    body = client.get("/api/search", params={"q": "zzzzqqqq"}).json()
    assert body == {**body, "total": 0, "results": [], "suggestions": []}


def test_search_empty_query(client):
    assert client.get("/api/search").status_code == 400
    assert client.get("/api/search", params={"q": "   "}).status_code == 400


def test_search_too_long_query(client):
    assert client.get("/api/search", params={"q": "a" * 500}).status_code == 400


def test_search_pagination(client):
    everything = client.get("/api/search", params={"q": "the", "limit": 100}).json()
    page = client.get("/api/search", params={"q": "the", "limit": 3, "offset": 3}).json()
    assert page["total"] == everything["total"]
    assert [r["id"] for r in page["results"]] == [r["id"] for r in everything["results"][3:6]]


# --------------------------------------------------------------------------- RegEx
def test_regex_valid_pattern(client):
    body = client.get("/api/search/advanced", params={"regex": "whal(e|es|ing)"}).json()
    assert body["mode"] == "regex"
    assert 2701 in [r["id"] for r in body["results"]]


def test_regex_invalid_pattern(client):
    response = client.get("/api/search/advanced", params={"regex": "(unclosed"})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_regex_no_match(client):
    body = client.get("/api/search/advanced", params={"regex": "zzzz+q"}).json()
    assert body["total"] == 0 and body["results"] == []


def test_regex_empty_or_too_long(client):
    assert client.get("/api/search/advanced").status_code == 400
    assert client.get("/api/search/advanced", params={"regex": "a" * 300}).status_code == 400


# --------------------------------------------------------------------- performance
def test_response_time_is_reasonable(client):
    """Garde-fou léger : une recherche sur le jeu d'exemple répond en moins d'une seconde."""
    start = time.perf_counter()
    for _ in range(20):
        assert client.get("/api/search", params={"q": "sea"}).status_code == 200
    assert (time.perf_counter() - start) / 20 < 1.0


# ------------------------------------------------------------ fichiers pré-calculés
def test_missing_artifacts_do_not_crash_startup(client):
    """Sans index, graphe ni PageRank, l'API démarre et signale la simulation."""
    modules = client.get("/api/health").json()["modules"]
    assert modules == {"search": "mock", "regex": "mock", "ranking": "mock", "recommendations": "mock"}
