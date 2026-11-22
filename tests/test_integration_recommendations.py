
import pytest

from backend.app.recommendations.graph_builder import construire_graphe
from backend.app.ranking.pagerank import calculer_pagerank
from backend.app.ranking.ranking_service import rank_results
from backend.app.recommendations.recommendation_service import recommend


def test_recherche_classement_et_recommandations():
    # On simule une petite bibliothèque de cinq livres
    livres = {
        1: {"mer", "bateau", "pirate"},
        2: {"mer", "bateau", "voyage"},
        3: {"mer", "pirate", "tresor"},
        4: {"montagne", "foret", "neige"},
        5: {"montagne", "foret", "randonnee"},
    }

    # On construit le graphe à partir des mots des livres
    graphe = construire_graphe(livres, seuil=0.3)

    assert len(graphe) == 5
    assert 2 in graphe[1]
    assert 3 in graphe[1]
    assert 5 in graphe[4]

    # On calcule l'importance de chaque livre
    scores = calculer_pagerank(graphe)

    assert len(scores) == 5
    assert sum(scores.values()) == pytest.approx(1.0)

    # On simule les résultats d'une recherche sur le mot "mer"
    occurrences = {
        1: 15,
        2: 8,
        3: 5,
    }

    # On classe les livres avec les occurrences et PageRank
    classement = rank_results(
        occurrences,
        scores,
        strategy="combined",
        alpha=0.5
    )

    assert len(classement) == 3
    assert set(classement) == {1, 2, 3}
    assert classement[0] == 1

    # On cherche des recommandations à partir du premier résultat
    recommandations = recommend(
        [classement[0]],
        graphe,
        exclude_ids=set(classement),
        limit=3
    )

    # Aucun des livres déjà trouvés ne doit être recommandé
    assert all(livre not in classement for livre in recommandations)


def test_recommandations_apres_recherche():
    livres = {
        1: {"mer", "bateau", "pirate"},
        2: {"mer", "bateau", "voyage"},
        3: {"mer", "pirate", "tresor"},
        4: {"montagne", "foret", "neige"},
    }

    graphe = construire_graphe(livres, seuil=0.3)
    scores = calculer_pagerank(graphe)

    # La recherche ne retourne que le livre 1
    classement = rank_results(
        {1: 10},
        scores,
        strategy="combined"
    )

    recommandations = recommend(
        classement,
        graphe,
        exclude_ids=set(classement),
        limit=2
    )

    # Les livres 2 et 3 sont similaires au livre 1
    assert recommandations == [2, 3]


def test_aucun_resultat_de_recherche():
    livres = {
        1: {"mer", "bateau"},
        2: {"montagne", "foret"},
    }

    graphe = construire_graphe(livres)
    scores = calculer_pagerank(graphe)

    # Aucun livre ne correspond à la recherche
    classement = rank_results({}, scores)

    recommandations = recommend(classement, graphe)

    assert classement == []
    assert recommandations == []
