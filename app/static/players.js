import { api } from "./api.js";
import {
  badge,
  confirmAction,
  element,
  emptyState,
  errorSummary,
  field,
  page,
  pendingAction,
  status,
  table,
} from "./render.js";

function playerForm({ player, onSave }) {
  const form = element("form", { className: "form-stack" });
  const name = field({
    id: "player_name",
    label: "Player name",
    value: player?.name ?? "",
  });
  name.control.required = true;
  name.control.maxLength = 255;
  const submit = element("button", {
    className: "button",
    text: player ? "Save player" : "Create player",
    attributes: { type: "submit" },
  });
  const result = element("div", { className: "result-slot" });
  form.append(name.wrapper, submit, result);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void pendingAction(submit, async () => {
      result.replaceChildren(status(player ? "Saving player\u2026" : "Creating player\u2026"));
      try {
        const values = { name: name.control.value.trim() };
        if (player) {
          await onSave(`/api/players/${player.id}`, values, "patch");
        } else {
          await onSave("/api/players", values, "post");
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

export function playerDirectoryView() {
  const root = page({
    eyebrow: "Player registry",
    title: "Players",
    description: "Maintain reusable player records for tournament registration.",
  });
  const layout = element("div", { className: "catalog-layout" });
  const directoryCard = element("section", { className: "card" });
  directoryCard.append(element("h2", { text: "Player directory" }));
  const directoryResult = element("div", { className: "result-slot" });
  directoryCard.append(directoryResult);

  const editorCard = element("section", { className: "card" });
  layout.append(directoryCard, editorCard);
  root.append(layout);
  let activeSignal;

  function showEditor(player = null) {
    editorCard.replaceChildren(
      badge(player ? "Edit player" : "Player creation", "accent"),
      element("h2", { text: player ? player.name : "New player" }),
    );
    const form = playerForm({
      player,
      onSave: async (path, values, method) => {
        await api[method](path, values, { signal: activeSignal });
        showEditor();
        await loadPlayers(activeSignal);
      },
    });
    editorCard.append(form);
    if (player) {
      const cancel = element("button", {
        className: "button button-secondary",
        text: "Cancel edit",
        attributes: { type: "button" },
      });
      cancel.addEventListener("click", () => showEditor(), {
        signal: activeSignal,
      });
      editorCard.append(cancel);
    }
  }

  async function loadPlayers(signal) {
    directoryResult.replaceChildren(status("Loading players\u2026"));
    try {
      const players = await api.get("/api/player-summaries", { signal });
      if (!players.length) {
        directoryResult.replaceChildren(
          emptyState("No players", "Create a player before registering entries."),
        );
        return;
      }
      directoryResult.replaceChildren(
        table({
          caption: "Player directory",
          columns: [
            { key: "name", label: "Player" },
            {
              key: "id",
              label: "Action",
              render: (_id, player) => {
                const edit = element("button", {
                  className: "button button-secondary button-small",
                  text: "Edit",
                  attributes: { type: "button" },
                });
                edit.addEventListener("click", () => showEditor(player), {
                  signal,
                });
                return edit;
              },
            },
          ],
          rows: players,
        }),
      );
    } catch (error) {
      if (!signal.aborted && error?.name !== "AbortError") {
        directoryResult.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  showEditor();
  return {
    title: "Players",
    element: root,
    activate({ signal }) {
      activeSignal = signal;
      void loadPlayers(signal);
    },
  };
}

function playerInitials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

function registrationRoster(players, participants, onRegister, onUnregister, signal) {
  const roster = element("div", { className: "player-action-list" });
  const registered = new Map(
    participants.map((participant) => [participant.player_id, participant]),
  );
  const heading = element("div", { className: "list-heading" });
  heading.append(
    element("h3", { text: "Tournament roster" }),
    element("span", {
      className: "count-label",
      text: `${participants.length} of ${players.length} registered`,
    }),
  );
  roster.append(heading);

  for (const player of players) {
    const participant = registered.get(player.id);
    const row = element("div", {
      className: `player-action-row${participant ? " is-registered" : ""}`,
    });
    const identity = element("div", { className: "player-identity" });
    identity.append(
      element("span", {
        className: "player-monogram",
        text: playerInitials(player.name),
        attributes: { "aria-hidden": "true" },
      }),
      element("span", { text: player.name }),
    );
    const button = element("button", {
      className: `button button-small roster-action ${
        participant ? "button-danger" : "button-secondary"
      }`,
      text: participant ? "\u2212 Remove" : "+ Add",
      attributes: {
        type: "button",
        "data-player-id": player.id,
        "aria-label": participant
          ? `Remove ${player.name} from the tournament`
          : `Add ${player.name} to the tournament`,
      },
    });
    button.addEventListener(
      "click",
      () =>
        void pendingAction(button, () =>
          participant
            ? onUnregister(participant.registration_id, player.name, player.id)
            : onRegister(player.id),
        ),
      { signal },
    );
    row.append(identity, button);
    roster.append(row);
  }
  return roster;
}

export function tournamentRegistrationCard(tournament, signal, onChange = null) {
  const card = element("section", { className: "card" });
  card.append(
    badge(
      tournament.lifecycle === "draft" ? "Draft registration" : "Participant roster",
      tournament.lifecycle === "draft" ? "accent" : "neutral",
    ),
    element("h2", { text: "Registered players" }),
  );
  const actionArea = element("div", { className: "registration-actions" });
  const result = element("div", { className: "result-slot" });
  card.append(actionArea, result);

  async function loadRegistration() {
    result.replaceChildren(status("Loading registrations\u2026"));
    try {
      const requests = [
        api.get(`/api/tournaments/${tournament.id}/participants`, { signal }),
      ];
      if (tournament.lifecycle === "draft") {
        requests.push(api.get("/api/player-summaries", { signal }));
      }
      const [participants, players = []] = await Promise.all(requests);
      actionArea.replaceChildren();
      if (tournament.lifecycle === "draft") {
        if (!players.length) {
          actionArea.append(
            element("p", {
              className: "muted",
              text: "Create a player in the player directory before registration.",
            }),
          );
        } else {
          actionArea.append(
            registrationRoster(
              players,
              participants,
              registerPlayer,
              unregisterPlayer,
              signal,
            ),
          );
        }
        result.replaceChildren(
          participants.length
            ? element("p", {
                className: "helper-copy",
                text: "Add and remove players directly. Changes are saved immediately.",
              })
            : emptyState("No registered players", "Select Add next to a player above."),
        );
        return;
      }
      if (!participants.length) {
        result.replaceChildren(
          emptyState("No registered players", "The tournament roster is empty."),
        );
        return;
      }
      result.replaceChildren(
        table({
          caption: "Registered players",
          columns: [{ key: "player_name", label: "Player" }],
          rows: participants,
        }),
      );
    } catch (error) {
      if (!signal.aborted && error?.name !== "AbortError") {
        result.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  async function registerPlayer(playerId) {
    try {
      await api.post(
        `/api/tournaments/${tournament.id}/participants`,
        { player_id: playerId },
        { signal },
      );
      await loadRegistration();
      await onChange?.({ focusPlayerId: playerId });
    } catch (error) {
      if (!signal.aborted && error?.name !== "AbortError") {
        result.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  async function unregisterPlayer(registrationId, playerName, playerId) {
    if (!confirmAction(`Unregister ${playerName} from ${tournament.name}?`)) {
      return;
    }
    try {
      await api.delete(
        `/api/tournaments/${tournament.id}/participants/${registrationId}`,
        { signal },
      );
      await loadRegistration();
      await onChange?.({ focusPlayerId: playerId });
    } catch (error) {
      if (!signal.aborted && error?.name !== "AbortError") {
        result.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  void loadRegistration();
  return card;
}
