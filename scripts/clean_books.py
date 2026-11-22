"""Prepare les fichiers des livres pour l'index."""

import argparse
import json
from pathlib import Path

from backend.app.search.nettoyage import decouper_mots


def nettoyer_fichier(source: Path, sortie: Path) -> None:
    """Lit un livre et enregistre ses mots dans un fichier JSON."""

    # On lit le texte du livre
    texte = source.read_text(encoding="utf-8-sig")

    # On nettoie le texte et on recupere les mots
    mots = decouper_mots(texte)

    # On cree le fichier JSON sans ecraser un fichier existant
    with sortie.open("x", encoding="utf-8") as fichier:
        json.dump(mots, fichier, ensure_ascii=False)
        fichier.write("\n")


def main() -> None:
    """Recupere les chemins des fichiers depuis le terminal."""

    parser = argparse.ArgumentParser(
        description="Prepare les mots d'un livre sans modifier son texte original."
    )

    parser.add_argument("source", type=Path, help="Fichier texte a lire")
    parser.add_argument("sortie", type=Path, help="Fichier JSON a creer")

    arguments = parser.parse_args()

    # On lance le nettoyage du fichier
    nettoyer_fichier(arguments.source, arguments.sortie)

    print(f"Mots enregistres dans {arguments.sortie}")


if __name__ == "__main__":
    main()
