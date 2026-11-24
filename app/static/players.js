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

function registrationForm(players, onRegister) {
  const form = element("form", { className: "registration-form" });
  const wrapper = element("div", { className: "field" });
  const label = element("label", {
    text: "Available player",
    attributes: { for: "registration_player" },
  });
  const select = element("select", {
    attributes: { id: "registration_player", name: "player_id" },
  });
  select.append(element("option", { text: "Choose a player\u2026", attributes: { value: "" } }));
  for (const player of players) {
    select.append(
      element("option", {
        text: player.name,
        attributes: { value: String(player.id) },
      }),
    );
  }
  const submit = element("button", {
    className: "button",
    text: "Register player",
    attributes: { type: "submit" },
  });
  submit.disabled = !players.length;
  select.disabled = !players.length;
  wrapper.append(label, select);
  form.append(wrapper, submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (select.value) {
      void pendingAction(submit, () => onRegister(Number(select.value)));
    }
  });
  return form;
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
        const registered = new Set(participants.map((item) => item.player_id));
        actionArea.append(
          registrationForm(
            players.filter((player) => !registered.has(player.id)),
            registerPlayer,
          ),
        );
        if (!players.length) {
          actionArea.append(
            element("p", {
              className: "muted",
              text: "Create a player in the player directory before registration.",
            }),
          );
        }
      }
      if (!participants.length) {
        result.replaceChildren(
          emptyState("No registered players", "The tournament roster is empty."),
        );
        return;
      }
      const columns = [{ key: "player_name", label: "Player" }];
      if (tournament.lifecycle === "draft") {
        columns.push({
          key: "registration_id",
          label: "Action",
          render: (registrationId, participant) => {
            const remove = element("button", {
              className: "button button-danger button-small",
              text: "Unregister",
              attributes: { type: "button" },
            });
            remove.addEventListener(
              "click",
              () => void pendingAction(remove, () => unregisterPlayer(registrationId, participant.player_name)),
              { signal },
            );
            return remove;
          },
        });
      }
      result.replaceChildren(
        table({ caption: "Registered players", columns, rows: participants }),
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
      await onChange?.();
    } catch (error) {
      if (!signal.aborted && error?.name !== "AbortError") {
        result.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  async function unregisterPlayer(registrationId, playerName) {
    if (!confirmAction(`Unregister ${playerName} from ${tournament.name}?`)) {
      return;
    }
    try {
      await api.delete(
        `/api/tournaments/${tournament.id}/participants/${registrationId}`,
        { signal },
      );
      await loadRegistration();
      await onChange?.();
    } catch (error) {
      if (!signal.aborted && error?.name !== "AbortError") {
        result.replaceChildren(status(errorSummary(error), "error"));
      }
    }
  }

  void loadRegistration();
  return card;
}
