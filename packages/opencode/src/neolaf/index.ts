/**
 * NEOLAF - NEural Ontology Learning Agent Framework
 *
 * A cognitive orchestration layer for LLM-based agents using the KSTAR-E loop.
 * NEOLAF adds persistent memory, skill lifecycle management, and learning from oracles.
 *
 * Core concepts:
 * - KSTAR-E Loop: Knowledge → Situation → Task → Action → Result + Emotion
 * - Skill Maturity: memorized → understood → applied → created → innovated
 * - Operating Modes: learning (explore) vs performance (exploit)
 * - Oracle Learning: LLM responses become candidate skills after validation
 *
 * @module neolaf
 */

// Re-export all types
export * from "./types"

// Re-export submodules
export * from "./orchestrator"
export * from "./mode-policy"
export * from "./emotion"
export * from "./memory"
export * from "./skill"
export * from "./oracle"
export * from "./plugin"

// Main namespace for direct access
import z from "zod"
import { Log } from "../util/log"
import {
  type KSTARTrace,
  type NEOLAFSkillInfo,
  type OperatingMode,
  type SituationVector,
  type Task,
  type Emotion as EmotionType,
  type ModePolicy,
} from "./types"

export namespace NEOLAF {
  const log = Log.create({ service: "neolaf" })

  /**
   * NEOLAF configuration schema
   */
  export const Config = z
    .object({
      enabled: z.boolean().default(true).describe("Enable NEOLAF cognitive layer"),
      mode: z.enum(["learning", "performance"]).default("learning").describe("Default operating mode"),
      memory: z
        .object({
          path: z.string().optional().describe("Custom memory database path"),
          maxTraces: z.number().default(10000).describe("Maximum traces to retain"),
          pruneOlderThan: z.number().default(30).describe("Days after which to prune traces"),
        })
        .optional()
        .describe("Memory configuration"),
      modePolicy: z
        .object({
          learningThreshold: z.number().default(0.7),
          performanceThreshold: z.number().default(0.9),
          minEpisodesForPerformance: z.number().default(3),
        })
        .optional()
        .describe("Mode switching policy"),
    })
    .optional()

  export type Config = z.infer<typeof Config>

  /**
   * Current NEOLAF version
   */
  export const VERSION = "0.1.0"

  /**
   * Check if NEOLAF is available and initialized
   */
  export function isAvailable(): boolean {
    // Will be implemented in M1 with actual state check
    return true
  }

  /**
   * Get current operating mode
   */
  export async function getMode(): Promise<OperatingMode> {
    // Stub - will be implemented in M4
    return "learning"
  }

  /**
   * Log a NEOLAF event for debugging
   */
  export function debug(message: string, data?: Record<string, unknown>): void {
    log.debug(message, data)
  }

  /**
   * Log a NEOLAF info message
   */
  export function info(message: string, data?: Record<string, unknown>): void {
    log.info(message, data)
  }
}
