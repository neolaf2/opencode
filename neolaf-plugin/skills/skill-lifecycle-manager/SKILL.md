---
name: skill-lifecycle-manager
description: >
  Manages the complete lifecycle of KSTAR skills from raw episodes to operational
  production-grade skills. Implements formal lifecycle states (Unknown→Candidate→
  Validated→Generalizing→Operational→Refined→Composed), memory rewrite rules for
  skill compilation (promote, generalize, split, merge, compose), and governance
  mechanisms (quarantine, deprecation, versioning). Solves two failure modes:
  (1) LLM-only systems that understand but don't persist, and (2) flat K-STAR DBs
  that store but can't abstract. Use when: (1) compiling raw episodes into skills,
  (2) promoting skills through lifecycle stages, (3) generalizing skills by
  parameterization, (4) splitting over-generalized skills, (5) merging duplicates,
  (6) composing macro-skills, (7) quarantining unsafe skills, (8) running overnight
  consolidation. Integrates with kstar-loop, kstar-skill-analyzer, student-companion,
  teacher-companion.
---

# Skill Lifecycle Manager

Transforms raw K-STAR episodes into **executable, generalizable skill objects** through a formal lifecycle with governed state transitions and memory rewrite rules.

## The Two Failure Modes This Solves

| Failure Mode | Problem | Solution |
|--------------|---------|----------|
| **LLM-only** | Can infer/understand in-context, but doesn't stabilize into durable skills | Memory + consolidation + lifecycle governance |
| **Flat K-STAR DB** | Can store/memorize, but without abstraction, indexing, applicability | Rewrite rules + skill compilation + lifecycle states |

## Core Architecture

A "skill" is a **first-class object** with two layers:

| Layer | Contents | Purpose |
|-------|----------|---------|
| **Symbolic** | K-STAR traces + templates + constraints | Explicit, inspectable, editable |
| **Neural** | Embeddings + retrieval indices | Fast retrieval + adaptation |

## Skill Lifecycle States

```
                                    ┌─────────────┐
                                    │   UNKNOWN   │
                                    │   (state 0) │
                                    └──────┬──────┘
                                           │ retrieval fails
                                           ▼
                                    ┌─────────────┐
                              ┌────►│  CANDIDATE  │◄───── from teacher/oracle
                              │     │   (state 1) │       from web/docs
                              │     └──────┬──────┘       from transfer
                              │            │
                              │    success │ failure
                              │            ▼
                        rejected    ┌─────────────┐
                                    │  VALIDATED  │
                                    │   (state 2) │
                                    └──────┬──────┘
                                           │ new contexts
                                           ▼
                                    ┌─────────────┐
                              ┌────►│GENERALIZING │
                              │     │   (state 3) │
                              │     └──────┬──────┘
                              │            │
                     split ◄─┴─► merge     │ stable success
                                           ▼
                                    ┌─────────────┐
                              ┌────►│ OPERATIONAL │◄───┐
                              │     │   (state 4) │    │
                              │     └──────┬──────┘    │
                              │            │           │
                        regressed    improved     composed
                              │            ▼           │
                              │     ┌─────────────┐    │
                              │     │   REFINED   │    │
                              │     │   (state 5) │    │
                              │     └─────────────┘    │
                              │                        │
                              │     ┌─────────────┐    │
                              └────►│  COMPOSED   │────┘
                                    │   (state 6) │
                                    └─────────────┘

                              failure/safety issue
                                        │
                                        ▼
                                    ┌─────────────┐
                                    │ QUARANTINED │
                                    │   (state 7) │
                                    └─────────────┘

                              superseded/invalid
                                        │
                                        ▼
                                    ┌─────────────┐
                                    │ DEPRECATED  │
                                    │   (state 8) │
                                    └─────────────┘
```

### State 0: UNKNOWN

No known skill covers the task (S,T) with acceptable confidence.

**Trigger**: Retrieval fails or confidence below threshold.

**Transition**: → CANDIDATE (via exploration)

### State 1: CANDIDATE (Exploration)

Skill exists as a hypothesis from:
- Teacher/oracle provision
- Web/documentation search
- Trial-and-error exploration
- Transfer from another agent

**Required artifacts**:
```yaml
CandidateSkill:
  prototype_plan: Plan           # Proposed action sequence
  safety_constraints: [Guard]    # Guardrails
  success_criteria: Criteria     # Binary OK check
  source: SourceType             # teacher | web | exploration | transfer
  created_at: datetime
```

**Transitions**:
- → VALIDATED (if succeeds at least once)
- → REJECTED (if repeatedly fails beyond threshold)

### State 2: VALIDATED (Single-instance success)

Skill has succeeded at least once in a real execution context.

**Warning**: Still fragile—may be overfit to one context.

**Required artifacts**:
```yaml
ValidatedSkill:
  base: CandidateSkill
  first_success_episode: EpisodeID
  success_context: Context       # The specific context it worked in
  validation_count: 1
```

**Transitions**:
- → GENERALIZING (if new contexts appear)
- → QUARANTINED (if fails in mild variations)

### State 3: GENERALIZING (Multi-context adaptation)

Skill is being exercised across varied contexts. Agent is actively learning:
- What **must** stay the same (invariants)
- What **can** vary (parameters)
- Which parameters control variation

**Required artifacts**:
```yaml
GeneralizingSkill:
  base: ValidatedSkill
  episodes: [EpisodeID]          # Multiple execution contexts
  invariants_discovered: [Invariant]
  parameters_discovered: [Parameter]
  variation_map: Dict[Feature, Variance]
  success_rate_by_context: Dict[Context, float]
```

**Transitions**:
- → OPERATIONAL (if stable success rate ≥ threshold)
- → SPLIT (if trying to cover two distinct regimes)
- → MERGED (if duplicating another skill)

### State 4: OPERATIONAL (Production-grade)

Skill is eligible for **operation mode** by default.

**Required artifacts**:
```yaml
OperationalSkill:
  skill_id: string
  version: SemanticVersion
  
  # Applicability
  applicability_signature: Signature  # σ(S,T)
  applicability_conditions: [Condition]
  do_not_apply_when: [Condition]
  
  # Execution
  parameter_schema: Schema            # Slots to fill
  plan_template: PlanTemplate         # Â(P)
  verification_steps: [Verification]  # How to confirm success
  fallback_plan: Plan                 # What to do if fails
  
  # Dependencies
  required_tools: [ToolID]
  required_skills: [SkillID]
  required_permissions: [Permission]
  
  # Reliability
  success_rate: float
  success_rate_by_regime: Dict[Regime, float]
  total_executions: int
  last_success: datetime
  last_failure: datetime
  
  # Explanations
  scaffolding: ScaffoldingConfig
  reasoning: string
```

**Transitions**:
- → REFINED (if improved)
- → REGRESSED (if environment/tool drift causes failures)
- → DEPRECATED (if replaced)
- → QUARANTINED (if safety issue)

### State 5: REFINED (Optimized operational)

Same skill, improved:
- Fewer steps
- Lower latency/cost
- Better robustness
- Better explanations/scaffolding

This is the **consolidation and compression** stage.

**Required artifacts**:
```yaml
RefinedSkill:
  base: OperationalSkill
  refinement_type: compression | optimization | scaffolding
  improvement_delta:
    steps_reduced: int
    latency_reduced: Duration
    success_rate_improvement: float
  previous_version: SkillVersion
```

### State 6: COMPOSED (Macro-skill)

Higher-level skill built from multiple operational skills.

**Example**: "Write and submit a research paper" = 
- literature_search + 
- outline_generation + 
- draft_writing + 
- citation_formatting + 
- submission_steps

**Required artifacts**:
```yaml
ComposedSkill:
  base: OperationalSkill
  component_skills: [SkillID]
  composition_type: sequence | parallel | conditional
  orchestration_logic: OrchestrationPlan
  inter_skill_bindings: [Binding]  # How outputs connect to inputs
```

**Transitions**:
- → OPERATIONAL (macro) once stable
- → SPLIT/MERGE as structure evolves

### State 7: QUARANTINED (Safety or reliability failure)

Skill is **prevented from automatic execution**.

**Triggers**:
- Unexpected harmful side effects
- Repeated failure beyond threshold
- Tool interface changes (breaking)
- Unclear verification (can't tell if it worked)

**Required artifacts**:
```yaml
QuarantinedSkill:
  base: AnySkillState
  quarantine_reason: QuarantineReason
  quarantine_date: datetime
  quarantine_evidence: [EpisodeID]
  review_required: boolean
  reviewer: human | teacher | system
```

**Transitions**:
- → Previous state (after review and fix)
- → DEPRECATED (if unfixable)

### State 8: DEPRECATED / ARCHIVED

Skill not used, superseded, or invalid in current environment.

**Retained for**: Traceability, historical analysis.
**Excluded from**: Default retrieval.

**Required artifacts**:
```yaml
DeprecatedSkill:
  base: AnySkillState
  deprecation_reason: DeprecationReason
  deprecated_date: datetime
  superseded_by: SkillID | null
  retain_until: datetime | forever
```

## Memory Architecture (Three Layers)

### Layer 1: Episodes (Append-only truth)

Episodes are **immutable ground truth**. Never rewrite them.

```yaml
Episode:
  episode_id: UUID
  timestamp: datetime
  
  # K-STAR components
  situation: S
  task: T
  plan: Â                    # Proposed plan
  actions: [A]               # Actual tool logs + steps
  result: R                  # Success/failure + outcome
  
  # Meta
  confidence_before: float   # Ê before execution
  confidence_after: float    # E after execution
  environment_signature:
    tool_versions: Dict[Tool, Version]
    context_keys: [string]
  
  # Links
  skill_id: SkillID | null   # Which skill was attempted
  skill_version: Version | null
```

**Rule E1**: Always store an episode for every meaningful attempt.

### Layer 2: Skills (Compiled objects)

Skills are **mutable, versioned** compilations of episodes.

```yaml
Skill:
  skill_id: UUID
  version: SemanticVersion
  lifecycle_state: LifecycleState
  
  # Applicability
  applicability_signature: EmbeddingVector
  applicability_conditions: [Condition]
  parameter_schema: Schema
  
  # Execution
  plan_template: PlanTemplate
  verification: Verification
  fallbacks: [Plan]
  
  # Dependencies
  required_tools: [ToolID]
  required_skills: [SkillID]
  
  # Reliability
  success_rate: float
  success_rate_by_regime: Dict[Regime, float]
  episode_ids: [EpisodeID]   # Evidence
  
  # Provenance
  created_from: [EpisodeID]
  last_modified: datetime
  modification_history: [Modification]
```

### Layer 3: Indices (Retrieval views)

Indices are **mutable, derived** views for fast retrieval.

```yaml
SkillIndex:
  # By situation signature
  situation_index: Dict[SituationEmbedding, [SkillID]]
  
  # By task type
  task_index: Dict[TaskType, [SkillID]]
  
  # By tool
  tool_index: Dict[ToolID, [SkillID]]
  
  # By lifecycle state
  state_index: Dict[LifecycleState, [SkillID]]
  
  # By success rate
  reliability_index: SortedList[(SkillID, float)]
```

## Memory Rewrite Rules

### Rule S1: PROMOTE (Candidate → Validated)

**Trigger**: An episode succeeds and matches a candidate.

**Rewrite**:
```python
def promote_to_validated(candidate: CandidateSkill, episode: Episode):
    if episode.result.success and matches(candidate, episode):
        candidate.lifecycle_state = VALIDATED
        candidate.first_success_episode = episode.episode_id
        candidate.success_context = episode.situation
        candidate.validation_count = 1
        emit_event(SkillPromoted(candidate.skill_id, VALIDATED))
```

### Rule S2: GENERALIZE by Parameterization

**Trigger**: Two or more validated episodes differ only by substitutable elements.

**Rewrite**:
```python
def generalize_by_parameterization(skill: ValidatedSkill, episodes: [Episode]):
    # Find differing elements
    diffs = find_substitutable_differences(episodes)
    
    for diff in diffs:
        # Replace constants with parameters
        param = Parameter(
            name=infer_param_name(diff),
            type=infer_param_type(diff.values),
            examples=diff.values
        )
        skill.parameter_schema.add(param)
        skill.plan_template = parameterize(skill.plan_template, diff, param)
    
    skill.lifecycle_state = GENERALIZING
    emit_event(SkillGeneralized(skill.skill_id, params=diffs))
```

**Example**:
- "email Cornell Graduate School" + "email admissions office" →
- "email {recipient} with {attachment} using {template}"

This is the first step from **memorization → understanding**.

### Rule S3: LEARN Applicability Boundaries

**Trigger**: Skill succeeds in some contexts, fails in others.

**Rewrite**:
```python
def learn_boundaries(skill: GeneralizingSkill, episodes: [Episode]):
    successes = [e for e in episodes if e.result.success]
    failures = [e for e in episodes if not e.result.success]
    
    # Find discriminating features
    guards = discriminate(successes, failures)
    
    for guard in guards:
        if guard.type == REQUIRED:
            skill.applicability_conditions.append(guard.condition)
        elif guard.type == FORBIDDEN:
            skill.do_not_apply_when.append(guard.condition)
    
    emit_event(BoundariesLearned(skill.skill_id, guards))
```

This turns "it works sometimes" into **"it works when..."**

### Rule S4: SPLIT on Bimodal Failure

**Trigger**: Skill exhibits two distinct regimes (clusters of failure modes).

**Rewrite**:
```python
def split_skill(skill: GeneralizingSkill, episodes: [Episode]):
    # Cluster by failure modes / context features
    clusters = cluster_by_regime(episodes)
    
    if len(clusters) >= 2 and clusters_are_distinct(clusters):
        new_skills = []
        for cluster in clusters:
            new_skill = skill.fork()
            new_skill.applicability_conditions = cluster.conditions
            new_skill.episodes = cluster.episodes
            new_skills.append(new_skill)
        
        skill.lifecycle_state = DEPRECATED
        skill.superseded_by = [s.skill_id for s in new_skills]
        
        emit_event(SkillSplit(skill.skill_id, new_skills))
        return new_skills
```

This prevents **overgeneralization**—a major cause of flat DB uselessness.

### Rule S5: MERGE Duplicates

**Trigger**: Two skills have high overlap in applicability and plan structure.

**Rewrite**:
```python
def merge_skills(skill_a: Skill, skill_b: Skill):
    if overlap(skill_a, skill_b) > MERGE_THRESHOLD:
        canonical = skill_a if skill_a.success_rate >= skill_b.success_rate else skill_b
        deprecated = skill_b if canonical == skill_a else skill_a
        
        # Merge knowledge
        canonical.episodes.extend(deprecated.episodes)
        canonical.applicability_conditions = union(
            canonical.applicability_conditions,
            deprecated.applicability_conditions
        )
        
        # Create alias
        deprecated.lifecycle_state = DEPRECATED
        deprecated.superseded_by = canonical.skill_id
        create_alias(deprecated.skill_id, canonical.skill_id)
        
        emit_event(SkillsMerged(skill_a.skill_id, skill_b.skill_id, canonical.skill_id))
```

### Rule S6: COMPOSE Macro-Skills

**Trigger**: Agent repeatedly executes Skill X → Y → Z for a higher task.

**Rewrite**:
```python
def compose_macro(frequent_sequence: [SkillID], higher_task: Task):
    macro = ComposedSkill(
        skill_id=new_uuid(),
        component_skills=frequent_sequence,
        composition_type=SEQUENCE,
        task=higher_task
    )
    
    # Learn inter-skill bindings
    for i in range(len(frequent_sequence) - 1):
        binding = learn_binding(
            output_of=frequent_sequence[i],
            input_to=frequent_sequence[i + 1]
        )
        macro.inter_skill_bindings.append(binding)
    
    macro.lifecycle_state = CANDIDATE
    emit_event(MacroComposed(macro.skill_id, frequent_sequence))
    return macro
```

### Rule S7: QUARANTINE on Failure

**Trigger**: Safety violation, repeated failure, or tool breakage.

**Rewrite**:
```python
def quarantine_skill(skill: Skill, reason: QuarantineReason, evidence: [Episode]):
    skill.previous_state = skill.lifecycle_state
    skill.lifecycle_state = QUARANTINED
    skill.quarantine_reason = reason
    skill.quarantine_evidence = [e.episode_id for e in evidence]
    skill.review_required = True
    
    # Remove from active indices
    remove_from_retrieval_index(skill.skill_id)
    
    emit_event(SkillQuarantined(skill.skill_id, reason))
```

### Rule S8: DEPRECATE on Supersession

**Trigger**: Skill replaced by better version or invalid in environment.

**Rewrite**:
```python
def deprecate_skill(skill: Skill, reason: DeprecationReason, superseded_by: SkillID = None):
    skill.lifecycle_state = DEPRECATED
    skill.deprecation_reason = reason
    skill.superseded_by = superseded_by
    
    # Remove from active indices, keep in archive
    remove_from_retrieval_index(skill.skill_id)
    add_to_archive_index(skill.skill_id)
    
    emit_event(SkillDeprecated(skill.skill_id, reason, superseded_by))
```

## Overnight Consolidation Loop

See [scripts/consolidation_loop.py](scripts/consolidation_loop.py) for implementation.

The consolidation loop runs periodically (e.g., nightly) to:

1. **Scan for promotion candidates**: Episodes that succeeded but skill is still CANDIDATE
2. **Scan for generalization opportunities**: Multiple episodes with substitutable differences
3. **Scan for split candidates**: Bimodal failure patterns
4. **Scan for merge candidates**: Duplicate/overlapping skills
5. **Scan for composition opportunities**: Repeated skill sequences
6. **Scan for quarantine needs**: Degrading success rates
7. **Update indices**: Rebuild retrieval indices with new knowledge
8. **Update neural embeddings**: Retrain/fine-tune skill embeddings

## Why This Solves the Flat DB Problem

A flat DB has **no notion of**:
- ✗ Validation maturity
- ✗ Applicability boundaries
- ✗ Versioning
- ✗ Composition
- ✗ Quarantine/rollback

The lifecycle gives you a **governed skill ecosystem** instead of a memory dump.

## Files

- `scripts/lifecycle_manager.py` - State machine and transitions
- `scripts/rewrite_rules.py` - Memory rewrite rule implementations
- `scripts/consolidation_loop.py` - Overnight consolidation logic
- `references/lifecycle-states.md` - Detailed state documentation
- `references/rewrite-rules.md` - Complete rewrite rule specifications
- `references/schemas.md` - All data schemas
