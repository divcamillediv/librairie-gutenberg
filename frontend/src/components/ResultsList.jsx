import { Link } from "react-router-dom";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";
import Pagination from "./Pagination.jsx";
import BookCard from "./BookCard.jsx";
import SuggestionsList from "./SuggestionsList.jsx";
import { Empty, ErrorMessage, Loading } from "./StatusMessage.jsx";

export const PAGE_SIZE = 10;

// Livres dont le titre ou l'auteur correspond à la requête (métadonnées de la base).
function TitleMatches({ items }) {
  if (!items?.length) return null;
  return (
    <section className="title-matches" aria-label="Titres et auteurs correspondants">
      <h2>Par titre ou auteur</h2>
      <ul>
        {items.map((book) => (
          <li key={book.id}>
            <Link to={`/books/${book.id}`}>{book.title}</Link>
            {book.author && <span className="muted">{book.author}</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}

// Liste de résultats classés + suggestions, commune aux deux modes de recherche.
export default function ResultsList({ mode, query, page, onPageChange }) {
  const offset = (page - 1) * PAGE_SIZE;
  const { data, error, loading } = useApi(
    (options) =>
      mode === "regex"
        ? api.advancedSearch(query, { limit: PAGE_SIZE, offset }, options)
        : api.search(query, { limit: PAGE_SIZE, offset }, options),
    [mode, query, page]
  );

  if (loading && !data) return <Loading label="Recherche en cours…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return null;

  const titleMatches = data.title_matches ?? [];

  if (data.total === 0) {
    if (titleMatches.length) {
      return (
        <>
          <TitleMatches items={titleMatches} />
          <Empty title="Aucun livre ne contient ces mots dans son texte." />
        </>
      );
    }
    return (
      <Empty title="Aucun livre ne correspond.">
        {mode === "regex"
          ? "La RegEx est comparée aux mots de l'index : essayez un motif plus large, par exemple whal.*"
          : "Vérifiez l'orthographe ou essayez un autre mot-clé (les textes sont en anglais)."}
      </Empty>
    );
  }

  const totalPages = Math.ceil(data.total / PAGE_SIZE);
  return (
    <div className={`results-layout${loading ? " is-loading" : ""}`}>
      <section aria-label="Résultats">
        <TitleMatches items={titleMatches} />
        <p className="results-count">
          {data.total} livre{data.total > 1 ? "s" : ""} pour <q className={mode === "regex" ? "mono" : undefined}>{data.query}</q>,
          dans le texte, classé{data.total > 1 ? "s" : ""} par pertinence
        </p>
        <ol className="results">
          {data.results.map((result, index) => (
            <BookCard key={result.id} rank={offset + index + 1} result={result} />
          ))}
        </ol>
        <Pagination page={page} totalPages={totalPages} onChange={onPageChange} label="Pages de résultats" />
      </section>
      <SuggestionsList title="Vous aimerez peut-être" items={data.suggestions} />
    </div>
  );
}
