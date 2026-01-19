# K-STAR to Claude Skill Field Mapping

Complete specification for mapping K-STAR memory entry fields to Claude Skill sections.

## K-STAR Input Requirements

### Required Fields

Every K-STAR entry used for skill construction MUST contain:

| Field | Type | Description |
|-------|------|-------------|
| S (Situation) | object | Trigger conditions, context, constraints |
| T (Task) | object | Goal, intent, scope |
| Â (Action Plan) | markdown | Executable procedure |
| A (Observed Action) | markdown | What actually happened |
| R (Result) | object | Success/failure with evidence |
| verification_evidence | object | How success was confirmed |
| context_snapshot | object | State at execution time |
| environment_signature | object | Tools, platform, constraints |
| timestamp | ISO8601 | When episode occurred |
| agent_identity | string | Teacher/executor identity |

### Optional but Recommended

| Field | Type | Description |
|-------|------|-------------|
| E_hat (Expected Feeling) | object | Confidence/uncertainty forecast |
| failure_diagnostics | object | Root cause analysis |
| oracle_source | enum | teacher / human / web / agent |
| tool_call_logs | array | Detailed invocation records |

## Section-by-Section Mapping

### 1. Skill Identity

**Target**: YAML frontmatter `name`, `lifecycle.version`

**Mapping Rules**:
```python
skill_id = stable_hash(
    canonical(S.trigger) + 
    canonical(T.goal) + 
    source_agent_id
)
version = semantic_version(rewrite_cycle_count)
```

**Requirements**:
- `skill_id` MUST be stable across versions
- Version increments on logic changes only
- Minor bumps for parameter changes
- Major bumps for structural changes

### 2. Description (Understanding Layer)

**Target**: `## Description` section

**Mapping Rules**:
1. Extract generalized pattern from multiple (S,T) pairs
2. Abstract away instance-specific details
3. Identify the **problem class** being solved

**Template**:
```markdown
## Description

This skill handles [problem class] by [approach].

**Structural pattern**: [what this skill recognizes]
**Problem class**: [category of problems solved]
**Why it works**: [causal explanation]
```

**Requirements**:
- Must be understandable without reading steps
- Must explain structural pattern, not instance
- Must include causal reasoning (why, not just how)

### 3. Applicability Conditions

**Target**: `## When to Use This Skill` section

**Mapping Rules**:

```python
def extract_applicability(episodes):
    successes = [e for e in episodes if e.R.success]
    failures = [e for e in episodes if not e.R.success]
    
    hard_guards = intersection([e.S for e in successes])
    soft_guards = common_features(successes) - hard_guards
    exclusions = generalize([e.S for e in failures])
    
    return {
        "hard": hard_guards,      # Must be true
        "soft": soft_guards,      # Preferred
        "exclude": exclusions     # Do not apply when
    }
```

**Template**:
```markdown
## When to Use This Skill

**Required conditions (hard guards)**:
- [condition derived from all successful episodes]

**Preferred conditions (soft guards)**:
- [condition present in most successful episodes]

**Do NOT apply when**:
- [condition present in failed episodes]
- [environment signature incompatible]
```

### 4. Inputs / Parameters

**Target**: `## Inputs` section

**Mapping Rules**:

```python
def extract_parameters(episodes):
    """Constants that vary across episodes become parameters."""
    parameters = {}
    
    for field in union_fields(episodes):
        values = [e.get(field) for e in episodes]
        if len(set(values)) > 1:  # Varies
            parameters[field] = {
                "type": infer_type(values),
                "required": all(v is not None for v in values),
                "default": mode(values) if safe_default(values) else None,
                "description": infer_description(field, values)
            }
    
    return parameters
```

**Type Inference**:
| Observed Values | Inferred Type |
|-----------------|---------------|
| Strings | `string` |
| Integers | `number` |
| True/False | `boolean` |
| Limited set | `enum: [values]` |
| File paths | `file` |

**Template**:
```markdown
## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| [name] | [type] | [yes/no] | [value/-] | [from usage] |
```

**Requirements**:
- Every parameter MUST have description
- Required parameters MUST be marked
- Safe defaults MUST be provided when possible

### 5. Procedure (Steps)

**Target**: `## Steps` section

**Mapping Rules**:

```python
def generalize_procedure(episodes):
    """Generalize action plans, replace literals with placeholders."""
    
    # Align action plans by structural similarity
    aligned = structural_align([e.A_hat for e in episodes])
    
    # Find common skeleton
    skeleton = extract_skeleton(aligned)
    
    # Replace literals with parameter references
    for literal, param in parameter_mapping.items():
        skeleton = skeleton.replace(literal, f"{{{{param}}}}")
    
    return skeleton
```

**Template**:
```markdown
## Steps

1. [Action with {{parameter}} placeholders]
2. [Action referencing tools from K]
   ```python
   # Specific tool invocation
   result = tool.execute({{param1}}, {{param2}})
   ```
3. [Verification step]
```

**Requirements**:
- Steps MUST be ordered
- Include tool invocation intent
- No hidden assumptions
- Replace all literals with parameters
- Must be "compilable" (executable by agent)

### 6. Verification

**Target**: `## Verification` section

**Mapping Rules**:

```python
def extract_verification(episodes):
    """Aggregate verification patterns from successful episodes."""
    
    checks = []
    for episode in episodes:
        if episode.R.success:
            checks.extend(episode.verification_evidence.checks)
    
    return {
        "success_indicators": generalize(checks),
        "artifacts": [e.R.artifact for e in episodes if e.R.artifact],
        "state_changes": [e.R.state_delta for e in episodes]
    }
```

**Template**:
```markdown
## Verification

**Success confirmed when**:
- [Observable condition]
- [Artifact exists: path/pattern]

**Verification method**:
```bash
# Executable verification command
verify_command --check {{expected_output}}
```
```

**Requirements**:
- A skill without verification is INVALID
- Verification MUST be executable or observable
- Include both positive and negative indicators

### 7. Failure Handling

**Target**: `## If Something Goes Wrong` section

**Mapping Rules**:

```python
def extract_failure_handling(episodes, oracle_corrections):
    """Derive handling from failures and corrections."""
    
    failures = [e for e in episodes if not e.R.success]
    
    return {
        "known_errors": categorize([f.failure_diagnostics for f in failures]),
        "retry_conditions": extract_retry_patterns(failures),
        "fallbacks": extract_fallback_strategies(oracle_corrections),
        "escalation": determine_escalation_threshold(failures)
    }
```

**Template**:
```markdown
## If Something Goes Wrong

**Common issues**:
| Error | Cause | Resolution |
|-------|-------|------------|
| [error] | [from diagnostics] | [from corrections] |

**Retry logic**:
- Retry when: [transient conditions]
- Max retries: [N]

**Fallback strategy**:
- If [condition], then [alternative approach]

**Escalation**:
- Escalate to [human/teacher agent] when: [threshold]
```

**Requirements**:
- MUST include retry logic
- MUST include fallback strategy
- MUST include escalation rule

### 8. Teaching Notes

**Target**: `## Teaching Notes` section

**Mapping Rules**:

```python
def extract_teaching_notes(episodes, teacher_reasoning):
    """Extract pedagogical insights."""
    
    struggles = identify_common_struggles(episodes)
    misconceptions = extract_misconceptions(failed_attempts)
    rationale = teacher_reasoning.explanations
    
    return {
        "step_rationale": {step: why for step, why in rationale},
        "common_struggles": struggles,
        "misconceptions": misconceptions
    }
```

**Template**:
```markdown
## Teaching Notes

**Why each step matters**:
1. Step 1: [rationale from teacher]
2. Step 2: [rationale]

**Common struggles**:
- [Where learners typically fail]
- [Why they fail]

**Misconceptions to address**:
- [Incorrect belief] → [Correction]
```

## Lifecycle Metadata Schema

```yaml
lifecycle:
  state: candidate | validated | operational | refined | quarantined
  source_agent: string  # Teacher/compiler agent ID
  derived_from:         # Provenance
    - kstar_episode_id_1
    - kstar_episode_id_2
  confidence: float     # [0.0, 1.0]
  last_updated: ISO8601
  version: semver       # major.minor.patch
  validation_history:
    - timestamp: ISO8601
      outcome: pass | fail
      notes: string
  refinement_lineage:   # Track evolution
    - version: string
      date: ISO8601
      changes: string
```

## Validation Checklist

Before accepting a compiled skill:

- [ ] All required sections present
- [ ] skill_id stable and unique
- [ ] Description explains problem class (not instance)
- [ ] Applicability includes hard guards, soft guards, exclusions
- [ ] All parameters have type, description, required flag
- [ ] Steps use parameter placeholders (no literals)
- [ ] Verification is executable or observable
- [ ] Failure handling includes retry, fallback, escalation
- [ ] Teaching notes present (if student-facing)
- [ ] Lifecycle metadata complete
- [ ] Derived from ≥3 episodes
