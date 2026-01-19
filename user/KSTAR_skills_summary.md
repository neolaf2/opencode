# NEOLAF/KSTAR Core Skills Catalog

**11 skills** in `user/`

---

## KSTAR Cognitive Framework (6 skills)

| Skill | Relative Path | Purpose |
|-------|---------------|---------|
| **kstar-loop** | `user/kstar-loop/` | Foundational cognitive cycle: K→S→T→Â→R with 4-component situation vector, staged execution, and AAR reflection |
| **kstar-transformation** | `user/kstar-transformation/` | NL ↔ KSTAR bidirectional transformation: `(K,S,T) → (Â,R̂)` canonical encoding |
| **kstar-xapi** | `user/kstar-xapi/` | KSTAR episodes → xAPI statements for Learning Record Stores (LRS interoperability) |
| **kstar-to-skill** | `user/kstar-to-skill/` | Compile episodic K-STAR memories → executable Claude Skills with lifecycle governance |
| **kstar-skill-analyzer** | `user/kstar-skill-analyzer/` | Evaluate skills for understanding vs memorization using 2-D world model (structure × causality) |
| **uair-control** | `user/uair-control/` | Meta-controller for Uncertainty-Aware Iterative Resolution (ASK/RETRIEVE/EXECUTE/STOP loops) |

## Skill Infrastructure (3 skills)

| Skill | Relative Path | Purpose |
|-------|---------------|---------|
| **skill-creator** | `user/skill-creator/` | Guide for creating effective skills with progressive disclosure and proper SKILL.md structure |
| **skill-lifecycle-manager** | `user/skill-lifecycle-manager/` | Full lifecycle: Unknown→Candidate→Validated→Generalizing→Operational→Refined→Composed |
| **skill-dependency-analyzer** | `user/skill-dependency-analyzer/` | Map skill dependencies, generate graphs, discover capabilities for S_N.tools_available |

## Integration (2 skills)

| Skill | Relative Path | Purpose |
|-------|---------------|---------|
| **agent-skills-api** | `user/agent-skills-api/` | Claude API skills integration (Anthropic pre-built + custom), versioning, file handling |
| **mcp-builder** | `user/mcp-builder/` | Guide for creating MCP servers (TypeScript/Python) to integrate external APIs |

---

## Architecture Diagram

```
                         ┌─────────────────────────┐
                         │      kstar-loop         │  ← Core cognitive cycle
                         │   K → S → T → Â → R     │
                         └───────────┬─────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ uair-control    │    │ kstar-          │    │ kstar-xapi      │
    │ (situation      │    │ transformation  │    │ (LRS            │
    │  completion)    │    │ (memory encode) │    │  integration)   │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                     │
                                     ▼
                         ┌─────────────────────┐
                         │   kstar-to-skill    │  ← Episode → Skill compilation
                         └─────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ skill-lifecycle │  │ skill-analyzer  │  │ skill-dependency│
    │ -manager        │  │ (quality eval)  │  │ -analyzer       │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
              ▼                                         ▼
    ┌─────────────────┐                      ┌─────────────────┐
    │  skill-creator  │                      │ agent-skills-api│
    │ (authoring)     │                      │ mcp-builder     │
    └─────────────────┘                      └─────────────────┘
```

---

## Quick Reference by Function

| Function | Skills |
|----------|--------|
| **Cognitive Cycle** | kstar-loop, uair-control |
| **Memory Encoding** | kstar-transformation |
| **Interoperability** | kstar-xapi, agent-skills-api, mcp-builder |
| **Skill Compilation** | kstar-to-skill |
| **Skill Governance** | skill-lifecycle-manager, skill-creator |
| **Quality & Analysis** | kstar-skill-analyzer, skill-dependency-analyzer |

---

## Skill Ecosystem Relationships

```
kstar-loop (core cognitive cycle)
    ├── uses → uair-control (situation completion)
    ├── uses → kstar-transformation (memory encoding)
    └── produces → kstar-xapi (learning records)

kstar-to-skill (episode → skill compilation)
    ├── uses → kstar-transformation
    └── managed by → skill-lifecycle-manager

skill-creator → produces skills
skill-dependency-analyzer → audits skill ecosystem
kstar-skill-analyzer → evaluates skill quality
```
