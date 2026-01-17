/**
 * NEOLAF Mode Policy - Learning vs Performance Mode Switching
 *
 * Controls when the agent operates in learning mode (explore) vs
 * performance mode (exploit based on established skills).
 *
 * Mode switching is based on:
 * - Confidence levels (Ê)
 * - Skill success rates
 * - ΔE variance (learning signal stability)
 * - Episode history
 *
 * @module neolaf/mode-policy
 */

import z from "zod"
import { Log } from "../util/log"
import { type OperatingMode, type ModePolicy, type NEOLAFSkillInfo, ModePolicy as ModePolicySchema } from "./types"

export namespace Mode {
  const log = Log.create({ service: "neolaf.mode" })

  /**
   * Default mode policy configuration
   */
  export const DEFAULT_POLICY: ModePolicy = {
    defaultMode: "learning",
    learningThreshold: 0.7,
    performanceThreshold: 0.9,
    deltaEVarianceThreshold: 0.3,
    minEpisodesForPerformance: 3,
  }

  // Current policy (can be configured)
  let currentPolicy: ModePolicy = { ...DEFAULT_POLICY }

  /**
   * Configure the mode policy
   */
  export function configure(policy: Partial<ModePolicy>): void {
    currentPolicy = { ...currentPolicy, ...policy }
    log.info("mode policy configured", { policy: currentPolicy })
  }

  /**
   * Get current policy
   */
  export function getPolicy(): Readonly<ModePolicy> {
    return { ...currentPolicy }
  }

  /**
   * Determine operating mode based on context
   *
   * @param confidence - Current confidence level (0-1)
   * @param skillInfo - Relevant skill information (if any)
   * @param recentDeltaEs - Recent ΔE values for variance calculation
   */
  export function determineMode(input: {
    confidence: number
    skillInfo?: NEOLAFSkillInfo
    recentDeltaEs?: number[]
  }): OperatingMode {
    const { confidence, skillInfo, recentDeltaEs = [] } = input

    // Low confidence → always learning
    if (confidence < currentPolicy.learningThreshold) {
      log.debug("mode: learning (low confidence)", { confidence })
      return "learning"
    }

    // No skill or immature skill → learning
    if (!skillInfo || skillInfo.maturity === "memorized") {
      log.debug("mode: learning (no/immature skill)", { skillInfo: skillInfo?.name })
      return "learning"
    }

    // Not enough episodes → learning
    if (skillInfo.episodes.length < currentPolicy.minEpisodesForPerformance) {
      log.debug("mode: learning (insufficient episodes)", {
        episodes: skillInfo.episodes.length,
        required: currentPolicy.minEpisodesForPerformance,
      })
      return "learning"
    }

    // High ΔE variance → learning (unstable results)
    if (recentDeltaEs.length > 0) {
      const variance = calculateVariance(recentDeltaEs)
      if (variance > currentPolicy.deltaEVarianceThreshold) {
        log.debug("mode: learning (high ΔE variance)", { variance })
        return "learning"
      }
    }

    // High confidence + mature skill + stable history → performance
    if (confidence >= currentPolicy.performanceThreshold) {
      log.debug("mode: performance", { confidence, skill: skillInfo.name })
      return "performance"
    }

    // Default to learning
    return "learning"
  }

  /**
   * Calculate variance of a number array
   */
  function calculateVariance(values: number[]): number {
    if (values.length === 0) return 0
    const mean = values.reduce((a, b) => a + b, 0) / values.length
    const squaredDiffs = values.map((v) => Math.pow(v - mean, 2))
    return squaredDiffs.reduce((a, b) => a + b, 0) / values.length
  }

  /**
   * Reset policy to defaults
   */
  export function reset(): void {
    currentPolicy = { ...DEFAULT_POLICY }
  }
}
