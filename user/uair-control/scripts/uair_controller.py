#!/usr/bin/env python3
"""
UAIR Controller - Uncertainty-Aware Iterative Resolution

A meta-control module that orchestrates agent workflows through bounded,
recursive decision loops to construct schema-valid artifacts.

Usage:
    from uair_controller import UAIRController
    
    controller = UAIRController(input_spec)
    result = controller.run()
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from copy import deepcopy


class DecisionType(Enum):
    ASK = "ASK"
    RETRIEVE = "RETRIEVE"
    EXECUTE = "EXECUTE"
    STOP = "STOP"


class Status(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    HALTED = "halted"


@dataclass
class UnmetConstraint:
    path: str
    constraint_type: str
    expected: Any
    actual: Any
    is_required: bool = True
    has_dependents: bool = False
    dependents: List[str] = field(default_factory=list)
    estimated_resolution_cost: int = 1
    has_derivation_rule: bool = False
    
    @property
    def priority_score(self) -> int:
        score = 0
        if self.is_required:
            score += 100
        if self.has_dependents:
            score += 50 * len(self.dependents)
        if self.estimated_resolution_cost < 2:
            score += 30
        if self.has_derivation_rule:
            score += 20
        return score


@dataclass
class Decision:
    type: DecisionType
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UAIROutput:
    decision: Decision
    artifact_delta: Dict[str, Any]
    status: Status
    trace: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": {
                "type": self.decision.type.value,
                "payload": self.decision.payload
            },
            "artifact_delta": self.artifact_delta,
            "status": self.status.value,
            "trace": self.trace
        }


class UAIRController:
    """
    Main UAIR control loop implementation.
    """
    
    def __init__(self, input_spec: Dict[str, Any]):
        self.task = input_spec["task"]
        self.output_schema = input_spec["output_schema"]
        self.artifact = deepcopy(input_spec.get("artifact", {}))
        self.capabilities = input_spec["interaction_capabilities"]
        self.budget = input_spec["budget"]
        self.policies = input_spec["policies"]
        self.available_subskills = input_spec.get("available_subskills", [])
        
        self.global_step = 0
        self.questions_asked = 0
        
        # Hooks for external resolution
        self.retrieval_handler: Optional[Callable] = None
        self.execution_handler: Optional[Callable] = None
    
    def run(self) -> UAIROutput:
        """
        Execute the global UAIR control loop.
        """
        steps_remaining = self.budget["max_global_steps"]
        
        while steps_remaining > 0:
            self.global_step += 1
            
            # Validate artifact
            unmet = self._validate()
            
            if not unmet:
                return self._stop("complete", "confidence_met")
            
            # Select highest priority constraint
            target = self._select_highest_priority(unmet)
            
            # Local step decision
            decision = self._local_step(target)
            
            if decision.type == DecisionType.ASK:
                self.questions_asked += 1
                return UAIROutput(
                    decision=decision,
                    artifact_delta={},
                    status=Status.IN_PROGRESS,
                    trace={
                        "global_step": self.global_step,
                        "reason": "blocking_constraint"
                    }
                )
            
            if decision.type == DecisionType.STOP:
                return UAIROutput(
                    decision=decision,
                    artifact_delta={},
                    status=Status.HALTED,
                    trace={
                        "global_step": self.global_step,
                        "reason": decision.payload.get("reason", "no_resolution_path")
                    }
                )
            
            if decision.type in [DecisionType.RETRIEVE, DecisionType.EXECUTE]:
                # Execute and merge
                delta = self._execute_decision(decision)
                self.artifact = self._merge(self.artifact, delta)
                steps_remaining -= 1
                continue
        
        return self._stop("halted", "max_steps")
    
    def _validate(self) -> List[UnmetConstraint]:
        """Validate artifact against output schema."""
        unmet = []
        
        for field_path in self.output_schema.get("required_fields", []):
            value = self._get_nested(self.artifact, field_path)
            if value is None:
                unmet.append(UnmetConstraint(
                    path=field_path,
                    constraint_type="required",
                    expected="non-null",
                    actual=None
                ))
        
        for path, expr in self.output_schema.get("constraints", {}).items():
            value = self._get_nested(self.artifact, path)
            if not self._evaluate_constraint(value, expr):
                unmet.append(UnmetConstraint(
                    path=path,
                    constraint_type=self._parse_constraint_type(expr),
                    expected=expr,
                    actual=value,
                    is_required=False
                ))
        
        return unmet
    
    def _select_highest_priority(self, unmet: List[UnmetConstraint]) -> UnmetConstraint:
        """Select most important constraint to resolve."""
        return max(unmet, key=lambda c: c.priority_score)
    
    def _local_step(self, target: UnmetConstraint) -> Decision:
        """Single resolution decision."""
        uncertainty = self._derive_uncertainty(target)
        
        # Try RETRIEVE
        if (self.capabilities.get("can_retrieve") and 
            self._can_resolve_by_retrieval(uncertainty)):
            return Decision(
                type=DecisionType.RETRIEVE,
                payload=self._build_retrieval_query(uncertainty)
            )
        
        # Try EXECUTE
        if (self.capabilities.get("can_execute_tools") and 
            self._can_resolve_by_execution(uncertainty)):
            return Decision(
                type=DecisionType.EXECUTE,
                payload=self._select_tool_call(uncertainty)
            )
        
        # Try ASK
        if (self.capabilities.get("can_ask_user") and 
            self.questions_asked < self.budget.get("max_user_questions", 3)):
            return Decision(
                type=DecisionType.ASK,
                payload=self._build_interaction_intent(uncertainty)
            )
        
        # No resolution path
        return Decision(
            type=DecisionType.STOP,
            payload={"reason": "no_resolution_path"}
        )
    
    def _derive_uncertainty(self, target: UnmetConstraint) -> Dict[str, Any]:
        """Analyze what information is missing."""
        return {
            "field_path": target.path,
            "constraint_type": target.constraint_type,
            "expected": target.expected,
            "current_value": target.actual,
            "resolution_hints": {}
        }
    
    def _can_resolve_by_retrieval(self, uncertainty: Dict) -> bool:
        """Check if retrievable from memory/knowledge."""
        # Heuristic: fields ending in _history, _preference, _cached
        path = uncertainty["field_path"]
        return any(hint in path for hint in ["history", "preference", "cached", "prior"])
    
    def _can_resolve_by_execution(self, uncertainty: Dict) -> bool:
        """Check if computable via tool."""
        path = uncertainty["field_path"]
        return any(hint in path for hint in ["score", "analysis", "computed", "derived"])
    
    def _build_retrieval_query(self, uncertainty: Dict) -> Dict:
        """Construct retrieval query."""
        return {
            "query": f"find {uncertainty['field_path']}",
            "source": "memory",
            "filters": {"recency": "30d", "confidence_threshold": 0.7}
        }
    
    def _select_tool_call(self, uncertainty: Dict) -> Dict:
        """Select tool for execution."""
        return {
            "tool_name": "generic_resolver",
            "parameters": {"target": uncertainty["field_path"]},
            "expected_output_field": uncertainty["field_path"]
        }
    
    def _build_interaction_intent(self, uncertainty: Dict) -> Dict:
        """Construct ASK payload."""
        template = "open_text"
        if uncertainty["constraint_type"] == "enum":
            template = "single_choice"
        elif uncertainty["constraint_type"] == "threshold":
            template = "scale"
        
        precision = "coarse" if self.policies.get("fatigue") == "low" else "fine"
        
        return {
            "target_field": uncertainty["field_path"],
            "template": template,
            "precision": precision
        }
    
    def _execute_decision(self, decision: Decision) -> Dict:
        """Execute RETRIEVE or EXECUTE decision."""
        if decision.type == DecisionType.RETRIEVE:
            if self.retrieval_handler:
                return self.retrieval_handler(decision.payload)
            return {}
        
        if decision.type == DecisionType.EXECUTE:
            if self.execution_handler:
                return self.execution_handler(decision.payload)
            return {}
        
        return {}
    
    def _merge(self, artifact: Dict, delta: Dict) -> Dict:
        """Deep merge delta into artifact."""
        result = deepcopy(artifact)
        for key, value in delta.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _stop(self, status: str, reason: str) -> UAIROutput:
        """Create STOP output."""
        return UAIROutput(
            decision=Decision(
                type=DecisionType.STOP,
                payload={"reason": reason, "final_artifact": self.artifact}
            ),
            artifact_delta={},
            status=Status.COMPLETE if status == "complete" else Status.HALTED,
            trace={
                "global_step": self.global_step,
                "reason": reason
            }
        )
    
    def _get_nested(self, obj: Dict, path: str) -> Any:
        """Get nested value by dot-path."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current
    
    def _evaluate_constraint(self, value: Any, expr: str) -> bool:
        """Evaluate constraint expression."""
        if expr == "required":
            return value is not None
        if expr.startswith("length >= "):
            min_len = int(expr.split(">=")[1].strip())
            return value is not None and len(value) >= min_len
        if expr.startswith("confidence >= "):
            threshold = float(expr.split(">=")[1].strip())
            return value is not None and value >= threshold
        return True
    
    def _parse_constraint_type(self, expr: str) -> str:
        """Parse constraint type from expression."""
        if "length" in expr:
            return "length"
        if "confidence" in expr:
            return "threshold"
        if "enum" in expr:
            return "enum"
        return "required"


def uair_control(input_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Functional interface to UAIR controller.
    """
    controller = UAIRController(input_spec)
    result = controller.run()
    return result.to_dict()


if __name__ == "__main__":
    # Example usage
    example_input = {
        "task": {
            "id": "profile_001",
            "description": "Build learner profile",
            "intent": "build_profile"
        },
        "output_schema": {
            "schema_id": "learner_profile_v1",
            "required_fields": ["name", "skill_level"],
            "optional_fields": ["preferences"],
            "constraints": {}
        },
        "artifact": {"name": "Alice"},
        "interaction_capabilities": {
            "can_ask_user": True,
            "can_retrieve": True,
            "can_execute_tools": False
        },
        "budget": {
            "max_global_steps": 5,
            "max_user_questions": 3
        },
        "policies": {
            "privacy": "normal",
            "fatigue": "low"
        },
        "available_subskills": []
    }
    
    result = uair_control(example_input)
    print(json.dumps(result, indent=2))
