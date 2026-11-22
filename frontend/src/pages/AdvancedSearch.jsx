import { useSearchParams } from "react-router-dom";
import ResultsList from "../components/ResultsList.jsx";
import SearchBar from "../components/SearchBar.jsx";

const EXAMPLES = [
  { pattern: "whal(e|es|ing)", note: "whale, whales, whaling" },
  { pattern: "sea.*", note: "mots commençant par sea" },
  { pattern: ".*ship", note: "mots finissant par ship" },
  { pattern: "[a-z]{12,}", note: "mots d'au moins 12 lettres" },
];

// Recherche avancée : la RegEx est comparée aux mots de l'index, pas au texte brut.
export default function AdvancedSearch() {
  const [params, setParams] = useSearchParams();
  const regex = (params.get("regex") ?? "").trim();
  const page = Math.max(1, Number.parseInt(params.get("page") ?? "1", 10) || 1);

  return (
    <>
      <h1>Recherche avancée</h1>
      <p className="lead">
        Saisissez une expression régulière. Un livre est retenu si l'un des mots de son
        index vérifie le motif en entier.
      </p>
      <SearchBar
        initialValue={regex}
        onSearch={(value) => setParams({ regex: value })}
        label="Expression régulière"
        placeholder="whal(e|es|ing)"
        buttonLabel="Rechercher"
        monospace
        maxLength={100}
        autoFocus={!regex}
      />
      {regex ? (
        <ResultsList
          mode="regex"
          query={regex}
          page={page}
          onPageChange={(next) => setParams({ regex, page: String(next) })}
        />
      ) : (
        <section className="help">
          <h2>Exemples</h2>
          <ul className="examples-list">
            {EXAMPLES.map(({ pattern, note }) => (
              <li key={pattern}>
                <button type="button" className="chip mono" onClick={() => setParams({ regex: pattern })}>
                  {pattern}
                </button>
                <span className="muted">{note}</span>
              </li>
            ))}
          </ul>
          <p className="muted">
            Limites : le motif porte sur un mot à la fois (pas de phrase ni d'espace), il est
            insensible à la casse car l'index est en minuscules, et il est limité à 100 caractères.
          </p>
        </section>
      )}
    </>
  );
}
