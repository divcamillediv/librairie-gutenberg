
import pytest

from backend.app.ranking.ranking_service import rank_results


def test_classement_textuel():
    occurrences = {1: 5, 2: 20, 3: 10}
    pagerank = {1: 0.5, 2: 0.1, 3: 0.2}

    resultat = rank_results(occurrences, pagerank, strategy="textual")

    assert resultat == [2, 3, 1]


def test_classement_pagerank():
    occurrences = {1: 20, 2: 5, 3: 10}
    pagerank = {1: 0.1, 2: 0.4, 3: 0.2}

    resultat = rank_results(occurrences, pagerank, strategy="pagerank")

    assert resultat == [2, 3, 1]


def test_classement_combine():
    occurrences = {1: 20, 2: 5, 3: 10}
    pagerank = {1: 0.1, 2: 0.4, 3: 0.2}

    resultat = rank_results(
        occurrences, pagerank, strategy="combined", alpha=0.5
    )

    assert resultat == [1, 2, 3]


def test_recherche_vide():
    assert rank_results({}, {}) == []


def test_score_pagerank_manquant():
    occurrences = {1: 10, 2: 5}
    pagerank = {1: 0.3}

    resultat = rank_results(
        occurrences, pagerank, strategy="pagerank"
    )

    assert resultat == [1, 2]


def test_strategie_invalide():
    with pytest.raises(ValueError):
        rank_results({1: 5}, {}, strategy="inconnue")


def test_alpha_invalide():
    with pytest.raises(ValueError):
        rank_results({1: 5}, {}, alpha=1.5)