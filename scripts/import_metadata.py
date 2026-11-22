
import json
import os
from pathlib import Path

import psycopg


DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
METADATA_DIR = DATA_DIR / "metadata"
RAW_DIR = DATA_DIR / "raw"


def importer_metadata():
    fichiers = sorted(METADATA_DIR.glob("*.json"))

    if not fichiers:
        raise RuntimeError("Aucun fichier de métadonnées trouvé.")

    with psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "gutenberg"),
            user=os.getenv("POSTGRES_USER", "gutenberg"),
            password=os.environ["POSTGRES_PASSWORD"]
    ) as connexion:

        with connexion.cursor() as curseur:
            for fichier in fichiers:
                metadata = json.loads(
                    fichier.read_text(encoding="utf-8-sig")
                )

                livre_id = str(metadata["text_id"])
                chemin = RAW_DIR / f"{livre_id}.txt"

                texte = chemin.read_text(encoding="utf-8-sig")
                nombre_mots = len(texte.split())

                curseur.execute("""
                                INSERT INTO books (
                                    id, title, authors, language,
                                    issued, subjects, locc, bookshelves,
                                    word_count, file_path
                                )
                                VALUES (
                                           %s, %s, %s, %s, %s,
                                           %s, %s, %s, %s, %s
                                       )
                                    ON CONFLICT (id) DO UPDATE SET
                                    title = EXCLUDED.title,
                                                            authors = EXCLUDED.authors,
                                                            language = EXCLUDED.language,
                                                            issued = EXCLUDED.issued,
                                                            subjects = EXCLUDED.subjects,
                                                            locc = EXCLUDED.locc,
                                                            bookshelves = EXCLUDED.bookshelves,
                                                            word_count = EXCLUDED.word_count,
                                                            file_path = EXCLUDED.file_path
                                """, (
                                    livre_id,
                                    metadata["title"],
                                    metadata.get("authors"),
                                    metadata.get("language"),
                                    metadata.get("issued") or None,
                                    metadata.get("subjects"),
                                    metadata.get("locc"),
                                    metadata.get("bookshelves"),
                                    nombre_mots,
                                    f"raw/{livre_id}.txt"
                                ))

    print(f"Importation réussie : {len(fichiers)} livres.")


if __name__ == "__main__":
    importer_metadata()
