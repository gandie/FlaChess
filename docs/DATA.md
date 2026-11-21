# Data Model

## `player`

Stores player names.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `name` | `VARCHAR(255)` | Not null |

Player names are not constrained to be unique.
