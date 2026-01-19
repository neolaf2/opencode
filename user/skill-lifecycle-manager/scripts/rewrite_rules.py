#!/usr/bin/env python3
"""
Memory Rewrite Rules

Implements the skill compilation rules that transform raw K-STAR episodes
into executable, generalizable skill objects.

Rules:
  S1: PROMOTE - Candidate → Validated on first success
  S2: GENERALIZE - Parameterize from multiple episodes
  S3: LEARN_BOUNDARIES - Discover applicability conditions
  S4: SPLIT - Divide bimodal skills
  S5: MERGE - Unify duplicates
  S6: COMPOSE - Create macro-skills from sequences
  S7: QUARANTINE - Isolate failing skills
  S8: DEPRECATE - Archive superseded skills
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import logging

from lifecycle_manager import (
    SkillLifecycleManager, Skill, Episode, Parameter, Condition,
    PlanTemplate, PlanStep, LifecycleState, STATE_NAMES,
    SkillGeneralized, SkillSplit, SkillsMerged, MacroComposed
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S1: PROMOTE (Candidate → Validated)
# ═══════════════════════════════════════════════════════════════════════════════

def rule_promote(manager: SkillLifecycleManager, skill: Skill, episode: Episode) -> bool:
    """
    Rule S1: Promote candidate to validated on first success.
    
    Trigger: An episode succeeds and matches a candidate skill.
    
    Rewrite:
    - Increment success count
    - Attach episode as evidence
    - Promote to Validated state
    """
    if skill.lifecycle_state != LifecycleState.CANDIDATE:
        return False
    
    if not episode.success:
        return False
    
    if episode.skill_id != skill.skill_id:
        return False
    
    # Record the evidence
    skill.created_from_episodes.append(episode.episode_id)
    
    # Promote
    success = manager.promote_to_validated(skill, episode)
    
    if success:
        logger.info(f"PROMOTE: {skill.name} → Validated (episode: {episode.episode_id})")
    
    return success


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S2: GENERALIZE by Parameterization
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SubstitutableDifference:
    """A difference between episodes that can become a parameter."""
    location: str  # Path in the plan/situation
    values: List[Any]
    inferred_name: str
    inferred_type: str


def find_substitutable_differences(episodes: List[Episode]) -> List[SubstitutableDifference]:
    """
    Find elements that differ between episodes but could be parameters.
    """
    if len(episodes) < 2:
        return []
    
    differences = []
    
    # Compare situations
    base_situation = episodes[0].situation
    for key in base_situation:
        values = [e.situation.get(key) for e in episodes]
        if len(set(str(v) for v in values)) > 1:
            # This key varies
            differences.append(SubstitutableDifference(
                location=f"situation.{key}",
                values=values,
                inferred_name=key,
                inferred_type=_infer_type(values)
            ))
    
    # Compare task goals
    base_task = episodes[0].task
    for key in base_task:
        values = [e.task.get(key) for e in episodes]
        if len(set(str(v) for v in values)) > 1:
            differences.append(SubstitutableDifference(
                location=f"task.{key}",
                values=values,
                inferred_name=key,
                inferred_type=_infer_type(values)
            ))
    
    # Compare plan steps
    if all(e.plan for e in episodes):
        for step_idx in range(len(episodes[0].plan)):
            for key in episodes[0].plan[step_idx]:
                try:
                    values = [e.plan[step_idx].get(key) for e in episodes]
                    if len(set(str(v) for v in values)) > 1:
                        differences.append(SubstitutableDifference(
                            location=f"plan[{step_idx}].{key}",
                            values=values,
                            inferred_name=f"step_{step_idx}_{key}",
                            inferred_type=_infer_type(values)
                        ))
                except (IndexError, KeyError):
                    pass
    
    return differences


def _infer_type(values: List[Any]) -> str:
    """Infer the type from a list of values."""
    types = set(type(v).__name__ for v in values if v is not None)
    if len(types) == 1:
        return types.pop()
    if types <= {"int", "float"}:
        return "number"
    return "string"


def rule_generalize(
    manager: SkillLifecycleManager,
    skill: Skill,
    episodes: List[Episode]
) -> bool:
    """
    Rule S2: Generalize by parameterization.
    
    Trigger: Two or more episodes differ only by substitutable elements.
    
    Rewrite:
    - Replace constants with parameters
    - Add parameter schema
    - Promote to Generalizing
    """
    if skill.lifecycle_state != LifecycleState.VALIDATED:
        return False
    
    if len(episodes) < 2:
        return False
    
    # Find differences
    diffs = find_substitutable_differences(episodes)
    
    if not diffs:
        return False
    
    # Add parameters
    params_added = []
    for diff in diffs:
        param = Parameter(
            name=diff.inferred_name,
            type=diff.inferred_type,
            description=f"Extracted from {diff.location}",
            examples=diff.values[:3]  # Keep up to 3 examples
        )
        
        # Don't add duplicates
        if not any(p.name == param.name for p in skill.parameter_schema):
            skill.parameter_schema.append(param)
            params_added.append(param.name)
    
    if not params_added:
        return False
    
    # Update plan template to use parameters
    if skill.plan_template:
        for diff in diffs:
            if diff.location.startswith("plan["):
                _parameterize_plan_template(skill.plan_template, diff)
    
    # Promote to generalizing
    skill.lifecycle_state = LifecycleState.GENERALIZING
    skill.last_modified = datetime.now()
    
    # Emit event
    manager.emit_event(SkillGeneralized(
        skill_id=skill.skill_id,
        parameters_added=params_added
    ))
    
    logger.info(f"GENERALIZE: {skill.name} - added parameters: {params_added}")
    return True


def _parameterize_plan_template(template: PlanTemplate, diff: SubstitutableDifference):
    """Update plan template to use a parameter."""
    # Parse location like "plan[0].target"
    import re
    match = re.match(r"plan\[(\d+)\]\.(\w+)", diff.location)
    if match:
        step_idx = int(match.group(1))
        key = match.group(2)
        if step_idx < len(template.steps):
            # Replace with parameter reference
            template.steps[step_idx].parameters[key] = f"${{{diff.inferred_name}}}"


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S3: LEARN Applicability Boundaries
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DiscriminatingFeature:
    """A feature that discriminates success from failure."""
    feature: str
    type: str  # "required" or "forbidden"
    condition: str
    confidence: float


def find_discriminating_features(
    successes: List[Episode],
    failures: List[Episode]
) -> List[DiscriminatingFeature]:
    """
    Find features that distinguish successful from failed episodes.
    """
    features = []
    
    if not successes or not failures:
        return features
    
    # Collect all features from situations
    all_keys: Set[str] = set()
    for e in successes + failures:
        all_keys.update(e.situation.keys())
        all_keys.update(e.environment_signature.keys())
    
    for key in all_keys:
        # Values in successes
        success_values = set()
        for e in successes:
            val = e.situation.get(key) or e.environment_signature.get(key)
            if val is not None:
                success_values.add(str(val))
        
        # Values in failures
        failure_values = set()
        for e in failures:
            val = e.situation.get(key) or e.environment_signature.get(key)
            if val is not None:
                failure_values.add(str(val))
        
        # Check for discrimination
        if success_values and not failure_values:
            # This feature is required
            features.append(DiscriminatingFeature(
                feature=key,
                type="required",
                condition=f"{key} in {success_values}",
                confidence=len(successes) / (len(successes) + len(failures))
            ))
        
        elif failure_values and not success_values:
            # Absence of this feature is required
            features.append(DiscriminatingFeature(
                feature=key,
                type="forbidden",
                condition=f"{key} exists",
                confidence=len(successes) / (len(successes) + len(failures))
            ))
        
        elif success_values and failure_values and not success_values.intersection(failure_values):
            # Different values discriminate
            features.append(DiscriminatingFeature(
                feature=key,
                type="required",
                condition=f"{key} in {success_values} (not {failure_values})",
                confidence=1.0
            ))
    
    # Sort by confidence
    features.sort(key=lambda f: -f.confidence)
    return features


def rule_learn_boundaries(
    manager: SkillLifecycleManager,
    skill: Skill,
    episodes: List[Episode]
) -> bool:
    """
    Rule S3: Learn applicability boundaries.
    
    Trigger: Skill succeeds in some contexts, fails in others.
    
    Rewrite:
    - Add guard conditions (required/forbidden)
    - Update applicability_conditions and do_not_apply_when
    """
    if skill.lifecycle_state not in [LifecycleState.VALIDATED, LifecycleState.GENERALIZING]:
        return False
    
    successes = [e for e in episodes if e.success]
    failures = [e for e in episodes if not e.success]
    
    if not successes or not failures:
        return False  # Need both to learn boundaries
    
    # Find discriminating features
    features = find_discriminating_features(successes, failures)
    
    if not features:
        return False
    
    conditions_added = 0
    for feature in features[:5]:  # Take top 5
        condition = Condition(
            expression=feature.condition,
            description=f"Learned from {len(successes)} successes, {len(failures)} failures",
            type=feature.type
        )
        
        if feature.type == "required":
            if not any(c.expression == condition.expression for c in skill.applicability_conditions):
                skill.applicability_conditions.append(condition)
                conditions_added += 1
        else:
            if not any(c.expression == condition.expression for c in skill.do_not_apply_when):
                skill.do_not_apply_when.append(condition)
                conditions_added += 1
    
    if conditions_added > 0:
        skill.last_modified = datetime.now()
        logger.info(f"LEARN_BOUNDARIES: {skill.name} - added {conditions_added} conditions")
        return True
    
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S4: SPLIT on Bimodal Failure
# ═══════════════════════════════════════════════════════════════════════════════

def cluster_by_regime(episodes: List[Episode]) -> List[Dict[str, Any]]:
    """
    Cluster episodes by failure modes / context features.
    Returns list of clusters, each with conditions and episodes.
    """
    # Simple clustering based on environment signatures
    clusters = defaultdict(list)
    
    for episode in episodes:
        # Create a signature from key environment features
        sig_parts = []
        for key in sorted(episode.environment_signature.keys()):
            sig_parts.append(f"{key}={episode.environment_signature[key]}")
        
        # Also consider situation features
        for key in sorted(episode.situation.keys()):
            val = episode.situation[key]
            if isinstance(val, (str, int, float, bool)):
                sig_parts.append(f"s:{key}={val}")
        
        signature = "|".join(sig_parts) if sig_parts else "default"
        clusters[signature].append(episode)
    
    # Convert to list of cluster dicts
    result = []
    for sig, eps in clusters.items():
        success_rate = sum(1 for e in eps if e.success) / len(eps) if eps else 0
        result.append({
            "signature": sig,
            "episodes": eps,
            "success_rate": success_rate,
            "conditions": sig.split("|")
        })
    
    return result


def clusters_are_distinct(clusters: List[Dict], threshold: float = 0.3) -> bool:
    """Check if clusters have significantly different success rates."""
    if len(clusters) < 2:
        return False
    
    rates = [c["success_rate"] for c in clusters]
    return max(rates) - min(rates) >= threshold


def rule_split(
    manager: SkillLifecycleManager,
    skill: Skill,
    episodes: List[Episode]
) -> Optional[List[Skill]]:
    """
    Rule S4: Split on bimodal failure.
    
    Trigger: Skill exhibits two distinct regimes.
    
    Rewrite:
    - Cluster episodes by failure modes
    - Create new skills with narrower applicability
    - Deprecate original skill
    """
    if skill.lifecycle_state not in [LifecycleState.GENERALIZING, LifecycleState.OPERATIONAL]:
        return None
    
    clusters = cluster_by_regime(episodes)
    
    if len(clusters) < 2 or not clusters_are_distinct(clusters):
        return None
    
    # Create new skills for each cluster
    new_skills = []
    for i, cluster in enumerate(clusters):
        new_skill = Skill(
            skill_id=f"{skill.skill_id}_split_{i}",
            name=f"{skill.name} (variant {i+1})",
            version="0.1.0",
            lifecycle_state=LifecycleState.VALIDATED,
            parameter_schema=skill.parameter_schema.copy(),
            plan_template=skill.plan_template,
            required_tools=skill.required_tools.copy(),
            source="split",
            created_from_episodes=[e.episode_id for e in cluster["episodes"]]
        )
        
        # Add conditions from cluster
        for cond_str in cluster["conditions"]:
            if cond_str and cond_str != "default":
                new_skill.applicability_conditions.append(Condition(
                    expression=cond_str,
                    description="From cluster analysis"
                ))
        
        # Calculate success rate
        new_skill.success_rate = cluster["success_rate"]
        new_skill.total_executions = len(cluster["episodes"])
        new_skill.episode_ids = [e.episode_id for e in cluster["episodes"]]
        
        new_skills.append(new_skill)
        manager.skills[new_skill.skill_id] = new_skill
    
    # Deprecate original
    manager.deprecate(skill, "Split into specialized variants", 
                      superseded_by=new_skills[0].skill_id if new_skills else None)
    
    # Emit event
    manager.emit_event(SkillSplit(
        skill_id=skill.skill_id,
        new_skill_ids=[s.skill_id for s in new_skills],
        split_reason="Bimodal failure pattern detected"
    ))
    
    logger.info(f"SPLIT: {skill.name} → {len(new_skills)} variants")
    return new_skills


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S5: MERGE Duplicates
# ═══════════════════════════════════════════════════════════════════════════════

def compute_skill_overlap(skill_a: Skill, skill_b: Skill) -> float:
    """
    Compute overlap between two skills based on:
    - Plan structure similarity
    - Applicability condition overlap
    - Parameter schema similarity
    """
    overlap_score = 0.0
    
    # Compare plans
    if skill_a.plan_template and skill_b.plan_template:
        steps_a = [s.action_type for s in skill_a.plan_template.steps]
        steps_b = [s.action_type for s in skill_b.plan_template.steps]
        
        common = set(steps_a) & set(steps_b)
        total = set(steps_a) | set(steps_b)
        if total:
            overlap_score += 0.4 * len(common) / len(total)
    
    # Compare parameters
    params_a = {p.name for p in skill_a.parameter_schema}
    params_b = {p.name for p in skill_b.parameter_schema}
    if params_a or params_b:
        common = params_a & params_b
        total = params_a | params_b
        if total:
            overlap_score += 0.3 * len(common) / len(total)
    
    # Compare tools
    tools_a = set(skill_a.required_tools)
    tools_b = set(skill_b.required_tools)
    if tools_a or tools_b:
        common = tools_a & tools_b
        total = tools_a | tools_b
        if total:
            overlap_score += 0.3 * len(common) / len(total)
    
    return overlap_score


def rule_merge(
    manager: SkillLifecycleManager,
    skill_a: Skill,
    skill_b: Skill,
    merge_threshold: float = 0.7
) -> Optional[Skill]:
    """
    Rule S5: Merge duplicates.
    
    Trigger: Two skills have high overlap in applicability and plan structure.
    
    Rewrite:
    - Merge into canonical skill
    - Create aliases
    - Preserve provenance
    """
    overlap = compute_skill_overlap(skill_a, skill_b)
    
    if overlap < merge_threshold:
        return None
    
    # Choose canonical (higher success rate wins)
    if skill_a.success_rate >= skill_b.success_rate:
        canonical, deprecated = skill_a, skill_b
    else:
        canonical, deprecated = skill_b, skill_a
    
    # Merge knowledge
    canonical.episode_ids.extend(deprecated.episode_ids)
    canonical.total_executions += deprecated.total_executions
    
    # Merge applicability conditions
    for cond in deprecated.applicability_conditions:
        if not any(c.expression == cond.expression for c in canonical.applicability_conditions):
            canonical.applicability_conditions.append(cond)
    
    # Recalculate success rate
    if canonical.total_executions > 0:
        success_count = sum(
            1 for eid in canonical.episode_ids
            if eid in manager.episodes and manager.episodes[eid].success
        )
        canonical.success_rate = success_count / canonical.total_executions
    
    # Deprecate the other
    manager.deprecate(deprecated, "Merged with duplicate", superseded_by=canonical.skill_id)
    
    # Emit event
    manager.emit_event(SkillsMerged(
        skill_id=deprecated.skill_id,
        merged_skill_id=deprecated.skill_id,
        canonical_skill_id=canonical.skill_id
    ))
    
    logger.info(f"MERGE: {deprecated.name} → {canonical.name} (overlap: {overlap:.1%})")
    return canonical


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S6: COMPOSE Macro-Skills
# ═══════════════════════════════════════════════════════════════════════════════

def find_frequent_sequences(
    episodes: List[Episode],
    min_frequency: int = 3
) -> List[Tuple[List[str], int]]:
    """
    Find frequently occurring skill sequences in episodes.
    """
    # Build sequence from consecutive episodes
    sequences = defaultdict(int)
    
    # Group episodes by session/context
    sessions = defaultdict(list)
    for e in episodes:
        # Use date as session key
        session_key = e.timestamp.strftime("%Y-%m-%d")
        sessions[session_key].append(e)
    
    # Find sequences within sessions
    for session_eps in sessions.values():
        session_eps.sort(key=lambda e: e.timestamp)
        
        for window_size in [2, 3, 4]:
            for i in range(len(session_eps) - window_size + 1):
                window = session_eps[i:i+window_size]
                
                # Only consider successful skill sequences
                if all(e.skill_id and e.success for e in window):
                    seq = tuple(e.skill_id for e in window)
                    sequences[seq] += 1
    
    # Filter by frequency
    frequent = [(list(seq), count) for seq, count in sequences.items() if count >= min_frequency]
    frequent.sort(key=lambda x: -x[1])
    
    return frequent


def rule_compose(
    manager: SkillLifecycleManager,
    skill_ids: List[str],
    macro_name: str,
    macro_task: Dict[str, Any]
) -> Optional[Skill]:
    """
    Rule S6: Compose macro-skills from frequent sequences.
    
    Trigger: Agent repeatedly executes skill sequence for higher task.
    
    Rewrite:
    - Create macro-skill
    - Add orchestration logic
    - Learn inter-skill bindings
    """
    # Validate all component skills exist and are operational
    component_skills = []
    for sid in skill_ids:
        if sid not in manager.skills:
            return None
        skill = manager.skills[sid]
        if skill.lifecycle_state not in [LifecycleState.OPERATIONAL, LifecycleState.REFINED]:
            return None
        component_skills.append(skill)
    
    # Create macro skill
    macro = Skill(
        skill_id=f"macro_{skill_ids[0]}_{len(skill_ids)}",
        name=macro_name,
        lifecycle_state=LifecycleState.CANDIDATE,
        source="composition",
        component_skills=skill_ids,
        composition_type="sequence"
    )
    
    # Build composite plan template
    composite_steps = []
    for i, skill in enumerate(component_skills):
        if skill.plan_template:
            for step in skill.plan_template.steps:
                composite_steps.append(PlanStep(
                    step_id=f"{i}_{step.step_id}",
                    action_type=step.action_type,
                    description=f"[{skill.name}] {step.description}",
                    parameters=step.parameters.copy()
                ))
    
    macro.plan_template = PlanTemplate(steps=composite_steps)
    
    # Collect all required tools
    all_tools = set()
    for skill in component_skills:
        all_tools.update(skill.required_tools)
    macro.required_tools = list(all_tools)
    
    # Collect all required skills
    macro.required_skills = skill_ids
    
    # Store
    manager.skills[macro.skill_id] = macro
    
    # Emit event
    manager.emit_event(MacroComposed(
        skill_id=macro.skill_id,
        component_skill_ids=skill_ids
    ))
    
    logger.info(f"COMPOSE: {macro_name} from {len(skill_ids)} skills")
    return macro


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S7: QUARANTINE on Failure
# ═══════════════════════════════════════════════════════════════════════════════

def rule_quarantine(
    manager: SkillLifecycleManager,
    skill: Skill,
    reason: str,
    evidence: List[Episode] = None
) -> bool:
    """
    Rule S7: Quarantine on failure.
    
    Trigger: Safety violation, repeated failure, or tool breakage.
    
    Rewrite:
    - Preserve previous state
    - Move to quarantine
    - Remove from retrieval index
    """
    if skill.lifecycle_state == LifecycleState.QUARANTINED:
        return False  # Already quarantined
    
    if skill.lifecycle_state == LifecycleState.DEPRECATED:
        return False  # Can't quarantine deprecated
    
    manager.quarantine(skill, reason, evidence)
    logger.info(f"QUARANTINE: {skill.name} - {reason}")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# RULE S8: DEPRECATE on Supersession
# ═══════════════════════════════════════════════════════════════════════════════

def rule_deprecate(
    manager: SkillLifecycleManager,
    skill: Skill,
    reason: str,
    superseded_by: str = None
) -> bool:
    """
    Rule S8: Deprecate on supersession.
    
    Trigger: Skill replaced by better version or invalid in environment.
    
    Rewrite:
    - Move to deprecated
    - Keep in archive
    - Remove from retrieval
    """
    if skill.lifecycle_state == LifecycleState.DEPRECATED:
        return False
    
    manager.deprecate(skill, reason, superseded_by)
    logger.info(f"DEPRECATE: {skill.name} - {reason}")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# RULE APPLICATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class RewriteEngine:
    """
    Engine that applies rewrite rules to maintain the skill ecosystem.
    """
    
    def __init__(self, manager: SkillLifecycleManager):
        self.manager = manager
        self.rules_applied: List[Dict] = []
    
    def process_episode(self, episode: Episode):
        """Process a new episode and apply relevant rules."""
        self.manager.record_episode(episode)
        
        if episode.skill_id and episode.skill_id in self.manager.skills:
            skill = self.manager.skills[episode.skill_id]
            skill_episodes = [
                self.manager.episodes[eid]
                for eid in skill.episode_ids
                if eid in self.manager.episodes
            ]
            
            # Try promotion rules
            if skill.lifecycle_state == LifecycleState.CANDIDATE:
                if rule_promote(self.manager, skill, episode):
                    self._record_rule("S1_PROMOTE", skill.skill_id)
            
            # Try generalization
            elif skill.lifecycle_state == LifecycleState.VALIDATED:
                if len(skill_episodes) >= 2:
                    if rule_generalize(self.manager, skill, skill_episodes):
                        self._record_rule("S2_GENERALIZE", skill.skill_id)
            
            # Try boundary learning
            elif skill.lifecycle_state == LifecycleState.GENERALIZING:
                if rule_learn_boundaries(self.manager, skill, skill_episodes):
                    self._record_rule("S3_LEARN_BOUNDARIES", skill.skill_id)
                
                # Check for promotion to operational
                self.manager.promote_to_operational(skill)
    
    def run_maintenance(self):
        """Run maintenance rules across all skills."""
        # Check for splits
        for skill in list(self.manager.skills.values()):
            if skill.lifecycle_state in [LifecycleState.GENERALIZING, LifecycleState.OPERATIONAL]:
                episodes = [
                    self.manager.episodes[eid]
                    for eid in skill.episode_ids
                    if eid in self.manager.episodes
                ]
                
                new_skills = rule_split(self.manager, skill, episodes)
                if new_skills:
                    self._record_rule("S4_SPLIT", skill.skill_id)
        
        # Check for merges
        operational = self.manager.get_operational_skills()
        for i, skill_a in enumerate(operational):
            for skill_b in operational[i+1:]:
                merged = rule_merge(self.manager, skill_a, skill_b)
                if merged:
                    self._record_rule("S5_MERGE", f"{skill_a.skill_id},{skill_b.skill_id}")
    
    def _record_rule(self, rule_name: str, target: str):
        self.rules_applied.append({
            "timestamp": datetime.now().isoformat(),
            "rule": rule_name,
            "target": target
        })


if __name__ == "__main__":
    # Example usage
    print("Rewrite Rules Module")
    print("=" * 40)
    print()
    print("Available rules:")
    print("  S1: PROMOTE - Candidate → Validated")
    print("  S2: GENERALIZE - Add parameters")
    print("  S3: LEARN_BOUNDARIES - Add conditions")
    print("  S4: SPLIT - Divide bimodal skills")
    print("  S5: MERGE - Unify duplicates")
    print("  S6: COMPOSE - Create macro-skills")
    print("  S7: QUARANTINE - Isolate failing skills")
    print("  S8: DEPRECATE - Archive superseded skills")
