---
name: kstar-skill-analyzer
description: >
  Evaluate KSTAR skills for depth of understanding vs rote memorization using the
  2-D world model (structure × causality) framework. Analyzes skills as structures-in-motion,
  not static objects. Assesses position on the ability ladder (L0:memorization →
  L1:understanding → L2:application → L3:creation → L4:meta-creation), measures
  abstraction depth through 4 levels (instance→pattern→operation→structure), detects
  whether skills support graph operations (attach/merge/split/lift/ground/prune/reweight),
  and evaluates transfer potential. Use when: (1) validating skill quality before
  publication, (2) assessing if skill teaches understanding or just procedure, (3)
  evaluating if skill supports restructuring not just accumulation, (4) measuring
  abstraction depth and invariance level, (5) checking if skill separates pattern
  from execution, (6) auditing skill libraries for structural plasticity, or (7)
  designing progression paths. Integrates with kstar-loop, student-companion, teacher-companion.
---

# KSTAR Skill Analyzer

Evaluates skills using the **memorization→understanding** distinction and the **2-D world model** (structure × causality). Skills are not static objects—they are **structures-in-motion** that remain valid only until the world model reorganizes.

## Core Theoretical Framework

### The Fundamental Distinction

| | Memorization | Understanding |
|---|---|---|
| **Form** | A → B (association) | Instance → Pattern → Instance |
| **What binds** | Symbols | Structure |
| **Transfer** | None (context-fragile) | High (structure-preserving) |
| **Test** | Change symbols → fails | Change symbols → succeeds |
| **Agent view** | Shallow retrieval | Model-based mapping |

> **Key principle**: The more invariant the abstraction, the deeper the understanding.

### The 2-D World Model

Every skill must address BOTH dimensions:

```
                    STRUCTURE (Pattern)
                           │
    "What kind of         │    • Invariants
     thing is this?"      │    • Symmetries
                          │    • Models
    ──────────────────────┼──────────────────────
                          │
    • Algorithms          │    "What happens
    • Procedures          │     if I do this?"
    • Feedback            │
                          │
                    CAUSALITY (Process)
```

**Structure alone** → Abstract but inert  
**Causality alone** → Reactive but blind  
**Understanding emerges** when causal execution is recognized as instance of structural pattern

### Abstraction Depth (4 Levels)

Using arithmetic as canonical example:

| Level | Name | Example | What's Understood |
|-------|------|---------|-------------------|
| **L1** | Instance Memory | 2 + 2 = 4 | Pure association |
| **L2** | Pattern Recognition | n + n = 2n | Parameterized structure |
| **L3** | Operation Abstraction | "+" has closure, associativity, identity | Operations, not numbers |
| **L4** | Structure Generalization | Any set + axioms → group | Structure-preserving mappings |

**Deep understanding** = operating on form, not symbols.

### The Ability Ladder (5 Levels)

| Level | Name | Can Do | Test |
|-------|------|--------|------|
| **L0** | Memorization | Recall facts, repeat steps | Change context → fails |
| **L1** | Understanding | Explain why, map instance→pattern | New symbols same structure → succeeds |
| **L2** | Application | Apply pattern with noise/constraints | Incomplete info → adapts |
| **L3** | Creation | Modify pattern, combine, invent | New domain → builds method |
| **L4** | Meta-Creation | Improve pattern, teach, formalize | Compresses experience into reusable form |

### Skills as Structures-in-Motion

Skills are **NOT**:
- Static units
- Checklist items
- Isolated competencies

Skills **ARE**:
- Provisional (temporary stabilization)
- Contextual (valid in scope)
- Composable (combine with others)
- Revisable (update on new evidence)

> A skill = active structure inside a larger model, not a standalone atom.

### Learning = Restructuring (Not Adding)

Four simultaneous operations:

| Operation | What It Does | Graph Equivalent |
|-----------|--------------|------------------|
| **Acquisition** | New associations, experiences | Node insertion |
| **Re-association** | Link new to existing patterns | Edge creation |
| **Consolidation** | Merge skills into higher pattern | Node merge, compression |
| **Differentiation** | Split overgeneralized skills | Node split, refinement |

**Learning updates relations more than contents.**

### Graph Operations on Skills

| Operation | Description | When Used |
|-----------|-------------|-----------|
| **Attach** | Link experience to existing pattern | New instance fits known pattern |
| **Merge** | Unify skills under higher abstraction | Discover shared structure |
| **Split** | Divide overgeneralized skill | Boundaries too coarse |
| **Lift** | Abstract pattern upward | Ready for generalization |
| **Ground** | Re-anchor abstraction to cases | Abstraction drifted |
| **Prune** | Remove obsolete paths | Superseded or wrong |
| **Reweight** | Change confidence/applicability | Evidence changes |

## Analysis Protocol

### Step 1: Assess the Pattern-Causality Split

**Core question**: Does the skill explicitly separate WHAT from HOW?

```python
def assess_pattern_causality_split(skill):
    pattern_evidence = {
        "explicit_pattern": has_pattern_declaration(skill),
        "invariants_identified": has_invariants(skill),
        "structure_named": pattern_is_named(skill),
        "abstraction_level": measure_abstraction_level(skill)
    }
    
    causality_evidence = {
        "action_sequence": has_action_plan(skill),
        "feedback_loops": has_feedback(skill),
        "temporal_order": steps_are_ordered(skill),
        "adaptation_guidance": has_adaptation(skill)
    }
    
    integration_evidence = {
        "pattern_grounds_action": actions_reference_pattern(skill),
        "action_validates_pattern": feedback_updates_pattern(skill),
        "reasoning_connects_both": reasoning_bridges_dimensions(skill)
    }
    
    return pattern_evidence, causality_evidence, integration_evidence
```

### Step 2: Measure Abstraction Depth

**Question**: At what level does this skill operate?

| Level | Detection Criteria |
|-------|-------------------|
| **L1** | Only concrete examples, no parameterization |
| **L2** | Parameters present, but fixed operation type |
| **L3** | Operation properties discussed, not just applied |
| **L4** | Structure-preserving mappings to other domains |

```python
def measure_abstraction_depth(skill):
    if has_structure_generalization(skill):
        return 4, "Structure Generalization"
    if discusses_operation_properties(skill):
        return 3, "Operation Abstraction"
    if has_parameterized_pattern(skill):
        return 2, "Pattern Recognition"
    if has_concrete_examples_only(skill):
        return 1, "Instance Memory"
    return 0, "No Abstraction"
```

### Step 3: Determine Ability Level

**Question**: What capability does this skill enable?

```python
def determine_ability_level(skill, scores):
    # L4: Meta-Creation
    if (scores.overall >= 80 and 
        can_teach_pattern(skill) and 
        can_compress_to_reusable(skill)):
        return 4, "Meta-Creation"
    
    # L3: Creation
    if (scores.overall >= 65 and 
        has_pattern_modification(skill) and
        has_combination_guidance(skill)):
        return 3, "Creation"
    
    # L2: Application
    if (scores.causality >= 60 and 
        has_noise_handling(skill) and
        has_constraint_adaptation(skill)):
        return 2, "Application"
    
    # L1: Understanding
    if (scores.structure >= 50 and 
        has_explicit_pattern(skill) and
        has_instance_to_pattern_mapping(skill)):
        return 1, "Understanding"
    
    # L0: Memorization
    return 0, "Memorization"
```

### Step 4: Evaluate Structural Plasticity

**Question**: Does this skill support restructuring or only accumulation?

```python
def evaluate_structural_plasticity(skill):
    plasticity = {
        "supports_attach": can_attach_new_instances(skill),
        "supports_merge": identifies_merge_candidates(skill),
        "supports_split": has_boundary_conditions(skill),
        "supports_lift": has_generalization_hints(skill),
        "supports_ground": has_concrete_anchors(skill),
        "supports_prune": identifies_obsolescence_criteria(skill),
        "supports_reweight": has_confidence_signals(skill)
    }
    
    # Plasticity score = how many operations are enabled
    enabled = sum(plasticity.values())
    
    if enabled >= 5:
        return "high", plasticity
    elif enabled >= 3:
        return "medium", plasticity
    else:
        return "low", plasticity
```

### Step 5: Generate Complete Diagnosis

See [references/diagnosis-schema.md](references/diagnosis-schema.md) for complete output schema.

## Diagnostic Output

```yaml
SkillDiagnosis:
  skill_id: string
  analyzed_at: datetime
  
  # 2-D World Model Scores
  dimensions:
    structure_score: 0-100
    causality_score: 0-100
    integration_score: 0-100
  
  # Abstraction Assessment
  abstraction:
    depth_level: 1-4
    depth_name: string  # "Instance" | "Pattern" | "Operation" | "Structure"
    invariance_quality: 0-100
  
  # Ability Assessment
  ability:
    level: 0-4
    name: string  # "Memorization" → "Meta-Creation"
    evidence: [string]
  
  # Structural Plasticity
  plasticity:
    score: "low" | "medium" | "high"
    supported_operations: [string]
    missing_operations: [string]
  
  # Classification
  flags:
    is_rote: boolean           # Pure memorization
    is_understanding: boolean  # Has structural mapping
    is_applicable: boolean     # Can handle context variation
    is_creative: boolean       # Enables pattern modification
    is_teachable: boolean      # Can transfer to others
    separates_pattern_process: boolean
    supports_restructuring: boolean
  
  # Recommendations
  recommendations:
    to_add_understanding: [string]
    to_add_application: [string]
    to_add_plasticity: [string]
    priority_order: [string]
```

## Design Rules for Skills (Derived from Theory)

### Rule 1: No skill without explicit pattern
Every skill must answer: "What general structure does this instantiate?"  
If it doesn't → it's rote.

### Rule 2: Separate structure from execution
Pattern = reusable across contexts  
Execution = contextual to situation  
Store them separately but linked.

### Rule 3: Measure by abstraction, not content
Progress is NOT "more facts"  
Progress IS "fewer assumptions, greater invariance, broader transfer"

### Rule 4: Teaching = aligning instance → pattern
Not dumping steps, but showing WHY this belongs to existing structure.

### Rule 5: Skills must support restructuring
Must enable: attach, merge, split, lift, ground, prune, reweight  
Not just: add more facts

## Files

- `scripts/analyzer.py` - Core analysis engine with all detection functions
- `scripts/abstraction_analyzer.py` - Abstraction depth measurement
- `scripts/plasticity_analyzer.py` - Structural plasticity evaluation
- `references/scoring-rubrics.md` - Complete scoring criteria
- `references/detection-patterns.md` - Heuristics for detection
- `references/diagnosis-schema.md` - Full output schema
- `references/theoretical-foundation.md` - Complete theoretical framework
