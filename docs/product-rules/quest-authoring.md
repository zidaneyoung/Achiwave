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

## Difficulty

New quests require one of these exact machine values:

| Machine value | Display label |
| --- | --- |
| `easy` | Easy |
| `medium` | Medium |
| `hard` | Hard |

Difficulty is planning metadata. It never determines, defaults, or changes XP,
and the backend accepts every allowed reward independently of difficulty. Mobile
shows a visible Medium default for new quests. Historical rows created before
this contract remain `null` and display **Not set** until the owner explicitly
chooses a difficulty; unrelated edits may preserve that legacy null. Explicit
null, labels, aliases, case variants, whitespace variants, and unknown values are
rejected for new configuration. Archive and restore retain the stored value.

## Configured XP rewards

The only values selectable for a new quest or a changed definition reward are
`0`, `10`, and `20` XP. Values are JSON integers; numeric strings, fractions,
negative values, and other integers are rejected. Difficulty never selects or
constrains a reward value.

This setting is not an XP award. Creating or editing a quest does not add a
ledger entry, change progression, or change an already generated occurrence's
reward snapshot. Existing definitions with a historical reward outside the
allowed choices remain readable and authoritative for their existing occurrence.
They may be submitted unchanged and may be omitted during unrelated edits, but
any actual reward change must select an allowed value. No database allowlist
constraint or data backfill rewrites legacy configured or snapshotted rewards;
the existing nonnegative database integrity constraint remains in force.

## Active quest order

Quest `display_order` is presentation metadata only. A reorder request must name
every active, non-deleted quest in one owned, non-archived campaign exactly once,
with current campaign and quest record versions plus a stable client mutation
identifier. The backend applies the order atomically as contiguous nonnegative
positions and returns the canonical result. Duplicate, missing, unknown,
cross-campaign, cross-owner, archived, or stale entries are rejected without a
partial write.

Archived quests do not participate in active order. Restoring a quest appends it
after the current active order. Reordering does not create a completion, reward,
progress event, campaign transition, or other product-state change. Mobile must
offer visible, accessible move-up and move-down controls; it must not require a
drag gesture and must disable reordering when filters, archived history, or a
noncanonical sort make the full active sequence ambiguous.
