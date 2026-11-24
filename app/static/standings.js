import { api } from "./api.js";
import {
  element,
  errorSummary,
  pendingAction,
  status,
  table,
} from "./render.js";

function labelFor(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function displayNumber(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(Number(value));
}

function tiebreakLabel(rule) {
  const label = labelFor(rule.code);
  return rule.parameter ? `${label} (${rule.parameter})` : label;
}

function snapshotTime(standings) {
  if (!standings.length) {
    return "";
  }
  const date = new Date(standings[0].computed_at);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function standingsTable(operation, standings, round) {
  const names = new Map(
    operation.participants.map((participant) => [
      String(participant.id),
      participant.player_name,
    ]),
  );
  const columns = [
    { key: "rank", label: "Rank" },
    { key: "player_name", label: "Player" },
    { key: "points", label: "Points" },
    { key: "wins", label: "W" },
    { key: "draws", label: "D" },
    { key: "losses", label: "L" },
    ...operation.tiebreaks.map((rule) => ({
      key: `tiebreak_${rule.id}`,
      label: tiebreakLabel(rule),
    })),
  ];
  const rows = standings.map((standing) => {
    const values = new Map(
      standing.values.map((value) => [
        String(value.tiebreak_id),
        displayNumber(value.value),
      ]),
    );
    return {
      ...standing,
      player_name: names.get(String(standing.participant_id)) ?? "Unknown player",
      points: displayNumber(standing.points),
      ...Object.fromEntries(
        operation.tiebreaks.map((rule) => [
          `tiebreak_${rule.id}`,
          values.get(String(rule.id)) ?? "",
        ]),
      ),
    };
  });
  return table({
    caption: `Standings through round ${round.number}`,
    columns,
    rows,
    emptyMessage: "Recompute standings for this round.",
  });
}

export async function recomputeStandings({ sectionId, roundId, signal }) {
  return api.post(
    `/api/tournament-sections/${sectionId}/standings/recompute?through_round_id=${roundId}`,
    {},
    { signal },
  );
}

export function standingsReview({ operation, round, signal }) {
  const card = element("section", { className: "card standings-card" });
  const isFinal =
    operation.tournament_lifecycle === "finished" ||
    operation.lifecycle === "finished";
  const canRecompute =
    operation.tournament_lifecycle === "active" &&
    operation.lifecycle === "active";
  const heading = element("div", { className: "section-heading" });
  const copy = element("div");
  copy.append(
    element("h2", {
      text: isFinal
        ? `Final standings through round ${round.number}`
        : `Standings through round ${round.number}`,
    }),
    element("p", {
      className: "muted",
      text: isFinal
        ? "This final snapshot is preserved with the completed section."
        : "Rankings use the section's active tie-break order.",
    }),
  );
  const recomputeButton = element("button", {
    className: "button button-secondary button-small",
    text: "Recompute standings",
    attributes: { type: "button" },
  });
  heading.append(copy);
  if (canRecompute) {
    heading.append(recomputeButton);
  }
  const snapshot = element("p", { className: "snapshot-time muted" });
  const result = element("div", { className: "result-slot" });
  card.append(heading, snapshot, result);

  async function load() {
    result.replaceChildren(status("Loading standings\u2026"));
    try {
      const standings = await api.get(
        `/api/tournament-sections/${operation.id}/standings?through_round_id=${round.id}`,
        { signal },
      );
      if (!standings.length) {
        result.replaceChildren(
          status("No standings snapshot exists for this round yet.", "warning"),
        );
        snapshot.textContent = "";
        return;
      }
      result.replaceChildren(standingsTable(operation, standings, round));
      snapshot.textContent = `Snapshot: ${snapshotTime(standings)}`;
    } catch (error) {
      if (error?.name !== "AbortError") {
        result.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  if (canRecompute) {
    recomputeButton.addEventListener(
      "click",
      () => {
        void pendingAction(recomputeButton, async () => {
          result.replaceChildren(status("Recomputing standings\u2026"));
          try {
            await recomputeStandings({
              sectionId: operation.id,
              roundId: round.id,
              signal,
            });
            await load();
          } catch (error) {
            if (error?.name !== "AbortError") {
              result.replaceChildren(status(errorSummary(error), "error"));
            }
          }
        });
      },
      { signal },
    );
  }
  void load();
  return card;
}
