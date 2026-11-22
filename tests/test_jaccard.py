
from backend.app.recommendations.jaccard import (
    jaccard_similarity,
    jaccard_distance,
)


def test_livres_partiellement_similaires():
    livre1 = {"mer", "bateau", "voyage"}
    livre2 = {"mer", "bateau", "pirate"}

    # Deux mots communs sur quatre mots distincts
    assert jaccard_similarity(livre1, livre2) == 0.5


def test_livres_identiques_et_differents():
    livre1 = {"mer", "bateau"}
    livre2 = {"montagne", "foret"}

    assert jaccard_similarity(livre1, livre1) == 1.0
    assert jaccard_similarity(livre1, livre2) == 0.0


def test_ensembles_vides():
    # Vérifie qu'on ne divise pas par zéro
    assert jaccard_similarity(set(), set()) == 1.0
    assert jaccard_similarity({"mer"}, set()) == 0.0


def test_distance_jaccard():
    livre1 = {"mer", "bateau", "voyage"}
    livre2 = {"mer", "bateau", "pirate"}

    assert jaccard_distance(livre1, livre2) == 0.5
    assert jaccard_distance(livre1, livre1) == 0.0
    assert jaccard_distance(livre1, {"montagne"}) == 1.0
