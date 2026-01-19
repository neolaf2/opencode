---
name: kstar-loop
description: >
  Meta-skill implementing the K→S→T→A→R cognitive cycle for any agent. Supports
  two modes: LEARNING (exploration, deep reflection, knowledge acquisition) and
  PERFORMANCE (efficient execution, minimal overhead). Provides the foundational
  control loop where Knowledge (K) conditions Situation (S) assessment, Task (T)
  decomposition drives staged planning, Action (Â) generation is forecast-validated,
  and Results (R) feed back into knowledge updates. Use when: (1) structured reasoning
  cycles needed, (2) situation-aware planning with 4-component S vector, (3) staged
  task execution, (4) reflective learning with AAR, or (5) coordination with UAIR.
  Specify mode with "learning mode" or "performance mode" in request.
---

# KSTAR Loop Skill

The KSTAR loop is the **foundational cognitive cycle** for agents. It orchestrates the flow from knowledge through situation assessment, task decomposition, action planning, execution, and reflective learning.

## Core Principle

Every agent action emerges from the cycle:

```
K → S → T → Â → Execute → R → Compare(R, R̂) → Update K → Loop
```

This skill is **domain-agnostic**. The same cycle applies whether the agent is a learning companion, coding assistant, research agent, or any other role.

## Operating Modes

The KSTAR loop supports two modes that govern cycle behavior:

### Learning Mode 📚

**Purpose**: Maximize knowledge acquisition and understanding

```
Mode = LEARNING
├── Exploration: HIGH     — Try alternatives, investigate unknowns
├── Reflection: DEEP      — Full AAR after every stage
├── UAIR bias: ASK        — Prefer clarifying questions over assumptions
├── K updates: FREQUENT   — Record detailed episodes
├── Forecast: REQUIRED    — Always generate R̂ for learning signal
└── Speed: SECONDARY      — Thoroughness over efficiency
```

**When to use**:
- New domains or unfamiliar tasks
- User wants to understand the process
- Building knowledge base for future performance
- Debugging or analyzing failures
- Training scenarios

**Behavior modifications**:
- `understand` stage: Ask clarifying questions even if could proceed
- `plan` stage: Generate multiple alternatives, explain trade-offs
- `execute` stage: Narrate actions, explain reasoning
- `validate` stage: Detailed comparison of R vs R̂
- `reflect` stage: Full AAR with lessons learned

### Performance Mode ⚡

**Purpose**: Maximize execution efficiency using existing knowledge

```
Mode = PERFORMANCE
├── Exploration: LOW      — Use proven patterns
├── Reflection: MINIMAL   — Only on errors or significant deltas
├── UAIR bias: RETRIEVE   — Use existing knowledge, avoid interruptions
├── K updates: SPARSE     — Only key outcomes
├── Forecast: OPTIONAL    — Skip if high confidence
└── Speed: PRIMARY        — Efficiency over exploration
```

**When to use**:
- Familiar tasks with established patterns
- Time-sensitive execution
- User wants results, not explanation
- Production/operational contexts
- Routine workflows

**Behavior modifications**:
- `understand` stage: Quick parse, proceed if K contains similar patterns
- `plan` stage: Select best known approach, minimal alternatives
- `execute` stage: Direct action, minimal narration
- `validate` stage: Binary pass/fail check
- `reflect` stage: Skip unless |R - R̂| > threshold

### Mode Selection

Mode is determined by:
1. **Explicit request**: "learning mode" or "performance mode" in prompt
2. **S_P.interaction_pattern**: "tutorial" → LEARNING, "production" → PERFORMANCE
3. **K confidence**: Low familiarity → LEARNING, high familiarity → PERFORMANCE
4. **Default**: LEARNING (prefer knowledge acquisition)

See [references/modes.md](references/modes.md) for detailed mode specifications.

## The KSTAR Components

### K — Knowledge

The agent's accumulated knowledge base:
- Episodic memory (past interactions, outcomes)
- Semantic knowledge (domain facts, procedures)
- Actor model (user/environment state beliefs)

### S — Situation (4-Component Vector)

```
S := ⟨S_A, S_D, S_P, S_N⟩
```

| Component | Description | Examples |
|-----------|-------------|----------|
| **S_A** | Actor state | User skills, preferences, goals, constraints |
| **S_D** | Domain state | Objectives, resources, rubrics, requirements |
| **S_P** | Protocol state | Current stage, workflow type, interaction pattern |
| **S_N** | Now state | Time, tools available, session context |

See [references/situation-schema.md](references/situation-schema.md) for complete field specifications.

### T — Task (Staged Goal Structure)

```
T := ⟨goal, stage, success_criteria, constraints⟩
```

Stages form a progression:
```
understand → plan → execute → validate → reflect
```

See [references/stage-transitions.md](references/stage-transitions.md) for transition rules.

### A — Action (Plan + Forecast)

Planning and forecasting are twin functors:

```
Π_K : (K, S, T) → Â     # Action plan generation
R_K : (K, S, Â) → R̂     # Result forecast
```

The agent generates both **what to do** (Â) and **what to expect** (R̂).

### R — Result (Observation + Reflection)

After execution:
- Observe actual result R
- Compare R vs R̂ (prediction error)
- Generate learning signal
- Update K via kstar-transformation

## The Control Loop

```python
def kstar_loop(K, S_init, T_init, mode="LEARNING"):
    """
    Main KSTAR cognitive cycle.

    Args:
        K: Knowledge state
        S_init: Initial situation vector
        T_init: Initial task state
        mode: "LEARNING" or "PERFORMANCE"
    """
    S = S_init
    T = T_init
    episodes = []

    # Mode-specific thresholds
    config = MODE_CONFIG[mode]

    while T.stage != "complete":
        # 1. Situation completion (mode affects UAIR behavior)
        if not situation_complete(S, config.required_fields):
            S = uair_complete(S, T, bias=config.uair_bias)

        # 2. Generate action plan
        A_hat = plan(K, S, T, explore=config.exploration)

        # 3. Generate forecast (optional in PERFORMANCE mode)
        if config.forecast_required or confidence(K, S, T) < config.confidence_threshold:
            R_hat = forecast(K, S, A_hat)
        else:
            R_hat = None  # Skip forecast in high-confidence PERFORMANCE

        # 4. Execute action
        R = execute(A_hat, narrate=config.narrate_actions)

        # 5. Validate (PEV)
        delta = compare(R, R_hat) if R_hat else None

        # 6. Update knowledge (frequency depends on mode)
        if config.record_all_episodes or (delta and abs(delta) > config.delta_threshold):
            episode = build_episode(S, T, A_hat, R, delta)
            episodes.append(episode)
            K = update_knowledge(K, episode)

        # 7. Stage transition
        T = next_stage(T, R, delta)

        # 8. Inter-stage reflection (LEARNING mode only)
        if mode == "LEARNING" and T.stage != "complete":
            mini_aar = reflect_on_stage(K, T, episodes[-1] if episodes else None)
            if mini_aar.insights:
                K = integrate_reflection(K, mini_aar)

    # 9. Final reflection / AAR
    if mode == "LEARNING" or any(e.delta > config.delta_threshold for e in episodes):
        aar = generate_aar(K, T, episodes, depth=config.aar_depth)
        K = integrate_reflection(K, aar)
    else:
        aar = None  # Skip AAR in PERFORMANCE if no significant deltas

    return K, aar, episodes


# Mode configurations
MODE_CONFIG = {
    "LEARNING": ModeConfig(
        exploration=0.8,           # High exploration
        uair_bias="ASK",           # Prefer questions
        forecast_required=True,    # Always forecast
        confidence_threshold=0.95, # High bar to skip forecast
        record_all_episodes=True,  # Record everything
        delta_threshold=0.0,       # Any delta triggers update
        narrate_actions=True,      # Explain what we're doing
        aar_depth="full",          # Complete AAR
        required_fields=["S_A", "S_D", "S_P", "S_N"],  # All fields
    ),
    "PERFORMANCE": ModeConfig(
        exploration=0.2,           # Low exploration
        uair_bias="RETRIEVE",      # Use existing knowledge
        forecast_required=False,   # Skip if confident
        confidence_threshold=0.7,  # Lower bar to skip forecast
        record_all_episodes=False, # Only significant events
        delta_threshold=0.3,       # Only large deltas trigger update
        narrate_actions=False,     # Minimal output
        aar_depth="summary",       # Brief AAR
        required_fields=["S_D"],   # Only domain required
    ),
}
```

## Workflow Overview

### Phase 1: Initialization
1. Load or initialize K (knowledge state)
2. Construct initial S from context
3. Parse goal into T with stage="understand"

### Phase 2: Situation Completion
1. Check S_A, S_D, S_P, S_N for required fields
2. If gaps exist → invoke `uair-control` skill
3. UAIR returns ASK/RETRIEVE/EXECUTE decisions
4. Merge responses into S until complete

### Phase 3: Staged Execution
For each stage in {understand, plan, execute, validate}:
1. Generate stage-appropriate action plan Â
2. Forecast expected result R̂
3. Execute Â
4. Observe R
5. Compute prediction error
6. Decide: advance stage, retry, or escalate

### Phase 4: Reflection
1. Aggregate episode history
2. Generate After-Action Review (AAR)
3. Extract learning deltas
4. Update K via kstar-transformation
5. Mark T.stage = "complete"

## Integration Points

### With uair-control
UAIR is the **situation completion controller**. When KSTAR detects incomplete S:

```python
if missing_fields(S):
    uair_input = build_uair_request(S, T)
    decision = uair_control(uair_input)
    # Handle ASK/RETRIEVE/EXECUTE
    S = merge(S, decision.artifact_delta)
```

### With kstar-transformation
Episodes are encoded into K via KSTAR canonical form:

```python
episode = {
    "K": knowledge_snapshot,
    "S": situation_vector,
    "T": task_state,
    "A": action_taken,
    "R": result_observed
}
kstar_entry = transform_to_kstar(episode)
K = integrate(K, kstar_entry)
```

## Stage-Specific Behaviors

| Stage | Primary Action | Success Criteria |
|-------|---------------|------------------|
| **understand** | Parse goal, clarify ambiguities | Goal decomposed, constraints identified |
| **plan** | Generate action sequence | Feasible plan with resource allocation |
| **execute** | Perform actions, invoke tools | Actions completed, outputs generated |
| **validate** | Check results against criteria | Success criteria met or gaps identified |
| **reflect** | AAR, extract lessons | Learning integrated into K |

## Situation Schema (Summary)

```json
{
  "situation": {
    "actor_state": {
      "id": "string",
      "capabilities": {},
      "preferences": {},
      "constraints": {}
    },
    "domain_state": {
      "objective": "string",
      "resources": [],
      "requirements": {},
      "rubrics": {}
    },
    "protocol_state": {
      "workflow_type": "string",
      "current_stage": "understand|plan|execute|validate|reflect",
      "interaction_pattern": "string"
    },
    "now_state": {
      "timestamp": "ISO8601",
      "tools_available": [],
      "time_budget": null,
      "session_context": {}
    }
  }
}
```

## Task Schema (Summary)

```json
{
  "task": {
    "id": "string",
    "goal": "string",
    "stage": "understand|plan|execute|validate|reflect|complete",
    "success_criteria": [],
    "constraints": {},
    "parent_task": null,
    "subtasks": []
  }
}
```

## Skill Acquisition Strategies

Beyond episodic learning (recording K→S→T→A→R episodes), the KSTAR loop supports **skill acquisition** - acquiring procedural knowledge from external sources.

### Acquisition Hierarchy

```
Level 1: COPY      ─→  Copy skill from catalog/agent (easiest)
Level 2: DELEGATE  ─→  Ask advanced agent, observe and encode
Level 3: CREATE    ─→  Use skill-creator with advanced agent (most effort)
```

### Strategy Selection

```python
def select_acquisition_strategy(capability_needed, K, sources):
    # 1. Check if skill exists in accessible catalogs
    if skill := find_in_catalogs(capability_needed, sources):
        return COPY, skill

    # 2. Check if advanced agent has capability
    if agent := find_capable_agent(capability_needed):
        return DELEGATE, agent

    # 3. Fall back to creation
    return CREATE, None
```

### Copy Skills (Level 1)

The simplest method - copy an existing skill from:
- Another agent's skill catalog
- Shared/public skill repositories
- Plugin skill directories

```bash
# Copy skill from claude-code to local catalog
/copy-skill claude-code:code-review → ~/.claude/skills/
```

### Delegate and Learn (Level 2)

Ask a more advanced agent to perform the task, then:
1. Observe execution trace
2. Extract patterns
3. Encode as local skill

### Create via Skill-Creator (Level 3)

Full skill creation pipeline:
1. Design skill with advanced agent guidance
2. Use skill-creator toolkit to scaffold
3. Implement components
4. Validate and copy to local catalog

See [references/skill-acquisition.md](references/skill-acquisition.md) for detailed protocols.

## Files

- `scripts/kstar_loop.py` - Reference implementation with mode support
- `references/situation-schema.md` - Complete S vector specification
- `references/stage-transitions.md` - Stage transition rules and conditions
- `references/modes.md` - Learning vs Performance mode specifications
- `references/skill-acquisition.md` - Skill acquisition strategies and protocols
