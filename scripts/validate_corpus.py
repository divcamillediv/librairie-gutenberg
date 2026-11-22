from pathlib import Path

from backend.app.search.nettoyage import decouper_mots


def verifier_longueur_livre(
        chemin: Path,
        minimum_mots: int = 10000
) -> bool:
    """Vérifie qu'un livre contient assez de mots."""

    # On lit le texte du livre
    texte = chemin.read_text(encoding="utf-8-sig")

    # On compte les mots après nettoyage
    mots = decouper_mots(texte)

    return len(mots) >= minimum_mots


def valider_corpus(
        dossier: Path,
        minimum_livres: int = 1664,
        minimum_mots: int = 10000
) -> dict:
    """Vérifie le nombre de livres valides dans le corpus."""

    # On récupère les fichiers texte du dossier
    fichiers = sorted(dossier.glob("*.txt"))

    livres_valides = 0
    livres_trop_courts = []

    # On vérifie la longueur de chaque livre
    for fichier in fichiers:
        if verifier_longueur_livre(fichier, minimum_mots):
            livres_valides += 1
        else:
            livres_trop_courts.append(fichier.stem)

    # On prépare le bilan du corpus
    return {
        "total_livres": len(fichiers),
        "livres_valides": livres_valides,
        "livres_trop_courts": livres_trop_courts,
        "corpus_valide": livres_valides >= minimum_livres
    }

