/**
 * NEOLAF Memory Export/Import - Bundle Management
 *
 * Enables exporting and importing agent memory for transfer learning,
 * backup, and sharing.
 *
 * @module neolaf/memory/export
 */

import z from "zod"
import { Log } from "../../util/log"
import {
  type MemoryBundle,
  type KSTARTrace,
  type NEOLAFSkillInfo,
  type OracleResponse,
  MemoryBundle as MemoryBundleSchema,
} from "../types"
import { MemoryStore } from "./store"

export namespace MemoryExport {
  const log = Log.create({ service: "neolaf.memory.export" })

  /**
   * Export options
   */
  export interface ExportOptions {
    includeTraces?: boolean
    includeSkills?: boolean
    includeOracleResponses?: boolean
    sessionFilter?: string[]
    dateRange?: {
      start?: Date
      end?: Date
    }
  }

  /**
   * Export memory to a bundle
   */
  export async function exportBundle(options: ExportOptions = {}): Promise<MemoryBundle> {
    log.info("exporting memory bundle", { options })

    const {
      includeTraces = true,
      includeSkills = true,
      includeOracleResponses = true,
      sessionFilter,
      dateRange,
    } = options

    let traces: KSTARTrace[] = []
    let skills: NEOLAFSkillInfo[] = []
    let oracleResponses: OracleResponse[] = []

    // Gather data based on options
    if (includeTraces) {
      traces = await MemoryStore.queryTraces({
        sessionId: sessionFilter?.[0], // TODO: Support multiple sessions
        startDate: dateRange?.start,
        endDate: dateRange?.end,
      })
    }

    if (includeSkills) {
      skills = await MemoryStore.getAllSkills()
    }

    if (includeOracleResponses) {
      oracleResponses = await MemoryStore.getOracleResponses(true) // Only validated
    }

    // Determine date range from traces
    let startDate: string | undefined
    let endDate: string | undefined
    if (traces.length > 0) {
      const timestamps = traces.map((t) => new Date(t.timestamp).getTime())
      startDate = new Date(Math.min(...timestamps)).toISOString()
      endDate = new Date(Math.max(...timestamps)).toISOString()
    }

    const bundle: MemoryBundle = {
      version: "1.0.0",
      exportedAt: new Date().toISOString(),
      traces,
      skills,
      oracleResponses,
      metadata: {
        sessionCount: new Set(traces.map((t) => t.sessionId)).size,
        traceCount: traces.length,
        skillCount: skills.length,
        dateRange:
          startDate && endDate
            ? { start: startDate, end: endDate }
            : undefined,
      },
    }

    // Validate bundle
    const parsed = MemoryBundleSchema.safeParse(bundle)
    if (!parsed.success) {
      log.error("bundle validation failed", { issues: parsed.error.issues })
      throw new Error(`Invalid bundle: ${parsed.error.message}`)
    }

    log.info("bundle exported", {
      traces: traces.length,
      skills: skills.length,
      oracleResponses: oracleResponses.length,
    })

    return parsed.data
  }

  /**
   * Export bundle to JSON string
   */
  export async function exportToJSON(options: ExportOptions = {}): Promise<string> {
    const bundle = await exportBundle(options)
    return JSON.stringify(bundle, null, 2)
  }

  /**
   * Export bundle to file
   */
  export async function exportToFile(filepath: string, options: ExportOptions = {}): Promise<void> {
    const json = await exportToJSON(options)
    await Bun.write(filepath, json)
    log.info("bundle exported to file", { filepath })
  }

  /**
   * Import options
   */
  export interface ImportOptions {
    overwrite?: boolean
    merge?: boolean
    validateOnly?: boolean
  }

  /**
   * Import memory from a bundle
   */
  export async function importBundle(
    bundle: MemoryBundle,
    options: ImportOptions = {},
  ): Promise<{ imported: number; skipped: number; errors: string[] }> {
    log.info("importing memory bundle", { options })

    const { overwrite = false, merge = true, validateOnly = false } = options
    const result = { imported: 0, skipped: 0, errors: [] as string[] }

    // Validate bundle
    const parsed = MemoryBundleSchema.safeParse(bundle)
    if (!parsed.success) {
      result.errors.push(`Invalid bundle: ${parsed.error.message}`)
      return result
    }

    if (validateOnly) {
      log.info("bundle validation passed (dry run)")
      return result
    }

    // Import traces
    for (const trace of bundle.traces) {
      try {
        const existing = await MemoryStore.getTrace(trace.id)
        if (existing && !overwrite) {
          result.skipped++
          continue
        }
        await MemoryStore.storeTrace(trace)
        result.imported++
      } catch (error) {
        result.errors.push(`Failed to import trace ${trace.id}: ${error}`)
      }
    }

    // Import skills
    for (const skill of bundle.skills) {
      try {
        const existing = await MemoryStore.getSkill(skill.id)
        if (existing && !overwrite && !merge) {
          result.skipped++
          continue
        }
        // TODO: Merge skill episodes if merge=true
        await MemoryStore.storeSkill(skill)
        result.imported++
      } catch (error) {
        result.errors.push(`Failed to import skill ${skill.id}: ${error}`)
      }
    }

    // Import oracle responses
    for (const response of bundle.oracleResponses) {
      try {
        await MemoryStore.storeOracleResponse(response)
        result.imported++
      } catch (error) {
        result.errors.push(`Failed to import oracle response: ${error}`)
      }
    }

    log.info("bundle import complete", result)
    return result
  }

  /**
   * Import from JSON string
   */
  export async function importFromJSON(
    json: string,
    options: ImportOptions = {},
  ): Promise<ReturnType<typeof importBundle>> {
    const data = JSON.parse(json)
    const bundle = MemoryBundleSchema.parse(data)
    return importBundle(bundle, options)
  }

  /**
   * Import from file
   */
  export async function importFromFile(
    filepath: string,
    options: ImportOptions = {},
  ): Promise<ReturnType<typeof importBundle>> {
    const file = Bun.file(filepath)
    const json = await file.text()
    return importFromJSON(json, options)
  }
}
