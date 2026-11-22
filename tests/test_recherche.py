from scripts.build_index import (
    construire_index_des_livres,
    enregistrer_index,
    charger_index,
)
from backend.app.search.recherche import rechercher_livres
def test_rechercher_livres():
    index = {
        "alice": {"11": 3, "84": 1},
        "wonderland": {"11": 2, "74": 1}
    }

    resultat = rechercher_livres(index, "The Alice Wonderland!")

    assert resultat == {"11": 5}


def test_rechercher_livres_requete_vide():
    index = {
        "alice": {"11": 3}
    }

    resultat = rechercher_livres(index, "the and of")

    assert resultat == {}


def test_recherche_complete(tmp_path):
    # On crée trois petits livres
    (tmp_path / "11.txt").write_text(
        "The Alice Wonderland Alice",
        encoding="utf-8"
    )

    (tmp_path / "84.txt").write_text(
        "Alice and the rabbit",
        encoding="utf-8"
    )

    (tmp_path / "74.txt").write_text(
        "A journey through the ocean",
        encoding="utf-8"
    )

    # On construit l'index à partir des fichiers
    index = construire_index_des_livres(tmp_path)

    # On lance une recherche avec une phrase
    resultat = rechercher_livres(index, "The Alice Wonderland!")

    assert resultat == {"11": 3}

def test_recherche_sur_index_recharge(tmp_path):
    # On crée trois petits livres
    dossier = tmp_path / "livres"
    dossier.mkdir()

    (dossier / "11.txt").write_text(
        "Alice rabbit rabbit wonderland", encoding="utf-8"
    )
    (dossier / "84.txt").write_text(
        "Monster castle mystery", encoding="utf-8"
    )
    (dossier / "120.txt").write_text(
        "Alice adventure sea", encoding="utf-8"
    )

    # On construit et enregistre l'index
    index = construire_index_des_livres(dossier)
    chemin = tmp_path / "index.json"
    enregistrer_index(index, chemin)

    # On recharge l'index depuis le fichier JSON
    index_recharge = charger_index(chemin)

    # On recherche dans l'index rechargé
    resultats = rechercher_livres(index_recharge, "Alice rabbit")

    assert resultats == {"11": 3}
