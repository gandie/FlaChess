export function createRouter({
  routes,
  notFound,
  mount,
  onLoading,
  onError,
  onNavigate,
}) {
  let activeController = null;
  let generation = 0;

  function routeFor(path) {
    for (const [pattern, load] of routes) {
      const keys = [];
      const expression = pattern.replace(
        /:([A-Za-z][A-Za-z0-9_]*)/g,
        (_, key) => {
          keys.push(key);
          return "([^/]+)";
        },
      );
      const match = path.match(new RegExp(`^${expression}$`));
      if (match) {
        return {
          load,
          params: Object.fromEntries(
            keys.map((key, index) => [key, match[index + 1]]),
          ),
        };
      }
    }
    return { load: notFound, params: {} };
  }

  function currentPath() {
    const hash = window.location.hash.replace(/^#/, "");
    return hash || "/";
  }

  async function render(path) {
    activeController?.abort();
    activeController = new AbortController();
    const currentGeneration = ++generation;
    const signal = activeController.signal;
    const { load, params } = routeFor(path);

    onNavigate?.(path);
    onLoading?.();

    try {
      const view = await load({ path, params, signal });
      if (signal.aborted || currentGeneration !== generation) {
        return;
      }

      mount(view.element);
      document.title = `${view.title} | Fla Chess`;
      await view.activate?.({ signal });
    } catch (error) {
      if (signal.aborted || error?.name === "AbortError") {
        return;
      }
      if (currentGeneration === generation) {
        onError(error);
      }
    }
  }

  function handleNavigation() {
    void render(currentPath());
  }

  return {
    start() {
      window.addEventListener("hashchange", handleNavigation);
      handleNavigation();
    },
    navigate(path) {
      window.location.hash = path;
    },
  };
}
