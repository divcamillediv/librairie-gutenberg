import { Link } from "react-router-dom";

// Un résultat classé : rang, titre, auteur et détail du score (classement visible).
export default function BookCard({ rank, result }) {
  const percent = Math.round(result.score * 100);
  return (
    <li className="result">
      <span className="result-rank" aria-label={`Rang ${rank}`}>{rank}</span>
      <div className="result-body">
        <h3><Link to={`/books/${result.id}`}>{result.title}</Link></h3>
        <p className="muted">{result.author || "Auteur inconnu"}</p>
        <dl className="metrics">
          <div><dt>Occurrences</dt><dd>{result.occurrences}</dd></div>
          <div><dt>PageRank</dt><dd>{result.pagerank.toFixed(4)}</dd></div>
          <div className="metric-score">
            <dt>Score</dt>
            <dd>
              <span className="scorebar" aria-hidden="true"><span style={{ width: `${percent}%` }} /></span>
              {result.score.toFixed(2)}
            </dd>
          </div>
        </dl>
      </div>
    </li>
  );
}
