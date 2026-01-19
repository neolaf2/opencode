#!/usr/bin/env python3
"""
KSTAR to xAPI Transformer

Converts KSTAR episode objects into xAPI statements conforming to the
KSTAR xAPI Profile v0.1.

Usage:
    from kstar_to_xapi import KSTARToXAPI
    
    transformer = KSTARToXAPI(agent_id="agent_001", agent_name="My Agent")
    statements = transformer.transform_episode(episode)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


__version__ = "0.1"

# Profile IRIs
PROFILE_ID = "https://neolaf.ai/xapi/profiles/kstar"
VERBS = {
    "understood": "https://neolaf.ai/xapi/verbs/understood",
    "planned": "https://neolaf.ai/xapi/verbs/planned",
    "executed": "https://neolaf.ai/xapi/verbs/executed",
    "validated": "https://neolaf.ai/xapi/verbs/validated",
    "reflected": "https://neolaf.ai/xapi/verbs/reflected",
    "forecasted": "https://neolaf.ai/xapi/verbs/forecasted",
    "transitioned": "https://neolaf.ai/xapi/verbs/transitioned",
    "completed_cycle": "https://neolaf.ai/xapi/verbs/completed-cycle",
}
ACTIVITY_TYPES = {
    "episode": "https://neolaf.ai/xapi/activities/kstar-episode",
    "task": "https://neolaf.ai/xapi/activities/kstar-task",
    "stage": "https://neolaf.ai/xapi/activities/kstar-stage",
    "situation": "https://neolaf.ai/xapi/activities/situation-assessment",
    "aar": "https://neolaf.ai/xapi/activities/after-action-review",
}
EXTENSIONS = {
    "knowledge_state": "https://neolaf.ai/xapi/extensions/knowledge-state",
    "situation_vector": "https://neolaf.ai/xapi/extensions/situation-vector",
    "actor_state": "https://neolaf.ai/xapi/extensions/actor-state",
    "domain_state": "https://neolaf.ai/xapi/extensions/domain-state",
    "protocol_state": "https://neolaf.ai/xapi/extensions/protocol-state",
    "now_state": "https://neolaf.ai/xapi/extensions/now-state",
    "task_specification": "https://neolaf.ai/xapi/extensions/task-specification",
    "action_plan": "https://neolaf.ai/xapi/extensions/action-plan",
    "forecast": "https://neolaf.ai/xapi/extensions/forecast",
    "prediction_error": "https://neolaf.ai/xapi/extensions/prediction-error",
    "stage_transition": "https://neolaf.ai/xapi/extensions/stage-transition",
    "aar": "https://neolaf.ai/xapi/extensions/aar",
    "knowledge_delta": "https://neolaf.ai/xapi/extensions/knowledge-delta",
}


@dataclass
class XAPIStatement:
    """xAPI Statement structure."""
    actor: Dict[str, Any]
    verb: Dict[str, Any]
    object: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        stmt = {
            "id": self.id or str(uuid.uuid4()),
            "actor": self.actor,
            "verb": self.verb,
            "object": self.object,
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat()
        }
        if self.result:
            stmt["result"] = self.result
        if self.context:
            stmt["context"] = self.context
        return stmt


class KSTARToXAPI:
    """
    Transform KSTAR episodes and events into xAPI statements.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        home_page: str = "https://neolaf.ai/agents",
        base_iri: str = "https://neolaf.ai"
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.home_page = home_page
        self.base_iri = base_iri
    
    def _build_actor(self) -> Dict[str, Any]:
        """Build xAPI actor (the agent)."""
        return {
            "objectType": "Agent",
            "name": self.agent_name,
            "account": {
                "homePage": self.home_page,
                "name": self.agent_id
            }
        }
    
    def _build_verb(self, verb_key: str) -> Dict[str, Any]:
        """Build xAPI verb."""
        verb_id = VERBS.get(verb_key, VERBS["executed"])
        display = verb_key.replace("_", " ")
        return {
            "id": verb_id,
            "display": {"en": display}
        }
    
    def _build_activity(
        self,
        activity_id: str,
        activity_type: str,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build xAPI activity object."""
        definition = {
            "type": ACTIVITY_TYPES.get(activity_type, activity_type),
            "name": {"en": name}
        }
        if description:
            definition["description"] = {"en": description}
        
        return {
            "objectType": "Activity",
            "id": activity_id,
            "definition": definition
        }
    
    def transform_episode(self, episode: Dict[str, Any]) -> XAPIStatement:
        """
        Transform a KSTAR episode into an xAPI statement.
        
        Args:
            episode: KSTAR episode dict with K, S, T, A, R components
        
        Returns:
            XAPIStatement for the episode execution
        """
        task_id = episode.get("T", {}).get("id", "unknown")
        episode_id = f"{self.base_iri}/episodes/{task_id}_{uuid.uuid4().hex[:8]}"
        task_iri = f"{self.base_iri}/tasks/{task_id}"
        
        # Build context extensions
        context_extensions = {}
        
        if "K" in episode:
            context_extensions[EXTENSIONS["knowledge_state"]] = episode["K"]
        
        if "S" in episode:
            context_extensions[EXTENSIONS["situation_vector"]] = episode["S"]
        
        if "T" in episode:
            context_extensions[EXTENSIONS["task_specification"]] = episode["T"]
        
        if "A" in episode:
            context_extensions[EXTENSIONS["action_plan"]] = episode["A"]
        
        # Build result
        result_data = episode.get("R", {})
        result = {
            "success": result_data.get("success", True),
            "completion": True
        }
        
        result_extensions = {}
        if "prediction_error" in result_data:
            result_extensions[EXTENSIONS["prediction_error"]] = result_data["prediction_error"]
        
        if result_extensions:
            result["extensions"] = result_extensions
        
        return XAPIStatement(
            actor=self._build_actor(),
            verb=self._build_verb("executed"),
            object=self._build_activity(
                episode_id,
                "episode",
                f"KSTAR Episode: {episode.get('T', {}).get('goal', 'Unknown')}",
                "Single KSTAR cognitive cycle episode"
            ),
            result=result,
            context={
                "contextActivities": {
                    "grouping": [
                        self._build_activity(task_iri, "task", episode.get("T", {}).get("goal", "Task"))
                    ]
                },
                "extensions": context_extensions
            },
            timestamp=episode.get("timestamp")
        )
    
    def transform_stage_completion(
        self,
        stage: str,
        task: Dict[str, Any],
        situation: Dict[str, Any],
        from_stage: Optional[str] = None,
        to_stage: Optional[str] = None,
        success: bool = True
    ) -> XAPIStatement:
        """
        Transform a stage completion event into xAPI statement.
        
        Args:
            stage: The completed stage (understand, plan, execute, validate, reflect)
            task: Task specification
            situation: Situation vector
            from_stage: Previous stage (for transition)
            to_stage: Next stage (for transition)
            success: Whether stage completed successfully
        
        Returns:
            XAPIStatement for the stage completion
        """
        task_id = task.get("id", "unknown")
        stage_iri = f"{self.base_iri}/tasks/{task_id}/stages/{stage}"
        task_iri = f"{self.base_iri}/tasks/{task_id}"
        
        # Map stage to verb
        verb_map = {
            "understand": "understood",
            "plan": "planned",
            "execute": "executed",
            "validate": "validated",
            "reflect": "reflected"
        }
        verb_key = verb_map.get(stage, "executed")
        
        result = {
            "success": success,
            "completion": True
        }
        
        if from_stage or to_stage:
            result["extensions"] = {
                EXTENSIONS["stage_transition"]: {
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "reason": f"{stage}_complete"
                }
            }
        
        return XAPIStatement(
            actor=self._build_actor(),
            verb=self._build_verb(verb_key),
            object=self._build_activity(
                stage_iri,
                "stage",
                f"{stage.capitalize()} Stage",
                f"KSTAR {stage} stage completion"
            ),
            result=result,
            context={
                "contextActivities": {
                    "grouping": [
                        self._build_activity(task_iri, "task", task.get("goal", "Task"))
                    ]
                },
                "extensions": {
                    EXTENSIONS["task_specification"]: task,
                    EXTENSIONS["situation_vector"]: situation
                }
            }
        )
    
    def transform_forecast(
        self,
        task: Dict[str, Any],
        action_plan: Dict[str, Any],
        forecast: Dict[str, Any]
    ) -> XAPIStatement:
        """
        Transform a forecast event into xAPI statement.
        
        Args:
            task: Task specification
            action_plan: The action plan being forecasted
            forecast: Forecast data (expected_outcome, success_probability, risks)
        
        Returns:
            XAPIStatement for the forecast
        """
        task_id = task.get("id", "unknown")
        task_iri = f"{self.base_iri}/tasks/{task_id}"
        
        return XAPIStatement(
            actor=self._build_actor(),
            verb=self._build_verb("forecasted"),
            object=self._build_activity(
                task_iri,
                "task",
                task.get("goal", "Task")
            ),
            context={
                "extensions": {
                    EXTENSIONS["action_plan"]: action_plan,
                    EXTENSIONS["forecast"]: forecast
                }
            }
        )
    
    def transform_cycle_completion(
        self,
        task: Dict[str, Any],
        situation: Dict[str, Any],
        aar: Dict[str, Any],
        knowledge_delta: Dict[str, Any],
        success: bool = True,
        duration_seconds: Optional[int] = None,
        score: Optional[float] = None
    ) -> XAPIStatement:
        """
        Transform a full cycle completion into xAPI statement.
        
        Args:
            task: Task specification
            situation: Final situation vector
            aar: After-Action Review data
            knowledge_delta: Knowledge changes from this cycle
            success: Overall cycle success
            duration_seconds: Total duration
            score: Overall score (0-1)
        
        Returns:
            XAPIStatement for the cycle completion
        """
        task_id = task.get("id", "unknown")
        task_iri = f"{self.base_iri}/tasks/{task_id}"
        
        result = {
            "success": success,
            "completion": True,
            "extensions": {
                EXTENSIONS["aar"]: aar,
                EXTENSIONS["knowledge_delta"]: knowledge_delta
            }
        }
        
        if duration_seconds:
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            result["duration"] = f"PT{hours}H{minutes}M{seconds}S" if hours else f"PT{minutes}M{seconds}S"
        
        if score is not None:
            result["score"] = {"scaled": score}
        
        return XAPIStatement(
            actor=self._build_actor(),
            verb=self._build_verb("completed_cycle"),
            object=self._build_activity(
                task_iri,
                "task",
                task.get("goal", "Task")
            ),
            result=result,
            context={
                "extensions": {
                    EXTENSIONS["situation_vector"]: situation
                }
            }
        )
    
    def transform_full_cycle(
        self,
        episodes: List[Dict[str, Any]],
        task: Dict[str, Any],
        situation: Dict[str, Any],
        aar: Optional[Dict[str, Any]] = None
    ) -> List[XAPIStatement]:
        """
        Transform a complete KSTAR cycle into a sequence of xAPI statements.
        
        Args:
            episodes: List of KSTAR episode dicts
            task: Task specification
            situation: Situation vector
            aar: Optional AAR data
        
        Returns:
            List of XAPIStatements representing the full cycle
        """
        statements = []
        
        # Stage completions
        stages = ["understand", "plan"]
        for i, stage in enumerate(stages):
            from_stage = stages[i-1] if i > 0 else None
            to_stage = stages[i+1] if i < len(stages)-1 else "execute"
            statements.append(self.transform_stage_completion(
                stage, task, situation, from_stage, to_stage
            ))
        
        # Episodes (execute stage)
        for episode in episodes:
            # Forecast
            if "A" in episode:
                forecast = episode.get("R", {}).get("forecast", {
                    "expected_outcome": "success",
                    "success_probability": 0.7
                })
                statements.append(self.transform_forecast(task, episode["A"], forecast))
            
            # Episode execution
            statements.append(self.transform_episode(episode))
        
        # Validate and reflect stages
        for stage in ["validate", "reflect"]:
            statements.append(self.transform_stage_completion(
                stage, task, situation
            ))
        
        # Cycle completion
        if aar or episodes:
            aar_data = aar or {
                "what_happened": f"Completed {len(episodes)} episodes",
                "what_worked": [],
                "what_didnt_work": [],
                "lessons_learned": [],
                "recommendations": []
            }
            knowledge_delta = {
                "episodes_added": len(episodes)
            }
            statements.append(self.transform_cycle_completion(
                task, situation, aar_data, knowledge_delta
            ))
        
        return statements


def episode_to_xapi(
    episode: Dict[str, Any],
    agent_id: str = "default_agent",
    agent_name: str = "KSTAR Agent"
) -> Dict[str, Any]:
    """
    Convenience function to transform a single episode.
    
    Args:
        episode: KSTAR episode dict
        agent_id: Agent identifier
        agent_name: Agent display name
    
    Returns:
        xAPI statement as dict
    """
    transformer = KSTARToXAPI(agent_id, agent_name)
    statement = transformer.transform_episode(episode)
    return statement.to_dict()


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("KSTAR to xAPI Transformer Example")
    print("=" * 60)
    
    # Sample KSTAR episode
    episode = {
        "K": {"summary": "Prior python knowledge"},
        "S": {
            "actor_state": {"id": "learner_001", "capabilities": {"python": 0.6}},
            "domain_state": {"objective": "Learn recursion"},
            "protocol_state": {"current_stage": "execute", "agent_role": "companion"},
            "now_state": {"tools_available": ["ide"]}
        },
        "T": {
            "id": "task_001",
            "goal": "Implement recursive factorial",
            "stage": "execute",
            "success_criteria": ["Working implementation"]
        },
        "A": {
            "actions": [{"type": "guide", "description": "Guide implementation"}],
            "is_feasible": True
        },
        "R": {
            "success": True,
            "outputs": {"code": "def factorial(n): ..."},
            "prediction_error": 0.1
        },
        "timestamp": "2025-01-10T10:00:00Z"
    }
    
    # Transform to xAPI
    statement = episode_to_xapi(episode, "agent_lc_001", "Learning Companion")
    print(json.dumps(statement, indent=2))
    
    print("\n" + "=" * 60)
    print("Full Cycle Transformation")
    print("=" * 60)
    
    transformer = KSTARToXAPI("agent_lc_001", "Learning Companion")
    
    task = {"id": "task_001", "goal": "Learn recursion", "stage": "complete"}
    situation = {"actor_state": {"id": "learner_001"}, "protocol_state": {"current_stage": "complete"}}
    aar = {
        "what_happened": "Completed recursion learning",
        "what_worked": ["Visual traces"],
        "what_didnt_work": [],
        "lessons_learned": ["Use visualization for recursion"],
        "recommendations": []
    }
    
    statements = transformer.transform_full_cycle([episode], task, situation, aar)
    print(f"Generated {len(statements)} statements for full cycle")
    print(f"Verbs: {[s.verb['display']['en'] for s in statements]}")
