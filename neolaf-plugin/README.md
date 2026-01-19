# NEOLAF Plugin

**NEOLAF Cognitive Agent Framework** - A Claude Code plugin providing KSTAR-based learning, memory, and skill acquisition for intelligent agents.

## Overview

NEOLAF implements the **K→S→T→A→R cognitive cycle**:

- **K**nowledge: Episodic memory + semantic knowledge + skills
- **S**ituation: 4-component vector (Actor, Domain, Protocol, Now)
- **T**ask: Goal with staged execution (understand → plan → execute → validate → reflect)
- **A**ction: Plan generation with forecast (R̂)
- **R**esult: Observation + reflection + learning

## Features

### Operating Modes

| Mode | Purpose | Behavior |
|------|---------|----------|
| **LEARNING** 📚 | Knowledge acquisition | Full reflection, alternatives, narration |
| **PERFORMANCE** ⚡ | Efficient execution | Minimal overhead, proven patterns |

### Skill Acquisition

Three-level hierarchy for acquiring new capabilities:

```
Level 1: COPY      ─→  Copy from catalog (easiest)
Level 2: DELEGATE  ─→  Ask advanced agent + learn
Level 3: CREATE    ─→  Generate via skill-creator
```

### Long-term Memory

KSTAR database for persistent agent memory:

```
db/
├── episodes/       # K* entry JSON files
├── knowledge/      # Aggregated knowledge
├── schema/         # JSON schemas
└── index/          # Query indices
```

### xAPI Integration

Export learning records to Experience API format for interoperability with Learning Record Stores.

## Installation

### Local Testing

```bash
claude --plugin-dir /path/to/neolaf-plugin
```

### Permanent Installation

Add to `~/.claude/settings.json`:

```json
{
  "plugins": [
    "/path/to/neolaf-plugin"
  ]
}
```

## Commands

| Command | Description |
|---------|-------------|
| `/kstar-memory` | Manage K* entries (CRUD, query, stats) |
| `/kstar-xapi` | Export to xAPI format |
| `/copy-skill` | Copy skills from external sources |

## Agents

| Agent | Description |
|-------|-------------|
| `kstar-agent` | Main cognitive loop agent |
| `skill-generator` | Generate skills from K* patterns |

## Skills

| Skill | Description |
|-------|-------------|
| `kstar-loop` | Foundational cognitive cycle |
| `kstar-transformation` | Transform data to K* format |
| `uair-control` | Uncertainty handling |
| `skill-creator` | Create new skills |
| `kstar-xapi` | xAPI mapping |
| ... | (11 skills total) |

## Directory Structure

```
neolaf-plugin/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── commands/               # Slash commands
│   ├── kstar-memory.md
│   ├── kstar-xapi.md
│   └── copy-skill.md
├── agents/                 # Subagents
│   ├── kstar-agent.md
│   └── skill-generator.md
├── skills/                 # KSTAR skills
│   ├── kstar-loop/
│   ├── kstar-transformation/
│   ├── uair-control/
│   └── ...
├── db/                     # Memory database
│   ├── schema/
│   ├── episodes/
│   └── knowledge/
├── scripts/                # Utility scripts
│   ├── kstar_db.py
│   └── copy_skill.py
└── docs/                   # Documentation
```

## Quick Start

### Run KSTAR Loop

```python
from kstar_loop import kstar_loop

result = kstar_loop(
    knowledge={"episodes": [], "confidence": {}},
    situation={
        "actor_state": {"id": "user"},
        "domain_state": {"objective": "Learn recursion"}
    },
    task={
        "goal": "Implement recursive factorial",
        "success_criteria": ["Explain concept", "Write code", "Test"]
    },
    mode="LEARNING"  # or "PERFORMANCE"
)
```

### Query Memory

```bash
# Get stats
python scripts/kstar_db.py --db db stats

# Query episodes
python scripts/kstar_db.py --db db query --domain programming --success true

# Get knowledge
python scripts/kstar_db.py --db db knowledge --domain programming
```

### Copy a Skill

```bash
python scripts/copy_skill.py \
  ~/.claude/plugins/some-plugin/skills/useful-skill \
  skills/
```

### Export to xAPI

```bash
python scripts/kstar_db.py --db db export-xapi --output statements.json
```

## KSTAR Entry Schema

Each memory entry contains:

```json
{
  "id": "kstar_<uuid>",
  "K": {
    "prior_knowledge": [...],
    "confidence": {"domain": 0.8},
    "skills_available": [...]
  },
  "S": {
    "S_A": {"id": "user", "capabilities": {...}},
    "S_D": {"objective": "...", "domain_type": "..."},
    "S_P": {"mode": "LEARNING", "stage": "execute"},
    "S_N": {"timestamp": "...", "tools": [...]}
  },
  "T": {
    "goal": "...",
    "success_criteria": [...]
  },
  "A": {
    "plan": {...},
    "forecast": {"success_probability": 0.85}
  },
  "R": {
    "observation": {"success": true},
    "prediction_error": 0.1,
    "learning": {"lessons": [...]}
  },
  "metadata": {
    "created_at": "...",
    "tags": [...]
  }
}
```

## Integration

### With Claude Code

The plugin integrates with Claude Code's:
- Skill system (auto-discovered from `skills/`)
- Command system (slash commands from `commands/`)
- Agent system (subagents from `agents/`)

### With xAPI/LRS

Export learning records to any xAPI-compliant Learning Record Store:

```python
statements = db.export_xapi()
# Send to LRS endpoint
```

### With IEEE Standards

Supports:
- P3394: Agent interface standards
- P3428: Adaptive agent framework

## License

MIT

## Related

- [KSTAR Cognitive Framework](./skills/kstar-loop/SKILL.md)
- [Skill Acquisition Guide](./skills/kstar-loop/references/skill-acquisition.md)
- [xAPI Statement Schema](./db/schema/xapi-statement.json)
