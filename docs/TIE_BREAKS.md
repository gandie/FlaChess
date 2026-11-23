# Chess Tie-Break Design

This document expands the tie-break recommendation summarized in
[DATA.md](./DATA.md). It is design guidance plus a record of the currently
implemented ranking subset.

## Recommended Data Model

Store tie-break rules on a section rather than hard-coding them in standings
code:

| Entity | Purpose |
| --- | --- |
| `section_tiebreak` | Ordered tie-break configuration for one section |
| `code` | Portable `VARCHAR` tie-break identifier |
| `sequence` | Position in the tie-break order |
| `parameter` | Optional cut, median, or Koya threshold |

Store an optional tournament-entry rating snapshot on `section_participant`.
The ranking engine should use that snapshot unless a tournament-specific rule
states otherwise.

## Required Raw Data

The ranking engine reads these existing entities rather than reconstructing
missing tournament history:

- `tournament_round`: round number and section ownership.
- `round_participant`: paired, bye, unplayed, absent, or allocated score.
- `game`: pair, scores, result provenance, and result-change comment.
- `section_participant`: rating snapshot and section membership.
- `section_tiebreak`: ordered rule configuration and optional parameter.

For direct encounter, the engine filters completed games between tied players.
For wins and progressive score, it reads the normalized game and round records.
For Buchholz and Sonneborn-Berger, it joins each game to opponent ratings and
final scores. For rating tie-breaks, it reads the opponent rating snapshot.

## Configuration and Integrity

`section_tiebreak` must be orderable and optionally lockable through
`tournament_section.tie_break_locked_at`. Once locked, the section's active
tie-break list should not change.

`round_participant` makes virtual-opponent and unplayed-round handling explicit.
The ranking engine must use its awarded score and FIDE/section-specific rules
instead of treating missing games as ordinary losses.

## FIDE Context

FIDE C.07 regulations, effective 1 March 2026, require the tournament rules to
define or share tied places, specify tie-break order, and announce it before
play. Candidate systems include direct encounter, wins, progressive score,
Buchholz variants, Sonneborn-Berger variants, Koya, rating-based systems,
performance ratings, and cut/median modifiers.

Ratings-based tie-breaks should be disabled or explicitly handle unrated
participants. They are not recommended when a participant can receive multiple
ratings during a tournament.

Opponent-based Swiss tie-breaks also need consistent virtual-opponent and
unplayed-round handling for byes and forfeits.

## Initial Defaults

- **Swiss:** Buchholz Cut-1, Buchholz Total, Number of Wins, Direct Encounter.
- **Round robin:** Direct Encounter, Sonneborn-Berger, Koya, Number of Wins.
- **Knockout:** no Swiss ranking tie-break; match outcomes decide advancement.

These are recommendations, not final rules. The operator must configure and
announce the exact list before the first round.

## Initial Implementation

The standings service calculates:

- direct encounter;
- number of wins;
- progressive score;
- Buchholz, Buchholz Cut-1/Cut-2, and Buchholz Median-1/Median-2;
- Sonneborn-Berger and Sonneborn-Berger Cut-1.

Awarded non-paired round scores contribute to total points. Virtual-opponent
policies, Koya thresholds, Fore Buchholz, rating-derived values, and
performance-rating formulas are not inferred. A configured unsupported code
therefore fails recomputation explicitly until its tournament rule is
specified.

## Sources

- [FIDE C.07 Play-Off and Tie-Break Regulations, effective 1 March 2026](https://handbook1090.fide.com/chapter/TieBreakRegulations032026)
- [FIDE Swiss pairing and tie-break background](https://old.fide.com/component/handbook/?id=85&view=article)
