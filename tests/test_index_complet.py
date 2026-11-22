
import os
import pytest
from pathlib import Path

from scripts.build_index import charger_index
from backend.app.search.recherche import rechercher_livres
from backend.app.search.inverted_index import chercher_regex


# Chemins résolus depuis la racine du dépôt, quel que soit le dossier courant.
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_LIVRES = RACINE / "data" / "raw"
CHEMIN_INDEX = RACINE / "data" / "indexes" / "index_complet.json"

# Le corpus complet et son index ne sont pas versionnés sur GitHub.
# Les tests restent obligatoires lors de leur exécution locale.
pytestmark = pytest.mark.skipif(
    os.getenv("GITHUB_ACTIONS") == "true"
    and (
            not CHEMIN_INDEX.exists()
            or not any(DOSSIER_LIVRES.glob("*.txt"))
    ),
    reason="Corpus complet non disponible sur GitHub Actions"
)


@pytest.fixture(scope="module")
def index_complet():
    return charger_index(CHEMIN_INDEX)


def test_nombre_livres():
    livres = list(DOSSIER_LIVRES.glob("*.txt"))
    assert len(livres) >= 1664


def test_longueur_livres():
    livres = list(DOSSIER_LIVRES.glob("*.txt"))

    assert len(livres) >= 1664

    for livre in livres:
        texte = livre.read_text(encoding="utf-8")
        assert len(texte.split()) >= 10000, (
            f"Le livre {livre.name} contient moins de 10000 mots"
        )


def test_index_complet(index_complet):
    assert len(index_complet) > 0
    assert "alice" in index_complet


def test_recherche_un_mot(index_complet):
    resultats = rechercher_livres(index_complet, "alice")

    assert len(resultats) > 0
    assert "11" in resultats
    assert resultats["11"] == 397


def test_recherche_plusieurs_mots(index_complet):
    resultats = rechercher_livres(index_complet, "alice rabbit")

    assert len(resultats) > 0
    assert "11" in resultats
    assert resultats["11"] == 450

    # Recherche ET : les deux mots doivent être présents.
    for identifiant in resultats:
        assert identifiant in index_complet["alice"]
        assert identifiant in index_complet["rabbit"]


# Tests complémentaires sur l'index des 1 700 livres

def test_recherche_mot_inexistant(index_complet):
    resultats = rechercher_livres(
        index_complet, "motinventeintrouvablexyz123"
    )
    assert resultats == {}


def test_recherche_and(index_complet):
    resultats = rechercher_livres(index_complet, "alice rabbit")

    assert len(resultats) == 85
    assert resultats["11"] == 450

    for livre_id in resultats:
        assert livre_id in index_complet["alice"]
        assert livre_id in index_complet["rabbit"]


def test_regex_mot_exact(index_complet):
    resultats = chercher_regex(index_complet, "^alice$")

    assert resultats == index_complet["alice"]


def test_regex_prefixe(index_complet):
    resultats = chercher_regex(index_complet, "^alic.*")

    assert len(resultats) == 268
    assert "11" in resultats


def test_regex_operateur_ou(index_complet):
    resultats = chercher_regex(
        index_complet, "^(alice|rabbit)$"
    )

    livres_attendus = (
            set(index_complet["alice"])
            | set(index_complet["rabbit"])
    )

    assert set(resultats) == livres_attendus


def test_regex_repetition(index_complet):
    resultats = chercher_regex(index_complet, "^rabb.*")

    assert set(index_complet["rabbit"]).issubset(
        set(resultats)
    )


def test_regex_aucun_resultat(index_complet):
    resultats = chercher_regex(
        index_complet, "^motinventeintrouvablexyz123$"
    )

    assert resultats == {}
