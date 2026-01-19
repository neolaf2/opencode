#!/usr/bin/env python3
"""
Claude Skill Validator

Validates that a compiled skill meets all requirements for execution.

Usage:
    python3 validate_skill.py <skill-path>
    python3 validate_skill.py <skill-path> --strict
    python3 validate_skill.py <skill-path> --json

Checks:
- Required sections present
- Parameters properly typed
- Verification executable/observable
- Failure handling complete
- Lifecycle metadata valid
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional
import yaml


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
    
    def error(self, msg: str):
        self.errors.append(msg)
    
    def warn(self, msg: str):
        self.warnings.append(msg)
    
    def note(self, msg: str):
        self.info.append(msg)
    
    @property
    def valid(self) -> bool:
        return len(self.errors) == 0
    
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info
        }


def validate_frontmatter(frontmatter: dict, result: ValidationResult):
    """Validate YAML frontmatter."""
    # Required fields
    if not frontmatter.get("name"):
        result.error("Missing required field: name")
    elif not re.match(r'^[a-z][a-z0-9-]*$', frontmatter["name"]):
        result.error(f"Invalid skill name format: {frontmatter['name']} (must be lowercase with hyphens)")
    
    if not frontmatter.get("description"):
        result.error("Missing required field: description")
    elif len(frontmatter["description"]) < 50:
        result.warn("Description is very short (recommend 50+ characters)")
    
    # Lifecycle metadata
    lifecycle = frontmatter.get("lifecycle", {})
    if not lifecycle:
        result.error("Missing lifecycle metadata")
    else:
        required_lifecycle = ["state", "source_agent", "derived_from", "confidence", "last_updated", "version"]
        for field in required_lifecycle:
            if field not in lifecycle:
                result.error(f"Missing lifecycle field: {field}")
        
        # Validate state
        valid_states = ["candidate", "validated", "operational", "refined", "quarantined"]
        if lifecycle.get("state") and lifecycle["state"] not in valid_states:
            result.error(f"Invalid lifecycle state: {lifecycle['state']}")
        
        # Validate derived_from
        if lifecycle.get("derived_from"):
            if not isinstance(lifecycle["derived_from"], list):
                result.error("derived_from must be a list")
            elif len(lifecycle["derived_from"]) < 3:
                result.warn(f"Skill derived from only {len(lifecycle['derived_from'])} episodes (recommend 3+)")
        
        # Validate confidence
        conf = lifecycle.get("confidence")
        if conf is not None:
            if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                result.error(f"Confidence must be between 0 and 1, got: {conf}")
        
        # Validate version
        version = lifecycle.get("version")
        if version and not re.match(r'^\d+\.\d+\.\d+$', str(version)):
            result.error(f"Version must be semver format (x.y.z), got: {version}")


def validate_sections(content: str, result: ValidationResult):
    """Validate that all required sections are present."""
    required_sections = [
        ("## Description", "Description section"),
        ("## When to Use", "When to Use section"),
        ("## Inputs", "Inputs section"),
        ("## Steps", "Steps section"),
        ("## Verification", "Verification section"),
        ("## If Something Goes Wrong", "Failure handling section")
    ]
    
    for pattern, name in required_sections:
        if pattern not in content:
            result.error(f"Missing required section: {name}")
    
    # Optional but recommended
    if "## Teaching Notes" not in content:
        result.note("Teaching Notes section not present (optional but recommended)")


def validate_inputs_section(content: str, result: ValidationResult):
    """Validate the Inputs section has proper parameter definitions."""
    # Find inputs section
    inputs_match = re.search(r'## Inputs\s+(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if not inputs_match:
        return
    
    inputs_content = inputs_match.group(1)
    
    # Check for parameter table
    if "| Parameter |" not in inputs_content and "| Name |" not in inputs_content:
        result.warn("Inputs section should contain a parameter table")
        return
    
    # Parse table rows
    rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|', inputs_content)
    if len(rows) < 2:  # Header + at least one parameter
        result.note("No parameters defined in Inputs section")
        return
    
    for row in rows[1:]:  # Skip header
        name, ptype, required, default, desc = [c.strip() for c in row]
        if name.startswith("-"):
            continue  # Skip separator rows
        
        # Validate type
        valid_types = ["string", "number", "boolean", "file", "enum", "object", "array"]
        if ptype.lower() not in valid_types and not ptype.startswith("enum"):
            result.warn(f"Parameter '{name}' has unusual type: {ptype}")
        
        # Check description exists
        if desc in ["-", "", "—"]:
            result.warn(f"Parameter '{name}' has no description")


def validate_steps_section(content: str, result: ValidationResult):
    """Validate the Steps section has ordered, executable steps."""
    steps_match = re.search(r'## Steps\s+(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if not steps_match:
        return
    
    steps_content = steps_match.group(1)
    
    # Check for numbered steps
    steps = re.findall(r'^(\d+)\.\s+(.+)$', steps_content, re.MULTILINE)
    if not steps:
        result.error("Steps section must contain numbered steps (1. 2. 3. ...)")
        return
    
    # Validate ordering
    prev_num = 0
    for num_str, step_text in steps:
        num = int(num_str)
        if num != prev_num + 1:
            result.warn(f"Steps should be sequential: expected {prev_num + 1}, got {num}")
        prev_num = num
        
        # Check for hidden assumptions (heuristic)
        assumption_patterns = ["as mentioned", "obviously", "of course", "you know"]
        for pattern in assumption_patterns:
            if pattern in step_text.lower():
                result.warn(f"Step {num} may contain hidden assumption: '{pattern}'")
    
    result.note(f"Found {len(steps)} steps")


def validate_verification_section(content: str, result: ValidationResult):
    """Validate verification section is executable/observable."""
    verify_match = re.search(r'## Verification\s+(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if not verify_match:
        return
    
    verify_content = verify_match.group(1)
    
    # Check for success indicators
    if "Success confirmed when" not in verify_content and "success" not in verify_content.lower():
        result.warn("Verification section should specify success indicators")
    
    # Check for executable verification (code block)
    if "```" not in verify_content:
        result.note("Verification has no code block (manual verification only)")


def validate_failure_section(content: str, result: ValidationResult):
    """Validate failure handling section is complete."""
    failure_match = re.search(r'## If Something Goes Wrong\s+(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if not failure_match:
        return
    
    failure_content = failure_match.group(1)
    
    required_elements = [
        ("Retry", "retry logic"),
        ("Fallback", "fallback strategy"),
        ("Escalate", "escalation rule")
    ]
    
    for pattern, name in required_elements:
        if pattern.lower() not in failure_content.lower():
            result.error(f"Failure handling missing: {name}")


def validate_skill(skill_path: str, strict: bool = False) -> ValidationResult:
    """Run all validations on a skill."""
    result = ValidationResult()
    skill_dir = Path(skill_path)
    
    # Check directory exists
    if not skill_dir.exists():
        result.error(f"Skill path does not exist: {skill_path}")
        return result
    
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result.error("SKILL.md not found")
        return result
    
    content = skill_md.read_text()
    
    # Extract frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        result.error("No YAML frontmatter found")
    else:
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            validate_frontmatter(frontmatter, result)
        except yaml.YAMLError as e:
            result.error(f"Invalid YAML frontmatter: {e}")
    
    # Validate sections
    validate_sections(content, result)
    validate_inputs_section(content, result)
    validate_steps_section(content, result)
    validate_verification_section(content, result)
    validate_failure_section(content, result)
    
    # Check directory structure
    for subdir in ["scripts", "references", "assets"]:
        if not (skill_dir / subdir).exists():
            result.note(f"Optional directory not present: {subdir}/")
    
    # Strict mode: warnings become errors
    if strict:
        result.errors.extend(result.warnings)
        result.warnings = []
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate a compiled Claude Skill")
    parser.add_argument("skill_path", help="Path to skill directory")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    result = validate_skill(args.skill_path, args.strict)
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Skill Validation: {args.skill_path}")
        print(f"{'='*60}")
        
        if result.errors:
            print(f"\n❌ ERRORS ({len(result.errors)}):")
            for err in result.errors:
                print(f"   • {err}")
        
        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for warn in result.warnings:
                print(f"   • {warn}")
        
        if result.info:
            print(f"\nℹ️  INFO ({len(result.info)}):")
            for info in result.info:
                print(f"   • {info}")
        
        print(f"\n{'='*60}")
        if result.valid:
            print("✅ VALIDATION PASSED")
            print("   Skill is ready for use (state: candidate)")
            print("   To promote: update lifecycle.state to 'validated'")
        else:
            print("❌ VALIDATION FAILED")
            print(f"   Fix {len(result.errors)} error(s) before use")
        print(f"{'='*60}\n")
    
    sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
