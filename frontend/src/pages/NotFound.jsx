import { Link } from "react-router-dom";
import { Empty } from "../components/StatusMessage.jsx";

export default function NotFound() {
  return (
    <Empty title="Cette page n'existe pas.">
      <Link to="/">Revenir à la recherche</Link>
    </Empty>
  );
}
