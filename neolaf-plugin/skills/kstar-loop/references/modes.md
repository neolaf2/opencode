# Operating Modes

The KSTAR loop supports two operating modes that fundamentally alter cognitive cycle behavior.

## Mode Comparison

| Aspect | Learning Mode 📚 | Performance Mode ⚡ |
|--------|------------------|---------------------|
| **Primary Goal** | Maximize knowledge acquisition | Maximize execution efficiency |
| **Exploration** | High (0.8) - try alternatives | Low (0.2) - use proven patterns |
| **Reflection** | Deep - full AAR every stage | Minimal - only on errors |
| **UAIR Bias** | ASK - prefer clarification | RETRIEVE - use existing K |
| **K Updates** | Frequent - record all episodes | Sparse - only significant events |
| **Forecasting** | Required - always generate R̂ | Optional - skip if confident |
| **Narration** | Verbose - explain actions | Minimal - direct execution |

## Learning Mode 📚

### Philosophy

Learning mode treats every interaction as an opportunity for knowledge acquisition. The agent prioritizes understanding over speed, explores alternatives even when a working solution exists, and maintains detailed records for future reference.

### Behavioral Characteristics

**Situation Completion (UAIR)**
- Bias toward ASK: When information is missing, prefer asking clarifying questions
- Complete all S components (S_A, S_D, S_P, S_N) before proceeding
- Explore actor preferences and constraints thoroughly
- Document domain context even if not strictly required

```python
uair_behavior = {
    "bias": "ASK",
    "required_fields": ["S_A", "S_D", "S_P", "S_N"],
    "clarification_threshold": 0.7,  # Ask if confidence < 70%
    "assumption_logging": True       # Record all assumptions made
}
```

**Planning Phase**
- Generate multiple alternative plans (2-3 minimum)
- Explain trade-offs between alternatives
- Include educational annotations in plan
- Lower threshold for plan acceptance (explore suboptimal paths)

```python
plan_behavior = {
    "alternatives_required": 2,
    "explain_tradeoffs": True,
    "acceptance_threshold": 0.3,  # Accept riskier plans to learn
    "annotate_decisions": True
}
```

**Execution Phase**
- Narrate each action before execution
- Explain reasoning behind tool selection
- Pause at decision points for reflection
- Record intermediate states

```python
execute_behavior = {
    "narrate_actions": True,
    "explain_reasoning": True,
    "checkpoint_frequency": "high",
    "record_intermediate": True
}
```

**Validation Phase**
- Detailed comparison of R vs R̂
- Analyze prediction errors thoroughly
- Document what was learned from discrepancies
- Expand success criteria if new insights emerge

```python
validate_behavior = {
    "comparison_depth": "detailed",
    "error_analysis": True,
    "expand_criteria": True,
    "prediction_error_threshold": 0.0  # Any error triggers learning
}
```

**Reflection Phase**
- Full After-Action Review (AAR)
- Extract multiple lessons learned
- Generate recommendations for future
- Update K with detailed episode records
- Inter-stage mini-AARs between each stage

```python
reflect_behavior = {
    "aar_depth": "full",
    "lessons_minimum": 3,
    "inter_stage_reflection": True,
    "knowledge_update_threshold": 0.0  # Always update K
}
```

### When to Use Learning Mode

1. **New Domains**: First encounter with a problem type
2. **Training Scenarios**: User explicitly wants to learn
3. **Debugging**: Understanding why something failed
4. **Knowledge Building**: Building K for future performance
5. **Uncertain Context**: Low confidence in existing knowledge
6. **Tutorial Mode**: User requests explanation and guidance

### Mode Selection Triggers

```python
def should_use_learning_mode(S, K, T):
    # Explicit request
    if "learning" in T.goal.lower() or "learn" in T.goal.lower():
        return True

    # Tutorial interaction pattern
    if S.protocol_state.interaction_pattern == "tutorial":
        return True

    # Low K confidence for this domain
    domain_confidence = K.get("confidence", {}).get(S.domain_state.domain_type, 0)
    if domain_confidence < 0.5:
        return True

    # Few prior episodes in this domain
    prior_episodes = len(K.get("episodes", {}).get(S.domain_state.domain_type, []))
    if prior_episodes < 5:
        return True

    return False
```

## Performance Mode ⚡

### Philosophy

Performance mode optimizes for execution efficiency. The agent leverages existing knowledge, minimizes overhead, and produces results with minimal ceremony. Reflection occurs only when significant errors indicate knowledge gaps.

### Behavioral Characteristics

**Situation Completion (UAIR)**
- Bias toward RETRIEVE: Use existing K to fill gaps
- Only S_D (domain state) strictly required
- Make reasonable assumptions rather than asking
- Skip optional context gathering

```python
uair_behavior = {
    "bias": "RETRIEVE",
    "required_fields": ["S_D"],
    "clarification_threshold": 0.3,  # Only ask if confidence < 30%
    "assumption_logging": False
}
```

**Planning Phase**
- Select best known approach immediately
- Skip alternative generation unless blocked
- No educational annotations
- Higher threshold for plan acceptance (use proven patterns)

```python
plan_behavior = {
    "alternatives_required": 0,
    "explain_tradeoffs": False,
    "acceptance_threshold": 0.7,  # Require higher confidence
    "annotate_decisions": False
}
```

**Execution Phase**
- Direct action without narration
- Skip reasoning explanations
- Minimal checkpointing
- Record only final outputs

```python
execute_behavior = {
    "narrate_actions": False,
    "explain_reasoning": False,
    "checkpoint_frequency": "low",
    "record_intermediate": False
}
```

**Validation Phase**
- Binary pass/fail check
- Skip detailed error analysis if passing
- Use existing criteria without expansion
- Only significant prediction errors trigger analysis

```python
validate_behavior = {
    "comparison_depth": "binary",
    "error_analysis": False,  # Unless failure
    "expand_criteria": False,
    "prediction_error_threshold": 0.3  # Only large errors matter
}
```

**Reflection Phase**
- Skip AAR if all criteria met
- Summary-level reflection only
- K updates only for significant outcomes
- No inter-stage reflection

```python
reflect_behavior = {
    "aar_depth": "summary",
    "lessons_minimum": 0,
    "inter_stage_reflection": False,
    "knowledge_update_threshold": 0.3  # Only significant events
}
```

### When to Use Performance Mode

1. **Familiar Tasks**: High K confidence for domain
2. **Time-Sensitive**: User needs quick results
3. **Production Context**: Operational, not training
4. **Routine Workflows**: Repeated, well-understood tasks
5. **Results-Focused**: User wants output, not explanation

### Mode Selection Triggers

```python
def should_use_performance_mode(S, K, T):
    # Explicit request
    if "quick" in T.goal.lower() or "fast" in T.goal.lower():
        return True

    # Production interaction pattern
    if S.protocol_state.interaction_pattern == "production":
        return True

    # High K confidence for this domain
    domain_confidence = K.get("confidence", {}).get(S.domain_state.domain_type, 0)
    if domain_confidence > 0.8:
        return True

    # Many prior successful episodes
    prior_episodes = K.get("episodes", {}).get(S.domain_state.domain_type, [])
    successful = [e for e in prior_episodes if e.get("R", {}).get("success")]
    if len(successful) > 10:
        return True

    return False
```

## Mode Configuration

### Full Configuration Schema

```python
@dataclass
class ModeConfig:
    """Complete mode configuration."""

    # Identity
    name: str                          # "LEARNING" or "PERFORMANCE"

    # Exploration
    exploration: float                 # 0.0-1.0, tendency to try alternatives

    # UAIR behavior
    uair_bias: str                     # "ASK" or "RETRIEVE"
    required_fields: List[str]         # S components required
    clarification_threshold: float     # Confidence threshold to ask

    # Planning
    alternatives_required: int         # Minimum alternative plans
    plan_acceptance_threshold: float   # Confidence to accept plan
    annotate_decisions: bool           # Include educational notes

    # Forecasting
    forecast_required: bool            # Always generate R̂?
    confidence_threshold: float        # Skip forecast if above

    # Execution
    narrate_actions: bool              # Explain actions
    checkpoint_frequency: str          # "high", "medium", "low"
    record_intermediate: bool          # Save intermediate states

    # Validation
    comparison_depth: str              # "detailed" or "binary"
    prediction_error_threshold: float  # Threshold for triggering analysis

    # Reflection
    aar_depth: str                     # "full" or "summary"
    inter_stage_reflection: bool       # Mini-AARs between stages
    record_all_episodes: bool          # Always record to K
    knowledge_update_threshold: float  # Delta threshold for K update


# Standard configurations
LEARNING_MODE = ModeConfig(
    name="LEARNING",
    exploration=0.8,
    uair_bias="ASK",
    required_fields=["S_A", "S_D", "S_P", "S_N"],
    clarification_threshold=0.7,
    alternatives_required=2,
    plan_acceptance_threshold=0.3,
    annotate_decisions=True,
    forecast_required=True,
    confidence_threshold=0.95,
    narrate_actions=True,
    checkpoint_frequency="high",
    record_intermediate=True,
    comparison_depth="detailed",
    prediction_error_threshold=0.0,
    aar_depth="full",
    inter_stage_reflection=True,
    record_all_episodes=True,
    knowledge_update_threshold=0.0
)

PERFORMANCE_MODE = ModeConfig(
    name="PERFORMANCE",
    exploration=0.2,
    uair_bias="RETRIEVE",
    required_fields=["S_D"],
    clarification_threshold=0.3,
    alternatives_required=0,
    plan_acceptance_threshold=0.7,
    annotate_decisions=False,
    forecast_required=False,
    confidence_threshold=0.7,
    narrate_actions=False,
    checkpoint_frequency="low",
    record_intermediate=False,
    comparison_depth="binary",
    prediction_error_threshold=0.3,
    aar_depth="summary",
    inter_stage_reflection=False,
    record_all_episodes=False,
    knowledge_update_threshold=0.3
)
```

## Mode Transitions

Modes can transition during execution based on conditions:

### Learning → Performance

Transition when:
- Accumulated sufficient successful episodes (>10)
- Domain confidence exceeds threshold (>0.8)
- User explicitly requests faster execution

```python
def should_transition_to_performance(K, episodes, S):
    # Sufficient learning completed
    success_count = sum(1 for e in episodes if e.result.get("success"))
    if success_count > 10:
        return True

    # High confidence achieved
    if K.get("confidence", {}).get(S.domain_state.domain_type, 0) > 0.8:
        return True

    return False
```

### Performance → Learning

Transition when:
- Prediction error exceeds threshold (>0.5)
- Execution failures indicate knowledge gap
- New domain/task type encountered
- User requests explanation

```python
def should_transition_to_learning(delta, R, S, T):
    # Significant prediction error
    if abs(delta) > 0.5:
        return True

    # Repeated failures
    if not R.success and S.protocol_state.stage_history.count("execute") > 2:
        return True

    # Novel situation
    if is_novel_situation(S, T):
        return True

    return False
```

## Integration with UAIR

Mode affects UAIR decision-making:

```python
def uair_decide(S, T, K, mode):
    """UAIR decision influenced by mode."""
    missing = get_missing_fields(S, mode.required_fields)

    for field in missing:
        confidence = estimate_confidence(K, field)

        if mode.uair_bias == "ASK":
            if confidence < mode.clarification_threshold:
                yield UAIRAction.ASK, field
            else:
                yield UAIRAction.INFER, field

        elif mode.uair_bias == "RETRIEVE":
            if confidence < mode.clarification_threshold:
                # Try harder to retrieve before asking
                retrieved = deep_retrieve(K, field)
                if retrieved:
                    yield UAIRAction.INFER, field
                else:
                    yield UAIRAction.ASK, field
            else:
                yield UAIRAction.INFER, field
```

## Stage-Specific Mode Effects

### understand Stage

| Aspect | Learning | Performance |
|--------|----------|-------------|
| Clarification | Ask even if can proceed | Only if truly blocked |
| Goal parsing | Detailed decomposition | Quick extraction |
| Criteria generation | Comprehensive | Minimal viable |

### plan Stage

| Aspect | Learning | Performance |
|--------|----------|-------------|
| Alternatives | Generate 2-3 | Best known only |
| Trade-off analysis | Detailed | Skip |
| Annotations | Educational notes | None |
| Risk tolerance | Higher (explore) | Lower (proven paths) |

### execute Stage

| Aspect | Learning | Performance |
|--------|----------|-------------|
| Narration | Full explanation | Silent |
| Checkpointing | Every action | Final only |
| Tool selection | Explain why | Direct use |
| Error detail | Verbose | Minimal |

### validate Stage

| Aspect | Learning | Performance |
|--------|----------|-------------|
| R vs R̂ comparison | Detailed analysis | Pass/fail check |
| Error investigation | Deep dive | Only if failing |
| Criteria expansion | Add insights | Fixed criteria |

### reflect Stage

| Aspect | Learning | Performance |
|--------|----------|-------------|
| AAR generation | Full 6-section | Summary only |
| Lessons extraction | Multiple insights | Only if errors |
| K updates | Every episode | Significant only |
| Inter-stage reflection | Yes | No |

## Default Mode Selection

When no explicit mode is specified:

```python
def select_default_mode(S, K, T):
    """Select mode based on context."""

    # 1. Check explicit request in goal
    goal_lower = T.goal.lower()
    if any(w in goal_lower for w in ["learn", "teach", "explain", "tutorial"]):
        return "LEARNING"
    if any(w in goal_lower for w in ["quick", "fast", "just do", "execute"]):
        return "PERFORMANCE"

    # 2. Check interaction pattern
    if S.protocol_state.interaction_pattern == "tutorial":
        return "LEARNING"
    if S.protocol_state.interaction_pattern == "production":
        return "PERFORMANCE"

    # 3. Check K confidence
    domain = S.domain_state.domain_type
    confidence = K.get("confidence", {}).get(domain, 0)
    if confidence < 0.5:
        return "LEARNING"
    if confidence > 0.8:
        return "PERFORMANCE"

    # 4. Default to LEARNING (prefer knowledge acquisition)
    return "LEARNING"
```
