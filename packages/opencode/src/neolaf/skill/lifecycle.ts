/**
 * NEOLAF Skill Lifecycle - State Transitions
 *
 * Manages skill maturity transitions based on episode evidence.
 * Implements Bloom's taxonomy-based progression:
 *
 * memorized → understood → applied → created → innovated
 *
 * @module neolaf/skill/lifecycle
 */

import z from "zod"
import { Log } from "../../util/log"
import { type NEOLAFSkillInfo, type SkillMaturity, type SkillEpisode } from "../types"
import { SkillRegistry } from "./registry"

export namespace SkillLifecycle {
  const log = Log.create({ service: "neolaf.skill.lifecycle" })

  /**
   * Maturity level ordering for comparisons
   */
  const MATURITY_ORDER: SkillMaturity[] = [
    "memorized",
    "understood",
    "applied",
    "created",
    "innovated",
  ]

  /**
   * Thresholds for maturity promotion
   */
  export interface PromotionThresholds {
    // memorized → understood: comprehension demonstrated
    understoodMinEpisodes: number
    understoodMinSuccessRate: number

    // understood → applied: practical success
    appliedMinEpisodes: number
    appliedMinSuccessRate: number
    appliedMinDomains: number // Different domains/contexts

    // applied → created: ability to generate variations
    createdMinEpisodes: number
    createdMinSuccessRate: number
    createdMinVariations: number // Unique parameter combinations

    // created → innovated: novel approaches created
    innovatedMinEpisodes: number
    innovatedMinSuccessRate: number
    innovatedMinNovelApproaches: number // Truly new methods
  }

  /**
   * Default promotion thresholds
   */
  export const DEFAULT_THRESHOLDS: PromotionThresholds = {
    understoodMinEpisodes: 3,
    understoodMinSuccessRate: 0.6,

    appliedMinEpisodes: 5,
    appliedMinSuccessRate: 0.75,
    appliedMinDomains: 2,

    createdMinEpisodes: 10,
    createdMinSuccessRate: 0.85,
    createdMinVariations: 5,

    innovatedMinEpisodes: 20,
    innovatedMinSuccessRate: 0.9,
    innovatedMinNovelApproaches: 3,
  }

  // Current thresholds (configurable)
  let thresholds = { ...DEFAULT_THRESHOLDS }

  /**
   * Configure promotion thresholds
   */
  export function configure(custom: Partial<PromotionThresholds>): void {
    thresholds = { ...thresholds, ...custom }
    log.info("lifecycle thresholds configured", { thresholds })
  }

  /**
   * Evaluate if a skill should be promoted
   * Returns the new maturity level if promotion is warranted
   */
  export function evaluatePromotion(skill: NEOLAFSkillInfo): SkillMaturity | null {
    const { maturity, episodes, successRate = 0 } = skill
    const currentIndex = MATURITY_ORDER.indexOf(maturity)

    if (currentIndex === MATURITY_ORDER.length - 1) {
      return null // Already at maximum maturity
    }

    const nextMaturity = MATURITY_ORDER[currentIndex + 1]

    // Check promotion criteria based on target level
    switch (nextMaturity) {
      case "understood":
        if (
          episodes.length >= thresholds.understoodMinEpisodes &&
          successRate >= thresholds.understoodMinSuccessRate
        ) {
          log.debug("skill eligible for understood promotion", { skill: skill.name })
          return "understood"
        }
        break

      case "applied":
        if (
          episodes.length >= thresholds.appliedMinEpisodes &&
          successRate >= thresholds.appliedMinSuccessRate
        ) {
          const domains = countUniqueDomains(episodes)
          if (domains >= thresholds.appliedMinDomains) {
            log.debug("skill eligible for applied promotion", { skill: skill.name, domains })
            return "applied"
          }
        }
        break

      case "created":
        if (
          episodes.length >= thresholds.createdMinEpisodes &&
          successRate >= thresholds.createdMinSuccessRate
        ) {
          // TODO M3: Track variations in trace capture
          log.debug("skill eligible for created promotion", { skill: skill.name })
          return "created"
        }
        break

      case "innovated":
        if (
          episodes.length >= thresholds.innovatedMinEpisodes &&
          successRate >= thresholds.innovatedMinSuccessRate
        ) {
          // TODO M3: Track novel approaches
          log.debug("skill eligible for innovated promotion", { skill: skill.name })
          return "innovated"
        }
        break
    }

    return null
  }

  /**
   * Check and apply promotion for a skill
   */
  export async function checkAndPromote(skillId: string): Promise<boolean> {
    const skill = await SkillRegistry.get(skillId)
    if (!skill) {
      return false
    }

    const newMaturity = evaluatePromotion(skill)
    if (newMaturity) {
      await SkillRegistry.updateMaturity(skillId, newMaturity)
      log.info("skill promoted", {
        skillId,
        name: skill.name,
        from: skill.maturity,
        to: newMaturity,
      })
      return true
    }

    return false
  }

  /**
   * Check for demotion (after repeated failures)
   * Skills can be demoted if they show consistent failure
   */
  export async function checkDemotion(skillId: string): Promise<boolean> {
    const skill = await SkillRegistry.get(skillId)
    if (!skill || skill.maturity === "memorized") {
      return false
    }

    // Check recent episodes for failure pattern
    const recentEpisodes = skill.episodes.slice(-5)
    if (recentEpisodes.length < 3) {
      return false
    }

    const recentSuccessRate =
      recentEpisodes.filter((e) => e.success).length / recentEpisodes.length

    // Demote if recent success rate drops below 30%
    if (recentSuccessRate < 0.3) {
      const currentIndex = MATURITY_ORDER.indexOf(skill.maturity)
      const newMaturity = MATURITY_ORDER[Math.max(0, currentIndex - 1)]

      await SkillRegistry.updateMaturity(skillId, newMaturity)
      log.warn("skill demoted due to poor performance", {
        skillId,
        name: skill.name,
        from: skill.maturity,
        to: newMaturity,
        recentSuccessRate,
      })
      return true
    }

    return false
  }

  /**
   * Get maturity level as a number (0-4)
   */
  export function maturityToLevel(maturity: SkillMaturity): number {
    return MATURITY_ORDER.indexOf(maturity)
  }

  /**
   * Get maturity from level number
   */
  export function levelToMaturity(level: number): SkillMaturity {
    const clamped = Math.max(0, Math.min(MATURITY_ORDER.length - 1, level))
    return MATURITY_ORDER[clamped]
  }

  /**
   * Compare two maturity levels
   * Returns: -1 if a < b, 0 if equal, 1 if a > b
   */
  export function compareMaturity(a: SkillMaturity, b: SkillMaturity): number {
    const aIndex = MATURITY_ORDER.indexOf(a)
    const bIndex = MATURITY_ORDER.indexOf(b)
    return Math.sign(aIndex - bIndex)
  }

  /**
   * Count unique domains from episodes (based on context)
   */
  function countUniqueDomains(episodes: SkillEpisode[]): number {
    const domains = new Set<string>()
    for (const episode of episodes) {
      if (episode.context) {
        // Extract domain hint from context
        const domainMatch = episode.context.match(/domain:(\w+)/i)
        if (domainMatch) {
          domains.add(domainMatch[1])
        } else {
          // Use first word as domain approximation
          domains.add(episode.context.split(/\s+/)[0])
        }
      }
    }
    return domains.size
  }

  /**
   * Reset thresholds to defaults
   */
  export function reset(): void {
    thresholds = { ...DEFAULT_THRESHOLDS }
  }
}
