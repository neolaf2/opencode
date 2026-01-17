/**
 * NEOLAF Trace Capture - KSTAR-E Trace Creation and Management
 *
 * Utilities for creating, validating, and managing KSTAR-E traces.
 *
 * @module neolaf/memory/trace
 */

import z from "zod"
import { Log } from "../../util/log"
import {
  type KSTARTrace,
  type SituationVector,
  type Task,
  type Action,
  type Result,
  type Emotion,
  type OperatingMode,
  KSTARTrace as KSTARTraceSchema,
} from "../types"

export namespace TraceCapture {
  const log = Log.create({ service: "neolaf.memory.trace" })

  /**
   * Trace builder for incremental construction
   */
  export interface TraceBuilder {
    id: string
    sessionId: string
    mode: OperatingMode
    startedAt: number

    setKnowledge(knowledge: KSTARTrace["knowledge"]): TraceBuilder
    setSituation(situation: SituationVector): TraceBuilder
    setTask(task: Task): TraceBuilder
    setAnticipated(anticipated: KSTARTrace["anticipated"]): TraceBuilder
    setAction(action: Action): TraceBuilder
    setResult(result: Result): TraceBuilder
    setEmotion(emotion: Emotion): TraceBuilder
    addTag(tag: string): TraceBuilder
    build(): KSTARTrace
  }

  /**
   * Create a new trace builder
   */
  export function builder(sessionId: string, mode: OperatingMode = "learning"): TraceBuilder {
    const id = generateTraceId()
    const startedAt = Date.now()

    let knowledge: KSTARTrace["knowledge"] = {
      skillsAvailable: [],
      assumptions: [],
    }
    let situation: SituationVector | undefined
    let task: Task | undefined
    let anticipated: KSTARTrace["anticipated"] = {}
    let action: Action | undefined
    let result: Result | undefined
    let emotion: Emotion | undefined
    let tags: string[] = []
    let parentTraceId: string | undefined

    const builder: TraceBuilder = {
      id,
      sessionId,
      mode,
      startedAt,

      setKnowledge(k) {
        knowledge = k
        return this
      },

      setSituation(s) {
        situation = s
        return this
      },

      setTask(t) {
        task = t
        return this
      },

      setAnticipated(a) {
        anticipated = a
        return this
      },

      setAction(a) {
        action = a
        return this
      },

      setResult(r) {
        result = r
        return this
      },

      setEmotion(e) {
        emotion = e
        return this
      },

      addTag(tag) {
        tags.push(tag)
        return this
      },

      build(): KSTARTrace {
        if (!situation) {
          throw new Error("Situation is required to build trace")
        }
        if (!task) {
          throw new Error("Task is required to build trace")
        }

        // Calculate deltas if we have anticipated and actual values
        let deltaR: number | undefined
        let deltaE: number | undefined

        if (anticipated.result && result) {
          deltaR = result.success ? 1 : -1
          if (anticipated.result.success !== result.success) {
            deltaR = result.success ? 0.5 : -0.5 // Unexpected outcome
          }
        }

        if (anticipated.emotion && emotion) {
          deltaE = emotion.confidence - anticipated.emotion.confidence
        }

        const trace: KSTARTrace = {
          id,
          sessionId,
          parentTraceId,
          timestamp: new Date().toISOString(),
          mode,
          knowledge,
          situation,
          task,
          anticipated,
          actual: {
            action,
            result,
            emotion,
          },
          deltas: {
            result: deltaR,
            emotion: deltaE,
          },
          tags,
          annotations: {},
        }

        // Validate before returning
        const parsed = KSTARTraceSchema.safeParse(trace)
        if (!parsed.success) {
          log.error("trace validation failed", { issues: parsed.error.issues })
          throw new Error(`Invalid trace: ${parsed.error.message}`)
        }

        log.debug("trace built", { id, task: task.goal })
        return parsed.data
      },
    }

    return builder
  }

  /**
   * Generate a unique trace ID
   */
  function generateTraceId(): string {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).slice(2, 8)
    return `trace_${timestamp}_${random}`
  }

  /**
   * Create a minimal situation vector
   */
  export function createSituation(input: {
    actor?: string
    domain?: string
    protocol?: string
    now?: string
    metadata?: Record<string, unknown>
  }): SituationVector {
    return {
      actor: input.actor ?? "agent",
      domain: input.domain ?? "general",
      protocol: input.protocol ?? "opencode",
      now: input.now ?? new Date().toISOString(),
      metadata: input.metadata,
    }
  }

  /**
   * Create a task from a goal string
   */
  export function createTask(goal: string, options?: Partial<Task>): Task {
    return {
      id: `task_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
      goal,
      stage: options?.stage ?? "pending",
      successCriteria: options?.successCriteria ?? [],
      constraints: options?.constraints ?? [],
      subtasks: options?.subtasks ?? [],
      priority: options?.priority ?? 5,
    }
  }
}
