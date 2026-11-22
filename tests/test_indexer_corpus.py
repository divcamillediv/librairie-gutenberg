
import json

from scripts.indexer_corpus import indexer_corpus


def test_indexer_corpus(tmp_path):
    # On prépare deux livres
    dossier = tmp_path / "livres"
    dossier.mkdir()

    (dossier / "11.txt").write_text("the alice rabbit", encoding="utf-8")
    (dossier / "84.txt").write_text("the mystery castle", encoding="utf-8")

    # On choisit où enregistrer l'index
    chemin_index = tmp_path / "indexes" / "index.json"

    # On construit et enregistre l'index
    indexer_corpus(dossier, chemin_index)

    # On vérifie le fichier enregistré
    assert chemin_index.exists()

    index = json.loads(chemin_index.read_text(encoding="utf-8"))

    assert "the" not in index
    assert index["alice"] == {"11": 1}
    assert index["mystery"] == {"84": 1}
