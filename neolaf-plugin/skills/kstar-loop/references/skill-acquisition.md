# Skill Acquisition Strategies

The KSTAR loop supports multiple strategies for acquiring new skills, ordered by complexity and effort.

## Acquisition Strategy Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL ACQUISITION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 1: COPY         ──→  Copy skill from another agent      │
│  (Lowest effort)            or shared catalog                   │
│                                                                 │
│  Level 2: DELEGATE     ──→  Ask advanced agent to perform      │
│  (Medium effort)            task, observe and encode           │
│                                                                 │
│  Level 3: CREATE       ──→  Use skill-creator toolkit with     │
│  (Highest effort)           advanced agent guidance            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Strategy 1: Copy Skills

The simplest acquisition method. Copy an existing skill from:
- Another agent's accessible skill catalog
- A shared/public skill repository
- A mentor agent's skill set

### When to Use

- Skill already exists and is accessible
- No customization needed
- Quick capability bootstrap

### Process

```python
def acquire_by_copy(skill_id: str, source: SkillSource) -> Skill:
    """
    Copy a skill from another agent or catalog.

    Args:
        skill_id: Identifier of skill to copy
        source: Where to copy from (agent, catalog, repository)

    Returns:
        Copied skill ready for local use
    """
    # 1. Locate skill in source
    skill = source.get_skill(skill_id)

    # 2. Validate compatibility
    if not compatible_with_local_env(skill):
        raise IncompatibleSkillError(skill_id)

    # 3. Copy to local catalog
    local_skill = copy_to_local(skill)

    # 4. Register in K
    K["skills"][skill_id] = {
        "source": source.id,
        "acquired_via": "copy",
        "acquired_at": timestamp(),
        "skill": local_skill
    }

    return local_skill
```

### Skill Source Types

| Source Type | Description | Example |
|-------------|-------------|---------|
| **Agent Catalog** | Skills from another agent | Copy from `claude-code-agent` |
| **Shared Repository** | Public/team skill repos | GitHub skills registry |
| **Mentor Agent** | Skills from teaching agent | Expert agent shares domain skills |
| **Plugin Skills** | Skills bundled in plugins | `agent-sdk-toolkit` skills |

### Copy Skill Protocol

```json
{
  "action": "copy_skill",
  "source": {
    "type": "agent_catalog",
    "agent_id": "claude-code-agent",
    "skill_id": "code-review"
  },
  "target": {
    "catalog": "local",
    "path": "~/.claude/skills/"
  },
  "options": {
    "include_references": true,
    "include_scripts": true,
    "adapt_paths": true
  }
}
```

## Strategy 2: Delegate to Advanced Agent

When the skill doesn't exist but the capability does in a more advanced agent.

### When to Use

- Task is within advanced agent's capability
- Learning by observation desired
- Skill extraction from demonstrated behavior

### Process

```python
def acquire_by_delegation(
    task: Task,
    advanced_agent: Agent,
    observe: bool = True
) -> Optional[Skill]:
    """
    Delegate task to advanced agent and optionally learn from it.

    Args:
        task: Task to perform
        advanced_agent: More capable agent to delegate to
        observe: Whether to observe and encode skill

    Returns:
        Extracted skill if observe=True, else None
    """
    # 1. Delegate task
    execution_trace = advanced_agent.execute(task)

    # 2. Get result
    result = execution_trace.result

    if not observe:
        return None

    # 3. Analyze execution trace
    patterns = extract_patterns(execution_trace)

    # 4. Encode as skill
    skill = encode_skill_from_trace(
        task=task,
        trace=execution_trace,
        patterns=patterns
    )

    # 5. Register in K
    K["skills"][skill.id] = {
        "source": advanced_agent.id,
        "acquired_via": "delegation_observation",
        "acquired_at": timestamp(),
        "original_task": task.to_dict(),
        "skill": skill
    }

    return skill
```

### Delegation Protocol

```json
{
  "action": "delegate_and_learn",
  "task": {
    "goal": "Review this Python code for security issues",
    "context": {...}
  },
  "delegate_to": {
    "agent": "claude-code",
    "model": "opus"
  },
  "learning": {
    "observe": true,
    "extract_patterns": true,
    "create_skill": true,
    "skill_name": "security-code-review"
  }
}
```

### Observation Points

When observing advanced agent execution, capture:

1. **Tool Selection** - Which tools were used and why
2. **Decision Points** - How choices were made
3. **Patterns** - Recurring sequences or templates
4. **Error Handling** - How failures were addressed
5. **Output Structure** - Format of results

## Strategy 3: Create via Skill Creator

The most sophisticated method: actively create a new skill using the skill-creator toolkit with guidance from an advanced agent.

### When to Use

- Novel capability needed
- No existing skill to copy
- Custom behavior required
- Building reusable knowledge

### Process

```python
def acquire_by_creation(
    capability_description: str,
    advanced_agent: Agent,
    skill_creator: SkillCreator
) -> Skill:
    """
    Create new skill using skill-creator with advanced agent guidance.

    Args:
        capability_description: What the skill should do
        advanced_agent: Agent to guide skill creation
        skill_creator: Skill creation toolkit

    Returns:
        Newly created skill
    """
    # 1. Design skill with advanced agent
    skill_design = advanced_agent.design_skill(capability_description)

    # 2. Use skill-creator to scaffold
    skill_scaffold = skill_creator.create_scaffold(
        name=skill_design.name,
        description=skill_design.description,
        components=skill_design.components
    )

    # 3. Advanced agent implements components
    for component in skill_scaffold.components:
        implementation = advanced_agent.implement(component)
        skill_scaffold.set_component(component.id, implementation)

    # 4. Validate skill
    validation = skill_creator.validate(skill_scaffold)
    if not validation.passed:
        # Iterate with advanced agent to fix
        skill_scaffold = advanced_agent.fix_issues(
            skill_scaffold,
            validation.issues
        )

    # 5. Register in K
    K["skills"][skill_scaffold.id] = {
        "source": "created",
        "created_by": advanced_agent.id,
        "created_via": "skill_creator",
        "created_at": timestamp(),
        "skill": skill_scaffold.finalize()
    }

    return skill_scaffold.finalize()
```

### Creation Workflow

```
User Need → Advanced Agent → Skill Creator → Validation → Local Catalog
    │              │              │              │              │
    │              ▼              │              │              │
    │      ┌──────────────┐      │              │              │
    │      │ Design Skill │      │              │              │
    │      │  Structure   │      │              │              │
    │      └──────┬───────┘      │              │              │
    │             │              ▼              │              │
    │             │      ┌──────────────┐      │              │
    │             └─────▶│   Scaffold   │      │              │
    │                    │    SKILL.md  │      │              │
    │                    │  references/ │      │              │
    │                    │   scripts/   │      │              │
    │                    └──────┬───────┘      │              │
    │                           │              ▼              │
    │                           │      ┌──────────────┐      │
    │                           └─────▶│   Validate   │      │
    │                                  │   Structure  │      │
    │                                  │   Content    │      │
    │                                  └──────┬───────┘      │
    │                                         │              ▼
    │                                         │      ┌──────────────┐
    │                                         └─────▶│ Copy to Local│
    │                                                │   Catalog    │
    │                                                └──────────────┘
```

### Skill Creator Integration

Use the `skill-creator` skill from `plugin-dev` plugin:

```markdown
## Creation Steps

1. **Understand requirements** - Gather concrete usage examples
2. **Plan components** - Identify scripts, references, assets needed
3. **Create structure** - Scaffold SKILL.md and directories
4. **Implement content** - Write SKILL.md, references, scripts
5. **Validate** - Check structure, triggers, content quality
6. **Copy to catalog** - Install in local skills directory
```

## Strategy Selection

The KSTAR loop selects acquisition strategy based on:

```python
def select_acquisition_strategy(
    capability_needed: str,
    K: Knowledge,
    available_sources: List[SkillSource]
) -> AcquisitionStrategy:
    """
    Select best acquisition strategy for needed capability.
    """
    # 1. Check if skill exists in accessible catalogs
    for source in available_sources:
        if skill := source.find_skill(capability_needed):
            return AcquisitionStrategy.COPY, skill, source

    # 2. Check if advanced agent has capability
    for agent in get_available_advanced_agents():
        if agent.has_capability(capability_needed):
            return AcquisitionStrategy.DELEGATE, None, agent

    # 3. Fall back to creation
    return AcquisitionStrategy.CREATE, None, None
```

### Decision Matrix

| Condition | Strategy |
|-----------|----------|
| Skill exists in catalog | COPY |
| Skill exists in another agent | COPY from agent |
| Capability exists in advanced agent | DELEGATE |
| Novel capability needed | CREATE |

## Integration with KSTAR Loop

### During Learning Mode

When KSTAR loop encounters a capability gap:

```python
def handle_capability_gap(K, S, T, gap: str):
    """Handle missing capability during KSTAR execution."""

    # 1. Identify acquisition strategy
    strategy, skill, source = select_acquisition_strategy(
        capability_needed=gap,
        K=K,
        available_sources=get_sources(S)
    )

    # 2. Execute acquisition
    if strategy == AcquisitionStrategy.COPY:
        new_skill = acquire_by_copy(skill.id, source)

    elif strategy == AcquisitionStrategy.DELEGATE:
        # Create subtask for advanced agent
        subtask = Task(goal=T.goal, context=S)
        new_skill = acquire_by_delegation(subtask, source, observe=True)

    elif strategy == AcquisitionStrategy.CREATE:
        # Full skill creation workflow
        new_skill = acquire_by_creation(
            capability_description=gap,
            advanced_agent=get_best_available_agent(),
            skill_creator=get_skill_creator()
        )

    # 3. Update K with new skill
    K["skills"][new_skill.id] = new_skill

    # 4. Record learning episode
    record_acquisition_episode(K, strategy, new_skill)

    return new_skill
```

### K Structure for Skills

```json
{
  "K": {
    "skills": {
      "code-review": {
        "source": "claude-code-agent",
        "acquired_via": "copy",
        "acquired_at": "2024-01-15T10:00:00Z",
        "usage_count": 15,
        "success_rate": 0.93,
        "skill": { "...skill definition..." }
      },
      "security-audit": {
        "source": "created",
        "created_by": "claude-opus",
        "created_via": "skill_creator",
        "created_at": "2024-01-16T14:30:00Z",
        "usage_count": 3,
        "success_rate": 1.0,
        "skill": { "...skill definition..." }
      }
    },
    "acquisition_history": [
      {
        "timestamp": "2024-01-15T10:00:00Z",
        "strategy": "copy",
        "skill_id": "code-review",
        "source": "claude-code-agent",
        "trigger": "capability_gap_in_task"
      }
    ]
  }
}
```

## Skill Catalog Locations

### Local Catalogs

```
~/.claude/skills/                    # User's global skills
  ├── copied/                        # Skills copied from others
  ├── created/                       # Skills created locally
  └── delegated/                     # Skills learned by observation

<project>/.claude/skills/            # Project-specific skills
  └── ...

<project>/user/                      # Alternative project skills
  └── ...
```

### Remote Sources

| Source | Path/URL | Access |
|--------|----------|--------|
| Plugin skills | `~/.claude/plugins/<plugin>/skills/` | Read |
| Team catalog | `https://skills.company.com/` | Read/Write |
| Public registry | `https://github.com/skills-registry/` | Read |
| Agent catalog | Agent's embedded skills | Delegate |

## Copy Skill Agent

A specialized agent for skill copying:

```yaml
name: copy-skill-agent
description: >
  Copies skills from external sources to local catalog.
  Handles compatibility checking, path adaptation, and registration.

capabilities:
  - Locate skills in remote catalogs
  - Validate skill compatibility
  - Adapt paths for local environment
  - Register skills in K

workflow:
  1. Parse skill source reference
  2. Fetch skill definition
  3. Validate structure and dependencies
  4. Adapt paths (replace remote paths with local)
  5. Copy to target catalog
  6. Register in K
  7. Verify skill loads correctly
```

### Copy Agent Usage

```
/copy-skill claude-code:code-review → ~/.claude/skills/
```

## Best Practices

### When to Copy

- Skill is well-established and tested
- No customization needed
- Quick bootstrap of capabilities
- Sharing between team agents

### When to Delegate

- One-time or rare tasks
- Learning new patterns by observation
- Advanced capability not worth full skill creation
- Testing if skill creation is worthwhile

### When to Create

- Recurring need for capability
- Specific customization required
- Building team/project expertise
- No existing skill covers the need

## Skill Versioning

Track skill versions for updates:

```json
{
  "skill_id": "code-review",
  "local_version": "1.2.0",
  "source_version": "1.3.0",
  "update_available": true,
  "update_strategy": "auto" | "manual" | "notify"
}
```

### Update Strategies

- **auto**: Automatically update when source updates
- **manual**: Require explicit update command
- **notify**: Alert user but don't auto-update
