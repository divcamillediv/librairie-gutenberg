import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

# Permet d'utiliser les fonctions du backend
racine = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(racine))

from backend.app.ranking.pagerank import calculer_pagerank


def charger_graphe(chemin: Path) -> dict:
    with chemin.open("r", encoding="utf-8") as fichier:
        return json.load(fichier)


def enregistrer_scores(scores: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as fichier:
        json.dump(scores, fichier, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path("data/graphs/graph.json")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/graphs/pagerank.json")
    )
    parser.add_argument("--alpha", type=float, default=0.85)

    args = parser.parse_args()

    if not args.graph.is_file():
        parser.error("Le fichier du graphe est introuvable")

    graphe = charger_graphe(args.graph)

    debut = perf_counter()
    scores = calculer_pagerank(graphe, alpha=args.alpha)
    duree = perf_counter() - debut

    enregistrer_scores(scores, args.output)

    print(f"Livres : {len(scores)}")
    print(f"Temps de calcul PageRank : {duree:.4f} secondes")
    print(f"Somme des scores : {sum(scores.values()):.6f}")
    print(f"Scores enregistrés dans : {args.output}")

    # On affiche les cinq livres avec les meilleurs scores
    classement = sorted(
        scores.items(),
        key=lambda element: element[1],
        reverse=True
    )

    print("Meilleurs scores PageRank :")
    for identifiant, score in classement[:5]:
        print(f"  Livre {identifiant} : {score:.6f}")


if __name__ == "__main__":
    main()
