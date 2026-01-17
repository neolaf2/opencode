/**
 * NEOLAF Plugin - Tool Execution Hook Integration
 *
 * Integrates NEOLAF trace capture into the opencode plugin system.
 * Hooks into tool.execute.before and tool.execute.after to capture
 * KSTAR-E traces for every tool invocation.
 *
 * @module neolaf/plugin
 */

import type { Hooks, PluginInput, Plugin as PluginInstance } from "@opencode-ai/plugin"
import { Log } from "../util/log"
import { MemoryStore } from "./memory/store"
import { TraceCapture } from "./memory/trace"
import { Orchestrator } from "./orchestrator"
import { Mode } from "./mode-policy"
import { EmotionTracker } from "./emotion"
import { SkillRegistry } from "./skill/registry"
import { SkillLifecycle } from "./skill/lifecycle"
import { syncSkillsWithNEOLAF, recordSkillUsage } from "./skill/loader"
import { OracleLearner } from "./oracle/learner"
import type { KSTARTrace, Action, Result, Emotion, SituationVector, Task } from "./types"

const log = Log.create({ service: "neolaf.plugin" })

/**
 * Active trace tracking for in-flight tool executions
 */
interface ActiveTrace {
  traceId: string
  builder: ReturnType<typeof TraceCapture.builder>
  startTime: number
  tool: string
  args: unknown
}

// Map of callID to active trace
const activeTraces = new Map<string, ActiveTrace>()

/**
 * NEOLAF Plugin - captures KSTAR-E traces for tool executions
 */
export const NEOLAFPlugin: PluginInstance = async (input: PluginInput): Promise<Hooks> => {
  log.info("initializing NEOLAF plugin")

  // Initialize memory store
  await MemoryStore.init().catch((err) => {
    log.error("failed to initialize memory store", { error: err })
  })

  // Initialize skill registry and sync with existing skills
  await SkillRegistry.init().catch((err) => {
    log.error("failed to initialize skill registry", { error: err })
  })

  // Sync NEOLAF metadata with existing skills
  await syncSkillsWithNEOLAF().catch((err) => {
    log.error("failed to sync skills with NEOLAF", { error: err })
  })

  return {
    /**
     * Before tool execution - create trace and record anticipated outcomes
     */
    "tool.execute.before": async (
      input: { tool: string; sessionID: string; callID: string },
      output: { args: unknown },
    ): Promise<void> => {
      if (!MemoryStore.isInitialized()) return

      try {
        const { tool, sessionID, callID } = input
        const { args } = output

        // Determine operating mode
        const mode = Mode.determineMode({
          confidence: 0.5, // TODO: Calculate from context
        })

        // Create situation vector
        const situation = TraceCapture.createSituation({
          actor: "agent",
          domain: tool,
          protocol: "tool-execution",
          now: new Date().toISOString(),
          metadata: {
            tool,
            sessionID,
            callID,
          },
        })

        // Create task from tool invocation
        const taskGoal = describeToolGoal(tool, args)
        const task = TraceCapture.createTask(taskGoal, {
          stage: "active",
        })

        // Create trace builder
        const builder = TraceCapture.builder(sessionID, mode)
          .setSituation(situation)
          .setTask(task)
          .setKnowledge({
            skillsAvailable: [], // TODO: Get available skills
            assumptions: [],
          })
          .addTag(tool)
          .addTag(`session:${sessionID}`)

        // Estimate anticipated emotion
        const anticipatedEmotion = EmotionTracker.estimate({
          taskComplexity: estimateToolComplexity(tool),
        })

        // Record anticipated outcomes
        const anticipatedAction: Action = {
          type: "tool-call",
          parameters: args as Record<string, unknown>,
          toolCalls: [
            {
              tool,
              input: args as Record<string, unknown>,
            },
          ],
        }

        const anticipatedResult: Result = {
          success: true, // Optimistic
          output: null,
        }

        builder.setAnticipated({
          action: anticipatedAction,
          result: anticipatedResult,
          emotion: anticipatedEmotion,
        })

        // Store active trace
        activeTraces.set(callID, {
          traceId: builder.id,
          builder,
          startTime: Date.now(),
          tool,
          args,
        })

        log.debug("trace started", {
          traceId: builder.id,
          tool,
          callID,
          mode,
        })
      } catch (err) {
        log.error("failed to start trace", { error: err })
      }
    },

    /**
     * After tool execution - complete trace with actual results
     */
    "tool.execute.after": async (
      input: { tool: string; sessionID: string; callID: string },
      output: { title: string; output: string; metadata: unknown },
    ): Promise<void> => {
      if (!MemoryStore.isInitialized()) return

      try {
        const { tool, callID } = input
        const activeTrace = activeTraces.get(callID)

        if (!activeTrace) {
          log.debug("no active trace for call", { callID })
          return
        }

        const { builder, startTime, args } = activeTrace
        const duration = Date.now() - startTime

        // Determine success from output
        const success = !output.output.toLowerCase().includes("error")

        // Create actual action
        const actualAction: Action = {
          type: "tool-call",
          parameters: args as Record<string, unknown>,
          toolCalls: [
            {
              tool,
              input: args as Record<string, unknown>,
              output: output.output,
            },
          ],
        }

        // Create actual result
        const actualResult: Result = {
          success,
          output: output.output,
          error: success ? undefined : output.output,
          metrics: {
            duration,
          },
        }

        // Calculate actual emotion based on result
        const anticipatedEmotion = builder.build().anticipated.emotion ?? EmotionTracker.NEUTRAL
        const actualEmotion = EmotionTracker.updateFromResult(anticipatedEmotion, actualResult)

        // Complete the trace
        builder.setAction(actualAction).setResult(actualResult).setEmotion(actualEmotion)

        const trace = builder.build()

        // Store the trace
        await MemoryStore.storeTrace(trace)

        // Clean up active trace
        activeTraces.delete(callID)

        // Learn from the trace (pattern extraction and skill promotion)
        await OracleLearner.learnFromTrace(trace).catch((err) => {
          log.debug("oracle learning failed", { error: err })
        })

        log.debug("trace completed", {
          traceId: trace.id,
          tool,
          callID,
          success,
          duration,
          deltaE: trace.deltas.emotion,
        })
      } catch (err) {
        log.error("failed to complete trace", { error: err })
        // Clean up on error
        activeTraces.delete(input.callID)
      }
    },
  }
}

/**
 * Generate a human-readable goal description for a tool invocation
 */
function describeToolGoal(tool: string, args: unknown): string {
  const argObj = args as Record<string, unknown>

  switch (tool) {
    case "bash":
      return `Execute command: ${truncate(String(argObj.command ?? ""), 50)}`
    case "read":
      return `Read file: ${argObj.file_path ?? argObj.filePath ?? "unknown"}`
    case "write":
      return `Write file: ${argObj.file_path ?? argObj.filePath ?? "unknown"}`
    case "edit":
      return `Edit file: ${argObj.file_path ?? argObj.filePath ?? "unknown"}`
    case "glob":
      return `Find files matching: ${argObj.pattern ?? "unknown"}`
    case "grep":
      return `Search for: ${truncate(String(argObj.pattern ?? ""), 30)}`
    case "task":
      return `Execute subagent task: ${truncate(String(argObj.prompt ?? ""), 50)}`
    default:
      return `Execute tool: ${tool}`
  }
}

/**
 * Estimate tool complexity for emotion calculation
 */
function estimateToolComplexity(tool: string): number {
  const complexityMap: Record<string, number> = {
    bash: 0.7, // Commands can have complex effects
    read: 0.2, // Simple file read
    write: 0.5, // File creation/modification
    edit: 0.6, // Targeted edits
    glob: 0.3, // File pattern matching
    grep: 0.4, // Content search
    task: 0.8, // Subagent tasks are complex
    webfetch: 0.5, // External network call
    websearch: 0.5, // External search
  }

  return complexityMap[tool] ?? 0.5
}

/**
 * Truncate a string to a maximum length
 */
function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - 3) + "..."
}
