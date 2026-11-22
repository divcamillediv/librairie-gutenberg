# Jeu synthétique — pas un corpus de livres

`book_terms.json` représente dix documents fictifs sous forme de listes JSON
de termes uniques, à convertir en ensembles Python. Les identifiants `sample-*`
ne sont pas des identifiants Gutenberg. Ces termes sont déjà préparés :
ce jeu ne valide ni le nettoyage, ni le stemming, ni l'indexation.

Cas utiles pour les premiers tests :

| Paire | Propriété | Similarité attendue |
|---|---|---|
| `sample-01`, `sample-02` | Ensembles identiques non vides | 1 |
| `sample-01`, `sample-03` | Deux termes communs, quatre dans l'union | 0,5 |
| `sample-01`, `sample-04` | Ensembles disjoints | 0 |
| `sample-01`, `sample-06` | Un terme commun, trois dans l'union | 1/3 |
| `sample-01`, `sample-05` | Un seul ensemble vide | 0 |
| `sample-05`, `sample-05` | Deux ensembles vides | Convention à valider |

`sample-10` permettra de vérifier la conservation d'un sommet isolé dans un
graphe ne conservant que des similarités strictement positives.

Le format est une proposition de contrat. Aucune métadonnée ni aucun texte
réel n'est fourni ici. Les tests API auront besoin de leurs propres métadonnées
et textes de test cohérents. Les dix vrais livres de test restent à préparer.

## Livres d'exemple de la couche web

`books.json`, `texts/`, `neighbors.json` et `pagerank.json` servent au moteur simulé
de l'API (`backend/app/mocks.py`) en attendant les vrais modules. Les identifiants,
titres et auteurs sont ceux de dix livres Gutenberg, mais chaque texte est un court
résumé rédigé pour le développement (moins de 200 mots), marqué
`[SIMULATED SAMPLE TEXT]`. PageRank et similarités sont fictifs. Ces fichiers sont
générés par `scripts/make_sample_data.py` et ne remplacent pas les dix vrais livres
de test.
