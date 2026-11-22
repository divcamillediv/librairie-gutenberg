"""Exceptions partagées entre les modules (contrat commun).

Les modules de recherche lèvent ces exceptions ; les routeurs FastAPI les
traduisent en erreurs HTTP 400 avec un message lisible par l'utilisateur.
"""


class InvalidRegexError(ValueError):
    """Motif RegEx invalide, trop long ou trop coûteux à évaluer."""
