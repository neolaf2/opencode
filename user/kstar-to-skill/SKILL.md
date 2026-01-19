---
name: kstar-to-skill
description: >
  Compile K-STAR memory entries into executable Claude Skills (SKILL.md format).
  Use when: (1) transforming episodic experience traces into reusable skills,
  (2) generalizing from specific K-STAR instances to parameterized procedures,
  (3) creating teachable/verifiable skills from agent learning, (4) closing the
  learning loop by generating K-STAR episodes from skill execution, or
  (5) managing skill lifecycle states (candidate→validated→operational→refined).
  Triggers on "compile skill from episodes", "generalize this experience",
  "create skill from K-STAR", "extract procedure from memory", or skill refinement tasks.
---

# K-STAR to Claude Skill Compiler

Transform K-STAR memory entries into executable, parameterized, verifiable Claude Skills.

## Core Distinction

**Episode ≠ Skill**

| K-STAR Entry | Claude Skill |
|--------------|--------------|
| Evidence (single experience) | Compiled policy (generalized) |
| Instance-bound | Parameterized |
| Learning substrate | Execution artifact |
| Raw observation | Verified procedure |

A Claude Skill is a **compiled operational projection** of K-STAR experience—not a memory dump.

## Compilation Workflow

### Phase 1: Gather Episodes

Collect K-STAR entries with matching (S,T) patterns:

```python
def gather_episodes(kstar_entries, situation_pattern, task_pattern):
    """Filter entries by structural similarity."""
    return [e for e in kstar_entries 
            if matches(e.S, situation_pattern) 
            and matches(e.T, task_pattern)]
```

Minimum requirements per entry:
- S (Situation), T (Task), Â (Action Plan), R (Result)
- Verification evidence
- Context snapshot, environment signature
- Timestamp, agent identity

### Phase 2: Analyze Patterns

From collected episodes:

1. **Extract invariants** → applicability conditions
2. **Identify variables** → skill parameters  
3. **Generalize Â** → procedure with placeholders
4. **Aggregate R** → verification criteria
5. **Catalog failures** → error handling strategies

### Phase 3: Generate Skill

Produce SKILL.md conforming to Claude skill format with all required sections.

## Field Mapping Specification

See [references/field-mapping.md](references/field-mapping.md) for complete mapping rules.

### Summary Mapping Table

| K-STAR Source | Claude Skill Target | Mapping Rule |
|---------------|---------------------|--------------|
| hash(S + T + agent_id) | skill_id | Stable across versions |
| Generalized (S,T) | Description | Abstract problem class |
| Common S features | When to Use | Hard/soft guards |
| Episode constants | Inputs | Parameterize variables |
| Generalized Â | Steps | Replace literals with params |
| R success patterns | Verification | Executable/observable checks |
| Failed episodes | If Something Goes Wrong | Retry, fallback, escalate |
| Teacher reasoning | Teaching Notes | Common struggles, rationale |

## Output Structure

```
skill-name/
├── SKILL.md
│   ├── YAML frontmatter (name, description, lifecycle)
│   └── Sections: Description, When to Use, Inputs, Steps, 
│       Verification, Failure Handling, Teaching Notes
├── scripts/           # Extracted tool implementations
├── references/        # Domain knowledge, schemas
└── assets/            # Templates, resources
```

## Lifecycle Governance

Every generated skill embeds lifecycle metadata in frontmatter:

```yaml
---
name: skill-name
description: ...
lifecycle:
  state: candidate | validated | operational | refined | quarantined
  source_agent: teacher_agent_id
  derived_from: [kstar_episode_ids]
  confidence: 0.85
  last_updated: 2025-01-16T00:00:00Z
  version: 1.0.0
---
```

**Execution Rules:**
- `candidate` / `quarantined` → Refuse auto-execution unless explicit override
- `validated` → Execute with elevated monitoring
- `operational` → Standard execution
- `refined` → Track refinement lineage

## Reverse Mapping (Skill → K-STAR)

Every skill execution MUST produce a K-STAR episode. Run:

```bash
python3 scripts/reverse_map.py --skill-id <id> --execution-trace <trace.json>
```

Output episode contains:
- Bound parameters
- Executed steps (observed A)
- Verification outcome
- Updated confidence
- Delta from expected R̂

This closes the learning loop.

## Consolidation Protocol

At each consolidation cycle (minimum daily):

1. **Reconciliation** — Match episodes to skills, update success rates
2. **Boundary check** — Detect applicability violations
3. **Rewrite proposals** — Parameterize, split, merge, compose
4. **Confidence update** — Bayesian update from new evidence
5. **Version bump** — Apply approved rewrites

## Validation

Before finalizing any generated skill:

```bash
python3 scripts/validate_skill.py <skill-path>
```

Checks:
- All required sections present
- Parameters properly typed with defaults
- Verification executable/observable
- Failure handling includes escalation path
- No hidden assumptions in steps

## Integration Points

### With kstar-transformation
- Use to encode execution episodes back into K-STAR format
- Provides the canonical memory representation

### With kstar-loop
- Skills become available actions in the Action (Â) phase
- Skill execution generates episodes for the Result (R) phase

### With uair-control
- UAIR orchestrates skill compilation when episode count sufficient
- Manages progressive refinement through bounded loops

## Resources

- Field mapping details: [references/field-mapping.md](references/field-mapping.md)
- Output schema: [references/skill-schema.md](references/skill-schema.md)
- Compilation script: `scripts/compile_skill.py`
- Reverse mapping: `scripts/reverse_map.py`
- Validation: `scripts/validate_skill.py`

## Execution Discipline

Output only:
- Valid Claude Skill (SKILL.md + resources), or
- Skill execution episode (K-STAR format), or
- Validation report

Never generate skills from single episodes. Minimum 3 episodes with shared (S,T) pattern required.
