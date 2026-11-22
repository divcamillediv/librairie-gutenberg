import { Link, useSearchParams } from "react-router-dom";
import Pagination from "../components/Pagination.jsx";
import { Empty, ErrorMessage, Loading } from "../components/StatusMessage.jsx";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";

const PAGE_SIZE = 20;

// Catalogue paginé de la bibliothèque, trié par titre.
export default function Library() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number.parseInt(params.get("page") ?? "1", 10) || 1);
  const { data, error, loading } = useApi(
    (options) => api.listBooks({ limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }, options),
    [page]
  );

  return (
    <>
      <h1>Catalogue</h1>
      {loading && !data && <Loading />}
      {error && <ErrorMessage error={error} />}
      {data && data.books.length === 0 && <Empty title="Aucun livre sur cette page." />}
      {data && data.books.length > 0 && (
        <>
          <p className="results-count">{data.total} livres dans la bibliothèque</p>
          <ul className="catalogue">
            {data.books.map((book) => (
              <li key={book.id}>
                <Link to={`/books/${book.id}`}>{book.title}</Link>
                <span className="muted">{book.author || "Auteur inconnu"}</span>
                <span className="muted count">{book.word_count.toLocaleString("fr-FR")} mots</span>
              </li>
            ))}
          </ul>
          <Pagination
            page={page}
            totalPages={Math.ceil(data.total / PAGE_SIZE)}
            onChange={(next) => setParams({ page: String(next) })}
            label="Pages du catalogue"
          />
        </>
      )}
    </>
  );
}
