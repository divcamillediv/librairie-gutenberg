import { useEffect, useState } from "react";

// Lance un appel API à chaque changement de `deps` et expose son état.
// `fetcher` reçoit {signal} pour annuler la requête si la vue change entre-temps.
export function useApi(fetcher, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    const controller = new AbortController();
    setState((previous) => ({ ...previous, error: null, loading: true }));
    fetcher({ signal: controller.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== "AbortError") setState({ data: null, error, loading: false });
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
