#!/usr/bin/env python3
"""
Skill Execution to K-STAR Reverse Mapper

Transforms skill execution traces back into K-STAR episodes,
closing the learning loop.

Usage:
    python3 reverse_map.py --skill-id <id> --execution-trace <trace.json> --output <episode.json>
    python3 reverse_map.py --skill-path <path/to/skill> --execution-trace <trace.json>

Input: Skill metadata + execution trace
Output: K-STAR episode for knowledge integration
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import yaml


def load_skill_metadata(skill_path: str) -> dict:
    """Load skill metadata from SKILL.md frontmatter."""
    skill_md = Path(skill_path) / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")
    
    content = skill_md.read_text()
    
    # Extract YAML frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        raise ValueError("No YAML frontmatter found in SKILL.md")
    
    frontmatter = yaml.safe_load(match.group(1))
    return frontmatter


def calculate_prediction_error(r_hat: dict, r_observed: dict) -> float:
    """Calculate prediction error between expected and observed results."""
    # Simple binary comparison for now
    expected_success = r_hat.get("confidence", 0.5) > 0.5
    actual_success = r_observed.get("success", False)
    
    if expected_success == actual_success:
        return 0.0
    else:
        return abs(r_hat.get("confidence", 0.5) - (1.0 if actual_success else 0.0))


def bayesian_update(prior: float, evidence_success: bool, evidence_weight: float = 0.1) -> float:
    """Simple Bayesian update of confidence."""
    # Likelihood ratio (simple model)
    if evidence_success:
        likelihood = 0.9  # P(success | skill works)
        likelihood_neg = 0.2  # P(success | skill doesn't work)
    else:
        likelihood = 0.1  # P(failure | skill works)
        likelihood_neg = 0.8  # P(failure | skill doesn't work)
    
    # Posterior calculation
    posterior = (likelihood * prior) / (
        likelihood * prior + likelihood_neg * (1 - prior)
    )
    
    # Dampen update by evidence weight
    return prior + evidence_weight * (posterior - prior)


def reverse_map(skill_metadata: dict, execution_trace: dict, agent_id: str = "executor") -> dict:
    """
    Map skill execution back to K-STAR episode format.
    
    Args:
        skill_metadata: Skill's YAML frontmatter + lifecycle info
        execution_trace: Execution trace with inputs, outputs, steps executed
        agent_id: Identity of executing agent
    
    Returns:
        K-STAR episode structure
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    skill_id = skill_metadata.get("name", "unknown")
    version = skill_metadata.get("lifecycle", {}).get("version", "0.0.0")
    
    # Extract execution details
    inputs_bound = execution_trace.get("inputs", {})
    steps_executed = execution_trace.get("steps_executed", [])
    result = execution_trace.get("result", {})
    verification_outcome = execution_trace.get("verification", {})
    duration_ms = execution_trace.get("duration_ms", 0)
    
    # Build K-STAR components
    kstar = {
        "K": {
            "refs": [skill_id],
            "tools": list(set(
                step.get("tool") for step in steps_executed if step.get("tool")
            )),
            "assumptions": inputs_bound
        },
        "S": {
            "trigger": f"Skill invocation: {skill_id}",
            "context": execution_trace.get("context", "Skill execution context"),
            "constraints": execution_trace.get("constraints", [])
        },
        "T": {
            "goal": skill_metadata.get("description", "Execute compiled skill"),
            "intent": execution_trace.get("intent", "Apply learned procedure"),
            "scope": execution_trace.get("scope", "single_execution")
        }
    }
    
    # Action plan (from skill) vs observed (actual execution)
    a_hat = {
        "executor": "skill_executor",
        "plan": f"Execute skill {skill_id} v{version}",
        "control": {"type": "sequential"}
    }
    
    a_observed = {
        "steps_executed": [
            {
                "step": i + 1,
                "action": step.get("action", ""),
                "tool_calls": step.get("tool_calls", []),
                "duration_ms": step.get("duration_ms", 0),
                "output": step.get("output")
            }
            for i, step in enumerate(steps_executed)
        ],
        "parameters_bound": inputs_bound,
        "total_duration_ms": duration_ms
    }
    
    # Expected result (from skill confidence)
    prior_confidence = skill_metadata.get("lifecycle", {}).get("confidence", 0.5)
    r_hat = {
        "type": "validation",
        "description": "Expected outcome based on skill confidence",
        "success_criteria": skill_metadata.get("verification", {}).get("success_indicators", []),
        "confidence": prior_confidence
    }
    
    # Observed result
    success = result.get("success", verification_outcome.get("passed", False))
    r_observed = {
        "success": success,
        "verification_outcome": {
            "checks_passed": verification_outcome.get("passed_checks", []),
            "checks_failed": verification_outcome.get("failed_checks", []),
            "artifacts_produced": result.get("artifacts", [])
        },
        "output": result.get("output"),
        "error": result.get("error")
    }
    
    # Calculate deltas
    prediction_error = calculate_prediction_error(r_hat, r_observed)
    posterior_confidence = bayesian_update(prior_confidence, success)
    
    r_observed["delta_from_expected"] = {
        "prediction_error": round(prediction_error, 4),
        "unexpected_outcomes": result.get("unexpected", [])
    }
    
    # Build complete episode
    episode = {
        "id": f"kstar_exec_{skill_id}_{timestamp.replace(':', '-').replace('.', '-')}",
        "type": "execution_trace",
        "source_skill": {
            "skill_id": skill_id,
            "version": version
        },
        "kstar": kstar,
        "A_hat": a_hat,
        "A_observed": a_observed,
        "R_hat": r_hat,
        "R_observed": r_observed,
        "confidence_update": {
            "prior": round(prior_confidence, 4),
            "posterior": round(posterior_confidence, 4),
            "evidence_weight": 0.1
        },
        "timestamp": timestamp,
        "agent_identity": agent_id
    }
    
    return episode


def main():
    parser = argparse.ArgumentParser(description="Map skill execution to K-STAR episode")
    parser.add_argument("--skill-path", help="Path to skill directory")
    parser.add_argument("--skill-metadata", help="Path to skill metadata JSON (alternative to --skill-path)")
    parser.add_argument("--execution-trace", required=True, help="Path to execution trace JSON")
    parser.add_argument("--output", help="Output path for K-STAR episode (default: stdout)")
    parser.add_argument("--agent-id", default="executor", help="Executing agent ID")
    
    args = parser.parse_args()
    
    # Load skill metadata
    if args.skill_path:
        skill_metadata = load_skill_metadata(args.skill_path)
        print(f"📥 Loaded skill metadata from: {args.skill_path}", file=sys.stderr)
    elif args.skill_metadata:
        with open(args.skill_metadata) as f:
            skill_metadata = json.load(f)
        print(f"📥 Loaded skill metadata from: {args.skill_metadata}", file=sys.stderr)
    else:
        print("❌ Error: Either --skill-path or --skill-metadata required", file=sys.stderr)
        sys.exit(1)
    
    # Load execution trace
    with open(args.execution_trace) as f:
        execution_trace = json.load(f)
    print(f"📥 Loaded execution trace: {args.execution_trace}", file=sys.stderr)
    
    # Generate K-STAR episode
    episode = reverse_map(skill_metadata, execution_trace, args.agent_id)
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(episode, f, indent=2)
        print(f"✅ K-STAR episode written to: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(episode, indent=2))
    
    # Summary
    print(f"\n📊 Episode Summary:", file=sys.stderr)
    print(f"   ID: {episode['id']}", file=sys.stderr)
    print(f"   Skill: {episode['source_skill']['skill_id']} v{episode['source_skill']['version']}", file=sys.stderr)
    print(f"   Success: {episode['R_observed']['success']}", file=sys.stderr)
    print(f"   Prediction Error: {episode['R_observed']['delta_from_expected']['prediction_error']}", file=sys.stderr)
    print(f"   Confidence: {episode['confidence_update']['prior']} → {episode['confidence_update']['posterior']}", file=sys.stderr)


if __name__ == "__main__":
    main()
