from backend.app.recommendations.similarity_matrix import (
    construire_matrice_similarite,
)


def test_matrice_similarite():
    livres = {
        1: {"mer", "bateau"},
        2: {"mer", "pirate"},
        3: {"montagne", "foret"},
    }

    matrice = construire_matrice_similarite(livres)

    # Un livre est identique à lui-même
    assert matrice[1][1] == 1.0
    assert matrice[2][2] == 1.0

    # La matrice est symétrique
    assert matrice[1][2] == matrice[2][1]

    # Deux livres sans mots communs
    assert matrice[1][3] == 0.0

    # Un mot commun sur trois mots distincts
    assert matrice[1][2] == 1 / 3


def test_matrice_vide():
    assert construire_matrice_similarite({}) == {}