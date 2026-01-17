/**
 * NEOLAF Skill Registry - Maturity Tracking
 *
 * Manages NEOLAF-enhanced skill information including maturity levels,
 * episode history, and success rates.
 *
 * Integrates with the existing skill loader at src/skill/skill.ts
 *
 * @module neolaf/skill/registry
 */

import z from "zod"
import { Log } from "../../util/log"
import {
  type NEOLAFSkillInfo,
  type SkillMaturity,
  type SkillEpisode,
  type SkillSignature,
  NEOLAFSkillInfo as NEOLAFSkillInfoSchema,
} from "../types"
import { MemoryStore } from "../memory/store"

export namespace SkillRegistry {
  const log = Log.create({ service: "neolaf.skill.registry" })

  // In-memory cache of NEOLAF skill data
  const cache = new Map<string, NEOLAFSkillInfo>()

  /**
   * Initialize the registry from persistent storage
   */
  export async function init(): Promise<void> {
    log.info("initializing skill registry")

    // Load all skills from memory store
    const skills = await MemoryStore.getAllSkills()
    for (const skill of skills) {
      cache.set(skill.id, skill)
    }

    log.info("skill registry initialized", { count: cache.size })
  }

  /**
   * Get NEOLAF info for a skill by ID
   */
  export async function get(skillId: string): Promise<NEOLAFSkillInfo | undefined> {
    // Check cache first
    if (cache.has(skillId)) {
      return cache.get(skillId)
    }

    // Try loading from store
    const skill = await MemoryStore.getSkill(skillId)
    if (skill) {
      cache.set(skillId, skill)
    }
    return skill ?? undefined
  }

  /**
   * Get or create NEOLAF info for a skill
   * Used when integrating with existing skills
   */
  export async function getOrCreate(
    skillId: string,
    baseInfo: { name: string; description: string; location: string },
  ): Promise<NEOLAFSkillInfo> {
    const existing = await get(skillId)
    if (existing) {
      return existing
    }

    // Create new NEOLAF skill info
    const neolafInfo: NEOLAFSkillInfo = {
      id: skillId,
      name: baseInfo.name,
      version: "1.0.0",
      description: baseInfo.description,
      location: baseInfo.location,
      maturity: "memorized",
      episodes: [],
      useCount: 0,
      source: "user",
      tags: [],
      metadata: {},
    }

    // Persist and cache
    await MemoryStore.storeSkill(neolafInfo)
    cache.set(skillId, neolafInfo)

    log.debug("created NEOLAF skill info", { skillId, name: baseInfo.name })
    return neolafInfo
  }

  /**
   * Record a skill usage episode
   */
  export async function recordEpisode(
    skillId: string,
    episode: Omit<SkillEpisode, "timestamp">,
  ): Promise<void> {
    const skill = await get(skillId)
    if (!skill) {
      log.warn("cannot record episode for unknown skill", { skillId })
      return
    }

    const fullEpisode: SkillEpisode = {
      ...episode,
      timestamp: new Date().toISOString(),
    }

    // Update skill info
    const updated: NEOLAFSkillInfo = {
      ...skill,
      episodes: [...skill.episodes, fullEpisode],
      useCount: skill.useCount + 1,
      lastUsed: fullEpisode.timestamp,
      successRate: calculateSuccessRate([...skill.episodes, fullEpisode]),
      avgDeltaE: calculateAvgDeltaE([...skill.episodes, fullEpisode]),
    }

    // Persist and update cache
    await MemoryStore.storeSkill(updated)
    cache.set(skillId, updated)

    log.debug("recorded skill episode", {
      skillId,
      success: episode.success,
      useCount: updated.useCount,
    })
  }

  /**
   * Update skill maturity level
   */
  export async function updateMaturity(skillId: string, maturity: SkillMaturity): Promise<void> {
    const skill = await get(skillId)
    if (!skill) {
      log.warn("cannot update maturity for unknown skill", { skillId })
      return
    }

    if (skill.maturity === maturity) {
      return // No change needed
    }

    const updated: NEOLAFSkillInfo = {
      ...skill,
      maturity,
    }

    await MemoryStore.storeSkill(updated)
    cache.set(skillId, updated)

    log.info("skill maturity updated", {
      skillId,
      name: skill.name,
      from: skill.maturity,
      to: maturity,
    })
  }

  /**
   * Update skill signature
   */
  export async function updateSignature(skillId: string, signature: SkillSignature): Promise<void> {
    const skill = await get(skillId)
    if (!skill) {
      log.warn("cannot update signature for unknown skill", { skillId })
      return
    }

    const updated: NEOLAFSkillInfo = {
      ...skill,
      signature,
    }

    await MemoryStore.storeSkill(updated)
    cache.set(skillId, updated)

    log.debug("skill signature updated", { skillId })
  }

  /**
   * Get all registered skills
   */
  export async function all(): Promise<NEOLAFSkillInfo[]> {
    // Refresh from store if cache is empty
    if (cache.size === 0) {
      await init()
    }
    return Array.from(cache.values())
  }

  /**
   * Get skills by maturity level
   */
  export async function byMaturity(maturity: SkillMaturity): Promise<NEOLAFSkillInfo[]> {
    const allSkills = await all()
    return allSkills.filter((s) => s.maturity === maturity)
  }

  /**
   * Get skills applicable to a domain
   */
  export async function byDomain(domain: string): Promise<NEOLAFSkillInfo[]> {
    const allSkills = await all()
    return allSkills.filter((s) => {
      if (!s.signature?.applicableDomains) return false
      return s.signature.applicableDomains.some(
        (d) => d === domain || d === "*" || domain.startsWith(d),
      )
    })
  }

  /**
   * Clear the cache (for testing)
   */
  export function clearCache(): void {
    cache.clear()
  }

  /**
   * Calculate success rate from episodes
   */
  function calculateSuccessRate(episodes: SkillEpisode[]): number {
    if (episodes.length === 0) return 0
    const successful = episodes.filter((e) => e.success).length
    return successful / episodes.length
  }

  /**
   * Calculate average deltaE from episodes
   */
  function calculateAvgDeltaE(episodes: SkillEpisode[]): number {
    const withDeltaE = episodes.filter((e) => e.deltaE !== undefined)
    if (withDeltaE.length === 0) return 0
    const sum = withDeltaE.reduce((acc, e) => acc + (e.deltaE ?? 0), 0)
    return sum / withDeltaE.length
  }
}
