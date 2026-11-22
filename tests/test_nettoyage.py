"""Tests du nettoyage des textes et des fichiers."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from backend.app.search.inverted_index import chercher_mot, creer_index
from backend.app.search.nettoyage import decouper_mots, nettoyer_texte
from scripts.clean_books import nettoyer_fichier
from backend.app.search.nettoyage import supprimer_stopwords

@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("La MER, la mer !", "la mer la mer"),
        ("  mer\t  bateau\r\nile  ", "mer bateau ile"),
        ("L'été, c'est beau.", "l été c est beau"),
        ("l’été porte-monnaie", "l été porte monnaie"),
        ("mer,bateau/ile", "mer bateau ile"),
        ("bateau42mer 2026", "bateau mer"),
        ("mer²ile ١٢٣", "mer ile"),
        ("ÉTÉ, forêt et garçon", "été forêt et garçon"),
        ("E\u0301TE\u0301", "été"),
        ("mer_bateau 🌊 ile", "mer bateau ile"),
        ("", ""),
        (" \n\t ", ""),
        ("123 -- !!!", ""),
    ],
)
def test_nettoyer_texte(texte, attendu):
    # On verifie le nettoyage de differents textes
    assert nettoyer_texte(texte) == attendu


def test_decouper_mots():
    # On garde l'ordre et les repetitions
    assert decouper_mots("La mer, la MER !") == [
        "la", "mer", "la", "mer"
    ]


def test_sans_stemming():
    # Le singulier et le pluriel restent differents
    assert decouper_mots("Bateau bateaux") == ["bateau", "bateaux"]


def test_texte_sans_mots():
    # Un texte vide ne contient aucun mot
    assert decouper_mots("") == []
    assert decouper_mots("42 !!!") == []


def test_nettoyage_repetable():
    # Nettoyer deux fois donne le meme resultat
    texte = nettoyer_texte("L'ÉTÉ, la MER ! 2026")

    assert nettoyer_texte(texte) == texte


def test_nettoyage_et_index():
    # On verifie que le nettoyage fonctionne avec l'index
    livres = {
        "1": decouper_mots("Mer, MER ! L'été."),
        "2": decouper_mots("La mer et la forêt."),
    }

    index = creer_index(livres)

    assert index == {
        "mer": {"1": 2, "2": 1},
        "l": {"1": 1},
        "été": {"1": 1},
        "la": {"2": 2},
        "et": {"2": 1},
        "forêt": {"2": 1},
    }

    mot = decouper_mots("MER!")[0]
    assert chercher_mot(index, mot) == {"1": 2, "2": 1}
    assert chercher_mot(index, "ete") == {}


def test_nettoyer_fichier(tmp_path):
    # On cree le JSON sans modifier le livre original
    source = tmp_path / "livre.txt"
    sortie = tmp_path / "mots.json"

    original = "Été, MER !\r\nLa mer.\r\n".encode("utf-8-sig")
    source.write_bytes(original)

    nettoyer_fichier(source, sortie)

    assert json.loads(sortie.read_text(encoding="utf-8")) == [
        "été", "mer", "la", "mer"
    ]
    assert source.read_bytes() == original


def test_fichier_vide(tmp_path):
    # Un fichier vide donne une liste vide
    source = tmp_path / "livre.txt"
    sortie = tmp_path / "mots.json"

    source.write_text("", encoding="utf-8")

    nettoyer_fichier(source, sortie)

    assert json.loads(sortie.read_text(encoding="utf-8")) == []


def test_source_absente(tmp_path):
    # On signale si le livre n'existe pas
    sortie = tmp_path / "mots.json"

    with pytest.raises(FileNotFoundError):
        nettoyer_fichier(tmp_path / "absent.txt", sortie)

    assert not sortie.exists()


def test_encodage_invalide(tmp_path):
    # On refuse un fichier qui n'est pas en UTF-8
    source = tmp_path / "livre.txt"
    sortie = tmp_path / "mots.json"

    source.write_bytes(b"\xffmer")

    with pytest.raises(UnicodeDecodeError):
        nettoyer_fichier(source, sortie)

    assert not sortie.exists()


def test_sortie_existante(tmp_path):
    # On ne remplace pas un fichier deja present
    source = tmp_path / "livre.txt"
    sortie = tmp_path / "mots.json"

    source.write_text("La mer", encoding="utf-8")
    sortie.write_text("a conserver", encoding="utf-8")

    with pytest.raises(FileExistsError):
        nettoyer_fichier(source, sortie)

    assert sortie.read_text(encoding="utf-8") == "a conserver"


def test_source_protegee(tmp_path):
    # On ne doit jamais ecraser le livre original
    source = tmp_path / "livre.txt"
    source.write_text("La MER !", encoding="utf-8")

    with pytest.raises(FileExistsError):
        nettoyer_fichier(source, source)

    assert source.read_text(encoding="utf-8") == "La MER !"


def test_commande(tmp_path):
    # On teste le script comme depuis le terminal
    source = tmp_path / "livre exemple.txt"
    sortie = tmp_path / "mots exemple.json"

    source.write_text("La MER, la mer !", encoding="utf-8")

    resultat = subprocess.run(
        [sys.executable, "-m", "scripts.clean_books", str(source), str(sortie)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert resultat.returncode == 0, resultat.stderr
    assert json.loads(sortie.read_text(encoding="utf-8")) == [
        "la", "mer", "la", "mer"
    ]


def test_commande_en_erreur(tmp_path):
    # On verifie que la commande signale un fichier absent
    sortie = tmp_path / "mots.json"

    resultat = subprocess.run(
        [
            sys.executable, "-m", "scripts.clean_books",
            str(tmp_path / "absent.txt"), str(sortie),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert resultat.returncode != 0
    assert "FileNotFoundError" in resultat.stderr
    assert not sortie.exists()
def test_supprimer_stopwords():
    """Vérifie que les stopwords sont supprimés."""
    mots = ["la", "mer", "et", "le", "bateau"]
    stopwords = {"la", "et", "le"}

    resultat = supprimer_stopwords(mots, stopwords)

    assert resultat == ["mer", "bateau"]


def test_garder_repetitions():
    """Vérifie que les mots répétés sont conservés."""
    mots = ["la", "mer", "et", "la", "mer"]
    stopwords = {"la", "et"}

    resultat = supprimer_stopwords(mots, stopwords)

    assert resultat == ["mer", "mer"]