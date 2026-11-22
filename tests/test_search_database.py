"""Chaîne complète de la couche web avec les vrais modules (responsable : Camille).

- métadonnées lues depuis PostgreSQL (simulé ici), avec repli sur les fichiers ;
- recherche simple et RegEx de Kenza branchées sur l'API ;
- index, graphe et PageRank construits par les fonctions de l'équipe sur un
  petit corpus temporaire, puis chargés au démarrage comme en production.

Le test contre un vrai serveur PostgreSQL est dans tests/test_postgres.py.
"""
import json

import pytest
from fastapi.testclient import TestClient

from app.books import service as books_service
from app.config import settings
from app.errors import InvalidRegexError
from app.main import app
from app.ranking.pagerank import calculer_pagerank
from app.recommendations.graph_builder import construire_graphe
from app.search import inverted_index, regex_search, simple_search
from scripts.build_index import construire_index_des_livres, enregistrer_index

# Petit corpus : trois livres marins, deux livres de montagne, un livre isolé.
TEXTS = {
    1: "The whale rose from the sea. The harpooner saw the whale and the ship.",
    2: "A ship sailed the sea; a whale followed the ship to the island.",
    3: "Pirates buried treasure on the island and sailed the sea by ship.",
    4: "The mountain was covered in snow and the forest was silent.",
    5: "Snow fell on the forest; the mountain path vanished in the snow.",
    6: "Violins and pianos filled the concert hall with music.",
}
TITLES = {1: "The Whale", 2: "Sea Voyage", 3: "Treasure", 4: "Mountain", 5: "Snow Forest", 6: "Concert"}


def _rows():
    """Lignes renvoyées par app.config.database.load_books_from_postgres."""
    return [
        {"id": i, "title": TITLES[i], "author": f"Author {i}", "language": "en",
         "word_count": 12000, "file_path": f"data/raw/{i}.txt"}
        for i in TEXTS
    ]


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    """Dossier de données complet : textes, index, graphe et PageRank."""
    data = tmp_path_factory.mktemp("data")
    raw = data / "raw"
    raw.mkdir()
    for book_id, text in TEXTS.items():
        (raw / f"{book_id}.txt").write_text(text, encoding="utf-8")

    index = construire_index_des_livres(raw, seuil=0.99)
    enregistrer_index(index, data / "indexes" / "index_complet.json")

    terms = {book_id: set(text.lower().replace(";", " ").replace(".", " ").split())
             for book_id, text in TEXTS.items()}
    graph = construire_graphe(terms, seuil=0.2)
    graphs = data / "graphs"
    graphs.mkdir()
    (graphs / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    (graphs / "pagerank.json").write_text(json.dumps(calculer_pagerank(graph)), encoding="utf-8")
    return data


@pytest.fixture(scope="module")
def client(corpus):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "data_dir", corpus.resolve())
        mp.setattr(settings, "indexes_dir", corpus / "indexes")
        mp.setattr(settings, "graphs_dir", corpus / "graphs")
        mp.setattr(settings, "metadata_file", corpus / "metadata" / "books.json")
        mp.setattr(settings, "use_postgres", True)
        mp.setattr("app.config.database.load_books_from_postgres", _rows)
        with TestClient(app) as test_client:
            yield test_client


# ------------------------------------------------------------------ démarrage
def test_health_reports_postgres_and_real_modules(client):
    body = client.get("/api/health").json()
    assert body["data_source"] == "postgres"
    assert body["books_loaded"] == len(TEXTS)
    assert body["modules"] == {"search": "real", "regex": "real", "ranking": "real", "recommendations": "real"}


def test_catalogue_comes_from_database(client):
    body = client.get("/api/books", params={"limit": 100}).json()
    assert body["total"] == len(TEXTS)
    assert {b["title"] for b in body["books"]} == set(TITLES.values())
    book = client.get("/api/books/1").json()
    assert book["source_url"] == "https://www.gutenberg.org/ebooks/1"


def test_book_text_is_read_from_database_path(client):
    text = client.get("/api/books/1/text").json()["text"]
    assert text.startswith("The whale rose from the sea.")


# ------------------------------------------------------------------- recherche
def test_search_finds_books_in_database(client):
    body = client.get("/api/search", params={"q": "whale"}).json()
    assert {r["id"] for r in body["results"]} == {1, 2}
    assert body["results"][0]["id"] == 1  # 2 occurrences contre 1
    assert body["results"][0]["title"] == "The Whale"
    assert all(r["pagerank"] > 0 for r in body["results"])


def test_search_word_only_in_body(client):
    body = client.get("/api/search", params={"q": "harpooner"}).json()
    assert [r["id"] for r in body["results"]] == [1]


def test_search_multiple_words_is_and(client):
    body = client.get("/api/search", params={"q": "whale island"}).json()
    assert [r["id"] for r in body["results"]] == [2]


def test_search_ignores_case_punctuation_and_stopwords(client):
    reference = client.get("/api/search", params={"q": "whale"}).json()["results"]
    variant = client.get("/api/search", params={"q": "  The WHALE!  "}).json()["results"]
    assert [r["id"] for r in variant] == [r["id"] for r in reference]


def test_search_only_stopwords_returns_nothing(client):
    assert client.get("/api/search", params={"q": "the and"}).json()["total"] == 0


def test_search_suggestions_come_from_graph(client):
    body = client.get("/api/search", params={"q": "harpooner"}).json()
    suggested = {s["id"] for s in body["suggestions"]}
    assert suggested and suggested <= {2, 3}  # voisins marins, jamais la montagne ni le concert


def test_regex_matches_whole_terms(client):
    assert client.get("/api/search/advanced", params={"regex": "whal"}).json()["total"] == 0
    body = client.get("/api/search/advanced", params={"regex": "whal.*"}).json()
    assert {r["id"] for r in body["results"]} == {1, 2}


def test_regex_errors_are_400(client):
    for pattern in ["(unclosed", "(a+)+"]:
        response = client.get("/api/search/advanced", params={"regex": pattern})
        assert response.status_code == 400
        assert response.json()["detail"]


def test_similar_books_from_graph(client):
    body = client.get("/api/books/4/similar").json()
    assert [s["id"] for s in body["suggestions"]] == [5]
    assert client.get("/api/books/6/similar").json()["suggestions"] == []


# ------------------------------------------------------- fonctions branchées
def test_search_functions_directly(monkeypatch):
    monkeypatch.setattr(inverted_index, "index_charge", {"whale": {"1": 2}, "whaling": {"1": 1, "2": 1}})
    assert simple_search.search("") == {}
    assert simple_search.search("Whale") == {"1": 2}
    assert regex_search.regex_search("whal.*") == {"1": 3, "2": 1}
    assert regex_search.regex_search("hal") == {}
    with pytest.raises(InvalidRegexError):
        regex_search.regex_search("[")
    with pytest.raises(InvalidRegexError):
        regex_search.regex_search("(x+){2,}")
    with pytest.raises(InvalidRegexError):
        regex_search.regex_search("a" * 101)


# ------------------------------------------------- repli et chemins de fichiers
def test_database_failure_falls_back_to_files(monkeypatch, tmp_path):
    def broken():
        raise OSError("connexion refusée")

    monkeypatch.setattr(settings, "use_postgres", True)
    monkeypatch.setattr(settings, "metadata_file", tmp_path / "absent.json")
    monkeypatch.setattr("app.config.database.load_books_from_postgres", broken)
    service = books_service.BookService()
    service.load()
    assert service.source == "sample"
    assert service.count() == 10


@pytest.mark.parametrize("path", ["data/raw/1.txt", "raw/1.txt"])
def test_resolve_data_path_with_or_without_prefix(monkeypatch, tmp_path, path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    assert settings.resolve_data_path(path) == tmp_path / "raw" / "1.txt"


@pytest.mark.parametrize("path", ["../secret.txt", "data/../../secret.txt", "/etc/passwd"])
def test_resolve_data_path_refuses_escape(monkeypatch, tmp_path, path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    with pytest.raises(ValueError):
        settings.resolve_data_path(path)


# ------------------------------------------------ titres et auteurs de la base
def test_title_and_author_matches(client):
    body = client.get("/api/search", params={"q": "treasure"}).json()
    assert [r["id"] for r in body["results"]] == [3]  # le classement du texte est inchangé
    assert body["title_matches"] == []  # « Treasure » est déjà dans les résultats affichés

    by_author = client.get("/api/search", params={"q": "author 5"}).json()
    # « 5 » n'est pas une lettre : seul « author » compte, présent chez tous les auteurs
    assert len(by_author["title_matches"]) == 5

    # « voyage » n'est que dans le titre de « Sea Voyage », pas dans son texte.
    nothing_in_text = client.get("/api/search", params={"q": "Voyage"}).json()
    assert nothing_in_text["total"] == 0
    assert [b["id"] for b in nothing_in_text["title_matches"]] == [2]


def test_title_matches_only_on_first_page_of_simple_search(client):
    assert client.get("/api/search", params={"q": "treasure", "offset": 10}).json()["title_matches"] == []
    assert client.get("/api/search/advanced", params={"regex": "treasure"}).json()["title_matches"] == []
