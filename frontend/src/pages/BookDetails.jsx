import { useEffect, useRef } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import Pagination from "../components/Pagination.jsx";
import { ErrorMessage, Loading } from "../components/StatusMessage.jsx";
import SuggestionsList from "../components/SuggestionsList.jsx";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";

// Lecture paginée du texte intégral.
function Reader({ bookId, page, onPageChange }) {
  const { data, error, loading } = useApi(
    (options) => api.getBookText(bookId, { page }, options),
    [bookId, page]
  );
  const top = useRef(null);

  // Revenir en haut du texte à chaque changement de page.
  useEffect(() => {
    if (data && page > 1) top.current?.scrollIntoView({ block: "start" });
  }, [data, page]);

  if (loading && !data) return <Loading label="Chargement du texte…" />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return null;

  return (
    <section className={`reader${loading ? " is-loading" : ""}`} ref={top} aria-label="Texte du livre">
      <Pagination page={data.page} totalPages={data.total_pages} onChange={onPageChange} label="Pages du livre" />
      <article className="book-text">{data.text}</article>
      <Pagination page={data.page} totalPages={data.total_pages} onChange={onPageChange} label="Pages du livre (bas)" />
    </section>
  );
}

// Détail d'un livre : métadonnées, texte, livres similaires.
export default function BookDetails() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number.parseInt(params.get("page") ?? "1", 10) || 1);

  const book = useApi((options) => api.getBook(bookId, options), [bookId]);
  const similar = useApi((options) => api.getSimilar(bookId, options), [bookId]);

  if (book.loading && !book.data) return <Loading />;
  if (book.error) {
    return (
      <>
        <ErrorMessage error={book.error} />
        <button type="button" className="link-button" onClick={() => navigate(-1)}>← Retour</button>
      </>
    );
  }

  const { title, author, language, word_count: wordCount, source_url: sourceUrl } = book.data;
  return (
    <>
      <button type="button" className="link-button" onClick={() => navigate(-1)}>← Retour</button>
      <header className="book-header">
        <h1>{title}</h1>
        <p className="lead">{author || "Auteur inconnu"}</p>
        <p className="muted">
          {wordCount.toLocaleString("fr-FR")} mots · langue : {language}
          {sourceUrl && (
            <> · <a href={sourceUrl} target="_blank" rel="noreferrer">source Gutenberg</a></>
          )}
        </p>
      </header>
      <div className="results-layout">
        <Reader bookId={bookId} page={page} onPageChange={(next) => setParams({ page: String(next) })} />
        <SuggestionsList title="Livres similaires" items={similar.data?.suggestions} />
      </div>
    </>
  );
}
