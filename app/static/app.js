import { api, ApiError } from "./api.js";
import {
  badge,
  element,
  emptyState,
  errorSummary,
  page,
  pendingAction,
  status,
} from "./render.js";
import { createRouter } from "./router.js";
import {
  tournamentCatalogView,
  tournamentOverviewView,
} from "./tournaments.js";
import { playerDirectoryView } from "./players.js";

const view = document.querySelector("#app-view");
const connectionStatus = document.querySelector("#app-connection-status");

function overviewView() {
  const root = page({
    eyebrow: "Operator workspace",
    title: "Fla Chess",
    description:
      "Manage local tournaments from draft creation through final standings.",
  });

  const cards = element("div", { className: "overview-grid" });
  const foundation = element("article", { className: "card feature-card" });
  foundation.append(
    badge("Foundation ready", "success"),
    element("h2", { text: "Workspace connected" }),
    element("p", {
      text: "Navigation, API requests, loading states, and backend errors share one application shell.",
    }),
  );

  const next = element("article", { className: "card" });
  next.append(
    badge("Operator workflow", "accent"),
    element("h2", { text: "Tournament catalog" }),
    element("p", {
      text: "Review tournaments, create a draft, and open its editable overview.",
    }),
    element("a", {
      className: "button button-secondary",
      text: "Open tournaments",
      attributes: { href: "#/tournaments" },
    }),
  );

  cards.append(foundation, next);
  root.append(cards);
  return { title: "Overview", element: root };
}

function systemView() {
  const checkButton = element("button", {
    className: "button button-secondary",
    text: "Check again",
    attributes: { type: "button" },
  });
  const root = page({
    eyebrow: "Connection",
    title: "System",
    description:
      "Verify the frontend can use the API without requiring a database connection.",
    actions: [checkButton],
  });

  const healthCard = element("section", { className: "card" });
  healthCard.append(
    element("h2", { text: "API health" }),
    element("p", {
      className: "muted",
      text: "This check calls /api/health, which is independent of PostgreSQL.",
    }),
  );
  const healthResult = element("div", { className: "result-slot" });
  healthCard.append(healthResult);

  const errorButton = element("button", {
    className: "button button-secondary",
    text: "Test 404 handling",
    attributes: { type: "button" },
  });
  const errorCard = element("section", { className: "card" });
  errorCard.append(
    element("h2", { text: "Backend error handling" }),
    element("p", {
      className: "muted",
      text: "This safe smoke action requests a missing API path and displays the normalized error.",
    }),
    errorButton,
  );
  const errorResult = element("div", { className: "result-slot" });
  errorCard.append(errorResult);
  root.append(healthCard, errorCard);

  async function checkHealth(signal) {
    healthResult.replaceChildren(status("Checking API health\u2026"));
    connectionStatus.textContent = "Checking";
    try {
      const response = await api.get("/api/health", { signal });
      if (response?.status !== "ok") {
        throw new ApiError("The health response was not recognized.", {
          kind: "unexpected-response",
          detail: response,
        });
      }
      healthResult.replaceChildren(status("API is healthy.", "success"));
      connectionStatus.textContent = "API healthy";
    } catch (error) {
      if (signal?.aborted || error?.name === "AbortError") {
        return;
      }
      healthResult.replaceChildren(status(errorSummary(error), "error"));
      connectionStatus.textContent = "API unavailable";
    }
  }

  async function testErrorHandling(signal) {
    errorResult.replaceChildren(status("Requesting a missing API resource\u2026"));
    try {
      await api.get("/api/frontend-smoke/missing", { signal });
      errorResult.replaceChildren(
        status("The missing resource unexpectedly succeeded.", "warning"),
      );
    } catch (error) {
      if (signal?.aborted || error?.name === "AbortError") {
        return;
      }
      const tone = error instanceof ApiError && error.status === 404 ? "success" : "error";
      errorResult.replaceChildren(status(errorSummary(error), tone));
    }
  }

  return {
    title: "System",
    element: root,
    activate({ signal }) {
      checkButton.addEventListener(
        "click",
        () => void pendingAction(checkButton, () => checkHealth(signal)),
        { signal },
      );
      errorButton.addEventListener(
        "click",
        () => void pendingAction(errorButton, () => testErrorHandling(signal)),
        { signal },
      );
      void checkHealth(signal);
    },
  };
}

function notFoundView() {
  const root = page({
    eyebrow: "Page not found",
    title: "That screen does not exist",
    description: "Choose one of the available workspace views.",
  });
  root.append(
    emptyState(
      "Unknown route",
      "The address may be incomplete or belong to a later frontend slice.",
    ),
  );
  return { title: "Not found", element: root };
}

const router = createRouter({
  routes: new Map([
    ["/", overviewView],
    ["/tournaments", () => tournamentCatalogView(router.navigate)],
    [
      "/tournaments/:id",
      ({ params }) =>
        tournamentOverviewView({ tournamentId: params.id }),
    ],
    ["/players", playerDirectoryView],
    ["/system", systemView],
  ]),
  notFound: notFoundView,
  mount(element) {
    view.replaceChildren(element);
    document.querySelector("#page-title")?.focus({ preventScroll: true });
  },
  onLoading() {
    view.replaceChildren(
      element("section", {
        className: "loading-state",
        text: "Loading the application\u2026",
      }),
    );
  },
  onError(error) {
    view.replaceChildren(status(errorSummary(error), "error"));
  },
  onNavigate(path) {
    for (const link of document.querySelectorAll("[data-route-link]")) {
      const route = link.dataset.routeLink;
      const active =
        path === route || (route !== "/" && path.startsWith(`${route}/`));
      link.classList.toggle("active", active);
      if (active) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    }
  },
});

router.start();
