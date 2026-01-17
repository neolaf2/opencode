/**
 * NEOLAF Core Types - KSTAR-E Cognitive Framework
 *
 * NEOLAF (NEural Ontology Learning Agent Framework) provides cognitive
 * orchestration for LLM-based agents using the KSTAR-E loop:
 * Knowledge → Situation → Task → Action → Result + Emotion
 *
 * These schemas define the persistent memory structures for
 * agent learning and skill evolution.
 */

import z from "zod"

/**
 * Operating mode determines whether the agent is learning new skills
 * or executing with established competence.
 */
export const OperatingMode = z.enum(["learning", "performance"]).meta({ ref: "OperatingMode" })
export type OperatingMode = z.infer<typeof OperatingMode>

/**
 * Skill maturity levels following Bloom's taxonomy adaptation.
 * Skills progress through these levels based on successful episodes.
 */
export const SkillMaturity = z
  .enum([
    "memorized", // Level 1: Can recall but not apply
    "understood", // Level 2: Comprehends relationships
    "applied", // Level 3: Successfully used in practice
    "created", // Level 4: Can generate variations
    "innovated", // Level 5: Can create novel approaches
  ])
  .meta({ ref: "SkillMaturity" })
export type SkillMaturity = z.infer<typeof SkillMaturity>

/**
 * Situation vector captures the 4-component context for any action:
 * - actor: who/what is performing
 * - domain: problem space being addressed
 * - protocol: interaction patterns/constraints
 * - now: current state/timestamp
 */
export const SituationVector = z
  .object({
    actor: z.string().describe("Identity of the acting entity"),
    domain: z.string().describe("Problem domain or knowledge area"),
    protocol: z.string().describe("Interaction protocol or constraints"),
    now: z.string().describe("Current state or timestamp (ISO 8601)"),
    metadata: z.record(z.unknown()).optional().describe("Additional contextual data"),
  })
  .meta({ ref: "SituationVector" })
export type SituationVector = z.infer<typeof SituationVector>

/**
 * Task represents a staged goal with success criteria.
 * Tasks can be hierarchical (subtasks) and have constraints.
 */
export const Task = z
  .object({
    id: z.string().describe("Unique task identifier"),
    goal: z.string().describe("What the task aims to achieve"),
    stage: z
      .enum(["pending", "active", "blocked", "completed", "failed"])
      .default("pending")
      .describe("Current task stage"),
    successCriteria: z.array(z.string()).default([]).describe("Measurable criteria for success"),
    constraints: z.array(z.string()).default([]).describe("Limitations or requirements"),
    subtasks: z.array(z.lazy(() => Task)).default([]).describe("Hierarchical subtasks"),
    priority: z.number().min(0).max(10).default(5).describe("Task priority (0-10)"),
  })
  .meta({ ref: "Task" })
export type Task = z.infer<typeof Task>

/**
 * Emotion tracking for confidence/risk/value shortcuts.
 * E enables fast decision-making without full deliberation.
 *
 * Based on somatic marker hypothesis - emotional signals guide decisions.
 */
export const Emotion = z
  .object({
    confidence: z.number().min(0).max(1).describe("Confidence in success (0-1)"),
    risk: z.number().min(0).max(1).describe("Perceived risk level (0-1)"),
    value: z.number().min(-1).max(1).describe("Expected value (-1 to 1)"),
    valence: z.enum(["positive", "negative", "neutral"]).default("neutral").describe("Emotional valence"),
    arousal: z.number().min(0).max(1).default(0.5).describe("Activation level (0-1)"),
  })
  .meta({ ref: "Emotion" })
export type Emotion = z.infer<typeof Emotion>

/**
 * Action represents what was actually done.
 * Captures both the intended action and its parameters.
 */
export const Action = z
  .object({
    type: z.string().describe("Action type identifier"),
    skillUsed: z.string().optional().describe("Skill ID if a skill was invoked"),
    parameters: z.record(z.unknown()).default({}).describe("Action parameters"),
    toolCalls: z
      .array(
        z.object({
          tool: z.string(),
          input: z.record(z.unknown()),
          output: z.unknown().optional(),
        }),
      )
      .default([])
      .describe("Tool invocations during action"),
  })
  .meta({ ref: "Action" })
export type Action = z.infer<typeof Action>

/**
 * Result captures the outcome of an action.
 * Includes both the raw output and success/failure status.
 */
export const Result = z
  .object({
    success: z.boolean().describe("Whether the action achieved its goal"),
    output: z.unknown().describe("Raw output from the action"),
    error: z.string().optional().describe("Error message if failed"),
    metrics: z
      .object({
        duration: z.number().optional().describe("Execution time in ms"),
        tokens: z.number().optional().describe("Token usage"),
        cost: z.number().optional().describe("Estimated cost"),
      })
      .optional()
      .describe("Performance metrics"),
  })
  .meta({ ref: "Result" })
export type Result = z.infer<typeof Result>

/**
 * KSTAR-E Trace - The core learning record.
 *
 * Each trace captures a complete cognitive cycle:
 * - K: Knowledge state before action
 * - S: Situation context
 * - T: Task being addressed
 * - Â: Anticipated action (what we expected to do)
 * - R̂: Anticipated result (what we expected)
 * - Ê: Anticipated emotion (confidence before)
 * - A: Actual action taken
 * - R: Actual result obtained
 * - E: Actual emotion after
 * - ΔR: Result delta (actual vs expected)
 * - ΔE: Emotion delta (learning signal)
 */
export const KSTARTrace = z
  .object({
    // Identifiers
    id: z.string().describe("Unique trace identifier"),
    sessionId: z.string().describe("Session this trace belongs to"),
    parentTraceId: z.string().optional().describe("Parent trace for hierarchical tasks"),
    timestamp: z.string().datetime().describe("When the trace was created"),

    // Operating context
    mode: OperatingMode.describe("Agent operating mode during this trace"),

    // K - Knowledge state
    knowledge: z
      .object({
        skillsAvailable: z.array(z.string()).default([]).describe("Skills available at trace start"),
        priorContext: z.string().optional().describe("Relevant prior context"),
        assumptions: z.array(z.string()).default([]).describe("Assumptions made"),
      })
      .describe("Knowledge state before action"),

    // S - Situation
    situation: SituationVector.describe("Contextual situation vector"),

    // T - Task
    task: Task.describe("Task being addressed"),

    // Anticipated (hat) values - predictions before action
    anticipated: z
      .object({
        action: Action.optional().describe("Â - Expected action"),
        result: Result.optional().describe("R̂ - Expected result"),
        emotion: Emotion.optional().describe("Ê - Pre-action emotional state"),
      })
      .default({})
      .describe("Predictions before action"),

    // Actual values - what really happened
    actual: z
      .object({
        action: Action.optional().describe("A - Action actually taken"),
        result: Result.optional().describe("R - Actual result"),
        emotion: Emotion.optional().describe("E - Post-action emotional state"),
      })
      .default({})
      .describe("Actual outcomes"),

    // Deltas - learning signals
    deltas: z
      .object({
        result: z.number().optional().describe("ΔR - Result deviation (-1 to 1)"),
        emotion: z.number().optional().describe("ΔE - Emotional shift (learning signal)"),
        explanation: z.string().optional().describe("Interpretation of deltas"),
      })
      .default({})
      .describe("Deviation measures for learning"),

    // Metadata
    tags: z.array(z.string()).default([]).describe("Categorical tags"),
    annotations: z.record(z.unknown()).default({}).describe("Additional annotations"),
  })
  .meta({ ref: "KSTARTrace" })
export type KSTARTrace = z.infer<typeof KSTARTrace>

/**
 * Skill episode - a reference to a trace where this skill was used.
 * Episodes are the evidence base for skill maturity promotion.
 */
export const SkillEpisode = z
  .object({
    traceId: z.string().describe("Reference to the KSTAR trace"),
    timestamp: z.string().datetime().describe("When the episode occurred"),
    success: z.boolean().describe("Whether the skill use succeeded"),
    deltaE: z.number().optional().describe("Learning signal from this episode"),
    context: z.string().optional().describe("Brief context description"),
  })
  .meta({ ref: "SkillEpisode" })
export type SkillEpisode = z.infer<typeof SkillEpisode>

/**
 * Skill signature - the interface contract for a skill.
 * Defines inputs, outputs, and applicability conditions.
 */
export const SkillSignature = z
  .object({
    inputs: z
      .array(
        z.object({
          name: z.string(),
          type: z.string(),
          description: z.string().optional(),
          required: z.boolean().default(true),
        }),
      )
      .default([])
      .describe("Required inputs"),
    outputs: z
      .array(
        z.object({
          name: z.string(),
          type: z.string(),
          description: z.string().optional(),
        }),
      )
      .default([])
      .describe("Expected outputs"),
    preconditions: z.array(z.string()).default([]).describe("Conditions that must hold before invocation"),
    postconditions: z.array(z.string()).default([]).describe("Conditions guaranteed after successful execution"),
    applicableDomains: z.array(z.string()).default([]).describe("Domains where this skill applies"),
  })
  .meta({ ref: "SkillSignature" })
export type SkillSignature = z.infer<typeof SkillSignature>

/**
 * NEOLAF-enhanced skill information.
 * Extends base skill with maturity tracking and episode history.
 */
export const NEOLAFSkillInfo = z
  .object({
    // Core identity
    id: z.string().describe("Unique skill identifier"),
    name: z.string().describe("Human-readable skill name"),
    version: z.string().default("1.0.0").describe("Semantic version"),
    description: z.string().describe("What the skill does"),
    location: z.string().describe("File path to skill definition"),

    // NEOLAF extensions
    maturity: SkillMaturity.default("memorized").describe("Current maturity level"),
    signature: SkillSignature.optional().describe("Skill interface contract"),
    episodes: z.array(SkillEpisode).default([]).describe("Usage history"),

    // Metrics
    successRate: z.number().min(0).max(1).optional().describe("Historical success rate"),
    avgDeltaE: z.number().optional().describe("Average emotional learning signal"),
    lastUsed: z.string().datetime().optional().describe("Last usage timestamp"),
    useCount: z.number().default(0).describe("Total invocation count"),

    // Source tracking
    source: z
      .enum(["builtin", "user", "oracle", "evolved"])
      .default("user")
      .describe("How the skill was acquired"),
    parentSkillId: z.string().optional().describe("Parent skill if evolved/derived"),

    // Tags and metadata
    tags: z.array(z.string()).default([]).describe("Categorical tags"),
    metadata: z.record(z.unknown()).default({}).describe("Additional metadata"),
  })
  .meta({ ref: "NEOLAFSkillInfo" })
export type NEOLAFSkillInfo = z.infer<typeof NEOLAFSkillInfo>

/**
 * Mode policy configuration.
 * Controls when the agent switches between learning and performance modes.
 */
export const ModePolicy = z
  .object({
    defaultMode: OperatingMode.default("learning").describe("Default operating mode"),
    learningThreshold: z.number().min(0).max(1).default(0.7).describe("Confidence below which triggers learning"),
    performanceThreshold: z.number().min(0).max(1).default(0.9).describe("Confidence above which enables performance"),
    deltaEVarianceThreshold: z
      .number()
      .default(0.3)
      .describe("ΔE variance threshold for mode switching"),
    minEpisodesForPerformance: z.number().default(3).describe("Minimum successful episodes before performance mode"),
  })
  .meta({ ref: "ModePolicy" })
export type ModePolicy = z.infer<typeof ModePolicy>

/**
 * Oracle query - a request for guidance from an LLM oracle.
 */
export const OracleQuery = z
  .object({
    id: z.string().describe("Unique query identifier"),
    sessionId: z.string().describe("Session context"),
    situation: SituationVector.describe("Current situation"),
    task: Task.describe("Task needing guidance"),
    question: z.string().describe("Specific question for the oracle"),
    timestamp: z.string().datetime().describe("When the query was made"),
  })
  .meta({ ref: "OracleQuery" })
export type OracleQuery = z.infer<typeof OracleQuery>

/**
 * Oracle response - guidance received from an LLM oracle.
 * Responses are candidate plans that require validation.
 */
export const OracleResponse = z
  .object({
    queryId: z.string().describe("Reference to the query"),
    content: z.string().describe("Oracle's response content"),
    suggestedActions: z.array(Action).default([]).describe("Suggested action sequence"),
    confidence: z.number().min(0).max(1).optional().describe("Oracle's confidence in the response"),
    validated: z.boolean().default(false).describe("Whether this response has been validated"),
    validationTraceId: z.string().optional().describe("Trace from validation attempt"),
    timestamp: z.string().datetime().describe("When the response was received"),
  })
  .meta({ ref: "OracleResponse" })
export type OracleResponse = z.infer<typeof OracleResponse>

/**
 * Memory bundle - exportable snapshot of agent memory.
 * Used for transfer learning and memory persistence.
 */
export const MemoryBundle = z
  .object({
    version: z.string().default("1.0.0").describe("Bundle format version"),
    exportedAt: z.string().datetime().describe("Export timestamp"),
    traces: z.array(KSTARTrace).default([]).describe("KSTAR-E traces"),
    skills: z.array(NEOLAFSkillInfo).default([]).describe("Skill definitions"),
    oracleResponses: z.array(OracleResponse).default([]).describe("Validated oracle responses"),
    metadata: z
      .object({
        sessionCount: z.number().optional(),
        traceCount: z.number().optional(),
        skillCount: z.number().optional(),
        dateRange: z
          .object({
            start: z.string().datetime().optional(),
            end: z.string().datetime().optional(),
          })
          .optional(),
      })
      .default({})
      .describe("Summary metadata"),
  })
  .meta({ ref: "MemoryBundle" })
export type MemoryBundle = z.infer<typeof MemoryBundle>
