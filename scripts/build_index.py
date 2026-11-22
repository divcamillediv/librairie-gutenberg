"""Prépare les textes de plusieurs livres pour l'indexation."""
from backend.app.search.stopwords import STOPWORDS_ANGLAIS
from pathlib import Path
import json
from backend.app.search.nettoyage import decouper_mots
from backend.app.search.nettoyage import supprimer_stopwords
from backend.app.search.inverted_index import creer_index
from backend.app.search.inverted_index import retirer_mots_presents_dans_trop_de_livres

def lire_et_nettoyer_livres(dossier: Path) -> dict[str, list[str]]:
    """Lit les fichiers texte d'un dossier et prépare leurs mots."""

    livres = {}

    # On parcourt les fichiers texte du dossier
    for fichier in sorted(dossier.glob("*.txt")):

        # On récupère l'identifiant du livre
        identifiant = fichier.stem

        # On lit et on nettoie le texte du livre
        texte = fichier.read_text(encoding="utf-8-sig")
        mots = decouper_mots(texte)

        # On garde les mots avec l'identifiant du livre
        livres[identifiant] = mots

    return livres


def construire_index_des_livres(
        dossier: Path,
        stopwords: set[str] | None = None,
        seuil: float = 0.8
) -> dict[str, dict[str, int]]:
    """Construit un index inversé sans stopwords ni mots trop fréquents."""
    if stopwords is None:
        stopwords = STOPWORDS_ANGLAIS
    # On lit et on nettoie les livres
    livres = lire_et_nettoyer_livres(dossier)

    # On retire les stopwords de chaque livre
    for identifiant, mots in livres.items():
        livres[identifiant] = supprimer_stopwords(mots, stopwords)

    # On construit l'index inversé
    index = creer_index(livres)

    # On retire les mots présents dans trop de livres
    if livres:
        index = retirer_mots_presents_dans_trop_de_livres(
            index,
            nombre_total_livres=len(livres),
            seuil=seuil
        )
        # On utilise les stopwords anglais si aucune liste n'est fournie

    return index

def enregistrer_index(index: dict[str, dict[str, int]], chemin: Path) -> None:
    """Enregistre l'index inversé dans un fichier JSON pour le réutiliser."""

    # On crée le dossier de destination s'il n'existe pas
    chemin.parent.mkdir(parents=True, exist_ok=True)

    # On enregistre l'index au format JSON
    with chemin.open("w", encoding="utf-8") as fichier:
        json.dump(index, fichier, ensure_ascii=False, indent=2)

def charger_index(chemin: Path) -> dict[str, dict[str, int]]:
    """Charge un index inversé depuis un fichier JSON."""

    with chemin.open("r", encoding="utf-8") as fichier:
        index = json.load(fichier)

    return index
