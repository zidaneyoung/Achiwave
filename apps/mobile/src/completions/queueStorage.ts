import * as SQLite from "expo-sqlite";

import {
  COMPLETION_QUEUE_SCHEMA_VERSION,
  type CompletionQueueRecord,
  type CompletionQueueState,
} from "./queueTypes";

const DATABASE_NAME = "achiwave-protected-sync.db";

interface QueueRow {
  queue_id: string;
  schema_version: number;
  account_id: string;
  device_id: string;
  operation_type: "complete_occurrence";
  occurrence_id: string;
  expected_occurrence_version: number;
  client_mutation_id: string;
  canonical_payload_hash: string;
  device_observed_at: string;
  device_timezone_name: string;
  state: CompletionQueueState;
  attempt_count: number;
  automatic_attempt_count: number;
  next_attempt_at: string | null;
  last_attempt_at: string | null;
  lease_expires_at: string | null;
  safe_error_class: string | null;
  safe_error_message: string | null;
  completion_id: string | null;
  campaign_id: string | null;
  event_sequence: number | null;
  canonical_result_json: string | null;
  created_at: string;
  updated_at: string;
  terminal_at: string | null;
}

function fromRow(row: QueueRow): CompletionQueueRecord {
  return {
    queueId: row.queue_id,
    schemaVersion: row.schema_version,
    accountId: row.account_id,
    deviceId: row.device_id,
    operationType: row.operation_type,
    occurrenceId: row.occurrence_id,
    expectedOccurrenceVersion: row.expected_occurrence_version,
    clientMutationId: row.client_mutation_id,
    canonicalPayloadHash: row.canonical_payload_hash,
    deviceObservedAt: row.device_observed_at,
    deviceTimezoneName: row.device_timezone_name,
    state: row.state,
    attemptCount: row.attempt_count,
    automaticAttemptCount: row.automatic_attempt_count,
    nextAttemptAt: row.next_attempt_at,
    lastAttemptAt: row.last_attempt_at,
    leaseExpiresAt: row.lease_expires_at,
    safeErrorClass: row.safe_error_class,
    safeErrorMessage: row.safe_error_message,
    completionId: row.completion_id,
    campaignId: row.campaign_id,
    eventSequence: row.event_sequence,
    canonicalResultJson: row.canonical_result_json,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    terminalAt: row.terminal_at,
  };
}

let databasePromise: Promise<SQLite.SQLiteDatabase> | null = null;

async function database(): Promise<SQLite.SQLiteDatabase> {
  if (databasePromise === null) {
    databasePromise = SQLite.openDatabaseAsync(DATABASE_NAME).then(async (db) => {
      await db.execAsync(`
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;
        PRAGMA secure_delete = ON;
        CREATE TABLE IF NOT EXISTS completion_queue (
          queue_id TEXT PRIMARY KEY NOT NULL,
          schema_version INTEGER NOT NULL,
          account_id TEXT NOT NULL,
          device_id TEXT NOT NULL,
          operation_type TEXT NOT NULL CHECK (operation_type = 'complete_occurrence'),
          occurrence_id TEXT NOT NULL,
          expected_occurrence_version INTEGER NOT NULL,
          client_mutation_id TEXT NOT NULL,
          canonical_payload_hash TEXT NOT NULL,
          device_observed_at TEXT NOT NULL,
          device_timezone_name TEXT NOT NULL,
          state TEXT NOT NULL CHECK (state IN ('pending', 'in_flight', 'retryable_failure', 'succeeded', 'permanent_failure', 'cancelled')),
          attempt_count INTEGER NOT NULL DEFAULT 0,
          automatic_attempt_count INTEGER NOT NULL DEFAULT 0,
          next_attempt_at TEXT,
          last_attempt_at TEXT,
          lease_expires_at TEXT,
          safe_error_class TEXT,
          safe_error_message TEXT,
          completion_id TEXT,
          campaign_id TEXT,
          event_sequence INTEGER,
          canonical_result_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          terminal_at TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_completion_queue_mutation
          ON completion_queue (account_id, client_mutation_id);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_completion_queue_active_occurrence
          ON completion_queue (account_id, occurrence_id)
          WHERE state IN ('pending', 'in_flight', 'retryable_failure');
        CREATE INDEX IF NOT EXISTS ix_completion_queue_partition_due
          ON completion_queue (account_id, state, next_attempt_at, created_at);
        PRAGMA user_version = ${COMPLETION_QUEUE_SCHEMA_VERSION};
      `);
      return db;
    }).catch((error) => {
      databasePromise = null;
      throw error;
    });
  }
  return databasePromise;
}

export interface NewCompletionQueueRecord {
  queueId: string;
  accountId: string;
  deviceId: string;
  occurrenceId: string;
  expectedOccurrenceVersion: number;
  clientMutationId: string;
  canonicalPayloadHash: string;
  deviceObservedAt: string;
  deviceTimezoneName: string;
  now: string;
}

export const completionQueueStorage = {
  async findActive(
    accountId: string,
    occurrenceId: string,
  ): Promise<CompletionQueueRecord | null> {
    const db = await database();
    const row = await db.getFirstAsync<QueueRow>(
      `SELECT * FROM completion_queue
       WHERE account_id = ? AND occurrence_id = ?
         AND state IN ('pending', 'in_flight', 'retryable_failure')
       ORDER BY created_at LIMIT 1`,
      accountId,
      occurrenceId,
    );
    return row ? fromRow(row) : null;
  },

  async insert(record: NewCompletionQueueRecord): Promise<CompletionQueueRecord> {
    const db = await database();
    await db.runAsync(
      `INSERT INTO completion_queue (
        queue_id, schema_version, account_id, device_id, operation_type,
        occurrence_id, expected_occurrence_version, client_mutation_id,
        canonical_payload_hash, device_observed_at, device_timezone_name,
        state, attempt_count, automatic_attempt_count, created_at, updated_at
      ) VALUES (?, ?, ?, ?, 'complete_occurrence', ?, ?, ?, ?, ?, ?, 'pending', 0, 0, ?, ?)`,
      record.queueId,
      COMPLETION_QUEUE_SCHEMA_VERSION,
      record.accountId,
      record.deviceId,
      record.occurrenceId,
      record.expectedOccurrenceVersion,
      record.clientMutationId,
      record.canonicalPayloadHash,
      record.deviceObservedAt,
      record.deviceTimezoneName,
      record.now,
      record.now,
    );
    const inserted = await this.findActive(record.accountId, record.occurrenceId);
    if (!inserted) throw new Error("The offline completion was not stored.");
    return inserted;
  },
};
