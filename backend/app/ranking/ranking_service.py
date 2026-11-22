from app.ranking import pagerank as module_pagerank

def rank_results(
    occurrences: dict[int, int],
    pagerank: dict[int, float] | None = None,
    *,
    strategy: str = "combined",
    alpha: float = 0.5
) -> list:

    if strategy not in ("textual", "pagerank", "combined"):
        raise ValueError("Strategie de classement inconnue")

    if not 0 <= alpha <= 1:
        raise ValueError("alpha doit etre compris entre 0 et 1")

    if not occurrences:
        return []

    # Si Camille ne fournit pas les scores, on utilise ceux charges au demarrage
    mode_integration = pagerank is None

    if mode_integration:
        pagerank = module_pagerank.pagerank_charge

    livres = list(occurrences.keys())

    # On normalise les occurrences entre 0 et 1
    max_occurrences = max(occurrences.values())

    scores_textuels = {}
    for livre in livres:
        if max_occurrences > 0:
            scores_textuels[livre] = occurrences[livre] / max_occurrences
        else:
            scores_textuels[livre] = 0.0

    # On normalise aussi les scores PageRank
    max_pagerank = max(pagerank.get(livre, 0.0) for livre in livres)

    scores_pagerank = {}
    for livre in livres:
        if max_pagerank > 0:
            scores_pagerank[livre] = pagerank.get(livre, 0.0) / max_pagerank
        else:
            scores_pagerank[livre] = 0.0

    # On calcule le score final de chaque livre
    scores = {}

    for livre in livres:
        if strategy == "textual":
            scores[livre] = scores_textuels[livre]

        elif strategy == "pagerank":
            scores[livre] = scores_pagerank[livre]

        else:
            scores[livre] = (
                alpha * scores_textuels[livre]
                + (1 - alpha) * scores_pagerank[livre]
            )

    classement = sorted(livres, key=lambda livre: (-scores[livre], livre))

    # Ancien fonctionnement : on renvoie seulement les identifiants
    if not mode_integration:
        return classement

    # Pour Camille : on renvoie les informations necessaires a l'interface
    return [
        {
            "id": livre,
            "occurrences": occurrences[livre],
            "pagerank": round(pagerank.get(livre, 0.0), 6),
            "score": round(scores[livre], 4)
        }
        for livre in classement
    ]