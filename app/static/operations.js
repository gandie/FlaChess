import { api } from "./api.js";
import {
  badge,
  confirmAction,
  element,
  emptyState,
  errorSummary,
  page,
  pendingAction,
  status,
  table,
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
  const article = element("article", {
    className: "operation-record game-record",
    attributes: {
      id: `game-${game.id}`,
      tabindex: "-1",
      "data-game-id": game.id,
      "data-result-state": game.white_score === null ? "incomplete" : "recorded",
    },
  });
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
        await context.refreshAfterResult(round.id, game.id);
      },
    }),
  );
  return article;
}

function jumpToGame(gameId) {
  const record = document.querySelector(`#game-${gameId}`);
  if (!record) {
    return;
  }
  record.scrollIntoView({ block: "center" });
  record.querySelector("select, input, button")?.focus({ preventScroll: true });
}

function resultQueue(context, round) {
  if (!context.editable || !round.games.length) {
    return null;
  }
  const incomplete = round.games.filter((game) => game.white_score === null);
  const queue = element("section", {
    className: "result-queue",
    attributes: {
      "aria-label": `Round ${round.number} result entry shortcuts`,
      tabindex: "-1",
    },
  });
  queue.append(
    element("div", { className: "result-queue-heading" }),
  );
  queue.firstElementChild.append(
    element("h3", { text: "Result entry" }),
    element("span", {
      className: "muted",
      text: `${incomplete.length} incomplete ${
        incomplete.length === 1 ? "game" : "games"
      }`,
    }),
  );
  const links = element("div", { className: "result-jump-list" });
  const orderedGames = [...round.games].sort(
    (left, right) =>
      Number(left.white_score !== null) - Number(right.white_score !== null),
  );
  for (const game of orderedGames) {
    const button = element("button", {
      className: "result-jump",
      text: `${game.white_player_name} – ${game.black_player_name}`,
      attributes: { type: "button" },
    });
    if (game.white_score === null) {
      button.classList.add("incomplete");
    }
    button.addEventListener("click", () => jumpToGame(game.id), {
      signal: context.signal,
    });
    links.append(button);
  }
  queue.append(links);
  return queue;
}

function roundIsComplete(round) {
  return (
    (round.games.length > 0 || round.records.length > 0) &&
    round.games.every(
      (game) => game.white_score !== null && game.black_score !== null,
    )
  );
}

function focusResultEntry(round) {
  const firstIncomplete = round.games.find(
    (game) => game.white_score === null || game.black_score === null,
  );
  if (firstIncomplete) {
    jumpToGame(firstIncomplete.id);
    return;
  }
  document.querySelector(".result-queue")?.focus();
}

function creationDisclosure(title, summary, content) {
  const details = element("details", { className: "operation-disclosure" });
  details.append(
    element("summary", { text: summary }),
    element("h4", { text: title }),
    content,
  );
  return details;
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
  const queue = resultQueue(context, round);
  if (queue) {
    card.append(queue);
  }
  const games = element("section", { className: "operation-panel" });
  games.append(element("h3", { text: "Games and pairings" }));
  if (round.games.length) {
    games.append(...round.games.map((game) => gameEditor(context, round, game)));
  } else {
    games.append(emptyState("No pairings", "Add a manual pairing for this round."));
  }
  if (context.editable) {
    games.append(
      creationDisclosure(
        "New manual pairing",
        "Add a manual pairing",
        pairingCreator(context, round),
      ),
    );
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
    records.append(
      creationDisclosure(
        "New participation record",
        "Add a bye, unplayed round, or absence",
        participationCreator(context, round),
      ),
    );
  }
  card.append(games, records);
  return card;
}

function roundNavigation(operation, tournamentId, activeRoundId) {
  const navigation = element("nav", {
    className: "round-navigation live-round-rail",
    attributes: { "aria-label": "Round review navigation" },
  });
  navigation.append(
    element("span", { className: "round-rail-label", text: "Round desk" }),
  );
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

function nextRoundNumber(operation) {
  return Math.max(0, ...operation.rounds.map((round) => round.number)) + 1;
}

function pairingParticipantLabel(context, preview, participantId) {
  const participant = context.operation.participants.find(
    (candidate) => String(candidate.id) === String(participantId),
  );
  const seed = preview.seed_order.find(
    (candidate) => String(candidate.participant_id) === String(participantId),
  );
  const name = participant?.player_name ?? `Participant ${participantId}`;
  return seed ? `${name} (seed ${seed.seed_position})` : name;
}

function pairingPreviewGames(context, preview) {
  return table({
    caption: `Round ${preview.target_round} pairing preview`,
    columns: [
      { key: "board", label: "Board" },
      {
        key: "white",
        label: "White",
        render: (value) => pairingParticipantLabel(context, preview, value),
      },
      {
        key: "black",
        label: "Black",
        render: (value) => pairingParticipantLabel(context, preview, value),
      },
    ],
    rows: preview.games.map((game, index) => ({
      board: index + 1,
      white: game.white_participant_id,
      black: game.black_participant_id,
    })),
    emptyMessage: "The preview contains no paired games.",
  });
}

function pairingPreviewOutcomes(context, preview) {
  if (!preview.outcomes.length) {
    return null;
  }
  const section = element("section", { className: "pairing-preview-outcomes" });
  section.append(
    element("h4", { text: "Byes and non-paired outcomes" }),
    table({
      caption: `Round ${preview.target_round} non-paired outcomes`,
      columns: [
        {
          key: "participant",
          label: "Player",
          render: (value) => pairingParticipantLabel(context, preview, value),
        },
        { key: "outcome", label: "Outcome" },
        { key: "score", label: "Awarded score" },
      ],
      rows: preview.outcomes.map((outcome) => ({
        participant: outcome.participant_id,
        outcome: labelFor(outcome.outcome_type),
        score:
          outcome.score_awarded === null
            ? "No score"
            : Number(outcome.score_awarded),
      })),
      emptyMessage: "No player is marked as non-paired.",
    }),
  );
  return section;
}

function pairingPreviewWarnings(preview) {
  if (!preview.warnings.length) {
    return null;
  }
  const section = element("section", { className: "pairing-preview-warnings" });
  const list = element("ul");
  list.append(
    ...preview.warnings.map((warning) => element("li", { text: warning })),
  );
  section.append(element("h4", { text: "Warnings" }), list);
  return section;
}

function pairingPreviewContent(context, preview) {
  const container = element("div", { className: "pairing-preview" });
  const outcomeSection = pairingPreviewOutcomes(context, preview);
  const warningSection = pairingPreviewWarnings(preview);
  container.append(
    element("div", { className: "section-heading" }),
  );
  container.firstElementChild.append(
    element("h3", { text: `Preview round ${preview.target_round}` }),
    badge(labelFor(preview.format), "accent"),
  );
  container.append(
    element("p", {
      className: "muted",
      text: `Round ${preview.target_round} of ${preview.planned_round_count} planned; ${preview.calculated_round_count} rounds calculated.`,
    }),
    pairingPreviewGames(context, preview),
  );
  if (outcomeSection) {
    container.append(outcomeSection);
  }
  if (warningSection) {
    container.append(warningSection);
  }
  return container;
}

function pairingConfirmAction(context, preview, result) {
  const button = element("button", {
    className: "button",
    text: "Confirm generation",
    attributes: { type: "button" },
  });
  button.addEventListener("click", () => {
    let generatedRoundId = null;
    void pendingAction(button, async () => {
      result.replaceChildren(status("Generating round\u2026"));
      try {
        const generated = await api.post(
          `/api/tournament-sections/${context.operation.id}/pairing/confirm`,
          { expected_round_number: preview.target_round },
          { signal: context.signal },
        );
        result.replaceChildren(
          status(
            `Round ${generated.target_round} generated successfully.`,
            "success",
          ),
        );
        if (generated.round_id === null) {
          throw new Error("The confirmed pairing response has no round ID.");
        }
        generatedRoundId = generated.round_id;
      } catch (error) {
        if (error?.name !== "AbortError") {
          result.replaceChildren(status(errorSummary(error), "error"));
        }
      }
    }).then(() => {
      if (generatedRoundId !== null) {
        button.disabled = true;
        button.textContent = "Generation confirmed";
        window.location.hash =
          `/tournaments/${context.operation.tournament_id}/sections/` +
          `${context.operation.id}/rounds/${generatedRoundId}`;
      }
    });
  });
  return button;
}

function pairingAutomation(context) {
  const nextRound = nextRoundNumber(context.operation);
  if (
    !context.editable ||
    context.operation.planned_round_count === null ||
    nextRound > context.operation.planned_round_count
  ) {
    return null;
  }
  const latestRound = context.operation.rounds.at(-1);
  const previewReady = !latestRound || roundIsComplete(latestRound);
  const card = element("section", { className: "card pairing-automation-card" });
  const actionResult = element("div", { className: "result-slot compact" });
  const previewResult = element("div", { className: "pairing-preview-slot" });
  const previewButton = element("button", {
    className: "button",
    text: "Preview next round",
    attributes: { type: "button" },
  });
  previewButton.disabled = !previewReady;
  if (!previewReady) {
    actionResult.append(
      status(
        `Record every result in round ${latestRound.number} before previewing round ${nextRound}.`,
        "warning",
      ),
    );
  }
  previewButton.addEventListener("click", () => {
    void pendingAction(previewButton, async () => {
      actionResult.replaceChildren(status("Preparing pairing preview\u2026"));
      try {
        const preview = await api.get(
          `/api/tournament-sections/${context.operation.id}/pairing/preview`,
          { signal: context.signal },
        );
        const review = pairingPreviewContent(context, preview);
        const confirmResult = element("div", {
          className: "result-slot compact pairing-confirm-result",
        });
        const actions = element("div", { className: "action-group" });
        actions.append(pairingConfirmAction(context, preview, confirmResult));
        review.append(actions, confirmResult);
        previewResult.replaceChildren(review);
        actionResult.replaceChildren();
      } catch (error) {
        if (error?.name !== "AbortError") {
          actionResult.replaceChildren(status(errorSummary(error), "error"));
        }
      }
    });
  });
  card.append(
    element("h2", { text: "Automated pairing" }),
    element("p", {
      className: "muted",
      text: "Preview the next round before committing its complete pairing plan.",
    }),
    previewButton,
    actionResult,
    previewResult,
  );
  return card;
}

function sectionAction(context) {
  if (context.operation.tournament_lifecycle === "finished") {
    return null;
  }
  const transition = {
    draft: {
      action: "Activate section",
      pending: "Activating section\u2026",
      target: "activate",
      confirmation:
        "Activate this section? Round creation and result entry will become available.",
    },
    active: {
      action: "Finish section",
      pending: "Finishing section\u2026",
      target: "finish",
      confirmation:
        "Finish this section? Its operation and standings will become read-only.",
    },
  }[context.operation.lifecycle];
  if (!transition) {
    return null;
  }
  const button = element("button", {
    className:
      transition.target === "finish" ? "button button-danger" : "button",
    text: transition.action,
    attributes: { type: "button" },
  });
  const result = element("div", { className: "result-slot" });
  button.addEventListener("click", () => {
    if (
      transition.confirmation &&
      !confirmAction(transition.confirmation)
    ) {
      return;
    }
    void pendingAction(button, async () => {
      result.replaceChildren(status(transition.pending));
      try {
        await api.post(
          `/api/tournament-sections/${context.operation.id}/${transition.target}`,
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
    description:
      "Preview generated pairings, manage manual rounds, and record results.",
  });
  root.classList.add("operation-page");
  const result = element("div", { className: "result-slot" });
  root.append(result);

  function render(operation, workspace, signal) {
    const activeRound =
      operation.rounds.find(
        (round) => String(round.id) === String(roundId),
      ) ?? operation.rounds.at(-1);
    const context = {
      operation,
      signal,
      editable:
        operation.tournament_lifecycle === "active" &&
        operation.lifecycle === "active",
      refresh: () => load(signal),
      refreshAfterResult: async (changedRoundId) => {
        const refreshed = await fetchOperation(signal);
        const changedRound = refreshed.rounds.find(
          (round) => String(round.id) === String(changedRoundId),
        );
        let standingsError = null;
        if (changedRound) {
          try {
            await recomputeStandings({
              sectionId,
              roundId: changedRound.id,
              signal,
            });
          } catch (error) {
            if (error?.name !== "AbortError") {
              standingsError = error;
            }
          }
        }
        render(refreshed, workspace, signal);
        if (standingsError) {
          result.prepend(
            status(
              `The result was saved, but standings could not be recomputed. ${errorSummary(standingsError)}`,
              "error",
            ),
          );
        }
        window.requestAnimationFrame(() => {
          if (changedRound) {
            focusResultEntry(changedRound);
          }
        });
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
    if (operation.tournament_lifecycle === "finished") {
      summary.append(
        status(
          "Historical section: the finished tournament workspace is read-only.",
          "success",
        ),
      );
    } else if (operation.lifecycle === "draft") {
      summary.append(
        status("Activate the section before creating rounds and recording results.", "warning"),
      );
    } else if (operation.lifecycle === "finished") {
      summary.append(
        status("Final section standings and round records are read-only.", "success"),
      );
    }
    const automation = pairingAutomation(context);
    const navigation = element("nav", {
      className: "tournament-desk",
      attributes: { "aria-label": "Tournament navigation" },
    });
    navigation.append(
      element("span", { className: "tournament-desk-label", text: "Tournament desk" }),
      element("a", {
        className: "tournament-desk-link",
        text: "Overview",
        attributes: { href: `#/tournaments/${tournamentId}` },
      }),
    );
    for (const phase of workspace.phases) {
      for (const section of phase.sections) {
        const current = String(section.id) === String(operation.id);
        navigation.append(
          element(current ? "span" : "a", {
            className: `tournament-desk-link${current ? " active" : ""}`,
            text: current ? `${section.sequence}. ${section.name}` : section.name,
            attributes: current
              ? { "aria-current": "page" }
              : {
                  href: `#/tournaments/${tournamentId}/sections/${section.id}`,
                },
          }),
        );
      }
    }
    navigation.append(
      element("a", {
        className: "tournament-desk-link",
        text: "Player display",
        attributes: { href: `#/display/tournaments/${tournamentId}` },
      }),
    );
    const action = sectionAction(context);
    if (action) {
      action.classList.add("tournament-desk-progress");
      navigation.append(action);
    }
    result.append(navigation, summary);
    if (activeRound) {
      result.append(
        roundNavigation(operation, tournamentId, activeRound.id),
        ...(automation ? [automation] : []),
        roundPanel(context, activeRound),
        standingsReview({
          operation,
          round: activeRound,
          signal,
        }),
      );
      if (
        roundId !== null &&
        String(activeRound.id) === String(roundId)
      ) {
        window.requestAnimationFrame(() => focusResultEntry(activeRound));
      }
    } else {
      result.append(emptyState("No rounds", "Create the first round for this section."));
    }
    if (!activeRound && automation) {
      result.append(automation);
    }
    if (context.editable) {
      const card = element("section", { className: "card" });
      const nextRound = nextRoundNumber(operation);
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
      const [operation, workspace] = await Promise.all([
        fetchOperation(signal),
        api.get(`/api/tournaments/${tournamentId}/workspace`, { signal }),
      ]);
      render(operation, workspace, signal);
    } catch (error) {
      if (signal.aborted || error?.name === "AbortError") {
        return;
      }
      result.replaceChildren(status(errorSummary(error), "error"));
    }
  }

  async function fetchOperation(signal) {
    const operation = await api.get(
      `/api/tournament-sections/${sectionId}/operation`,
      { signal },
    );
    if (String(operation.tournament_id) !== String(tournamentId)) {
      throw new Error("The requested section does not belong to this tournament.");
    }
    return operation;
  }

  return {
    title: "Section operation",
    element: root,
    activate({ signal }) {
      void load(signal);
    },
  };
}
