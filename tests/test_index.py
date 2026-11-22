"""Tests de l'index inverse."""
import pytest
from backend.app.search.inverted_index import chercher_plusieurs_mots
from backend.app.search.inverted_index import chercher_mot, creer_index
from backend.app.search.inverted_index import chercher_regex
import json
from pathlib import Path
def test_creer_index():
    # On verifie le nombre d'occurrences dans chaque livre
    livres = {
        "1": ["mer", "bateau", "mer"],
        "2": ["mer", "ile"],
    }

    assert creer_index(livres) == {
        "mer": {"1": 2, "2": 1},
        "bateau": {"1": 1},
        "ile": {"2": 1},
    }


def test_livres_vides():
    # Un corpus vide doit donner un index vide
    assert creer_index({}) == {}
    assert creer_index({"1": [], "2": []}) == {}


def test_livre_vide_et_livre_rempli():
    # Un livre vide ne doit pas apparaitre dans l'index
    assert creer_index({"1": [], "2": ["mer"]}) == {"mer": {"2": 1}}


def test_identifiant_vide():
    # On refuse un livre sans identifiant
    with pytest.raises(ValueError, match="identifiant"):
        creer_index({"": []})


def test_mot_vide_dans_livre():
    # On refuse les mots vides
    with pytest.raises(ValueError, match="mot vide"):
        creer_index({"1": ["mer", ""]})


def test_livres_non_modifies():
    # La creation de l'index ne doit pas modifier les livres
    livres = {"1": ["mer", "bateau", "mer"]}

    creer_index(livres)

    assert livres == {"1": ["mer", "bateau", "mer"]}


def test_chercher_mot():
    # On cherche un mot present dans plusieurs livres
    index = creer_index({"1": ["mer", "mer"], "2": ["mer", "ile"]})

    assert chercher_mot(index, "mer") == {"1": 2, "2": 1}


def test_mot_absent():
    # Un mot absent doit retourner un dictionnaire vide
    index = creer_index({"1": ["mer"]})

    assert chercher_mot(index, "montagne") == {}
    assert index == {"mer": {"1": 1}}
    assert chercher_mot({}, "mer") == {}


def test_recherche_vide():
    # On refuse une recherche vide
    with pytest.raises(ValueError, match="mot recherche"):
        chercher_mot({}, "")


def test_resultat_independant():
    # Modifier le resultat ne doit pas changer l'index
    index = creer_index({"1": ["mer", "mer"]})

    resultat = chercher_mot(index, "mer")
    resultat["1"] = 99
    resultat["2"] = 1

    assert index == {"mer": {"1": 2}}


def test_pas_de_nettoyage_implicite():
    # Les majuscules et minuscules restent differentes
    index = creer_index({"1": ["Mer", "mer"]})

    assert index == {"Mer": {"1": 1}, "mer": {"1": 1}}
    assert chercher_mot(index, "MER") == {}

from backend.app.search.inverted_index import retirer_mots_presents_dans_trop_de_livres


def test_retirer_mots_trop_frequents():
    """Vérifie que les mots trop fréquents sont retirés."""
    index = {
        "mer": {"1": 2, "2": 1},
        "bateau": {"1": 1},
        "histoire": {"1": 1, "2": 1, "3": 1}
    }

    resultat = retirer_mots_presents_dans_trop_de_livres(index, 3, 0.8)

    assert "histoire" not in resultat
    assert "mer" in resultat
    assert "bateau" in resultat


def test_garder_frequence_des_mots():
    """Vérifie que les occurrences des mots gardés ne changent pas."""
    index = {
        "mer": {"1": 3},
        "bateau": {"2": 2}
    }

    resultat = retirer_mots_presents_dans_trop_de_livres(index, 3, 0.8)

    assert resultat["mer"] == {"1": 3}
    assert resultat["bateau"] == {"2": 2}


def test_seuil_atteint():
    """Vérifie qu'un mot est retiré lorsqu'il atteint le seuil."""
    index = {
        "mer": {"1": 1, "2": 1, "3": 1, "4": 1}
    }

    resultat = retirer_mots_presents_dans_trop_de_livres(index, 5, 0.8)

    assert resultat == {}


def test_index_original_non_modifie():
    """Vérifie que l'index original reste inchangé."""
    index = {
        "histoire": {"1": 1, "2": 1},
        "mer": {"1": 2}
    }

    resultat = retirer_mots_presents_dans_trop_de_livres(index, 2, 0.8)

    assert "histoire" in index
    assert "histoire" not in resultat

def test_chercher_plusieurs_mots():
    index = {
        "alice": {"11": 3, "84": 1},
        "wonderland": {"11": 2, "74": 1}
    }

    resultat = chercher_plusieurs_mots(index, ["alice", "wonderland"])

    assert resultat == {"11": 5}


def test_chercher_plusieurs_mots_sans_resultat():
    index = {
        "alice": {"11": 3},
        "bateau": {"84": 2}
    }

    resultat = chercher_plusieurs_mots(index, ["alice", "bateau"])

    assert resultat == {}

def test_chercher_regex():
    index = {
        "aventure": {"11": 2},
        "aventures": {"11": 1, "84": 3},
        "bateau": {"74": 2}
    }

    resultat = chercher_regex(index, r"^aventur")

    assert resultat == {"11": 3, "84": 3}


def test_chercher_regex_sans_resultat():
    index = {
        "alice": {"11": 2},
        "bateau": {"84": 1}
    }

    resultat = chercher_regex(index, r"^dragon")

    assert resultat == {}



def test_regex_sur_index_json(tmp_path):
    # On crée un petit index pour le test
    index = {
        "adventure": {"11": 2},
        "adventures": {"11": 1, "74": 3},
        "alice": {"84": 1}
    }

    # On enregistre l'index dans un fichier temporaire
    chemin = tmp_path / "index_inverse_test.json"
    chemin.write_text(
        json.dumps(index),
        encoding="utf-8"
    )

    # On recharge l'index depuis le fichier JSON
    index_charge = json.loads(
        chemin.read_text(encoding="utf-8")
    )

    # On recherche les mots commençant par adventur
    resultat = chercher_regex(index_charge, r"^adventur")

    assert resultat == {"11": 3, "74": 3}
