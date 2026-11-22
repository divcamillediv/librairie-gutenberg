from pathlib import Path
from urllib.request import urlopen


def telecharger_livre(identifiant: int, dossier: Path) -> Path:
    """Télécharge le texte d'un livre Gutenberg."""

    # On prépare le fichier de destination
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"{identifiant}.txt"

    # On garde le fichier seulement s'il contient des données
    if chemin.exists() and chemin.stat().st_size > 0:
        return chemin

    # On récupère le texte depuis Gutenberg
    url = f"https://www.gutenberg.org/ebooks/{identifiant}.txt.utf-8"

    with urlopen(url, timeout=30) as reponse:
        texte = reponse.read()

    # On enregistre le livre sans modifier son contenu
    chemin.write_bytes(texte)

    return chemin

def telecharger_plusieurs_livres(
        identifiants: list[int],
        dossier: Path
) -> dict[int, Path]:
    """Télécharge plusieurs livres et conserve ceux qui ont réussi."""

    livres_telecharges = {}

    for identifiant in identifiants:
        try:
            chemin = telecharger_livre(identifiant, dossier)
            livres_telecharges[identifiant] = chemin

        except (OSError, ValueError) as erreur:
            print(f"Impossible de télécharger le livre {identifiant} : {erreur}")

    return livres_telecharges

