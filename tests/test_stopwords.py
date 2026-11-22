from backend.app.search.stopwords import STOPWORDS_ANGLAIS
from backend.app.search.nettoyage import supprimer_stopwords


def test_supprimer_stopwords_anglais():
    mots = ["the", "alice", "and", "rabbit"]

    resultat = supprimer_stopwords(mots, STOPWORDS_ANGLAIS)

    assert resultat == ["alice", "rabbit"]


def test_garder_mots_utiles():
    mots = ["adventure", "mystery", "wonderland"]

    resultat = supprimer_stopwords(mots, STOPWORDS_ANGLAIS)

    assert resultat == mots
