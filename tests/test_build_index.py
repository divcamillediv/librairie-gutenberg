import json

from scripts.build_index import (
    construire_index_des_livres,
    enregistrer_index,
    charger_index,
)


def test_construire_index(tmp_path):
    (tmp_path / "1.txt").write_text("La mer, la mer !", encoding="utf-8")
    (tmp_path / "2.txt").write_text("Le bateau sur la mer.", encoding="utf-8")
    (tmp_path / "3.txt").write_text("Un poisson.", encoding="utf-8")

    index = construire_index_des_livres(
        tmp_path, {"la", "le"}, seuil=0.8
    )

    assert index["mer"] == {"1": 2, "2": 1}
    assert "la" not in index
    assert "le" not in index

def test_filtrer_mots_trop_frequents(tmp_path):
    (tmp_path / "1.txt").write_text("mer bateau", encoding="utf-8")
    (tmp_path / "2.txt").write_text("mer poisson", encoding="utf-8")

    index = construire_index_des_livres(tmp_path, set(), seuil=0.8)

    assert "mer" not in index
    assert "bateau" in index
    assert "poisson" in index


def test_enregistrer_index(tmp_path):
    index = {"mer": {"1": 2}}
    chemin = tmp_path / "index.json"

    enregistrer_index(index, chemin)

    resultat = json.loads(chemin.read_text(encoding="utf-8"))
    assert resultat == index


def test_index_avec_stopwords_anglais_par_defaut(tmp_path):
    # On crée deux petits livres
    (tmp_path / "11.txt").write_text(
        "the alice and alice rabbit",
        encoding="utf-8"
    )

    (tmp_path / "84.txt").write_text(
        "the mystery and castle",
        encoding="utf-8"
    )

    # On construit l'index sans fournir de stopwords
    index = construire_index_des_livres(tmp_path)

    # Les mots courants sont supprimés
    assert "the" not in index
    assert "and" not in index

    # Les mots utiles sont conservés
    assert index["alice"] == {"11": 2}
    assert index["rabbit"] == {"11": 1}
    assert index["mystery"] == {"84": 1}
    assert index["castle"] == {"84": 1}

def test_charger_index(tmp_path):
    # On prépare un index simple
    index = {
        "alice": {"11": 2},
        "rabbit": {"11": 1, "84": 3},
    }

    chemin = tmp_path / "index.json"

    # On enregistre puis on recharge l'index
    enregistrer_index(index, chemin)
    index_charge = charger_index(chemin)

    # On vérifie que les données sont identiques
    assert index_charge == index

