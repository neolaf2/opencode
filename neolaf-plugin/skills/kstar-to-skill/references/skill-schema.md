# Claude Skill Output Schema

Canonical schema for skills generated from K-STAR episodes.

## SKILL.md Structure

```markdown
---
name: {skill_id}
description: >
  {generalized_description}
  {trigger_patterns}
lifecycle:
  state: {candidate|validated|operational|refined|quarantined}
  source_agent: {agent_id}
  derived_from: [{episode_ids}]
  confidence: {0.0-1.0}
  last_updated: {ISO8601}
  version: {semver}
---

# {Skill Title}

{Brief overview - what structural pattern this skill represents}

## Description

{Detailed explanation of:
- Problem class this skill solves
- Why the approach works (causal reasoning)
- Structural pattern recognized}

## When to Use This Skill

**Required conditions (hard guards)**:
- {Invariant from all successful episodes}

**Preferred conditions (soft guards)**:
- {Common but not universal condition}

**Do NOT apply when**:
- {Condition from failed episodes}
- {Incompatible environment}

## Inputs

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| {name} | {type} | {yes/no} | {value} | {description} |

## Steps

1. {Step with {{parameter}} placeholders}
2. {Step with tool invocation}
   ```{language}
   # Tool call
   ```
3. {Verification step}

## Verification

**Success confirmed when**:
- {Observable condition}

**Verification command**:
```bash
{executable_verification}
```

## If Something Goes Wrong

| Error | Cause | Resolution |
|-------|-------|------------|
| {error} | {cause} | {resolution} |

**Retry**: {conditions and limits}
**Fallback**: {alternative strategy}
**Escalate**: {when to escalate}

## Teaching Notes

**Step rationale**:
1. {why step 1 matters}

**Common struggles**:
- {where learners fail}

**Misconceptions**:
- {incorrect belief} → {correction}
```

## JSON Schema (Programmatic)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CompiledClaudeSkill",
  "type": "object",
  "required": ["metadata", "sections"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["name", "description", "lifecycle"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z][a-z0-9-]*$"
        },
        "description": {
          "type": "string",
          "minLength": 50,
          "maxLength": 500
        },
        "lifecycle": {
          "type": "object",
          "required": ["state", "source_agent", "derived_from", "confidence", "last_updated", "version"],
          "properties": {
            "state": {
              "type": "string",
              "enum": ["candidate", "validated", "operational", "refined", "quarantined"]
            },
            "source_agent": {
              "type": "string"
            },
            "derived_from": {
              "type": "array",
              "items": {"type": "string"},
              "minItems": 3
            },
            "confidence": {
              "type": "number",
              "minimum": 0.0,
              "maximum": 1.0
            },
            "last_updated": {
              "type": "string",
              "format": "date-time"
            },
            "version": {
              "type": "string",
              "pattern": "^\\d+\\.\\d+\\.\\d+$"
            }
          }
        }
      }
    },
    "sections": {
      "type": "object",
      "required": ["description", "when_to_use", "inputs", "steps", "verification", "failure_handling"],
      "properties": {
        "description": {
          "type": "object",
          "required": ["problem_class", "approach", "rationale"],
          "properties": {
            "problem_class": {"type": "string"},
            "approach": {"type": "string"},
            "rationale": {"type": "string"}
          }
        },
        "when_to_use": {
          "type": "object",
          "required": ["hard_guards", "exclusions"],
          "properties": {
            "hard_guards": {
              "type": "array",
              "items": {"type": "string"},
              "minItems": 1
            },
            "soft_guards": {
              "type": "array",
              "items": {"type": "string"}
            },
            "exclusions": {
              "type": "array",
              "items": {"type": "string"},
              "minItems": 1
            }
          }
        },
        "inputs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "type", "required", "description"],
            "properties": {
              "name": {"type": "string"},
              "type": {
                "type": "string",
                "enum": ["string", "number", "boolean", "file", "enum", "object", "array"]
              },
              "required": {"type": "boolean"},
              "default": {},
              "description": {"type": "string"},
              "enum_values": {
                "type": "array",
                "items": {"type": "string"}
              }
            }
          }
        },
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["order", "action", "tool_intent"],
            "properties": {
              "order": {"type": "integer"},
              "action": {"type": "string"},
              "tool_intent": {"type": "string"},
              "code_block": {
                "type": "object",
                "properties": {
                  "language": {"type": "string"},
                  "code": {"type": "string"}
                }
              },
              "parameters_used": {
                "type": "array",
                "items": {"type": "string"}
              }
            }
          }
        },
        "verification": {
          "type": "object",
          "required": ["success_indicators", "method"],
          "properties": {
            "success_indicators": {
              "type": "array",
              "items": {"type": "string"},
              "minItems": 1
            },
            "artifacts": {
              "type": "array",
              "items": {"type": "string"}
            },
            "method": {
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["executable", "observable", "assertion"]
                },
                "command": {"type": "string"},
                "expected_output": {"type": "string"}
              }
            }
          }
        },
        "failure_handling": {
          "type": "object",
          "required": ["known_errors", "retry", "fallback", "escalation"],
          "properties": {
            "known_errors": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["error", "cause", "resolution"],
                "properties": {
                  "error": {"type": "string"},
                  "cause": {"type": "string"},
                  "resolution": {"type": "string"}
                }
              }
            },
            "retry": {
              "type": "object",
              "properties": {
                "conditions": {"type": "string"},
                "max_attempts": {"type": "integer"}
              }
            },
            "fallback": {
              "type": "object",
              "properties": {
                "condition": {"type": "string"},
                "strategy": {"type": "string"}
              }
            },
            "escalation": {
              "type": "object",
              "required": ["target", "threshold"],
              "properties": {
                "target": {"type": "string"},
                "threshold": {"type": "string"}
              }
            }
          }
        },
        "teaching_notes": {
          "type": "object",
          "properties": {
            "step_rationale": {
              "type": "object",
              "additionalProperties": {"type": "string"}
            },
            "common_struggles": {
              "type": "array",
              "items": {"type": "string"}
            },
            "misconceptions": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "incorrect": {"type": "string"},
                  "correct": {"type": "string"}
                }
              }
            }
          }
        }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "scripts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "path": {"type": "string"},
              "purpose": {"type": "string"}
            }
          }
        },
        "references": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "path": {"type": "string"},
              "purpose": {"type": "string"}
            }
          }
        },
        "assets": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "path": {"type": "string"},
              "purpose": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

## Execution Episode Schema (Reverse Mapping Output)

When a skill executes, output this K-STAR episode:

```json
{
  "id": "kstar_exec_{skill_id}_{timestamp}",
  "type": "execution_trace",
  "source_skill": {
    "skill_id": "string",
    "version": "semver"
  },
  "kstar": {
    "K": {
      "refs": ["skill_id"],
      "tools": ["tools_invoked"],
      "assumptions": ["bound_parameters"]
    },
    "S": {
      "trigger": "skill invocation context",
      "context": "execution environment",
      "constraints": ["runtime_constraints"]
    },
    "T": {
      "goal": "skill's stated goal",
      "intent": "user's intent",
      "scope": "execution scope"
    }
  },
  "A_hat": {
    "executor": "skill_executor",
    "plan": "skill steps as executed",
    "control": {"type": "sequential"}
  },
  "A_observed": {
    "steps_executed": [
      {
        "step": 1,
        "action": "what actually happened",
        "tool_calls": ["actual tool invocations"],
        "duration_ms": 0
      }
    ],
    "parameters_bound": {
      "param_name": "actual_value"
    }
  },
  "R_hat": {
    "type": "validation",
    "description": "expected from skill verification",
    "success_criteria": ["from skill"],
    "confidence": 0.0
  },
  "R_observed": {
    "success": true,
    "verification_outcome": {
      "checks_passed": ["which checks"],
      "checks_failed": [],
      "artifacts_produced": ["paths"]
    },
    "delta_from_expected": {
      "prediction_error": 0.0,
      "unexpected_outcomes": []
    }
  },
  "confidence_update": {
    "prior": 0.0,
    "posterior": 0.0,
    "evidence_weight": 0.0
  },
  "timestamp": "ISO8601",
  "agent_identity": "executor_id"
}
```

## Lifecycle State Transitions

```
┌─────────────┐
│  candidate  │ ← Initial compilation
└──────┬──────┘
       │ validation passes
       ▼
┌─────────────┐
│  validated  │ ← Human/teacher approval
└──────┬──────┘
       │ production use begins
       ▼
┌─────────────┐
│ operational │ ← Standard execution
└──────┬──────┘
       │ improvements applied
       ▼
┌─────────────┐
│   refined   │ ← Updated from new episodes
└─────────────┘
       │ errors detected
       ▼
┌─────────────┐
│ quarantined │ ← Suspended pending review
└─────────────┘
```

**Transition Rules**:
- `candidate` → `validated`: Requires explicit approval + tests pass
- `validated` → `operational`: 3+ successful executions in production
- `operational` → `refined`: Version bump after improvement
- `*` → `quarantined`: Failure rate > threshold OR safety violation
- `quarantined` → `validated`: After review and fix
