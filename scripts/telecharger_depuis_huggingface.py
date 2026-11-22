
import json
from pathlib import Path
from datasets import load_dataset


def telecharger_livres(limite=1700):
    dossier = Path("data/raw")
    dossier.mkdir(parents=True, exist_ok=True)

    dossier_metadata = Path("data/metadata")
    dossier_metadata.mkdir(parents=True, exist_ok=True)

    livres_existants = {
        fichier.stem
        for fichier in dossier.glob("*.txt")
        if fichier.stat().st_size > 0
    }

    print(f"Livres déjà présents : {len(livres_existants)}")

    if len(livres_existants) >= limite:
        print("Objectif déjà atteint.")
        return

    ds = load_dataset(
        "sedthh/gutenberg_english",
        split="train",
        streaming=True
    )

    compteur = len(livres_existants)

    for livre in ds:
        texte = livre.get("TEXT")
        if not isinstance(texte, str):
            continue

        if len(texte.split()) < 10000:
            continue

        try:
            metadata = json.loads(livre["METADATA"])
        except (TypeError, ValueError):
            continue

        identifiant = metadata.get("text_id")
        if identifiant is None:
            continue

        identifiant = str(identifiant)

        if not identifiant.isdigit():
            continue

        chemin = dossier / f"{identifiant}.txt"
        chemin_metadata = dossier_metadata / f"{identifiant}.json"

        if identifiant in livres_existants:
            continue

        chemin.write_text(texte, encoding="utf-8")
        chemin_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        livres_existants.add(identifiant)
        compteur += 1

        print(f"[{compteur}/{limite}] Livre {identifiant} enregistré")

        if compteur >= limite:
            break

    print(f"Terminé : {compteur} livres disponibles.")


if __name__ == "__main__":
    telecharger_livres()
