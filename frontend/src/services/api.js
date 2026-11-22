// Client HTTP de l'API FastAPI (contrat : docs/api_contract.md).
//
// Par défaut les appels sont relatifs (/api/...) : le proxy Vite (développement)
// ou nginx (Docker) les relaie vers le backend. VITE_API_BASE_URL permet de
// viser un backend situé ailleurs.
const BASE_URL = (import.meta.env?.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status; // 0 = backend injoignable
  }
}

function buildUrl(path, params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  }
  const suffix = query.toString();
  return `${BASE_URL}${path}${suffix ? `?${suffix}` : ""}`;
}

// FastAPI renvoie {"detail": "message"} (nos erreurs) ou {"detail": [{msg}]} (validation 422).
function extractDetail(body, status) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) return detail.map((d) => d.msg).join(" ; ");
  return `Erreur ${status}`;
}

// Cache mémoire des réponses réussies : revenir sur une page de résultats, un
// livre ou une page de texte déjà vue s'affiche sans nouvel appel réseau.
// Les données du serveur ne changent pas en cours d'utilisation (calculées hors ligne).
const CACHE_MAX = 200;
const cache = new Map();

export function clearApiCache() {
  cache.clear();
}

export async function request(path, params, { signal, useCache = true } = {}) {
  const url = buildUrl(path, params);
  if (useCache && cache.has(url)) return cache.get(url);

  let response;
  try {
    response = await fetch(url, { signal });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError(0, "Le serveur est injoignable. Vérifiez que le backend est démarré.");
  }
  let body = null;
  try {
    body = await response.json();
  } catch {
    /* réponse sans JSON */
  }
  if (!response.ok) throw new ApiError(response.status, extractDetail(body, response.status));
  if (useCache) {
    if (cache.size >= CACHE_MAX) cache.delete(cache.keys().next().value); // plus ancienne entrée
    cache.set(url, body);
  }
  return body;
}

export const api = {
  health: (options) => request("/api/health", {}, { ...options, useCache: false }),
  listBooks: ({ limit = 20, offset = 0 } = {}, options) =>
    request("/api/books", { limit, offset }, options),
  getBook: (id, options) => request(`/api/books/${id}`, {}, options),
  getBookText: (id, { page = 1, pageSize } = {}, options) =>
    request(`/api/books/${id}/text`, { page, page_size: pageSize }, options),
  getSimilar: (id, options) => request(`/api/books/${id}/similar`, {}, options),
  search: (q, { limit = 10, offset = 0 } = {}, options) =>
    request("/api/search", { q, limit, offset }, options),
  advancedSearch: (regex, { limit = 10, offset = 0 } = {}, options) =>
    request("/api/search/advanced", { regex, limit, offset }, options),
};
