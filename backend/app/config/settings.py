"""Chemins et configuration du backend (responsable : Camille).

Toute la configuration passe par des variables d'environnement afin que le même
code tourne en local (uvicorn) et dans Docker (volume monté sur /data).
"""
from __future__ import annotations

import os
from pathlib import Path

# Racine du dépôt en local : daar-search-engine/ (backend/app/config/settings.py -> parents[3]).
# Dans Docker, le code est dans /app/app/config/, donc parents[3] == "/" et DATA_DIR vaut /data.
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Configuration lue une seule fois au démarrage."""

    def __init__(self) -> None:
        # Un DATA_DIR relatif (ex. "./data") est résolu depuis la racine du projet,
        # pas depuis le dossier courant.
        data_dir = Path(os.getenv("DATA_DIR", "data"))
        self.data_dir: Path = (data_dir if data_dir.is_absolute() else _REPO_ROOT / data_dir).resolve()

        # Données réelles (produites par les scripts de Kenza et Nadine).
        self.metadata_file: Path = self.data_dir / "metadata" / "books.json"
        self.indexes_dir: Path = self.data_dir / "indexes"
        self.graphs_dir: Path = self.data_dir / "graphs"

        # Jeu d'exemple versionné : 10 livres simulés (voir scripts/make_sample_data.py).
        self.sample_dir: Path = self.data_dir / "sample"
        self.sample_metadata_file: Path = self.sample_dir / "books.json"

        # Métadonnées dans PostgreSQL : activé dès que POSTGRES_PASSWORD est défini
        # (voir app/config/database.py). USE_POSTGRES=0 force la lecture des fichiers.
        self.use_postgres: bool = bool(os.getenv("POSTGRES_PASSWORD")) and os.getenv(
            "USE_POSTGRES", "1"
        ) not in ("0", "false", "no")

        # CORS : "*" en développement ; liste d'origines séparées par des virgules sinon.
        self.cors_origins: list[str] = [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]

        # Garde-fous de l'API.
        self.max_query_length: int = int(os.getenv("MAX_QUERY_LENGTH", "200"))
        self.max_regex_length: int = int(os.getenv("MAX_REGEX_LENGTH", "100"))
        self.suggestions_limit: int = int(os.getenv("SUGGESTIONS_LIMIT", "6"))
        # Nombre de « meilleurs résultats » dont on suggère les voisins (énoncé : 2 ou 3).
        self.suggestions_top_k: int = int(os.getenv("SUGGESTIONS_TOP_K", "3"))
        # Le moteur simulé ne parcourt jamais plus de livres que cette limite.
        self.mock_max_books: int = int(os.getenv("MOCK_MAX_BOOKS", "50"))

    def resolve_data_path(self, relative_path: str) -> Path:
        """Résout un `file_path` de métadonnées (ex. "data/raw/123.txt" ou "raw/123.txt").

        Le chemin est relatif au dossier de données, avec ou sans le préfixe
        "data/" : il fonctionne donc quel que soit le nom réel de ce dossier
        (./data en local, /data dans Docker). On refuse tout chemin qui
        sortirait du dossier de données.
        """
        relative = Path(relative_path)
        if relative.is_absolute():
            raise ValueError(f"Chemin absolu refusé : {relative_path}")
        if relative.parts and relative.parts[0] == "data":
            relative = Path(*relative.parts[1:])
        candidate = (self.data_dir / relative).resolve()
        if not candidate.is_relative_to(self.data_dir):
            raise ValueError(f"Chemin hors du dossier de données : {relative_path}")
        return candidate


settings = Settings()
