# KSTAR Meta-Skill Integration

This skill functions as a meta-skill within the KSTAR cognitive cycle, providing capability discovery and dependency resolution.

## Role in KSTAR Cycle

```
K → S → T → Â → R
│   │   │   │   │
│   │   │   │   └── Verify skill integration worked
│   │   │   └────── Plan skill invocation chain
│   │   └────────── Match goal to skill
│   └────────────── Populate S_N.tools_available
└────────────────── Know what skills exist
```

## Integration Points

### 1. Knowledge (K) — Skill Inventory

Use `get_inventory()` to populate agent's knowledge of available capabilities:

```python
from analyze_dependencies import SkillDependencyAnalyzer

def update_knowledge_with_skills(K: dict) -> dict:
    """Add skill inventory to knowledge base."""
    analyzer = SkillDependencyAnalyzer("/mnt/skills/user")
    
    K["available_skills"] = analyzer.get_inventory()
    K["skill_categories"] = group_by_category(analyzer.get_inventory())
    
    return K


def group_by_category(inventory: list) -> dict:
    """Group skills by category for quick lookup."""
    categories = {}
    for skill in inventory:
        cat = skill["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(skill["name"])
    return categories
```

### 2. Situation (S_N) — Tools Available

Use `get_available()` to populate the now_state tools vector:

```python
def populate_tools_available(S: dict) -> dict:
    """
    Populate S_N.tools_available from skill inventory.
    Called during KSTAR situation completion.
    """
    analyzer = SkillDependencyAnalyzer("/mnt/skills/user")
    
    S["now_state"]["tools_available"] = analyzer.get_available()
    
    return S
```

Output format matches KSTAR S_N schema:

```json
{
  "now_state": {
    "tools_available": [
      {
        "name": "kstar-loop",
        "type": "skill",
        "status": "ready",
        "category": "core",
        "capabilities": ["structured reasoning", "cognitive cycle"]
      }
    ]
  }
}
```

### 3. Task (T) — Skill Matching

Use `match_skill()` to find appropriate skill for a goal:

```python
def select_skill_for_task(T: dict, analyzer: SkillDependencyAnalyzer) -> Optional[str]:
    """
    Find skill that can accomplish task goal.
    """
    goal = T.get("goal", "")
    
    matched = analyzer.match_skill(goal)
    
    if matched:
        return matched["name"]
    return None


# Example usage in KSTAR planning
def plan_with_skill_selection(K, S, T):
    """Generate action plan with skill selection."""
    analyzer = SkillDependencyAnalyzer("/mnt/skills/user")
    
    # Find appropriate skill
    skill_name = select_skill_for_task(T, analyzer)
    
    if skill_name:
        # Get skill dependencies
        deps = analyzer.get_dependencies(skill_name)
        
        A_hat = {
            "executor": "skill",
            "skill": skill_name,
            "dependencies": deps["uses"],
            "plan": f"Invoke {skill_name} to accomplish: {T['goal']}"
        }
    else:
        A_hat = {
            "executor": "agent",
            "plan": "No matching skill found; proceeding with general reasoning"
        }
    
    return A_hat
```

### 4. Action (Â) — Dependency Chain

Use `get_dependencies()` to plan skill invocation order:

```python
def build_invocation_chain(skill_name: str, analyzer: SkillDependencyAnalyzer) -> list:
    """
    Build ordered list of skills to invoke.
    Handles transitive dependencies.
    """
    chain = []
    visited = set()
    
    def resolve(name: str):
        if name in visited:
            return
        visited.add(name)
        
        deps = analyzer.get_dependencies(name)
        for dep in deps.get("uses", []):
            if dep in analyzer.graph.nodes:  # Only if exists
                resolve(dep)
        
        chain.append(name)
    
    resolve(skill_name)
    return chain


# Example: Planning KSTAR loop invocation
def plan_kstar_invocation(analyzer: SkillDependencyAnalyzer) -> dict:
    """Plan invocation of kstar-loop with dependencies."""
    chain = build_invocation_chain("kstar-loop", analyzer)
    
    return {
        "invocation_order": chain,
        "primary_skill": "kstar-loop",
        "supporting_skills": chain[:-1]  # All except primary
    }

# Result:
# {
#   "invocation_order": ["uair-control", "kstar-transformation", "kstar-loop"],
#   "primary_skill": "kstar-loop",
#   "supporting_skills": ["uair-control", "kstar-transformation"]
# }
```

### 5. Result (R) — Integration Verification

Use dependency analysis to verify skill integration worked:

```python
def verify_skill_integration(skill_name: str, result: dict, analyzer: SkillDependencyAnalyzer) -> dict:
    """
    Verify skill executed correctly by checking expected integrations.
    """
    deps = analyzer.get_dependencies(skill_name)
    
    verification = {
        "skill": skill_name,
        "success": result.get("success", False),
        "integration_checks": []
    }
    
    for dep in deps.get("uses", []):
        check = {
            "dependency": dep,
            "invoked": dep in result.get("skills_invoked", []),
            "expected": True
        }
        verification["integration_checks"].append(check)
    
    verification["all_integrations_ok"] = all(
        c["invoked"] == c["expected"] 
        for c in verification["integration_checks"]
    )
    
    return verification
```

## UAIR Integration

The skill-dependency-analyzer can serve as a RETRIEVE handler for UAIR:

```python
def uair_capability_retrieval(query: dict) -> dict:
    """
    UAIR RETRIEVE handler for capability/tool discovery.
    
    Handles queries like:
    - "what tools are available"
    - "find skill for [goal]"
    - "skill dependencies"
    """
    analyzer = SkillDependencyAnalyzer("/mnt/skills/user")
    query_text = query.get("query", "").lower()
    
    if "available" in query_text or "tools" in query_text:
        return {
            "artifact_delta": {
                "now_state": {
                    "tools_available": analyzer.get_available()
                }
            }
        }
    
    if "find" in query_text or "match" in query_text:
        # Extract goal from query
        goal = query_text.replace("find skill for", "").strip()
        matched = analyzer.match_skill(goal)
        if matched:
            return {
                "artifact_delta": {
                    "matched_skill": matched
                }
            }
    
    if "dependencies" in query_text:
        # Full dependency analysis
        return {
            "artifact_delta": {
                "skill_dependencies": analyzer.analyze()["dependencies"]
            }
        }
    
    return {"artifact_delta": {}}
```

## Complete KSTAR Integration Example

```python
from analyze_dependencies import SkillDependencyAnalyzer
from kstar_loop import KSTARLoop
from uair_controller import uair_control

def kstar_with_skill_awareness():
    """
    Run KSTAR loop with skill dependency awareness.
    """
    # Initialize analyzer
    analyzer = SkillDependencyAnalyzer("/mnt/skills/user")
    
    # Build initial knowledge with skill inventory
    K = {
        "domain_knowledge": {},
        "available_skills": analyzer.get_inventory(),
        "skill_graph": analyzer.analyze()["dependencies"]
    }
    
    # Build situation with tools populated
    S = {
        "actor_state": {"id": "user_001"},
        "domain_state": {"objective": "Complete analysis task"},
        "protocol_state": {"current_stage": "understand"},
        "now_state": {
            "tools_available": analyzer.get_available()
        }
    }
    
    # Task with skill matching
    T = {
        "id": "task_001",
        "goal": "Analyze document structure",
        "stage": "understand"
    }
    
    # Check if skill exists for task
    matched_skill = analyzer.match_skill(T["goal"])
    if matched_skill:
        T["suggested_skill"] = matched_skill["name"]
        T["skill_dependencies"] = analyzer.get_dependencies(matched_skill["name"])
    
    # Run KSTAR loop
    loop = KSTARLoop(K, S, T)
    result = loop.run()
    
    return result
```

## Self-Analysis Capability

The skill can analyze itself:

```python
def self_analyze():
    """Meta-skill analyzing its own dependencies."""
    analyzer = SkillDependencyAnalyzer("/mnt/skills/user")
    
    self_deps = analyzer.get_dependencies("skill-dependency-analyzer")
    
    return {
        "skill": "skill-dependency-analyzer",
        "meta": True,
        "dependencies": self_deps,
        "can_analyze_self": True
    }
```
