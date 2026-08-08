# Quest authoring configuration

This document defines accepted Stage 6 quest-authoring values. Backend validation
and database constraints own the stored machine values. Mobile clients display
the labels returned by the authenticated authoring-options API and never infer
progression behavior from presentation metadata.

## Categories

Quest category is optional. SQL and API `null` mean **Uncategorized**. The only
accepted non-null machine values and labels are:

| Machine value | Display label |
| --- | --- |
| `personal` | Personal |
| `health` | Health |
| `learning` | Learning |
| `work` | Work |
| `finance` | Finance |

Values are exact and case-sensitive. Labels, aliases, blank strings, surrounding
whitespace, and unknown values are rejected rather than normalized. Category is
definition metadata only: changing it does not modify an occurrence, completion,
reward, campaign state, or historical record. Existing quests are not backfilled
and remain Uncategorized until explicitly edited.
