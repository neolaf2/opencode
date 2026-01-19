# UAIR Schemas Reference

## Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UAIRInput",
  "type": "object",
  "required": ["task", "output_schema", "artifact", "interaction_capabilities", "budget", "policies"],
  "properties": {
    "task": {
      "type": "object",
      "required": ["id", "description", "intent"],
      "properties": {
        "id": { "type": "string" },
        "description": { "type": "string" },
        "intent": {
          "type": "string",
          "enum": ["build_profile", "assess", "configure", "diagnose", "other"]
        }
      }
    },
    "output_schema": {
      "type": "object",
      "required": ["schema_id", "required_fields"],
      "properties": {
        "schema_id": { "type": "string" },
        "required_fields": {
          "type": "array",
          "items": { "type": "string" }
        },
        "optional_fields": {
          "type": "array",
          "items": { "type": "string" }
        },
        "constraints": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      }
    },
    "artifact": {
      "type": "object",
      "additionalProperties": true,
      "description": "Partial artifact being constructed"
    },
    "interaction_capabilities": {
      "type": "object",
      "required": ["can_ask_user", "can_retrieve", "can_execute_tools"],
      "properties": {
        "can_ask_user": { "type": "boolean" },
        "can_retrieve": { "type": "boolean" },
        "can_execute_tools": { "type": "boolean" }
      }
    },
    "budget": {
      "type": "object",
      "required": ["max_global_steps", "max_user_questions"],
      "properties": {
        "max_global_steps": { "type": "integer", "minimum": 1 },
        "max_user_questions": { "type": "integer", "minimum": 0 }
      }
    },
    "policies": {
      "type": "object",
      "required": ["privacy", "fatigue"],
      "properties": {
        "privacy": { "type": "string", "enum": ["strict", "normal"] },
        "fatigue": { "type": "string", "enum": ["low", "medium", "high"] }
      }
    },
    "available_subskills": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

## Output Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UAIROutput",
  "type": "object",
  "required": ["decision", "artifact_delta", "status", "trace"],
  "properties": {
    "decision": {
      "type": "object",
      "required": ["type", "payload"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["ASK", "RETRIEVE", "EXECUTE", "STOP"]
        },
        "payload": {
          "type": "object",
          "additionalProperties": true
        }
      }
    },
    "artifact_delta": {
      "type": "object",
      "additionalProperties": true
    },
    "status": {
      "type": "string",
      "enum": ["in_progress", "complete", "halted"]
    },
    "trace": {
      "type": "object",
      "required": ["global_step", "reason"],
      "properties": {
        "global_step": { "type": "integer", "minimum": 0 },
        "reason": {
          "type": "string",
          "enum": ["blocking_constraint", "max_steps", "confidence_met", "no_resolution_path", "budget_exhausted"]
        }
      }
    }
  }
}
```

## Decision Payloads

### ASK Payload

```json
{
  "target_field": "learner_profile.skill_vector.python",
  "template": "single_choice | multi_choice | scale | open_text | confirmation",
  "choices": ["none", "syntax", "scripts", "data", "backend"],
  "precision": "coarse | fine",
  "context": "optional context for rendering"
}
```

### RETRIEVE Payload

```json
{
  "query": "user python experience history",
  "source": "memory | knowledge_base | external",
  "filters": {
    "recency": "30d",
    "confidence_threshold": 0.7
  }
}
```

### EXECUTE Payload

```json
{
  "tool_name": "code_analyzer",
  "parameters": {
    "file_path": "/user/projects/main.py",
    "analysis_type": "complexity"
  },
  "expected_output_field": "learner_profile.code_samples.complexity"
}
```

### STOP Payload

```json
{
  "reason": "complete | halted | no_resolution_path",
  "final_artifact": { },
  "validation_result": {
    "valid": true,
    "unmet_constraints": []
  }
}
```

## Constraint Expression Syntax

| Expression | Meaning |
|------------|---------|
| `required` | Field must exist and be non-null |
| `confidence >= 0.7` | Numeric threshold |
| `length >= 1` | Array/string length |
| `enum: [a, b, c]` | Value must be in set |
| `pattern: regex` | String pattern match |
