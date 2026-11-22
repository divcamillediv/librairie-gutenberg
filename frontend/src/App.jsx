import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";
import Results from "./pages/Results.jsx";
import AdvancedSearch from "./pages/AdvancedSearch.jsx";
import Library from "./pages/Library.jsx";
import BookDetails from "./pages/BookDetails.jsx";
import NotFound from "./pages/NotFound.jsx";

// Vues de l'application :
//   /            accueil + recherche par mot-clé
//   /search      résultats classés + suggestions
//   /advanced    recherche avancée par RegEx (formulaire + résultats)
//   /books       catalogue paginé
//   /books/:id   détail et lecture du texte intégral
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="search" element={<Results />} />
        <Route path="advanced" element={<AdvancedSearch />} />
        <Route path="books" element={<Library />} />
        <Route path="books/:bookId" element={<BookDetails />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
