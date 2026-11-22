"""Recherche avancée par expression régulière sur les termes de l'index.

Le motif doit correspondre à un terme ENTIER de l'index (équivalent de
re.fullmatch) : « whal » ne trouve pas « whale », « whal.* » oui. Les termes
de l'index sont en minuscules, sans ponctuation ni chiffres, et sans stopwords :
un motif portant sur un stopword ou sur plusieurs mots ne trouve rien.

Garde-fous : longueur maximale (également vérifiée par l'API), motif invalide
et quantificateurs imbriqués du type (a+)+ refusés, car le module `re` ne peut
pas être interrompu en cours d'évaluation.
"""
from __future__ import annotations

import re

from app.errors import InvalidRegexError

from . import inverted_index
from .inverted_index import chercher_regex

LONGUEUR_MAX = 100

# Groupe contenant un quantificateur, lui-même suivi d'un quantificateur : (a+)+, (a*b)*, (x+){2,}
_QUANTIFICATEURS_IMBRIQUES = re.compile(r"\((?:[^()\\]|\\.)*[+*}](?:[^()\\]|\\.)*\)(?:[+*]|\{\d+,?\d*\})")


def regex_search(pattern: str) -> dict[str, int]:
    """Retourne {book_id: occurrences cumulées} des livres dont un terme vérifie le motif."""
    if not pattern or not pattern.strip():
        return {}
    if len(pattern) > LONGUEUR_MAX:
        raise InvalidRegexError(f"L'expression régulière dépasse {LONGUEUR_MAX} caractères.")
    if _QUANTIFICATEURS_IMBRIQUES.search(pattern):
        raise InvalidRegexError(
            "Motif refusé : quantificateurs imbriqués, par exemple (a+)+, trop coûteux à évaluer."
        )
    try:
        re.compile(pattern)
    except re.error as exc:
        raise InvalidRegexError(f"Expression régulière invalide : {exc}") from exc

    # Ancrage : le motif doit couvrir tout le terme.
    return chercher_regex(inverted_index.index_charge, f"^(?:{pattern})$")
