# Scoring Rubrics

Complete rubrics for evaluating KSTAR skills across the 2-D world model, abstraction depth, ability level, and structural plasticity.

## 1. Structure Dimension (0-100)

Evaluates the **Pattern** axis of the 2-D world model.

### Pattern Explicitness (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | No pattern; pure step sequence |
| 6-10 | Implicit pattern; could be inferred |
| 11-15 | Pattern mentioned but not characterized |
| 16-20 | Pattern explicitly stated with properties |
| 21-25 | Pattern formally defined with invariants |

**Detection questions:**
- Does the skill say "This is an instance of [X]"?
- Is a pattern name explicitly given?
- Are pattern properties listed?

### Invariant Identification (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | No invariants; everything context-specific |
| 6-10 | One or two invariants implied |
| 11-15 | Invariants listed but not explained |
| 16-20 | Invariants explained with justification |
| 21-25 | Complete invariant specification with boundaries |

**Key question:** What stays the same when context changes?

### Abstraction Level (0-25)

Based on the 4-level hierarchy:

| Score | Level | Criteria |
|-------|-------|----------|
| 0-5 | L0 | No abstraction |
| 6-10 | L1 | Instance only (2+2=4) |
| 11-15 | L2 | Pattern (n+n=2n) |
| 16-20 | L3 | Operation (+has properties) |
| 21-25 | L4 | Structure (group theory level) |

### Transfer Potential (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | Context-locked; no transfer possible |
| 6-10 | Hints at transfer |
| 11-15 | Transfer to similar contexts explained |
| 16-20 | Transfer to different domains demonstrated |
| 21-25 | Transfer methodology provided |

**Key indicator:** "This same pattern appears in..."

---

## 2. Causality Dimension (0-100)

Evaluates the **Process** axis of the 2-D world model.

### Action Completeness (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | Missing critical steps |
| 6-10 | Steps present but incomplete |
| 11-15 | Complete steps, no preconditions |
| 16-20 | Complete steps with preconditions |
| 21-25 | Steps, preconditions, and expected results |

### Feedback Integration (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | No feedback; blind execution |
| 6-10 | Checkpoints exist, no response to failure |
| 11-15 | Basic failure handling |
| 16-20 | Feedback loops that adjust execution |
| 21-25 | Comprehensive feedback with learning signals |

### Error Handling (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | No error handling |
| 6-10 | Error states identified, not addressed |
| 11-15 | Basic recovery for common cases |
| 16-20 | Comprehensive with diagnosis |
| 21-25 | Pattern-based recovery |

### Adaptation Guidance (0-25)

| Score | Criteria |
|-------|----------|
| 0-5 | Rigid; no adaptation |
| 6-10 | Some flexibility acknowledged |
| 11-15 | Explicit adaptation for known variations |
| 16-20 | Adaptation principles provided |
| 21-25 | Meta-guidance for novel variations |

---

## 3. Integration Dimension (0-100)

Evaluates how **Structure and Causality are linked**.

### Pattern-Causality Linkage (0-35)

| Score | Criteria |
|-------|----------|
| 0-7 | Exist but unconnected |
| 8-14 | Implicit connection |
| 15-21 | Explicit connection in some steps |
| 22-28 | Consistent connection throughout |
| 29-35 | Bidirectional: structure informs action, action validates structure |

**Core question:** Does action instantiate pattern?

### Reasoning Transparency (0-35)

| Score | Criteria |
|-------|----------|
| 0-7 | No reasoning; just steps |
| 8-14 | Brief reasoning |
| 15-21 | Reasoning at key points |
| 22-28 | Comprehensive reasoning |
| 29-35 | Causal chain explicit; learner could derive steps |

**Key indicator:** "We do X because Y"

### Scaffolding for Understanding (0-30)

| Score | Criteria |
|-------|----------|
| 0-6 | No scaffolding |
| 7-12 | Procedural scaffolding only |
| 13-18 | Scaffolding guides toward pattern |
| 19-24 | Scaffolding explicitly teaches pattern |
| 25-30 | Scaffolding enables independent discovery |

---

## 4. Abstraction Depth Assessment

### Level 0: No Abstraction
- No pattern identified
- Pure procedural steps
- Would fail on any variation

**Score:** Structure < 20

### Level 1: Instance Memory
- Concrete examples only
- No parameterization
- "2 + 2 = 4" as fact

**Detection:**
- Has examples: Yes
- Parameters: No
- Operation discussion: No
- Structure mapping: No

### Level 2: Pattern Recognition
- Parameters present
- Fixed operation type
- "n + n = 2n"

**Detection:**
- Has examples: Yes
- Parameters: Yes
- Operation discussion: No
- Structure mapping: No

### Level 3: Operation Abstraction
- Operation properties discussed
- Not just applied, but characterized
- "+" has closure, associativity, identity

**Detection:**
- Has examples: Yes
- Parameters: Yes
- Operation discussion: Yes
- Structure mapping: No

### Level 4: Structure Generalization
- Structure-preserving mappings
- Same pattern in different domains
- Group theory level abstraction

**Detection:**
- Has examples: Yes
- Parameters: Yes
- Operation discussion: Yes
- Structure mapping: Yes

---

## 5. Ability Level Assessment

### Level 0: Memorization

**Test criteria:**
- [ ] Would fail if symbols changed
- [ ] Would fail if context changed
- [ ] Can only repeat exactly

**Detection:**
```python
is_memorization = (
    would_fail_on_symbol_change and
    would_fail_on_context_change and
    no_adaptation_guidance
)
```

### Level 1: Understanding

**Test criteria:**
- [ ] Can explain why
- [ ] Can map instance to pattern
- [ ] Succeeds with new symbols, same structure

**Detection:**
```python
is_understanding = (
    has_explicit_pattern and
    has_instance_to_pattern_mapping and
    not is_memorization
)
```

### Level 2: Application

**Test criteria:**
- [ ] Handles noise
- [ ] Handles constraints
- [ ] Adapts to incomplete info

**Detection:**
```python
is_application = (
    causality_score >= 60 and
    has_noise_handling and
    has_constraint_adaptation
)
```

### Level 3: Creation

**Test criteria:**
- [ ] Has pattern modification guidance
- [ ] Has combination hints
- [ ] Identifies pattern boundaries

**Detection:**
```python
is_creation = (
    overall_score >= 65 and
    has_pattern_modification and
    has_combination_guidance
)
```

### Level 4: Meta-Creation

**Test criteria:**
- [ ] Can teach the pattern
- [ ] Can formalize for transfer
- [ ] Can compress to reusable form

**Detection:**
```python
is_meta_creation = (
    overall_score >= 80 and
    can_teach_pattern and
    can_compress_to_reusable
)
```

---

## 6. Structural Plasticity Assessment

### Graph Operation Support

| Operation | Detection Criteria |
|-----------|-------------------|
| **Attach** | Can new instances be linked? Has "applies to..." |
| **Merge** | Identifies merge candidates? Has "similar to..." |
| **Split** | Has boundary conditions? Has "doesn't apply when..." |
| **Lift** | Has generalization hints? Has "generalizes to..." |
| **Ground** | Has concrete anchors? Has specific examples |
| **Prune** | Identifies obsolescence? Has "superseded by..." |
| **Reweight** | Has confidence signals? Has "more/less certain when..." |

### Plasticity Score

| Score | Enabled Operations |
|-------|-------------------|
| Low | 0-2 |
| Medium | 3-4 |
| High | 5-7 |

---

## 7. Rote Detection Algorithm

A skill is classified as **rote memorization** if:

```python
def is_rote(skill, scores):
    checks = [
        scores.structure < 30,
        not has_explicit_pattern(skill),
        not has_invariants(skill),
        not has_reasoning(skill),
        scores.integration < 25,
        all_steps_are_rigid(skill)
    ]
    return sum(checks) >= 3
```

---

## 8. Verdict Assignment

| Verdict | Criteria |
|---------|----------|
| **ROTE** | is_rote = True |
| **PROCEDURAL** | Has process but structure < 40 |
| **STRUCTURAL** | structure >= 50, understanding level |
| **APPLICABLE** | application level, causality >= 60 |
| **CREATIVE** | creation level, has modification |
| **META** | meta-creation level, teachable |

---

## 9. Score Thresholds Summary

| Metric | Concern | Warning | Acceptable | Good | Excellent |
|--------|---------|---------|------------|------|-----------|
| Structure | <20 | 20-39 | 40-59 | 60-79 | 80+ |
| Causality | <20 | 20-39 | 40-59 | 60-79 | 80+ |
| Integration | <20 | 20-39 | 40-59 | 60-79 | 80+ |
| Overall | <20 | 20-39 | 40-59 | 60-79 | 80+ |
| Abstraction | L0 | L1 | L2 | L3 | L4 |
| Ability | L0 | L0-L1 | L1-L2 | L2-L3 | L3-L4 |
| Plasticity | 0-2 ops | - | 3-4 ops | - | 5-7 ops |
