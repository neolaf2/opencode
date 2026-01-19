# KSTAR Canonical Schema Reference

## Entry Structure

```json
{
  "id": "kstar_<uuid>",
  "type": "direct",
  "kstar": {
    "K": { },
    "S": { },
    "T": { }
  },
  "A_hat": { },
  "R_hat": { },
  "metadata": { }
}
```

## Component Specifications

### K (Knowledge)

References, assumptions, tools, policies, prior memories, or models required for cognition.

```json
"K": {
  "refs": ["memory_id_1", "memory_id_2"],
  "tools": ["tool_name"],
  "policies": ["policy_ref"],
  "assumptions": ["assumption text"],
  "models": ["model_ref"]
}
```

Minimal form (when context is self-contained):
```json
"K": {
  "assumptions": ["Domain knowledge is available in context"]
}
```

### S (Situation)

The conditions, context, or circumstances under which the entry applies.

```json
"S": {
  "trigger": "condition that activates this memory",
  "context": "environmental or conversational context",
  "constraints": ["constraint_1", "constraint_2"]
}
```

### T (Task)

The goal, objective, or intent of cognition.

```json
"T": {
  "goal": "primary objective",
  "intent": "underlying purpose",
  "scope": "boundary of the task"
}
```

### Â (A_hat) — Action Plan

Future-directed, executable cognitive or agentic action plan.

**Markdown format** (preferred for readability):
```json
"A_hat": {
  "executor": "agent",
  "plan": "## Steps\n1. Recall X from K\n2. Assert Y to memory\n3. Present Z to user",
  "control": {
    "type": "sequential"
  }
}
```

**Structured format** (for programmatic processing):
```json
"A_hat": {
  "executor": "agent",
  "plan": [
    {
      "step": 1,
      "action": "recall",
      "target": "weather_api_endpoint",
      "using": ["memory_retrieval"],
      "inputs": ["location_context"],
      "output": "endpoint_ref"
    },
    {
      "step": 2,
      "action": "execute",
      "target": "api_call",
      "using": ["http_tool"],
      "inputs": ["endpoint_ref", "query_params"],
      "output": "weather_data"
    }
  ],
  "control": {
    "type": "sequential"
  }
}
```

**Valid action types:**
- `recall` — retrieve from memory
- `assert` — write to memory
- `predict` — generate forecast
- `execute` — run tool/function
- `delegate` — pass to subagent
- `simulate` — mental simulation
- `present` — output to user/environment

**Control types:**
- `sequential` — steps execute in order
- `conditional` — branch based on condition
- `loop` — repeat until stop_condition

### R̂ (R_hat) — Expected Result

Confidence-bearing expectation of epistemic success or future state.

```json
"R_hat": {
  "type": "epistemic | prediction | validation",
  "description": "expected cognitive or world outcome",
  "success_criteria": [
    "criterion_1",
    "criterion_2"
  ],
  "confidence": 0.85
}
```

**Type semantics:**
- `epistemic` — knowledge state change (recall success, belief update)
- `prediction` — forecast of future state
- `validation` — confirmation of existing belief

### metadata (optional)

```json
"metadata": {
  "created": "ISO8601 timestamp",
  "source": "origin of the memory",
  "tags": ["tag1", "tag2"],
  "version": "1.0"
}
```

## Validation Rules

1. All entries MUST have: `id`, `type`, `kstar`, `A_hat`, `R_hat`
2. `kstar` MUST contain non-empty: `K`, `S`, `T`
3. `A_hat` MUST contain: `executor`, `plan`
4. `R_hat` MUST contain: `type`, `description`, `confidence`
5. `confidence` MUST be in range [0.0, 1.0]
6. `type` MUST be `"direct"` (procedural reserved for future)

## ID Convention

```
kstar_<domain>_<sequence>
```

Examples:
- `kstar_weather_001`
- `kstar_auth_login_001`
- `kstar_memory_recall_001`
