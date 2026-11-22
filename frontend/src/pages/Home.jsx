import { Link, useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar.jsx";

const EXAMPLES = ["whale", "ship", "marriage", "castle", "treasure"];

export default function Home() {
  const navigate = useNavigate();
  const go = (query) => navigate(`/search?q=${encodeURIComponent(query)}`);

  return (
    <section className="hero">
      <h1>Cherchez dans le texte de toute la bibliothèque</h1>
      <p className="lead">
        Un mot-clé suffit : les livres qui le contiennent sont classés par pertinence,
        et des lectures voisines vous sont suggérées.
      </p>
      <SearchBar
        onSearch={go}
        label="Mot-clé"
        placeholder="Un mot présent dans les livres, par ex. whale"
        autoFocus
      />
      <p className="examples">
        Essayer :{" "}
        {EXAMPLES.map((word) => (
          <button key={word} type="button" className="chip" onClick={() => go(word)}>{word}</button>
        ))}
      </p>
      <p className="muted">
        Besoin d'un motif plus précis ? Utilisez la <Link to="/advanced">recherche avancée par RegEx</Link>{" "}
        ou parcourez le <Link to="/books">catalogue</Link>.
      </p>
    </section>
  );
}
