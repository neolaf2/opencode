import type { Argv } from "yargs"
import { cmd } from "./cmd"
import { bootstrap } from "../bootstrap"
import { MemoryStore } from "../../neolaf/memory/store"
import { MemoryExport } from "../../neolaf/memory/export"
import { SkillRegistry } from "../../neolaf/skill/registry"
import { getAllNEOLAFSkills, syncSkillsWithNEOLAF } from "../../neolaf/skill/loader"
import { OracleLearner } from "../../neolaf/oracle/learner"

export const NEOLAFCommand = cmd({
  command: "neolaf <command>",
  describe: "NEOLAF cognitive agent management",
  builder: (yargs: Argv) => {
    return yargs
      .command(TracesCommand)
      .command(SkillsCommand)
      .command(ExportBundleCommand)
      .command(ImportBundleCommand)
      .command(StatsCommand)
      .command(PatternsCommand)
      .demandCommand(1, "Please specify a subcommand")
  },
  handler: async () => {
    // This is handled by subcommands
  },
})

/**
 * View KSTAR-E traces
 */
const TracesCommand = cmd({
  command: "traces [sessionID]",
  describe: "View KSTAR-E traces for a session",
  builder: (yargs: Argv) => {
    return yargs
      .positional("sessionID", {
        describe: "Session ID to filter traces",
        type: "string",
      })
      .option("limit", {
        describe: "Maximum number of traces to show",
        type: "number",
        default: 20,
      })
      .option("mode", {
        describe: "Filter by operating mode (learning/performance)",
        type: "string",
        choices: ["learning", "performance"],
      })
  },
  handler: async (args) => {
    await bootstrap(process.cwd(), async () => {
      await MemoryStore.init()

      const traces = await MemoryStore.queryTraces({
        sessionId: args.sessionID,
        mode: args.mode,
        limit: args.limit,
      })

      if (traces.length === 0) {
        console.log("No traces found")
        return
      }

      console.log("┌────────────────────────────────────────────────────────┐")
      console.log("│                    KSTAR-E TRACES                      │")
      console.log("├────────────────────────────────────────────────────────┤")

      for (const trace of traces) {
        const time = new Date(trace.timestamp).toLocaleString()
        const success = trace.actual.result?.success ? "✓" : "✗"
        const deltaE = trace.deltas.emotion?.toFixed(2) ?? "n/a"

        console.log(`│ ${trace.id.slice(0, 20).padEnd(20)} ${time.padEnd(20)} │`)
        console.log(`│   Mode: ${trace.mode.padEnd(12)} Success: ${success}  ΔE: ${deltaE.padStart(6)} │`)
        console.log(`│   Task: ${truncate(trace.task.goal, 44).padEnd(44)} │`)
        console.log("├────────────────────────────────────────────────────────┤")
      }

      // Replace last separator
      process.stdout.write("\x1B[1A")
      console.log("└────────────────────────────────────────────────────────┘")
      console.log(`\nShowing ${traces.length} traces`)

      await MemoryStore.close()
    })
  },
})

/**
 * View NEOLAF-enhanced skills
 */
const SkillsCommand = cmd({
  command: "skills",
  describe: "View NEOLAF-enhanced skills with maturity levels",
  builder: (yargs: Argv) => {
    return yargs
      .option("maturity", {
        describe: "Filter by minimum maturity level",
        type: "string",
        choices: ["memorized", "understood", "applied", "created", "innovated"],
      })
      .option("sync", {
        describe: "Sync skills with NEOLAF registry",
        type: "boolean",
        default: false,
      })
  },
  handler: async (args) => {
    await bootstrap(process.cwd(), async () => {
      await MemoryStore.init()
      await SkillRegistry.init()

      if (args.sync) {
        console.log("Syncing skills with NEOLAF registry...")
        await syncSkillsWithNEOLAF()
      }

      const skills = await getAllNEOLAFSkills()

      if (skills.length === 0) {
        console.log("No skills found. Run with --sync to sync existing skills.")
        return
      }

      // Filter by maturity if specified
      const maturityOrder = ["memorized", "understood", "applied", "created", "innovated"]
      const filteredSkills = args.maturity
        ? skills.filter((s) => maturityOrder.indexOf(s.maturity) >= maturityOrder.indexOf(args.maturity!))
        : skills

      console.log("┌────────────────────────────────────────────────────────┐")
      console.log("│                    NEOLAF SKILLS                       │")
      console.log("├────────────────────────────────────────────────────────┤")

      // Group by maturity
      const byMaturity = new Map<string, typeof skills>()
      for (const skill of filteredSkills) {
        const group = byMaturity.get(skill.maturity) ?? []
        group.push(skill)
        byMaturity.set(skill.maturity, group)
      }

      for (const maturity of maturityOrder) {
        const group = byMaturity.get(maturity)
        if (!group || group.length === 0) continue

        const maturityLabel = maturity.charAt(0).toUpperCase() + maturity.slice(1)
        console.log(`│ ${maturityLabel.padEnd(54)} │`)

        for (const skill of group) {
          const successRate = skill.successRate !== undefined ? `${(skill.successRate * 100).toFixed(0)}%` : "n/a"
          console.log(`│   ${truncate(skill.name, 32).padEnd(32)} Uses: ${skill.useCount.toString().padStart(4)} Success: ${successRate.padStart(4)} │`)
        }
        console.log("├────────────────────────────────────────────────────────┤")
      }

      // Replace last separator
      process.stdout.write("\x1B[1A")
      console.log("└────────────────────────────────────────────────────────┘")
      console.log(`\nTotal: ${filteredSkills.length} skills`)

      await MemoryStore.close()
    })
  },
})

/**
 * Export memory bundle
 */
const ExportBundleCommand = cmd({
  command: "export <file>",
  describe: "Export NEOLAF memory to a bundle file",
  builder: (yargs: Argv) => {
    return yargs
      .positional("file", {
        describe: "Output file path (JSON)",
        type: "string",
        demandOption: true,
      })
      .option("traces", {
        describe: "Include traces in export",
        type: "boolean",
        default: true,
      })
      .option("skills", {
        describe: "Include skills in export",
        type: "boolean",
        default: true,
      })
  },
  handler: async (args) => {
    await bootstrap(process.cwd(), async () => {
      await MemoryStore.init()

      console.log("Exporting NEOLAF memory bundle...")

      await MemoryExport.exportToFile(args.file!, {
        includeTraces: args.traces,
        includeSkills: args.skills,
      })

      console.log(`Bundle exported to: ${args.file}`)

      await MemoryStore.close()
    })
  },
})

/**
 * Import memory bundle
 */
const ImportBundleCommand = cmd({
  command: "import <file>",
  describe: "Import NEOLAF memory from a bundle file",
  builder: (yargs: Argv) => {
    return yargs
      .positional("file", {
        describe: "Input file path (JSON)",
        type: "string",
        demandOption: true,
      })
      .option("merge", {
        describe: "Merge with existing data instead of overwriting",
        type: "boolean",
        default: true,
      })
      .option("dry-run", {
        describe: "Validate bundle without importing",
        type: "boolean",
        default: false,
      })
  },
  handler: async (args) => {
    await bootstrap(process.cwd(), async () => {
      await MemoryStore.init()

      console.log(`Importing NEOLAF memory bundle from: ${args.file}`)

      const result = await MemoryExport.importFromFile(args.file!, {
        merge: args.merge,
        validateOnly: args.dryRun,
      })

      if (args.dryRun) {
        console.log("Dry run complete - no data imported")
      } else {
        console.log(`Import complete:`)
      }
      console.log(`  - Imported: ${result.imported}`)
      console.log(`  - Skipped: ${result.skipped}`)
      if (result.errors.length > 0) {
        console.log(`  - Errors: ${result.errors.length}`)
        for (const err of result.errors.slice(0, 5)) {
          console.log(`    ${err}`)
        }
      }

      await MemoryStore.close()
    })
  },
})

/**
 * View NEOLAF statistics
 */
const StatsCommand = cmd({
  command: "stats",
  describe: "Show NEOLAF memory statistics",
  builder: (yargs: Argv) => yargs,
  handler: async () => {
    await bootstrap(process.cwd(), async () => {
      await MemoryStore.init()

      const stats = await MemoryStore.getStats()
      const patterns = OracleLearner.getAllPatterns()

      console.log("┌────────────────────────────────────────────────────────┐")
      console.log("│                   NEOLAF STATISTICS                    │")
      console.log("├────────────────────────────────────────────────────────┤")
      console.log(`│ Traces:             ${stats.traceCount.toString().padStart(34)} │`)
      console.log(`│ Skills:             ${stats.skillCount.toString().padStart(34)} │`)
      console.log(`│ Oracle Responses:   ${stats.oracleResponseCount.toString().padStart(34)} │`)
      console.log(`│ Learned Patterns:   ${patterns.length.toString().padStart(34)} │`)
      console.log(`│ Database Size:      ${formatBytes(stats.dbSizeBytes).padStart(34)} │`)
      console.log("└────────────────────────────────────────────────────────┘")

      await MemoryStore.close()
    })
  },
})

/**
 * View learned patterns
 */
const PatternsCommand = cmd({
  command: "patterns",
  describe: "Show learned action patterns",
  builder: (yargs: Argv) => {
    return yargs.option("limit", {
      describe: "Maximum number of patterns to show",
      type: "number",
      default: 10,
    })
  },
  handler: async () => {
    await bootstrap(process.cwd(), async () => {
      const patterns = OracleLearner.getAllPatterns()

      if (patterns.length === 0) {
        console.log("No patterns learned yet. Patterns are extracted from successful traces.")
        return
      }

      // Sort by success count
      const sorted = [...patterns].sort((a, b) => b.successCount - a.successCount)

      console.log("┌────────────────────────────────────────────────────────┐")
      console.log("│                   LEARNED PATTERNS                     │")
      console.log("├────────────────────────────────────────────────────────┤")

      for (const pattern of sorted.slice(0, 10)) {
        const successRate = (pattern.successCount / (pattern.successCount + pattern.failureCount) * 100).toFixed(0)
        console.log(`│ ${truncate(pattern.taskPattern, 44).padEnd(44)} │`)
        console.log(`│   Domain: ${pattern.domain.padEnd(15)} Success: ${pattern.successCount.toString().padStart(3)} (${successRate}%) │`)
        console.log("├────────────────────────────────────────────────────────┤")
      }

      // Replace last separator
      process.stdout.write("\x1B[1A")
      console.log("└────────────────────────────────────────────────────────┘")
      console.log(`\nTotal: ${patterns.length} patterns`)
    })
  },
})

/**
 * Truncate a string with ellipsis
 */
function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - 3) + "..."
}

/**
 * Format bytes to human-readable
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}
