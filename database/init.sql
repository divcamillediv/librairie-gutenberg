CREATE TABLE IF NOT EXISTS books (
                                     id TEXT PRIMARY KEY,
                                     title TEXT NOT NULL,
                                     authors TEXT,
                                     language TEXT,
                                     issued DATE,
                                     subjects TEXT,
                                     locc TEXT,
                                     bookshelves TEXT,
                                     word_count INTEGER NOT NULL CHECK (word_count >= 10000),
    file_path TEXT NOT NULL UNIQUE
    );