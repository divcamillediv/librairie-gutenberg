from .jaccard import jaccard_similarity

def construire_matrice_similarite(livres: dict[int, set[str]]) -> dict:
    ids = list(livres.keys())
    matrice = {}

    for i, id1 in enumerate(ids):
        matrice[id1] = {}

        for j, id2 in enumerate(ids):
            if i == j:
                # Un livre est toujours identique à lui-même
                matrice[id1][id2] = 1.0

            elif j < i:
                # On récupère le résultat déjà calculé
                matrice[id1][id2] = matrice[id2][id1]

            else:
                # On compare les mots des deux livres
                matrice[id1][id2] = jaccard_similarity(
                    livres[id1], livres[id2]
                )

    return matrice