import { ApiError } from "./api.js";

export function element(tag, { className = "", text, attributes = {} } = {}) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined) {
    node.textContent = text;
  }
  for (const [name, value] of Object.entries(attributes)) {
    node.setAttribute(name, value);
  }
  return node;
}

export function page({ eyebrow, title, description, actions = [] }) {
  const section = element("section", { className: "page" });
  const headingGroup = element("div", { className: "page-heading" });
  const copy = element("div");

  if (eyebrow) {
    copy.append(element("p", { className: "eyebrow", text: eyebrow }));
  }
  const heading = element("h1", { text: title });
  heading.id = "page-title";
  heading.tabIndex = -1;
  copy.append(heading);

  if (description) {
    copy.append(element("p", { className: "page-description", text: description }));
  }

  headingGroup.append(copy);
  if (actions.length) {
    const actionGroup = element("div", { className: "action-group" });
    actionGroup.append(...actions);
    headingGroup.append(actionGroup);
  }
  section.append(headingGroup);
  return section;
}

export function status(message, tone = "neutral") {
  const node = element("div", {
    className: `status status-${tone}`,
    text: message,
  });
  node.setAttribute("role", "status");
  return node;
}

export function emptyState(title, message) {
  const node = element("div", { className: "empty-state" });
  node.append(
    element("h2", { text: title }),
    element("p", { text: message }),
  );
  return node;
}

export function field({
  id,
  label,
  type = "text",
  value = "",
  help = "",
  error = "",
}) {
  const wrapper = element("div", { className: "field" });
  wrapper.append(element("label", { text: label, attributes: { for: id } }));
  const control = element("input", {
    attributes: { id, name: id, type, value },
  });
  control.classList.toggle("field-invalid", Boolean(error));
  if (error) {
    control.setAttribute("aria-invalid", "true");
  }
  wrapper.append(control);
  if (help) {
    wrapper.append(element("p", { className: "field-help", text: help }));
  }
  if (error) {
    wrapper.append(element("p", { className: "field-error", text: error }));
  }
  return { wrapper, control };
}

export function table({ caption, columns, rows, emptyMessage = "Nothing to show." }) {
  const wrapper = element("div", { className: "table-wrap" });
  if (!rows.length) {
    wrapper.append(emptyState("No records", emptyMessage));
    return wrapper;
  }

  const tableNode = element("table");
  tableNode.append(element("caption", { className: "sr-only", text: caption }));
  const headRow = element("tr");
  for (const column of columns) {
    headRow.append(
      element("th", {
        text: column.label,
        attributes: { scope: "col" },
      }),
    );
  }
  const head = element("thead");
  head.append(headRow);
  const body = element("tbody");
  for (const row of rows) {
    const tableRow = element("tr");
    for (const column of columns) {
      const value = column.render ? column.render(row[column.key], row) : row[column.key];
      tableRow.append(
        value instanceof Node
          ? (() => {
              const cell = element("td");
              cell.append(value);
              return cell;
            })()
          : element("td", { text: value ?? "" }),
      );
    }
    body.append(tableRow);
  }
  tableNode.append(head, body);
  wrapper.append(tableNode);
  return wrapper;
}

export function badge(label, tone = "neutral") {
  return element("span", {
    className: `badge badge-${tone}`,
    text: label,
  });
}

export function confirmAction(message) {
  return window.confirm(message);
}

export async function pendingAction(button, operation) {
  const originalText = button.textContent;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.textContent = "Working\u2026";
  try {
    return await operation();
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.textContent = originalText;
  }
}

export function errorSummary(error) {
  if (error instanceof ApiError) {
    let message = error.message;
    if (typeof error.detail === "string") {
      message = `${message} ${error.detail}`;
    } else if (Array.isArray(error.detail)) {
      const details = error.detail
        .map((item) => item?.msg)
        .filter(Boolean)
        .join("; ");
      if (details) {
        message = `${message} ${details}`;
      }
    }
    return error.status ? `${message} (HTTP ${error.status})` : message;
  }
  return "The page could not be loaded.";
}
