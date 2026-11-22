import json
from pathlib import Path


# Scores chargés une seule fois au démarrage de l'application
pagerank_charge = {}


def calculer_pagerank(graphe: dict, alpha: float = 0.85,
                     iterations: int = 100, tolerance: float = 1e-6) -> dict:
    if not graphe:
        return {}

    if not 0 <= alpha < 1:
        raise ValueError("alpha doit être compris entre 0 et 1 exclu")

    if iterations <= 0 or tolerance <= 0:
        raise ValueError("Paramètres d'itération invalides")

    n = len(graphe)

    # Au départ, tous les livres ont le même score
    scores = {livre: 1 / n for livre in graphe}

    for _ in range(iterations):
        nouveaux_scores = {livre: (1 - alpha) / n for livre in graphe}

        for livre, voisins in graphe.items():
            poids_total = sum(voisins.values())

            if poids_total == 0:
                # Un livre isolé répartit son score entre tous les livres
                part = alpha * scores[livre] / n
                for autre in graphe:
                    nouveaux_scores[autre] += part
            else:
                # Chaque voisin reçoit une part selon le poids du lien
                for voisin, poids in voisins.items():
                    nouveaux_scores[voisin] += (
                        alpha * scores[livre] * poids / poids_total
                    )

        # On arrête si les scores ne changent presque plus
        difference = sum(
            abs(nouveaux_scores[livre] - scores[livre])
            for livre in graphe
        )

        scores = nouveaux_scores

        if difference < tolerance:
            break

    return scores


def load_pagerank(directory: Path) -> dict:
    global pagerank_charge

    chemin = Path(directory) / "pagerank.json"

    # On récupère les scores enregistrés par compute_pagerank.py
    with chemin.open("r", encoding="utf-8") as fichier:
        donnees = json.load(fichier)

    pagerank_charge = {
        int(livre): float(score)
        for livre, score in donnees.items()
    }

    return pagerank_charge
