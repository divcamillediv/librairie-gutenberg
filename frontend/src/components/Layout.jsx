import { Link, NavLink, Outlet } from "react-router-dom";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";

// Bandeau affiché tant qu'une partie des réponses vient du moteur simulé.
function DataBanner() {
  const { data } = useApi((options) => api.health(options), []);
  if (!data) return null;
  const mocked = Object.values(data.modules).some((status) => status === "mock");
  const sample = data.data_source === "sample";
  if (!sample && !mocked) return null;
  return (
    <p className="banner" role="status">
      Mode démonstration : {data.books_loaded} livres{sample ? " simulés" : ""}
      {mocked ? ", recherche et classement simulés" : ""}.
    </p>
  );
}

export default function Layout() {
  return (
    <div className="app">
      <header className="header">
        <Link to="/" className="brand">
          <span className="brand-mark" aria-hidden="true">G</span>
          Bibliothèque Gutenberg
        </Link>
        <nav className="nav" aria-label="Navigation principale">
          <NavLink to="/" end>Recherche</NavLink>
          <NavLink to="/advanced">RegEx</NavLink>
          <NavLink to="/books">Catalogue</NavLink>
        </nav>
      </header>
      <DataBanner />
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">
        DAAR Projet 2 — textes issus du <a href="https://www.gutenberg.org/">projet Gutenberg</a>
      </footer>
    </div>
  );
}
