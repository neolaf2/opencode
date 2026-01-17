/**
 * NEOLAF Skill Validator - Validation Against Episodes
 *
 * Validates skill definitions and candidate plans against historical episodes.
 * Used in oracle learning to verify LLM suggestions before promotion.
 *
 * @module neolaf/skill/validator
 */

import z from "zod"
import { Log } from "../../util/log"
import {
  type NEOLAFSkillInfo,
  type SkillSignature,
  type KSTARTrace,
  type Action,
  NEOLAFSkillInfo as NEOLAFSkillInfoSchema,
} from "../types"
import { MemoryStore } from "../memory/store"

export namespace SkillValidator {
  const log = Log.create({ service: "neolaf.skill.validator" })

  /**
   * Validation result
   */
  export interface ValidationResult {
    valid: boolean
    confidence: number // 0-1
    issues: string[]
    evidence: {
      supportingTraces: string[] // Trace IDs
      contradictingTraces: string[]
    }
    suggestions: string[]
  }

  /**
   * Validate a skill definition
   */
  export async function validateSkill(skill: NEOLAFSkillInfo): Promise<ValidationResult> {
    log.debug("validating skill", { skillId: skill.id, name: skill.name })

    const issues: string[] = []
    const suggestions: string[] = []
    const supportingTraces: string[] = []
    const contradictingTraces: string[] = []

    // Basic schema validation
    const parsed = NEOLAFSkillInfoSchema.safeParse(skill)
    if (!parsed.success) {
      issues.push(`Schema validation failed: ${parsed.error.message}`)
    }

    // Check required fields
    if (!skill.name || skill.name.trim() === "") {
      issues.push("Skill name is required")
    }

    if (!skill.description || skill.description.trim() === "") {
      issues.push("Skill description is required")
    }

    // Validate signature if present
    if (skill.signature) {
      const signatureIssues = validateSignature(skill.signature)
      issues.push(...signatureIssues)
    } else {
      suggestions.push("Consider adding a signature for better skill matching")
    }

    // Check against historical episodes
    if (skill.episodes.length > 0) {
      const episodeAnalysis = analyzeEpisodes(skill.episodes)

      if (episodeAnalysis.successRate < 0.5) {
        issues.push(
          `Low success rate (${(episodeAnalysis.successRate * 100).toFixed(1)}%) suggests skill may need refinement`,
        )
      }

      if (episodeAnalysis.hasNegativeTrend) {
        issues.push("Recent episodes show declining performance")
      }

      // TODO M3: Cross-reference with traces to find supporting/contradicting evidence
    }

    // Calculate confidence
    const confidence = calculateValidationConfidence(issues, suggestions, skill.episodes.length)

    const result: ValidationResult = {
      valid: issues.length === 0,
      confidence,
      issues,
      evidence: {
        supportingTraces,
        contradictingTraces,
      },
      suggestions,
    }

    log.debug("validation complete", { skillId: skill.id, result })
    return result
  }

  /**
   * Validate a candidate action plan against episode history
   */
  export async function validatePlan(
    actions: Action[],
    context: { domain?: string; task?: string },
  ): Promise<ValidationResult> {
    log.debug("validating action plan", { actionCount: actions.length, context })

    const issues: string[] = []
    const suggestions: string[] = []
    const supportingTraces: string[] = []
    const contradictingTraces: string[] = []

    // Check each action has required fields
    for (let i = 0; i < actions.length; i++) {
      const action = actions[i]
      if (!action.type) {
        issues.push(`Action ${i + 1} missing type`)
      }
    }

    // Look for similar historical traces
    const similarTraces = await findSimilarTraces(context)

    for (const trace of similarTraces) {
      const actualAction = trace.actual.action
      if (!actualAction) continue

      const similarity = calculateActionSimilarity(actions, [actualAction])
      if (similarity > 0.7) {
        if (trace.actual.result?.success) {
          supportingTraces.push(trace.id)
        } else {
          contradictingTraces.push(trace.id)
        }
      }
    }

    // Analyze evidence balance
    if (contradictingTraces.length > supportingTraces.length * 2) {
      issues.push(
        `Historical evidence suggests this approach may fail (${contradictingTraces.length} failures vs ${supportingTraces.length} successes)`,
      )
    }

    if (supportingTraces.length === 0 && contradictingTraces.length === 0) {
      suggestions.push("No historical evidence found - this is a novel approach that will need validation")
    }

    const confidence = calculatePlanConfidence(supportingTraces.length, contradictingTraces.length)

    return {
      valid: issues.length === 0,
      confidence,
      issues,
      evidence: {
        supportingTraces,
        contradictingTraces,
      },
      suggestions,
    }
  }

  /**
   * Validate a skill signature
   */
  function validateSignature(signature: SkillSignature): string[] {
    const issues: string[] = []

    // Check input definitions
    for (const input of signature.inputs) {
      if (!input.name || input.name.trim() === "") {
        issues.push("Input missing name")
      }
      if (!input.type || input.type.trim() === "") {
        issues.push(`Input "${input.name}" missing type`)
      }
    }

    // Check output definitions
    for (const output of signature.outputs) {
      if (!output.name || output.name.trim() === "") {
        issues.push("Output missing name")
      }
      if (!output.type || output.type.trim() === "") {
        issues.push(`Output "${output.name}" missing type`)
      }
    }

    // Check pre/post conditions are non-empty strings
    for (const pre of signature.preconditions) {
      if (pre.trim() === "") {
        issues.push("Empty precondition")
      }
    }

    for (const post of signature.postconditions) {
      if (post.trim() === "") {
        issues.push("Empty postcondition")
      }
    }

    return issues
  }

  /**
   * Analyze episode history
   */
  function analyzeEpisodes(episodes: { success: boolean; deltaE?: number }[]): {
    successRate: number
    hasNegativeTrend: boolean
    avgDeltaE: number
  } {
    if (episodes.length === 0) {
      return { successRate: 0, hasNegativeTrend: false, avgDeltaE: 0 }
    }

    const successCount = episodes.filter((e) => e.success).length
    const successRate = successCount / episodes.length

    // Check for negative trend in last 5 episodes
    const recent = episodes.slice(-5)
    const recentSuccessRate = recent.filter((e) => e.success).length / recent.length
    const hasNegativeTrend = recentSuccessRate < successRate - 0.2

    // Calculate average deltaE
    const withDeltaE = episodes.filter((e) => e.deltaE !== undefined)
    const avgDeltaE =
      withDeltaE.length > 0
        ? withDeltaE.reduce((sum, e) => sum + (e.deltaE ?? 0), 0) / withDeltaE.length
        : 0

    return { successRate, hasNegativeTrend, avgDeltaE }
  }

  /**
   * Calculate validation confidence
   */
  function calculateValidationConfidence(
    issues: string[],
    suggestions: string[],
    episodeCount: number,
  ): number {
    let confidence = 1.0

    // Reduce for each issue
    confidence -= issues.length * 0.2

    // Slight reduction for suggestions (not critical)
    confidence -= suggestions.length * 0.05

    // Boost for more episodes (more evidence)
    const episodeBonus = Math.min(0.2, episodeCount * 0.02)
    confidence += episodeBonus

    return Math.max(0, Math.min(1, confidence))
  }

  /**
   * Calculate plan confidence from evidence
   */
  function calculatePlanConfidence(supporting: number, contradicting: number): number {
    const total = supporting + contradicting
    if (total === 0) return 0.5 // No evidence

    const supportRatio = supporting / total
    // Scale from 0.5 (all contradicting) to 1.0 (all supporting)
    return 0.5 + supportRatio * 0.5
  }

  /**
   * Find similar historical traces
   */
  async function findSimilarTraces(context: {
    domain?: string
    task?: string
  }): Promise<KSTARTrace[]> {
    // TODO M3: Implement semantic similarity search
    // For now, return empty (will be implemented with memory store)
    return []
  }

  /**
   * Calculate similarity between action sequences
   */
  function calculateActionSimilarity(a: Action[], b: Action[]): number {
    if (a.length === 0 || b.length === 0) return 0

    // Simple type-based similarity for now
    const aTypes = new Set(a.map((action) => action.type))
    const bTypes = new Set(b.map((action) => action.type))

    const intersection = new Set([...aTypes].filter((t) => bTypes.has(t)))
    const union = new Set([...aTypes, ...bTypes])

    return intersection.size / union.size // Jaccard similarity
  }
}
