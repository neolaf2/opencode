#!/usr/bin/env python3
"""
KSTAR Skill Analyzer

Evaluates KSTAR skills using the memorization→understanding framework,
2-D world model (structure × causality), abstraction depth hierarchy,
ability ladder, and structural plasticity assessment.

Skills are structures-in-motion, not static objects.
Learning updates relations more than contents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import IntEnum
import re


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS AND CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class AbstractionDepth(IntEnum):
    """The 4-level abstraction hierarchy."""
    NONE = 0                    # No abstraction
    INSTANCE = 1                # 2+2=4 (instance memory)
    PATTERN = 2                 # n+n=2n (pattern recognition)
    OPERATION = 3               # "+" has properties (operation abstraction)
    STRUCTURE = 4               # Groups, functors (structure generalization)


class AbilityLevel(IntEnum):
    """The 5-level ability ladder."""
    MEMORIZATION = 0            # Recall only
    UNDERSTANDING = 1           # Structural mapping
    APPLICATION = 2             # Contextual execution
    CREATION = 3                # Pattern modification
    META_CREATION = 4           # Pattern improvement, teaching


class Verdict(IntEnum):
    """Skill classification verdict."""
    ROTE = 0
    PROCEDURAL = 1
    STRUCTURAL = 2
    APPLICABLE = 3
    CREATIVE = 4
    META = 5


class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


ABSTRACTION_NAMES = {
    0: "None",
    1: "Instance Memory",
    2: "Pattern Recognition",
    3: "Operation Abstraction",
    4: "Structure Generalization"
}

ABILITY_NAMES = {
    0: "Memorization",
    1: "Understanding",
    2: "Application",
    3: "Creation",
    4: "Meta-Creation"
}

VERDICT_NAMES = {
    0: "ROTE",
    1: "PROCEDURAL",
    2: "STRUCTURAL",
    3: "APPLICABLE",
    4: "CREATIVE",
    5: "META"
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DimensionScores:
    """Scores for the 2-D world model dimensions."""
    structure: int = 0
    causality: int = 0
    integration: int = 0
    
    @property
    def overall(self) -> int:
        return (self.structure + self.causality + self.integration) // 3


@dataclass
class AbstractionAssessment:
    """Abstraction depth assessment."""
    depth_level: int
    depth_name: str
    has_concrete_instances: bool = False
    has_parameterized_pattern: bool = False
    discusses_operation_properties: bool = False
    has_structure_mapping: bool = False
    invariance_quality: int = 0
    what_varies: List[str] = field(default_factory=list)
    what_stays_same: List[str] = field(default_factory=list)


@dataclass
class AbilityAssessment:
    """Ability level assessment."""
    level: int
    name: str
    evidence: List[str] = field(default_factory=list)
    # Test results
    would_fail_symbol_change: bool = True
    would_fail_context_change: bool = True
    can_explain_why: bool = False
    can_map_instance_to_pattern: bool = False
    handles_noise: bool = False
    handles_constraints: bool = False
    has_modification_guidance: bool = False
    can_teach: bool = False
    can_compress: bool = False


@dataclass
class PlasticityOperation:
    """Single graph operation support."""
    name: str
    supported: bool
    evidence: Optional[str] = None


@dataclass
class PlasticityAssessment:
    """Structural plasticity assessment."""
    score: str  # "low" | "medium" | "high"
    enabled_count: int
    operations: Dict[str, PlasticityOperation] = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SkillFlags:
    """Boolean flags about skill characteristics."""
    is_rote: bool = False
    is_understanding: bool = False
    is_applicable: bool = False
    is_creative: bool = False
    is_teachable: bool = False
    separates_pattern_process: bool = False
    supports_restructuring: bool = False
    has_transfer_potential: bool = False


@dataclass
class Weakness:
    """Identified weakness."""
    dimension: str
    issue: str
    severity: Severity
    impact: str = ""


@dataclass
class Recommendation:
    """Improvement recommendation."""
    category: str  # "pattern", "understanding", "application", "creation", "plasticity"
    suggestion: str
    target: str
    priority: int
    expected_improvement: str = ""


@dataclass
class SkillDiagnosis:
    """Complete skill diagnosis."""
    skill_id: str
    skill_name: str
    analyzed_at: datetime
    
    # Scores
    dimensions: DimensionScores
    
    # Assessments
    abstraction: AbstractionAssessment
    ability: AbilityAssessment
    plasticity: PlasticityAssessment
    
    # Classification
    verdict: int
    verdict_name: str
    flags: SkillFlags
    
    # Issues and recommendations
    weaknesses: List[Weakness]
    recommendations: List[Recommendation]
    
    # Summary
    headline: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_all_text(skill: Dict) -> str:
    """Extract all textual content from skill for analysis."""
    texts = []
    
    def extract_recursive(obj, depth=0):
        if depth > 10:
            return
        if isinstance(obj, str):
            texts.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                extract_recursive(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item, depth + 1)
    
    extract_recursive(skill)
    return " ".join(texts)


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN/STRUCTURE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def has_explicit_pattern(skill: Dict) -> bool:
    """Check if skill has explicit pattern declaration."""
    text = extract_all_text(skill).lower()
    
    pattern_keywords = [
        "pattern", "structure", "model", "instance of", "case of",
        "general form", "abstraction", "underlying", "this is a",
        "same as", "type of", "kind of"
    ]
    
    if any(kw in text for kw in pattern_keywords):
        return True
    
    signature = skill.get("situation", {}).get("signature", {})
    if signature and (signature.get("pattern_type") or signature.get("pattern")):
        return True
    
    return False


def has_invariants(skill: Dict) -> bool:
    """Check if skill identifies invariants."""
    conditions = skill.get("situation", {}).get("applicability_conditions", [])
    if conditions:
        return True
    
    text = extract_all_text(skill).lower()
    invariant_keywords = [
        "invariant", "always", "regardless", "preserved",
        "stays the same", "independent of", "boundary", "constant",
        "never changes", "holds for all"
    ]
    
    return any(kw in text for kw in invariant_keywords)


def has_transfer_guidance(skill: Dict) -> bool:
    """Check if skill provides transfer guidance."""
    text = extract_all_text(skill).lower()
    
    transfer_keywords = [
        "also applies", "same pattern", "similar to", "analogous",
        "transfer", "other contexts", "can be used when",
        "generalizes to", "in other domains", "works for"
    ]
    
    return any(kw in text for kw in transfer_keywords)


def pattern_is_named(skill: Dict) -> bool:
    """Check if pattern has an explicit name."""
    text = extract_all_text(skill).lower()
    
    # Look for named patterns
    named_patterns = [
        "this is the", "called", "known as", "named",
        "pattern:", "structure:", "follows the"
    ]
    
    if any(np in text for np in named_patterns):
        return True
    
    signature = skill.get("situation", {}).get("signature", {})
    return bool(signature.get("name") or signature.get("pattern_name"))


# ═══════════════════════════════════════════════════════════════════════════════
# ABSTRACTION DEPTH DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def has_concrete_instances(skill: Dict) -> bool:
    """Check if skill has concrete examples."""
    text = extract_all_text(skill).lower()
    
    instance_indicators = [
        "example", "for instance", "such as", "like",
        "specifically", "consider", "suppose"
    ]
    
    return any(ind in text for ind in instance_indicators)


def has_parameterized_pattern(skill: Dict) -> bool:
    """Check if skill uses parameters (not just concrete values)."""
    text = extract_all_text(skill)
    
    # Look for variable notation
    if re.search(r'\b[xyz]\b|\bn\b|\bN\b|\[.*?\]|\{.*?\}', text):
        return True
    
    # Look for parameter language
    param_indicators = ["parameter", "variable", "any", "for all", "given"]
    text_lower = text.lower()
    
    return any(ind in text_lower for ind in param_indicators)


def discusses_operation_properties(skill: Dict) -> bool:
    """Check if skill discusses operation properties (not just applies them)."""
    text = extract_all_text(skill).lower()
    
    property_indicators = [
        "closure", "associative", "commutative", "identity",
        "inverse", "property", "axiom", "satisfies",
        "operation has", "operation is", "the operation"
    ]
    
    return any(ind in text for ind in property_indicators)


def has_structure_mapping(skill: Dict) -> bool:
    """Check if skill shows structure-preserving mappings to other domains."""
    text = extract_all_text(skill).lower()
    
    mapping_indicators = [
        "same structure", "isomorphic", "analogous structure",
        "structure-preserving", "functor", "morphism",
        "behaves similarly", "same axioms", "same pattern in"
    ]
    
    return any(ind in text for ind in mapping_indicators)


def measure_abstraction_depth(skill: Dict) -> Tuple[int, str, AbstractionAssessment]:
    """Measure abstraction depth level (0-4)."""
    has_inst = has_concrete_instances(skill)
    has_param = has_parameterized_pattern(skill)
    has_ops = discusses_operation_properties(skill)
    has_struct = has_structure_mapping(skill)
    
    # Determine level
    if has_struct:
        level = 4
    elif has_ops:
        level = 3
    elif has_param:
        level = 2
    elif has_inst:
        level = 1
    else:
        level = 0
    
    assessment = AbstractionAssessment(
        depth_level=level,
        depth_name=ABSTRACTION_NAMES[level],
        has_concrete_instances=has_inst,
        has_parameterized_pattern=has_param,
        discusses_operation_properties=has_ops,
        has_structure_mapping=has_struct,
        invariance_quality=level * 25  # Simple heuristic
    )
    
    return level, ABSTRACTION_NAMES[level], assessment


# ═══════════════════════════════════════════════════════════════════════════════
# CAUSALITY/PROCESS DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def has_reasoning(skill: Dict) -> bool:
    """Check if skill provides reasoning."""
    reasoning = skill.get("action", {}).get("reasoning", "")
    if reasoning and len(reasoning) > 50:
        return True
    
    text = extract_all_text(skill).lower()
    reasoning_indicators = ["because", "therefore", "since", "thus", "so that", "reason"]
    
    return any(ind in text for ind in reasoning_indicators)


def reasoning_depth(skill: Dict) -> str:
    """Determine reasoning depth: none, shallow, medium, deep."""
    reasoning = skill.get("action", {}).get("reasoning", "") or ""
    text = (reasoning + " " + extract_all_text(skill)).lower()
    
    if not reasoning and "because" not in text:
        return "none"
    
    pattern_refs = ["pattern", "structure", "property", "invariant"]
    has_pattern = any(ref in text for ref in pattern_refs)
    
    causal_words = ["because", "therefore", "since", "thus"]
    has_causal = any(word in text for word in causal_words)
    
    if has_pattern and has_causal:
        return "deep"
    elif has_causal:
        return "medium"
    elif len(reasoning) > 20:
        return "shallow"
    return "none"


def has_feedback_loops(skill: Dict) -> bool:
    """Check if skill has feedback loops."""
    steps = skill.get("action", {}).get("plan", [])
    
    has_checkpoints = any(step.get("has_checkpoint") for step in steps)
    has_expected = any(step.get("expected_result") for step in steps)
    has_errors = any(step.get("common_mistakes") for step in steps)
    
    return has_checkpoints or (has_expected and has_errors)


def has_adaptation_guidance(skill: Dict) -> bool:
    """Check if skill provides adaptation guidance."""
    text = extract_all_text(skill).lower()
    
    adaptation_words = ["adjust", "depending", "if", "vary", "adapt",
                        "modify", "when", "unless", "alternatively"]
    
    return any(word in text for word in adaptation_words)


def all_steps_rigid(skill: Dict) -> bool:
    """Check if all steps are rigid (no flexibility)."""
    steps = skill.get("action", {}).get("plan", [])
    if not steps:
        return True
    
    rigid_words = ["always", "exactly", "must", "never", "precisely"]
    flexible_words = ["if", "depending", "adjust", "vary", "optionally", "when"]
    
    rigid_count = 0
    for step in steps:
        desc = step.get("description", "").lower()
        if any(w in desc for w in rigid_words):
            rigid_count += 1
        elif any(w in desc for w in flexible_words):
            rigid_count -= 1
    
    return rigid_count >= len(steps) // 2


# ═══════════════════════════════════════════════════════════════════════════════
# ABILITY LEVEL DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def has_pattern_modification(skill: Dict) -> bool:
    """Check if skill teaches pattern modification."""
    text = extract_all_text(skill).lower()
    
    mod_keywords = ["extend", "modify", "variant", "combine",
                    "create your own", "innovate", "what if",
                    "could be changed", "adapt the pattern"]
    
    return any(kw in text for kw in mod_keywords)


def has_combination_guidance(skill: Dict) -> bool:
    """Check if skill shows how to combine with other patterns."""
    text = extract_all_text(skill).lower()
    
    combo_keywords = ["combine with", "together with", "along with",
                      "complementary", "works with", "pair with"]
    
    return any(kw in text for kw in combo_keywords)


def can_teach_pattern(skill: Dict) -> bool:
    """Check if skill can be used to teach others."""
    text = extract_all_text(skill).lower()
    
    teach_keywords = ["teach", "explain to others", "help others learn",
                      "show someone", "demonstrate to"]
    
    if any(kw in text for kw in teach_keywords):
        return True
    
    # Check for teaching scaffolds
    return bool(skill.get("assessment", {}).get("self_check_questions"))


def can_compress_to_reusable(skill: Dict) -> bool:
    """Check if skill teaches compression to reusable form."""
    text = extract_all_text(skill).lower()
    
    compress_keywords = ["summarize", "key insight", "essential",
                         "core principle", "remember as", "mnemonic",
                         "in short", "the gist"]
    
    return any(kw in text for kw in compress_keywords)


def determine_ability_level(skill: Dict, scores: DimensionScores) -> Tuple[int, str, AbilityAssessment]:
    """Determine ability level (0-4)."""
    # Collect evidence
    has_pattern = has_explicit_pattern(skill)
    has_reason = has_reasoning(skill)
    has_adapt = has_adaptation_guidance(skill)
    has_mod = has_pattern_modification(skill)
    has_combo = has_combination_guidance(skill)
    can_teach = can_teach_pattern(skill)
    can_compress = can_compress_to_reusable(skill)
    rigid = all_steps_rigid(skill)
    
    assessment = AbilityAssessment(
        level=0,
        name="Memorization",
        would_fail_symbol_change=not has_pattern,
        would_fail_context_change=rigid,
        can_explain_why=has_reason,
        can_map_instance_to_pattern=has_pattern,
        handles_noise=has_adapt,
        handles_constraints=has_adapt,
        has_modification_guidance=has_mod,
        can_teach=can_teach,
        can_compress=can_compress
    )
    
    # L4: Meta-Creation
    if scores.overall >= 80 and can_teach and can_compress:
        assessment.level = 4
        assessment.name = "Meta-Creation"
        assessment.evidence = ["Can teach pattern", "Can compress to reusable form"]
        return 4, "Meta-Creation", assessment
    
    # L3: Creation
    if scores.overall >= 65 and has_mod and has_combo:
        assessment.level = 3
        assessment.name = "Creation"
        assessment.evidence = ["Has pattern modification guidance", "Has combination guidance"]
        return 3, "Creation", assessment
    
    # L2: Application
    if scores.causality >= 60 and has_adapt and not rigid:
        assessment.level = 2
        assessment.name = "Application"
        assessment.evidence = ["Handles adaptation", "Not rigid"]
        return 2, "Application", assessment
    
    # L1: Understanding
    if scores.structure >= 50 and has_pattern and has_reason:
        assessment.level = 1
        assessment.name = "Understanding"
        assessment.evidence = ["Has explicit pattern", "Has reasoning"]
        return 1, "Understanding", assessment
    
    # L0: Memorization
    assessment.evidence = ["Falls below understanding threshold"]
    return 0, "Memorization", assessment


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURAL PLASTICITY DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def check_attach_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports ATTACH operation."""
    text = extract_all_text(skill).lower()
    indicators = ["applies to", "can be used for", "works with", "fits"]
    
    if any(ind in text for ind in indicators):
        return True, "Has 'applies to' language"
    return False, ""


def check_merge_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports MERGE operation."""
    text = extract_all_text(skill).lower()
    indicators = ["similar to", "related to", "same as", "shares structure with"]
    
    if any(ind in text for ind in indicators):
        return True, "Identifies related patterns"
    return False, ""


def check_split_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports SPLIT operation (has boundary conditions)."""
    text = extract_all_text(skill).lower()
    indicators = ["doesn't apply when", "except when", "not valid for",
                  "boundary", "limit", "breaks when", "fails when"]
    
    if any(ind in text for ind in indicators):
        return True, "Has boundary conditions"
    
    if skill.get("situation", {}).get("applicability_conditions"):
        return True, "Has applicability conditions"
    
    return False, ""


def check_lift_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports LIFT operation (generalization hints)."""
    text = extract_all_text(skill).lower()
    indicators = ["generalizes to", "more general", "abstract version",
                  "can be extended", "broader pattern"]
    
    if any(ind in text for ind in indicators):
        return True, "Has generalization hints"
    return False, ""


def check_ground_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports GROUND operation (concrete anchors)."""
    if has_concrete_instances(skill):
        return True, "Has concrete examples"
    return False, ""


def check_prune_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports PRUNE operation (obsolescence criteria)."""
    text = extract_all_text(skill).lower()
    indicators = ["superseded by", "deprecated", "obsolete when",
                  "replaced by", "no longer valid"]
    
    if any(ind in text for ind in indicators):
        return True, "Has obsolescence criteria"
    return False, ""


def check_reweight_support(skill: Dict) -> Tuple[bool, str]:
    """Check if skill supports REWEIGHT operation (confidence signals)."""
    text = extract_all_text(skill).lower()
    indicators = ["confidence", "certainty", "more sure when", "less sure when",
                  "reliability", "trust"]
    
    if any(ind in text for ind in indicators):
        return True, "Has confidence signals"
    return False, ""


def evaluate_plasticity(skill: Dict) -> PlasticityAssessment:
    """Evaluate structural plasticity."""
    operations = {}
    
    # Check each operation
    checks = [
        ("attach", check_attach_support),
        ("merge", check_merge_support),
        ("split", check_split_support),
        ("lift", check_lift_support),
        ("ground", check_ground_support),
        ("prune", check_prune_support),
        ("reweight", check_reweight_support)
    ]
    
    for name, check_fn in checks:
        supported, evidence = check_fn(skill)
        operations[name] = PlasticityOperation(
            name=name,
            supported=supported,
            evidence=evidence if supported else None
        )
    
    enabled_count = sum(1 for op in operations.values() if op.supported)
    missing = [name for name, op in operations.items() if not op.supported]
    
    if enabled_count >= 5:
        score = "high"
    elif enabled_count >= 3:
        score = "medium"
    else:
        score = "low"
    
    recommendations = []
    if "split" not in [n for n, op in operations.items() if op.supported]:
        recommendations.append("Add boundary conditions to enable SPLIT")
    if "lift" not in [n for n, op in operations.items() if op.supported]:
        recommendations.append("Add generalization hints to enable LIFT")
    if "merge" not in [n for n, op in operations.items() if op.supported]:
        recommendations.append("Identify similar patterns to enable MERGE")
    
    return PlasticityAssessment(
        score=score,
        enabled_count=enabled_count,
        operations=operations,
        missing=missing,
        recommendations=recommendations
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def score_structure(skill: Dict) -> int:
    """Score structure dimension (0-100)."""
    score = 0
    
    # Pattern explicitness (0-25)
    if has_explicit_pattern(skill):
        score += 15
        if pattern_is_named(skill):
            score += 10
    
    # Invariant identification (0-25)
    if has_invariants(skill):
        score += 15
        conditions = skill.get("situation", {}).get("applicability_conditions", [])
        score += min(len(conditions) * 5, 10)
    
    # Abstraction level (0-25)
    depth, _, _ = measure_abstraction_depth(skill)
    score += depth * 6  # 0, 6, 12, 18, 24
    
    # Transfer potential (0-25)
    if has_transfer_guidance(skill):
        score += 15
        if has_structure_mapping(skill):
            score += 10
    
    return min(score, 100)


def score_causality(skill: Dict) -> int:
    """Score causality dimension (0-100)."""
    score = 0
    steps = skill.get("action", {}).get("plan", [])
    
    # Action completeness (0-25)
    if steps:
        score += 5
        if all(s.get("description") for s in steps):
            score += 5
        if all(s.get("expected_result") for s in steps):
            score += 10
        if len(steps) >= 3:
            score += 5
    
    # Feedback integration (0-25)
    if has_feedback_loops(skill):
        score += 15
        checkpoint_count = sum(1 for s in steps if s.get("has_checkpoint"))
        score += min(checkpoint_count * 5, 10)
    
    # Error handling (0-25)
    mistake_count = sum(len(s.get("common_mistakes", [])) for s in steps)
    score += min(mistake_count * 5, 15)
    if skill.get("action", {}).get("where_students_struggle"):
        score += 10
    
    # Adaptation guidance (0-25)
    if has_adaptation_guidance(skill):
        score += 15
        if not all_steps_rigid(skill):
            score += 10
    
    return min(score, 100)


def score_integration(skill: Dict) -> int:
    """Score integration dimension (0-100)."""
    score = 0
    
    # Pattern-causality linkage (0-35)
    reasoning = skill.get("action", {}).get("reasoning", "")
    if reasoning:
        score += 15
        if has_explicit_pattern(skill) and "pattern" in reasoning.lower():
            score += 20
    
    # Reasoning transparency (0-35)
    depth = reasoning_depth(skill)
    depth_scores = {"none": 0, "shallow": 10, "medium": 22, "deep": 35}
    score += depth_scores.get(depth, 0)
    
    # Scaffolding for understanding (0-30)
    steps = skill.get("action", {}).get("plan", [])
    scaffolded = sum(1 for s in steps if s.get("scaffolding_hints"))
    if steps and scaffolded > 0:
        score += int((scaffolded / len(steps)) * 30)
    
    return min(score, 100)


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def is_rote(skill: Dict, scores: DimensionScores) -> bool:
    """Determine if skill is pure rote memorization."""
    checks = [
        scores.structure < 30,
        not has_explicit_pattern(skill),
        not has_invariants(skill),
        not has_reasoning(skill),
        scores.integration < 25,
        all_steps_rigid(skill)
    ]
    return sum(checks) >= 3


def determine_verdict(skill: Dict, scores: DimensionScores, ability: int) -> Tuple[int, str]:
    """Determine overall verdict."""
    if is_rote(skill, scores):
        return 0, "ROTE"
    
    if ability >= 4:
        return 5, "META"
    if ability >= 3:
        return 4, "CREATIVE"
    if ability >= 2:
        return 3, "APPLICABLE"
    if scores.structure >= 50:
        return 2, "STRUCTURAL"
    if scores.causality >= 40:
        return 1, "PROCEDURAL"
    
    return 0, "ROTE"


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_weaknesses(skill: Dict, scores: DimensionScores) -> List[Weakness]:
    """Identify weaknesses."""
    weaknesses = []
    
    if scores.structure < 40:
        if not has_explicit_pattern(skill):
            weaknesses.append(Weakness(
                dimension="structure",
                issue="No explicit pattern declaration",
                severity=Severity.HIGH,
                impact="Cannot transfer to new contexts"
            ))
        if not has_invariants(skill):
            weaknesses.append(Weakness(
                dimension="structure",
                issue="No invariants identified",
                severity=Severity.MEDIUM,
                impact="Cannot distinguish essential from accidental"
            ))
    
    if scores.causality < 40:
        if not has_feedback_loops(skill):
            weaknesses.append(Weakness(
                dimension="causality",
                issue="No feedback loops",
                severity=Severity.HIGH,
                impact="Cannot detect or recover from errors"
            ))
        if all_steps_rigid(skill):
            weaknesses.append(Weakness(
                dimension="causality",
                issue="All steps are rigid",
                severity=Severity.MEDIUM,
                impact="Cannot adapt to variations"
            ))
    
    if scores.integration < 40:
        if not has_reasoning(skill):
            weaknesses.append(Weakness(
                dimension="integration",
                issue="No reasoning connecting pattern to action",
                severity=Severity.HIGH,
                impact="Learner cannot understand WHY"
            ))
    
    return weaknesses


def generate_recommendations(
    skill: Dict,
    scores: DimensionScores,
    abstraction: AbstractionAssessment,
    plasticity: PlasticityAssessment
) -> List[Recommendation]:
    """Generate improvement recommendations."""
    recs = []
    priority = 1
    
    # Pattern recommendations
    if not has_explicit_pattern(skill):
        recs.append(Recommendation(
            category="pattern",
            suggestion="Add explicit pattern declaration: 'This is an instance of [X]'",
            target="situation.signature",
            priority=priority,
            expected_improvement="Enables structural mapping and transfer"
        ))
        priority += 1
    
    if not has_invariants(skill):
        recs.append(Recommendation(
            category="pattern",
            suggestion="Identify invariants: 'What stays the same across contexts?'",
            target="situation.applicability_conditions",
            priority=priority,
            expected_improvement="Enables correct transfer"
        ))
        priority += 1
    
    # Understanding recommendations
    if not has_reasoning(skill):
        recs.append(Recommendation(
            category="understanding",
            suggestion="Add reasoning explaining WHY each step works",
            target="action.reasoning",
            priority=priority,
            expected_improvement="Moves from memorization to understanding"
        ))
        priority += 1
    
    # Application recommendations
    if not has_adaptation_guidance(skill):
        recs.append(Recommendation(
            category="application",
            suggestion="Add adaptation guidance for context variations",
            target="action.plan",
            priority=priority,
            expected_improvement="Enables real-world application"
        ))
        priority += 1
    
    # Plasticity recommendations
    for rec in plasticity.recommendations[:2]:
        recs.append(Recommendation(
            category="plasticity",
            suggestion=rec,
            target="various",
            priority=priority,
            expected_improvement="Enables skill restructuring"
        ))
        priority += 1
    
    return recs


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_skill(skill: Dict) -> SkillDiagnosis:
    """Perform complete skill analysis."""
    # Score dimensions
    scores = DimensionScores(
        structure=score_structure(skill),
        causality=score_causality(skill),
        integration=score_integration(skill)
    )
    
    # Measure abstraction depth
    abs_level, abs_name, abstraction = measure_abstraction_depth(skill)
    
    # Determine ability level
    ability_level, ability_name, ability = determine_ability_level(skill, scores)
    
    # Evaluate plasticity
    plasticity = evaluate_plasticity(skill)
    
    # Determine verdict
    verdict, verdict_name = determine_verdict(skill, scores, ability_level)
    
    # Build flags
    flags = SkillFlags(
        is_rote=is_rote(skill, scores),
        is_understanding=ability_level >= 1,
        is_applicable=ability_level >= 2,
        is_creative=ability_level >= 3,
        is_teachable=ability_level >= 4,
        separates_pattern_process=has_explicit_pattern(skill) and len(skill.get("action", {}).get("plan", [])) > 0,
        supports_restructuring=plasticity.score in ["medium", "high"],
        has_transfer_potential=has_transfer_guidance(skill)
    )
    
    # Generate weaknesses and recommendations
    weaknesses = generate_weaknesses(skill, scores)
    recommendations = generate_recommendations(skill, scores, abstraction, plasticity)
    
    # Generate headline
    headline = f"{verdict_name}: {ability_name} level skill with {abs_name} abstraction depth"
    if flags.is_rote:
        headline = "ROTE: Pure memorization - needs pattern and reasoning"
    
    return SkillDiagnosis(
        skill_id=skill.get("id", "unknown"),
        skill_name=skill.get("name", "Unknown Skill"),
        analyzed_at=datetime.now(),
        dimensions=scores,
        abstraction=abstraction,
        ability=ability,
        plasticity=plasticity,
        verdict=verdict,
        verdict_name=verdict_name,
        flags=flags,
        weaknesses=weaknesses,
        recommendations=recommendations,
        headline=headline
    )


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(diagnosis: SkillDiagnosis) -> str:
    """Generate human-readable report."""
    lines = [
        "═" * 70,
        "KSTAR SKILL ANALYSIS REPORT",
        "═" * 70,
        f"Skill: {diagnosis.skill_name}",
        f"ID: {diagnosis.skill_id}",
        f"Analyzed: {diagnosis.analyzed_at.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"VERDICT: {diagnosis.verdict_name}",
        f"  {diagnosis.headline}",
        "",
        "─" * 70,
        "2-D WORLD MODEL SCORES",
        "─" * 70,
        f"  Structure:   {diagnosis.dimensions.structure:3d}  {'█' * (diagnosis.dimensions.structure // 5)}",
        f"  Causality:   {diagnosis.dimensions.causality:3d}  {'█' * (diagnosis.dimensions.causality // 5)}",
        f"  Integration: {diagnosis.dimensions.integration:3d}  {'█' * (diagnosis.dimensions.integration // 5)}",
        f"  Overall:     {diagnosis.dimensions.overall:3d}  {'█' * (diagnosis.dimensions.overall // 5)}",
        "",
        "─" * 70,
        "ABSTRACTION DEPTH",
        "─" * 70,
        f"  Level: {diagnosis.abstraction.depth_level} - {diagnosis.abstraction.depth_name}",
        f"  Has Concrete Instances: {diagnosis.abstraction.has_concrete_instances}",
        f"  Has Parameterized Pattern: {diagnosis.abstraction.has_parameterized_pattern}",
        f"  Discusses Operation Properties: {diagnosis.abstraction.discusses_operation_properties}",
        f"  Has Structure Mapping: {diagnosis.abstraction.has_structure_mapping}",
        "",
        "─" * 70,
        "ABILITY LEVEL",
        "─" * 70,
        f"  Level: {diagnosis.ability.level} - {diagnosis.ability.name}",
        f"  Evidence: {', '.join(diagnosis.ability.evidence)}",
        "",
        "─" * 70,
        "STRUCTURAL PLASTICITY",
        "─" * 70,
        f"  Score: {diagnosis.plasticity.score} ({diagnosis.plasticity.enabled_count}/7 operations)",
    ]
    
    for name, op in diagnosis.plasticity.operations.items():
        icon = "✓" if op.supported else "✗"
        lines.append(f"    {icon} {name.upper()}: {op.evidence or 'Not supported'}")
    
    lines.extend([
        "",
        "─" * 70,
        "FLAGS",
        "─" * 70,
    ])
    
    flag_map = {
        "Is Rote (BAD)": diagnosis.flags.is_rote,
        "Is Understanding": diagnosis.flags.is_understanding,
        "Is Applicable": diagnosis.flags.is_applicable,
        "Is Creative": diagnosis.flags.is_creative,
        "Is Teachable": diagnosis.flags.is_teachable,
        "Separates Pattern/Process": diagnosis.flags.separates_pattern_process,
        "Supports Restructuring": diagnosis.flags.supports_restructuring,
        "Has Transfer Potential": diagnosis.flags.has_transfer_potential,
    }
    
    for name, value in flag_map.items():
        icon = "✓" if value else "✗"
        if "BAD" in name:
            icon = "✗" if value else "✓"
        lines.append(f"    {icon} {name}")
    
    if diagnosis.weaknesses:
        lines.extend([
            "",
            "─" * 70,
            "WEAKNESSES",
            "─" * 70,
        ])
        for w in diagnosis.weaknesses:
            severity_icon = {1: "🟢", 2: "🟡", 3: "🔴"}[w.severity]
            lines.append(f"  {severity_icon} [{w.dimension}] {w.issue}")
            if w.impact:
                lines.append(f"      Impact: {w.impact}")
    
    if diagnosis.recommendations:
        lines.extend([
            "",
            "─" * 70,
            "RECOMMENDATIONS (prioritized)",
            "─" * 70,
        ])
        for r in diagnosis.recommendations:
            lines.append(f"  [{r.priority}] {r.suggestion}")
            lines.append(f"      Target: {r.target}")
            if r.expected_improvement:
                lines.append(f"      Expected: {r.expected_improvement}")
    
    lines.extend([
        "",
        "═" * 70,
    ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("KSTAR Skill Analyzer")
    print("=" * 40)
    print()
    print("Usage:")
    print("  from analyzer import analyze_skill, generate_report")
    print("  diagnosis = analyze_skill(skill_dict)")
    print("  print(generate_report(diagnosis))")
