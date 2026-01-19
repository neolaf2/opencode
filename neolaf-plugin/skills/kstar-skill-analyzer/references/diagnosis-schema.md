# Diagnosis Schema

Complete schema for skill analysis output.

## Primary Diagnosis Structure

```yaml
SkillDiagnosis:
  # Identity
  skill_id: string
  skill_name: string
  skill_version: string (optional)
  analyzed_at: datetime (ISO 8601)
  analyzer_version: string
  
  # ═══════════════════════════════════════════════════════════════════════
  # 2-D WORLD MODEL ASSESSMENT
  # ═══════════════════════════════════════════════════════════════════════
  
  dimensions:
    structure:
      score: 0-100
      subscores:
        pattern_explicitness: 0-25      # Is pattern declared?
        invariant_identification: 0-25   # Are invariants named?
        abstraction_level: 0-25          # How abstract?
        transfer_potential: 0-25         # Can it transfer?
      evidence: [string]                 # Specific findings
      
    causality:
      score: 0-100
      subscores:
        action_completeness: 0-25        # All steps present?
        feedback_integration: 0-25       # Closed loops?
        error_handling: 0-25             # Handles failure?
        adaptation_guidance: 0-25        # Handles variation?
      evidence: [string]
      
    integration:
      score: 0-100
      subscores:
        pattern_causality_linkage: 0-35  # Connected?
        reasoning_transparency: 0-35     # Explains why?
        scaffolding_for_understanding: 0-30  # Teaches pattern?
      evidence: [string]
    
    overall_score: 0-100  # Average of three dimensions
  
  # ═══════════════════════════════════════════════════════════════════════
  # ABSTRACTION DEPTH ASSESSMENT
  # ═══════════════════════════════════════════════════════════════════════
  
  abstraction:
    depth_level: 0-4
    depth_name: enum
      - "None"                  # Level 0
      - "Instance Memory"       # Level 1: 2+2=4
      - "Pattern Recognition"   # Level 2: n+n=2n
      - "Operation Abstraction" # Level 3: "+" has properties
      - "Structure Generalization" # Level 4: Groups, functors
    
    evidence:
      has_concrete_instances: boolean
      has_parameterized_pattern: boolean
      discusses_operation_properties: boolean
      has_structure_mapping: boolean
      
    invariance_quality: 0-100  # How well are invariants specified?
    
    what_varies: [string]      # What can change
    what_stays_same: [string]  # What is invariant
  
  # ═══════════════════════════════════════════════════════════════════════
  # ABILITY LEVEL ASSESSMENT
  # ═══════════════════════════════════════════════════════════════════════
  
  ability:
    level: 0-4
    name: enum
      - "Memorization"    # L0: Recall only
      - "Understanding"   # L1: Structural mapping
      - "Application"     # L2: Contextual execution
      - "Creation"        # L3: Pattern modification
      - "Meta-Creation"   # L4: Pattern improvement, teaching
    
    evidence: [string]    # What supports this classification
    
    level_tests:
      memorization_test:
        would_fail_on_symbol_change: boolean
        would_fail_on_context_change: boolean
      understanding_test:
        can_explain_why: boolean
        can_map_instance_to_pattern: boolean
      application_test:
        handles_noise: boolean
        handles_constraints: boolean
        adapts_to_incomplete_info: boolean
      creation_test:
        has_modification_guidance: boolean
        has_combination_hints: boolean
        identifies_pattern_boundaries: boolean
      meta_creation_test:
        can_teach_pattern: boolean
        can_formalize_for_transfer: boolean
        can_compress_to_reusable: boolean
  
  # ═══════════════════════════════════════════════════════════════════════
  # STRUCTURAL PLASTICITY ASSESSMENT
  # ═══════════════════════════════════════════════════════════════════════
  
  plasticity:
    score: enum ["low", "medium", "high"]
    enabled_count: 0-7  # How many graph ops supported
    
    operations:
      attach:
        supported: boolean
        evidence: string (optional)
        # Can new instances be linked to the pattern?
        
      merge:
        supported: boolean
        evidence: string (optional)
        # Does it identify merge candidates with other patterns?
        
      split:
        supported: boolean
        evidence: string (optional)
        # Are boundary conditions specified for when pattern breaks?
        
      lift:
        supported: boolean
        evidence: string (optional)
        # Does it hint at higher generalizations?
        
      ground:
        supported: boolean
        evidence: string (optional)
        # Are there concrete anchors to prevent abstraction drift?
        
      prune:
        supported: boolean
        evidence: string (optional)
        # Does it identify when skill becomes obsolete?
        
      reweight:
        supported: boolean
        evidence: string (optional)
        # Does it have confidence signals that can be updated?
    
    missing_operations: [string]
    recommendations_for_plasticity: [string]
  
  # ═══════════════════════════════════════════════════════════════════════
  # CLASSIFICATION FLAGS
  # ═══════════════════════════════════════════════════════════════════════
  
  flags:
    # Memorization vs Understanding
    is_rote: boolean               # Pure memorization (A→B)
    is_understanding: boolean      # Has structural mapping
    
    # Pattern-Process Separation
    separates_pattern_process: boolean
    pattern_is_explicit: boolean
    process_is_complete: boolean
    
    # Capability Flags
    is_applicable: boolean         # Handles context variation
    is_creative: boolean           # Enables pattern modification
    is_teachable: boolean          # Can transfer to others
    
    # Structural Health
    supports_restructuring: boolean
    has_transfer_potential: boolean
    avoids_context_fragility: boolean
  
  # ═══════════════════════════════════════════════════════════════════════
  # WEAKNESSES
  # ═══════════════════════════════════════════════════════════════════════
  
  weaknesses:
    - dimension: enum ["structure", "causality", "integration", "abstraction", "plasticity"]
      issue: string
      severity: enum ["low", "medium", "high"]
      impact: string  # What capability is lost
      
  # ═══════════════════════════════════════════════════════════════════════
  # RECOMMENDATIONS
  # ═══════════════════════════════════════════════════════════════════════
  
  recommendations:
    # By target capability
    to_add_pattern:
      - suggestion: string
        target: string (field path)
        priority: 1-5
        expected_improvement: string
        
    to_add_understanding:
      - suggestion: string
        target: string
        priority: 1-5
        expected_improvement: string
        
    to_add_application:
      - suggestion: string
        target: string
        priority: 1-5
        expected_improvement: string
        
    to_add_creation:
      - suggestion: string
        target: string
        priority: 1-5
        expected_improvement: string
        
    to_add_plasticity:
      - suggestion: string
        target: string
        priority: 1-5
        expected_improvement: string
    
    # Prioritized list
    priority_order: [string]  # Most important first
```

## Summary Report Structure

```yaml
SkillSummaryReport:
  skill_name: string
  
  verdict: enum
    - "ROTE"            # Pure memorization, needs restructuring
    - "PROCEDURAL"      # Has process but no pattern
    - "STRUCTURAL"      # Has pattern, basic understanding
    - "APPLICABLE"      # Can handle variation
    - "CREATIVE"        # Enables modification
    - "META"            # Teachable, compressible
  
  headline: string      # One-line summary
  
  scores:
    structure: 0-100
    causality: 0-100
    integration: 0-100
    overall: 0-100
  
  ability_level: string  # e.g., "L2: Application"
  abstraction_depth: string  # e.g., "L3: Operation Abstraction"
  plasticity: string  # "low" | "medium" | "high"
  
  top_strengths: [string]  # Max 3
  top_weaknesses: [string]  # Max 3
  top_recommendations: [string]  # Max 3, prioritized
```

## Library Analysis Structure

```yaml
LibraryAnalysis:
  library_id: string
  analyzed_at: datetime
  total_skills: integer
  
  # Distribution by verdict
  verdict_distribution:
    ROTE: integer
    PROCEDURAL: integer
    STRUCTURAL: integer
    APPLICABLE: integer
    CREATIVE: integer
    META: integer
  
  # Average scores
  avg_scores:
    structure: float
    causality: float
    integration: float
    overall: float
  
  # Average levels
  avg_ability_level: float
  avg_abstraction_depth: float
  
  # Plasticity distribution
  plasticity_distribution:
    low: integer
    medium: integer
    high: integer
  
  # Problem areas
  rote_percentage: float
  skills_lacking_pattern: integer
  skills_lacking_feedback: integer
  skills_lacking_transfer: integer
  
  # Common issues
  common_weaknesses:
    - issue: string
      count: integer
      percentage: float
      
  # Aggregate recommendations
  library_recommendations:
    - recommendation: string
      affected_skills: integer
      priority: 1-5
```

## Comparison Structure

```yaml
SkillComparison:
  skill_a_id: string
  skill_b_id: string
  compared_at: datetime
  
  # Score deltas
  score_deltas:
    structure: integer  # B - A
    causality: integer
    integration: integer
    overall: integer
  
  # Level changes
  ability_level_change: integer  # +/- levels
  abstraction_depth_change: integer
  plasticity_change: string  # e.g., "low → medium"
  
  # Specific changes
  improvements: [string]  # What got better
  regressions: [string]   # What got worse
  unchanged: [string]     # What stayed same
  
  # Verdict
  overall_direction: enum ["improved", "regressed", "mixed", "unchanged"]
```
