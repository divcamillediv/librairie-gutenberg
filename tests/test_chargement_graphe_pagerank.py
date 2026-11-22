import json

import pytest

from backend.app.recommendations.graph_builder import load_graph
from backend.app.ranking.pagerank import load_pagerank, calculer_pagerank


def test_chargement_graphe_json(tmp_path):
    # On crée un petit graphe comme celui généré par notre script
    graphe = {
        "1": {"2": 0.75},
        "2": {"1": 0.75},
        "3": {}
    }

    chemin = tmp_path / "graph.json"
    chemin.write_text(json.dumps(graphe), encoding="utf-8")

    # On vérifie que les identifiants sont convertis en entiers
    resultat = load_graph(tmp_path)

    assert resultat == {
        1: {2: 0.75},
        2: {1: 0.75},
        3: {}
    }


def test_chargement_pagerank_json(tmp_path):
    # On crée un fichier de scores PageRank
    scores = {
        "1": 0.45,
        "2": 0.45,
        "3": 0.10
    }

    chemin = tmp_path / "pagerank.json"
    chemin.write_text(json.dumps(scores), encoding="utf-8")

    resultat = load_pagerank(tmp_path)

    # Les identifiants sont des entiers et les scores sont conservés
    assert resultat == {
        1: 0.45,
        2: 0.45,
        3: 0.10
    }


def test_pagerank_avec_plusieurs_livres_isoles():
    # Les livres 3, 4 et 5 n'ont aucun voisin
    graphe = {
        1: {2: 0.8},
        2: {1: 0.8},
        3: {},
        4: {},
        5: {}
    }

    scores = calculer_pagerank(graphe)

    # Tous les livres doivent avoir un score positif
    assert len(scores) == 5
    assert all(score > 0 for score in scores.values())

    # La somme des scores doit rester proche de 1
    assert sum(scores.values()) == pytest.approx(1.0)

    # Les deux livres connectés doivent être mieux classés
    assert scores[1] > scores[3]
    assert scores[2] > scores[4]


def test_pagerank_graphe_entierement_isole():
    # Aucun livre n'a de voisin
    graphe = {
        1: {},
        2: {},
        3: {},
        4: {}
    }

    scores = calculer_pagerank(graphe)

    # Sans liens, tous les livres doivent avoir le même score
    assert len(scores) == 4

    for score in scores.values():
        assert score == pytest.approx(0.25)

    assert sum(scores.values()) == pytest.approx(1.0)
