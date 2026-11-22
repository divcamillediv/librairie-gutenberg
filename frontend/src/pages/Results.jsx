import { Link, useSearchParams } from "react-router-dom";
import ResultsList from "../components/ResultsList.jsx";
import SearchBar from "../components/SearchBar.jsx";
import { Empty } from "../components/StatusMessage.jsx";

// Résultats de la recherche par mot-clé. L'état (requête, page) vit dans l'URL :
// la page est partageable et le bouton retour fonctionne.
export default function Results() {
  const [params, setParams] = useSearchParams();
  const query = (params.get("q") ?? "").trim();
  const page = Math.max(1, Number.parseInt(params.get("page") ?? "1", 10) || 1);

  return (
    <>
      <SearchBar
        initialValue={query}
        onSearch={(q) => setParams({ q })}
        label="Mot-clé"
        placeholder="Mot-clé"
      />
      <p className="muted switch-mode">
        <Link to="/advanced">Passer à la recherche avancée (RegEx)</Link>
      </p>
      {query ? (
        <ResultsList
          mode="simple"
          query={query}
          page={page}
          onPageChange={(next) => setParams({ q: query, page: String(next) })}
        />
      ) : (
        <Empty title="Saisissez un mot-clé pour lancer la recherche." />
      )}
    </>
  );
}
