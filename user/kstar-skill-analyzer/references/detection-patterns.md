# Detection Patterns

Heuristics for detecting skill quality characteristics through textual and structural analysis.

## Pattern Detection Heuristics

### Detecting Explicit Patterns

**Positive indicators** (pattern is explicit):

```yaml
textual_indicators:
  - "This is a case of [X]"
  - "This follows the [X] pattern"
  - "The underlying structure is..."
  - "This instantiates..."
  - "The general form is..."
  - "This is an instance of..."

structural_indicators:
  - situation.signature.pattern_type is populated
  - skill references a named pattern
  - skill inherits from a pattern skill
  - explicit pattern_id field
```

**Negative indicators** (pattern is missing):

```yaml
missing_pattern_signals:
  - Only procedural steps, no abstraction
  - No mention of "pattern", "structure", "model", "type"
  - Every step is concrete, nothing parameterized
  - No references to other instances of same pattern
```

**Detection function:**

```python
def has_explicit_pattern(skill) -> bool:
    # Check textual content
    text_corpus = extract_all_text(skill)
    pattern_keywords = [
        "pattern", "structure", "model", "instance", "case of",
        "general form", "abstraction", "underlying"
    ]
    
    keyword_present = any(kw in text_corpus.lower() for kw in pattern_keywords)
    
    # Check structural fields
    has_pattern_field = (
        skill.situation.signature.get("pattern_type") or
        skill.metadata.get("pattern_id") or
        skill.metadata.get("inherits_from")
    )
    
    return keyword_present or has_pattern_field
```

### Detecting Invariants

**Positive indicators**:

```yaml
textual_indicators:
  - "What stays the same is..."
  - "Regardless of [context]..."
  - "This always holds..."
  - "The invariant is..."
  - "Preserved across..."
  - "Independent of..."
  - "applicability_conditions" contains conditions

structural_indicators:
  - applicability_conditions field populated
  - boundary_conditions field exists
  - "when this applies" documentation
```

**Detection function:**

```python
def has_invariants(skill) -> bool:
    # Check for applicability conditions
    if skill.situation.applicability_conditions:
        return True
    
    # Check textual content
    text_corpus = extract_all_text(skill)
    invariant_keywords = [
        "invariant", "always", "regardless", "preserved",
        "stays the same", "independent of", "boundary"
    ]
    
    return any(kw in text_corpus.lower() for kw in invariant_keywords)
```

### Detecting Transfer Guidance

**Positive indicators**:

```yaml
explicit_transfer:
  - "This same pattern applies in..."
  - "You can use this when..."
  - "The analog in [domain] is..."
  - "To adapt this to [context]..."
  - "Similar situations include..."

implicit_transfer:
  - Multiple examples from different domains
  - Abstraction high enough to span contexts
  - Explicit parameters that can vary
```

**Detection function:**

```python
def has_transfer_guidance(skill) -> bool:
    text_corpus = extract_all_text(skill)
    
    transfer_keywords = [
        "also applies", "same pattern", "similar to",
        "analog", "adapt", "transfer", "other contexts",
        "can be used when", "generalizes to"
    ]
    
    return any(kw in text_corpus.lower() for kw in transfer_keywords)
```

### Detecting Reasoning

**Positive indicators**:

```yaml
reasoning_present:
  - "Because..."
  - "The reason is..."
  - "This works because..."
  - "We do this to..."
  - action.reasoning field is substantive
  - scaffolding_hints.pre explains "why"

reasoning_depth:
  shallow: "Do this step"
  medium: "Do this step because [immediate reason]"
  deep: "Do this step because [pattern property] requires [action]"
```

**Detection function:**

```python
def has_reasoning(skill) -> bool:
    # Check reasoning field
    if skill.action.reasoning and len(skill.action.reasoning) > 50:
        return True
    
    # Check for reasoning in scaffolding
    for step in skill.action.plan:
        hints = step.scaffolding_hints
        if hints and hints.pre and "because" in hints.pre.lower():
            return True
    
    return False

def reasoning_depth(skill) -> str:
    reasoning = skill.action.reasoning or ""
    
    if not reasoning:
        return "none"
    
    # Check for pattern references in reasoning
    pattern_refs = ["pattern", "structure", "property", "invariant"]
    has_pattern_ref = any(ref in reasoning.lower() for ref in pattern_refs)
    
    # Check for causal explanation
    causal_words = ["because", "therefore", "since", "thus", "so that"]
    has_causal = any(word in reasoning.lower() for word in causal_words)
    
    if has_pattern_ref and has_causal:
        return "deep"
    elif has_causal:
        return "medium"
    elif len(reasoning) > 20:
        return "shallow"
    else:
        return "none"
```

### Detecting Rigid vs Flexible Steps

**Rigid step indicators**:

```yaml
rigid_signals:
  - "Always do exactly..."
  - "Never deviate..."
  - "Must be precisely..."
  - No conditional branching
  - No parameters or variables
  - Hard-coded values throughout
```

**Flexible step indicators**:

```yaml
flexible_signals:
  - "Depending on [condition]..."
  - "If [X], then [Y]..."
  - "Adjust based on..."
  - "Parameters: [list]"
  - Conditional branches in plan
  - Variables instead of constants
```

**Detection function:**

```python
def step_rigidity_score(step) -> float:
    """Returns 0.0 (flexible) to 1.0 (rigid)"""
    rigid_signals = 0
    flexible_signals = 0
    
    desc = step.description.lower()
    
    # Check for rigid language
    rigid_words = ["always", "exactly", "must", "never", "precisely"]
    rigid_signals += sum(1 for w in rigid_words if w in desc)
    
    # Check for flexible language
    flexible_words = ["if", "depending", "adjust", "vary", "optionally"]
    flexible_signals += sum(1 for w in flexible_words if w in desc)
    
    # Check for parameters
    if step.parameters:
        flexible_signals += len(step.parameters)
    
    # Check for conditionals
    if has_conditional_logic(step):
        flexible_signals += 2
    
    total = rigid_signals + flexible_signals
    if total == 0:
        return 0.5  # Neutral
    
    return rigid_signals / total

def all_steps_are_rigid(skill) -> bool:
    steps = skill.action.plan
    if not steps:
        return True
    
    avg_rigidity = sum(step_rigidity_score(s) for s in steps) / len(steps)
    return avg_rigidity > 0.7
```

### Detecting Feedback Loops

**Feedback present indicators**:

```yaml
feedback_signals:
  - Checkpoints defined (has_checkpoint = True)
  - Expected results specified
  - Validation criteria present
  - Error handling documented
  - Adjustment guidance provided

closed_loop_signals:
  - Result feeds back to adjust action
  - Learning signal extracted
  - Pattern updated based on execution
```

**Detection function:**

```python
def has_feedback_loops(skill) -> bool:
    steps = skill.action.plan
    
    # Check for checkpoints
    has_checkpoints = any(step.has_checkpoint for step in steps)
    
    # Check for expected results
    has_expected = any(step.expected_result for step in steps)
    
    # Check for error handling
    has_error_handling = any(step.common_mistakes for step in steps)
    
    return has_checkpoints or (has_expected and has_error_handling)

def feedback_loop_quality(skill) -> str:
    """Returns: none, basic, adaptive, learning"""
    
    if not has_feedback_loops(skill):
        return "none"
    
    # Check for adjustment based on feedback
    has_adjustment = any(
        "adjust" in str(step).lower() or "if" in step.description.lower()
        for step in skill.action.plan
    )
    
    # Check for learning signal extraction
    has_learning = skill.action.where_students_struggle and len(skill.action.where_students_struggle) > 0
    
    if has_learning:
        return "learning"
    elif has_adjustment:
        return "adaptive"
    else:
        return "basic"
```

### Detecting Adaptation Capability

**Adaptation indicators**:

```yaml
explicit_adaptation:
  - "If [context], adjust [action]"
  - "For [variation], use [alternative]"
  - Conditional steps in plan
  - Multiple paths through execution

implicit_adaptation:
  - High abstraction level (parameterized)
  - Pattern explanation enables inference
  - Invariants clearly distinguish must-have vs can-vary
```

**Detection function:**

```python
def has_adaptation_guidance(skill) -> bool:
    # Check for conditional logic in steps
    for step in skill.action.plan:
        if has_conditional_logic(step):
            return True
        if "adjust" in step.description.lower():
            return True
        if "depending" in step.description.lower():
            return True
    
    # Check for alternatives in action
    if skill.action.alternatives:
        return True
    
    return False
```

### Detecting Pattern Modification Guidance

**Creation-level indicators**:

```yaml
modification_guidance:
  - "You could extend this by..."
  - "To create a variant..."
  - "This pattern can be modified to..."
  - "Combine with [other pattern] when..."
  - Explicit boundary conditions (where pattern breaks)

innovation_scaffolds:
  - Questions that prompt extension
  - Gaps deliberately left for learner
  - "What if..." scenarios
```

**Detection function:**

```python
def has_pattern_modification_guidance(skill) -> bool:
    text_corpus = extract_all_text(skill)
    
    modification_keywords = [
        "extend", "modify", "variant", "combine",
        "create your own", "adapt", "innovate",
        "what if", "could be changed"
    ]
    
    return any(kw in text_corpus.lower() for kw in modification_keywords)
```

### Detecting Teaching Capability

**Meta-creation indicators**:

```yaml
teaching_signals:
  - Scaffolding designed to fade
  - Self-check questions present
  - Explanation of how to teach this
  - Compression into memorable form
  - Transfer methodology provided

meta_signals:
  - Skill about skills
  - Pattern about patterns
  - Learning about learning
```

**Detection function:**

```python
def has_teaching_scaffolds(skill) -> bool:
    # Check for self-check questions
    if skill.assessment.self_check_questions:
        return True
    
    # Check for fading scaffolding
    if scaffolding_fades(skill):
        return True
    
    # Check for teaching language
    text = extract_all_text(skill)
    teaching_words = ["teach", "explain to others", "help others learn"]
    
    return any(w in text.lower() for w in teaching_words)

def has_compression_guidance(skill) -> bool:
    """Check if skill teaches how to compress/summarize the pattern"""
    text = extract_all_text(skill)
    
    compression_words = [
        "summarize", "key insight", "essential", "core principle",
        "remember as", "mnemonic", "in short"
    ]
    
    return any(w in text.lower() for w in compression_words)
```

## Composite Detectors

### Is Rote Memorization

```python
def is_rote(skill) -> bool:
    """Determine if skill is pure rote memorization"""
    checks = [
        not has_explicit_pattern(skill),
        not has_invariants(skill),
        not has_transfer_guidance(skill),
        all_steps_are_rigid(skill),
        reasoning_depth(skill) in ["none", "shallow"]
    ]
    
    # Rote if 3+ indicators present
    return sum(checks) >= 3
```

### Understanding Depth

```python
def understanding_depth(skill) -> str:
    """Classify depth: rote, procedural, structural, deep"""
    
    if is_rote(skill):
        return "rote"
    
    has_pattern = has_explicit_pattern(skill)
    has_invariant = has_invariants(skill)
    has_transfer = has_transfer_guidance(skill)
    reasoning = reasoning_depth(skill)
    
    if has_pattern and has_invariant and has_transfer and reasoning == "deep":
        return "deep"
    elif has_pattern and (has_invariant or reasoning in ["medium", "deep"]):
        return "structural"
    else:
        return "procedural"
```

### Transfer Readiness

```python
def transfer_readiness(skill) -> str:
    """Classify: none, narrow, broad, universal"""
    
    if not has_explicit_pattern(skill):
        return "none"
    
    has_transfer = has_transfer_guidance(skill)
    has_invariant = has_invariants(skill)
    has_modification = has_pattern_modification_guidance(skill)
    
    if has_modification and has_transfer and has_invariant:
        return "universal"
    elif has_transfer and has_invariant:
        return "broad"
    elif has_transfer or has_invariant:
        return "narrow"
    else:
        return "none"
```
