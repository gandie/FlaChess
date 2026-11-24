import { api } from "./api.js";
import {
  badge,
  element,
  emptyState,
  errorSummary,
  page,
  pendingAction,
  status,
} from "./render.js";
import {
  recomputeStandings,
  standingsReview,
} from "./standings.js";

const RESULT_TYPES = [
  ["normal", "Normal"],
  ["white_forfeit", "White forfeit"],
  ["black_forfeit", "Black forfeit"],
  ["double_forfeit", "Double forfeit"],
  ["adjusted", "Adjusted"],
];

const OUTCOMES = [
  ["unrecorded", "Not yet recorded"],
  ["1:0", "White wins (1-0)"],
  ["0.5:0.5", "Draw (½-½)"],
  ["0:1", "Black wins (0-1)"],
];

function labelFor(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formField({ id, label, options = null, type = "text", value = "" }) {
  const wrapper = element("div", { className: "field" });
  wrapper.append(element("label", { text: label, attributes: { for: id } }));
  const control = element(options ? "select" : "input", {
    attributes: { id, name: id },
  });
  if (options) {
    for (const [optionValue, optionLabel] of options) {
      const option = element("option", {
        text: optionLabel,
        attributes: { value: optionValue },
      });
      option.selected = String(optionValue) === String(value);
      control.append(option);
    }
  } else {
    control.type = type;
    control.value = value;
  }
  wrapper.append(control);
  return { wrapper, control };
}

function outcomeValue(whiteScore, blackScore) {
  if (whiteScore === null || blackScore === null) {
    return "unrecorded";
  }
  return `${Number(whiteScore)}:${Number(blackScore)}`;
}

function scoresFor(value) {
  if (value === "unrecorded") {
    return [null, null];
  }
  const [whiteScore, blackScore] = value.split(":").map(Number);
  if (
    ![0, 0.5, 1].includes(whiteScore) ||
    ![0, 0.5, 1].includes(blackScore) ||
    whiteScore + blackScore !== 1
  ) {
    return null;
  }
  return [whiteScore, blackScore];
}

function writeForm({ fields, submitText, className, onWrite }) {
  const form = element("form", { className: className ?? "operation-form" });
  const controls = fields();
  const submit = element("button", {
    className: "button button-small",
    text: submitText,
    attributes: { type: "submit" },
  });
  const result = element("div", { className: "result-slot compact" });
  form.append(...controls.map((field) => field.wrapper), submit, result);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void pendingAction(submit, async () => {
      result.replaceChildren(status("Saving\u2026"));
      try {
        const completed = await onWrite(controls, result);
        if (completed !== false) {
          result.replaceChildren();
        }
      } catch (error) {
        if (error?.name !== "AbortError") {
          result.replaceChildren(status(errorSummary(error), "error"));
        }
      }
    });
  });
  return form;
}

function gameEditor(context, round, game) {
  const article = element("article", { className: "operation-record" });
  const recorded = game.white_score !== null;
  article.append(
    element("h4", {
      text: `${game.white_player_name} – ${game.black_player_name}`,
    }),
    badge(recorded ? "Recorded" : "Incomplete", recorded ? "success" : "accent"),
    badge(labelFor(game.result_type)),
  );
  if (!context.editable) {
    article.append(
      element("p", {
        text:
          game.white_score === null
            ? "Result not recorded."
            : `${game.white_score} - ${game.black_score}`,
      }),
      element("p", { className: "muted", text: game.comment || "No comment" }),
    );
    return article;
  }
  article.append(
    writeForm({
      fields: () => [
        formField({
          id: `game_${game.id}_outcome`,
          label: "Result",
          options: OUTCOMES,
          value: outcomeValue(game.white_score, game.black_score),
        }),
        formField({
          id: `game_${game.id}_result_type`,
          label: "Result type",
          options: RESULT_TYPES,
          value: game.result_type,
        }),
        formField({
          id: `game_${game.id}_comment`,
          label: "Comment",
          value: game.comment ?? "",
        }),
      ],
      submitText: "Save game result",
      className: "operation-form game-form",
      onWrite: async ([outcome, resultType, comment], result) => {
        const scores = scoresFor(outcome.control.value);
        if (scores === null) {
          result.replaceChildren(
            status(
              "Choose an allowed pair of scores that totals one, or leave the result unrecorded.",
              "error",
            ),
          );
          return false;
        }
        const [whiteScore, blackScore] = scores;
        await api.patch(
          `/api/games/${game.id}`,
          {
            white_score: whiteScore,
            black_score: blackScore,
            result_type: resultType.control.value,
            recorded_at:
              whiteScore === null
                ? null
                : game.recorded_at ?? new Date().toISOString(),
            comment: comment.control.value.trim() || null,
          },
          { signal: context.signal },
        );
        await context.refreshAfterResult(round.id);
      },
    }),
  );
  return article;
}

function pairingCreator(context, round) {
  return writeForm({
    fields: () => [
      formField({
        id: `round_${round.id}_white`,
        label: "White",
        options: context.operation.participants.map((participant) => [
          participant.id,
          participant.player_name,
        ]),
      }),
      formField({
        id: `round_${round.id}_black`,
        label: "Black",
        options: context.operation.participants.map((participant) => [
          participant.id,
          participant.player_name,
        ]),
      }),
      formField({
        id: `round_${round.id}_outcome`,
        label: "Result",
        options: OUTCOMES,
        value: "unrecorded",
      }),
      formField({
        id: `round_${round.id}_result_type`,
        label: "Result type",
        options: RESULT_TYPES,
        value: "normal",
      }),
      formField({
        id: `round_${round.id}_comment`,
        label: "Comment",
      }),
    ],
    submitText: "Add pairing",
    className: "operation-form game-form",
    onWrite: async ([white, black, outcome, resultType, comment], result) => {
      if (white.control.value === black.control.value) {
        result.replaceChildren(
          status("White and black must be different section members.", "error"),
        );
        return false;
      }
      const scores = scoresFor(outcome.control.value);
      if (scores === null) {
        result.replaceChildren(status("The selected score pair is invalid.", "error"));
        return false;
      }
      const [whiteScore, blackScore] = scores;
      await api.post(
        "/api/games",
        {
          round_id: round.id,
          white_participant_id: Number(white.control.value),
          black_participant_id: Number(black.control.value),
          white_score: whiteScore,
          black_score: blackScore,
          result_type: resultType.control.value,
          recorded_at: whiteScore === null ? null : new Date().toISOString(),
          comment: comment.control.value.trim() || null,
        },
        { signal: context.signal },
      );
      await context.refreshAfterResult(round.id);
    },
  });
}

function participationEditor(context, record) {
  const article = element("article", { className: "operation-record" });
  article.append(element("h4", { text: record.player_name }));
  if (!context.editable) {
    article.append(
      badge(labelFor(record.participation_type), "neutral"),
      element("p", {
        text:
          record.score_awarded === null
            ? "No awarded score"
            : `${record.score_awarded} point${Number(record.score_awarded) === 1 ? "" : "s"}`,
      }),
      element("p", { className: "muted", text: record.comment || "No comment" }),
    );
    return article;
  }
  article.append(
    writeForm({
      fields: () => [
        formField({
          id: `record_${record.id}_type`,
          label: "Participation",
          options:
            record.participation_type === "paired"
              ? [["paired", "Paired"]]
              : [
                  ["bye", "Bye"],
                  ["unplayed", "Unplayed"],
                  ["absent", "Absent"],
                ],
          value: record.participation_type,
        }),
        formField({
          id: `record_${record.id}_score`,
          label: "Awarded score",
          options:
            record.participation_type === "paired"
              ? [["none", "None"]]
              : [
                  ["none", "None"],
                  ["0", "0"],
                  ["0.5", "0.5"],
                  ["1", "1"],
                ],
          value:
            record.score_awarded === null
              ? "none"
              : Number(record.score_awarded),
        }),
        formField({
          id: `record_${record.id}_comment`,
          label: "Comment",
          value: record.comment ?? "",
        }),
      ],
      submitText: "Save participation",
      onWrite: async ([type, score, comment]) => {
        await api.patch(
          `/api/round-participants/${record.id}`,
          {
            participation_type: type.control.value,
            score_awarded:
              score.control.value === "none"
                ? null
                : Number(score.control.value),
            comment: comment.control.value.trim() || null,
          },
          { signal: context.signal },
        );
        await context.refreshAfterResult(record.round_id);
      },
    }),
  );
  return article;
}

function participationCreator(context, round) {
  return writeForm({
    fields: () => [
      formField({
        id: `round_${round.id}_record_player`,
        label: "Section member",
        options: context.operation.participants.map((participant) => [
          participant.id,
          participant.player_name,
        ]),
      }),
      formField({
        id: `round_${round.id}_record_type`,
        label: "Participation",
        options: [
          ["bye", "Bye"],
          ["unplayed", "Unplayed"],
          ["absent", "Absent"],
        ],
      }),
      formField({
        id: `round_${round.id}_record_score`,
        label: "Awarded score",
        options: [
          ["none", "None"],
          ["0", "0"],
          ["0.5", "0.5"],
          ["1", "1"],
        ],
      }),
      formField({
        id: `round_${round.id}_record_comment`,
        label: "Comment",
      }),
    ],
    submitText: "Record participation",
    onWrite: async ([participant, type, score, comment]) => {
      await api.post(
        "/api/round-participants",
        {
          round_id: round.id,
          participant_id: Number(participant.control.value),
          participation_type: type.control.value,
          score_awarded:
            score.control.value === "none" ? null : Number(score.control.value),
          comment: comment.control.value.trim() || null,
        },
        { signal: context.signal },
      );
      await context.refreshAfterResult(round.id);
    },
  });
}

function roundPanel(context, round) {
  const card = element("section", { className: "round-card" });
  card.append(
    badge(`Round ${round.number}`, "accent"),
    element("h2", { text: `Round ${round.number}` }),
  );
  const games = element("section", { className: "operation-panel" });
  games.append(element("h3", { text: "Games and pairings" }));
  if (round.games.length) {
    games.append(...round.games.map((game) => gameEditor(context, round, game)));
  } else {
    games.append(emptyState("No pairings", "Add a manual pairing for this round."));
  }
  if (context.editable) {
    const creator = element("div", { className: "operation-panel" });
    creator.append(element("h4", { text: "New manual pairing" }), pairingCreator(context, round));
    games.append(creator);
  }
  const records = element("section", { className: "operation-panel" });
  records.append(element("h3", { text: "Byes, unplayed rounds, and absences" }));
  if (round.records.length) {
    records.append(
      ...round.records.map((record) => participationEditor(context, record)),
    );
  } else {
    records.append(
      emptyState("No participation records", "Record non-game participation as needed."),
    );
  }
  if (context.editable) {
    const creator = element("div", { className: "operation-panel" });
    creator.append(
      element("h4", { text: "New participation record" }),
      participationCreator(context, round),
    );
    records.append(creator);
  }
  card.append(games, records);
  return card;
}

function roundNavigation(operation, tournamentId, activeRoundId) {
  const navigation = element("nav", {
    className: "round-navigation",
    attributes: { "aria-label": "Round review navigation" },
  });
  for (const round of operation.rounds) {
    const link = element("a", {
      className: "round-navigation-link",
      text: `Round ${round.number}`,
      attributes: {
        href: `#/tournaments/${tournamentId}/sections/${operation.id}/rounds/${round.id}`,
      },
    });
    if (String(round.id) === String(activeRoundId)) {
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
    }
    navigation.append(link);
  }
  return navigation;
}

function sectionAction(context) {
  if (context.operation.lifecycle !== "draft") {
    return null;
  }
  const button = element("button", {
    className: "button",
    text: "Activate section",
    attributes: { type: "button" },
  });
  const result = element("div", { className: "result-slot" });
  button.addEventListener("click", () => {
    void pendingAction(button, async () => {
      result.replaceChildren(status("Activating section\u2026"));
      try {
        await api.post(
          `/api/tournament-sections/${context.operation.id}/activate`,
          {},
          { signal: context.signal },
        );
        await context.refresh();
      } catch (error) {
        if (error?.name !== "AbortError") {
          result.replaceChildren(status(errorSummary(error), "error"));
        }
      }
    });
  });
  const wrapper = element("div");
  wrapper.append(button, result);
  return wrapper;
}

export function sectionOperationView({
  tournamentId,
  sectionId,
  roundId = null,
}) {
  const root = page({
    eyebrow: "Section operation",
    title: "Section",
    description: "Create rounds, pair players manually, and record round results.",
  });
  const result = element("div", { className: "result-slot" });
  root.append(result);

  function render(operation, signal) {
    const activeRound =
      operation.rounds.find(
        (round) => String(round.id) === String(roundId),
      ) ?? operation.rounds.at(-1);
    const context = {
      operation,
      signal,
      editable: operation.lifecycle === "active",
      refresh: () => load(signal),
      refreshAfterResult: async (changedRoundId) => {
        await recomputeStandings({
          sectionId,
          roundId: changedRoundId,
          signal,
        });
        await load(signal);
      },
    };
    result.replaceChildren();
    const summary = element("section", { className: "card operation-summary" });
    const title = element("h2", { text: `${operation.sequence}. ${operation.name}` });
    summary.append(
      badge(labelFor(operation.lifecycle), operation.lifecycle === "active" ? "success" : "accent"),
      title,
      element("p", {
        className: "muted",
        text: `${operation.tournament_name} · ${operation.participants.length} section members`,
      }),
    );
    const action = sectionAction(context);
    if (action) {
      summary.append(action);
    }
    if (operation.lifecycle === "draft") {
      summary.append(
        status("Activate the section before creating rounds and recording results.", "warning"),
      );
    } else if (operation.lifecycle !== "active") {
      summary.append(status("This section operation view is read-only.", "warning"));
    }
    result.append(summary);
    if (activeRound) {
      result.append(
        roundNavigation(operation, tournamentId, activeRound.id),
        standingsReview({
          operation,
          round: activeRound,
          signal,
        }),
        roundPanel(context, activeRound),
      );
    } else {
      result.append(emptyState("No rounds", "Create the first round for this section."));
    }
    if (context.editable) {
      const card = element("section", { className: "card" });
      const nextRound = Math.max(0, ...operation.rounds.map((round) => round.number)) + 1;
      card.append(
        element("h2", { text: "New round" }),
        element("p", {
          className: "muted",
          text: operation.planned_round_count
            ? `Round ${nextRound} of ${operation.planned_round_count} planned.`
            : "The section has no planned round count.",
        }),
        writeForm({
          fields: () => [
            formField({
              id: "new_round_number",
              label: "Round number",
              type: "number",
              value: nextRound,
            }),
          ],
          submitText: "Create round",
          onWrite: async ([number]) => {
            await api.post(
              "/api/tournament-rounds",
              {
                section_id: Number(sectionId),
                number: Number(number.control.value),
              },
              { signal },
            );
            await load(signal);
          },
        }),
      );
      result.append(card);
    }
  }

  async function load(signal) {
    result.replaceChildren(status("Loading section operation\u2026"));
    try {
      const operation = await api.get(
        `/api/tournament-sections/${sectionId}/operation`,
        { signal },
      );
      if (String(operation.tournament_id) !== String(tournamentId)) {
        throw new Error("The requested section does not belong to this tournament.");
      }
      render(operation, signal);
    } catch (error) {
      if (signal.aborted || error?.name === "AbortError") {
        return;
      }
      result.replaceChildren(status(errorSummary(error), "error"));
    }
  }

  return {
    title: "Section operation",
    element: root,
    activate({ signal }) {
      void load(signal);
    },
  };
}
