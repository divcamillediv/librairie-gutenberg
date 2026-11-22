// Pagination précédente / suivante, pilotée par l'URL (paramètre `page`).
export default function Pagination({ page, totalPages, onChange, label = "Pagination" }) {
  if (totalPages <= 1) return null;
  return (
    <nav className="pagination" aria-label={label}>
      <button type="button" onClick={() => onChange(page - 1)} disabled={page <= 1}>
        ← Précédent
      </button>
      <span>Page {page} / {totalPages}</span>
      <button type="button" onClick={() => onChange(page + 1)} disabled={page >= totalPages}>
        Suivant →
      </button>
    </nav>
  );
}
