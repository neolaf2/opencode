---
description: Copy skills from external sources to local catalog (Level 1 skill acquisition)
argument-hint: <source> <target>
allowed-tools: Read, Write, Bash, Glob
---

# Copy Skill

Copy skills from external sources to the local NEOLAF skill catalog. This is the simplest form of skill acquisition (Level 1).

## Arguments

`$ARGUMENTS`: `<source_path> <target_directory>`

- **source**: Path to skill directory (must contain SKILL.md)
- **target**: Target directory where skill will be copied

Options:
- `--name <name>`: Override skill name
- `--dry-run`: Show what would be done without copying
- `list`: List available skills in search paths

## Usage Examples

### Copy from Plugin

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/copy_skill.py \
  ~/.claude/plugins/agent-sdk-toolkit/skills/agent-sdk-basics \
  $CLAUDE_PLUGIN_ROOT/skills/
```

### Copy from Another Project

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/copy_skill.py \
  /path/to/project/user/some-skill \
  $CLAUDE_PLUGIN_ROOT/skills/
```

### List Available Skills

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/copy_skill.py list
```

### Dry Run

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/copy_skill.py \
  ~/.claude/skills/code-review \
  $CLAUDE_PLUGIN_ROOT/skills/ \
  --dry-run
```

## Skill Sources

| Source Type | Path Pattern | Example |
|-------------|--------------|---------|
| Plugin | `~/.claude/plugins/<plugin>/skills/<skill>` | `~/.claude/plugins/agent-sdk-toolkit/skills/agent-sdk-basics` |
| User Global | `~/.claude/skills/<skill>` | `~/.claude/skills/code-review` |
| Project | `<project>/user/<skill>` | `./user/kstar-loop` |
| Remote | URL (future) | `https://skills.neolaf.org/skill-name` |

## Acquisition Record

Each copy is recorded in `.skill-acquisitions.json`:

```json
[
  {
    "name": "agent-sdk-basics",
    "source_path": "/Users/rich/.claude/plugins/agent-sdk-toolkit/skills/agent-sdk-basics",
    "target_path": "/path/to/neolaf-plugin/skills/agent-sdk-basics",
    "copied_at": "2024-01-15T10:00:00Z",
    "source_type": "plugin",
    "strategy": "copy"
  }
]
```

## Validation

Before copying, the tool validates:
- Source path exists and is a directory
- SKILL.md file exists
- SKILL.md has valid frontmatter (name, description)
- Target doesn't already exist

## Integration with K*

Copied skills are registered in the agent's knowledge base:

```python
K["skills"]["skill-name"] = {
    "source": "plugin:agent-sdk-toolkit",
    "acquired_via": "copy",
    "acquired_at": "2024-01-15T10:00:00Z",
    "usage_count": 0,
    "skill": {...}
}
```

## Skill Acquisition Hierarchy

```
Level 1: COPY      ─→  This command (easiest)
Level 2: DELEGATE  ─→  Ask advanced agent, observe and encode
Level 3: CREATE    ─→  Use skill-creator with advanced agent
```

Use `/copy-skill` when:
- Skill already exists somewhere accessible
- No customization needed
- Quick capability bootstrap required

Use higher levels when:
- Skill doesn't exist (Delegate or Create)
- Custom behavior needed (Create)
- Learning by observation desired (Delegate)
