# KSTAR Transformation Examples

## Example 1: Factual Knowledge

**Input (Natural Language):**
> The capital of France is Paris.

**Output (KSTAR):**
```json
{
  "id": "kstar_geo_001",
  "type": "direct",
  "kstar": {
    "K": {
      "assumptions": ["Geographic knowledge domain"]
    },
    "S": {
      "trigger": "Query about capital of France",
      "context": "Geographic fact retrieval"
    },
    "T": {
      "goal": "Provide capital city of France",
      "intent": "Factual recall"
    }
  },
  "A_hat": {
    "executor": "agent",
    "plan": "## Steps\n1. Recall geographic fact: France → capital\n2. Assert: Paris\n3. Present result to requester",
    "control": {"type": "sequential"}
  },
  "R_hat": {
    "type": "epistemic",
    "description": "Successful recall of France capital",
    "success_criteria": ["Response matches: Paris"],
    "confidence": 0.99
  }
}
```

---

## Example 2: Procedural Skill

**Input (Natural Language):**
> When a user asks about the weather, fetch current data from the weather API using their location, then summarize the conditions.

**Output (KSTAR):**
```json
{
  "id": "kstar_weather_001",
  "type": "direct",
  "kstar": {
    "K": {
      "refs": ["weather_api_endpoint", "location_resolver"],
      "tools": ["http_client", "summarizer"],
      "assumptions": ["User location is available or can be requested"]
    },
    "S": {
      "trigger": "User query contains weather intent",
      "context": "Conversational agent interaction",
      "constraints": ["API must be reachable", "Location must be resolvable"]
    },
    "T": {
      "goal": "Provide current weather summary for user location",
      "intent": "Inform user of weather conditions",
      "scope": "Current conditions only, not forecast"
    }
  },
  "A_hat": {
    "executor": "agent",
    "plan": "## Steps\n1. Extract or request user location\n2. Resolve location to coordinates via `location_resolver`\n3. Execute `http_client.get(weather_api_endpoint, {coords})`\n4. Parse response for current conditions\n5. Summarize using `summarizer` skill\n6. Present natural language summary to user",
    "control": {"type": "sequential"}
  },
  "R_hat": {
    "type": "prediction",
    "description": "User receives accurate, current weather summary",
    "success_criteria": [
      "API returns valid response",
      "Summary includes temperature, conditions, humidity",
      "User acknowledges or acts on information"
    ],
    "confidence": 0.85
  }
}
```

---

## Example 3: Conditional Rule

**Input (Natural Language):**
> If the user is a premium subscriber, provide detailed analytics. Otherwise, show only summary stats.

**Output (KSTAR):**
```json
{
  "id": "kstar_analytics_001",
  "type": "direct",
  "kstar": {
    "K": {
      "refs": ["user_subscription_status", "analytics_full", "analytics_summary"],
      "policies": ["tiered_access_policy"]
    },
    "S": {
      "trigger": "User requests analytics data",
      "context": "Dashboard or reporting interface"
    },
    "T": {
      "goal": "Provide appropriate analytics based on subscription tier",
      "intent": "Enforce access control while serving data"
    }
  },
  "A_hat": {
    "executor": "agent",
    "plan": "## Steps\n1. Recall user subscription status from `user_subscription_status`\n2. If premium:\n   - Execute `analytics_full.generate(user_id)`\n   - Present detailed report\n3. Else:\n   - Execute `analytics_summary.generate(user_id)`\n   - Present summary stats",
    "control": {
      "type": "conditional",
      "condition": "subscription_tier == 'premium'"
    }
  },
  "R_hat": {
    "type": "validation",
    "description": "User receives tier-appropriate analytics",
    "success_criteria": [
      "Premium users see full analytics",
      "Non-premium users see summary only",
      "No unauthorized data exposure"
    ],
    "confidence": 0.95
  }
}
```

---

## Example 4: Observational Memory

**Input (Natural Language):**
> The user mentioned they prefer dark mode interfaces.

**Output (KSTAR):**
```json
{
  "id": "kstar_pref_001",
  "type": "direct",
  "kstar": {
    "K": {
      "assumptions": ["User preference observation"]
    },
    "S": {
      "trigger": "UI customization context or new interface presentation",
      "context": "User expressed preference during conversation"
    },
    "T": {
      "goal": "Apply dark mode when presenting interfaces",
      "intent": "Personalize user experience"
    }
  },
  "A_hat": {
    "executor": "agent",
    "plan": "## Steps\n1. Recall preference: user → dark_mode = true\n2. When presenting UI, assert theme = 'dark'\n3. Apply to all interface outputs",
    "control": {"type": "sequential"}
  },
  "R_hat": {
    "type": "epistemic",
    "description": "UI presentations use dark mode",
    "success_criteria": ["All presented interfaces use dark theme"],
    "confidence": 0.90
  }
}
```

---

## Example 5: Prediction/Forecast

**Input (Natural Language):**
> Based on current trends, the project will likely be delayed by two weeks.

**Output (KSTAR):**
```json
{
  "id": "kstar_forecast_001",
  "type": "direct",
  "kstar": {
    "K": {
      "refs": ["project_timeline", "velocity_metrics", "blocker_log"],
      "models": ["schedule_predictor"]
    },
    "S": {
      "trigger": "Project status review or timeline query",
      "context": "Current sprint shows velocity decline and unresolved blockers"
    },
    "T": {
      "goal": "Forecast project completion date",
      "intent": "Enable proactive planning adjustments"
    }
  },
  "A_hat": {
    "executor": "agent",
    "plan": "## Steps\n1. Recall current velocity from `velocity_metrics`\n2. Recall unresolved blockers from `blocker_log`\n3. Execute `schedule_predictor.forecast(velocity, blockers)`\n4. Assert prediction: delay = 2 weeks\n5. Present forecast with confidence interval",
    "control": {"type": "sequential"}
  },
  "R_hat": {
    "type": "prediction",
    "description": "Project delayed ~2 weeks from original deadline",
    "success_criteria": [
      "Actual completion within ±3 days of forecast"
    ],
    "confidence": 0.70
  }
}
```

---

## Transformation Checklist

When converting NL → KSTAR:

1. **Extract S (Situation)**: What triggers or contextualizes this?
2. **Identify T (Task)**: What's the goal/intent?
3. **Enumerate K (Knowledge)**: What refs, tools, assumptions needed?
4. **Construct Â (Plan)**: What actions achieve T given K and S?
5. **Forecast R̂ (Result)**: What outcome is expected? How confident?

Remember: *There is no passive knowledge.* Every fact implies a recall action.
