# Schemas

Complete data schemas for the skill lifecycle manager.

## Episode Schema (Layer 1: Append-only truth)

Episodes are **immutable ground truth**. Never rewrite them.

```yaml
Episode:
  episode_id: UUID
  timestamp: datetime (ISO 8601)
  
  # K-STAR components
  situation:
    context: Dict[string, any]    # Environmental context
    state: Dict[string, any]      # Agent/system state
    constraints: [string]         # Active constraints
    
  task:
    goal: string                  # What to accomplish
    type: string                  # Task classification
    parameters: Dict[string, any] # Task inputs
    success_criteria: [Criterion] # How to know if done
    
  plan:                           # Proposed plan (Â)
    - step_id: string
      action_type: string
      description: string
      parameters: Dict[string, string]
      expected_result: string
      
  actions:                        # Actual actions (A)
    - action_id: string
      timestamp: datetime
      action_type: string
      input: any
      output: any
      success: boolean
      error: string | null
      duration_ms: integer
      
  result:                         # Outcome (R)
    success: boolean
    outcome: any
    error: string | null
    completion_time: datetime
  
  # Meta
  confidence_before: float (0-1)  # Ê before execution
  confidence_after: float (0-1)   # E after execution
  
  environment_signature:
    tool_versions: Dict[Tool, Version]
    context_keys: [string]
    platform: string
    
  # Links
  skill_id: SkillID | null        # Which skill was attempted
  skill_version: Version | null
  session_id: string | null       # Session grouping
```

## Skill Schema (Layer 2: Compiled objects)

Skills are **mutable, versioned** compilations of episodes.

```yaml
Skill:
  # Identity
  skill_id: UUID
  name: string
  description: string
  version: SemanticVersion        # e.g., "1.2.3"
  
  # Lifecycle
  lifecycle_state: LifecycleState
  previous_state: LifecycleState | null  # For quarantine recovery
  
  # ─────────────────────────────────────────────────────────────
  # APPLICABILITY (When to use this skill)
  # ─────────────────────────────────────────────────────────────
  
  applicability_signature:        # Embedding for retrieval
    vector: [float]
    dimensions: integer
    
  applicability_conditions:       # Explicit conditions
    - expression: string          # e.g., "tool.available('browser')"
      description: string
      type: "required"
      confidence: float
      
  do_not_apply_when:              # Negative conditions
    - expression: string          # e.g., "context.offline == true"
      description: string
      type: "forbidden"
      confidence: float
  
  # ─────────────────────────────────────────────────────────────
  # PARAMETERS (What to fill in)
  # ─────────────────────────────────────────────────────────────
  
  parameter_schema:
    - name: string
      type: string                # string | number | boolean | object | array
      description: string
      required: boolean
      default: any | null
      examples: [any]
      validation: string | null   # Validation expression
  
  # ─────────────────────────────────────────────────────────────
  # EXECUTION (How to do it)
  # ─────────────────────────────────────────────────────────────
  
  plan_template:
    steps:
      - step_id: string
        action_type: string
        description: string
        parameters: Dict[string, string]  # May include ${param} refs
        expected_result: string
        preconditions: [string]
        fallback: string | null
        
    parameters:                   # Template-level parameters
      - name: string
        type: string
        
  verification_steps:             # How to confirm success
    - check: string               # Verification expression
      description: string
      timeout_seconds: integer
      
  fallback_plans:                 # What to do if fails
    - trigger: string             # When to use this fallback
      plan: PlanTemplate
  
  # ─────────────────────────────────────────────────────────────
  # DEPENDENCIES
  # ─────────────────────────────────────────────────────────────
  
  required_tools: [ToolID]
  required_skills: [SkillID]      # For compositions
  required_permissions: [Permission]
  
  # ─────────────────────────────────────────────────────────────
  # RELIABILITY (How well it works)
  # ─────────────────────────────────────────────────────────────
  
  success_rate: float (0-1)
  success_rate_by_regime:         # Breakdown by context
    regime_key: float
    
  total_executions: integer
  episode_ids: [EpisodeID]        # Evidence
  
  last_success: datetime | null
  last_failure: datetime | null
  
  # ─────────────────────────────────────────────────────────────
  # PROVENANCE (Where it came from)
  # ─────────────────────────────────────────────────────────────
  
  source: SourceType              # teacher | web | exploration | transfer | split | merge | composition
  created_at: datetime
  created_by: AgentID | UserID
  created_from_episodes: [EpisodeID]
  
  last_modified: datetime
  modification_history:
    - timestamp: datetime
      type: string                # state_transition | parameter_add | boundary_add | etc.
      details: Dict
  
  # ─────────────────────────────────────────────────────────────
  # QUARANTINE INFO (if applicable)
  # ─────────────────────────────────────────────────────────────
  
  quarantine_reason: string | null
  quarantine_evidence: [EpisodeID]
  quarantine_date: datetime | null
  review_required: boolean
  
  # ─────────────────────────────────────────────────────────────
  # DEPRECATION INFO (if applicable)
  # ─────────────────────────────────────────────────────────────
  
  deprecation_reason: string | null
  superseded_by: SkillID | null
  deprecated_date: datetime | null
  
  # ─────────────────────────────────────────────────────────────
  # COMPOSITION INFO (if applicable)
  # ─────────────────────────────────────────────────────────────
  
  component_skills: [SkillID]     # For macro-skills
  composition_type: CompositionType | null  # sequence | parallel | conditional
  inter_skill_bindings:           # How outputs connect to inputs
    - from_skill: SkillID
      from_output: string
      to_skill: SkillID
      to_input: string
```

## Index Schema (Layer 3: Retrieval views)

Indices are **mutable, derived** views for fast retrieval.

```yaml
SkillIndex:
  # By situation signature (embedding similarity)
  situation_index:
    index_type: "vector"
    dimensions: integer
    entries:
      - skill_id: SkillID
        vector: [float]
        metadata:
          lifecycle_state: LifecycleState
          success_rate: float
  
  # By task type
  task_index:
    task_type:
      - skill_id: SkillID
        priority: integer         # Based on success rate
  
  # By tool
  tool_index:
    tool_id:
      - skill_id: SkillID
  
  # By lifecycle state
  state_index:
    lifecycle_state:
      - skill_id: SkillID
  
  # By success rate (for ranking)
  reliability_index:
    sorted_list:
      - skill_id: SkillID
        success_rate: float
```

## Lifecycle Event Schemas

```yaml
LifecycleEvent:
  event_id: UUID
  timestamp: datetime
  skill_id: SkillID
  event_type: string

SkillCreated:
  extends: LifecycleEvent
  source: SourceType

SkillPromoted:
  extends: LifecycleEvent
  from_state: LifecycleState
  to_state: LifecycleState
  evidence: [EpisodeID]

SkillGeneralized:
  extends: LifecycleEvent
  parameters_added: [string]
  invariants_discovered: [string]

SkillSplit:
  extends: LifecycleEvent
  new_skill_ids: [SkillID]
  split_reason: string

SkillsMerged:
  extends: LifecycleEvent
  merged_skill_id: SkillID
  canonical_skill_id: SkillID

MacroComposed:
  extends: LifecycleEvent
  component_skill_ids: [SkillID]

SkillQuarantined:
  extends: LifecycleEvent
  reason: string
  evidence: [EpisodeID]

SkillDeprecated:
  extends: LifecycleEvent
  reason: string
  superseded_by: SkillID | null
```

## Consolidation Report Schema

```yaml
ConsolidationReport:
  run_id: UUID
  started_at: datetime
  completed_at: datetime
  
  # Counts
  skills_scanned: integer
  episodes_processed: integer
  
  # Actions
  promotions:
    - skill_id: SkillID
      from: LifecycleState
      to: LifecycleState
      evidence: EpisodeID | null
      
  generalizations:
    - skill_id: SkillID
      parameters_added: [string]
      
  boundaries_learned:
    - skill_id: SkillID
      conditions_added: integer
      forbidden_added: integer
      
  splits:
    - original_skill_id: SkillID
      new_skill_ids: [SkillID]
      
  merges:
    - merged_skill_id: SkillID
      canonical_skill_id: SkillID
      overlap: float
      
  compositions:
    - macro_skill_id: SkillID
      component_skills: [SkillID]
      frequency: integer
      
  quarantines:
    - skill_id: SkillID
      reason: [string]
      
  deprecations:
    - skill_id: SkillID
      reason: string
      superseded_by: SkillID | null
  
  # Summary
  total_actions: integer
  errors: [string]
```

## Enums

```yaml
LifecycleState:
  - UNKNOWN: 0
  - CANDIDATE: 1
  - VALIDATED: 2
  - GENERALIZING: 3
  - OPERATIONAL: 4
  - REFINED: 5
  - COMPOSED: 6
  - QUARANTINED: 7
  - DEPRECATED: 8

SourceType:
  - teacher
  - web
  - exploration
  - transfer
  - split
  - merge
  - composition

CompositionType:
  - sequence
  - parallel
  - conditional

ConditionType:
  - required
  - forbidden
```
