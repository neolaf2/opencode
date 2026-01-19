# Dependency Detection Patterns

This reference documents the patterns used to detect skill dependencies.

## Pattern Categories

### 1. Explicit Reference Patterns

Direct mentions of skill names in natural language:

```
uses uair-control
invokes kstar-transformation
calls kstar-loop
coordinates with uair-control
integrates with kstar-xapi
```

Regex:
```python
r'(?:uses?|invokes?|calls?|coordinates?\s+with|integrates?\s+with)\s+[`"]?(\w+(?:-\w+)*)[`"]?'
```

### 2. Import Patterns

Python import statements:

```python
from kstar_loop import KSTARLoop
from uair_controller import uair_control
import kstar_transformation
```

Regex:
```python
r'from\s+(\w+(?:_\w+)*)\s+import'
```

Note: Underscores are converted to hyphens for skill name matching.

### 3. Section Header Patterns

Integration sections in SKILL.md:

```markdown
### With uair-control
### With kstar-transformation
## Integration with kstar-xapi
```

Regex:
```python
r'###?\s+With\s+(\w+(?:-\w+)*)'
```

### 4. JSON Configuration Patterns

Skill references in JSON configuration:

```json
{
  "available_subskills": ["interview.step", "quiz.step"],
  "integrations": ["uair-control", "kstar-transformation"]
}
```

Regex:
```python
r'"available_subskills":\s*\[([^\]]+)\]'
```

### 5. Variable Assignment Patterns

Skill names in code variables:

```python
skill_name = "uair-control"
target_skill: str = "kstar-loop"
```

Regex:
```python
r'skill(?:_name)?\s*[=:]\s*["\'](\w+(?:-\w+)*)["\']'
```

## Validation Rules

### Valid Skill Names

Pattern: `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`

Valid:
- `kstar-loop`
- `uair-control`
- `skill-dependency-analyzer`

Invalid:
- `KSTAR-Loop` (uppercase)
- `skill_name` (underscore - converted automatically)
- `123-skill` (starts with number)

### False Positive Filtering

The analyzer filters out common false positives:

1. **Common words**: "the", "a", "an", "with", "for"
2. **Reserved terms**: "python", "json", "yaml", "markdown"
3. **Self-references**: A skill referencing itself

## Category Classification

Skills are categorized based on name and description keywords:

| Category | Keywords |
|----------|----------|
| `core` | kstar, uair, loop, control, transform |
| `document` | docx, pdf, latex, pptx, xlsx, html, markdown |
| `domain` | neolaf, wechat, business |
| `workflow` | consolidat, review, format |
| `integration` | xapi, api, sdk |
| `meta` | skill, dependency, analyz |
| `other` | (default) |

## Confidence Levels

Dependency detection confidence:

| Pattern | Confidence | Reason |
|---------|------------|--------|
| Import statement | High | Explicit code dependency |
| Integration section | High | Documented relationship |
| available_subskills | High | Runtime dependency |
| Text mention | Medium | May be documentation only |
| Variable assignment | Medium | May be dynamic/conditional |

## Edge Types

| Type | Meaning | Example |
|------|---------|---------|
| `uses` | A invokes/depends on B | kstar-loop → uair-control |
| `extends` | A extends B's functionality | (future) |
| `optional` | A may use B if available | (future) |
