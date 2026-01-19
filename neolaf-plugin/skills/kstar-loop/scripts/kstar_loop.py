#!/usr/bin/env python3
"""
KSTAR Loop - Foundational Cognitive Cycle for Agents

Implements the K→S→T→A→R cycle:
- K: Knowledge (episodic + semantic + actor model)
- S: Situation (actor, domain, protocol, now)
- T: Task (goal, stage, criteria, constraints)
- A: Action (plan + forecast)
- R: Result (observation + reflection)

Usage:
    from kstar_loop import KSTARLoop
    
    loop = KSTARLoop(knowledge, situation, task)
    result = loop.run()
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from copy import deepcopy
from datetime import datetime, timezone


class Stage(Enum):
    UNDERSTAND = "understand"
    PLAN = "plan"
    EXECUTE = "execute"
    VALIDATE = "validate"
    REFLECT = "reflect"
    COMPLETE = "complete"


class Mode(Enum):
    LEARNING = "LEARNING"
    PERFORMANCE = "PERFORMANCE"


@dataclass
class ModeConfig:
    """Configuration for KSTAR operating mode."""
    name: str
    exploration: float                 # 0.0-1.0, tendency to try alternatives
    uair_bias: str                     # "ASK" or "RETRIEVE"
    required_fields: List[str]         # S components required before proceeding
    clarification_threshold: float     # Confidence threshold to ask questions
    alternatives_required: int         # Minimum alternative plans to generate
    plan_acceptance_threshold: float   # Confidence to accept plan
    forecast_required: bool            # Always generate R̂?
    confidence_threshold: float        # Skip forecast if confidence above this
    narrate_actions: bool              # Explain actions during execution
    record_all_episodes: bool          # Always record to K
    prediction_error_threshold: float  # Delta threshold for K update
    aar_depth: str                     # "full" or "summary"
    inter_stage_reflection: bool       # Mini-AARs between stages


# Standard mode configurations
MODE_CONFIGS = {
    Mode.LEARNING: ModeConfig(
        name="LEARNING",
        exploration=0.8,
        uair_bias="ASK",
        required_fields=["actor_state.id", "domain_state.objective", "protocol_state.workflow_type", "now_state.tools_available"],
        clarification_threshold=0.7,
        alternatives_required=2,
        plan_acceptance_threshold=0.3,
        forecast_required=True,
        confidence_threshold=0.95,
        narrate_actions=True,
        record_all_episodes=True,
        prediction_error_threshold=0.0,
        aar_depth="full",
        inter_stage_reflection=True
    ),
    Mode.PERFORMANCE: ModeConfig(
        name="PERFORMANCE",
        exploration=0.2,
        uair_bias="RETRIEVE",
        required_fields=["domain_state.objective"],
        clarification_threshold=0.3,
        alternatives_required=0,
        plan_acceptance_threshold=0.7,
        forecast_required=False,
        confidence_threshold=0.7,
        narrate_actions=False,
        record_all_episodes=False,
        prediction_error_threshold=0.3,
        aar_depth="summary",
        inter_stage_reflection=False
    )
}


@dataclass
class ActorState:
    id: str
    role: Optional[str] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)


@dataclass
class DomainState:
    objective: str
    domain_type: Optional[str] = None
    resources: List[Dict] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    rubrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtocolState:
    current_stage: Stage = Stage.UNDERSTAND
    workflow_type: Optional[str] = None
    interaction_pattern: Optional[str] = None
    agent_role: str = "companion"
    stage_history: List[Dict] = field(default_factory=list)
    turn_count: int = 0


@dataclass
class NowState:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tools_available: List[Dict] = field(default_factory=list)
    time_budget_minutes: Optional[int] = None
    session_context: Dict[str, Any] = field(default_factory=dict)
    active_artifacts: List[str] = field(default_factory=list)


@dataclass
class Situation:
    actor_state: ActorState
    domain_state: DomainState
    protocol_state: ProtocolState
    now_state: NowState
    
    def to_dict(self) -> Dict:
        return {
            "actor_state": self.actor_state.__dict__,
            "domain_state": self.domain_state.__dict__,
            "protocol_state": {
                **self.protocol_state.__dict__,
                "current_stage": self.protocol_state.current_stage.value
            },
            "now_state": self.now_state.__dict__
        }


@dataclass
class Task:
    id: str
    goal: str
    stage: Stage = Stage.UNDERSTAND
    success_criteria: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    parent_task: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "stage": self.stage.value,
            "success_criteria": self.success_criteria,
            "constraints": self.constraints,
            "parent_task": self.parent_task,
            "subtasks": self.subtasks
        }


@dataclass
class ActionPlan:
    actions: List[Dict]
    resources: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    is_feasible: bool = True


@dataclass
class Forecast:
    expected_outcome: str
    success_probability: float
    risks: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class Result:
    observation: Any
    success: bool
    errors: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Episode:
    """Single KSTAR episode for memory encoding."""
    knowledge_snapshot: Dict
    situation: Dict
    task: Dict
    action: Dict
    result: Dict
    prediction_error: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_kstar_entry(self) -> Dict:
        """Transform to KSTAR canonical form for memory."""
        return {
            "K": self.knowledge_snapshot,
            "S": self.situation,
            "T": self.task,
            "A": self.action,
            "R": {
                **self.result,
                "prediction_error": self.prediction_error
            },
            "timestamp": self.timestamp
        }


@dataclass
class AAR:
    """After-Action Review."""
    what_happened: str
    what_worked: List[str]
    what_didnt_work: List[str]
    lessons_learned: List[str]
    knowledge_deltas: List[Dict]
    recommendations: List[str]
    complete: bool = False


class KSTARLoop:
    """
    Main KSTAR cognitive loop implementation.
    
    Orchestrates the K→S→T→A→R cycle with:
    - Situation completion via UAIR
    - Staged task execution
    - Forecast validation
    - Reflective learning
    """
    
    RETRY_LIMITS = {
        Stage.UNDERSTAND: 3,
        Stage.PLAN: 3,
        Stage.EXECUTE: 5,
        Stage.VALIDATE: 2,
        Stage.REFLECT: 2
    }
    
    def __init__(
        self,
        knowledge: Dict[str, Any],
        situation: Situation,
        task: Task,
        mode: Mode = Mode.LEARNING
    ):
        self.K = deepcopy(knowledge)
        self.S = situation
        self.T = task
        self.mode = mode
        self.config = MODE_CONFIGS[mode]

        self.episodes: List[Episode] = []
        self.stage_counts: Dict[Stage, int] = {s: 0 for s in Stage}
        self.stage_reflections: List[Dict] = []  # For inter-stage reflection

        # Pluggable handlers
        self.uair_handler: Optional[Callable] = None
        self.planner: Optional[Callable] = None
        self.forecaster: Optional[Callable] = None
        self.executor: Optional[Callable] = None
        self.validator: Optional[Callable] = None
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the KSTAR loop until completion or halt.

        Returns final state including knowledge updates and AAR.
        Mode affects: situation requirements, narration, reflection depth, K updates.
        """
        if self.config.narrate_actions:
            self._narrate(f"Starting KSTAR loop in {self.mode.value} mode for: {self.T.goal}")

        while self.T.stage != Stage.COMPLETE:
            # Check retry limits
            if self.stage_counts[self.T.stage] >= self.RETRY_LIMITS.get(self.T.stage, 3):
                return self._halt(f"Retry limit exceeded for {self.T.stage.value}")

            self.stage_counts[self.T.stage] += 1
            prev_stage = self.T.stage

            # Record stage entry
            self.S.protocol_state.stage_history.append({
                "stage": self.T.stage.value,
                "entered_at": datetime.now(timezone.utc).isoformat(),
                "mode": self.mode.value
            })

            # 1. Situation completion (mode-aware field requirements)
            if not self._situation_complete():
                completion_result = self._complete_situation()
                if completion_result.get("status") == "blocked":
                    return self._pause(completion_result)

            # 2. Stage-specific processing
            if self.T.stage == Stage.UNDERSTAND:
                result = self._stage_understand()
            elif self.T.stage == Stage.PLAN:
                result = self._stage_plan()
            elif self.T.stage == Stage.EXECUTE:
                result = self._stage_execute()
            elif self.T.stage == Stage.VALIDATE:
                result = self._stage_validate()
            elif self.T.stage == Stage.REFLECT:
                result = self._stage_reflect()
            else:
                break

            # 3. Stage transition
            self.T.stage = self._next_stage(result)

            # 4. Inter-stage reflection (LEARNING mode only)
            if self.config.inter_stage_reflection and self.T.stage != Stage.COMPLETE:
                mini_aar = self._inter_stage_reflect(prev_stage, result)
                if mini_aar:
                    self.stage_reflections.append(mini_aar)

        return self._complete()

    def _narrate(self, message: str):
        """Output narration in LEARNING mode."""
        if self.config.narrate_actions:
            print(f"[KSTAR] {message}")

    def _inter_stage_reflect(self, prev_stage: Stage, result: Dict) -> Optional[Dict]:
        """Generate mini-AAR between stages (LEARNING mode)."""
        if not self.config.inter_stage_reflection:
            return None

        return {
            "stage": prev_stage.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "observations": [
                f"Completed {prev_stage.value} stage",
                f"Result success: {result.get('complete', result.get('goal_structured', 'unknown'))}"
            ],
            "insights": [],
            "adjustments": []
        }
    
    def _situation_complete(self) -> bool:
        """Check if situation has required fields based on mode and stage."""
        # Mode-specific base requirements
        mode_required = self.config.required_fields

        # Stage-specific additional requirements
        stage_required = {
            Stage.UNDERSTAND: [],
            Stage.PLAN: ["actor_state.capabilities"] if self.mode == Mode.LEARNING else [],
            Stage.EXECUTE: ["now_state.tools_available"] if self.mode == Mode.LEARNING else [],
            Stage.VALIDATE: ["domain_state.requirements"] if self.mode == Mode.LEARNING else [],
            Stage.REFLECT: []
        }

        # Combine mode + stage requirements
        all_required = set(mode_required) | set(stage_required.get(self.T.stage, []))

        for path in all_required:
            if not self._has_value(self.S.to_dict(), path):
                if self.config.narrate_actions:
                    self._narrate(f"Missing required field: {path}")
                return False
        return True
    
    def _complete_situation(self) -> Dict:
        """Invoke UAIR for situation completion."""
        if self.uair_handler:
            return self.uair_handler(self.S.to_dict(), self.T.to_dict())
        
        # Default: mark as needing input
        return {
            "status": "needs_input",
            "missing_fields": self._get_missing_fields()
        }
    
    def _get_missing_fields(self) -> List[str]:
        """Identify missing situation fields."""
        missing = []
        s_dict = self.S.to_dict()
        
        checks = [
            ("actor_state.id", "Actor ID"),
            ("domain_state.objective", "Objective"),
            ("protocol_state.workflow_type", "Workflow type")
        ]
        
        for path, label in checks:
            if not self._has_value(s_dict, path):
                missing.append(path)
        
        return missing
    
    def _stage_understand(self) -> Dict:
        """Process understand stage."""
        # Parse goal, identify constraints, define success criteria
        
        structured_goal = self._parse_goal(self.T.goal)
        
        if not self.T.success_criteria:
            self.T.success_criteria = self._derive_criteria(structured_goal)
        
        return {
            "stage": "understand",
            "goal_structured": True,
            "criteria_defined": len(self.T.success_criteria) > 0,
            "structured_goal": structured_goal
        }
    
    def _stage_plan(self) -> Dict:
        """Process plan stage with mode-aware behavior."""
        if self.config.narrate_actions:
            self._narrate(f"Planning stage - generating {'multiple alternatives' if self.config.alternatives_required > 0 else 'best approach'}")

        # Generate action plan(s)
        if self.planner:
            plan = self.planner(self.K, self.S.to_dict(), self.T.to_dict())
        else:
            plan = self._default_plan()

        # In LEARNING mode, generate alternatives
        alternatives = []
        if self.config.alternatives_required > 0:
            for i in range(self.config.alternatives_required):
                alt = self._generate_alternative_plan(plan, i)
                alternatives.append(alt)
            if self.config.narrate_actions:
                self._narrate(f"Generated {len(alternatives)} alternative plans for comparison")

        # Generate forecast (required in LEARNING, optional in PERFORMANCE)
        forecast = None
        if self.config.forecast_required or self._needs_forecast():
            if self.forecaster:
                forecast = self.forecaster(self.K, self.S.to_dict(), plan)
            else:
                forecast = self._default_forecast(plan)
        elif self.config.narrate_actions:
            self._narrate("Skipping forecast (high confidence in PERFORMANCE mode)")

        self._current_plan = plan
        self._current_forecast = forecast
        self._current_alternatives = alternatives

        return {
            "stage": "plan",
            "plan": plan,
            "alternatives": alternatives,
            "forecast": forecast,
            "is_feasible": plan.get("is_feasible", True),
            "success_probability": forecast.get("success_probability", 0.7) if forecast else 0.7,
            "mode": self.mode.value
        }

    def _generate_alternative_plan(self, base_plan: Dict, index: int) -> Dict:
        """Generate alternative plan variation (LEARNING mode)."""
        # Simple variation - in production would use K to generate meaningful alternatives
        alt = deepcopy(base_plan)
        alt["variation"] = index + 1
        alt["approach"] = f"alternative_{index + 1}"
        return alt

    def _needs_forecast(self) -> bool:
        """Check if forecast is needed based on confidence."""
        # Estimate confidence from K
        domain = getattr(self.S.domain_state, 'domain_type', 'unknown')
        confidence = self.K.get("confidence", {}).get(domain, 0.5)
        return confidence < self.config.confidence_threshold
    
    def _stage_execute(self) -> Dict:
        """Process execute stage with mode-aware behavior."""
        plan = getattr(self, "_current_plan", self._default_plan())
        forecast = getattr(self, "_current_forecast", {})

        if self.config.narrate_actions:
            self._narrate(f"Executing plan: {plan.get('actions', [{}])[0].get('description', 'action')}")

        if self.executor:
            result = self.executor(plan, self.S.to_dict())
        else:
            result = self._default_execute(plan)

        if self.config.narrate_actions:
            self._narrate(f"Execution {'succeeded' if result.get('success') else 'failed'}")

        # Compute prediction error
        prediction_error = self._compute_prediction_error(result, forecast) if forecast else 0.0

        # Record episode based on mode
        should_record = (
            self.config.record_all_episodes or
            abs(prediction_error) > self.config.prediction_error_threshold
        )

        if should_record:
            episode = Episode(
                knowledge_snapshot={"summary": "snapshot", "mode": self.mode.value},
                situation=self.S.to_dict(),
                task=self.T.to_dict(),
                action=plan,
                result=result,
                prediction_error=prediction_error
            )
            self.episodes.append(episode)
            if self.config.narrate_actions:
                self._narrate(f"Recorded episode (prediction_error={prediction_error:.2f})")
        elif self.config.narrate_actions:
            self._narrate(f"Skipping episode recording (error {prediction_error:.2f} below threshold)")

        return {
            "stage": "execute",
            "result": result,
            "prediction_error": prediction_error,
            "complete": result.get("success", False),
            "episode_recorded": should_record,
            "mode": self.mode.value
        }
    
    def _stage_validate(self) -> Dict:
        """Process validate stage."""
        if not self.episodes:
            return {"stage": "validate", "status": "no_episodes"}
        
        last_episode = self.episodes[-1]
        
        if self.validator:
            validation = self.validator(
                last_episode.result,
                self.T.success_criteria,
                self.S.domain_state.rubrics
            )
        else:
            validation = self._default_validate(last_episode.result)
        
        return {
            "stage": "validate",
            "validation": validation,
            "all_criteria_met": validation.get("all_met", False),
            "gaps": validation.get("gaps", [])
        }
    
    def _stage_reflect(self) -> Dict:
        """Process reflect stage - generate AAR based on mode."""
        if self.config.narrate_actions:
            self._narrate(f"Reflection stage - generating {self.config.aar_depth} AAR")

        # Check if AAR should be generated (PERFORMANCE mode may skip)
        should_generate_aar = (
            self.config.aar_depth == "full" or
            any(e.prediction_error > self.config.prediction_error_threshold for e in self.episodes)
        )

        if should_generate_aar:
            aar = self._generate_aar()
            # Update knowledge with learning deltas
            for delta in aar.knowledge_deltas:
                self._integrate_knowledge(delta)
        else:
            # Minimal AAR in PERFORMANCE mode with no significant errors
            aar = AAR(
                what_happened=f"Completed goal: {self.T.goal}",
                what_worked=["Execution completed successfully"],
                what_didnt_work=[],
                lessons_learned=[],
                knowledge_deltas=[],
                recommendations=[],
                complete=True
            )
            if self.config.narrate_actions:
                self._narrate("Skipping detailed AAR (PERFORMANCE mode, no significant errors)")

        return {
            "stage": "reflect",
            "aar": aar.__dict__,
            "aar_depth": self.config.aar_depth,
            "complete": aar.complete,
            "mode": self.mode.value
        }
    
    def _next_stage(self, result: Dict) -> Stage:
        """Determine next stage based on result."""
        current = self.T.stage
        
        if current == Stage.UNDERSTAND:
            if result.get("goal_structured") and result.get("criteria_defined"):
                return Stage.PLAN
            return Stage.UNDERSTAND
        
        elif current == Stage.PLAN:
            if result.get("is_feasible") and result.get("success_probability", 0) > 0.3:
                return Stage.EXECUTE
            return Stage.PLAN
        
        elif current == Stage.EXECUTE:
            if result.get("complete"):
                return Stage.VALIDATE
            if result.get("prediction_error", 1.0) > 0.8:
                return Stage.PLAN  # Replan needed
            return Stage.EXECUTE
        
        elif current == Stage.VALIDATE:
            if result.get("all_criteria_met"):
                return Stage.REFLECT
            if result.get("gaps"):
                return Stage.EXECUTE  # Fix gaps
            return Stage.REFLECT  # Proceed with documented gaps
        
        elif current == Stage.REFLECT:
            if result.get("complete"):
                return Stage.COMPLETE
            return Stage.REFLECT
        
        return Stage.COMPLETE
    
    def _parse_goal(self, goal: str) -> Dict:
        """Parse natural language goal into structure."""
        return {
            "original": goal,
            "parsed": goal,
            "entities": [],
            "constraints": []
        }
    
    def _derive_criteria(self, structured_goal: Dict) -> List[str]:
        """Derive success criteria from structured goal."""
        return [f"Complete: {structured_goal.get('parsed', 'goal')}"]
    
    def _default_plan(self) -> Dict:
        """Default planning when no planner provided."""
        return {
            "actions": [{"type": "execute", "description": self.T.goal}],
            "resources": {},
            "is_feasible": True
        }
    
    def _default_forecast(self, plan: Dict) -> Dict:
        """Default forecasting when no forecaster provided."""
        return {
            "expected_outcome": "success",
            "success_probability": 0.7,
            "risks": []
        }
    
    def _default_execute(self, plan: Dict) -> Dict:
        """Default execution when no executor provided."""
        return {
            "success": True,
            "outputs": {"status": "simulated"},
            "errors": []
        }
    
    def _default_validate(self, result: Dict) -> Dict:
        """Default validation when no validator provided."""
        return {
            "all_met": result.get("success", False),
            "gaps": [] if result.get("success") else ["execution_incomplete"]
        }
    
    def _compute_prediction_error(self, result: Dict, forecast: Dict) -> float:
        """Compute prediction error between result and forecast."""
        if result.get("success") and forecast.get("success_probability", 0) > 0.5:
            return 0.1  # Good prediction
        elif not result.get("success") and forecast.get("success_probability", 0) < 0.5:
            return 0.1  # Also good prediction
        else:
            return 0.8  # Poor prediction
    
    def _generate_aar(self) -> AAR:
        """Generate After-Action Review from episodes."""
        if not self.episodes:
            return AAR(
                what_happened="No episodes recorded",
                what_worked=[],
                what_didnt_work=[],
                lessons_learned=[],
                knowledge_deltas=[],
                recommendations=[],
                complete=True
            )
        
        successes = [e for e in self.episodes if e.result.get("success")]
        failures = [e for e in self.episodes if not e.result.get("success")]
        
        return AAR(
            what_happened=f"Executed {len(self.episodes)} episodes for goal: {self.T.goal}",
            what_worked=[f"Episode {i}" for i, e in enumerate(successes)],
            what_didnt_work=[f"Episode {i}: {e.result.get('errors', [])}" for i, e in enumerate(failures)],
            lessons_learned=self._extract_lessons(),
            knowledge_deltas=[e.to_kstar_entry() for e in self.episodes],
            recommendations=self._generate_recommendations(),
            complete=True
        )
    
    def _extract_lessons(self) -> List[str]:
        """Extract lessons from episodes."""
        lessons = []
        for ep in self.episodes:
            if ep.prediction_error > 0.5:
                lessons.append(f"Prediction error high: review forecast for {ep.task.get('goal')}")
        return lessons
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for future."""
        recs = []
        if any(e.prediction_error > 0.5 for e in self.episodes):
            recs.append("Improve forecasting for this task type")
        return recs
    
    def _integrate_knowledge(self, delta: Dict):
        """Integrate knowledge delta into K."""
        # Simple merge - production would use kstar-transformation
        if "episodes" not in self.K:
            self.K["episodes"] = []
        self.K["episodes"].append(delta)
    
    def _has_value(self, obj: Dict, path: str) -> bool:
        """Check if nested path has a non-None value."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return current is not None
    
    def _halt(self, reason: str) -> Dict:
        """Halt loop with reason."""
        return {
            "status": "halted",
            "reason": reason,
            "stage": self.T.stage.value,
            "episodes": [e.to_kstar_entry() for e in self.episodes]
        }
    
    def _pause(self, info: Dict) -> Dict:
        """Pause loop for external input."""
        return {
            "status": "paused",
            "stage": self.T.stage.value,
            "needs": info,
            "situation": self.S.to_dict(),
            "task": self.T.to_dict()
        }
    
    def _complete(self) -> Dict:
        """Complete loop with final state."""
        if self.config.narrate_actions:
            self._narrate(f"KSTAR loop complete in {self.mode.value} mode")

        # Generate final AAR based on mode
        aar = None
        if self.episodes:
            should_generate = (
                self.config.aar_depth == "full" or
                any(e.prediction_error > self.config.prediction_error_threshold for e in self.episodes)
            )
            if should_generate:
                aar = self._generate_aar()

        return {
            "status": "complete",
            "mode": self.mode.value,
            "knowledge": self.K,
            "aar": aar.__dict__ if aar else None,
            "episodes": [e.to_kstar_entry() for e in self.episodes],
            "stage_reflections": self.stage_reflections if self.config.inter_stage_reflection else [],
            "final_stage": self.T.stage.value,
            "config": {
                "exploration": self.config.exploration,
                "uair_bias": self.config.uair_bias,
                "aar_depth": self.config.aar_depth
            }
        }


# Convenience function
def kstar_loop(
    knowledge: Dict,
    situation: Dict,
    task: Dict,
    mode: str = "LEARNING"
) -> Dict:
    """
    Run KSTAR loop with dict inputs.

    Args:
        knowledge: Knowledge state dictionary
        situation: Situation vector dictionary
        task: Task dictionary with goal and criteria
        mode: "LEARNING" or "PERFORMANCE" (default: LEARNING)

    Returns:
        Final state including knowledge updates and AAR
    """
    S = Situation(
        actor_state=ActorState(**situation.get("actor_state", {"id": "default"})),
        domain_state=DomainState(**situation.get("domain_state", {"objective": "unknown"})),
        protocol_state=ProtocolState(),
        now_state=NowState()
    )

    T = Task(
        id=task.get("id", "task_001"),
        goal=task.get("goal", ""),
        success_criteria=task.get("success_criteria", [])
    )

    # Parse mode string to enum
    mode_enum = Mode.LEARNING if mode.upper() == "LEARNING" else Mode.PERFORMANCE

    loop = KSTARLoop(knowledge, S, T, mode=mode_enum)
    return loop.run()


if __name__ == "__main__":
    # Example: Compare LEARNING vs PERFORMANCE modes
    print("=" * 60)
    print("KSTAR Loop - Mode Comparison Example")
    print("=" * 60)

    knowledge = {
        "domain": "general",
        "episodes": [],
        "confidence": {"programming": 0.7}
    }

    situation = {
        "actor_state": {
            "id": "user_001",
            "role": "learner",
            "capabilities": {"python": 0.6}
        },
        "domain_state": {
            "objective": "Learn recursion",
            "domain_type": "programming",
            "resources": [{"id": "tutorial", "type": "document"}]
        }
    }

    task = {
        "id": "task_001",
        "goal": "Understand and implement recursive factorial",
        "success_criteria": [
            "Explain recursion concept",
            "Implement factorial function",
            "Test with examples"
        ]
    }

    # Run in LEARNING mode
    print("\n" + "=" * 60)
    print("LEARNING MODE")
    print("=" * 60)
    result_learning = kstar_loop(knowledge, situation, task, mode="LEARNING")
    print(f"\nMode: {result_learning.get('mode')}")
    print(f"Episodes recorded: {len(result_learning.get('episodes', []))}")
    print(f"Stage reflections: {len(result_learning.get('stage_reflections', []))}")
    print(f"AAR generated: {'Yes' if result_learning.get('aar') else 'No'}")

    # Run in PERFORMANCE mode
    print("\n" + "=" * 60)
    print("PERFORMANCE MODE")
    print("=" * 60)
    result_performance = kstar_loop(knowledge, situation, task, mode="PERFORMANCE")
    print(f"\nMode: {result_performance.get('mode')}")
    print(f"Episodes recorded: {len(result_performance.get('episodes', []))}")
    print(f"Stage reflections: {len(result_performance.get('stage_reflections', []))}")
    print(f"AAR generated: {'Yes' if result_performance.get('aar') else 'No'}")

    # Full output
    print("\n" + "=" * 60)
    print("LEARNING MODE - Full Output")
    print("=" * 60)
    print(json.dumps(result_learning, indent=2, default=str))
