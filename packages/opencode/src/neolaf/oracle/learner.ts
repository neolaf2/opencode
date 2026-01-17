/**
 * NEOLAF Oracle Learner - Learning from LLM Responses
 *
 * The oracle learning loop:
 * 1. Agent encounters task without established skill
 * 2. Queries LLM oracle for guidance
 * 3. Receives candidate plan
 * 4. Validates plan against episode history
 * 5. Executes plan and records outcome
 * 6. Successful plans can be promoted to skills
 *
 * Learning happens automatically from traces:
 * - Successful tool sequences become candidate patterns
 * - Repeated success across sessions promotes to skill
 * - Failed patterns are tracked to avoid repetition
 *
 * @module neolaf/oracle/learner
 */

import z from "zod"
import { Log } from "../../util/log"
import {
  type OracleQuery,
  type OracleResponse,
  type SituationVector,
  type Task,
  type Action,
  type KSTARTrace,
  type NEOLAFSkillInfo,
  OracleQuery as OracleQuerySchema,
  OracleResponse as OracleResponseSchema,
} from "../types"
import { MemoryStore } from "../memory/store"
import { SkillValidator } from "../skill/validator"
import { SkillRegistry } from "../skill/registry"

export namespace OracleLearner {
  const log = Log.create({ service: "neolaf.oracle.learner" })

  /**
   * Oracle learner configuration
   */
  export interface Config {
    minValidationConfidence: number // Minimum confidence to accept response
    maxRetries: number // Max retries for failed validations
    autoPromoteThreshold: number // Success count before auto-promoting to skill
    patternSimilarityThreshold: number // Threshold for pattern matching
  }

  /**
   * Default configuration
   */
  export const DEFAULT_CONFIG: Config = {
    minValidationConfidence: 0.6,
    maxRetries: 2,
    autoPromoteThreshold: 3,
    patternSimilarityThreshold: 0.7,
  }

  // Current configuration
  let config = { ...DEFAULT_CONFIG }

  /**
   * Pattern represents a learned action sequence
   */
  interface Pattern {
    id: string
    domain: string
    taskPattern: string // Normalized task goal
    actions: Action[]
    successCount: number
    failureCount: number
    lastUsed: string
  }

  // In-memory pattern cache
  const patterns = new Map<string, Pattern>()

  /**
   * Configure the oracle learner
   */
  export function configure(options: Partial<Config>): void {
    config = { ...config, ...options }
    log.info("oracle learner configured", { config })
  }

  /**
   * Create an oracle query
   */
  export function createQuery(input: {
    sessionId: string
    situation: SituationVector
    task: Task
    question: string
  }): OracleQuery {
    const query: OracleQuery = {
      id: `query_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
      sessionId: input.sessionId,
      situation: input.situation,
      task: input.task,
      question: input.question,
      timestamp: new Date().toISOString(),
    }

    log.debug("created oracle query", { queryId: query.id, question: query.question })
    return query
  }

  /**
   * Process an oracle response
   *
   * This is called when the LLM provides guidance.
   * The response is validated and stored for later use.
   */
  export async function processResponse(
    query: OracleQuery,
    response: {
      content: string
      suggestedActions?: Action[]
      confidence?: number
    },
  ): Promise<OracleResponse> {
    log.debug("processing oracle response", { queryId: query.id })

    const oracleResponse: OracleResponse = {
      queryId: query.id,
      content: response.content,
      suggestedActions: response.suggestedActions ?? [],
      confidence: response.confidence,
      validated: false,
      timestamp: new Date().toISOString(),
    }

    // Validate if we have suggested actions
    if (oracleResponse.suggestedActions.length > 0) {
      const validation = await SkillValidator.validatePlan(oracleResponse.suggestedActions, {
        domain: query.situation.domain,
        task: query.task.goal,
      })

      if (validation.confidence >= config.minValidationConfidence) {
        oracleResponse.validated = true
        log.info("oracle response validated", {
          queryId: query.id,
          confidence: validation.confidence,
        })
      } else {
        log.debug("oracle response failed validation", {
          queryId: query.id,
          confidence: validation.confidence,
          issues: validation.issues,
        })
      }
    }

    // Store the response
    await MemoryStore.storeOracleResponse(oracleResponse)

    return oracleResponse
  }

  /**
   * Record execution result for an oracle response
   *
   * Called after the suggested actions are executed.
   * Successful executions can lead to skill promotion.
   */
  export async function recordExecution(
    response: OracleResponse,
    trace: KSTARTrace,
  ): Promise<{
    promoted: boolean
    skillId?: string
  }> {
    log.debug("recording oracle execution", {
      queryId: response.queryId,
      traceId: trace.id,
      success: trace.actual.result?.success,
    })

    // Update response with validation trace
    const updatedResponse: OracleResponse = {
      ...response,
      validationTraceId: trace.id,
      validated: trace.actual.result?.success ?? false,
    }

    await MemoryStore.storeOracleResponse(updatedResponse)

    // Check for skill promotion
    if (trace.actual.result?.success) {
      const promotionResult = await checkForSkillPromotion(response, trace)
      if (promotionResult.promoted) {
        return promotionResult
      }
    }

    return { promoted: false }
  }

  /**
   * Check if an oracle response pattern should become a skill
   */
  async function checkForSkillPromotion(
    response: OracleResponse,
    trace: KSTARTrace,
  ): Promise<{ promoted: boolean; skillId?: string }> {
    // Find similar validated responses
    const validatedResponses = await MemoryStore.getOracleResponses(true)

    // Group by content similarity
    // TODO M3: Implement proper content similarity
    const similarResponses = validatedResponses.filter(
      (r) =>
        r.content.length > 0 &&
        response.content.length > 0 &&
        calculateContentSimilarity(r.content, response.content) > 0.7,
    )

    if (similarResponses.length >= config.autoPromoteThreshold) {
      // Create a new skill from the pattern
      const skillId = `skill_oracle_${Date.now().toString(36)}`

      await SkillRegistry.getOrCreate(skillId, {
        name: extractSkillName(response.content),
        description: extractSkillDescription(response.content, trace.task.goal),
        location: `oracle:${response.queryId}`,
      })

      log.info("oracle response promoted to skill", {
        skillId,
        responseCount: similarResponses.length,
      })

      return { promoted: true, skillId }
    }

    return { promoted: false }
  }

  /**
   * Calculate content similarity (simple token overlap for now)
   */
  function calculateContentSimilarity(a: string, b: string): number {
    const tokenize = (s: string) =>
      new Set(
        s
          .toLowerCase()
          .split(/\W+/)
          .filter((t) => t.length > 2),
      )

    const tokensA = tokenize(a)
    const tokensB = tokenize(b)

    const intersection = new Set([...tokensA].filter((t) => tokensB.has(t)))
    const union = new Set([...tokensA, ...tokensB])

    return union.size > 0 ? intersection.size / union.size : 0
  }

  /**
   * Extract a skill name from oracle response content
   */
  function extractSkillName(content: string): string {
    // Look for patterns like "To X, you should Y" or imperative verbs
    const lines = content.split("\n").filter((l) => l.trim())
    const firstLine = lines[0] || "oracle-derived-skill"

    // Take first few words
    const words = firstLine.split(/\s+/).slice(0, 5)
    return words.join("-").toLowerCase().replace(/[^a-z0-9-]/g, "")
  }

  /**
   * Extract a skill description
   */
  function extractSkillDescription(content: string, taskGoal: string): string {
    // Combine task goal with first sentence of content
    const firstSentence = content.split(/[.!?]/)[0]?.trim() || content.slice(0, 100)
    return `Skill derived from oracle guidance for: ${taskGoal}. ${firstSentence}`
  }

  /**
   * Get unvalidated oracle responses for review
   */
  export async function getPendingResponses(): Promise<OracleResponse[]> {
    const responses = await MemoryStore.getOracleResponses(false)
    return responses.filter((r) => !r.validated && !r.validationTraceId)
  }

  /**
   * Learn from a completed trace
   *
   * This is called after each trace completion to extract patterns
   * and update the oracle's knowledge.
   */
  export async function learnFromTrace(trace: KSTARTrace): Promise<void> {
    if (!trace.actual.action || !trace.actual.result) {
      return // Incomplete trace
    }

    const domain = trace.situation.domain
    const taskPattern = normalizeTaskGoal(trace.task.goal)
    const patternId = `pattern_${domain}_${hashString(taskPattern)}`

    // Get or create pattern
    let pattern = patterns.get(patternId)
    if (!pattern) {
      pattern = {
        id: patternId,
        domain,
        taskPattern,
        actions: [],
        successCount: 0,
        failureCount: 0,
        lastUsed: new Date().toISOString(),
      }
    }

    // Update pattern with this trace's action
    if (trace.actual.result.success) {
      pattern.successCount++
      // Add or update action in pattern
      if (trace.actual.action) {
        const existingIdx = pattern.actions.findIndex((a) => a.type === trace.actual.action?.type)
        if (existingIdx >= 0) {
          // Update existing action
          pattern.actions[existingIdx] = trace.actual.action
        } else {
          pattern.actions.push(trace.actual.action)
        }
      }
    } else {
      pattern.failureCount++
    }

    pattern.lastUsed = new Date().toISOString()
    patterns.set(patternId, pattern)

    // Check if pattern should be promoted to skill
    await checkPatternPromotion(pattern)

    log.debug("learned from trace", {
      patternId,
      success: trace.actual.result.success,
      successCount: pattern.successCount,
      failureCount: pattern.failureCount,
    })
  }

  /**
   * Check if a pattern has enough evidence to become a skill
   */
  async function checkPatternPromotion(pattern: Pattern): Promise<void> {
    const successRate =
      pattern.successCount / (pattern.successCount + pattern.failureCount)

    if (
      pattern.successCount >= config.autoPromoteThreshold &&
      successRate >= config.minValidationConfidence
    ) {
      const skillId = `skill_learned_${pattern.id.replace("pattern_", "")}`

      const existing = await SkillRegistry.get(skillId)
      if (existing) {
        return // Already promoted
      }

      await SkillRegistry.getOrCreate(skillId, {
        name: `learned-${pattern.domain}-${Date.now().toString(36).slice(-4)}`,
        description: `Automatically learned pattern for: ${pattern.taskPattern}`,
        location: `pattern:${pattern.id}`,
      })

      log.info("pattern promoted to skill", {
        patternId: pattern.id,
        skillId,
        successCount: pattern.successCount,
        successRate,
      })
    }
  }

  /**
   * Get suggested actions for a task based on learned patterns
   */
  export async function getSuggestedActions(
    domain: string,
    taskGoal: string,
  ): Promise<Action[]> {
    const taskPattern = normalizeTaskGoal(taskGoal)

    // Find matching patterns
    const matchingPatterns: { pattern: Pattern; similarity: number }[] = []

    for (const pattern of patterns.values()) {
      if (pattern.domain !== domain && pattern.domain !== "*") continue

      const similarity = calculateContentSimilarity(pattern.taskPattern, taskPattern)
      if (similarity >= config.patternSimilarityThreshold) {
        matchingPatterns.push({ pattern, similarity })
      }
    }

    // Sort by success rate and similarity
    matchingPatterns.sort((a, b) => {
      const aRate = a.pattern.successCount / (a.pattern.successCount + a.pattern.failureCount)
      const bRate = b.pattern.successCount / (b.pattern.successCount + b.pattern.failureCount)
      const rateWeight = 0.6
      const simWeight = 0.4
      return (bRate * rateWeight + b.similarity * simWeight) - (aRate * rateWeight + a.similarity * simWeight)
    })

    // Return actions from best matching pattern
    if (matchingPatterns.length > 0) {
      return matchingPatterns[0].pattern.actions
    }

    return []
  }

  /**
   * Normalize a task goal for pattern matching
   */
  function normalizeTaskGoal(goal: string): string {
    return goal
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, "")
      .replace(/\s+/g, " ")
      .trim()
  }

  /**
   * Simple string hash for pattern IDs
   */
  function hashString(str: string): string {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = (hash << 5) - hash + char
      hash = hash & hash // Convert to 32bit integer
    }
    return Math.abs(hash).toString(36)
  }

  /**
   * Get all learned patterns (for debugging/export)
   */
  export function getAllPatterns(): Pattern[] {
    return Array.from(patterns.values())
  }

  /**
   * Clear all patterns (for testing)
   */
  export function clearPatterns(): void {
    patterns.clear()
  }

  /**
   * Reset configuration to defaults
   */
  export function reset(): void {
    config = { ...DEFAULT_CONFIG }
    patterns.clear()
  }
}
