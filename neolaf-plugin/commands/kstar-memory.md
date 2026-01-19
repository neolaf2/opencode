---
description: Manage KSTAR memory entries - create, read, query, and analyze agent episodic memory
argument-hint: <action> [options]
allowed-tools: Read, Write, Bash, Grep, Glob
---

# KSTAR Memory Management

Manage the agent's long-term memory stored as KSTAR entries. The memory database stores complete cognitive episodes in the K→S→T→A→R format.

## Arguments

`$ARGUMENTS` specifies the action:
- `create` - Create a new K* entry from current context
- `read <id>` - Read a specific entry
- `query [filters]` - Query entries with filters
- `stats` - Show memory statistics
- `knowledge [domain]` - Get aggregated knowledge
- `lessons` - Extract lessons learned

## Database Location

```
$CLAUDE_PLUGIN_ROOT/db/
├── episodes/       # K* entry JSON files
├── knowledge/      # Aggregated knowledge
└── index/          # Query indices
```

## Actions

### Create Entry

Create a new K* entry from the current interaction:

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db create
```

Or create programmatically:

```python
from kstar_db import KSTARDatabase, KSTAREntry

db = KSTARDatabase("$CLAUDE_PLUGIN_ROOT/db")

entry = {
    "K": {
        "prior_knowledge": [...],
        "confidence": {"domain": 0.7},
        "skills_available": ["skill-1", "skill-2"]
    },
    "S": {
        "S_A": {"id": "user", "role": "learner"},
        "S_D": {"objective": "...", "domain_type": "..."},
        "S_P": {"mode": "LEARNING", "current_stage": "execute"},
        "S_N": {"timestamp": "...", "tools_available": [...]}
    },
    "T": {
        "id": "task_001",
        "goal": "...",
        "success_criteria": [...]
    },
    "A": {
        "plan": {"actions": [...]},
        "forecast": {"expected_outcome": "...", "success_probability": 0.8}
    },
    "R": {
        "observation": {"success": true, "outputs": {...}},
        "prediction_error": 0.1,
        "learning": {"lessons": ["..."]}
    },
    "metadata": {
        "tags": ["category", "project"]
    }
}

entry_id = db.create(entry)
print(f"Created: {entry_id}")
```

### Read Entry

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db read <entry_id>
```

### Query Entries

Query with filters:

```bash
# By domain
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db query --domain programming

# By success
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db query --success true

# By mode
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db query --mode LEARNING
```

### Get Statistics

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db stats
```

Output:
```json
{
  "total_entries": 150,
  "domains": ["programming", "writing", "research"],
  "success_count": 142,
  "modes": {
    "LEARNING": 100,
    "PERFORMANCE": 50
  }
}
```

### Get Aggregated Knowledge

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/kstar_db.py --db $CLAUDE_PLUGIN_ROOT/db knowledge --domain programming
```

Output:
```json
{
  "episodes_count": 75,
  "success_rate": 0.94,
  "domains": {"programming": {"count": 75, "successes": 71}},
  "lessons": ["Always validate input", "Use type hints"],
  "skills_used": {"code-review": 30, "debugging": 15},
  "confidence": {"programming": 0.94}
}
```

### Extract Lessons

Get lessons from episodes with high prediction error:

```python
db = KSTARDatabase("$CLAUDE_PLUGIN_ROOT/db")
lessons = db.extract_lessons(domain="programming", min_prediction_error=0.3)

for lesson in lessons:
    print(f"- {lesson['lesson']}")
    print(f"  From: {lesson['goal']}")
    print(f"  Error: {lesson['prediction_error']}")
```

## KSTAR Entry Schema

Each entry contains:

| Component | Description |
|-----------|-------------|
| **K** | Knowledge state - prior knowledge, confidence, available skills |
| **S** | Situation vector - Actor (S_A), Domain (S_D), Protocol (S_P), Now (S_N) |
| **T** | Task - goal, success criteria, constraints |
| **A** | Action - plan, forecast (R̂), execution trace |
| **R** | Result - observation, prediction error, learning, AAR |
| **metadata** | Entry metadata - timestamps, tags, relations |

## Integration with KSTAR Loop

The KSTAR loop automatically records episodes to the database in LEARNING mode:

```python
from kstar_loop import kstar_loop

result = kstar_loop(knowledge, situation, task, mode="LEARNING")
# Episodes are recorded to db/episodes/
```

## Workflow

1. **During execution**: KSTAR loop records episodes
2. **After reflection**: AAR and lessons extracted
3. **Query for context**: Retrieve relevant prior episodes
4. **Build knowledge**: Aggregate patterns and confidence
5. **Export to xAPI**: Generate learning records for interoperability
