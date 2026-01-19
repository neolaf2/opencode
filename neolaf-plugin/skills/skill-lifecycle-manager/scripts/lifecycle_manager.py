#!/usr/bin/env python3
"""
Skill Lifecycle Manager

Implements the formal skill lifecycle state machine with governed transitions.
Skills progress from Unknown → Candidate → Validated → Generalizing → Operational → Refined/Composed.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import IntEnum, auto
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE STATES
# ═══════════════════════════════════════════════════════════════════════════════

class LifecycleState(IntEnum):
    """Skill lifecycle states."""
    UNKNOWN = 0
    CANDIDATE = 1
    VALIDATED = 2
    GENERALIZING = 3
    OPERATIONAL = 4
    REFINED = 5
    COMPOSED = 6
    QUARANTINED = 7
    DEPRECATED = 8


STATE_NAMES = {
    0: "Unknown",
    1: "Candidate",
    2: "Validated",
    3: "Generalizing",
    4: "Operational",
    5: "Refined",
    6: "Composed",
    7: "Quarantined",
    8: "Deprecated"
}


# Valid state transitions
VALID_TRANSITIONS = {
    LifecycleState.UNKNOWN: [LifecycleState.CANDIDATE],
    LifecycleState.CANDIDATE: [LifecycleState.VALIDATED, LifecycleState.DEPRECATED],
    LifecycleState.VALIDATED: [LifecycleState.GENERALIZING, LifecycleState.QUARANTINED],
    LifecycleState.GENERALIZING: [
        LifecycleState.OPERATIONAL,
        LifecycleState.QUARANTINED,
        LifecycleState.DEPRECATED  # For split/merge
    ],
    LifecycleState.OPERATIONAL: [
        LifecycleState.REFINED,
        LifecycleState.COMPOSED,
        LifecycleState.QUARANTINED,
        LifecycleState.DEPRECATED
    ],
    LifecycleState.REFINED: [
        LifecycleState.OPERATIONAL,  # Can regress
        LifecycleState.QUARANTINED,
        LifecycleState.DEPRECATED
    ],
    LifecycleState.COMPOSED: [
        LifecycleState.OPERATIONAL,
        LifecycleState.QUARANTINED,
        LifecycleState.DEPRECATED
    ],
    LifecycleState.QUARANTINED: [
        LifecycleState.CANDIDATE,  # Needs revalidation
        LifecycleState.VALIDATED,
        LifecycleState.GENERALIZING,
        LifecycleState.OPERATIONAL,
        LifecycleState.DEPRECATED
    ],
    LifecycleState.DEPRECATED: []  # Terminal state
}


# ═══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LifecycleEvent:
    """Base class for lifecycle events."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    skill_id: str = ""


@dataclass
class SkillCreated(LifecycleEvent):
    source: str = ""  # teacher | web | exploration | transfer


@dataclass
class SkillPromoted(LifecycleEvent):
    from_state: LifecycleState = LifecycleState.UNKNOWN
    to_state: LifecycleState = LifecycleState.CANDIDATE
    evidence: List[str] = field(default_factory=list)  # Episode IDs


@dataclass
class SkillGeneralized(LifecycleEvent):
    parameters_added: List[str] = field(default_factory=list)
    invariants_discovered: List[str] = field(default_factory=list)


@dataclass
class SkillSplit(LifecycleEvent):
    new_skill_ids: List[str] = field(default_factory=list)
    split_reason: str = ""


@dataclass
class SkillsMerged(LifecycleEvent):
    merged_skill_id: str = ""
    canonical_skill_id: str = ""


@dataclass
class MacroComposed(LifecycleEvent):
    component_skill_ids: List[str] = field(default_factory=list)


@dataclass
class SkillQuarantined(LifecycleEvent):
    reason: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class SkillDeprecated(LifecycleEvent):
    reason: str = ""
    superseded_by: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Parameter:
    """Skill parameter definition."""
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Any = None
    examples: List[Any] = field(default_factory=list)


@dataclass
class Condition:
    """Applicability condition."""
    expression: str
    description: str = ""
    type: str = "required"  # required | forbidden


@dataclass
class Verification:
    """Success verification step."""
    check: str
    description: str = ""
    timeout_seconds: int = 30


@dataclass
class PlanStep:
    """A step in a plan template."""
    step_id: str
    action_type: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)
    expected_result: str = ""
    fallback: Optional[str] = None


@dataclass
class PlanTemplate:
    """Parameterized plan template."""
    steps: List[PlanStep] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)


@dataclass
class Episode:
    """A K-STAR execution episode."""
    episode_id: str
    timestamp: datetime
    
    # K-STAR
    situation: Dict[str, Any]
    task: Dict[str, Any]
    plan: List[Dict]
    actions: List[Dict]
    result: Dict[str, Any]
    
    # Meta
    success: bool
    confidence_before: float = 0.5
    confidence_after: float = 0.5
    environment_signature: Dict[str, str] = field(default_factory=dict)
    
    # Links
    skill_id: Optional[str] = None
    skill_version: Optional[str] = None


@dataclass
class Skill:
    """A skill object with lifecycle state."""
    skill_id: str
    name: str
    version: str = "0.1.0"
    lifecycle_state: LifecycleState = LifecycleState.CANDIDATE
    
    # Applicability
    applicability_signature: List[float] = field(default_factory=list)
    applicability_conditions: List[Condition] = field(default_factory=list)
    do_not_apply_when: List[Condition] = field(default_factory=list)
    
    # Execution
    parameter_schema: List[Parameter] = field(default_factory=list)
    plan_template: Optional[PlanTemplate] = None
    verification_steps: List[Verification] = field(default_factory=list)
    fallback_plans: List[PlanTemplate] = field(default_factory=list)
    
    # Dependencies
    required_tools: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    
    # Reliability
    success_rate: float = 0.0
    success_rate_by_regime: Dict[str, float] = field(default_factory=dict)
    total_executions: int = 0
    episode_ids: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    # Provenance
    source: str = ""  # teacher | web | exploration | transfer
    created_from_episodes: List[str] = field(default_factory=list)
    modification_history: List[Dict] = field(default_factory=list)
    
    # Quarantine info (if applicable)
    previous_state: Optional[LifecycleState] = None
    quarantine_reason: Optional[str] = None
    quarantine_evidence: List[str] = field(default_factory=list)
    
    # Deprecation info (if applicable)
    deprecation_reason: Optional[str] = None
    superseded_by: Optional[str] = None
    
    # Composition info (if applicable)
    component_skills: List[str] = field(default_factory=list)
    composition_type: Optional[str] = None  # sequence | parallel | conditional


# ═══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class SkillLifecycleManager:
    """
    Manages skill lifecycle transitions and enforces governance rules.
    """
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.episodes: Dict[str, Episode] = {}
        self.events: List[LifecycleEvent] = []
        self.event_handlers: Dict[type, List[Callable]] = {}
    
    # ─────────────────────────────────────────────────────────────────────────
    # Event System
    # ─────────────────────────────────────────────────────────────────────────
    
    def emit_event(self, event: LifecycleEvent):
        """Emit a lifecycle event."""
        self.events.append(event)
        logger.info(f"Event: {type(event).__name__} for skill {event.skill_id}")
        
        # Notify handlers
        for handler in self.event_handlers.get(type(event), []):
            handler(event)
    
    def on_event(self, event_type: type, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    # ─────────────────────────────────────────────────────────────────────────
    # State Transitions
    # ─────────────────────────────────────────────────────────────────────────
    
    def can_transition(self, skill: Skill, to_state: LifecycleState) -> bool:
        """Check if a transition is valid."""
        valid_targets = VALID_TRANSITIONS.get(skill.lifecycle_state, [])
        return to_state in valid_targets
    
    def transition(self, skill: Skill, to_state: LifecycleState, reason: str = "") -> bool:
        """
        Transition a skill to a new state.
        
        Returns True if successful, False if transition is invalid.
        """
        if not self.can_transition(skill, to_state):
            logger.warning(
                f"Invalid transition: {STATE_NAMES[skill.lifecycle_state]} → {STATE_NAMES[to_state]}"
            )
            return False
        
        from_state = skill.lifecycle_state
        skill.lifecycle_state = to_state
        skill.last_modified = datetime.now()
        
        # Record in history
        skill.modification_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "state_transition",
            "from": STATE_NAMES[from_state],
            "to": STATE_NAMES[to_state],
            "reason": reason
        })
        
        # Emit event
        self.emit_event(SkillPromoted(
            skill_id=skill.skill_id,
            from_state=from_state,
            to_state=to_state
        ))
        
        return True
    
    # ─────────────────────────────────────────────────────────────────────────
    # Skill Creation
    # ─────────────────────────────────────────────────────────────────────────
    
    def create_candidate(
        self,
        name: str,
        plan_template: PlanTemplate,
        source: str = "exploration",
        success_criteria: List[Verification] = None
    ) -> Skill:
        """Create a new candidate skill."""
        skill = Skill(
            skill_id=str(uuid4()),
            name=name,
            lifecycle_state=LifecycleState.CANDIDATE,
            plan_template=plan_template,
            verification_steps=success_criteria or [],
            source=source
        )
        
        self.skills[skill.skill_id] = skill
        self.emit_event(SkillCreated(skill_id=skill.skill_id, source=source))
        
        return skill
    
    # ─────────────────────────────────────────────────────────────────────────
    # Episode Recording
    # ─────────────────────────────────────────────────────────────────────────
    
    def record_episode(self, episode: Episode):
        """Record an execution episode."""
        self.episodes[episode.episode_id] = episode
        
        # Update skill if linked
        if episode.skill_id and episode.skill_id in self.skills:
            skill = self.skills[episode.skill_id]
            skill.episode_ids.append(episode.episode_id)
            skill.total_executions += 1
            
            # Update success tracking
            if episode.success:
                skill.last_success = episode.timestamp
                success_count = sum(
                    1 for eid in skill.episode_ids
                    if self.episodes[eid].success
                )
                skill.success_rate = success_count / skill.total_executions
            else:
                skill.last_failure = episode.timestamp
    
    # ─────────────────────────────────────────────────────────────────────────
    # Promotion Logic
    # ─────────────────────────────────────────────────────────────────────────
    
    def promote_to_validated(self, skill: Skill, episode: Episode) -> bool:
        """Promote a candidate to validated on first success."""
        if skill.lifecycle_state != LifecycleState.CANDIDATE:
            return False
        
        if not episode.success:
            return False
        
        return self.transition(skill, LifecycleState.VALIDATED, 
                               f"First success in episode {episode.episode_id}")
    
    def promote_to_generalizing(self, skill: Skill) -> bool:
        """Promote to generalizing when multiple contexts are seen."""
        if skill.lifecycle_state != LifecycleState.VALIDATED:
            return False
        
        # Need at least 2 distinct contexts
        if skill.total_executions < 2:
            return False
        
        return self.transition(skill, LifecycleState.GENERALIZING,
                               "Multiple execution contexts observed")
    
    def promote_to_operational(
        self,
        skill: Skill,
        success_rate_threshold: float = 0.8,
        min_executions: int = 5
    ) -> bool:
        """Promote to operational when reliability is established."""
        if skill.lifecycle_state != LifecycleState.GENERALIZING:
            return False
        
        if skill.total_executions < min_executions:
            return False
        
        if skill.success_rate < success_rate_threshold:
            return False
        
        return self.transition(skill, LifecycleState.OPERATIONAL,
                               f"Reached {skill.success_rate:.1%} success rate")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Quarantine and Deprecation
    # ─────────────────────────────────────────────────────────────────────────
    
    def quarantine(self, skill: Skill, reason: str, evidence: List[Episode] = None):
        """Quarantine a skill due to safety or reliability issues."""
        skill.previous_state = skill.lifecycle_state
        skill.quarantine_reason = reason
        skill.quarantine_evidence = [e.episode_id for e in (evidence or [])]
        
        self.transition(skill, LifecycleState.QUARANTINED, reason)
        self.emit_event(SkillQuarantined(
            skill_id=skill.skill_id,
            reason=reason,
            evidence=skill.quarantine_evidence
        ))
    
    def restore_from_quarantine(self, skill: Skill) -> bool:
        """Restore a quarantined skill to its previous state."""
        if skill.lifecycle_state != LifecycleState.QUARANTINED:
            return False
        
        if skill.previous_state is None:
            skill.previous_state = LifecycleState.CANDIDATE
        
        return self.transition(skill, skill.previous_state,
                               "Restored from quarantine after review")
    
    def deprecate(self, skill: Skill, reason: str, superseded_by: str = None):
        """Deprecate a skill."""
        skill.deprecation_reason = reason
        skill.superseded_by = superseded_by
        
        self.transition(skill, LifecycleState.DEPRECATED, reason)
        self.emit_event(SkillDeprecated(
            skill_id=skill.skill_id,
            reason=reason,
            superseded_by=superseded_by
        ))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_operational_skills(self) -> List[Skill]:
        """Get all skills in operational or refined state."""
        return [
            s for s in self.skills.values()
            if s.lifecycle_state in [LifecycleState.OPERATIONAL, LifecycleState.REFINED]
        ]
    
    def get_skills_by_state(self, state: LifecycleState) -> List[Skill]:
        """Get all skills in a given state."""
        return [s for s in self.skills.values() if s.lifecycle_state == state]
    
    def get_quarantined_skills(self) -> List[Skill]:
        """Get all quarantined skills needing review."""
        return self.get_skills_by_state(LifecycleState.QUARANTINED)
    
    def get_skill_history(self, skill_id: str) -> List[Dict]:
        """Get modification history for a skill."""
        if skill_id not in self.skills:
            return []
        return self.skills[skill_id].modification_history


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def check_promotion_eligibility(manager: SkillLifecycleManager, skill: Skill) -> Dict[str, Any]:
    """Check what promotions a skill is eligible for."""
    result = {
        "current_state": STATE_NAMES[skill.lifecycle_state],
        "eligible_transitions": [],
        "blockers": []
    }
    
    if skill.lifecycle_state == LifecycleState.CANDIDATE:
        if skill.total_executions == 0:
            result["blockers"].append("No executions yet")
        elif skill.success_rate == 0:
            result["blockers"].append("No successful executions")
        else:
            result["eligible_transitions"].append("→ Validated")
    
    elif skill.lifecycle_state == LifecycleState.VALIDATED:
        if skill.total_executions < 2:
            result["blockers"].append("Need more execution contexts")
        else:
            result["eligible_transitions"].append("→ Generalizing")
    
    elif skill.lifecycle_state == LifecycleState.GENERALIZING:
        if skill.total_executions < 5:
            result["blockers"].append(f"Need ≥5 executions (have {skill.total_executions})")
        if skill.success_rate < 0.8:
            result["blockers"].append(f"Need ≥80% success (have {skill.success_rate:.1%})")
        if not result["blockers"]:
            result["eligible_transitions"].append("→ Operational")
    
    return result


if __name__ == "__main__":
    # Example usage
    manager = SkillLifecycleManager()
    
    # Create a candidate skill
    plan = PlanTemplate(steps=[
        PlanStep(
            step_id="1",
            action_type="search",
            description="Search for information"
        )
    ])
    
    skill = manager.create_candidate(
        name="Web Search Skill",
        plan_template=plan,
        source="exploration"
    )
    
    print(f"Created skill: {skill.name}")
    print(f"State: {STATE_NAMES[skill.lifecycle_state]}")
    print(f"Eligibility: {check_promotion_eligibility(manager, skill)}")
