# History, archival, and deletion

This document is normative for issue #15.

## #15 — Definitions and product boundary

| Operation | Reversible | User-facing MVP operation | Meaning |
|---|---:|---:|---|
| Archive | Yes | Yes | Hide an active campaign/quest by default and block new activity while preserving identity and history. |
| Soft deletion | Policy-dependent | No | Backend tombstone used for recovery, moderation, or staged privacy processing; blocks use and hides normal views. |
| Permanent deletion | No | No, except privacy workflow | Erase or irreversibly de-identify data under account-deletion or legal obligation. |
| Account deletion | No after any statutory recovery window | Yes as a privacy workflow in a later stage | Revoke access and remove/de-identify the user's product data as one coordinated process. |

Ordinary campaign and quest “delete” in MVP means archive. Individual permanent
deletion is not a shortcut for changing progression.

## Effects matrix

| Record / behavior | Archive campaign or quest | Soft deletion | Permanent/account deletion |
|---|---|---|---|
| Campaign/quest definition | Retained, hidden by default, restorable. | Tombstone retained with stable references; not restorable through normal UI. | Personal content erased or de-identified as legally required. |
| Occurrences | Existing states/snapshots retained; future generation stops; archived-period dates not backfilled. | Retained behind tombstone for integrity; no generation. | Removed or de-identified with account; no future processing. |
| New completion | Rejected while campaign or quest archived. | Rejected. | Impossible; credentials/sessions revoked. |
| Existing completion | Retained and authoritative. | Retained for ledger/audit integrity while account exists. | Removed/de-identified with deleted account; no post-deletion progression promise. |
| Reversal | Allowed against active completion despite archive. | Only authorized privacy/support correction path. | Not applicable after account data is erased. |
| XP ledger | Award/compensation retained and included. Archive itself creates no delta. | Retained and authoritative while account exists. | Erased/de-identified consistently; never leave linkable orphan personal data. |
| Level | Re-derived from retained ledger; archive alone does not change it. | Same while account exists. | User progression ceases to exist. |
| Streak | Retained qualifying history; no new archived completions. | Retained/recalculated from remaining authoritative data. | User streak ceases to exist. |
| Achievements | Progress/unlocks retained; unlocked remains unlocked. | Retained while account exists, concealed from normal item views as needed. | User unlocks/progress removed or de-identified. |
| Sync operations | Pending completion becomes permanent failure after server archive; exact prior success remains success. | Pending operations rejected and tombstone returned safely. | Server invalidates sessions/devices; queued local private data is cancelled and cleared. |
| Audit history | Archive/restore appended; no prior events rewritten. | Tombstone and actor/reason audited. | Retain only legally permitted minimal non-identifying security/audit data. |
| Visibility | Hidden from default active views; optional archived-history view. | Hidden from ordinary user views. | Not visible; anonymized aggregate data cannot identify user. |

## Archive and restore rules

- Archive is owner-requested, backend-authorized, versioned, and server-timestamped.
- Archiving a campaign blocks quest creation, recurrence generation, and completion
  for all contained quests without rewriting each quest state.
- Archiving a quest stops its recurrence and excludes it from future campaign
  obligations. Existing reward-bearing history remains associated with both quest
  and campaign.
- Archive never awards, reverses, or deletes XP and never relocks an achievement.
- Pending offline completion received after archive is permanently rejected even
  when device metadata predates archive.
- Reversal remains allowed because correction cannot depend on visibility state.
- Restore validates the parent campaign and current record version. Restoring a
  quest inside an archived campaign is rejected until the campaign is restored.
- Restore resumes recurrence from the restore effective date with no archived-period
  backfill. Generated pre-archive occurrences retain their original windows; those
  still eligible may be completed after restore, while expired ones remain expired.
- Campaign state is recalculated after archive/restore; prior campaign completion
  events remain in history.

## Historical integrity

Completion, reversal, XP ledger, campaign-state, level-change, streak-derivation,
achievement-unlock, timezone-change, archive/restore, and synchronization outcome
events are append-only while the account exists. A product edit must never:

- delete a reward entry to reduce XP;
- change an accepted completion time;
- move a completed quest to another campaign;
- regenerate an occurrence under a new timezone;
- erase a reversal relation;
- relock an unlocked achievement; or
- mark a failed queued mutation successful locally.

Corrections use explicit compensating events and reconciliation. Database retention
must preserve referential integrity even when normal product views hide definitions.

## Privacy and legal boundary

Account deletion is an explicit authenticated workflow with reauthentication and
confirmation defined during authentication implementation. It must:

1. revoke sessions, device registrations, and push-token associations;
2. stop recurrence, notifications, workers, and synchronization;
3. cancel and securely clear local queues/caches on devices when they receive the
   deletion or revocation state;
4. erase or irreversibly de-identify campaigns, quests, occurrences, completions,
   ledger, progression, achievement, device, notification, timestamp metadata, and
   private content as required;
5. prevent orphan records from identifying the user; and
6. retain only data required by law or security, access-restricted and no longer
   used for product progression.

Specific statutory retention periods, recovery windows, and jurisdictional export
formats are deferred to the later privacy implementation because they depend on
deployment jurisdiction. This is a bounded compliance decision, not permission to
retain data indefinitely: the deployed policy must state the period before account
deletion ships.

Legal erasure is the sole exception to append-only product history. Because the
account no longer exists afterward, totals need not remain reconstructable for that
user. Aggregate analytics may remain only when irreversibly anonymized.

## Examples and exceptions

- Valid: archive a finished campaign; XP and achievement remain.
- Valid: reverse an erroneous completion inside an archived campaign; a negative
  ledger entry explains the change.
- Valid: restore a daily quest after ten archived days; generation resumes now and
  does not create ten missed rewards.
- Invalid: permanently delete one completed quest while retaining its unexplained
  XP total.
- Invalid: accept a queued completion after archive because device time was earlier.
- Exception: verified account deletion removes/de-identifies reward history under
  privacy law and terminates the account's progression.
