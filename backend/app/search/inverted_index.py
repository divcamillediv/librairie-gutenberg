"""Index inverse construit a partir des mots nettoyes des livres."""
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Nom du fichier produit par `python -m scripts.indexer_corpus data/raw data/indexes/index_complet.json`.
NOM_FICHIER_INDEX = "index_complet.json"

# Index chargé une seule fois au démarrage de l'API (voir load_index).
index_charge: dict[str, dict[str, int]] = {}

def creer_index(livres: dict[str, list[str]]) -> dict[str, dict[str, int]]:
    """Construit un index avec les mots et leurs occurrences dans chaque livre."""

    index: dict[str, dict[str, int]] = {}

    # On parcourt tous les livres
    for livre_id, mots in livres.items():

        # On verifie que le livre a un identifiant
        if not livre_id:
            raise ValueError("L'identifiant du livre ne doit pas etre vide.")

        # On parcourt les mots du livre
        for mot in mots:

            # On refuse les mots vides
            if not mot or not mot.strip():
                raise ValueError(f"Le livre {livre_id} contient un mot vide.")

            # Si le mot n'existe pas encore, on l'ajoute a l'index
            if mot not in index:
                index[mot] = {}

            # On initialise le compteur pour ce livre
            if livre_id not in index[mot]:
                index[mot][livre_id] = 0

            # On compte chaque apparition du mot
            index[mot][livre_id] += 1

    return index


def chercher_mot(index: dict[str, dict[str, int]], mot: str) -> dict[str, int]:
    """Cherche un mot et renvoie les livres qui le contiennent."""

    # On verifie que le mot recherche n'est pas vide
    if not mot or not mot.strip():
        raise ValueError("Le mot recherche ne doit pas etre vide.")

    # On retourne les livres trouves et leurs frequences
    return index.get(mot, {}).copy()


def retirer_mots_presents_dans_trop_de_livres(
        index: dict[str, dict[str, int]],
        nombre_total_livres: int,
        seuil: float = 0.8
) -> dict[str, dict[str, int]]:
    """Allège l'index inversé en retirant les mots présents dans presque
    tous les livres, car ils sont souvent moins utiles pour la recherche.
    """

    # On vérifie que le nombre de livres et le seuil sont valides
    if nombre_total_livres <= 0:
        raise ValueError("Le nombre de livres doit être positif.")

    if not 0 < seuil <= 1:
        raise ValueError("Le seuil doit être entre 0 et 1.")

    # On crée un nouvel index pour garder l'original
    index_filtre = {}

    # On parcourt chaque mot et les livres où il apparaît
    for mot, livres_contenant_mot in index.items():

        # On calcule dans quelle proportion des livres le mot apparaît
        proportion = len(livres_contenant_mot) / nombre_total_livres

        # On garde seulement les mots présents dans moins de livres que le seuil
        if proportion < seuil:
            index_filtre[mot] = livres_contenant_mot.copy()

    return index_filtre

def chercher_plusieurs_mots(
        index: dict[str, dict[str, int]],
        mots: list[str]
) -> dict[str, int]:
    """Cherche les livres qui contiennent tous les mots demandés."""

    # Une recherche vide ne donne aucun résultat
    if not mots:
        return {}

    # On commence avec les livres du premier mot
    resultats = chercher_mot(index, mots[0])

    # On cherche les autres mots
    for mot in mots[1:]:
        livres = chercher_mot(index, mot)

        # On garde seulement les livres qui contiennent les deux
        for livre_id in list(resultats):
            if livre_id in livres:
                resultats[livre_id] += livres[livre_id]
            else:
                del resultats[livre_id]

    return resultats


def chercher_regex(
        index: dict[str, dict[str, int]],
        motif: str
) -> dict[str, int]:
    """Cherche les livres contenant des mots correspondant au motif."""

    if not motif or not motif.strip():
        raise ValueError("Le motif ne doit pas etre vide.")

    resultats = {}

    # On parcourt les mots de l'index
    for mot, livres in index.items():

        # On vérifie si le mot correspond au motif
        if re.search(motif, mot):

            # On additionne les occurrences pour chaque livre
            for livre_id, frequence in livres.items():
                resultats[livre_id] = resultats.get(livre_id, 0) + frequence

    return resultats



def load_index(dossier: Path) -> dict[str, dict[str, int]]:
    """Charge l'index inversé enregistré par scripts/indexer_corpus.py.

    Appelée une seule fois au démarrage de l'API. Lève FileNotFoundError si
    l'index n'a pas été construit : l'API passe alors en simulation.
    """
    global index_charge

    chemin = Path(dossier) / NOM_FICHIER_INDEX
    with chemin.open("r", encoding="utf-8") as fichier:
        index = json.load(fichier)

    if not isinstance(index, dict) or not index:
        raise ValueError(f"Index vide ou mal formé : {chemin}")

    index_charge = index
    logger.info("Index chargé : %d termes", len(index_charge))
    return index_charge
