"""Lecture des métadonnées dans un vrai serveur PostgreSQL.

Ignoré si POSTGRES_PASSWORD n'est pas défini ou si la base est injoignable.
Dans la CI, un service PostgreSQL est démarré pour ce test.
Le test travaille dans une table temporaire : il ne modifie pas la table books.
"""
import os
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from app.config import database  # noqa: E402

INIT_SQL = Path(__file__).resolve().parents[1] / "database" / "init.sql"


@pytest.fixture
def connexion():
    if not os.getenv("POSTGRES_PASSWORD"):
        pytest.skip("POSTGRES_PASSWORD non défini")
    try:
        conn = database.get_connection()
    except psycopg.OperationalError as exc:
        pytest.skip(f"PostgreSQL injoignable : {exc}")
    with conn:
        yield conn


def test_load_books_from_postgres(connexion, monkeypatch):
    with connexion.cursor() as cur:
        # Table temporaire du même schéma, prioritaire sur public.books pour cette session.
        cur.execute(INIT_SQL.read_text().replace("CREATE TABLE IF NOT EXISTS books", "CREATE TEMP TABLE books"))
        cur.execute(
            "INSERT INTO books (id, title, authors, language, word_count, file_path) VALUES "
            "('2701', 'Moby Dick', 'Herman Melville', 'en', 215000, 'raw/2701.txt'), "
            "('11', 'Alice', NULL, NULL, 27000, 'raw/11.txt')"
        )
        with pytest.raises(psycopg.errors.CheckViolation):
            with connexion.transaction():
                cur.execute("INSERT INTO books (id, title, word_count, file_path) VALUES ('1', 'Court', 50, 'raw/1.txt')")

    monkeypatch.setattr(database, "get_connection", lambda: _Reuse(connexion))
    rows = database.load_books_from_postgres()

    assert rows == [
        {"id": 11, "title": "Alice", "author": "", "language": "en", "word_count": 27000,
         "file_path": "data/raw/11.txt", "source_url": "https://www.gutenberg.org/ebooks/11"},
        {"id": 2701, "title": "Moby Dick", "author": "Herman Melville", "language": "en", "word_count": 215000,
         "file_path": "data/raw/2701.txt", "source_url": "https://www.gutenberg.org/ebooks/2701"},
    ]


class _Reuse:
    """Réutilise la connexion du test (et donc sa table temporaire) sans la fermer."""

    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, *exc):
        return False
