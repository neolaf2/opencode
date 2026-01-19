# NEOLAF on OpenCode – Requirements & Implementation Specification

> **Status:** Repo‑ready v0.1  
> **Purpose:** Turn OpenCode into a NEOLAF/KSTAR learning agent via plugins, sub‑agents, and a starter skill kit.

---

## 1. Overview

This document specifies how to fork **OpenCode** and evolve it into a **NEOLAF base user‑proxy agent** that:

- Implements the **NEOLAF Agent core** (KSTAR / KSTAR‑E loop)
- Dynamically saves and rewrites memory
- Learns primarily from **Oracles** (LLMs, humans, other agents)
- Creates, validates, composes, and governs **skills** with a 5‑level maturity model
- Ships with a **starter kit** containing existing KSTAR skills

OpenCode remains the **CLI/TUI runtime and UX layer**. NEOLAF is added as a **cognitive orchestration layer**.

---

## 2. Conceptual Architecture

### 2.1 Agent Role Separation

- **OpenCode**: session management, model calls, TUI/CLI, file context
- **NEOLAF Layer**: cognition, memory, skills, learning policy

```
User → OpenCode Session
        ↓
   NEOLAF Orchestrator
        ↓
 (K,S,T) → (Â,R̂,Ê) → (A,R,E)
        ↓
   Memory Rewrite + Skill Lifecycle
```

### 2.2 Core Cognitive State (KSTAR‑E)

```
(K, S, T) → (Â, R̂, Ê) → (A, R, E)
ΔR = R − R̂
ΔE = E − Ê
```

- **Emotion (E/Ê)** is a System‑1 shortcut for confidence, risk, and value
- Learning is driven by **ΔR and ΔE**

---

## 3. Skill & Knowledge Model

### 3.1 Unified View

- Knowledge = Skills = Action Plans
- All skills manifest as **World Model Knowledge** with a **double category**:
  - **Form** (structure, pattern)
  - **Causality** (process, execution)

### 3.2 Skill Maturity Levels

1. **Memorized** – associative recall
2. **Understood** – pattern matching across episodes/sub‑episodes
3. **Applied** – validated in real or simulated environments
4. **Created / Adapted** – composed via cartesian products of meta‑skills
5. **Innovated / Invented** – hypothesis → validation → proof

Promotion/demotion is evidence‑based.

---

## 4. Operating Modes

- **Learning‑Dominant**
  - High oracle usage
  - Aggressive memory rewrite
  - Exploration‑first

- **Performance‑Dominant**
  - Skill reuse (Level ≥3)
  - Minimal oracle calls
  - Emotion used as anomaly detector

Mode switching is driven by emotion deltas and task risk.

---

## 5. Oracle Learning Policy

- Oracle is the **primary source of new skills**
- Oracle outputs are **candidate plans**, not trusted by default
- Oracle calls themselves follow KSTAR‑E as subtasks
- Skills learned from oracles must be validated before promotion

---

## 6. Functional Requirements

### 6.1 Trace Capture

For every user request, NEOLAF must persist a **KSTAR‑E trace**:

- Situation S (repo state, constraints)
- Task T (normalized + decomposed)
- Planned action Â
- Expected result R̂ (binary success for v0)
- Expected emotion Ê
- Executed action A
- Result R
- Actual emotion E
- ΔR, ΔE

### 6.2 Memory

- Local‑first persistent store (JSONL / SQLite initially)
- Rewritable (merge, split, deprecate skills)
- Exportable memory bundle for seeding new installs

### 6.3 Skill Lifecycle

- Skill objects include:
  - signature, scope, plan template
  - validation protocol
  - maturity level
  - evidence links (traces, tests)

---

## 7. Existing KSTAR Skills (Starter Kit)

The NEOLAF starter kit **must include** the following skills copied from `/opencode/user/` and indexed on startup:

- kstar-loop
- kstar-transformation
- kstar-xapi
- kstar-to-skill
- kstar-skill-analyzer
- uair-control
- skill-creator
- skill-lifecycle-manager
- skill-dependency-analyzer
- agent-skills-api
- mcp-builder

These skills form the **foundational cognitive, governance, and integration layer** of the NEOLAF agent and are treated as Level‑2 or higher seed skills, subject to further validation and promotion. fileciteturn0file0

---

## 8. Repo Layout (Concrete)

```
opencode/                  # forked upstream repo
├── cmd/
├── internal/
├── neolaf/
│   ├── runtime/             # core KSTAR‑E orchestrator
│   │   ├── orchestrator.go
│   │   ├── mode_policy.go
│   │   └── emotion.go
│   ├── memory/
│   │   ├── store.go         # interface
│   │   ├── sqlite.go
│   │   └── export.go
│   ├── skills/
│   │   ├── registry.go
│   │   ├── composer.go
│   │   └── validator.go
│   ├── subagents/
│   │   ├── oracle.go
│   │   ├── retriever.go
│   │   ├── validator.go
│   │   └── rewriter.go
│   └── config/
│       └── neolaf.yaml
├── user/                    # copied starter skill kit
│   ├── kstar-loop/
│   ├── kstar-transformation/
│   ├── kstar-xapi/
│   ├── kstar-to-skill/
│   ├── kstar-skill-analyzer/
│   ├── uair-control/
│   ├── skill-creator/
│   ├── skill-lifecycle-manager/
│   ├── skill-dependency-analyzer/
│   ├── agent-skills-api/
│   └── mcp-builder/
└── docs/
    └── NEOLAF_on_Opencode_REQUIREMENTS.md
```

---

## 9. Minimal Interfaces (Go)

### 9.1 Skill Interface

```go
type Skill interface {
    ID() string
    Version() string
    Maturity() int
    Signature() IOSchema
    Plan(ctx Context) ActionPlan
    Validate(result ExecutionResult) ValidationResult
}
```

### 9.2 Oracle Interface

```go
type Oracle interface {
    ProposePlan(ctx Context) ActionPlan
}
```

### 9.3 Memory Store

```go
type MemoryStore interface {
    SaveTrace(trace KSTARTrace) error
    LoadSkills() ([]Skill, error)
    UpdateSkill(skill Skill) error
    ExportBundle(path string) error
}
```

---

## 10. Milestones

- **M0** Fork OpenCode, add `/neolaf` skeleton
- **M1** Trace capture + local memory
- **M2** Import starter skill kit
- **M3** Oracle learning loop
- **M4** Validation + promotion
- **M5** Skill composition + world model indexing
- **M6** Dual‑mode policy

---

## 11. Acceptance Criteria (v0)

The system is acceptable when:

1. A user request produces a persisted KSTAR‑E trace
2. Existing KSTAR skills are retrieved and reused
3. Missing skills trigger oracle learning
4. Validated oracle plans become reusable skills
5. Memory can be exported and reused to seed another install

---

**End of Document**

