# DAAR — Moteur de recherche de livres

Application web de recherche dans une bibliothèque de livres du projet Gutenberg :
recherche par mot-clé, recherche avancée par RegEx, classement par pertinence (occurrences
et PageRank sur le graphe de Jaccard), suggestions de livres voisins, lecture du texte.

## État actuel

| Partie | Responsable | État |
|---|---|---|
| API FastAPI, interface React/Vite, lecture des livres, tests web | Camille | Fonctionnel |
| Corpus, nettoyage, index inversé, recherche simple et RegEx | Kenza | Fonctionnel, branché sur l'API |
| Jaccard, graphe, PageRank, classement, recommandations | Nadine | Fonctionnel, branché sur l'API |
| Base PostgreSQL des métadonnées | Kenza, Nadine | Lue par l'API au démarrage |
| Docker Compose (base, backend, frontend), CI | Collectif | Écrits ; Docker reste à lancer sur une machine équipée |

Au démarrage, l'API charge une seule fois :

| Donnée | Source | Si absente |
|---|---|---|
| Métadonnées des livres | PostgreSQL (si `POSTGRES_PASSWORD` est défini), sinon `data/metadata/books.json` | 10 livres d'exemple de `data/sample/` |
| Index inversé | `data/indexes/index_complet.json` | Recherche simulée |
| Graphe de Jaccard, PageRank | `data/graphs/graph.json`, `data/graphs/pagerank.json` | Classement et suggestions simulés |

`/api/health` indique la source des métadonnées (`postgres`, `corpus` ou `sample`) et,
module par module, `real` ou `mock`. L'interface affiche un bandeau « Mode démonstration »
tant qu'une partie est simulée.

## Organisation

- `backend/app/main.py`, `config/`, `books/` : point d'entrée, configuration, accès aux livres.
- `backend/app/search` : routes de recherche, accès à l'index, recherche simple et RegEx.
- `backend/app/recommendations` : Jaccard, matrice, graphe et recommandations.
- `backend/app/ranking` : PageRank et classement.
- `backend/app/integration.py`, `mocks.py` : branchement des modules et moteur simulé.
- `frontend` : interface web (pages, composants, appels à l'API).
- `scripts` : préparation hors ligne du corpus et des artefacts.
- `tests` : tests pytest (API active ; autres modules à développer progressivement).
- `data/sample` : jeux d'exemple versionnés (voir `data/sample/README.md`).
- `docs` : contrats proposés, étapes de développement et documentation.

Les calculs de matrice, de graphe et de PageRank doivent être réalisés hors ligne.
L'API charge les artefacts persistés au démarrage au lieu de les recalculer à chaque requête.
L'infrastructure et l'intégration sont collectives.

## Première étape des algorithmes : similarité

Lire [les instructions](docs/instructions.md), puis
[les contrats proposés](docs/api_contract.md).
Le premier incrément algorithmique sera limité à `jaccard_similarity`,
`jaccard_distance` et leurs tests. Il ne nécessite ni corpus complet, ni API,
ni frontend.

`data/sample/book_terms.json` contient dix ensembles fictifs. Ils servent aux tests
unitaires ; ils ne satisfont pas l'exigence de dix vrais livres de test ou celle
des 1 664 livres d'au moins 10 000 mots.

## Installation et démarrage

Prérequis : Python 3.11 ou plus récent, Node.js 20 ou plus récent, Docker (pour la base).

### 1. Configuration

```bash
cp .env.example .env      # puis remplacer POSTGRES_PASSWORD=change-me par un vrai mot de passe
```

### 2. Données (une fois, hors ligne)

Depuis la racine, environnement virtuel activé (voir étape 4) :

```bash
python scripts/telecharger_depuis_huggingface.py                              # data/raw + data/metadata (pip install datasets)
python -m scripts.indexer_corpus data/raw data/indexes/index_complet.json     # index inversé
python scripts/build_graph.py --corpus data/raw                               # data/graphs/graph.json
python scripts/compute_pagerank.py                                            # data/graphs/pagerank.json
```

### 3. Base de données

```bash
docker compose -f docker-compose.storage.yml --env-file .env up -d           # PostgreSQL seul, port 5432 local
set -a; source .env; set +a                                                   # exporte POSTGRES_PASSWORD...
python scripts/import_metadata.py                                             # remplit la table books
```

Sans base (pas de `POSTGRES_PASSWORD`), l'API lit `data/metadata/books.json` ou, à défaut,
les 10 livres d'exemple.

### 4. Backend et frontend

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --env-file ../.env

# Terminal 2 — frontend (une fois le backend démarré)
cd frontend
npm install
npm run dev
```

- Application : <http://localhost:5173>
- État de l'API : <http://localhost:8000/api/health>
- Documentation de l'API : <http://localhost:8000/docs>

Au démarrage, le backend doit afficher « 1700 livres chargés depuis PostgreSQL » et
« Chargé : index inversé », « graphe de Jaccard », « PageRank ». Le serveur Vite relaie
`/api` vers le backend.

### Avec Docker (base + backend + frontend)

```bash
docker compose up --build -d db                  # démarre la base
python scripts/import_metadata.py                # une fois, variables de .env exportées
docker compose up --build
```

- Application : <http://localhost:8080>
- Documentation de l'API : <http://localhost:8000/docs>

Les données de `data/` (textes, index, graphe) sont montées en lecture seule dans le backend.

## Utilisation depuis plusieurs machines

1. Connecter le serveur et les clients au même réseau (Wi-Fi ou partage de connexion).
2. Trouver l'adresse IP du serveur : `ipconfig` (Windows), `ipconfig getifaddr en0` (macOS),
   `hostname -I` (Linux).
3. Sur chaque client (PC, téléphone), ouvrir `http://<IP-du-serveur>:5173` (développement)
   ou `http://<IP-du-serveur>:8080` (Docker).

## Exemples de requêtes

Dans l'interface : saisir un mot-clé sur l'accueil, ou une expression régulière dans
l'onglet RegEx. Directement sur l'API (jeu d'exemple) :

```bash
curl "http://localhost:8000/api/health"
curl "http://localhost:8000/api/books?limit=5&offset=0"
curl "http://localhost:8000/api/books/2701"
curl "http://localhost:8000/api/books/2701/text?page=1"
curl "http://localhost:8000/api/books/2701/similar"
curl "http://localhost:8000/api/search?q=whale"
curl -G "http://localhost:8000/api/search/advanced" --data-urlencode "regex=whal(e|es|ing)"
```

| Requête | Résultat attendu sur le jeu d'exemple |
|---|---|
| `q=moby dick` | *Moby Dick* |
| `q=harpooner` | Un seul livre, *Moby Dick* : le mot n'apparaît dans aucun titre |
| `q=ship` | Plusieurs livres classés par score décroissant, avec suggestions |
| `q=zzzz` | `total: 0`, listes vides |
| `q=` (vide) | Erreur `400` |
| `regex=sea.*` | Livres contenant un mot commençant par `sea` |
| `regex=(bad` | Erreur `400` avec le motif de l'erreur |

Le format complet des réponses est dans [docs/api_contract.md](docs/api_contract.md).

## Tests

```bash
# Depuis la racine, environnement virtuel activé
python -m pytest            # API ; les tests des modules algorithmiques sont ignorés (squelettes)

cd frontend
npm test                    # client de l'API + parcours recherche → résultats → lecture → suggestions
```

## Git et intégration continue

Trois branches de travail : `feature/data-search` (Kenza), `feature/graph-ranking`
(Nadine), `feature/web-app` (Camille). Une Pull Request relue par une autre personne
avant toute fusion dans `main`.

Le workflow `.github/workflows/ci.yml` s'exécute à chaque push sur `main` ou sur une
branche `feature/**`, et à chaque Pull Request :

| Job | Étapes |
|---|---|
| `backend` | Installation de `backend/requirements.txt`, puis `python -m pytest` |
| `frontend` | `npm ci`, `npm test`, `npm run build` |

Une CI verte prouve que la couche web fonctionne et que rien n'est cassé à l'import. Elle
ne valide pas les algorithmes tant que leurs tests sont ignorés : en écrivant les vrais
tests d'un module, retirer le `pytest.skip` du fichier concerné.

Les données volumineuses (`data/raw`, `processed`, `indexes`, `graphs`, `metadata`) et
les secrets sont exclus du versionnement. Jeux d'exemple, scripts, tests et documents sont
versionnés.

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| Recherche sans réponse, ou « Le serveur est injoignable » | Backend arrêté, ou frontend lancé avant lui | Vérifier <http://localhost:8000/api/health>, puis arrêter et relancer `npm run dev` |
| `http proxy error` / `ECONNREFUSED` dans le terminal Vite | Le relais Vite ne joint pas le backend | Vérifier que le backend écoute sur le port 8000 ; sinon définir `VITE_PROXY_TARGET` et relancer `npm run dev` |
| « PostgreSQL indisponible » dans le terminal du backend | Base arrêtée, mauvais mot de passe, ou `--env-file ../.env` oublié | `docker compose -f docker-compose.storage.yml --env-file .env up -d` ; vérifier `.env` |
| « La table books de PostgreSQL est vide » | Métadonnées non importées | `python scripts/import_metadata.py` |
| Bandeau « Mode démonstration » | `data/metadata/books.json` absent, ou module encore en squelette | Normal tant que le corpus et les algorithmes ne sont pas livrés ; détail sur `/api/health` |
| « Le texte du livre n'est pas disponible » | `file_path` ne pointe pas vers un fichier de `data/` | Vérifier le fichier texte et le chemin relatif dans les métadonnées |
| La page ne s'ouvre pas depuis un autre appareil | Pare-feu, ou réseau qui isole les appareils (eduroam, Wi-Fi invité) | Autoriser le port 5173 (ou 8080) ; passer par un partage de connexion |
| `address already in use` | Port 8000, 5173 ou 8080 occupé | Arrêter l'autre programme, ou changer de port (`--port`, `.env`) |
| `ModuleNotFoundError: app` | `uvicorn` lancé hors de `backend/` | `cd backend` avant de lancer `uvicorn` ; pour `pytest`, se placer à la racine |
| Données non prises en compte | Le backend charge les fichiers au démarrage | Redémarrer le backend (`docker compose restart backend` avec Docker) |
