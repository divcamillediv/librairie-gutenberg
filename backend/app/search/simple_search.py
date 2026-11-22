"""Recherche simple par mot-clé, branchée sur l'API.

Sémantique (celle de recherche.rechercher_livres) : la requête est nettoyée
comme les livres (minuscules, lettres seulement), les stopwords anglais sont
retirés, puis un livre est retenu s'il contient TOUS les mots restants (ET).
Le nombre d'occurrences renvoyé est la somme des fréquences de ces mots.
"""
from __future__ import annotations

from . import inverted_index
from .recherche import rechercher_livres


def search(query: str) -> dict[str, int]:
    """Retourne {book_id: occurrences} pour la requête ({} si rien ne correspond)."""
    if not query or not query.strip():
        return {}
    return rechercher_livres(inverted_index.index_charge, query)
