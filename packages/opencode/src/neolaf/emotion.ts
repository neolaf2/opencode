/**
 * NEOLAF Emotion - Confidence/Risk/Value Tracking
 *
 * E (Emotion) provides fast decision-making shortcuts based on the
 * somatic marker hypothesis. Instead of full deliberation, emotional
 * signals guide agent behavior.
 *
 * Components:
 * - Confidence: Expected probability of success
 * - Risk: Perceived risk level
 * - Value: Expected value/utility
 * - Valence: Positive/negative/neutral
 * - Arousal: Activation level
 *
 * @module neolaf/emotion
 */

import z from "zod"
import { Log } from "../util/log"
import { type Emotion, type Result, Emotion as EmotionSchema } from "./types"

export namespace EmotionTracker {
  const log = Log.create({ service: "neolaf.emotion" })

  /**
   * Default neutral emotion state
   */
  export const NEUTRAL: Emotion = {
    confidence: 0.5,
    risk: 0.5,
    value: 0,
    valence: "neutral",
    arousal: 0.5,
  }

  /**
   * Create an emotion state from confidence and context
   */
  export function create(input: Partial<Emotion>): Emotion {
    return {
      confidence: input.confidence ?? 0.5,
      risk: input.risk ?? 0.5,
      value: input.value ?? 0,
      valence: input.valence ?? "neutral",
      arousal: input.arousal ?? 0.5,
    }
  }

  /**
   * Update emotion based on result outcome
   *
   * @param prior - Emotion state before action
   * @param result - Action result
   * @returns Updated emotion state
   */
  export function updateFromResult(prior: Emotion, result: Result): Emotion {
    const success = result.success

    // Adjust confidence based on outcome
    const confidenceShift = success ? 0.1 : -0.15
    const newConfidence = clamp(prior.confidence + confidenceShift, 0, 1)

    // Adjust risk perception
    const riskShift = success ? -0.05 : 0.1
    const newRisk = clamp(prior.risk + riskShift, 0, 1)

    // Update value
    const newValue = success ? clamp(prior.value + 0.1, -1, 1) : clamp(prior.value - 0.1, -1, 1)

    // Determine valence
    const valence = newValue > 0.1 ? "positive" : newValue < -0.1 ? "negative" : "neutral"

    // Arousal increases with surprise (deviation from expectation)
    const surprise = Math.abs(newConfidence - prior.confidence)
    const newArousal = clamp(prior.arousal + surprise, 0, 1)

    const updated: Emotion = {
      confidence: newConfidence,
      risk: newRisk,
      value: newValue,
      valence,
      arousal: newArousal,
    }

    log.debug("emotion updated", { prior, result: success, updated })
    return updated
  }

  /**
   * Calculate delta E (emotional shift)
   *
   * @param anticipated - Expected emotion (Ê)
   * @param actual - Actual emotion (E)
   * @returns Scalar delta representing learning signal
   */
  export function calculateDeltaE(anticipated: Emotion, actual: Emotion): number {
    // Weight components for overall delta
    const confidenceWeight = 0.4
    const riskWeight = 0.2
    const valueWeight = 0.4

    const deltaConfidence = actual.confidence - anticipated.confidence
    const deltaRisk = anticipated.risk - actual.risk // Inverted: lower risk is better
    const deltaValue = actual.value - anticipated.value

    const delta =
      deltaConfidence * confidenceWeight + deltaRisk * riskWeight + deltaValue * valueWeight

    log.debug("calculated ΔE", { anticipated, actual, delta })
    return delta
  }

  /**
   * Estimate initial emotion for a task based on skill and history
   *
   * @param skillMaturity - Maturity of relevant skill (if any)
   * @param recentSuccessRate - Recent success rate (0-1)
   * @param taskComplexity - Estimated task complexity (0-1)
   */
  export function estimate(input: {
    skillMaturity?: string
    recentSuccessRate?: number
    taskComplexity?: number
  }): Emotion {
    const { skillMaturity, recentSuccessRate = 0.5, taskComplexity = 0.5 } = input

    // Base confidence from skill maturity
    const maturityConfidence: Record<string, number> = {
      memorized: 0.3,
      understood: 0.5,
      applied: 0.7,
      created: 0.85,
      innovated: 0.95,
    }
    const baseConfidence = maturityConfidence[skillMaturity ?? ""] ?? 0.4

    // Adjust for recent performance
    const confidence = clamp(baseConfidence * 0.7 + recentSuccessRate * 0.3, 0, 1)

    // Risk inversely related to confidence, adjusted for complexity
    const risk = clamp((1 - confidence) * taskComplexity, 0, 1)

    // Value based on expected outcome
    const value = clamp((confidence - 0.5) * 2, -1, 1)

    return {
      confidence,
      risk,
      value,
      valence: value > 0 ? "positive" : value < 0 ? "negative" : "neutral",
      arousal: clamp(taskComplexity, 0.3, 0.8),
    }
  }

  /**
   * Clamp a value between min and max
   */
  function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value))
  }
}
