---
name: kstar-xapi
description: >
  Transform KSTAR cognitive cycle episodes into xAPI statements (v0.1) for Learning
  Record Stores. Use when: (1) recording agent reasoning traces to an LRS,
  (2) converting KSTAR episodes to xAPI format, (3) generating learning analytics
  from cognitive cycles, (4) integrating KSTAR-based agents with xAPI ecosystems,
  or (5) creating interoperable learning records from agent interactions. Includes
  formal xAPI Profile definition and Python transformer.
---

# KSTAR xAPI Skill

Transform KSTAR cognitive cycle episodes into xAPI-compliant statements for Learning Record Stores (LRS).

## Profile Overview

**Profile IRI:** `https://neolaf.ai/xapi/profiles/kstar`  
**Version:** 0.1  
**Conforms to:** xAPI 1.0.3, xAPI Profiles 1.0

## Quick Start

```python
from kstar_to_xapi import KSTARToXAPI, episode_to_xapi

# Single episode transformation
statement = episode_to_xapi(episode, "agent_001", "My Agent")

# Full cycle with all statement types
transformer = KSTARToXAPI("agent_001", "My Agent")
statements = transformer.transform_full_cycle(episodes, task, situation, aar)
```

## KSTAR → xAPI Mapping

| KSTAR | xAPI Location | Extension IRI |
|-------|---------------|---------------|
| K (Knowledge) | context.extensions | `extensions/knowledge-state` |
| S (Situation) | context.extensions | `extensions/situation-vector` |
| T (Task) | context.extensions | `extensions/task-specification` |
| Â (Action) | context.extensions | `extensions/action-plan` |
| R̂ (Forecast) | context.extensions | `extensions/forecast` |
| R (Result) | result.extensions | `extensions/prediction-error` |
| AAR | result.extensions | `extensions/aar` |

## Verbs

| Stage | Verb IRI | Display |
|-------|----------|---------|
| understand | `verbs/understood` | "understood" |
| plan | `verbs/planned` | "planned" |
| forecast | `verbs/forecasted` | "forecasted" |
| execute | `verbs/executed` | "executed" |
| validate | `verbs/validated` | "validated" |
| reflect | `verbs/reflected` | "reflected" |
| complete | `verbs/completed-cycle` | "completed cycle" |

## Activity Types

| Type | IRI | Description |
|------|-----|-------------|
| Episode | `activities/kstar-episode` | Single KSTAR iteration |
| Task | `activities/kstar-task` | Goal-directed task |
| Stage | `activities/kstar-stage` | Single stage in cycle |
| AAR | `activities/after-action-review` | Reflective review |

## Statement Templates

### Episode Statement

Records a single KSTAR episode execution:

```python
statement = transformer.transform_episode(episode)
```

**Verb:** `executed`  
**Object:** `kstar-episode`  
**Context:** K, S, T, Â  
**Result:** success, prediction-error

### Stage Completion

Records completion of a KSTAR stage:

```python
statement = transformer.transform_stage_completion(
    stage="plan",
    task=task,
    situation=situation,
    from_stage="understand",
    to_stage="execute"
)
```

### Forecast Statement

Records a prediction before execution:

```python
statement = transformer.transform_forecast(task, action_plan, forecast)
```

### Cycle Completion

Records full KSTAR cycle with AAR:

```python
statement = transformer.transform_cycle_completion(
    task=task,
    situation=situation,
    aar=aar,
    knowledge_delta=delta,
    success=True,
    duration_seconds=1500,
    score=0.85
)
```

## Full Cycle Statement Sequence

A complete KSTAR cycle generates 7 statements:

1. `understood` → stage completion
2. `planned` → stage completion
3. `forecasted` → prediction R̂
4. `executed` → episode with prediction_error
5. `validated` → stage completion
6. `reflected` → stage completion
7. `completed-cycle` → with AAR and knowledge_delta

## LRS Integration

### Sending to LRS

```python
import requests

def send_to_lrs(statement, lrs_endpoint, auth):
    response = requests.post(
        f"{lrs_endpoint}/statements",
        json=statement,
        headers={
            "Content-Type": "application/json",
            "X-Experience-API-Version": "1.0.3"
        },
        auth=auth
    )
    return response.json()
```

### Querying from LRS

```
# All episodes for a task
GET /statements?activity=https://neolaf.ai/tasks/{task_id}&related_activities=true

# All completed cycles
GET /statements?verb=https://neolaf.ai/xapi/verbs/completed-cycle

# Episodes with high prediction error
GET /statements?verb=https://neolaf.ai/xapi/verbs/executed
# Then filter by result.extensions.prediction-error > 0.5
```

## Integration with kstar-loop

```python
from kstar_loop import KSTARLoop
from kstar_to_xapi import KSTARToXAPI

# Run KSTAR loop
loop = KSTARLoop(knowledge, situation, task)
result = loop.run()

# Transform episodes to xAPI
transformer = KSTARToXAPI("agent_001", "My Agent")
for episode in result["episodes"]:
    statement = transformer.transform_episode(episode)
    send_to_lrs(statement, lrs_endpoint, auth)

# Transform AAR
if result["aar"]:
    cycle_stmt = transformer.transform_cycle_completion(
        task.to_dict(),
        situation.to_dict(),
        result["aar"],
        {"episodes_added": len(result["episodes"])}
    )
    send_to_lrs(cycle_stmt.to_dict(), lrs_endpoint, auth)
```

## Files

- `scripts/kstar_to_xapi.py` - Python transformer
- `references/kstar-profile.jsonld` - xAPI Profile definition
- `references/examples.md` - Example statements
