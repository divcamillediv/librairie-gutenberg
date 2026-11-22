// Messages d'état : chargement, erreur, résultat vide.
export function Loading({ label = "Chargement…" }) {
  return <p className="status" role="status">{label}</p>;
}

export function ErrorMessage({ error }) {
  const hint =
    error?.status === 0
      ? "Le backend ne répond pas."
      : error?.status >= 500
        ? "Erreur interne du serveur."
        : null;
  return (
    <div className="status status-error" role="alert">
      <strong>{hint ?? "La requête n'a pas abouti."}</strong>
      <span>{error?.message}</span>
    </div>
  );
}

export function Empty({ title, children }) {
  return (
    <div className="status status-empty">
      <strong>{title}</strong>
      {children && <span>{children}</span>}
    </div>
  );
}
