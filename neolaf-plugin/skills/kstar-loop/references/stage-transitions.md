# Stage Transitions

The KSTAR loop progresses through stages based on conditions and outcomes.

## Stage Progression

```
understand → plan → execute → validate → reflect → complete
     ↑         ↑        ↑         ↑
     └─────────┴────────┴─────────┘  (retry loops)
```

## Transition Rules

### understand → plan

**Conditions to advance:**
- Goal parsed into structured form
- Ambiguities resolved (or explicitly deferred)
- Constraints identified
- Success criteria defined

**Triggers to retry:**
- Goal still ambiguous after clarification
- Missing critical context

```python
def can_advance_from_understand(T, R):
    return (
        T.goal_structured and
        len(T.success_criteria) > 0 and
        R.ambiguities_resolved
    )
```

### plan → execute

**Conditions to advance:**
- Action sequence generated
- Resources allocated/verified
- Forecast R̂ generated
- No blocking constraints

**Triggers to retry:**
- Plan infeasible
- Resources unavailable
- Forecast indicates high failure probability

```python
def can_advance_from_plan(T, A_hat, R_hat):
    return (
        A_hat.is_feasible and
        A_hat.resources_available and
        R_hat.success_probability > 0.5
    )
```

### execute → validate

**Conditions to advance:**
- All planned actions completed
- Outputs generated
- No critical errors

**Triggers to retry:**
- Action failed, recoverable
- Partial completion, can continue

**Triggers to regress (→ plan):**
- Action failed, unrecoverable with current plan
- New information invalidates plan

```python
def transition_from_execute(T, R, A_hat):
    if R.all_actions_complete:
        return "validate"
    elif R.recoverable_failure:
        return "execute"  # retry
    else:
        return "plan"  # replan
```

### validate → reflect

**Conditions to advance:**
- Success criteria checked
- All criteria met OR
- Explicit decision to proceed despite gaps

**Triggers to retry:**
- Validation incomplete

**Triggers to regress:**
- Criteria not met → "execute" (fix) or "plan" (redesign)

```python
def transition_from_validate(T, R, validation_result):
    if validation_result.all_criteria_met:
        return "reflect"
    elif validation_result.fixable:
        return "execute"
    elif validation_result.needs_replan:
        return "plan"
    else:
        return "reflect"  # proceed with documented gaps
```

### reflect → complete

**Conditions to advance:**
- AAR generated
- Learning deltas extracted
- Knowledge updated

**Triggers to retry:**
- Reflection incomplete

```python
def transition_from_reflect(T, aar):
    if aar.complete and aar.knowledge_integrated:
        return "complete"
    else:
        return "reflect"  # continue reflection
```

## Stage State Machine

```json
{
  "states": ["understand", "plan", "execute", "validate", "reflect", "complete"],
  "transitions": [
    {"from": "understand", "to": "plan", "condition": "goal_structured"},
    {"from": "understand", "to": "understand", "condition": "retry_clarification"},
    
    {"from": "plan", "to": "execute", "condition": "plan_feasible"},
    {"from": "plan", "to": "plan", "condition": "retry_planning"},
    {"from": "plan", "to": "understand", "condition": "goal_unclear"},
    
    {"from": "execute", "to": "validate", "condition": "execution_complete"},
    {"from": "execute", "to": "execute", "condition": "retry_action"},
    {"from": "execute", "to": "plan", "condition": "replan_needed"},
    
    {"from": "validate", "to": "reflect", "condition": "validation_passed"},
    {"from": "validate", "to": "execute", "condition": "fix_needed"},
    {"from": "validate", "to": "plan", "condition": "redesign_needed"},
    
    {"from": "reflect", "to": "complete", "condition": "aar_complete"},
    {"from": "reflect", "to": "reflect", "condition": "continue_reflection"}
  ]
}
```

## Stage-Specific Actions

### understand

Primary actions:
- Parse goal into structured representation
- Identify implicit constraints
- Generate clarifying questions
- Build initial task decomposition

Output artifact:
```json
{
  "task": {
    "goal": "structured goal",
    "success_criteria": [...],
    "constraints": {...},
    "decomposition": [...]
  }
}
```

### plan

Primary actions:
- Generate action sequence
- Allocate resources
- Identify dependencies
- Generate forecast R̂

Output artifact:
```json
{
  "plan": {
    "actions": [...],
    "resource_allocation": {...},
    "dependencies": [...],
    "forecast": {
      "expected_outcome": "...",
      "success_probability": 0.8,
      "risks": [...]
    }
  }
}
```

### execute

Primary actions:
- Execute planned actions
- Invoke tools
- Monitor progress
- Capture outputs

Output artifact:
```json
{
  "execution_log": {
    "actions_completed": [...],
    "outputs": {...},
    "errors": [...],
    "observations": [...]
  }
}
```

### validate

Primary actions:
- Check outputs against success criteria
- Compute prediction error (R vs R̂)
- Identify gaps
- Generate validation report

Output artifact:
```json
{
  "validation": {
    "criteria_results": {...},
    "prediction_error": {...},
    "gaps": [...],
    "overall_status": "pass|partial|fail"
  }
}
```

### reflect

Primary actions:
- Generate After-Action Review (AAR)
- Extract learning deltas
- Update knowledge base
- Archive episode

Output artifact:
```json
{
  "aar": {
    "what_happened": "...",
    "what_worked": [...],
    "what_didnt_work": [...],
    "lessons_learned": [...],
    "knowledge_deltas": [...],
    "recommendations": [...]
  }
}
```

## Transition Decision Function

```python
def next_stage(T, R, delta):
    """
    Determine next stage based on current stage, result, and prediction error.
    """
    current = T.stage
    
    if current == "understand":
        if goal_is_structured(T) and criteria_defined(T):
            return Stage.PLAN
        return Stage.UNDERSTAND
    
    elif current == "plan":
        if plan_is_feasible(T.plan) and forecast_acceptable(T.forecast):
            return Stage.EXECUTE
        if needs_goal_revision(delta):
            return Stage.UNDERSTAND
        return Stage.PLAN
    
    elif current == "execute":
        if execution_complete(R):
            return Stage.VALIDATE
        if can_retry(R, T.plan):
            return Stage.EXECUTE
        return Stage.PLAN
    
    elif current == "validate":
        if all_criteria_met(R, T.success_criteria):
            return Stage.REFLECT
        if can_fix_in_execution(R):
            return Stage.EXECUTE
        if needs_replan(R):
            return Stage.PLAN
        return Stage.REFLECT  # proceed with gaps documented
    
    elif current == "reflect":
        if aar_complete(R):
            return Stage.COMPLETE
        return Stage.REFLECT
    
    return Stage.COMPLETE
```

## Retry Limits

To prevent infinite loops:

```python
RETRY_LIMITS = {
    "understand": 3,
    "plan": 3,
    "execute": 5,
    "validate": 2,
    "reflect": 2
}

def check_retry_limit(T, stage):
    count = sum(1 for s in T.stage_history if s.stage == stage)
    if count >= RETRY_LIMITS[stage]:
        raise RetryLimitExceeded(stage, count)
```
