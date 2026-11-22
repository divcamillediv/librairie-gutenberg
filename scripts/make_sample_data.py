"""Génère le jeu d'exemple versionné : 10 livres SIMULÉS (responsable : Camille).

Étape 3 du plan : « créer des réponses simulées sur 10 livres ; ne pas attendre
le corpus complet ». Les identifiants, titres et auteurs sont ceux de vrais
livres du projet Gutenberg, mais les textes sont de courts résumés rédigés pour
la démonstration : ils ne respectent PAS le seuil de 10 000 mots et ne font pas
partie du corpus final. Les valeurs de PageRank et de similarité sont fictives.

    python scripts/make_sample_data.py

Produit data/sample/{books.json, pagerank.json, neighbors.json, texts/*.txt}.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "sample"
HEADER = "[SIMULATED SAMPLE TEXT - short placeholder written for development, not the text of the book]"

BOOKS = [
    (1342, "Pride and Prejudice", "Jane Austen", [
        "In a quiet English county, a family with five unmarried daughters learns that a wealthy young gentleman has rented the neighbouring estate. The mother dreams of a marriage; the father prefers his library and his irony.",
        "The second daughter, quick and proud of her judgement, meets a reserved gentleman at a country ball. His pride offends her, and her prejudice blinds her. Letters, visits and long walks across the fields slowly change what each believes about the other.",
        "The novel observes manners, money and marriage with wit. Every conversation in a drawing room is a small duel, and every letter carries a secret that changes the fortune of a sister.",
    ]),
    (84, "Frankenstein; Or, The Modern Prometheus", "Mary Wollstonecraft Shelley", [
        "A sea captain sailing toward the frozen north rescues an exhausted stranger from the ice. The stranger tells his story: as a student of natural science he discovered how to give life to dead matter.",
        "In a lonely laboratory he assembles a creature and animates it, then flees in horror from the monster he has made. Abandoned, the creature learns language by watching a poor family and begs his creator for a companion.",
        "Refused and alone, the monster turns to revenge. Creator and creature pursue each other across mountains, lakes and finally the ice of the northern sea, where the ship of the captain waits.",
    ]),
    (11, "Alice's Adventures in Wonderland", "Lewis Carroll", [
        "On a warm afternoon a curious girl follows a white rabbit with a pocket watch and falls down a deep hole. At the bottom she finds a hall of locked doors, a tiny golden key and a bottle that makes her shrink.",
        "She meets a caterpillar on a mushroom, a grinning cat that vanishes, and a mad tea party where it is always six o'clock. Nothing follows the rules she learned at school, and every answer becomes another riddle.",
        "A furious queen of cards orders executions during a game of croquet. At the trial of the knave the girl grows to her full size, refuses the nonsense of the court, and wakes on the river bank beside her sister.",
    ]),
    (2701, "Moby Dick; Or, The Whale", "Herman Melville", [
        "A restless young sailor signs aboard a whaling ship leaving a cold island harbour. He shares a bed at the inn with a tattooed harpooner who becomes his closest friend.",
        "The captain of the ship walks the deck on a leg carved from whale bone. He nails a gold coin to the mast and swears the crew to hunt one white whale, the whale that maimed him. The ship crosses ocean after ocean, lowering boats for every whale it sights.",
        "The voyage becomes an obsession. When the white whale finally rises from the sea, the chase lasts three days, and only the sailor survives, floating on a coffin, to tell of the ship and the whale.",
    ]),
    (1661, "The Adventures of Sherlock Holmes", "Arthur Conan Doyle", [
        "In rooms above a London street, a detective studies tobacco ash, mud on a boot and the wear of a sleeve. His friend, a doctor, writes down each case with admiration and some confusion.",
        "A king fears a photograph, a pawnbroker with red hair is paid to copy an encyclopaedia, and a stepfather keeps a deadly snake. Each mystery begins with a visitor on the stairs and ends with a calm explanation by the fire.",
        "The detective insists that he only observes what others merely see. Crime in the great city is, for him, a puzzle of logic, and the doctor remains the faithful witness of every solution.",
    ]),
    (98, "A Tale of Two Cities", "Charles Dickens", [
        "Between London and Paris, in the years before a revolution, a doctor is released after long years in a prison tower. His daughter brings him back to life in a quiet English house.",
        "A French nobleman renounces his family name, and a careless English lawyer who resembles him loves the same woman. In Paris the wine shop of a patient, knitting woman keeps a register of enemies of the people.",
        "When the revolution fills the streets and the prison carts roll toward the guillotine, the lawyer takes the place of the condemned man. His sacrifice in one city saves a family in the other.",
    ]),
    (345, "Dracula", "Bram Stoker", [
        "A young English lawyer travels to a castle in the mountains to complete the sale of a London house. His host, an old count, never eats, casts no reflection and crawls down the castle wall at night.",
        "The count sails to England aboard a ship whose crew disappears one by one. A young woman grows pale and weak, and an old professor recognises the marks of a vampire. Letters, diaries and telegrams record the hunt.",
        "A small band of friends pursues the monster back across the sea to his castle. At sunset, in the snow, they end the long night of the count.",
    ]),
    (120, "Treasure Island", "Robert Louis Stevenson", [
        "At a lonely inn by the sea, a boy finds a map in the chest of a dead sailor. A squire and a doctor fit out a ship to seek the buried treasure of a pirate captain.",
        "The cook of the ship has one leg, a parrot and a secret: he and half the crew are pirates. Hidden in an apple barrel, the boy hears their plan for mutiny before the island is even in sight.",
        "On the island there are stockades, skeletons, a marooned sailor and a hunt for gold. The boy steals back the ship alone, and the one-legged cook escapes with a bag of coins.",
    ]),
    (1400, "Great Expectations", "Charles Dickens", [
        "On the marshes one cold evening, an orphan boy helps an escaped convict with food and a file. He grows up at the forge of a gentle blacksmith and is sent to play at the dark house of a rich woman who stopped all her clocks.",
        "There he meets a proud and beautiful girl and becomes ashamed of his rough hands. A lawyer announces that an unknown benefactor has given him great expectations, and he leaves for London to become a gentleman.",
        "The secret of his fortune returns from the other side of the sea. The boy learns the worth of loyalty, forgives old injuries, and finds his way back to the forge.",
    ]),
    (74, "The Adventures of Tom Sawyer", "Mark Twain", [
        "In a small town on a great river, a clever boy tricks his friends into whitewashing a fence for him. He plays pirate on an island, attends his own funeral and wins the heart of the new girl at school.",
        "One night in the graveyard he and his friend witness a murder and swear to keep silent. At the trial the boy finds the courage to speak, and the murderer escapes through a window.",
        "Lost in a cave during a picnic, the boy finds both the way out and the hidden treasure of the murderer. The town celebrates, and the two friends are suddenly rich.",
    ]),
]

# Similarités FICTIVES entre livres (arêtes non orientées du graphe simulé).
EDGES = [
    (98, 1400, 0.41), (84, 345, 0.38), (2701, 120, 0.36), (1342, 1400, 0.34),
    (120, 74, 0.31), (1342, 98, 0.29), (11, 74, 0.27), (1661, 345, 0.25),
    (1661, 98, 0.24), (84, 2701, 0.22), (11, 1342, 0.20),
]


def main() -> None:
    texts_dir = SAMPLE_DIR / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)

    metadata = []
    for book_id, title, author, paragraphs in BOOKS:
        text = "\n\n".join([HEADER, title.upper(), *paragraphs]) + "\n"
        (texts_dir / f"{book_id}.txt").write_text(text, encoding="utf-8")
        metadata.append({
            "id": book_id,
            "title": title,
            "author": author,
            "language": "en",
            "word_count": len(re.findall(r"\w+", text)),
            "file_path": f"data/sample/texts/{book_id}.txt",
            "source_url": f"https://www.gutenberg.org/ebooks/{book_id}",
        })

    neighbors: dict[int, list[dict]] = {book_id: [] for book_id, *_ in BOOKS}
    for a, b, similarity in EDGES:
        neighbors[a].append({"id": b, "similarity": similarity})
        neighbors[b].append({"id": a, "similarity": similarity})
    for items in neighbors.values():
        items.sort(key=lambda n: -n["similarity"])

    # PageRank fictif : proportionnel au degré pondéré, normalisé à 1.
    weights = {book_id: sum(n["similarity"] for n in items) for book_id, items in neighbors.items()}
    total = sum(weights.values())
    pagerank = {book_id: round(weight / total, 6) for book_id, weight in weights.items()}

    def dump(name: str, payload) -> None:
        (SAMPLE_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    dump("books.json", metadata)
    dump("neighbors.json", neighbors)
    dump("pagerank.json", pagerank)
    print(f"{len(metadata)} livres simulés écrits dans {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
