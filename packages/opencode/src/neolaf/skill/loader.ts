/**
 * NEOLAF Skill Loader - Bridge between base skills and NEOLAF registry
 *
 * Integrates with the existing Skill system at src/skill/skill.ts to
 * enhance skills with NEOLAF metadata (maturity, episodes, signatures).
 *
 * This loader:
 * 1. Watches for skill loading events
 * 2. Creates/updates NEOLAF skill records
 * 3. Parses optional NEOLAF metadata from SKILL.md frontmatter
 *
 * @module neolaf/skill/loader
 */

import z from "zod"
import { Log } from "../../util/log"
import { Skill } from "../../skill/skill"
import { ConfigMarkdown } from "../../config/markdown"
import { SkillRegistry } from "./registry"
import { SkillLifecycle } from "./lifecycle"
import { MemoryStore } from "../memory/store"
import {
  type NEOLAFSkillInfo,
  type SkillMaturity,
  type SkillSignature,
  SkillMaturity as SkillMaturitySchema,
} from "../types"

const log = Log.create({ service: "neolaf.skill.loader" })

/**
 * Extended skill metadata schema for SKILL.md frontmatter
 */
export const NEOLAFSkillMetadata = z
  .object({
    // Standard skill fields
    name: z.string(),
    description: z.string(),

    // Optional NEOLAF fields
    neolaf: z
      .object({
        maturity: SkillMaturitySchema.optional(),
        domains: z.array(z.string()).optional(),
        inputs: z
          .array(
            z.object({
              name: z.string(),
              type: z.string(),
              description: z.string().optional(),
              required: z.boolean().optional(),
            }),
          )
          .optional(),
        outputs: z
          .array(
            z.object({
              name: z.string(),
              type: z.string(),
              description: z.string().optional(),
            }),
          )
          .optional(),
        preconditions: z.array(z.string()).optional(),
        postconditions: z.array(z.string()).optional(),
        tags: z.array(z.string()).optional(),
      })
      .optional(),
  })
  .passthrough()

export type NEOLAFSkillMetadata = z.infer<typeof NEOLAFSkillMetadata>

/**
 * Load all skills and sync with NEOLAF registry
 */
export async function syncSkillsWithNEOLAF(): Promise<void> {
  log.info("syncing skills with NEOLAF registry")

  const baseSkills = await Skill.all()
  let created = 0
  let updated = 0

  for (const skill of baseSkills) {
    try {
      const neolafInfo = await loadNEOLAFSkillInfo(skill)
      const existing = await SkillRegistry.get(neolafInfo.id)

      if (existing) {
        // Preserve episode history and metrics
        neolafInfo.episodes = existing.episodes
        neolafInfo.useCount = existing.useCount
        neolafInfo.successRate = existing.successRate
        neolafInfo.avgDeltaE = existing.avgDeltaE
        neolafInfo.lastUsed = existing.lastUsed

        // Only upgrade maturity, never downgrade from file
        if (
          neolafInfo.maturity !== existing.maturity &&
          SkillLifecycle.compareMaturity(existing.maturity, neolafInfo.maturity) > 0
        ) {
          neolafInfo.maturity = existing.maturity
        }

        updated++
      } else {
        created++
      }

      await MemoryStore.storeSkill(neolafInfo)
    } catch (err) {
      log.error("failed to sync skill", { name: skill.name, error: err })
    }
  }

  log.info("skill sync complete", { created, updated, total: baseSkills.length })
}

/**
 * Load NEOLAF skill info from a base skill
 */
async function loadNEOLAFSkillInfo(skill: Skill.Info): Promise<NEOLAFSkillInfo> {
  // Generate consistent ID from name
  const id = generateSkillId(skill.name)

  // Try to load extended metadata from SKILL.md
  let metadata: NEOLAFSkillMetadata | undefined
  try {
    const md = await ConfigMarkdown.parse(skill.location)
    const parsed = NEOLAFSkillMetadata.safeParse(md.data)
    if (parsed.success) {
      metadata = parsed.data
    }
  } catch {
    // Use basic info if parsing fails
  }

  // Build signature if NEOLAF metadata is present
  let signature: SkillSignature | undefined
  if (metadata?.neolaf) {
    const n = metadata.neolaf
    signature = {
      inputs: n.inputs?.map((i) => ({
        name: i.name,
        type: i.type,
        description: i.description,
        required: i.required ?? true,
      })) ?? [],
      outputs: n.outputs?.map((o) => ({
        name: o.name,
        type: o.type,
        description: o.description,
      })) ?? [],
      preconditions: n.preconditions ?? [],
      postconditions: n.postconditions ?? [],
      applicableDomains: n.domains ?? [],
    }
  }

  // Determine initial maturity
  const maturity: SkillMaturity = metadata?.neolaf?.maturity ?? "understood"

  // Build NEOLAF skill info
  const neolafInfo: NEOLAFSkillInfo = {
    id,
    name: skill.name,
    version: "1.0.0",
    description: skill.description,
    location: skill.location,
    maturity,
    signature,
    episodes: [],
    useCount: 0,
    source: "user",
    tags: metadata?.neolaf?.tags ?? [],
    metadata: {},
  }

  return neolafInfo
}

/**
 * Generate a consistent skill ID from name
 */
function generateSkillId(name: string): string {
  // Normalize name to create ID
  return `skill_${name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}`
}

/**
 * Get NEOLAF-enhanced skill info by name
 */
export async function getNEOLAFSkill(name: string): Promise<NEOLAFSkillInfo | undefined> {
  const id = generateSkillId(name)
  return SkillRegistry.get(id)
}

/**
 * Get all NEOLAF-enhanced skills
 */
export async function getAllNEOLAFSkills(): Promise<NEOLAFSkillInfo[]> {
  return SkillRegistry.all()
}

/**
 * Get skills matching a domain
 */
export async function getSkillsForDomain(domain: string): Promise<NEOLAFSkillInfo[]> {
  return SkillRegistry.byDomain(domain)
}

/**
 * Get skills by minimum maturity level
 */
export async function getSkillsByMinMaturity(minMaturity: SkillMaturity): Promise<NEOLAFSkillInfo[]> {
  const all = await SkillRegistry.all()
  const minLevel = SkillLifecycle.maturityToLevel(minMaturity)
  return all.filter((s) => SkillLifecycle.maturityToLevel(s.maturity) >= minLevel)
}

/**
 * Record a skill invocation from a trace
 */
export async function recordSkillUsage(
  skillName: string,
  traceId: string,
  success: boolean,
  deltaE?: number,
): Promise<void> {
  const id = generateSkillId(skillName)

  await SkillRegistry.recordEpisode(id, {
    traceId,
    success,
    deltaE,
    context: `trace:${traceId}`,
  })

  // Check for maturity promotion/demotion
  if (success) {
    await SkillLifecycle.checkAndPromote(id)
  } else {
    await SkillLifecycle.checkDemotion(id)
  }
}
