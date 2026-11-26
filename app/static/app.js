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
import { sectionOperationView } from "./operations.js";
import { tournamentDisplayView } from "./display.js";

const view = document.querySelector("#app-view");
const connectionStatus = document.querySelector("#app-connection-status");

function overviewView() {
  const root = page({
    eyebrow: "Tournament control",
    title: "The room is live.",
    description:
      "Set the board, run the round, record the result. Every tournament control stays one move away.",
  });
  root.classList.add("overview-page");

  const commandDeck = element("section", {
    className: "command-deck",
    attributes: { "aria-label": "Tournament command desk" },
  });
  const signal = element("div", { className: "command-signal" });
  signal.append(
    element("span", {
      className: "command-signal-label",
      text: "Operator status",
    }),
    element("strong", {
      className: "command-signal-value",
      text: "Checking the floor",
    }),
  );
  const commandCopy = element("div", { className: "command-copy" });
  commandCopy.append(
    badge("Tournament desk", "clock"),
    element("h2", { text: "Bring today’s tournament into focus." }),
    element("p", {
      className: "command-description",
      text: "Open an active event, or start with the tournament catalog and build the next one.",
    }),
  );
  const commandActions = element("div", { className: "command-actions" });
  commandCopy.append(commandActions);
  commandDeck.append(signal, commandCopy);

  const launchGrid = element("div", { className: "launch-grid" });
  const tournamentLaunch = element("article", { className: "launch-card" });
  tournamentLaunch.append(
    element("span", { className: "launch-number", text: "01" }),
    element("h2", { text: "Tournament catalog" }),
    element("p", {
      text: "Create drafts, continue live events, and close finished tournaments.",
    }),
    element("a", {
      className: "text-link",
      text: "Open tournaments →",
      attributes: { href: "#/tournaments" },
    }),
  );

  const playerLaunch = element("article", { className: "launch-card" });
  playerLaunch.append(
    element("span", { className: "launch-number", text: "02" }),
    element("h2", { text: "Player registry" }),
    element("p", {
      text: "Keep names ready before registration opens and the room gets busy.",
    }),
    element("a", {
      className: "text-link",
      text: "Manage players →",
      attributes: { href: "#/players" },
    }),
  );

  const displayLaunch = element("article", { className: "launch-card" });
  displayLaunch.append(
    element("span", { className: "launch-number", text: "03" }),
    element("h2", { text: "Public boards" }),
    element("p", {
      text: "Open any tournament display for pairings, live results, and standings.",
    }),
    element("a", {
      className: "text-link",
      text: "Choose a tournament →",
      attributes: { href: "#/tournaments" },
    }),
  );

  launchGrid.append(tournamentLaunch, playerLaunch, displayLaunch);
  root.append(commandDeck, launchGrid);

  async function loadCommandDeck(signal) {
    try {
      const tournaments = await api.get("/api/tournament-summaries", { signal });
      const active = tournaments.filter(
        (tournament) => tournament.lifecycle === "active",
      );
      const drafts = tournaments.filter(
        (tournament) => tournament.lifecycle === "draft",
      );
      const current = active[0] ?? drafts[0] ?? tournaments[0];
      const label = signal?.aborted ? "" : active.length ? `${active.length} live` : "Ready";
      if (signal?.aborted) {
        return;
      }
      signalStatus(label);
      if (!current) {
        commandCopy.querySelector("h2").textContent = "Your next event starts here.";
        commandCopy.querySelector(".command-description").textContent =
          "Create the first tournament, add players, and set the opening round.";
      } else {
        const state = current.lifecycle === "active" ? "Live now" : "On the desk";
        commandCopy.querySelector("h2").textContent = `${current.name} · ${state}`;
        commandCopy.querySelector(".command-description").textContent =
          `${current.participant_count} players · ${current.phase_count} phase${
            current.phase_count === 1 ? "" : "s"
          } · ${current.section_count} section${
            current.section_count === 1 ? "" : "s"
          }`;
      }
      const open = element("a", {
        className: "button",
        text: current ? "Open tournament" : "Create tournament",
        attributes: {
          href: current ? `#/tournaments/${current.id}` : "#/tournaments",
        },
      });
      commandActions.replaceChildren(open);
      if (current) {
        commandActions.append(
          element("a", {
            className: "button button-light",
            text: "Open player display",
            attributes: {
              href: `#/display/tournaments/${current.id}`,
              target: "_blank",
              rel: "noopener noreferrer",
            },
          }),
        );
      }
    } catch (error) {
      if (signal?.aborted || error?.name === "AbortError") {
        return;
      }
      signalStatus("Offline");
      commandCopy.querySelector(".command-description").textContent =
        errorSummary(error);
      commandActions.replaceChildren(
        element("a", {
          className: "button",
          text: "Check system",
          attributes: { href: "#/system" },
        }),
      );
    }
  }

  function signalStatus(value) {
    signal.querySelector(".command-signal-value").textContent = value;
    commandDeck.dataset.state = value === "Offline" ? "offline" : "ready";
  }

  return {
    title: "Overview",
    element: root,
    activate({ signal }) {
      void loadCommandDeck(signal);
    },
  };
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
    [
      "/display/tournaments/:id",
      ({ params }) => tournamentDisplayView({ tournamentId: params.id }),
    ],
    [
      "/tournaments/:tournamentId/sections/:sectionId",
      ({ params }) =>
        sectionOperationView({
          tournamentId: params.tournamentId,
          sectionId: params.sectionId,
        }),
    ],
    [
      "/tournaments/:tournamentId/sections/:sectionId/rounds/:roundId",
      ({ params }) =>
        sectionOperationView({
          tournamentId: params.tournamentId,
          sectionId: params.sectionId,
          roundId: params.roundId,
        }),
    ],
    ["/players", playerDirectoryView],
    ["/system", systemView],
  ]),
  notFound: notFoundView,
  mount(element) {
    view.replaceChildren(element);
    document.querySelector("#page-title")?.focus();
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
