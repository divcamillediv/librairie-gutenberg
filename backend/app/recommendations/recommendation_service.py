
from app.recommendations import graph_builder as module_graphe


def recommend(
    book_ids: list[int],
    neighbors: dict[int, dict[int, float]] | None = None,
    *,
    exclude_ids=None,
    exclude=None,
    limit: int = 3
) -> list:

    if limit < 0:
        raise ValueError("La limite ne peut pas etre negative")

    if limit == 0 or not book_ids:
        return []

    # Si le graphe n'est pas fourni, on utilise celui charge au demarrage
    mode_integration = neighbors is None

    if mode_integration:
        neighbors = module_graphe.graphe_charge

    # On exclut les livres de depart et ceux deja affiches
    exclus = set(book_ids)

    if exclude_ids is not None:
        exclus.update(exclude_ids)

    if exclude is not None:
        exclus.update(exclude)

    scores = {}

    for livre in book_ids:
        # On recupere les voisins de chaque livre
        for voisin, similarite in neighbors.get(livre, {}).items():

            if voisin in exclus:
                continue

            # On garde la meilleure similarite pour chaque voisin
            if voisin not in scores or similarite > scores[voisin]:
                scores[voisin] = similarite

    # Les livres les plus similaires arrivent en premier
    recommandations = sorted(
        scores,
        key=lambda livre: (-scores[livre], livre)
    )[:limit]

    # Ancien fonctionnement : on renvoie uniquement les identifiants
    if not mode_integration:
        return recommandations

    # Pour Camille : on renvoie les identifiants et les similarites
    return [
        {
            "id": livre,
            "similarity": scores[livre]
        }
        for livre in recommandations
    ]