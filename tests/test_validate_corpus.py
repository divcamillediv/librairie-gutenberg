from scripts.validate_corpus import verifier_longueur_livre
from scripts.validate_corpus import valider_corpus

def test_verifier_longueur_livre(tmp_path):
    chemin = tmp_path / "livre.txt"
    chemin.write_text("bonjour " * 100, encoding="utf-8")

    assert verifier_longueur_livre(chemin, 50) is True
    assert verifier_longueur_livre(chemin, 200) is False

def test_valider_corpus(tmp_path):
    (tmp_path / "1.txt").write_text("bonjour " * 100, encoding="utf-8")
    (tmp_path / "2.txt").write_text("salut " * 20, encoding="utf-8")
    (tmp_path / "3.txt").write_text("merci " * 120, encoding="utf-8")

    resultat = valider_corpus(
        tmp_path,
        minimum_livres=2,
        minimum_mots=50
    )

    assert resultat["total_livres"] == 3
    assert resultat["livres_valides"] == 2
    assert resultat["livres_trop_courts"] == ["2"]
    assert resultat["corpus_valide"] is True
