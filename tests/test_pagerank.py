
import pytest

from backend.app.ranking.pagerank import calculer_pagerank
from backend.app.recommendations.graph_builder import construire_graphe


def test_graphe_vide():
    assert calculer_pagerank({}) == {}


def test_graphe_symetrique():
    graphe = {
        1: {2: 0.5},
        2: {1: 0.5},
    }

    scores = calculer_pagerank(graphe)

    # Les deux livres ont la même importance
    assert scores[1] == pytest.approx(0.5)
    assert scores[2] == pytest.approx(0.5)


def test_livre_central():
    graphe = {
        1: {2: 0.8, 3: 0.5},
        2: {1: 0.8},
        3: {1: 0.5},
    }

    scores = calculer_pagerank(graphe)

    # Le livre 1 est relié aux deux autres
    assert scores[1] > scores[2]
    assert scores[1] > scores[3]
    assert sum(scores.values()) == pytest.approx(1.0)


def test_livre_isole():
    graphe = {
        1: {2: 0.5},
        2: {1: 0.5},
        3: {},
    }

    scores = calculer_pagerank(graphe)

    assert len(scores) == 3
    assert sum(scores.values()) == pytest.approx(1.0)
    assert scores[3] > 0


def test_pagerank_avec_graphe_jaccard():
    livres = {
        1: {"mer", "bateau", "pirate"},
        2: {"mer", "bateau"},
        3: {"mer", "pirate"},
        4: {"montagne", "foret"},
    }

    graphe = construire_graphe(livres, seuil=0.3)
    scores = calculer_pagerank(graphe)

    # Le livre 1 est relié aux livres 2 et 3
    assert scores[1] > scores[4]

    # Tous les livres ont un score
    assert len(scores) == 4

    # La somme des scores vaut 1
    assert sum(scores.values()) == pytest.approx(1.0)
