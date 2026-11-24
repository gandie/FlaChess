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
  if (workspace.lifecycle === "finished") {
    return phases.at(-1);
  }
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

function selectedSnapshotKey(sectionId, roundId) {
  return `${sectionId}:${roundId}`;
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

function roundSelector(operation, selectedRound, onSelect, signal) {
  if (operation.rounds.length < 2) {
    return null;
  }
  const navigation = element("nav", {
    className: "display-round-selector",
    attributes: { "aria-label": `${operation.name} round history` },
  });
  navigation.append(
    element("span", { className: "display-round-label", text: "Round history" }),
  );
  for (const round of operation.rounds) {
    const button = element("button", {
      className: "display-round-button",
      text: `Round ${round.number}`,
      attributes: {
        type: "button",
        "aria-pressed": String(round.id === selectedRound.id),
      },
    });
    if (round.id === selectedRound.id) {
      button.classList.add("active");
    }
    button.addEventListener("click", () => onSelect(round), { signal });
    navigation.append(button);
  }
  return navigation;
}

function podium(operation, standings, round) {
  if (!standings.length) {
    return null;
  }
  const names = new Map(
    operation.participants.map((participant) => [
      String(participant.id),
      participant.player_name,
    ]),
  );
  const medalLabels = ["Champion", "Runner-up", "Third place"];
  const medals = standings.slice(0, 3).map((standing, index) => {
    const medal = element("li", {
      className: `podium-place podium-place-${index + 1}`,
    });
    medal.append(
      element("span", { className: "podium-rank", text: String(standing.rank) }),
      element("span", { className: "podium-medal-label", text: medalLabels[index] }),
      element("strong", {
        text: names.get(String(standing.participant_id)) ?? "Unknown player",
      }),
      element("span", {
        className: "podium-points",
        text: `${Number(standing.points)} point${
          Number(standing.points) === 1 ? "" : "s"
        }`,
      }),
    );
    return medal;
  });
  const ceremony = element("section", {
    className: "section-podium",
    attributes: { "aria-label": `${operation.name} final podium` },
  });
  ceremony.append(
    element("p", { className: "podium-kicker", text: `${operation.name} · Final` }),
    element("h3", { text: "The final table" }),
    element("p", {
      className: "muted",
      text: `Standings sealed after round ${round.number}.`,
    }),
    element("ol", { className: "podium-list" }),
  );
  ceremony.lastElementChild.append(...medals);
  return ceremony;
}

function sectionDisplay({
  operation,
  snapshots,
  selectedRound = latestRound(operation),
  signal,
}) {
  const round = selectedRound;
  const standings =
    snapshots.get(selectedSnapshotKey(operation.id, round?.id)) ?? [];
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

  const selector = roundSelector(
    operation,
    round,
    (nextRound) => {
      const replacement = sectionDisplay({
        operation,
        snapshots,
        selectedRound: nextRound,
        signal,
      });
      section.replaceWith(replacement);
      replacement.querySelector(".display-round-button.active")?.focus();
    },
    signal,
  );
  if (selector) {
    section.append(selector);
  }

  const finalPodium =
    round.id === latestRound(operation)?.id &&
    (operation.tournament_lifecycle === "finished" ||
      operation.lifecycle === "finished")
      ? podium(operation, standings, round)
      : null;
  if (finalPodium) {
    section.append(finalPodium);
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

function victoryCeremony(workspace, operations, snapshots) {
  if (workspace.lifecycle !== "finished") {
    return null;
  }
  const champions = operations.flatMap((operation) => {
    const finalRound = latestRound(operation);
    const standings = finalRound
      ? snapshots.get(selectedSnapshotKey(operation.id, finalRound.id)) ?? []
      : [];
    const champion = standings[0];
    if (!champion) {
      return [];
    }
    const participant = operation.participants.find(
      (candidate) => String(candidate.id) === String(champion.participant_id),
    );
    return participant
      ? [
          {
            section: operation.name,
            name: participant.player_name,
            points: Number(champion.points),
          },
        ]
      : [];
  });
  const ceremony = element("section", {
    className: "victory-ceremony",
    attributes: { "aria-label": "Tournament finished victory ceremony" },
  });
  const copy = element("div", { className: "victory-copy" });
  copy.append(
    element("p", { className: "victory-kicker", text: "Tournament complete" }),
    element("h2", { text: "The boards are closed." }),
    element("p", {
      className: "victory-description",
      text: champions.length
        ? "Final standings are sealed. Celebrate the players who finished on top."
        : "Final standings are sealed. The tournament has entered its history books.",
    }),
  );
  const laurels = element("div", { className: "victory-laurels" });
  for (const champion of champions) {
    const winner = element("div", { className: "victory-winner" });
    winner.append(
      element("span", {
        className: "victory-section",
        text: champion.section,
      }),
      element("strong", { text: champion.name }),
      element("span", {
        className: "victory-score",
        text: `${champion.points} point${champion.points === 1 ? "" : "s"}`,
      }),
    );
    laurels.append(winner);
  }
  ceremony.append(
    element("span", { className: "victory-crown", text: "♛" }),
    copy,
    ...(champions.length ? [laurels] : []),
  );
  return ceremony;
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
  let activeSignal;
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
  root.classList.add("display-page");
  const result = element("div", { className: "result-slot tournament-display" });
  const updated = element("p", { className: "display-updated muted" });
  root.append(updated, result);

  function render(workspace, operations, snapshots) {
    result.replaceChildren();
    root.classList.toggle(
      "display-tournament-finished",
      workspace.lifecycle === "finished",
    );
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
    root.querySelector(".page-description").textContent =
      workspace.lifecycle === "finished"
        ? "A finished tournament, final standings, and every completed round preserved for the ceremony."
        : "Browse the current pairings, revisit earlier rounds, and follow the latest standings.";
    if (workspace.lifecycle === "finished") {
      const ceremony = victoryCeremony(workspace, operations, snapshots);
      if (ceremony) {
        result.append(ceremony);
      }
    }
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
        sectionDisplay({
          operation,
          snapshots,
          signal: activeSignal,
        }),
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
      const snapshotEntries = await Promise.all(
        operations.flatMap((operation) =>
          operation.rounds.map(async (round) => [
            selectedSnapshotKey(operation.id, round.id),
            await api.get(
              `/api/tournament-sections/${operation.id}/standings?through_round_id=${round.id}`,
              { signal },
            ),
          ]),
        ),
      );
      const snapshots = new Map(snapshotEntries);
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
      activeSignal = signal;
      refresh.addEventListener(
        "click",
        () => void pendingAction(refresh, () => load(signal)),
        { signal },
      );
      void load(signal);
    },
  };
}
