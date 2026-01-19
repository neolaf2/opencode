# Rewrite Rules

Complete specification of memory rewrite rules that transform raw K-STAR episodes into executable, generalizable skill objects.

## The Three Memory Layers

| Layer | Contents | Mutability |
|-------|----------|------------|
| **Episodes** | Raw K-STAR traces | Immutable (append-only) |
| **Skills** | Compiled skill objects | Mutable (versioned) |
| **Indices** | Retrieval views | Mutable (derived) |

## Rule S1: PROMOTE (Candidate → Validated)

**Trigger**: An episode succeeds and matches a candidate skill.

**Preconditions**:
- Skill is in CANDIDATE state
- Episode succeeded
- Episode's skill_id matches the candidate

**Rewrite**:
```
skill.lifecycle_state = VALIDATED
skill.created_from_episodes.append(episode.episode_id)
skill.first_success_context = episode.situation
emit(SkillPromoted)
```

**Rationale**: First success provides evidence that the skill works in at least one context.

---

## Rule S2: GENERALIZE by Parameterization

**Trigger**: Two or more validated episodes differ only by substitutable elements.

**Preconditions**:
- Skill is in VALIDATED state
- ≥2 episodes exist with substitutable differences

**Rewrite**:
```
for diff in find_substitutable_differences(episodes):
    param = Parameter(
        name = infer_name(diff),
        type = infer_type(diff.values),
        examples = diff.values
    )
    skill.parameter_schema.append(param)
    skill.plan_template = parameterize(plan, diff, param)

skill.lifecycle_state = GENERALIZING
emit(SkillGeneralized)
```

**Example**:
```
Episode 1: "email Cornell Graduate School with resume.pdf"
Episode 2: "email admissions office with transcript.pdf"

→ Generalized: "email {recipient} with {attachment}"
   Parameters:
     - recipient: string
     - attachment: string
```

**Rationale**: This is the first step from **memorization → understanding**. The agent recognizes that multiple instances share a common pattern.

---

## Rule S3: LEARN Applicability Boundaries

**Trigger**: Skill succeeds in some contexts and fails in others.

**Preconditions**:
- Skill is in VALIDATED or GENERALIZING state
- Has both successful and failed episodes

**Rewrite**:
```
features = find_discriminating_features(successes, failures)

for feature in features:
    condition = Condition(
        expression = feature.condition,
        type = feature.type  # "required" | "forbidden"
    )
    
    if feature.type == "required":
        skill.applicability_conditions.append(condition)
    else:
        skill.do_not_apply_when.append(condition)

emit(BoundariesLearned)
```

**Example**:
```
Successes: all have tool.browser.available = true
Failures: all have tool.browser.available = false

→ Applicability condition: "tool.browser.available == true"
```

**Rationale**: Turns "it works sometimes" into **"it works when..."** This prevents overgeneralization.

---

## Rule S4: SPLIT on Bimodal Failure

**Trigger**: Skill exhibits two distinct regimes (clusters of failure modes).

**Preconditions**:
- Skill is in GENERALIZING or OPERATIONAL state
- Episode distribution is bimodal (distinct clusters)

**Detection**:
```
clusters = cluster_by_regime(episodes)
if len(clusters) >= 2 and success_rate_variance(clusters) > threshold:
    → Trigger split
```

**Rewrite**:
```
new_skills = []
for cluster in clusters:
    new_skill = skill.fork()
    new_skill.applicability_conditions = cluster.conditions
    new_skill.episodes = cluster.episodes
    new_skill.lifecycle_state = VALIDATED
    new_skills.append(new_skill)

skill.lifecycle_state = DEPRECATED
skill.superseded_by = new_skills[0].skill_id
emit(SkillSplit)
```

**Example**:
```
"Send message" skill fails differently:
  - Cluster A: SMS fails when phone is offline
  - Cluster B: Email fails when server is down

→ Split into:
  - "Send SMS" (requires: phone.online)
  - "Send Email" (requires: server.reachable)
```

**Rationale**: Prevents **overgeneralization**, a major cause of flat DB uselessness.

---

## Rule S5: MERGE Duplicates

**Trigger**: Two skills have high overlap in applicability and plan structure.

**Preconditions**:
- Two skills exist with overlap > threshold
- Neither is DEPRECATED or QUARANTINED

**Detection**:
```
overlap = compute_overlap(skill_a, skill_b)
if overlap > MERGE_THRESHOLD:
    → Trigger merge
```

**Rewrite**:
```
canonical = skill_a if skill_a.success_rate >= skill_b.success_rate else skill_b
deprecated = skill_b if canonical == skill_a else skill_a

canonical.episodes.extend(deprecated.episodes)
canonical.applicability_conditions = union(
    canonical.applicability_conditions,
    deprecated.applicability_conditions
)

deprecated.lifecycle_state = DEPRECATED
deprecated.superseded_by = canonical.skill_id
create_alias(deprecated.skill_id, canonical.skill_id)

emit(SkillsMerged)
```

**Rationale**: Eliminates redundancy, consolidates knowledge into canonical skills.

---

## Rule S6: COMPOSE Macro-Skills

**Trigger**: Agent repeatedly executes skill sequence X → Y → Z for a higher task.

**Preconditions**:
- Sequence appears ≥ N times (configurable)
- All component skills are OPERATIONAL or REFINED

**Detection**:
```
frequent_sequences = find_frequent_sequences(episodes, min_frequency=3)
for sequence, count in frequent_sequences:
    if not macro_exists(sequence):
        → Trigger composition
```

**Rewrite**:
```
macro = ComposedSkill(
    skill_id = new_uuid(),
    name = f"Composed: {sequence}",
    component_skills = sequence,
    composition_type = SEQUENCE,
    lifecycle_state = CANDIDATE
)

# Learn inter-skill bindings
for i in range(len(sequence) - 1):
    binding = learn_binding(
        output_of = sequence[i],
        input_to = sequence[i + 1]
    )
    macro.inter_skill_bindings.append(binding)

emit(MacroComposed)
```

**Example**:
```
Frequent sequence:
  1. literature_search → 2. outline_generation → 3. draft_writing

→ Composed skill: "Write research paper"
   Bindings:
     - literature_search.results → outline_generation.sources
     - outline_generation.outline → draft_writing.structure
```

**Rationale**: Creates higher-level abstractions from lower-level skills.

---

## Rule S7: QUARANTINE on Failure

**Trigger**: Safety violation, repeated failure, or tool breakage.

**Preconditions**:
- Skill is not already QUARANTINED or DEPRECATED
- One of:
  - Safety violation detected
  - Failure rate > threshold
  - Tool interface broken
  - Verification unclear

**Rewrite**:
```
skill.previous_state = skill.lifecycle_state
skill.lifecycle_state = QUARANTINED
skill.quarantine_reason = reason
skill.quarantine_evidence = [evidence_episode_ids]
skill.review_required = true

remove_from_retrieval_index(skill.skill_id)
emit(SkillQuarantined)
```

**Recovery**:
```
# After review and fix
skill.lifecycle_state = skill.previous_state
skill.quarantine_reason = null
add_to_retrieval_index(skill.skill_id)
```

**Rationale**: Prevents automatic execution of potentially harmful or unreliable skills.

---

## Rule S8: DEPRECATE on Supersession

**Trigger**: Skill replaced by better version or invalid in current environment.

**Preconditions**:
- Skill is not already DEPRECATED
- One of:
  - Superseded by better skill
  - Environment changed (skill no longer valid)
  - Inactive for extended period

**Rewrite**:
```
skill.lifecycle_state = DEPRECATED
skill.deprecation_reason = reason
skill.superseded_by = superseding_skill_id  # may be null

remove_from_retrieval_index(skill.skill_id)
add_to_archive_index(skill.skill_id)

emit(SkillDeprecated)
```

**Rationale**: Maintains clean skill library, preserves traceability.

---

## Rule Application Order

The consolidation loop applies rules in this order:

1. **S1: PROMOTE** - Move candidates forward
2. **S2: GENERALIZE** - Extract parameters
3. **S3: LEARN_BOUNDARIES** - Add conditions
4. **S4: SPLIT** - Divide bimodal skills
5. **S5: MERGE** - Unify duplicates
6. **S6: COMPOSE** - Create macro-skills
7. **S7: QUARANTINE** - Isolate failures
8. **S8: DEPRECATE** - Archive obsolete

---

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_executions_for_operational` | 5 | Executions needed for OPERATIONAL |
| `success_rate_for_operational` | 0.8 | Success rate needed for OPERATIONAL |
| `min_episodes_for_generalization` | 2 | Episodes needed for S2 |
| `bimodal_difference_threshold` | 0.3 | Success rate variance for S4 |
| `merge_overlap_threshold` | 0.7 | Overlap needed for S5 |
| `min_sequence_frequency` | 3 | Occurrences needed for S6 |
| `failure_rate_for_quarantine` | 0.7 | Failure rate triggering S7 |
| `days_inactive_for_deprecation` | 90 | Inactivity period for S8 |

---

## Graph Operations Summary

| Rule | Graph Operation | Effect |
|------|-----------------|--------|
| S1 | Promote node | Node gains new state |
| S2 | Add parameters | Node becomes template |
| S3 | Add edges | Boundary edges added |
| S4 | Split node | One node → multiple nodes |
| S5 | Merge nodes | Multiple nodes → one node |
| S6 | Compose nodes | Multiple nodes → parent node |
| S7 | Isolate node | Node removed from active graph |
| S8 | Archive node | Node moved to archive graph |

This is **learning as graph rewriting**, not record insertion.
