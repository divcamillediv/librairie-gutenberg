import pytest

from backend.app.recommendations.graph_builder import construire_graphe


def test_graphe_avec_seuil():
    livres = {
        1: {"mer", "bateau"},
        2: {"mer", "pirate"},
        3: {"montagne", "foret"},
    }

    graphe = construire_graphe(livres, seuil=0.3)

    # Les livres 1 et 2 ont une similarité de 1/3
    assert graphe[1][2] == 1 / 3
    assert graphe[2][1] == 1 / 3

    # Le livre 3 n'a aucun voisin
    assert graphe[3] == {}

    # Aucun livre n'est relié à lui-même
    assert 1 not in graphe[1]


def test_graphe_avec_seuil_eleve():
    livres = {
        1: {"mer", "bateau"},
        2: {"mer", "pirate"},
    }

    graphe = construire_graphe(livres, seuil=0.5)

    assert graphe == {1: {}, 2: {}}


def test_seuil_invalide():
    with pytest.raises(ValueError):
        construire_graphe({}, seuil=1.5)
