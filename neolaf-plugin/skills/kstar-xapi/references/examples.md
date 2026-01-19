# KSTAR xAPI Profile - Example Statements

## Overview

This document provides example xAPI statements conforming to the KSTAR Profile v0.1.

## Namespace Prefixes

| Prefix | IRI |
|--------|-----|
| `kstar:` | `https://neolaf.ai/xapi/` |
| `verbs:` | `https://neolaf.ai/xapi/verbs/` |
| `activities:` | `https://neolaf.ai/xapi/activities/` |
| `extensions:` | `https://neolaf.ai/xapi/extensions/` |

---

## Example 1: Stage Completion (Understand)

```json
{
  "actor": {
    "objectType": "Agent",
    "name": "Learning Companion Agent",
    "account": {
      "homePage": "https://neolaf.ai/agents",
      "name": "agent_lc_001"
    }
  },
  "verb": {
    "id": "https://neolaf.ai/xapi/verbs/understood",
    "display": { "en": "understood" }
  },
  "object": {
    "objectType": "Activity",
    "id": "https://neolaf.ai/tasks/task_001/stages/understand",
    "definition": {
      "type": "https://neolaf.ai/xapi/activities/kstar-stage",
      "name": { "en": "Understand Stage" },
      "description": { "en": "Parse goal, identify constraints, define success criteria" }
    }
  },
  "result": {
    "success": true,
    "completion": true,
    "extensions": {
      "https://neolaf.ai/xapi/extensions/stage-transition": {
        "from_stage": null,
        "to_stage": "plan",
        "reason": "goal_structured"
      }
    }
  },
  "context": {
    "contextActivities": {
      "grouping": [
        {
          "objectType": "Activity",
          "id": "https://neolaf.ai/tasks/task_001",
          "definition": {
            "type": "https://neolaf.ai/xapi/activities/kstar-task",
            "name": { "en": "Learn recursive factorial implementation" }
          }
        }
      ]
    },
    "extensions": {
      "https://neolaf.ai/xapi/extensions/task-specification": {
        "id": "task_001",
        "goal": "Understand and implement recursive factorial",
        "stage": "understand",
        "success_criteria": [
          "Explain recursion concept",
          "Implement factorial function",
          "Test with examples"
        ],
        "constraints": {}
      },
      "https://neolaf.ai/xapi/extensions/situation-vector": {
        "actor_state": {
          "id": "learner_001",
          "role": "learner",
          "capabilities": { "python": 0.6 }
        },
        "domain_state": {
          "objective": "Learn recursion",
          "resources": [{ "id": "tutorial", "type": "document" }]
        },
        "protocol_state": {
          "workflow_type": "ilt",
          "current_stage": "understand",
          "agent_role": "companion"
        },
        "now_state": {
          "tools_available": ["ide", "search"],
          "time_budget_minutes": 30
        }
      }
    }
  },
  "timestamp": "2025-01-10T10:00:00.000Z"
}
```

---

## Example 2: Forecast Statement

```json
{
  "actor": {
    "objectType": "Agent",
    "name": "Learning Companion Agent",
    "account": {
      "homePage": "https://neolaf.ai/agents",
      "name": "agent_lc_001"
    }
  },
  "verb": {
    "id": "https://neolaf.ai/xapi/verbs/forecasted",
    "display": { "en": "forecasted" }
  },
  "object": {
    "objectType": "Activity",
    "id": "https://neolaf.ai/tasks/task_001",
    "definition": {
      "type": "https://neolaf.ai/xapi/activities/kstar-task",
      "name": { "en": "Learn recursive factorial implementation" }
    }
  },
  "context": {
    "extensions": {
      "https://neolaf.ai/xapi/extensions/action-plan": {
        "actions": [
          { "type": "explain", "description": "Explain base case and recursive case" },
          { "type": "demonstrate", "description": "Show factorial(5) trace" },
          { "type": "guide", "description": "Guide learner to implement" }
        ],
        "resources": { "ide": "available" },
        "is_feasible": true
      },
      "https://neolaf.ai/xapi/extensions/forecast": {
        "expected_outcome": "Learner implements working factorial function",
        "success_probability": 0.75,
        "risks": ["May struggle with base case concept"],
        "confidence": 0.7
      }
    }
  },
  "timestamp": "2025-01-10T10:05:00.000Z"
}
```

---

## Example 3: Episode Execution

```json
{
  "actor": {
    "objectType": "Agent",
    "name": "Learning Companion Agent",
    "account": {
      "homePage": "https://neolaf.ai/agents",
      "name": "agent_lc_001"
    }
  },
  "verb": {
    "id": "https://neolaf.ai/xapi/verbs/executed",
    "display": { "en": "executed" }
  },
  "object": {
    "objectType": "Activity",
    "id": "https://neolaf.ai/episodes/ep_001",
    "definition": {
      "type": "https://neolaf.ai/xapi/activities/kstar-episode",
      "name": { "en": "Factorial Learning Episode" },
      "description": { "en": "Single KSTAR episode for factorial implementation task" }
    }
  },
  "result": {
    "success": true,
    "completion": true,
    "response": "Learner successfully implemented factorial function",
    "extensions": {
      "https://neolaf.ai/xapi/extensions/prediction-error": 0.1
    }
  },
  "context": {
    "contextActivities": {
      "grouping": [
        {
          "objectType": "Activity",
          "id": "https://neolaf.ai/tasks/task_001",
          "definition": {
            "type": "https://neolaf.ai/xapi/activities/kstar-task"
          }
        }
      ]
    },
    "extensions": {
      "https://neolaf.ai/xapi/extensions/knowledge-state": {
        "episodic_summary": "Previous python exercises completed",
        "semantic_refs": ["recursion_concept", "function_definition"]
      },
      "https://neolaf.ai/xapi/extensions/situation-vector": {
        "actor_state": { "id": "learner_001", "capabilities": { "python": 0.6 } },
        "domain_state": { "objective": "Learn recursion" },
        "protocol_state": { "current_stage": "execute", "agent_role": "companion" },
        "now_state": { "tools_available": ["ide"] }
      },
      "https://neolaf.ai/xapi/extensions/task-specification": {
        "id": "task_001",
        "goal": "Implement recursive factorial",
        "stage": "execute"
      },
      "https://neolaf.ai/xapi/extensions/action-plan": {
        "actions": [{ "type": "guide", "description": "Guide implementation" }],
        "is_feasible": true
      }
    }
  },
  "timestamp": "2025-01-10T10:15:00.000Z"
}
```

---

## Example 4: Cycle Completion with AAR

```json
{
  "actor": {
    "objectType": "Agent",
    "name": "Learning Companion Agent",
    "account": {
      "homePage": "https://neolaf.ai/agents",
      "name": "agent_lc_001"
    }
  },
  "verb": {
    "id": "https://neolaf.ai/xapi/verbs/completed-cycle",
    "display": { "en": "completed cycle" }
  },
  "object": {
    "objectType": "Activity",
    "id": "https://neolaf.ai/tasks/task_001",
    "definition": {
      "type": "https://neolaf.ai/xapi/activities/kstar-task",
      "name": { "en": "Learn recursive factorial implementation" }
    }
  },
  "result": {
    "success": true,
    "completion": true,
    "duration": "PT25M",
    "score": {
      "scaled": 0.85
    },
    "extensions": {
      "https://neolaf.ai/xapi/extensions/aar": {
        "what_happened": "Learner progressed through explanation, demonstration, and guided implementation of recursive factorial",
        "what_worked": [
          "Visual trace of factorial(5) helped understanding",
          "Incremental prompts during implementation"
        ],
        "what_didnt_work": [
          "Initial base case explanation too abstract"
        ],
        "lessons_learned": [
          "Start with concrete examples before abstract definition",
          "Use visual traces for recursive concepts"
        ],
        "recommendations": [
          "For future recursion topics, begin with call stack visualization"
        ]
      },
      "https://neolaf.ai/xapi/extensions/knowledge-delta": {
        "actor_model_updates": {
          "learner_001": {
            "capabilities": { "python": 0.65, "recursion": 0.5 },
            "preferences": { "learning_style": "visual" }
          }
        },
        "episode_added": "ep_001"
      }
    }
  },
  "context": {
    "extensions": {
      "https://neolaf.ai/xapi/extensions/situation-vector": {
        "actor_state": { "id": "learner_001" },
        "domain_state": { "objective": "Learn recursion" },
        "protocol_state": { "current_stage": "complete" },
        "now_state": {}
      }
    }
  },
  "timestamp": "2025-01-10T10:25:00.000Z"
}
```

---

## Statement Patterns

### Standard KSTAR Cycle Sequence

1. `understood` → stage completion (understand → plan)
2. `planned` → stage completion (plan → execute)  
3. `forecasted` → prediction before execution
4. `executed` → episode execution
5. `validated` → stage completion (execute → validate → reflect)
6. `reflected` → stage completion (validate → reflect)
7. `completed-cycle` → full cycle completion with AAR

### Mapping to xAPI Verbs

| KSTAR Stage | xAPI Verb | ADL Equivalent |
|-------------|-----------|----------------|
| understand | `verbs:understood` | completed |
| plan | `verbs:planned` | planned |
| forecast | `verbs:forecasted` | — |
| execute | `verbs:executed` | completed |
| validate | `verbs:validated` | evaluated |
| reflect | `verbs:reflected` | reflected |
| complete | `verbs:completed-cycle` | completed |

---

## Integration with LRS

### Recommended LRS Queries

**Get all episodes for a task:**
```
GET /statements?activity=https://neolaf.ai/tasks/task_001&related_activities=true
```

**Get prediction errors for analysis:**
```
GET /statements?verb=https://neolaf.ai/xapi/verbs/executed
```
Then filter by `result.extensions['prediction-error']`

**Get all AARs for a learner:**
```
GET /statements?agent={"account":{"name":"learner_001"}}&verb=https://neolaf.ai/xapi/verbs/completed-cycle
```
