import { api } from "./api.js";
import {
  badge,
  element,
  emptyState,
  errorSummary,
  page,
  pendingAction,
  status,
  table,
} from "./render.js";
import { standingsTable } from "./standings.js";

function labelFor(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function currentPhase(workspace) {
  const phases = [...workspace.phases];
  return (
    phases
      .reverse()
      .find((phase) =>
        phase.sections.some((section) => section.lifecycle === "active"),
      ) ??
    phases.find((phase) =>
      phase.sections.some((section) => section.lifecycle !== "finished"),
    ) ??
    phases[0]
  );
}

function latestRound(operation) {
  return operation.rounds.at(-1);
}

function resultLabel(game) {
  if (game.white_score === null || game.black_score === null) {
    return "Awaiting result";
  }
  return `${Number(game.white_score)} - ${Number(game.black_score)}`;
}

function gameTable(games, caption) {
  return table({
    caption,
    columns: [
      { key: "white_player_name", label: "White" },
      {
        key: "result",
        label: "Result",
        render: (result, game) => element("strong", { text: resultLabel(game) }),
      },
      { key: "black_player_name", label: "Black" },
    ],
    rows: games,
    emptyMessage: "No games in this group.",
  });
}

function participationSummary(round) {
  if (!round?.records.length) {
    return null;
  }
  const summary = element("p", { className: "display-participation muted" });
  summary.textContent = round.records
    .map((record) => {
      const score =
        record.score_awarded === null
          ? ""
          : `, ${Number(record.score_awarded)} point${
              Number(record.score_awarded) === 1 ? "" : "s"
            }`;
      return `${record.player_name}: ${labelFor(record.participation_type)}${score}`;
    })
    .join(" · ");
  return summary;
}

function sectionDisplay(operation, standings) {
  const round = latestRound(operation);
  const section = element("article", {
    className: "card display-section",
  });
  section.append(
    badge(
      labelFor(operation.lifecycle),
      operation.lifecycle === "active" ? "success" : "neutral",
    ),
    element("h2", { text: operation.name }),
  );
  if (!round) {
    section.append(
      emptyState(
        "No rounds yet",
        "Pairings will appear after the first round is created.",
      ),
    );
    return section;
  }

  section.append(
    element("div", { className: "display-section-heading" }),
  );
  section.lastElementChild.append(
    element("h3", { text: `Round ${round.number}` }),
    element("span", {
      className: "muted",
      text: `${round.games.length} game${round.games.length === 1 ? "" : "s"}`,
    }),
  );

  const upcoming = round.games.filter((game) => game.white_score === null);
  const completed = round.games.filter((game) => game.white_score !== null);
  const games = element("div", { className: "display-games-grid" });
  const upcomingCard = element("section", { className: "display-game-group" });
  upcomingCard.append(
    element("h4", { text: `Upcoming games (${upcoming.length})` }),
    gameTable(upcoming, `${operation.name} upcoming games`),
  );
  const resultsCard = element("section", { className: "display-game-group" });
  resultsCard.append(
    element("h4", { text: `Results (${completed.length})` }),
    gameTable(completed, `${operation.name} completed results`),
  );
  games.append(upcomingCard, resultsCard);
  section.append(games);
  const participation = participationSummary(round);
  if (participation) {
    section.append(participation);
  }

  const standingsHeading = element("h3", {
    className: "display-standings-heading",
    text: `Standings through round ${round.number}`,
  });
  section.append(standingsHeading);
  if (standings.length) {
    section.append(standingsTable(operation, standings, round));
  } else {
    section.append(
      status("Standings have not been published for this round yet.", "warning"),
    );
  }
  return section;
}

function phaseSummary(workspace, phase) {
  const activeSections = phase.sections.filter(
    (section) => section.lifecycle === "active",
  ).length;
  const unfinishedSections = phase.sections.filter(
    (section) => section.lifecycle !== "finished",
  ).length;
  const state = activeSections
    ? "Current phase"
    : unfinishedSections
      ? "Upcoming phase"
      : "Completed phase";
  const summary = element("section", { className: "card display-summary" });
  summary.append(
    badge(state, activeSections ? "success" : "neutral"),
    element("h2", {
      text: `Phase ${phase.sequence} · ${labelFor(phase.format)}`,
    }),
    element("p", {
      className: "display-summary-copy",
      text: `${phase.sections.length} section${
        phase.sections.length === 1 ? "" : "s"
      } · ${workspace.participants.length} tournament players`,
    }),
  );
  return summary;
}

export function tournamentDisplayView({ tournamentId }) {
  const refresh = element("button", {
    className: "button button-secondary",
    text: "Refresh display",
    attributes: { type: "button" },
  });
  const root = page({
    eyebrow: "Player display",
    title: "Tournament",
    description:
      "Current phase, upcoming games, recorded results, and the latest standings.",
    actions: [refresh],
  });
  const result = element("div", { className: "result-slot tournament-display" });
  const updated = element("p", { className: "display-updated muted" });
  root.append(updated, result);

  function render(workspace, operations, snapshots) {
    result.replaceChildren();
    const phase = currentPhase(workspace);
    if (!phase) {
      result.append(
        emptyState(
          "Tournament structure not ready",
          "No phases have been configured yet.",
        ),
      );
      return;
    }
    root.querySelector("#page-title").textContent = workspace.name;
    result.append(phaseSummary(workspace, phase));

    const sectionIds = new Set(phase.sections.map((section) => section.id));
    const currentOperations = operations.filter((operation) =>
      sectionIds.has(operation.id),
    );
    if (!currentOperations.length) {
      result.append(
        emptyState(
          "No sections",
          "Sections will appear when the phase is configured.",
        ),
      );
      return;
    }
    const sections = element("div", { className: "display-section-list" });
    sections.append(
      ...currentOperations.map((operation) =>
        sectionDisplay(operation, snapshots.get(operation.id) ?? []),
      ),
    );
    result.append(sections);
  }

  async function load(signal) {
    result.replaceChildren(status("Loading tournament display\u2026"));
    updated.textContent = "";
    try {
      const workspace = await api.get(
        `/api/tournaments/${tournamentId}/workspace`,
        { signal },
      );
      const phase = currentPhase(workspace);
      const sections = phase?.sections ?? [];
      const operations = await Promise.all(
        sections.map((section) =>
          api.get(`/api/tournament-sections/${section.id}/operation`, {
            signal,
          }),
        ),
      );
      const snapshots = new Map(
        await Promise.all(
          operations.map(async (operation) => {
            const round = latestRound(operation);
            if (!round) {
              return [operation.id, []];
            }
            const standings = await api.get(
              `/api/tournament-sections/${operation.id}/standings?through_round_id=${round.id}`,
              { signal },
            );
            return [operation.id, standings];
          }),
        ),
      );
      render(workspace, operations, snapshots);
      updated.textContent = `Updated ${new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date())}`;
    } catch (error) {
      if (signal.aborted || error?.name === "AbortError") {
        return;
      }
      result.replaceChildren(status(errorSummary(error), "error"));
    }
  }

  return {
    title: "Player tournament display",
    element: root,
    activate({ signal }) {
      refresh.addEventListener(
        "click",
        () => void pendingAction(refresh, () => load(signal)),
        { signal },
      );
      void load(signal);
    },
  };
}
