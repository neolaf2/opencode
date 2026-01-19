#!/usr/bin/env python3
"""
KSTAR Entry Validator
Validates KSTAR JSON entries against the canonical schema.

Usage:
    python validate_kstar.py <input.json>
    python validate_kstar.py --batch <directory>
    cat entry.json | python validate_kstar.py --stdin
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Any

REQUIRED_KSTAR_FIELDS = {"K", "S", "T"}
REQUIRED_A_HAT_FIELDS = {"executor", "plan"}
REQUIRED_R_HAT_FIELDS = {"type", "description", "confidence"}
VALID_A_HAT_ACTIONS = {"recall", "assert", "predict", "execute", "delegate", "simulate", "present"}
VALID_R_HAT_TYPES = {"epistemic", "prediction", "validation"}
VALID_CONTROL_TYPES = {"sequential", "conditional", "loop"}


def validate_kstar_component(kstar: dict) -> list[str]:
    """Validate the (K, S, T) component."""
    errors = []
    for field in REQUIRED_KSTAR_FIELDS:
        if field not in kstar:
            errors.append(f"kstar: missing required field '{field}'")
        elif kstar[field] is None or kstar[field] == "":
            errors.append(f"kstar.{field}: must not be empty")
    return errors


def validate_a_hat(a_hat: dict) -> list[str]:
    """Validate the Â (action plan) component."""
    errors = []
    
    for field in REQUIRED_A_HAT_FIELDS:
        if field not in a_hat:
            errors.append(f"A_hat: missing required field '{field}'")
    
    if "executor" in a_hat:
        if not isinstance(a_hat["executor"], str) or not a_hat["executor"]:
            errors.append("A_hat.executor: must be non-empty string")
    
    if "plan" in a_hat:
        plan = a_hat["plan"]
        # Plan can be markdown string or structured list
        if isinstance(plan, str):
            if not plan.strip():
                errors.append("A_hat.plan: must not be empty")
        elif isinstance(plan, list):
            for i, step in enumerate(plan):
                if not isinstance(step, dict):
                    errors.append(f"A_hat.plan[{i}]: must be object")
                elif "action" in step:
                    if step["action"] not in VALID_A_HAT_ACTIONS:
                        errors.append(f"A_hat.plan[{i}].action: '{step['action']}' not in {VALID_A_HAT_ACTIONS}")
        else:
            errors.append("A_hat.plan: must be string (markdown) or array (structured)")
    
    if "control" in a_hat:
        ctrl = a_hat["control"]
        if isinstance(ctrl, dict) and "type" in ctrl:
            if ctrl["type"] not in VALID_CONTROL_TYPES:
                errors.append(f"A_hat.control.type: '{ctrl['type']}' not in {VALID_CONTROL_TYPES}")
    
    return errors


def validate_r_hat(r_hat: dict) -> list[str]:
    """Validate the R̂ (expected result) component."""
    errors = []
    
    for field in REQUIRED_R_HAT_FIELDS:
        if field not in r_hat:
            errors.append(f"R_hat: missing required field '{field}'")
    
    if "type" in r_hat:
        if r_hat["type"] not in VALID_R_HAT_TYPES:
            errors.append(f"R_hat.type: '{r_hat['type']}' not in {VALID_R_HAT_TYPES}")
    
    if "confidence" in r_hat:
        conf = r_hat["confidence"]
        if not isinstance(conf, (int, float)) or conf < 0.0 or conf > 1.0:
            errors.append("R_hat.confidence: must be number in [0.0, 1.0]")
    
    if "success_criteria" in r_hat:
        criteria = r_hat["success_criteria"]
        if not isinstance(criteria, list):
            errors.append("R_hat.success_criteria: must be array")
    
    return errors


def validate_entry(entry: dict) -> list[str]:
    """Validate a complete KSTAR entry."""
    errors = []
    
    # Check required top-level fields
    if "id" not in entry:
        errors.append("missing required field 'id'")
    
    if "type" not in entry:
        errors.append("missing required field 'type'")
    elif entry["type"] not in {"direct", "procedure"}:
        errors.append(f"type: must be 'direct' or 'procedure', got '{entry['type']}'")
    
    # Validate kstar component
    if "kstar" not in entry:
        errors.append("missing required field 'kstar'")
    else:
        errors.extend(validate_kstar_component(entry["kstar"]))
    
    # Validate A_hat
    if "A_hat" not in entry:
        errors.append("missing required field 'A_hat'")
    else:
        errors.extend(validate_a_hat(entry["A_hat"]))
    
    # Validate R_hat
    if "R_hat" not in entry:
        errors.append("missing required field 'R_hat'")
    else:
        errors.extend(validate_r_hat(entry["R_hat"]))
    
    return errors


def validate_json(data: Any) -> dict:
    """Validate JSON data (single entry or batch)."""
    results = {"valid": True, "entries": []}
    
    entries = data if isinstance(data, list) else [data]
    
    for i, entry in enumerate(entries):
        entry_id = entry.get("id", f"entry_{i}")
        errors = validate_entry(entry)
        
        entry_result = {
            "id": entry_id,
            "valid": len(errors) == 0,
            "errors": errors
        }
        results["entries"].append(entry_result)
        
        if errors:
            results["valid"] = False
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate KSTAR JSON entries")
    parser.add_argument("input", nargs="?", help="Input JSON file")
    parser.add_argument("--batch", metavar="DIR", help="Validate all JSON files in directory")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output errors")
    args = parser.parse_args()
    
    if args.stdin:
        data = json.load(sys.stdin)
        results = validate_json(data)
    elif args.batch:
        batch_dir = Path(args.batch)
        all_results = {"valid": True, "files": []}
        for json_file in batch_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
            file_results = validate_json(data)
            file_results["file"] = str(json_file)
            all_results["files"].append(file_results)
            if not file_results["valid"]:
                all_results["valid"] = False
        results = all_results
    elif args.input:
        with open(args.input) as f:
            data = json.load(f)
        results = validate_json(data)
    else:
        parser.print_help()
        sys.exit(1)
    
    if args.quiet and results["valid"]:
        print("✓ Valid")
    else:
        print(json.dumps(results, indent=2))
    
    sys.exit(0 if results["valid"] else 1)


if __name__ == "__main__":
    main()
