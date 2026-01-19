---
description: Export KSTAR memory entries to xAPI format for learning record interoperability
argument-hint: [options]
allowed-tools: Read, Write, Bash
---

# KSTAR to xAPI Export

Export KSTAR memory entries as xAPI (Experience API) statements for learning analytics and interoperability with Learning Record Stores (LRS).

## Arguments

`$ARGUMENTS` options:
- `--output <file>` - Output file (default: xapi-statements.json)
- `--domain <domain>` - Filter by domain type
- `--entry <id>` - Export specific entry
- `--since <date>` - Export entries since date

## xAPI Statement Mapping

KSTAR entries are mapped to xAPI as follows:

| KSTAR | xAPI | Description |
|-------|------|-------------|
| S.S_A (Actor) | actor | Agent performing the action |
| T.stage | verb | Action type (understood, planned, executed, etc.) |
| T.goal | object | Activity being performed |
| R.observation | result | Outcome with success/completion |
| S (full vector) | context | Situational context |

## Verbs

KSTAR stages map to xAPI verbs:

| Stage | Verb IRI | Display |
|-------|----------|---------|
| understand | `https://neolaf.org/xapi/verbs/understood` | understood |
| plan | `https://neolaf.org/xapi/verbs/planned` | planned |
| execute | `https://neolaf.org/xapi/verbs/executed` | executed |
| validate | `https://neolaf.org/xapi/verbs/validated` | validated |
| reflect | `https://neolaf.org/xapi/verbs/reflected` | reflected |
| complete | `http://adlnet.gov/expapi/verbs/completed` | completed |

## Export Commands

### Export All

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db export-xapi --output statements.json
```

### Export by Domain

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db export-xapi --domain programming --output programming-statements.json
```

### Programmatic Export

```python
from kstar_db import KSTARDatabase

db = KSTARDatabase("$CLAUDE_PLUGIN_ROOT/db")

# Export all
statements = db.export_xapi()

# Export with query
statements = db.export_xapi(query_params={
    "domain": "programming",
    "success": True,
    "mode": "LEARNING"
})

# Export specific entries
statements = db.export_xapi(entry_ids=["kstar_abc123", "kstar_def456"])
```

## Example xAPI Statement

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "actor": {
    "objectType": "Agent",
    "name": "user_001",
    "account": {
      "homePage": "https://neolaf.org/agents",
      "name": "user_001"
    }
  },
  "verb": {
    "id": "https://neolaf.org/xapi/verbs/executed",
    "display": { "en-US": "executed" }
  },
  "object": {
    "objectType": "Activity",
    "id": "https://neolaf.org/activities/kstar_abc123",
    "definition": {
      "type": "https://neolaf.org/xapi/activity-types/kstar-episode",
      "name": { "en-US": "Implement recursive factorial" },
      "extensions": {
        "https://neolaf.org/xapi/extensions/kstar-entry-id": "kstar_abc123",
        "https://neolaf.org/xapi/extensions/domain-type": "programming"
      }
    }
  },
  "result": {
    "success": true,
    "completion": true,
    "extensions": {
      "https://neolaf.org/xapi/extensions/prediction-error": 0.1,
      "https://neolaf.org/xapi/extensions/lessons-learned": [
        "Always handle base case first in recursion"
      ]
    }
  },
  "context": {
    "extensions": {
      "https://neolaf.org/xapi/extensions/mode": "LEARNING",
      "https://neolaf.org/xapi/extensions/workflow-type": "tutorial"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## NEOLAF xAPI Extensions

Custom extensions for KSTAR-specific data:

| Extension IRI | Type | Description |
|---------------|------|-------------|
| `.../kstar-entry-id` | string | Original K* entry ID |
| `.../task-goal` | string | Task goal text |
| `.../domain-type` | string | Domain classification |
| `.../prediction-error` | number | R vs R̂ delta |
| `.../lessons-learned` | array | Extracted lessons |
| `.../mode` | string | LEARNING or PERFORMANCE |
| `.../workflow-type` | string | Workflow pattern |
| `.../situation-vector` | object | Full S vector |

## Sending to LRS

To send statements to a Learning Record Store:

```python
import requests

statements = db.export_xapi()

# Send to LRS
response = requests.post(
    "https://lrs.example.com/statements",
    json=statements,
    headers={
        "X-Experience-API-Version": "1.0.3",
        "Authorization": "Basic <credentials>"
    }
)
```

## Use Cases

1. **Learning Analytics**: Track agent learning progress over time
2. **Compliance**: Audit trail of agent decisions and actions
3. **Cross-Platform**: Share learning data between different systems
4. **Research**: Analyze agent cognitive patterns
5. **IEEE Standards**: Support P3394/P3428 compliance
