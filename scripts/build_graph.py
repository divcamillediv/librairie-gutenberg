"""Construit le graphe de Jaccard entre les livres (data/graphs/graph.json).

Nœud = livre ; arête = similarité de Jaccard entre les ensembles de mots
distincts de deux livres, conservée si 0 < J et J >= seuil.

Les mots sont nettoyés comme pour l'index inversé (decouper_mots), puis les
stopwords anglais sont retirés.

Deux optimisations, sans changer le résultat :
- nettoyage des textes avec str.translate (en C) au lieu d'une boucle Python
  caractère par caractère ; même règle que nettoyage.nettoyer_texte ;
- toutes les intersections calculées d'un coup par produit de matrices creuses
  au lieu de 1,4 million de comparaisons paire par paire.
L'option --lent utilise le calcul de référence (decouper_mots et
construire_graphe), pour vérifier que le graphe est identique.

    python scripts/build_graph.py --corpus data/raw
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path
from time import perf_counter

racine = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine))

from backend.app.recommendations.graph_builder import construire_graphe
from backend.app.search.nettoyage import decouper_mots, supprimer_stopwords
from backend.app.search.stopwords import STOPWORDS_ANGLAIS


# ---------------------------------------------------------------- nettoyage
class _LettreOuEspace(dict):
    """Table pour str.translate : garde les lettres, remplace tout le reste par une espace.

    Même test que nettoyage.nettoyer_texte (caractere.isalpha()). La décision
    est calculée une seule fois par caractère distinct, puis mémorisée.
    """

    def __missing__(self, code: int):
        valeur = code if chr(code).isalpha() else " "  # code : caractère conservé tel quel
        self[code] = valeur
        return valeur


_TABLE = _LettreOuEspace()


def decouper_mots_rapide(texte: str) -> list[str]:
    """Équivalent de nettoyage.decouper_mots (mêmes mots, même ordre), en plus rapide."""
    texte = unicodedata.normalize("NFC", texte).lower()
    return texte.translate(_TABLE).split()


def nettoyer_mots(texte: str, rapide: bool = True) -> set[str]:
    """Nettoie le texte et retire les mots courants."""

    # Utiliser le même nettoyage que pour l'index inversé
    mots = decouper_mots_rapide(texte) if rapide else decouper_mots(texte)

    # Supprimer les stopwords anglais
    mots = supprimer_stopwords(mots, STOPWORDS_ANGLAIS)

    # Jaccard utilise les mots distincts
    return set(mots)


def charger_livres(dossier: Path, rapide: bool = True) -> dict[str, set[str]]:
    """Lit les livres et récupère leurs mots distincts."""

    livres = {}
    fichiers = sorted(dossier.glob("*.txt"))

    for numero, fichier in enumerate(fichiers, start=1):
        identifiant = fichier.stem
        texte = fichier.read_text(
            encoding="utf-8-sig",
            errors="replace"
        )

        livres[identifiant] = nettoyer_mots(texte, rapide=rapide)

        if numero % 200 == 0 or numero == len(fichiers):
            print(f"  lecture : {numero}/{len(fichiers)} livres", flush=True)

    return livres


# ------------------------------------------------------------------- graphe
def construire_graphe_rapide(livres: dict[str, set[str]], seuil: float = 0.3) -> dict:
    """Même graphe que construire_graphe, calculé par produit de matrices creuses.

    Chaque livre devient une ligne d'une matrice binaire livres x mots. Le
    produit X . X^T donne d'un coup toutes les intersections |A ∩ B| ; l'union
    s'en déduit : |A ∪ B| = |A| + |B| - |A ∩ B|. La similarité, le seuil
    (0 < J et J >= seuil) et l'ordre des voisins sont ceux de construire_graphe,
    donc le fichier produit est identique.
    """
    import numpy as np
    from scipy import sparse

    if not 0 <= seuil <= 1:
        raise ValueError("Le seuil doit être compris entre 0 et 1")

    ids = list(livres)
    graphe = {id_livre: {} for id_livre in ids}
    if len(ids) < 2:
        return graphe

    # Matrice binaire creuse : une ligne par livre, une colonne par mot distinct.
    numeros: dict[str, int] = {}
    lignes, colonnes = [], []
    for ligne, id_livre in enumerate(ids):
        for mot in livres[id_livre]:
            lignes.append(ligne)
            colonnes.append(numeros.setdefault(mot, len(numeros)))
    x = sparse.csr_matrix(
        (np.ones(len(lignes), dtype=np.int32), (lignes, colonnes)),
        shape=(len(ids), max(len(numeros), 1)),
    )

    intersections = (x @ x.T).toarray()          # |A ∩ B| pour toutes les paires
    tailles = np.diag(intersections).copy()      # |A|
    unions = tailles[:, None] + tailles[None, :] - intersections

    for i, id1 in enumerate(ids):
        for j in range(i + 1, len(ids)):
            id2 = ids[j]
            if unions[i, j] == 0:
                similarite = 1.0                 # deux ensembles vides (convention de jaccard_similarity)
            else:
                similarite = int(intersections[i, j]) / int(unions[i, j])
            if 0 < similarite and similarite >= seuil:
                graphe[id1][id2] = similarite
                graphe[id2][id1] = similarite

    return graphe


def enregistrer_graphe(graphe: dict, destination: Path) -> None:
    """Enregistre le graphe dans un fichier JSON."""

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as fichier:
        json.dump(graphe, fichier, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--corpus",
        type=Path,
        required=True
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/graphs/graph.json")
    )

    parser.add_argument(
        "--seuil",
        type=float,
        default=0.3
    )

    parser.add_argument(
        "--lent",
        action="store_true",
        help="Calcul de référence (decouper_mots et construire_graphe), beaucoup plus long"
    )

    args = parser.parse_args()

    if not args.corpus.is_dir():
        parser.error("Le dossier du corpus est introuvable")

    debut = perf_counter()

    # Charger les livres et retirer les stopwords
    livres = charger_livres(args.corpus, rapide=not args.lent)

    print(f"Livres chargés : {len(livres)} ({perf_counter() - debut:.1f} s)", flush=True)

    # Construire le graphe avec les mots nettoyés
    debut_graphe = perf_counter()
    if args.lent:
        graphe = construire_graphe(livres, seuil=args.seuil)
    else:
        graphe = construire_graphe_rapide(livres, seuil=args.seuil)
    print(f"Similarités calculées ({perf_counter() - debut_graphe:.1f} s)", flush=True)

    duree = perf_counter() - debut

    # Sauvegarder le graphe
    enregistrer_graphe(graphe, args.output)

    nombre_aretes = sum(
        len(voisins) for voisins in graphe.values()
    ) // 2

    print(f"Sommets : {len(graphe)}")
    print(f"Arêtes : {nombre_aretes}")
    print(f"Temps total : {duree:.2f} secondes")
    print(f"Graphe enregistré dans : {args.output}")


if __name__ == "__main__":
    main()