import { api } from "./api.js";
import {
  badge,
  element,
  emptyState,
  errorSummary,
  field,
  page,
  pendingAction,
  status,
  table,
} from "./render.js";

function lifecycleBadge(lifecycle) {
  const tones = {
    draft: "accent",
    active: "success",
    finished: "neutral",
  };
  return badge(
    lifecycle.charAt(0).toUpperCase() + lifecycle.slice(1),
    tones[lifecycle] ?? "neutral",
  );
}

function formatDate(value) {
  if (!value) {
    return "Not scheduled";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function localDateTime(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function formValues(form) {
  const startsAt = form.elements.starts_at.value;
  const endsAt = form.elements.ends_at.value;
  return {
    name: form.elements.tournament_name.value.trim(),
    description: form.elements.description.value.trim() || null,
    time_control: form.elements.time_control.value.trim() || null,
    starts_at: startsAt ? new Date(startsAt).toISOString() : null,
    ends_at: endsAt ? new Date(endsAt).toISOString() : null,
  };
}

function metadataForm(tournament = {}) {
  const form = element("form", { className: "form-stack" });
  const name = field({
    id: "tournament_name",
    label: "Tournament name",
    value: tournament.name ?? "",
  });
  name.control.required = true;
  name.control.maxLength = 255;
  const timeControl = field({
    id: "time_control",
    label: "Time control",
    value: tournament.time_control ?? "",
    help: "Optional, for example 90 min + 30 sec.",
  });
  timeControl.control.maxLength = 255;
  const description = field({
    id: "description",
    label: "Description",
    value: tournament.description ?? "",
  });
  const startsAt = field({
    id: "starts_at",
    label: "Starts",
    type: "datetime-local",
    value: localDateTime(tournament.starts_at),
  });
  const endsAt = field({
    id: "ends_at",
    label: "Ends",
    type: "datetime-local",
    value: localDateTime(tournament.ends_at),
  });
  const dates = element("div", { className: "form-grid" });
  dates.append(startsAt.wrapper, endsAt.wrapper);
  form.append(
    name.wrapper,
    description.wrapper,
    timeControl.wrapper,
    dates,
  );
  return { form, values: () => formValues(form) };
}

export function tournamentCatalogView(navigate) {
  const root = page({
    eyebrow: "Tournament operations",
    title: "Tournaments",
    description:
      "Review the tournament catalog and create a draft tournament.",
  });
  const layout = element("div", { className: "catalog-layout" });
  const catalogCard = element("section", { className: "card" });
  catalogCard.append(element("h2", { text: "Tournament catalog" }));
  const catalogResult = element("div", { className: "result-slot" });
  catalogCard.append(catalogResult);

  const createCard = element("section", { className: "card" });
  createCard.append(
    badge("Draft creation", "accent"),
    element("h2", { text: "New tournament" }),
    element("p", {
      className: "muted",
      text: "Only tournament metadata is collected at this step.",
    }),
  );
  const { form, values } = metadataForm();
  const submit = element("button", {
    className: "button",
    text: "Create draft",
    attributes: { type: "submit" },
  });
  const createResult = element("div", { className: "result-slot" });
  form.append(submit, createResult);
  createCard.append(form);
  layout.append(catalogCard, createCard);
  root.append(layout);

  async function loadCatalog(signal) {
    catalogResult.replaceChildren(status("Loading tournaments\u2026"));
    try {
      const tournaments = await api.get("/api/tournament-summaries", { signal });
      if (!tournaments.length) {
        catalogResult.replaceChildren(
          emptyState(
            "No tournaments",
            "Create the first draft tournament to begin.",
          ),
        );
        return;
      }
      catalogResult.replaceChildren(
        table({
          caption: "Tournament catalog",
          columns: [
            {
              key: "name",
              label: "Tournament",
              render: (name, tournament) => {
                const link = element("a", {
                  text: name,
                  attributes: { href: `#/tournaments/${tournament.id}` },
                });
                link.className = "record-link";
                return link;
              },
            },
            {
              key: "lifecycle",
              label: "Status",
              render: (lifecycle) => lifecycleBadge(lifecycle),
            },
            { key: "starts_at", label: "Starts", render: formatDate },
            { key: "ends_at", label: "Ends", render: formatDate },
            {
              key: "participant_count",
              label: "Players",
            },
            {
              key: "phase_count",
              label: "Phases",
            },
            {
              key: "section_count",
              label: "Sections",
            },
          ],
          rows: tournaments,
        }),
      );
    } catch (error) {
      if (signal.aborted || error?.name === "AbortError") {
        return;
      }
      catalogResult.replaceChildren(status(errorSummary(error), "error"));
    }
  }

  return {
    title: "Tournaments",
    element: root,
    activate({ signal }) {
      form.addEventListener(
        "submit",
        (event) => {
          event.preventDefault();
          void pendingAction(submit, async () => {
            createResult.replaceChildren(status("Creating draft\u2026"));
            try {
              const tournament = await api.post(
                "/api/tournaments",
                values(),
                { signal },
              );
              navigate(`/tournaments/${tournament.id}`);
            } catch (error) {
              if (signal.aborted || error?.name === "AbortError") {
                return;
              }
              createResult.replaceChildren(
                status(errorSummary(error), "error"),
              );
            }
          });
        },
        { signal },
      );
      void loadCatalog(signal);
    },
  };
}

export function tournamentOverviewView({ tournamentId }) {
  const root = page({
    eyebrow: "Tournament overview",
    title: "Tournament",
    description: "Review lifecycle and tournament metadata.",
  });
  const result = element("div", { className: "result-slot" });
  root.append(result);

  function renderTournament(tournament, signal) {
    result.replaceChildren();
    const card = element("section", { className: "card" });
    const title = element("h2", { text: tournament.name });
    card.append(lifecycleBadge(tournament.lifecycle), title);
    if (tournament.lifecycle !== "draft") {
      card.append(
        status("This tournament is read-only outside draft state.", "warning"),
        element("dl", { className: "detail-list" }),
      );
      const details = card.lastElementChild;
      for (const [label, value] of [
        ["Description", tournament.description || "No description"],
        ["Time control", tournament.time_control || "Not specified"],
        ["Starts", formatDate(tournament.starts_at)],
        ["Ends", formatDate(tournament.ends_at)],
      ]) {
        details.append(
          element("dt", { text: label }),
          element("dd", { text: value }),
        );
      }
      result.append(card);
      return;
    }

    card.append(
      status("Draft metadata can be edited.", "success"),
      element("p", {
        className: "muted",
        text: "Changes are saved through the backend tournament contract.",
      }),
    );
    const { form, values } = metadataForm(tournament);
    const submit = element("button", {
      className: "button",
      text: "Save metadata",
      attributes: { type: "submit" },
    });
    const updateResult = element("div", { className: "result-slot" });
    form.append(submit, updateResult);
    form.addEventListener(
      "submit",
      (event) => {
        event.preventDefault();
        void pendingAction(submit, async () => {
          updateResult.replaceChildren(status("Saving metadata\u2026"));
          try {
            await api.patch(`/api/tournaments/${tournamentId}`, values(), {
              signal,
            });
            await loadTournament(signal);
          } catch (error) {
            if (signal.aborted || error?.name === "AbortError") {
              return;
            }
            updateResult.replaceChildren(status(errorSummary(error), "error"));
          }
        });
      },
      { signal },
    );
    card.append(form);
    result.append(card);
  }

  async function loadTournament(signal) {
    result.replaceChildren(status("Loading tournament\u2026"));
    try {
      const tournament = await api.get(
        `/api/tournaments/${tournamentId}`,
        { signal },
      );
      renderTournament(tournament, signal);
    } catch (error) {
      if (signal.aborted || error?.name === "AbortError") {
        return;
      }
      result.replaceChildren(status(errorSummary(error), "error"));
    }
  }

  return {
    title: "Tournament overview",
    element: root,
    activate({ signal }) {
      void loadTournament(signal);
    },
  };
}
