export async function fetchJson(path, fallback = null) {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return await response.json();
  } catch (error) {
    return fallback ?? { status: "missing", path, reason: error.message };
  }
}

export function useAsyncResource(loader, deps, React) {
  const { useEffect, useState } = React;
  const [state, setState] = useState({ loading: true, data: null, error: null });
  useEffect(() => {
    let mounted = true;
    setState({ loading: true, data: null, error: null });
    loader()
      .then((data) => mounted && setState({ loading: false, data, error: null }))
      .catch((error) => mounted && setState({ loading: false, data: null, error }));
    return () => {
      mounted = false;
    };
  }, deps);
  return state;
}
