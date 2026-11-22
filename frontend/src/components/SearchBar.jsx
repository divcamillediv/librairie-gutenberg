import { useEffect, useState } from "react";

// Champ de recherche réutilisé pour le mot-clé et pour la RegEx.
export default function SearchBar({
  initialValue = "",
  onSearch,
  label,
  placeholder,
  buttonLabel = "Rechercher",
  monospace = false,
  maxLength = 200,
  autoFocus = false,
}) {
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState("");

  // Resynchronise le champ quand l'URL change (bouton retour du navigateur).
  useEffect(() => setValue(initialValue), [initialValue]);

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) {
      setError("Saisissez au moins un caractère.");
      return;
    }
    setError("");
    onSearch(trimmed);
  }

  return (
    <form className="searchbar" onSubmit={handleSubmit} role="search" noValidate>
      <label className="visually-hidden" htmlFor="search-input">{label}</label>
      <div className="searchbar-row">
        <input
          id="search-input"
          type="search"
          className={monospace ? "mono" : undefined}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          maxLength={maxLength}
          autoFocus={autoFocus}
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          aria-invalid={Boolean(error)}
        />
        <button type="submit">{buttonLabel}</button>
      </div>
      {error && <p className="field-error" role="alert">{error}</p>}
    </form>
  );
}
