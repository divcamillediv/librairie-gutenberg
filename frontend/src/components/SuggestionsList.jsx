import { Link } from "react-router-dom";

// Livres voisins dans le graphe de Jaccard (suggestions implicites).
export default function SuggestionsList({ title = "Livres similaires", items }) {
  if (!items?.length) return null;
  return (
    <aside className="suggestions" aria-label={title}>
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <Link to={`/books/${item.id}`}>{item.title}</Link>
            {item.author && <span className="muted">{item.author}</span>}
            <span className="similarity">Similarité {Math.round(item.similarity * 100)} %</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
