from pathlib import Path
from unittest.mock import patch

from scripts.download_books import telecharger_livre, telecharger_plusieurs_livres

def test_telecharger_plusieurs_livres(tmp_path):
    def faux_telechargement(identifiant, dossier):
        chemin = dossier / f"{identifiant}.txt"
        chemin.write_text("Texte du livre", encoding="utf-8")
        return chemin

    with patch(
            "scripts.download_books.telecharger_livre",
            side_effect=faux_telechargement
    ):
        resultat = telecharger_plusieurs_livres([11, 84], tmp_path)

    assert set(resultat) == {11, 84}
    assert all(chemin.exists() for chemin in resultat.values())

def test_continuer_apres_erreur(tmp_path):
    def faux_telechargement(identifiant, dossier):
        if identifiant == 84:
            raise OSError("Site indisponible")

        chemin = dossier / f"{identifiant}.txt"
        chemin.write_text("Texte du livre", encoding="utf-8")
        return chemin

    with patch(
            "scripts.download_books.telecharger_livre",
            side_effect=faux_telechargement
    ):
        resultat = telecharger_plusieurs_livres([11, 84, 1342], tmp_path)

    assert set(resultat) == {11, 1342}
    assert 84 not in resultat

def test_retélécharger_fichier_vide(tmp_path):
    # On crée un fichier vide
    chemin = tmp_path / "11.txt"
    chemin.write_bytes(b"")

    # On simule une réponse de Gutenberg
    from unittest.mock import patch, MagicMock

    reponse = MagicMock()
    reponse.__enter__.return_value.read.return_value = b"Texte du livre"

    with patch("scripts.download_books.urlopen", return_value=reponse):
        resultat = telecharger_livre(11, tmp_path)

    assert resultat == chemin
    assert chemin.read_bytes() == b"Texte du livre"

