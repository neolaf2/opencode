---
name: uair-control
description: >
  Meta-control skill for Uncertainty-Aware Iterative Resolution. Orchestrates
  agent workflows by incrementally constructing schema-valid artifacts through
  bounded decision loops (ASK/RETRIEVE/EXECUTE/STOP). Use when: (1) building
  adaptive interviews or assessments, (2) progressively gathering information
  to satisfy output constraints, (3) coordinating sub-skills toward a target
  schema, (4) implementing fatigue-aware, privacy-respecting elicitation, or
  (5) completing KSTAR situation vectors with missing fields. Returns decisions
  (not user-facing content) for UI-agnostic, agent-to-agent transferable control.
---

# UAIR Control Skill

UAIR is a **control skill**, not a domain skill. It orchestrates sub-skills (interview, quiz, retrieval, execution) to incrementally construct a **schema-valid artifact** while respecting interaction budgets and policies.

## Core Principle

UAIR never directly emits user-facing content. It returns **decisions** that upstream systems render. This makes UAIR UI-agnostic and agent-to-agent transferable.

## Workflow

```
1. Receive input (task, output_schema, artifact, budget, policies)
2. GLOBAL LOOP (bounded by max_global_steps):
   a. Validate artifact against output_schema → unmet constraints
   b. If no unmet constraints → STOP (complete)
   c. Select highest-priority unmet constraint
   d. LOCAL STEP → decide: ASK | RETRIEVE | EXECUTE | STOP
   e. If ASK → return decision, pause for user response
   f. If RETRIEVE/EXECUTE → merge result into artifact, continue
3. If budget exhausted → STOP (halted)
```

## Input Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `task` | Yes | id, description, intent |
| `output_schema` | Yes | required_fields, optional_fields, constraints |
| `artifact` | Yes | Current partial artifact (object) |
| `interaction_capabilities` | Yes | can_ask_user, can_retrieve, can_execute_tools |
| `budget` | Yes | max_global_steps, max_user_questions |
| `policies` | Yes | privacy (strict/normal), fatigue (low/medium/high) |
| `available_subskills` | No | List of callable sub-skills |

See [references/schemas.md](references/schemas.md) for complete JSON Schema.

## Output

Every UAIR invocation returns:

```json
{
  "decision": {
    "type": "ASK | RETRIEVE | EXECUTE | STOP",
    "payload": { }
  },
  "artifact_delta": { },
  "status": "in_progress | complete | halted",
  "trace": {
    "global_step": 2,
    "reason": "blocking_constraint | max_steps | confidence_met"
  }
}
```

## Decision Types

| Type | When | Payload |
|------|------|---------|
| `ASK` | User input needed, budget allows | target_field, template, choices, precision |
| `RETRIEVE` | Memory/knowledge lookup can resolve | query, source, filters |
| `EXECUTE` | Tool invocation can resolve | tool_name, parameters |
| `STOP` | Complete, halted, or no resolution path | reason |

## Local Step Logic

```python
def uair_local_step(target, artifact, input):
    uncertainty = derive_uncertainty(target, artifact)
    caps = input["interaction_capabilities"]
    
    if can_resolve_by_retrieval(uncertainty) and caps["can_retrieve"]:
        return retrieve(build_retrieval_query(uncertainty))
    
    if can_resolve_by_execution(uncertainty) and caps["can_execute_tools"]:
        return execute(select_tool_call(uncertainty))
    
    if caps["can_ask_user"]:
        return ask(build_interaction_intent(uncertainty, input["policies"]))
    
    return stop(reason="no_resolution_path")
```

See [references/decision-logic.md](references/decision-logic.md) for detailed resolution strategies.

## Handling User Response

When UAIR returns `ASK`, the calling system:
1. Renders the interaction intent (chat, form, quiz UI)
2. Collects user response
3. Normalizes response into artifact delta
4. Re-invokes UAIR with merged artifact

UAIR resumes exactly where it left off.

## Policies

| Policy | Values | Effect |
|--------|--------|--------|
| `privacy` | strict / normal | Strict: No sensitive field inference, explicit consent |
| `fatigue` | low / medium / high | Low: Minimize questions, prefer retrieval/inference |

## Termination Guarantees

1. **Step budget**: `max_global_steps` hard limit
2. **Question budget**: `max_user_questions` prevents endless asking
3. **No internal loops**: LOCAL_STEP makes single decision per invocation
4. **Progress requirement**: Each RETRIEVE/EXECUTE must modify artifact
5. **Fallback STOP**: No resolution path triggers halt

## KSTAR Integration

UAIR serves as **situation completion controller** for kstar-loop:

```python
if missing_fields(S):
    uair_input = build_uair_request(S, T)
    decision = uair_control(uair_input)
    # Handle ASK/RETRIEVE/EXECUTE
    S = merge(S, decision.artifact_delta)
```

| UAIR | KSTAR |
|------|-------|
| `artifact` | K (Knowledge state) |
| `target` | T (Task goal) |
| `decision` | A (Action selection) |
| `artifact_delta` | R (Result integration) |
| `output_schema` | S (Situation constraints) |

## Files

- `scripts/uair_controller.py` - Reference implementation
- `references/schemas.md` - Complete JSON schemas
- `references/decision-logic.md` - Resolution strategy details
