
def jaccard_similarity(a: set[str], b: set[str]) -> float:
    # Deux ensembles vides sont considérés comme identiques
    if not a and not b:
        return 1.0

    # Mots en commun et mots distincts des deux livres
    intersection = a & b
    union = a | b

    return len(intersection) / len(union)


def jaccard_distance(a: set[str], b: set[str]) -> float:
    # Plus la distance est faible, plus les livres se ressemblent
    return 1.0 - jaccard_similarity(a, b)
