"""Nettoyage des textes avant l'indexation."""

import unicodedata


def nettoyer_texte(texte: str) -> str:
    """Met le texte en minuscules et retire les caracteres inutiles."""

    # On garde les accents et on met en minuscules
    texte = unicodedata.normalize("NFC", texte).lower()

    caracteres = []

    # On garde les lettres et on remplace le reste par des espaces
    for caractere in texte:
        if caractere.isalpha():
            caracteres.append(caractere)
        else:
            caracteres.append(" ")

    # On rassemble le texte et on retire les espaces en trop
    texte = "".join(caracteres)
    return " ".join(texte.split())


def decouper_mots(texte: str) -> list[str]:
    """Renvoie la liste des mots nettoyes."""

    return nettoyer_texte(texte).split()

def supprimer_stopwords(mots: list[str], stopwords: set[str]) -> list[str]:
    """Retire les mots courants peu utiles pour la recherche comme : le,la,the."""

    # On prépare une liste pour garder les mots utiles
    mots_filtres = []

    # On parcourt les mots du texte
    for mot in mots:

        # On garde le mot s'il ne fait pas partie des stopwords
        if mot not in stopwords:
            mots_filtres.append(mot)

    return mots_filtres
