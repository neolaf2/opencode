# Situation Schema

The Situation vector S is the complete state needed to generate action plans and forecasts.

```
S := ⟨S_A, S_D, S_P, S_N⟩
```

## Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SituationVector",
  "type": "object",
  "required": ["actor_state", "domain_state", "protocol_state", "now_state"],
  "properties": {
    "actor_state": { "$ref": "#/definitions/ActorState" },
    "domain_state": { "$ref": "#/definitions/DomainState" },
    "protocol_state": { "$ref": "#/definitions/ProtocolState" },
    "now_state": { "$ref": "#/definitions/NowState" }
  },
  "definitions": {
    "ActorState": {
      "type": "object",
      "description": "State of the primary actor (user, learner, client)",
      "required": ["id"],
      "properties": {
        "id": { "type": "string" },
        "role": { "type": "string" },
        "capabilities": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "level": { "type": "number", "minimum": 0, "maximum": 1 },
              "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
            }
          }
        },
        "preferences": {
          "type": "object",
          "properties": {
            "communication_style": { "type": "string" },
            "detail_level": { "enum": ["minimal", "moderate", "detailed"] },
            "interaction_mode": { "enum": ["guided", "collaborative", "autonomous"] }
          }
        },
        "constraints": {
          "type": "object",
          "properties": {
            "time_available": { "type": "integer", "description": "minutes" },
            "cognitive_load": { "enum": ["low", "medium", "high"] },
            "accessibility": { "type": "array", "items": { "type": "string" } }
          }
        },
        "goals": {
          "type": "array",
          "items": { "type": "string" }
        },
        "history_summary": { "type": "string" }
      }
    },
    "DomainState": {
      "type": "object",
      "description": "State of the domain/task environment",
      "required": ["objective"],
      "properties": {
        "objective": { "type": "string" },
        "domain_type": { "type": "string" },
        "resources": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string" },
              "type": { "type": "string" },
              "uri": { "type": "string" },
              "availability": { "enum": ["available", "restricted", "unavailable"] }
            }
          }
        },
        "requirements": {
          "type": "object",
          "properties": {
            "deliverables": { "type": "array", "items": { "type": "string" } },
            "quality_criteria": { "type": "array", "items": { "type": "string" } },
            "constraints": { "type": "array", "items": { "type": "string" } }
          }
        },
        "rubrics": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "criteria": { "type": "string" },
              "levels": { "type": "array", "items": { "type": "string" } }
            }
          }
        },
        "knowledge_graph_ref": { "type": "string" }
      }
    },
    "ProtocolState": {
      "type": "object",
      "description": "State of the interaction protocol/workflow",
      "required": ["current_stage"],
      "properties": {
        "workflow_type": {
          "type": "string",
          "examples": ["ilt", "assessment", "research", "creation", "diagnosis"]
        },
        "current_stage": {
          "enum": ["understand", "plan", "execute", "validate", "reflect", "complete"]
        },
        "stage_history": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "stage": { "type": "string" },
              "entered_at": { "type": "string", "format": "date-time" },
              "outcome": { "type": "string" }
            }
          }
        },
        "interaction_pattern": {
          "type": "string",
          "examples": ["socratic", "direct", "exploratory", "diagnostic"]
        },
        "agent_role": {
          "enum": ["coordinator", "monitor", "advisor", "companion", "executor"]
        },
        "turn_count": { "type": "integer" },
        "checkpoint": { "type": "string" }
      }
    },
    "NowState": {
      "type": "object",
      "description": "Immediate contextual state",
      "properties": {
        "timestamp": { "type": "string", "format": "date-time" },
        "tools_available": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "type": { "type": "string" },
              "status": { "enum": ["ready", "busy", "unavailable"] }
            }
          }
        },
        "time_budget_minutes": { "type": "integer" },
        "session_context": {
          "type": "object",
          "properties": {
            "session_id": { "type": "string" },
            "started_at": { "type": "string", "format": "date-time" },
            "environment": { "type": "string" }
          }
        },
        "active_artifacts": {
          "type": "array",
          "items": { "type": "string" }
        },
        "pending_inputs": {
          "type": "array",
          "items": { "type": "string" }
        },
        "interrupts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": { "type": "string" },
              "priority": { "enum": ["low", "medium", "high", "critical"] },
              "message": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

## Required vs Optional Fields

### Minimum Viable Situation

For KSTAR loop to proceed, at minimum:

```json
{
  "actor_state": { "id": "user_001" },
  "domain_state": { "objective": "..." },
  "protocol_state": { "current_stage": "understand" },
  "now_state": {}
}
```

### UAIR Trigger Conditions

Invoke `uair-control` when:

| Component | Condition | UAIR Target |
|-----------|-----------|-------------|
| S_A | `capabilities` empty, goal ambiguous | ASK for actor profile |
| S_D | `objective` vague, resources unknown | ASK/RETRIEVE domain info |
| S_P | `workflow_type` undetermined | ASK workflow preference |
| S_N | `tools_available` needed but empty | RETRIEVE/EXECUTE tool discovery |

## Domain-Specific Extensions

### Learning Companion

```json
{
  "actor_state": {
    "learner_profile": {
      "skill_vector": {},
      "learning_style": "visual|auditory|kinesthetic",
      "misconceptions": [],
      "motivation_level": 0.8
    }
  },
  "domain_state": {
    "curriculum": {},
    "learning_objectives": [],
    "prerequisite_check": {}
  }
}
```

### Coding Assistant

```json
{
  "actor_state": {
    "developer_profile": {
      "languages": {},
      "frameworks": [],
      "experience_level": "junior|mid|senior"
    }
  },
  "domain_state": {
    "codebase": { "repo": "", "branch": "" },
    "requirements": { "ticket": "", "acceptance_criteria": [] },
    "tech_stack": []
  }
}
```

### Research Agent

```json
{
  "actor_state": {
    "researcher_profile": {
      "expertise_areas": [],
      "methodological_preferences": []
    }
  },
  "domain_state": {
    "research_question": "",
    "literature_scope": {},
    "methodology_constraints": []
  }
}
```

## Situation Completeness Check

```python
def situation_complete(S, T):
    """Check if situation is sufficient for current stage."""
    
    required = {
        "understand": ["actor_state.id", "domain_state.objective"],
        "plan": ["actor_state.capabilities", "domain_state.resources"],
        "execute": ["now_state.tools_available", "protocol_state.workflow_type"],
        "validate": ["domain_state.requirements", "domain_state.rubrics"],
        "reflect": ["protocol_state.stage_history"]
    }
    
    for path in required.get(T.stage, []):
        if not has_value(S, path):
            return False
    return True
```
