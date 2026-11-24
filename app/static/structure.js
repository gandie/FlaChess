import { api } from "./api.js";
import {
  badge,
  confirmAction,
  element,
  emptyState,
  errorSummary,
  pendingAction,
  status,
} from "./render.js";

function labelFor(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function numberValue(control) {
  return control.value === "" ? null : Number(control.value);
}

function formField({
  id,
  label,
  value = "",
  type = "text",
  required = false,
  options = null,
}) {
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
  control.required = required;
  wrapper.append(control);
  return { wrapper, control };
}

function nextSequence(items) {
  return Math.max(0, ...items.map((item) => item.sequence)) + 1;
}

function nextSeedPosition(items) {
  return (
    Math.max(
      0,
      ...items.map((item) => item.seed_position).filter(Number.isFinite),
    ) + 1
  );
}

function setupDisclosure(title, content, open = false) {
  const details = element("details", { className: "setup-disclosure" });
  details.open = open;
  details.append(
    element("summary", { text: title }),
    content,
  );
  return details;
}

function earlierSections(context, section) {
  const phase = context.workspace.phases.find(
    (item) => item.sections.some((candidate) => candidate.id === section.id),
  );
  if (!phase) {
    return [];
  }
  return context.workspace.phases
    .filter((item) => item.sequence < phase.sequence)
    .flatMap((item) =>
      item.sections.map((candidate) => ({
        id: candidate.id,
        name: `Phase ${item.sequence}: ${candidate.name}`,
      })),
    );
}

function sourceSectionField(context, section, member = null) {
  return formField({
    id: `member_${member?.id ?? section.id}_source_section`,
    label: "Source section",
    value: member?.source_section_id ?? "",
    options: [
      ["", "Initial assignment"],
      ...earlierSections(context, section).map((candidate) => [
        candidate.id,
        candidate.name,
      ]),
    ],
  });
}

function sourceRankField(member = null, sectionId = null) {
  return formField({
    id: `member_${member?.id ?? sectionId}_source_rank`,
    label: "Source rank",
    type: "number",
    value: member?.source_rank ?? "",
  });
}

function writeForm({ fields, submitText, className = "structure-form", onWrite }) {
  const form = element("form", { className });
  const controls = fields();
  const button = element("button", {
    className: "button button-small",
    text: submitText,
    attributes: { type: "submit" },
  });
  const result = element("div", { className: "result-slot compact" });
  form.append(...controls.map((field) => field.wrapper), button, result);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void pendingAction(button, async () => {
      result.replaceChildren(status("Saving\u2026"));
      try {
        await onWrite(controls);
        result.replaceChildren();
      } catch (error) {
        if (error?.name !== "AbortError") {
          result.replaceChildren(status(errorSummary(error), "error"));
        }
      }
    });
  });
  return form;
}

function deleteButton({ text, message, onDelete }) {
  const button = element("button", {
    className: "button button-danger button-small",
    text,
    attributes: { type: "button" },
  });
  button.addEventListener("click", () => {
    if (confirmAction(message)) {
      void pendingAction(button, async () => {
        try {
          await onDelete();
        } catch (error) {
          if (error?.name !== "AbortError") {
            button.after(status(errorSummary(error), "error"));
          }
        }
      });
    }
  });
  return button;
}

function membershipActionButton(context, section, member) {
  const reentering = member.is_withdrawn;
  const action = reentering ? "re-enter" : "withdraw";
  const button = element("button", {
    className: "button button-secondary button-small",
    text: reentering ? "Re-enter" : "Withdraw",
    attributes: { type: "button" },
  });
  button.addEventListener("click", () => {
    if (
      confirmAction(
        `${reentering ? "Re-enter" : "Withdraw"} ${member.player_name} ${
          reentering ? "in" : "from"
        } ${section.name}? Historical results will remain unchanged.`,
      )
    ) {
      void pendingAction(button, async () => {
        try {
          await api.post(
            `/api/section-participants/${member.id}/${action}`,
            {},
            { signal: context.signal },
          );
          await context.refresh();
        } catch (error) {
          if (error?.name !== "AbortError") {
            button.after(status(errorSummary(error), "error"));
          }
        }
      });
    }
  });
  return button;
}

function phaseEditor(context, phase) {
  const form = writeForm({
    fields: () => {
      const sequence = formField({
        id: `phase_${phase.id}_sequence`,
        label: "Order",
        type: "number",
        value: phase.sequence,
        required: true,
      });
      sequence.control.min = "1";
      const format = formField({
        id: `phase_${phase.id}_format`,
        label: "Format",
        value: phase.format,
        options: [
          ["swiss", "Swiss"],
          ["round_robin", "Round robin"],
          ["knockout", "Knockout"],
        ],
        required: true,
      });
      return [sequence, format];
    },
    submitText: "Save phase",
    onWrite: async ([sequence, format]) => {
      await api.patch(
        `/api/tournament-phases/${phase.id}`,
        { sequence: numberValue(sequence.control), format: format.control.value },
        { signal: context.signal },
      );
      await context.refresh();
    },
  });
  form.append(
    deleteButton({
      text: "Delete phase",
      message: `Delete phase ${phase.sequence} and all of its sections?`,
      onDelete: async () => {
        await api.delete(`/api/tournament-phases/${phase.id}`, {
          signal: context.signal,
        });
        await context.refresh();
      },
    }),
  );
  return form;
}

function phaseCreator(context) {
  return writeForm({
    fields: () => {
      const sequence = formField({
        id: "new_phase_sequence",
        label: "Phase order",
        type: "number",
        value: nextSequence(context.workspace.phases),
        required: true,
      });
      sequence.control.min = "1";
      const format = formField({
        id: "new_phase_format",
        label: "Format",
        value: "swiss",
        options: [
          ["swiss", "Swiss"],
          ["round_robin", "Round robin"],
          ["knockout", "Knockout"],
        ],
        required: true,
      });
      return [sequence, format];
    },
    submitText: "Add phase",
    onWrite: async ([sequence, format]) => {
      await api.post(
        "/api/tournament-phases",
        {
          tournament_id: context.workspace.id,
          sequence: numberValue(sequence.control),
          format: format.control.value,
        },
        { signal: context.signal },
      );
      await context.refresh();
    },
  });
}

function sectionEditor(context, section) {
  const form = writeForm({
    fields: () => {
      const name = formField({
        id: `section_${section.id}_name`,
        label: "Section name",
        value: section.name,
        required: true,
      });
      name.control.maxLength = 255;
      const sequence = formField({
        id: `section_${section.id}_sequence`,
        label: "Order",
        type: "number",
        value: section.sequence,
        required: true,
      });
      sequence.control.min = "1";
      const rounds = formField({
        id: `section_${section.id}_rounds`,
        label: "Planned rounds",
        type: "number",
        value: section.planned_round_count ?? "",
      });
      rounds.control.min = "1";
      return [name, sequence, rounds];
    },
    submitText: "Save section",
    onWrite: async ([name, sequence, rounds]) => {
      await api.patch(
        `/api/tournament-sections/${section.id}`,
        {
          name: name.control.value.trim(),
          sequence: numberValue(sequence.control),
          planned_round_count: numberValue(rounds.control),
        },
        { signal: context.signal },
      );
      await context.refresh();
    },
  });
  form.append(
    deleteButton({
      text: "Delete section",
      message: `Delete ${section.name} and its section configuration?`,
      onDelete: async () => {
        await api.delete(`/api/tournament-sections/${section.id}`, {
          signal: context.signal,
        });
        await context.refresh();
      },
    }),
  );
  return form;
}

function sectionCreator(context, phase) {
  return writeForm({
    fields: () => {
      const name = formField({
        id: `new_section_${phase.id}_name`,
        label: "Section name",
        required: true,
      });
      name.control.maxLength = 255;
      const sequence = formField({
        id: `new_section_${phase.id}_sequence`,
        label: "Section order",
        type: "number",
        value: nextSequence(phase.sections),
        required: true,
      });
      sequence.control.min = "1";
      const rounds = formField({
        id: `new_section_${phase.id}_rounds`,
        label: "Planned rounds",
        type: "number",
      });
      rounds.control.min = "1";
      return [name, sequence, rounds];
    },
    submitText: "Add section",
    onWrite: async ([name, sequence, rounds]) => {
      await api.post(
        "/api/tournament-sections",
        {
          phase_id: phase.id,
          name: name.control.value.trim(),
          sequence: numberValue(sequence.control),
          planned_round_count: numberValue(rounds.control),
        },
        { signal: context.signal },
      );
      await context.refresh();
    },
  });
}

function membershipEditor(context, section, member) {
  const row = element("div", { className: "member-row" });
  if (!context.membershipEditable) {
    row.append(element("strong", { text: member.player_name }));
    const provenance = member.source_section_id
      ? `Advanced from ${member.source_section_name ?? "a previous section"}${
          member.source_rank ? ` at rank ${member.source_rank}` : ""
        }`
      : "Initial assignment";
    row.append(
      element("span", {
        className: "muted",
        text: `Seed ${member.seed_position ?? "not set"} · ${
          member.rating
            ? `${member.rating}${member.rating_source ? ` ${member.rating_source}` : ""}`
            : "Unrated"
        } · ${provenance} · ${
          member.is_withdrawn ? "Withdrawn" : "Eligible"
        }`,
      }),
    );
    if (context.membershipActions) {
      row.append(membershipActionButton(context, section, member));
    }
    return row;
  }
  const form = writeForm({
    fields: () => {
      const rating = formField({
        id: `member_${member.id}_rating`,
        label: "Rating",
        type: "number",
        value: member.rating ?? "",
      });
      rating.control.min = "1";
      const source = formField({
        id: `member_${member.id}_source`,
        label: "Rating source",
        value: member.rating_source ?? "",
      });
      source.control.maxLength = 64;
      const seed = formField({
        id: `member_${member.id}_seed`,
        label: "Seed position",
        type: "number",
        value: member.seed_position ?? "",
      });
      seed.control.min = "1";
      const sourceSection = sourceSectionField(context, section, member);
      const sourceRank = sourceRankField(member);
      sourceRank.control.min = "1";
      return [rating, source, seed, sourceSection, sourceRank];
    },
    submitText: "Save membership",
    className: "structure-form inline-form",
    onWrite: async ([rating, source, seed, sourceSection, sourceRank]) => {
      await api.patch(
        `/api/section-participants/${member.id}`,
        {
          rating: numberValue(rating.control),
          rating_source: source.control.value.trim() || null,
          seed_position: numberValue(seed.control),
          source_section_id: numberValue(sourceSection.control),
          source_rank: numberValue(sourceRank.control),
        },
        { signal: context.signal },
      );
      await context.refresh();
    },
  });
  form.append(
    deleteButton({
      text: "Remove",
      message: `Remove ${member.player_name} from ${section.name}?`,
      onDelete: async () => {
        await api.delete(`/api/section-participants/${member.id}`, {
          signal: context.signal,
        });
        await context.refresh();
      },
    }),
  );
  if (context.membershipActions) {
    form.append(membershipActionButton(context, section, member));
  }
  row.append(
    setupDisclosure(
      `${member.player_name} · seed ${member.seed_position ?? "not set"} · ${
        member.rating ?? "unrated"
      }`,
      form,
    ),
  );
  return row;
}

function membershipAssignmentRow(context, section, participant, suggestedSeed) {
  const form = element("form", { className: "membership-assignment-row" });
  const seed = formField({
    id: `section_${section.id}_participant_${participant.registration_id}_seed`,
    label: "Seed",
    type: "number",
    value: suggestedSeed,
    required: true,
  });
  seed.control.min = "1";
  seed.control.dataset.generatedSeed = "true";
  seed.control.addEventListener("input", () => {
    seed.control.dataset.userEdited = "true";
  });
  const advanced = element("details", { className: "inline-disclosure" });
  advanced.append(element("summary", { text: "Advancement details" }));
  const assignmentKey = `registration_${participant.registration_id}`;
  const sourceSection = sourceSectionField(context, section, { id: assignmentKey });
  const sourceRank = sourceRankField({ id: assignmentKey });
  sourceRank.control.min = "1";
  advanced.append(sourceSection.wrapper, sourceRank.wrapper);
  const submit = element("button", {
    className: "button button-secondary button-small",
    text: "+ Add",
    attributes: {
      type: "submit",
      "aria-label": `Add ${participant.player_name} to ${section.name}`,
    },
  });
  const identity = element("div", { className: "player-identity" });
  identity.append(
    element("span", {
      className: "player-monogram",
      text: participant.player_name
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part.charAt(0).toUpperCase())
        .join(""),
      attributes: { "aria-hidden": "true" },
    }),
    element("strong", { text: participant.player_name }),
  );
  const result = element("div", { className: "result-slot compact" });
  form.append(identity, seed.wrapper, submit, advanced, result);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void pendingAction(submit, async () => {
      result.replaceChildren(status("Adding player\u2026"));
      try {
        await api.post(
          "/api/section-participants",
          {
            participant_id: participant.registration_id,
            section_id: section.id,
            rating: null,
            rating_source: null,
            seed_position: numberValue(seed.control),
            source_section_id: numberValue(sourceSection.control),
            source_rank: numberValue(sourceRank.control),
          },
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
  return form;
}

function membershipPanel(context, section) {
  const panel = element("div", { className: "structure-panel" });
  panel.append(element("h4", { text: "Section membership and ratings" }));
  if (section.participants.length) {
    panel.append(...section.participants.map((member) =>
      membershipEditor(context, section, member),
    ));
  } else {
    panel.append(emptyState("No section members", "Assign registered players."));
  }
  if (!context.membershipEditable) {
    return panel;
  }
  const assigned = new Set(
    section.participants.map((member) => member.registration_id),
  );
  const available = context.workspace.participants.filter(
    (participant) => !assigned.has(participant.registration_id),
  );
  if (!available.length) {
    panel.append(
      element("p", {
        className: "muted",
        text: "Every registered player is already assigned to this section.",
      }),
    );
    return panel;
  }
  const nextSeed = nextSeedPosition(section.participants);
  const assignment = element("div", { className: "player-action-list" });
  const heading = element("div", { className: "list-heading" });
  heading.append(
    element("h5", { text: "Available registered players" }),
    element("span", {
      className: "count-label",
      text: `Next seed ${nextSeed}`,
    }),
  );
  assignment.append(
    heading,
    ...available.map((participant) =>
      membershipAssignmentRow(context, section, participant, nextSeed),
    ),
  );
  panel.append(assignment);
  return panel;
}

function tieBreakRow(context, section, rule) {
  const row = element("div", { className: "tiebreak-row" });
  const summary = element("div");
  summary.append(
    element("strong", {
      text: `${rule.sequence}. ${labelFor(rule.code)}`,
    }),
    element("p", {
      className: "muted",
      text: `${rule.code}${rule.parameter ? ` (${rule.parameter})` : ""}`,
    }),
    badge(rule.supported ? "Supported" : "Unsupported", rule.supported ? "success" : "neutral"),
    badge(rule.is_active ? "Active" : "Inactive", rule.is_active ? "success" : "accent"),
  );
  row.append(summary);
  if (!context.editable || section.tie_break_locked_at) {
    return row;
  }
  const form = writeForm({
    fields: () => {
      const sequence = formField({
        id: `rule_${rule.id}_sequence`,
        label: "Order",
        type: "number",
        value: rule.sequence,
        required: true,
      });
      sequence.control.min = "1";
      const parameter = formField({
        id: `rule_${rule.id}_parameter`,
        label: "Parameter",
        value: rule.parameter ?? "",
      });
      parameter.control.maxLength = 255;
      const active = formField({
        id: `rule_${rule.id}_active`,
        label: "Status",
        value: String(rule.is_active),
        options: [
          ["true", "Active"],
          ["false", "Inactive"],
        ],
        required: true,
      });
      return [sequence, parameter, active];
    },
    submitText: "Save order",
    className: "structure-form inline-form",
    onWrite: async ([sequence, parameter, active]) => {
      await api.patch(
        `/api/section-tiebreaks/${rule.id}`,
        {
          sequence: numberValue(sequence.control),
          parameter: parameter.control.value.trim() || null,
          is_active: active.control.value === "true",
        },
        { signal: context.signal },
      );
      await context.refresh();
    },
  });
  form.append(
    deleteButton({
      text: "Remove",
      message: `Remove ${labelFor(rule.code)} from ${section.name}?`,
      onDelete: async () => {
        await api.delete(`/api/section-tiebreaks/${rule.id}`, {
          signal: context.signal,
        });
        await context.refresh();
      },
    }),
  );
  row.append(form);
  return row;
}

function tieBreakPanel(context, section) {
  const locked = Boolean(section.tie_break_locked_at);
  const panel = element("div", { className: "structure-panel" });
  panel.append(
    element("h4", { text: "Ordered tie-break rules" }),
    status(
      locked
        ? "Tie-break configuration is locked for this section."
        : "Only standings-supported codes can be added.",
      locked ? "warning" : "neutral",
    ),
  );
  if (section.tiebreaks.length) {
    panel.append(...section.tiebreaks.map((rule) =>
      tieBreakRow(context, section, rule),
    ));
  } else {
    panel.append(emptyState("No tie-break rules", "No rules are configured."));
  }
  if (!context.editable || locked) {
    return panel;
  }
  panel.append(
    writeForm({
      fields: () => {
        const code = formField({
          id: `section_${section.id}_tiebreak`,
          label: "Supported code",
          options: context.workspace.supported_tiebreak_codes.map((value) => [
            value,
            labelFor(value),
          ]),
          required: true,
        });
        const sequence = formField({
          id: `section_${section.id}_tiebreak_sequence`,
          label: "Order",
          type: "number",
          value: nextSequence(section.tiebreaks),
          required: true,
        });
        sequence.control.min = "1";
        const parameter = formField({
          id: `section_${section.id}_tiebreak_parameter`,
          label: "Parameter",
        });
        parameter.control.maxLength = 255;
        return [code, sequence, parameter];
      },
      submitText: "Add tie-break",
      onWrite: async ([code, sequence, parameter]) => {
        await api.post(
          "/api/section-tiebreaks",
          {
            section_id: section.id,
            code: code.control.value,
            sequence: numberValue(sequence.control),
            parameter: parameter.control.value.trim() || null,
            is_active: true,
          },
          { signal: context.signal },
        );
        await context.refresh();
      },
    }),
  );
  return panel;
}

function sectionCard(context, section) {
  const sectionContext = {
    ...context,
    editable: context.editable && section.lifecycle === "draft",
    membershipEditable:
      context.workspace.lifecycle !== "finished" &&
      section.lifecycle === "draft",
    membershipActions:
      context.workspace.lifecycle !== "finished" &&
      section.lifecycle !== "finished",
  };
  const card = element("article", { className: "section-card" });
  card.append(
    badge(labelFor(section.lifecycle), section.lifecycle === "draft" ? "accent" : "neutral"),
    element("h3", { text: `${section.sequence}. ${section.name}` }),
    element("p", {
      className: "muted",
      text: section.planned_round_count
        ? `${section.planned_round_count} planned rounds`
        : "Planned round count not set",
    }),
  );
  card.append(
    element("a", {
      className: "button button-secondary button-small",
      text:
        section.lifecycle === "finished"
          ? "Review final standings"
          : "Open section operation",
      attributes: {
        href: `#/tournaments/${context.workspace.id}/sections/${section.id}`,
      },
    }),
  );
  if (context.editable && section.lifecycle === "draft") {
    card.append(setupDisclosure("Edit section details", sectionEditor(context, section)));
  }
  const membership = membershipPanel(sectionContext, section);
  card.append(
    context.workspace.lifecycle === "draft"
      ? setupDisclosure(
          `Section roster and assignments (${section.participants.length} assigned)`,
          membership,
        )
      : membership,
    setupDisclosure("Tie-break rules", tieBreakPanel(sectionContext, section)),
  );
  return card;
}

function phaseCard(context, phase) {
  const card = element("section", { className: "phase-card" });
  card.append(
    element("h3", { text: `Phase ${phase.sequence}: ${labelFor(phase.format)}` }),
  );
  if (context.editable) {
    card.append(setupDisclosure("Edit phase", phaseEditor(context, phase)));
  }
  const sections = element("div", { className: "section-list" });
  sections.append(
    ...(phase.sections.length
      ? phase.sections.map((section) => sectionCard(context, section))
      : [emptyState("No sections", "Add a section to this phase.")]),
  );
  card.append(sections);
  if (context.editable) {
    const creator = element("div", { className: "structure-panel" });
    creator.append(sectionCreator(context, phase));
    card.append(setupDisclosure("Add another section", creator));
  }
  return card;
}

function readinessCard(readiness) {
  const card = element("section", { className: "card readiness-card" });
  card.append(
    badge(readiness.can_activate ? "Ready to activate" : "Setup needed",
      readiness.can_activate ? "success" : "accent"),
    element("h2", { text: "Draft readiness" }),
  );
  for (const issue of readiness.blocking_issues) {
    card.append(status(issue, "error"));
  }
  for (const warning of readiness.setup_warnings) {
    card.append(status(warning, "warning"));
  }
  if (!readiness.blocking_issues.length && !readiness.setup_warnings.length) {
    card.append(status("No missing draft setup items were found.", "success"));
  }
  return card;
}

export function tournamentStructureCards(workspace, signal, refresh) {
  const context = {
    workspace,
    signal,
    refresh,
    editable: workspace.lifecycle === "draft",
  };
  const wrapper = element("div", { className: "workspace-structure" });
  if (workspace.lifecycle === "draft") {
    wrapper.append(readinessCard(workspace.readiness));
  }
  const phasesCard = element("section", { className: "card structure-card" });
  phasesCard.append(
    badge(context.editable ? "Draft configuration" : "Structure history", "accent"),
    element("h2", { text: "Phases and sections" }),
  );
  if (workspace.phases.length) {
    phasesCard.append(...workspace.phases.map((phase) => phaseCard(context, phase)));
  } else {
    phasesCard.append(emptyState("No phases", "Add the first phase."));
  }
  if (context.editable) {
    const creator = element("div", { className: "structure-panel" });
    creator.append(phaseCreator(context));
    phasesCard.append(setupDisclosure("Add another phase", creator));
  }
  wrapper.append(phasesCard);
  return wrapper;
}
