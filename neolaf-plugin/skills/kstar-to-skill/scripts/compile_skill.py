#!/usr/bin/env python3
"""
K-STAR to Claude Skill Compiler

Transforms K-STAR memory entries into executable Claude Skills.

Usage:
    python3 compile_skill.py --episodes <episodes.json> --output <skill-dir>
    python3 compile_skill.py --episodes <episodes.json> --output <skill-dir> --name <skill-name>

Input: JSON array of K-STAR episodes with shared (S,T) pattern
Output: Complete Claude Skill directory structure
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def stable_hash(s: str, t: str, agent_id: str) -> str:
    """Generate stable skill ID from situation, task, and agent."""
    content = f"{s}:{t}:{agent_id}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def canonical_situation(s: dict) -> str:
    """Extract canonical trigger pattern from situation."""
    trigger = s.get("trigger", "")
    context = s.get("context", "")
    return f"{trigger}|{context}"


def canonical_task(t: dict) -> str:
    """Extract canonical goal from task."""
    return t.get("goal", "")


def infer_type(values: list) -> str:
    """Infer parameter type from observed values."""
    if all(isinstance(v, bool) for v in values if v is not None):
        return "boolean"
    if all(isinstance(v, (int, float)) for v in values if v is not None):
        return "number"
    if all(isinstance(v, str) for v in values if v is not None):
        # Check for file paths
        if any(v.startswith("/") or v.endswith((".py", ".json", ".md")) for v in values if v):
            return "file"
        # Check for enum (limited unique values)
        unique = set(v for v in values if v)
        if len(unique) <= 5 and len(unique) < len(values) * 0.5:
            return f"enum"
        return "string"
    return "string"


def extract_parameters(episodes: list[dict]) -> list[dict]:
    """Extract parameters from varying values across episodes."""
    # Collect all values for each path in action plans
    value_patterns = defaultdict(list)
    
    for ep in episodes:
        a_hat = ep.get("A_hat", {}).get("plan", "")
        # Find potential parameter values (quoted strings, numbers, paths)
        literals = re.findall(r'"([^"]+)"|\'([^\']+)\'|(/[\w/.-]+)', a_hat)
        for match in literals:
            val = next(v for v in match if v)
            value_patterns[val].append(val)
    
    # Also check for explicit parameters in K
    for ep in episodes:
        k = ep.get("kstar", {}).get("K", {})
        for key, val in k.get("assumptions", {}).items() if isinstance(k.get("assumptions"), dict) else []:
            value_patterns[key].append(val)
    
    # Identify varying values as parameters
    parameters = []
    param_counter = Counter()
    
    for ep in episodes:
        a_hat = ep.get("A_hat", {}).get("plan", "")
        # Look for patterns that vary
        for pattern, values in value_patterns.items():
            if len(set(values)) > 1:  # Varies across episodes
                param_name = f"param_{param_counter['count']}"
                param_counter['count'] += 1
                
                params = {
                    "name": param_name,
                    "type": infer_type(values),
                    "required": all(v is not None for v in values),
                    "default": Counter(values).most_common(1)[0][0] if values else None,
                    "description": f"Derived from varying values: {set(values)}"
                }
                parameters.append(params)
    
    return parameters[:10]  # Limit parameters


def extract_applicability(episodes: list[dict]) -> dict:
    """Extract applicability conditions from episodes."""
    successes = [e for e in episodes if e.get("R_hat", {}).get("confidence", 0) > 0.5 or 
                 e.get("R_observed", {}).get("success", False)]
    failures = [e for e in episodes if not e.get("R_observed", {}).get("success", True)]
    
    # Extract common situation features from successes
    hard_guards = []
    soft_guards = []
    exclusions = []
    
    if successes:
        # Find common triggers
        triggers = [e.get("kstar", {}).get("S", {}).get("trigger", "") for e in successes]
        common_trigger = Counter(triggers).most_common(1)
        if common_trigger:
            hard_guards.append(f"Situation matches: {common_trigger[0][0]}")
        
        # Find common tool requirements
        tools = []
        for e in successes:
            tools.extend(e.get("kstar", {}).get("K", {}).get("tools", []))
        if tools:
            common_tools = [t for t, c in Counter(tools).items() if c > len(successes) * 0.5]
            if common_tools:
                hard_guards.append(f"Tools available: {', '.join(common_tools)}")
    
    if failures:
        # Extract failure patterns as exclusions
        for f in failures:
            diag = f.get("failure_diagnostics", {})
            if diag:
                exclusions.append(f"Avoid when: {diag.get('cause', 'unknown failure pattern')}")
    
    return {
        "hard_guards": hard_guards or ["Situation matches compiled pattern"],
        "soft_guards": soft_guards,
        "exclusions": exclusions or ["No known exclusions"]
    }


def generalize_steps(episodes: list[dict]) -> list[dict]:
    """Generalize action plans into parameterized steps."""
    steps = []
    
    # Collect all action plans
    plans = [e.get("A_hat", {}).get("plan", "") for e in episodes]
    
    # Find common structure (simplified - real impl would use diff/alignment)
    if plans:
        # Use first plan as template
        template = plans[0]
        
        # Split into steps
        step_lines = [l.strip() for l in template.split("\n") if l.strip() and 
                      (l.strip().startswith(tuple("0123456789")) or l.strip().startswith("-"))]
        
        for i, line in enumerate(step_lines, 1):
            step = {
                "order": i,
                "action": line.lstrip("0123456789.-) "),
                "tool_intent": "execute"  # Default
            }
            
            # Detect code blocks
            if "```" in template:
                code_match = re.search(r'```(\w+)?\n(.*?)```', template, re.DOTALL)
                if code_match:
                    step["code_block"] = {
                        "language": code_match.group(1) or "python",
                        "code": code_match.group(2).strip()
                    }
            
            steps.append(step)
    
    return steps or [{"order": 1, "action": "Execute compiled procedure", "tool_intent": "execute"}]


def extract_verification(episodes: list[dict]) -> dict:
    """Extract verification criteria from episodes."""
    success_indicators = []
    artifacts = []
    
    for ep in episodes:
        r_hat = ep.get("R_hat", {})
        success_criteria = r_hat.get("success_criteria", [])
        success_indicators.extend(success_criteria)
        
        # Check for artifacts
        r_obs = ep.get("R_observed", {})
        if "artifacts_produced" in r_obs.get("verification_outcome", {}):
            artifacts.extend(r_obs["verification_outcome"]["artifacts_produced"])
    
    return {
        "success_indicators": list(set(success_indicators)) or ["Task completed successfully"],
        "artifacts": list(set(artifacts)),
        "method": {
            "type": "observable",
            "command": "# Manual verification required",
            "expected_output": "Success criteria met"
        }
    }


def extract_failure_handling(episodes: list[dict]) -> dict:
    """Extract failure handling from failed episodes."""
    known_errors = []
    
    failures = [e for e in episodes if not e.get("R_observed", {}).get("success", True)]
    
    for f in failures:
        diag = f.get("failure_diagnostics", {})
        if diag:
            known_errors.append({
                "error": diag.get("error_type", "Unknown error"),
                "cause": diag.get("cause", "Unknown cause"),
                "resolution": diag.get("resolution", "Retry or escalate")
            })
    
    return {
        "known_errors": known_errors or [{"error": "No known errors", "cause": "-", "resolution": "-"}],
        "retry": {"conditions": "Transient failure detected", "max_attempts": 3},
        "fallback": {"condition": "Retry limit exceeded", "strategy": "Use alternative approach or skip"},
        "escalation": {"target": "human operator", "threshold": "After fallback exhausted"}
    }


def generate_skill_markdown(skill_data: dict) -> str:
    """Generate SKILL.md content from compiled skill data."""
    metadata = skill_data["metadata"]
    sections = skill_data["sections"]
    
    # Build YAML frontmatter
    frontmatter = f'''---
name: {metadata["name"]}
description: >
  {metadata["description"]}
lifecycle:
  state: {metadata["lifecycle"]["state"]}
  source_agent: {metadata["lifecycle"]["source_agent"]}
  derived_from: {json.dumps(metadata["lifecycle"]["derived_from"])}
  confidence: {metadata["lifecycle"]["confidence"]}
  last_updated: {metadata["lifecycle"]["last_updated"]}
  version: {metadata["lifecycle"]["version"]}
---'''

    # Build sections
    desc = sections["description"]
    when = sections["when_to_use"]
    inputs = sections["inputs"]
    steps = sections["steps"]
    verify = sections["verification"]
    failure = sections["failure_handling"]
    teaching = sections.get("teaching_notes", {})
    
    md = f'''{frontmatter}

# {metadata["name"].replace("-", " ").title()}

{desc.get("problem_class", "Compiled skill from K-STAR episodes.")}

## Description

**Problem class**: {desc.get("problem_class", "General procedure")}

**Approach**: {desc.get("approach", "Follow compiled steps")}

**Why it works**: {desc.get("rationale", "Derived from successful episodes")}

## When to Use This Skill

**Required conditions (hard guards)**:
'''
    
    for guard in when.get("hard_guards", []):
        md += f"- {guard}\n"
    
    if when.get("soft_guards"):
        md += "\n**Preferred conditions (soft guards)**:\n"
        for guard in when["soft_guards"]:
            md += f"- {guard}\n"
    
    md += "\n**Do NOT apply when**:\n"
    for excl in when.get("exclusions", []):
        md += f"- {excl}\n"
    
    md += "\n## Inputs\n\n"
    md += "| Parameter | Type | Required | Default | Description |\n"
    md += "|-----------|------|----------|---------|-------------|\n"
    for inp in inputs:
        default = inp.get("default", "-") or "-"
        md += f"| {inp['name']} | {inp['type']} | {'yes' if inp.get('required') else 'no'} | {default} | {inp.get('description', '-')} |\n"
    
    md += "\n## Steps\n\n"
    for step in steps:
        md += f"{step['order']}. {step['action']}\n"
        if step.get("code_block"):
            md += f"   ```{step['code_block'].get('language', 'python')}\n"
            md += f"   {step['code_block']['code']}\n"
            md += "   ```\n"
    
    md += "\n## Verification\n\n"
    md += "**Success confirmed when**:\n"
    for indicator in verify.get("success_indicators", []):
        md += f"- {indicator}\n"
    
    if verify.get("artifacts"):
        md += "\n**Artifacts produced**:\n"
        for artifact in verify["artifacts"]:
            md += f"- `{artifact}`\n"
    
    method = verify.get("method", {})
    if method.get("command"):
        md += f"\n**Verification command**:\n```bash\n{method['command']}\n```\n"
    
    md += "\n## If Something Goes Wrong\n\n"
    md += "| Error | Cause | Resolution |\n"
    md += "|-------|-------|------------|\n"
    for err in failure.get("known_errors", []):
        md += f"| {err['error']} | {err['cause']} | {err['resolution']} |\n"
    
    retry = failure.get("retry", {})
    md += f"\n**Retry**: {retry.get('conditions', 'On transient failure')} (max {retry.get('max_attempts', 3)} attempts)\n"
    
    fb = failure.get("fallback", {})
    md += f"\n**Fallback**: When {fb.get('condition', 'retry fails')}, {fb.get('strategy', 'escalate')}\n"
    
    esc = failure.get("escalation", {})
    md += f"\n**Escalate to**: {esc.get('target', 'human operator')} when {esc.get('threshold', 'fallback exhausted')}\n"
    
    if teaching:
        md += "\n## Teaching Notes\n\n"
        if teaching.get("step_rationale"):
            md += "**Why each step matters**:\n"
            for step, rationale in teaching["step_rationale"].items():
                md += f"- Step {step}: {rationale}\n"
        if teaching.get("common_struggles"):
            md += "\n**Common struggles**:\n"
            for struggle in teaching["common_struggles"]:
                md += f"- {struggle}\n"
        if teaching.get("misconceptions"):
            md += "\n**Misconceptions to address**:\n"
            for misc in teaching["misconceptions"]:
                md += f"- {misc.get('incorrect', '?')} → {misc.get('correct', '?')}\n"
    
    return md


def compile_skill(episodes: list[dict], skill_name: str = None, agent_id: str = "compiler") -> dict:
    """Compile K-STAR episodes into a Claude Skill structure."""
    
    if len(episodes) < 3:
        raise ValueError(f"Minimum 3 episodes required, got {len(episodes)}")
    
    # Extract canonical patterns
    first_ep = episodes[0]
    s = first_ep.get("kstar", {}).get("S", {})
    t = first_ep.get("kstar", {}).get("T", {})
    
    # Generate skill ID
    skill_id = stable_hash(
        canonical_situation(s),
        canonical_task(t),
        agent_id
    )
    
    name = skill_name or f"compiled-{skill_id}"
    
    # Extract all components
    parameters = extract_parameters(episodes)
    applicability = extract_applicability(episodes)
    steps = generalize_steps(episodes)
    verification = extract_verification(episodes)
    failure_handling = extract_failure_handling(episodes)
    
    # Calculate confidence from episode success rate
    successes = sum(1 for e in episodes if e.get("R_observed", {}).get("success", False))
    confidence = successes / len(episodes)
    
    # Build skill structure
    skill_data = {
        "metadata": {
            "name": name,
            "description": f"Compiled skill for: {t.get('goal', 'Unknown goal')}. " +
                          f"Triggers when: {s.get('trigger', 'matching situation')}",
            "lifecycle": {
                "state": "candidate",
                "source_agent": agent_id,
                "derived_from": [e.get("id", f"episode_{i}") for i, e in enumerate(episodes)],
                "confidence": round(confidence, 2),
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0"
            }
        },
        "sections": {
            "description": {
                "problem_class": t.get("goal", "General procedure"),
                "approach": t.get("intent", "Follow compiled steps"),
                "rationale": f"Derived from {len(episodes)} successful episodes"
            },
            "when_to_use": applicability,
            "inputs": parameters,
            "steps": steps,
            "verification": verification,
            "failure_handling": failure_handling,
            "teaching_notes": {
                "step_rationale": {},
                "common_struggles": [],
                "misconceptions": []
            }
        },
        "resources": {
            "scripts": [],
            "references": [],
            "assets": []
        }
    }
    
    return skill_data


def main():
    parser = argparse.ArgumentParser(description="Compile K-STAR episodes into Claude Skill")
    parser.add_argument("--episodes", required=True, help="Path to episodes JSON file")
    parser.add_argument("--output", required=True, help="Output directory for skill")
    parser.add_argument("--name", help="Skill name (optional)")
    parser.add_argument("--agent-id", default="compiler", help="Source agent ID")
    
    args = parser.parse_args()
    
    # Load episodes
    with open(args.episodes) as f:
        episodes = json.load(f)
    
    if not isinstance(episodes, list):
        episodes = [episodes]
    
    print(f"📥 Loaded {len(episodes)} episodes")
    
    # Compile skill
    try:
        skill_data = compile_skill(episodes, args.name, args.agent_id)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print(f"🔧 Compiled skill: {skill_data['metadata']['name']}")
    print(f"   Confidence: {skill_data['metadata']['lifecycle']['confidence']}")
    print(f"   Parameters: {len(skill_data['sections']['inputs'])}")
    print(f"   Steps: {len(skill_data['sections']['steps'])}")
    
    # Create output directory
    output_dir = Path(args.output) / skill_data['metadata']['name']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate SKILL.md
    skill_md = generate_skill_markdown(skill_data)
    (output_dir / "SKILL.md").write_text(skill_md)
    print(f"✅ Generated: {output_dir / 'SKILL.md'}")
    
    # Create subdirectories
    (output_dir / "scripts").mkdir(exist_ok=True)
    (output_dir / "references").mkdir(exist_ok=True)
    (output_dir / "assets").mkdir(exist_ok=True)
    
    # Save compilation metadata
    (output_dir / "references" / "compilation-metadata.json").write_text(
        json.dumps(skill_data, indent=2)
    )
    print(f"✅ Generated: {output_dir / 'references' / 'compilation-metadata.json'}")
    
    print(f"\n✅ Skill compiled successfully to: {output_dir}")
    print(f"   State: {skill_data['metadata']['lifecycle']['state']}")
    print(f"   Next: Validate with validate_skill.py, then promote to 'validated'")


if __name__ == "__main__":
    main()
