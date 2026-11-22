// @vitest-environment jsdom
// Test du parcours utilisateur : recherche -> résultats -> lecture -> suggestions.
// Le backend est simulé (fetch) : le test vérifie l'interface, pas le moteur.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "./App.jsx";
import { clearApiCache } from "./services/api.js";

const BOOKS = {
  2701: { id: 2701, title: "Moby Dick; Or, The Whale", author: "Herman Melville" },
  120: { id: 120, title: "Treasure Island", author: "Robert Louis Stevenson" },
};
const metadata = (id) => ({
  ...BOOKS[id], language: "en", word_count: 12000,
  file_path: `data/processed/${id}.txt`, source_url: "",
});

// Réponses du faux backend, par chemin + paramètres utiles.
function respond(url) {
  const { pathname, searchParams } = new URL(url, "http://test");
  const ok = (body) => ({ status: 200, body });

  if (pathname === "/api/health") {
    return ok({ status: "ok", books_loaded: 2, data_source: "corpus",
      modules: { search: "real", regex: "real", ranking: "real", recommendations: "real" } });
  }
  if (pathname === "/api/search") {
    const q = searchParams.get("q");
    const found = q === "whale";
    return ok({
      query: q, mode: "simple", total: found ? 1 : 0, limit: 10, offset: 0,
      results: found ? [{ ...BOOKS[2701], occurrences: 8, pagerank: 0.0887, score: 0.96 }] : [],
      suggestions: found ? [{ ...BOOKS[120], similarity: 0.36 }] : [],
      title_matches: q === "melville" ? [{ ...BOOKS[2701] }] : [],
    });
  }
  if (pathname === "/api/search/advanced") {
    return { status: 400, body: { detail: "Expression régulière invalide : parenthèse non fermée" } };
  }
  const match = pathname.match(/^\/api\/books\/(\d+)(\/text|\/similar)?$/);
  if (match && BOOKS[match[1]]) {
    const id = Number(match[1]);
    if (match[2] === "/text") {
      return ok({ id, title: BOOKS[id].title, page: 1, page_size: 4000, total_pages: 1,
        text: id === 2701 ? "The white whale rises from the sea." : "A map in a dead sailor's chest." });
    }
    if (match[2] === "/similar") {
      return ok({ book_id: id, suggestions: id === 2701 ? [{ ...BOOKS[120], similarity: 0.36 }] : [] });
    }
    return ok(metadata(id));
  }
  return { status: 404, body: { detail: "Introuvable." } };
}

beforeEach(() => {
  clearApiCache();
  vi.stubGlobal("fetch", vi.fn(async (url) => {
    const { status, body } = respond(url);
    return { ok: status < 400, status, json: async () => body };
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const renderAt = (path) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  );

describe("parcours utilisateur", () => {
  it("recherche, lit un livre puis suit une suggestion", async () => {
    const user = userEvent.setup();
    renderAt("/");

    // 1. Recherche par mot-clé depuis l'accueil
    await user.type(screen.getByRole("searchbox"), "whale");
    await user.click(screen.getByRole("button", { name: "Rechercher" }));

    // 2. Résultats classés + suggestions
    const result = await screen.findByRole("link", { name: "Moby Dick; Or, The Whale" });
    expect(screen.getByText("0.96")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Vous aimerez peut-être" })).toBeTruthy();

    // 3. Ouverture du livre et lecture du texte
    await user.click(result);
    expect(await screen.findByText("The white whale rises from the sea.")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1, name: "Moby Dick; Or, The Whale" })).toBeTruthy();

    // 4. Livres similaires, puis navigation vers une suggestion
    await screen.findByRole("heading", { name: "Livres similaires" });
    await user.click(screen.getByRole("link", { name: "Treasure Island" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Treasure Island" })).toBeTruthy();
    expect(await screen.findByText("A map in a dead sailor's chest.")).toBeTruthy();
  });

  it("propose les livres trouvés par titre ou auteur", async () => {
    const user = userEvent.setup();
    renderAt("/search?q=melville");
    expect(await screen.findByRole("heading", { name: "Par titre ou auteur" })).toBeTruthy();
    expect(screen.getByText("Aucun livre ne contient ces mots dans son texte.")).toBeTruthy();
    await user.click(screen.getByRole("link", { name: "Moby Dick; Or, The Whale" }));
    expect(await screen.findByText("The white whale rises from the sea.")).toBeTruthy();
  });

  it("affiche un message quand aucun livre ne correspond", async () => {
    renderAt("/search?q=zzzz");
    expect(await screen.findByText("Aucun livre ne correspond.")).toBeTruthy();
  });

  it("affiche l'erreur du backend pour une RegEx invalide", async () => {
    renderAt("/advanced?regex=(bad");
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Expression régulière invalide");
  });

  it("refuse une recherche vide sans appeler le backend de recherche", async () => {
    const user = userEvent.setup();
    renderAt("/");
    await user.click(screen.getByRole("button", { name: "Rechercher" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Saisissez");
    expect(fetch.mock.calls.every(([url]) => !String(url).includes("/api/search"))).toBe(true);
  });

  it("affiche une page d'erreur pour un livre inconnu", async () => {
    renderAt("/books/999");
    expect((await screen.findByRole("alert")).textContent).toContain("Introuvable.");
  });
});
