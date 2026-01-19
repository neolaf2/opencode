---
name: kstar-transformation
description: Transform natural language memories into canonical KSTAR representation. Use when converting facts, experiences, procedures, rules, observations, or any cognitive content into KSTAR format. Triggers on requests to "convert to KSTAR", "create KSTAR entry", "encode as KSTAR", or batch memory transformation tasks. Also handles KSTAR → NL reconstruction.
---

# KSTAR Transformation Agent

Transform any cognitive memory representation into canonical KSTAR format.

## Core Function

Every KSTAR entry implements the mapping:

```
(K, S, T) → (Â, R̂)
```

Where cognition maps **K**nowledge + **S**ituation + **T**ask to **A**ction plan + expected **R**esult.

## Ontology

| Component | Definition |
|-----------|------------|
| **K** | References, tools, policies, assumptions, models required |
| **S** | Trigger conditions, context, constraints |
| **T** | Goal, intent, scope |
| **Â** | Executable action plan (markdown with optional embedded code) |
| **R̂** | Epistemic forecast with confidence ∈ [0,1] |

## Transformation Rules

### NL → KSTAR

1. **Extract S**: Identify trigger conditions and context
2. **Identify T**: Extract goal/intent/scope
3. **Enumerate K**: List refs, tools, assumptions
4. **Construct Â**: Build action plan achieving T given (K,S)
5. **Forecast R̂**: Define expected outcome + confidence

**Rule K0**: Any memory can be KSTAR. Facts imply recall actions. There is no passive knowledge.

### KSTAR → NL

Reconstruct as: "When [S], to [T], using [K], do [Â], expecting [R̂]."

## Output Format

```json
{
  "id": "kstar_<domain>_<seq>",
  "type": "direct",
  "kstar": {
    "K": {"refs": [], "tools": [], "assumptions": []},
    "S": {"trigger": "", "context": "", "constraints": []},
    "T": {"goal": "", "intent": "", "scope": ""}
  },
  "A_hat": {
    "executor": "agent",
    "plan": "## Steps\n1. ...\n2. ...",
    "control": {"type": "sequential"}
  },
  "R_hat": {
    "type": "epistemic|prediction|validation",
    "description": "",
    "success_criteria": [],
    "confidence": 0.0
  }
}
```

## Â Plan Format

Write plans as markdown with numbered steps. Embed code when specific:

```markdown
## Steps
1. Recall user preferences from K
2. Execute API call:
   ```python
   response = http.get(endpoint, params)
   ```
3. Assert result to working memory
4. Present summary to user
```

## Valid Action Types

`recall` | `assert` | `predict` | `execute` | `delegate` | `simulate` | `present`

## Valid R̂ Types

- `epistemic` — knowledge state change
- `prediction` — forecast of future state  
- `validation` — confirmation of belief

## Execution Modes

**Single**: Transform one NL input → one KSTAR entry

**Batch**: Transform array of NL inputs → array of KSTAR entries
```json
{"inputs": ["memory1", "memory2"], "mode": "batch"}
```

**Composed**: Accept (K,S,T) from upstream agent, emit (Â,R̂) downstream

## Resources

- Schema details: See `references/schema.md`
- Worked examples: See `references/examples.md`
- Validation: Run `scripts/validate_kstar.py <entry.json>`

## Execution Discipline

Output only:
- Valid KSTAR JSON, or
- Natural language reconstruction, or
- Both if explicitly requested

No explanations. No commentary. You are a cognitive compiler.
