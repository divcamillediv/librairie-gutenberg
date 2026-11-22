"""Connexion du backend à PostgreSQL et chargement des métadonnées."""

import os

import psycopg
from psycopg.rows import dict_row


def get_connection():
    """Ouvre une connexion à PostgreSQL."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "gutenberg"),
        user=os.getenv("POSTGRES_USER", "gutenberg"),
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "3")),
        row_factory=dict_row
    )


def load_books_from_postgres() -> list[dict]:
    """Charge les métadonnées au format attendu par le backend."""
    with get_connection() as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("""
                SELECT
                    CAST(id AS INTEGER) AS id,
                    title,
                    COALESCE(authors, '') AS author,
                    COALESCE(language, 'en') AS language,
                    word_count,
                    'data/' || file_path AS file_path,
                    'https://www.gutenberg.org/ebooks/' || id AS source_url
                FROM books
                ORDER BY title, CAST(id AS INTEGER)
            """)

            return curseur.fetchall()
