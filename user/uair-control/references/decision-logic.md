# UAIR Decision Logic Reference

## Resolution Strategy Priority

When resolving an unmet constraint, UAIR attempts resolution in this order:

```
1. RETRIEVE (if can_retrieve and retrievable uncertainty)
2. EXECUTE (if can_execute_tools and executable uncertainty)
3. ASK (if can_ask_user and within question budget)
4. STOP (no resolution path)
```

This priority minimizes user interaction fatigue.

## Uncertainty Derivation

```python
def derive_uncertainty(target_constraint, artifact):
    """
    Analyze what information is missing and how to resolve it.
    """
    return {
        "field_path": target_constraint.path,
        "constraint_type": target_constraint.type,
        "expected": target_constraint.expected,
        "current_value": get_nested(artifact, target_constraint.path),
        "resolution_hints": infer_resolution_hints(target_constraint)
    }
```

## Retrieval Resolution

```python
def can_resolve_by_retrieval(uncertainty):
    """
    Check if uncertainty can be resolved via memory/knowledge lookup.
    """
    retrievable_types = ["historical", "preference", "cached", "derived"]
    return uncertainty.get("resolution_hints", {}).get("source") in retrievable_types

def build_retrieval_query(uncertainty):
    """
    Construct retrieval query from uncertainty.
    """
    return {
        "query": f"find {uncertainty['field_path']} for current user",
        "source": uncertainty.get("resolution_hints", {}).get("source", "memory"),
        "filters": {
            "recency": "30d",
            "confidence_threshold": 0.7
        }
    }
```

## Execution Resolution

```python
def can_resolve_by_execution(uncertainty):
    """
    Check if uncertainty can be resolved via tool execution.
    """
    executable_types = ["computed", "analyzed", "scored", "validated"]
    return uncertainty.get("resolution_hints", {}).get("derivation") in executable_types

def select_tool_call(uncertainty):
    """
    Select appropriate tool to resolve uncertainty.
    """
    tool_mapping = {
        "score": "compute_score",
        "analysis": "run_analysis",
        "code_quality": "code_analyzer",
        "sentiment": "sentiment_analyzer"
    }
    
    return {
        "tool_name": infer_tool(uncertainty, tool_mapping),
        "parameters": build_tool_params(uncertainty),
        "expected_output_field": uncertainty["field_path"]
    }
```

## Ask Resolution

```python
def build_interaction_intent(uncertainty, policies):
    """
    Construct user interaction intent.
    """
    template = select_template(uncertainty, policies)
    
    intent = {
        "target_field": uncertainty["field_path"],
        "template": template["type"],
        "precision": "coarse" if policies["fatigue"] == "low" else "fine"
    }
    
    if template["type"] == "single_choice":
        intent["choices"] = generate_choices(uncertainty)
    elif template["type"] == "scale":
        intent["min"] = 1
        intent["max"] = 5
        intent["labels"] = ["Beginner", "Expert"]
    
    return intent


def select_template(uncertainty, policies):
    """
    Choose interaction template based on constraint and policy.
    """
    templates = {
        "enum": {"type": "single_choice"},
        "threshold": {"type": "scale"},
        "required_string": {"type": "open_text"},
        "required_bool": {"type": "confirmation"},
        "multi_value": {"type": "multi_choice"}
    }
    
    # Apply fatigue policy adjustments
    if policies["fatigue"] == "low":
        if templates.get(uncertainty["constraint_type"], {}).get("type") == "open_text":
            return {"type": "single_choice"}  # Downgrade to choice
    
    return templates.get(uncertainty["constraint_type"], {"type": "open_text"})
```

## Constraint Priority Ordering

```python
def select_highest_priority(unmet_constraints):
    """
    Select most important constraint to resolve next.
    """
    def priority_score(constraint):
        scores = {
            "blocking": 100,      # Required, blocks progress
            "high_impact": 50,    # Affects multiple downstream fields
            "cheap_to_ask": 30,   # Single choice vs open text
            "derivable": 20       # Can be computed from existing
        }
        
        score = 0
        if constraint.is_required:
            score += scores["blocking"]
        if constraint.has_dependents:
            score += scores["high_impact"] * len(constraint.dependents)
        if constraint.estimated_resolution_cost < 2:
            score += scores["cheap_to_ask"]
        if constraint.has_derivation_rule:
            score += scores["derivable"]
        
        return score
    
    return max(unmet_constraints, key=priority_score)
```

## Artifact Merging

```python
def merge(artifact, delta):
    """
    Deep merge artifact delta into artifact.
    Handles nested paths and array appends.
    """
    result = deep_copy(artifact)
    
    for path, value in flatten_paths(delta):
        if path.endswith("[]"):
            # Array append
            base_path = path[:-2]
            current = get_nested(result, base_path) or []
            current.append(value)
            set_nested(result, base_path, current)
        else:
            # Direct set
            set_nested(result, path, value)
    
    return result
```

## Validation Logic

```python
def validate(artifact, output_schema):
    """
    Validate artifact against schema constraints.
    Returns list of unmet constraints.
    """
    unmet = []
    
    # Check required fields
    for field in output_schema["required_fields"]:
        value = get_nested(artifact, field)
        if value is None:
            unmet.append(UnmetConstraint(
                path=field,
                type="required",
                expected="non-null",
                actual=None
            ))
    
    # Check custom constraints
    for path, expr in output_schema.get("constraints", {}).items():
        value = get_nested(artifact, path)
        if not evaluate_constraint(value, expr):
            unmet.append(UnmetConstraint(
                path=path,
                type=parse_constraint_type(expr),
                expected=expr,
                actual=value
            ))
    
    return unmet
```
