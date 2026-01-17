/**
 * NEOLAF Memory Store - SQLite-based Persistence
 *
 * Stores KSTAR-E traces, skill information, and oracle responses
 * using bun:sqlite for fast, embedded storage.
 *
 * Storage location: {XDG_DATA_HOME}/opencode/neolaf/memory.sqlite
 *
 * @module neolaf/memory/store
 */

import { Database } from "bun:sqlite"
import path from "path"
import fs from "fs/promises"
import { Log } from "../../util/log"
import { Global } from "../../global"
import {
  type KSTARTrace,
  type NEOLAFSkillInfo,
  type OracleResponse,
  KSTARTrace as KSTARTraceSchema,
  NEOLAFSkillInfo as NEOLAFSkillInfoSchema,
  OracleResponse as OracleResponseSchema,
} from "../types"

export namespace MemoryStore {
  const log = Log.create({ service: "neolaf.memory.store" })

  /**
   * Store configuration
   */
  export interface Config {
    path?: string
    maxTraces?: number
    pruneOlderThan?: number
  }

  // Database instance
  let db: Database | null = null
  let config: Config = {}

  // Schema version for migrations
  const SCHEMA_VERSION = 1

  /**
   * Initialize the memory store
   */
  export async function init(options: Config = {}): Promise<void> {
    config = options

    // Determine database path
    const dbDir = path.join(Global.Path.data, "neolaf")
    await fs.mkdir(dbDir, { recursive: true })
    const dbPath = options.path ?? path.join(dbDir, "memory.sqlite")

    log.info("initializing memory store", { path: dbPath })

    // Open database
    db = new Database(dbPath, { create: true })

    // Enable WAL mode for better concurrent access
    db.run("PRAGMA journal_mode = WAL")
    db.run("PRAGMA synchronous = NORMAL")

    // Run migrations
    await runMigrations()

    log.info("memory store initialized")
  }

  /**
   * Run database migrations
   */
  async function runMigrations(): Promise<void> {
    if (!db) throw new Error("Database not initialized")

    // Check current schema version
    db.run(`
      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
      )
    `)

    const versionRow = db.query("SELECT version FROM schema_version LIMIT 1").get() as
      | { version: number }
      | null
    const currentVersion = versionRow?.version ?? 0

    if (currentVersion < SCHEMA_VERSION) {
      log.info("running migrations", { from: currentVersion, to: SCHEMA_VERSION })

      // Migration 1: Initial schema
      if (currentVersion < 1) {
        db.run(`
          CREATE TABLE IF NOT EXISTS traces (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            parent_trace_id TEXT,
            timestamp TEXT NOT NULL,
            mode TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at INTEGER NOT NULL DEFAULT (unixepoch())
          )
        `)
        db.run("CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id)")
        db.run("CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp)")
        db.run("CREATE INDEX IF NOT EXISTS idx_traces_mode ON traces(mode)")

        db.run(`
          CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            maturity TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at INTEGER NOT NULL DEFAULT (unixepoch())
          )
        `)
        db.run("CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)")
        db.run("CREATE INDEX IF NOT EXISTS idx_skills_maturity ON skills(maturity)")

        db.run(`
          CREATE TABLE IF NOT EXISTS oracle_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            validated INTEGER NOT NULL DEFAULT 0,
            validation_trace_id TEXT,
            data TEXT NOT NULL,
            created_at INTEGER NOT NULL DEFAULT (unixepoch())
          )
        `)
        db.run("CREATE INDEX IF NOT EXISTS idx_oracle_query ON oracle_responses(query_id)")
        db.run("CREATE INDEX IF NOT EXISTS idx_oracle_validated ON oracle_responses(validated)")

        // Tags table for efficient tag queries
        db.run(`
          CREATE TABLE IF NOT EXISTS trace_tags (
            trace_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (trace_id, tag),
            FOREIGN KEY (trace_id) REFERENCES traces(id) ON DELETE CASCADE
          )
        `)
        db.run("CREATE INDEX IF NOT EXISTS idx_trace_tags_tag ON trace_tags(tag)")
      }

      // Update schema version
      db.run("DELETE FROM schema_version")
      db.run("INSERT INTO schema_version (version) VALUES (?)", [SCHEMA_VERSION])
    }
  }

  /**
   * Store a KSTAR-E trace
   */
  export async function storeTrace(trace: KSTARTrace): Promise<void> {
    if (!db) throw new Error("Database not initialized")

    log.debug("storing trace", { id: trace.id, task: trace.task.goal })

    const stmt = db.prepare(`
      INSERT OR REPLACE INTO traces (id, session_id, parent_trace_id, timestamp, mode, data)
      VALUES (?, ?, ?, ?, ?, ?)
    `)

    stmt.run(
      trace.id,
      trace.sessionId,
      trace.parentTraceId ?? null,
      trace.timestamp,
      trace.mode,
      JSON.stringify(trace),
    )

    // Store tags
    if (trace.tags.length > 0) {
      const tagStmt = db.prepare("INSERT OR IGNORE INTO trace_tags (trace_id, tag) VALUES (?, ?)")
      for (const tag of trace.tags) {
        tagStmt.run(trace.id, tag)
      }
    }
  }

  /**
   * Retrieve traces by session
   */
  export async function getTracesBySession(sessionId: string): Promise<KSTARTrace[]> {
    if (!db) throw new Error("Database not initialized")

    log.debug("getting traces for session", { sessionId })

    const rows = db
      .query("SELECT data FROM traces WHERE session_id = ? ORDER BY timestamp ASC")
      .all(sessionId) as { data: string }[]

    return rows
      .map((row) => {
        try {
          return KSTARTraceSchema.parse(JSON.parse(row.data))
        } catch {
          log.warn("failed to parse trace", { sessionId })
          return null
        }
      })
      .filter((t): t is KSTARTrace => t !== null)
  }

  /**
   * Retrieve a specific trace by ID
   */
  export async function getTrace(traceId: string): Promise<KSTARTrace | null> {
    if (!db) throw new Error("Database not initialized")

    log.debug("getting trace", { traceId })

    const row = db.query("SELECT data FROM traces WHERE id = ?").get(traceId) as
      | { data: string }
      | null

    if (!row) return null

    try {
      return KSTARTraceSchema.parse(JSON.parse(row.data))
    } catch {
      log.warn("failed to parse trace", { traceId })
      return null
    }
  }

  /**
   * Query traces with filters
   */
  export async function queryTraces(filters: {
    sessionId?: string
    mode?: string
    tags?: string[]
    startDate?: Date
    endDate?: Date
    limit?: number
    offset?: number
  }): Promise<KSTARTrace[]> {
    if (!db) throw new Error("Database not initialized")

    log.debug("querying traces", { filters })

    const conditions: string[] = []
    const params: (string | number)[] = []

    if (filters.sessionId) {
      conditions.push("session_id = ?")
      params.push(filters.sessionId)
    }

    if (filters.mode) {
      conditions.push("mode = ?")
      params.push(filters.mode)
    }

    if (filters.startDate) {
      conditions.push("timestamp >= ?")
      params.push(filters.startDate.toISOString())
    }

    if (filters.endDate) {
      conditions.push("timestamp <= ?")
      params.push(filters.endDate.toISOString())
    }

    // Build query
    let query = "SELECT DISTINCT t.data FROM traces t"

    if (filters.tags && filters.tags.length > 0) {
      query += " INNER JOIN trace_tags tt ON t.id = tt.trace_id"
      const tagPlaceholders = filters.tags.map(() => "?").join(", ")
      conditions.push(`tt.tag IN (${tagPlaceholders})`)
      params.push(...filters.tags)
    }

    if (conditions.length > 0) {
      query += " WHERE " + conditions.join(" AND ")
    }

    query += " ORDER BY t.timestamp DESC"

    if (filters.limit) {
      query += ` LIMIT ${filters.limit}`
    }

    if (filters.offset) {
      query += ` OFFSET ${filters.offset}`
    }

    const rows = db.query(query).all(...params) as { data: string }[]

    return rows
      .map((row) => {
        try {
          return KSTARTraceSchema.parse(JSON.parse(row.data))
        } catch {
          return null
        }
      })
      .filter((t): t is KSTARTrace => t !== null)
  }

  /**
   * Store or update skill information
   */
  export async function storeSkill(skill: NEOLAFSkillInfo): Promise<void> {
    if (!db) throw new Error("Database not initialized")

    log.debug("storing skill", { id: skill.id, name: skill.name })

    const stmt = db.prepare(`
      INSERT OR REPLACE INTO skills (id, name, version, maturity, data, updated_at)
      VALUES (?, ?, ?, ?, ?, unixepoch())
    `)

    stmt.run(skill.id, skill.name, skill.version, skill.maturity, JSON.stringify(skill))
  }

  /**
   * Retrieve skill by ID
   */
  export async function getSkill(skillId: string): Promise<NEOLAFSkillInfo | null> {
    if (!db) throw new Error("Database not initialized")

    log.debug("getting skill", { skillId })

    const row = db.query("SELECT data FROM skills WHERE id = ?").get(skillId) as
      | { data: string }
      | null

    if (!row) return null

    try {
      return NEOLAFSkillInfoSchema.parse(JSON.parse(row.data))
    } catch {
      log.warn("failed to parse skill", { skillId })
      return null
    }
  }

  /**
   * Retrieve all skills
   */
  export async function getAllSkills(): Promise<NEOLAFSkillInfo[]> {
    if (!db) throw new Error("Database not initialized")

    log.debug("getting all skills")

    const rows = db.query("SELECT data FROM skills ORDER BY name ASC").all() as { data: string }[]

    return rows
      .map((row) => {
        try {
          return NEOLAFSkillInfoSchema.parse(JSON.parse(row.data))
        } catch {
          return null
        }
      })
      .filter((s): s is NEOLAFSkillInfo => s !== null)
  }

  /**
   * Store oracle response
   */
  export async function storeOracleResponse(response: OracleResponse): Promise<void> {
    if (!db) throw new Error("Database not initialized")

    log.debug("storing oracle response", { queryId: response.queryId })

    const stmt = db.prepare(`
      INSERT INTO oracle_responses (query_id, timestamp, validated, validation_trace_id, data)
      VALUES (?, ?, ?, ?, ?)
    `)

    stmt.run(
      response.queryId,
      response.timestamp,
      response.validated ? 1 : 0,
      response.validationTraceId ?? null,
      JSON.stringify(response),
    )
  }

  /**
   * Get oracle responses by validation status
   */
  export async function getOracleResponses(validated?: boolean): Promise<OracleResponse[]> {
    if (!db) throw new Error("Database not initialized")

    log.debug("getting oracle responses", { validated })

    let query = "SELECT data FROM oracle_responses"
    const params: number[] = []

    if (validated !== undefined) {
      query += " WHERE validated = ?"
      params.push(validated ? 1 : 0)
    }

    query += " ORDER BY timestamp DESC"

    const rows = db.query(query).all(...params) as { data: string }[]

    return rows
      .map((row) => {
        try {
          return OracleResponseSchema.parse(JSON.parse(row.data))
        } catch {
          return null
        }
      })
      .filter((r): r is OracleResponse => r !== null)
  }

  /**
   * Prune old traces
   */
  export async function prune(olderThanDays?: number): Promise<number> {
    if (!db) throw new Error("Database not initialized")

    const days = olderThanDays ?? config.pruneOlderThan ?? 30
    log.info("pruning traces", { olderThanDays: days })

    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - days)
    const cutoffISO = cutoffDate.toISOString()

    // Delete old traces (tags will be deleted via CASCADE)
    const result = db.run("DELETE FROM traces WHERE timestamp < ?", [cutoffISO])

    log.info("pruned traces", { deleted: result.changes })
    return result.changes
  }

  /**
   * Get statistics about the memory store
   */
  export async function getStats(): Promise<{
    traceCount: number
    skillCount: number
    oracleResponseCount: number
    dbSizeBytes: number
  }> {
    if (!db) throw new Error("Database not initialized")

    const traceCount =
      (db.query("SELECT COUNT(*) as count FROM traces").get() as { count: number })?.count ?? 0
    const skillCount =
      (db.query("SELECT COUNT(*) as count FROM skills").get() as { count: number })?.count ?? 0
    const oracleResponseCount =
      (db.query("SELECT COUNT(*) as count FROM oracle_responses").get() as { count: number })
        ?.count ?? 0

    // Get database file size
    const dbPath = path.join(Global.Path.data, "neolaf", "memory.sqlite")
    let dbSizeBytes = 0
    try {
      const stat = await fs.stat(dbPath)
      dbSizeBytes = stat.size
    } catch {
      // File may not exist yet
    }

    return {
      traceCount,
      skillCount,
      oracleResponseCount,
      dbSizeBytes,
    }
  }

  /**
   * Close the database connection
   */
  export async function close(): Promise<void> {
    log.info("closing memory store")
    if (db) {
      db.close()
      db = null
    }
  }

  /**
   * Check if store is initialized
   */
  export function isInitialized(): boolean {
    return db !== null
  }
}
