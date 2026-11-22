import pytest

from backend.app.recommendations.recommendation_service import recommend


def test_recommandations_un_livre():
    graphe = {
        1: {2: 0.8, 3: 0.5},
        2: {1: 0.8},
        3: {1: 0.5},
    }

    resultat = recommend([1], graphe)

    assert resultat == [2, 3]


def test_recommandations_plusieurs_livres():
    graphe = {
        1: {3: 0.8, 4: 0.5},
        2: {3: 0.6, 5: 0.7},
        3: {1: 0.8, 2: 0.6},
        4: {1: 0.5},
        5: {2: 0.7},
    }

    resultat = recommend([1, 2], graphe)

    # Le livre 3 conserve sa meilleure similarité : 0.8
    assert resultat == [3, 5, 4]


def test_exclusion_livres():
    graphe = {
        1: {2: 0.9, 3: 0.7, 4: 0.5},
    }

    resultat = recommend(
        [1], graphe, exclude_ids={2, 4}
    )

    assert resultat == [3]


def test_limite_recommandations():
    graphe = {
        1: {2: 0.9, 3: 0.8, 4: 0.7},
    }

    resultat = recommend([1], graphe, limit=2)

    assert resultat == [2, 3]


def test_livre_sans_voisins():
    graphe = {
        1: {},
        2: {3: 0.5},
    }

    assert recommend([1], graphe) == []


def test_livre_inconnu():
    assert recommend([99], {1: {2: 0.8}}) == []


def test_egalite_similarite():
    graphe = {
        1: {3: 0.8, 2: 0.8},
    }

    # À similarité égale, on classe par identifiant
    assert recommend([1], graphe) == [2, 3]


def test_limite_invalide():
    with pytest.raises(ValueError):
        recommend([1], {1: {2: 0.8}}, limit=-1)


def test_aucun_livre():
    assert recommend([], {}) == []
