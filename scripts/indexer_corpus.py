
"""Construit et enregistre l'index des livres disponibles."""

from pathlib import Path

from scripts.build_index import construire_index_des_livres, enregistrer_index


def indexer_corpus(dossier_livres: Path, chemin_index: Path) -> None:
    """Construit l'index d'un dossier et l'enregistre en JSON."""

    # On construit l'index à partir des livres
    index = construire_index_des_livres(dossier_livres)

    # On enregistre le résultat
    enregistrer_index(index, chemin_index)
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage : python -m scripts.indexer_corpus DOSSIER_LIVRES FICHIER_INDEX")
        sys.exit(1)

    dossier_livres = Path(sys.argv[1])
    chemin_index = Path(sys.argv[2])

    indexer_corpus(dossier_livres, chemin_index)
    print(f"Index enregistré dans {chemin_index}")