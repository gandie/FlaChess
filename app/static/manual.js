import { element, page } from "./render.js";

const tieBreaks = [
  {
    code: "direct_encounter",
    name: "Direct encounter",
    family: "Between tied players",
    summary:
      "Count the points scored in completed games against players who are still tied at this stage.",
    method:
      "Start a mini-table using only that tied group. Add the score each player earned against the others; a win is 1, a draw is 0.5, and a loss is 0.",
    example: {
      facts: "A, B, and C remain tied. A beat B and drew C.",
      calculation: "A: 1 + 0.5 = 1.5 · B: 0 · C: 0.5",
      result: "A has the highest direct-encounter value: 1.5.",
    },
  },
  {
    code: "number_of_wins",
    name: "Number of wins",
    family: "Results",
    summary: "Count completed games won, ignoring draws and losses.",
    method:
      "Add one for every completed game in which the player scored more points than the opponent. Awarded non-paired round points do not count as wins.",
    example: {
      facts: "D finishes with W-W-D-L-W-D.",
      calculation: "D: 1 + 1 + 0 + 0 + 1 + 0 = 3",
      result: "D’s number of wins is 3.",
    },
  },
  {
    code: "progressive_score",
    name: "Progressive score",
    family: "Timing",
    summary:
      "Add the player’s running total after every round, including awarded non-paired points.",
    method:
      "Read rounds in number order. After each round, note the total points so far, then add those running totals together. Earlier scoring produces a larger value.",
    example: {
      facts: "E scores 1, 0.5, 1, 0 across four rounds.",
      calculation: "Running totals: 1, 1.5, 2.5, 2.5 → 1 + 1.5 + 2.5 + 2.5 = 7.5",
      result: "E’s progressive score is 7.5.",
    },
  },
  {
    code: "buchholz",
    name: "Buchholz",
    family: "Opponent strength",
    summary: "Add the final total points of every completed-game opponent.",
    method:
      "For each opponent in a completed game, take that opponent’s final tournament points and add them. A repeated opponent contributes again for the repeated game. Non-paired awards add no opponent.",
    example: {
      facts: "F’s four opponents finish on 5.5, 4, 3, and 2.5 points.",
      calculation: "5.5 + 4 + 3 + 2.5 = 15",
      result: "F’s Buchholz value is 15.",
    },
  },
  {
    code: "buchholz_cut_1",
    name: "Buchholz Cut-1",
    family: "Opponent strength",
    summary:
      "Use Buchholz, but remove the contribution from the lowest-scoring opponent.",
    method:
      "Sort the opponent point totals from lowest to highest, discard the first value, and add the rest. With no values left after the cut, the value is 0.",
    example: {
      facts: "F’s opponents finish on 5.5, 4, 3, and 2.5 points.",
      calculation: "Remove 2.5 → 3 + 4 + 5.5 = 12.5",
      result: "F’s Buchholz Cut-1 value is 12.5.",
    },
  },
  {
    code: "buchholz_cut_2",
    name: "Buchholz Cut-2",
    family: "Opponent strength",
    summary:
      "Use Buchholz, but remove the contributions from the two lowest-scoring opponents.",
    method:
      "Sort the opponent point totals from lowest to highest, discard the first two values, and add the rest. With no values left after the cuts, the value is 0.",
    example: {
      facts: "G’s opponents finish on 5.5, 4, 3, and 2.5 points.",
      calculation: "Remove 2.5 and 3 → 4 + 5.5 = 9.5",
      result: "G’s Buchholz Cut-2 value is 9.5.",
    },
  },
  {
    code: "buchholz_median_1",
    name: "Buchholz Median-1",
    family: "Opponent strength",
    summary:
      "Use Buchholz after removing both the lowest- and highest-scoring opponent.",
    method:
      "Sort the opponent point totals, discard one value from each end, and add the remaining values. With no values left after the cuts, the value is 0.",
    example: {
      facts: "H’s opponents finish on 2, 3.5, 4, 5, and 5.5 points.",
      calculation: "Remove 2 and 5.5 → 3.5 + 4 + 5 = 12.5",
      result: "H’s Buchholz Median-1 value is 12.5.",
    },
  },
  {
    code: "buchholz_median_2",
    name: "Buchholz Median-2",
    family: "Opponent strength",
    summary:
      "Use Buchholz after removing the two lowest and two highest opponent totals.",
    method:
      "Sort the opponent point totals, discard two values from each end, and add the remaining values. With no values left after the cuts, the value is 0.",
    example: {
      facts: "I’s opponents finish on 1, 2.5, 4, 4.5, 5, and 6 points.",
      calculation: "Remove 1, 2.5, 5, 6 → 4 + 4.5 = 8.5",
      result: "I’s Buchholz Median-2 value is 8.5.",
    },
  },
  {
    code: "sonneborn_berger",
    name: "Sonneborn-Berger",
    family: "Result-weighted strength",
    summary:
      "Multiply each completed-game opponent’s final points by the score earned against that opponent.",
    method:
      "For every completed game, multiply opponent final points by 1 for a win, 0.5 for a draw, or 0 for a loss. Add all contributions.",
    example: {
      facts: "J beats a 5-point player, draws a 4-point player, and loses to a 3-point player.",
      calculation: "(5 × 1) + (4 × 0.5) + (3 × 0) = 7",
      result: "J’s Sonneborn-Berger value is 7.",
    },
  },
  {
    code: "sonneborn_berger_cut_1",
    name: "Sonneborn-Berger Cut-1",
    family: "Result-weighted strength",
    summary:
      "Use Sonneborn-Berger, but remove the lowest game contribution.",
    method:
      "Calculate each game contribution as opponent points multiplied by the earned score. Sort the contributions, discard the smallest one, and add the rest.",
    example: {
      facts: "J’s Sonneborn-Berger contributions are 5, 2, and 0.",
      calculation: "Remove 0 → 5 + 2 = 7",
      result: "J’s Sonneborn-Berger Cut-1 value is 7.",
    },
  },
];

function tieBreakArticle(tieBreak, index) {
  const article = element("article", {
    className: "manual-rule",
    attributes: { id: tieBreak.code, tabindex: "-1" },
  });
  const heading = element("div", { className: "manual-rule-heading" });
  heading.append(
    element("span", {
      className: "manual-rule-number",
      text: String(index + 1).padStart(2, "0"),
      attributes: { "aria-hidden": "true" },
    }),
    element("div", {}),
  );
  const titleGroup = heading.lastElementChild;
  titleGroup.append(
    element("span", {
      className: "manual-rule-family",
      text: tieBreak.family,
    }),
    element("h3", { text: tieBreak.name }),
    element("code", { className: "manual-rule-code", text: tieBreak.code }),
  );

  const explanation = element("div", { className: "manual-rule-copy" });
  explanation.append(
    element("p", { className: "manual-rule-summary", text: tieBreak.summary }),
    element("p", { text: tieBreak.method }),
  );

  const example = element("div", { className: "manual-example" });
  example.append(
    element("span", { className: "manual-example-label", text: "Worked example" }),
    element("p", { text: tieBreak.example.facts }),
    element("p", { className: "manual-calculation", text: tieBreak.example.calculation }),
    element("strong", { text: tieBreak.example.result }),
  );

  article.append(heading, explanation, example);
  return article;
}

export function manualView() {
  const root = page({
    eyebrow: "Operator field guide",
    title: "Manual",
    description:
      "Explain the standings table from the raw scores. This page mirrors every tie-break currently supported by Fla Chess.",
  });
  root.classList.add("manual-page");

  const orientation = element("section", {
    className: "manual-orientation",
    attributes: { "aria-labelledby": "manual-reading-order" },
  });
  orientation.append(
    element("div", { className: "manual-orientation-copy" }),
    element("nav", {
      className: "manual-contents",
      attributes: { "aria-label": "Manual chapters" },
    }),
  );
  orientation.firstElementChild.append(
    element("p", {
      className: "manual-kicker",
      text: "Chapter 01 · Tie-breaks",
    }),
    element("h2", {
      text: "Read the board in the configured order.",
      attributes: { id: "manual-reading-order" },
    }),
    element("p", {
      text: "Players are compared by points first. Only players still tied move to the next configured rule. Higher tie-break values rank ahead; if every value is equal, the tie remains.",
    }),
  );
  orientation.lastElementChild.append(
    element("strong", { text: "In this chapter" }),
    element("a", {
      text: "Tie-break order",
      attributes: {
        href: "#/manual",
        "data-manual-target": "tie-breaks",
      },
    }),
    ...tieBreaks.map((tieBreak) =>
      element("a", {
        text: tieBreak.name,
        attributes: {
          href: "#/manual",
          "data-manual-target": tieBreak.code,
        },
      }),
    ),
  );

  const scoreNote = element("aside", { className: "manual-score-note" });
  scoreNote.append(
    element("strong", { text: "Score convention" }),
    element("p", {
      text: "A completed win contributes 1 point, a draw 0.5, and a loss 0. Bye or other awarded round points count toward points and progressive score, but do not create an opponent or a win.",
    }),
  );

  const chapter = element("section", {
    className: "manual-chapter",
    attributes: {
      id: "tie-breaks",
      tabindex: "-1",
      "aria-labelledby": "tie-break-chapter-title",
    },
  });
  chapter.append(
    element("div", { className: "manual-chapter-heading" }),
  );
  chapter.firstElementChild.append(
    element("p", { className: "manual-kicker", text: "10 supported rules" }),
    element("h2", { text: "Tie-break calculations", attributes: { id: "tie-break-chapter-title" } }),
    element("p", {
      text: "Examples use the same completed games, awarded points, and final opponent totals as the standings service.",
    }),
  );
  chapter.append(...tieBreaks.map(tieBreakArticle));

  root.append(orientation, scoreNote, chapter);
  return {
    title: "Manual",
    element: root,
    activate({ signal }) {
      root.querySelector(".manual-contents").addEventListener(
        "click",
        (event) => {
          const link = event.target.closest("[data-manual-target]");
          if (!link) {
            return;
          }
          event.preventDefault();
          const target = document.getElementById(link.dataset.manualTarget);
          target?.scrollIntoView({ behavior: "smooth", block: "start" });
          target?.focus({ preventScroll: true });
        },
        { signal },
      );
    },
  };
}
