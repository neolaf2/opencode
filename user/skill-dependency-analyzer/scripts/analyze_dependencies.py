#!/usr/bin/env python3
"""
Skill Dependency Analyzer

Analyzes agent skill ecosystems to map dependencies, identify gaps,
and generate integration reports.

Usage:
    python analyze_dependencies.py /mnt/skills/user --format markdown
    python analyze_dependencies.py /mnt/skills/user --format json
    python analyze_dependencies.py /mnt/skills/user --format mermaid
"""

import os
import re
import json
import yaml
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict


@dataclass
class SkillInfo:
    """Information about a single skill."""
    name: str
    path: str
    description: str = ""
    size: int = 0
    category: str = "unknown"
    triggers: List[str] = field(default_factory=list)
    uses: Set[str] = field(default_factory=set)
    files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "size": self.size,
            "size_human": format_size(self.size),
            "category": self.category,
            "triggers": self.triggers,
            "uses": list(self.uses),
            "files": self.files
        }


@dataclass
class DependencyGraph:
    """Dependency relationships between skills."""
    nodes: Dict[str, SkillInfo] = field(default_factory=dict)
    edges: List[Dict] = field(default_factory=list)
    
    def add_skill(self, skill: SkillInfo):
        self.nodes[skill.name] = skill
    
    def add_edge(self, from_skill: str, to_skill: str, edge_type: str = "uses"):
        self.edges.append({
            "from": from_skill,
            "to": to_skill,
            "type": edge_type
        })
    
    def get_uses(self, skill_name: str) -> List[str]:
        return [e["to"] for e in self.edges if e["from"] == skill_name]
    
    def get_used_by(self, skill_name: str) -> List[str]:
        return [e["from"] for e in self.edges if e["to"] == skill_name]
    
    def to_dict(self) -> Dict:
        return {
            "nodes": [s.to_dict() for s in self.nodes.values()],
            "edges": self.edges
        }


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024}K"
    else:
        return f"{size_bytes // (1024 * 1024)}M"


def get_dir_size(path: str) -> int:
    """Get total size of directory."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


class SkillDependencyAnalyzer:
    """
    Main analyzer class for skill dependency analysis.
    """
    
    # Patterns for detecting skill references
    SKILL_REF_PATTERNS = [
        # Direct skill name mentions (e.g., "uses uair-control")
        r'(?:uses?|invokes?|calls?|coordinates?\s+with|integrates?\s+with)\s+[`"]?(\w+(?:-\w+)*)[`"]?',
        # Import patterns
        r'from\s+(\w+(?:_\w+)*)\s+import',
        # With sections (e.g., "### With kstar-transformation")
        r'###?\s+With\s+(\w+(?:-\w+)*)',
        # available_subskills references
        r'"available_subskills":\s*\[([^\]]+)\]',
        # Skill references in code (e.g., skill_name = "uair-control")
        r'skill(?:_name)?\s*[=:]\s*["\'](\w+(?:-\w+)*)["\']',
    ]
    
    # Known skill name patterns to filter false positives
    SKILL_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$')  # Require at least one hyphen
    
    # Common false positives to exclude
    FALSE_POSITIVES = {
        "for", "when", "with", "from", "into", "each", "this", "that", "the",
        "and", "or", "not", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "can", "use", "used", "using",
        "python", "json", "yaml", "markdown", "html", "css", "javascript",
        "string", "number", "boolean", "object", "array", "null", "true", "false",
        "input", "output", "result", "error", "success", "failure", "status",
        "name", "type", "value", "path", "file", "data", "text", "content"
    }
    
    # Category detection patterns
    CATEGORY_PATTERNS = {
        "core": ["kstar", "uair", "loop", "control", "transform"],
        "document": ["docx", "pdf", "latex", "pptx", "xlsx", "html", "markdown"],
        "domain": ["neolaf", "wechat", "business"],
        "workflow": ["consolidat", "review", "format"],
        "integration": ["xapi", "api", "sdk"],
        "meta": ["skill", "dependency", "analyz"]
    }
    
    def __init__(self, skill_path: str, include_paths: Optional[List[str]] = None):
        """
        Initialize analyzer with skill directory path.
        
        Args:
            skill_path: Primary path to scan for skills
            include_paths: Additional paths to include in analysis
        """
        self.skill_path = skill_path
        self.include_paths = include_paths or []
        self.graph = DependencyGraph()
        self._all_skill_names: Set[str] = set()
    
    def analyze(self) -> Dict:
        """
        Run full dependency analysis.
        
        Returns:
            Complete analysis result with inventory, dependencies, gaps, recommendations
        """
        # Scan all paths
        all_paths = [self.skill_path] + self.include_paths
        for path in all_paths:
            if os.path.isdir(path):
                self._scan_directory(path)
        
        # Build dependency edges
        self._build_edges()
        
        # Analyze gaps
        gaps = self._find_gaps()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(gaps)
        
        return {
            "inventory": [s.to_dict() for s in self.graph.nodes.values()],
            "dependencies": self._build_dependency_map(),
            "gaps": gaps,
            "recommendations": recommendations,
            "summary": {
                "total_skills": len(self.graph.nodes),
                "total_dependencies": len(self.graph.edges),
                "missing_skills": len(gaps)
            }
        }
    
    def _scan_directory(self, path: str):
        """Scan directory for skills."""
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            skill_md = os.path.join(item_path, "SKILL.md")
            
            if os.path.isdir(item_path) and os.path.isfile(skill_md):
                skill = self._parse_skill(item_path, skill_md)
                if skill:
                    self.graph.add_skill(skill)
                    self._all_skill_names.add(skill.name)
    
    def _parse_skill(self, skill_dir: str, skill_md_path: str) -> Optional[SkillInfo]:
        """Parse a skill from its SKILL.md file."""
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML frontmatter
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                else:
                    body = content
            else:
                body = content
            
            name = frontmatter.get('name', os.path.basename(skill_dir))
            description = frontmatter.get('description', '')
            if isinstance(description, str):
                description = description.strip()
            
            # Extract triggers from description
            triggers = self._extract_triggers(description)
            
            # Extract dependencies from full content
            uses = self._extract_dependencies(content)
            
            # Get file listing
            files = self._get_skill_files(skill_dir)
            
            # Determine category
            category = self._determine_category(name, description)
            
            return SkillInfo(
                name=name,
                path=skill_dir,
                description=description[:200] + "..." if len(description) > 200 else description,
                size=get_dir_size(skill_dir),
                category=category,
                triggers=triggers,
                uses=uses,
                files=files
            )
        except Exception as e:
            print(f"Warning: Could not parse {skill_md_path}: {e}")
            return None
    
    def _extract_triggers(self, description: str) -> List[str]:
        """Extract trigger phrases from description."""
        triggers = []
        
        # Look for "Triggers on" or "Use when" patterns
        trigger_match = re.search(
            r'(?:Triggers?\s+on|Use\s+when)[:\s]+(.+?)(?:\.|$)',
            description,
            re.IGNORECASE
        )
        if trigger_match:
            trigger_text = trigger_match.group(1)
            # Split by commas or "or"
            parts = re.split(r',\s*|\s+or\s+', trigger_text)
            triggers = [p.strip().strip('"\'') for p in parts if p.strip()]
        
        return triggers[:5]  # Limit to 5 triggers
    
    def _extract_dependencies(self, content: str) -> Set[str]:
        """Extract skill dependencies from content."""
        deps = set()
        
        for pattern in self.SKILL_REF_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # Clean and validate
                match = match.strip().strip('"\'').lower()
                match = match.replace('_', '-')
                
                # Filter false positives
                if match in self.FALSE_POSITIVES:
                    continue
                
                # Must have at least one hyphen (skill naming convention)
                if '-' not in match:
                    continue
                
                if self.SKILL_NAME_PATTERN.match(match):
                    deps.add(match)
        
        return deps
    
    def _get_skill_files(self, skill_dir: str) -> List[str]:
        """Get list of files in skill directory."""
        files = []
        for root, _, filenames in os.walk(skill_dir):
            for f in filenames:
                rel_path = os.path.relpath(os.path.join(root, f), skill_dir)
                files.append(rel_path)
        return sorted(files)
    
    def _determine_category(self, name: str, description: str) -> str:
        """Determine skill category based on name and description."""
        text = f"{name} {description}".lower()
        
        for category, keywords in self.CATEGORY_PATTERNS.items():
            if any(kw in text for kw in keywords):
                return category
        
        return "other"
    
    def _build_edges(self):
        """Build dependency edges between skills."""
        for skill_name, skill in self.graph.nodes.items():
            for dep in skill.uses:
                # Only add edge if dependency exists or is a known skill pattern
                if dep != skill_name:  # No self-references
                    self.graph.add_edge(skill_name, dep, "uses")
    
    def _find_gaps(self) -> List[Dict]:
        """Find missing dependencies (referenced but not found)."""
        gaps = []
        
        for skill_name, skill in self.graph.nodes.items():
            for dep in skill.uses:
                if dep not in self._all_skill_names and dep != skill_name:
                    gaps.append({
                        "referenced_by": skill_name,
                        "missing_skill": dep,
                        "severity": "warning" if "-" in dep else "info"
                    })
        
        return gaps
    
    def _generate_recommendations(self, gaps: List[Dict]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Missing dependencies
        missing_skills = set(g["missing_skill"] for g in gaps)
        if missing_skills:
            for skill in list(missing_skills)[:5]:
                recommendations.append(
                    f"Create or install '{skill}' skill (referenced by existing skills)"
                )
        
        # Orphan detection (skills not used by anything)
        used_skills = set()
        for edge in self.graph.edges:
            used_skills.add(edge["to"])
        
        orphans = set(self.graph.nodes.keys()) - used_skills
        if len(orphans) > 1:  # Exclude root skills
            recommendations.append(
                f"Consider integrating orphan skills: {', '.join(list(orphans)[:3])}"
            )
        
        # Circular dependency detection
        circular = self._detect_circular()
        if circular:
            recommendations.append(
                f"Review circular dependencies: {' -> '.join(circular)}"
            )
        
        return recommendations
    
    def _detect_circular(self) -> Optional[List[str]]:
        """Detect circular dependencies."""
        visited = set()
        path = []
        
        def dfs(node: str) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for dep in self.graph.get_uses(node):
                if dep in self.graph.nodes:
                    result = dfs(dep)
                    if result:
                        return result
            
            path.pop()
            return None
        
        for skill in self.graph.nodes:
            result = dfs(skill)
            if result:
                return result
            visited.clear()
            path.clear()
        
        return None
    
    def _build_dependency_map(self) -> Dict[str, Dict]:
        """Build map of skill -> {uses, used_by}."""
        dep_map = {}
        for skill_name in self.graph.nodes:
            dep_map[skill_name] = {
                "uses": self.graph.get_uses(skill_name),
                "used_by": self.graph.get_used_by(skill_name)
            }
        return dep_map
    
    # === Output Methods ===
    
    def get_inventory(self) -> List[Dict]:
        """Get skill inventory list."""
        if not self.graph.nodes:
            self.analyze()
        return [s.to_dict() for s in self.graph.nodes.values()]
    
    def get_available(self) -> List[Dict]:
        """Get available skills in format suitable for KSTAR S_N.tools_available."""
        if not self.graph.nodes:
            self.analyze()
        
        return [
            {
                "name": skill.name,
                "type": "skill",
                "status": "ready",
                "category": skill.category,
                "capabilities": skill.triggers
            }
            for skill in self.graph.nodes.values()
        ]
    
    def get_dependencies(self, skill_name: str) -> Dict:
        """Get dependencies for a specific skill."""
        if not self.graph.nodes:
            self.analyze()
        
        if skill_name not in self.graph.nodes:
            return {"error": f"Skill '{skill_name}' not found"}
        
        skill = self.graph.nodes[skill_name]
        return {
            "name": skill_name,
            "uses": self.graph.get_uses(skill_name),
            "used_by": self.graph.get_used_by(skill_name),
            "missing": [
                dep for dep in skill.uses
                if dep not in self._all_skill_names
            ]
        }
    
    def match_skill(self, goal: str) -> Optional[Dict]:
        """Find skill that matches a goal description."""
        if not self.graph.nodes:
            self.analyze()
        
        goal_lower = goal.lower()
        best_match = None
        best_score = 0
        
        for skill in self.graph.nodes.values():
            score = 0
            
            # Check triggers
            for trigger in skill.triggers:
                if any(word in goal_lower for word in trigger.lower().split()):
                    score += 3
            
            # Check name
            if skill.name.replace('-', ' ') in goal_lower:
                score += 5
            
            # Check description
            desc_words = skill.description.lower().split()
            matches = sum(1 for word in goal_lower.split() if word in desc_words)
            score += matches
            
            if score > best_score:
                best_score = score
                best_match = skill
        
        if best_match and best_score > 0:
            return best_match.to_dict()
        return None
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        result = self.analyze()
        
        lines = [
            "# Skill Dependency Report",
            "",
            f"**Generated for:** `{self.skill_path}`",
            f"**Total Skills:** {result['summary']['total_skills']}",
            f"**Total Dependencies:** {result['summary']['total_dependencies']}",
            "",
            "## Inventory",
            "",
            "| Skill | Category | Size | Uses | Used By |",
            "|-------|----------|------|------|---------|"
        ]
        
        deps = result["dependencies"]
        for skill in sorted(result["inventory"], key=lambda x: x["name"]):
            name = skill["name"]
            uses_count = len(deps.get(name, {}).get("uses", []))
            used_by_count = len(deps.get(name, {}).get("used_by", []))
            lines.append(
                f"| {name} | {skill['category']} | {skill['size_human']} | {uses_count} | {used_by_count} |"
            )
        
        lines.extend([
            "",
            "## Dependency Graph",
            "",
            "```mermaid",
            self.to_mermaid(),
            "```",
            ""
        ])
        
        if result["gaps"]:
            lines.extend([
                "## Gaps (Missing Dependencies)",
                ""
            ])
            for gap in result["gaps"]:
                lines.append(f"- **{gap['referenced_by']}** references `{gap['missing_skill']}` (not found)")
            lines.append("")
        
        if result["recommendations"]:
            lines.extend([
                "## Recommendations",
                ""
            ])
            for i, rec in enumerate(result["recommendations"], 1):
                lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)
    
    def to_mermaid(self) -> str:
        """Generate Mermaid flowchart."""
        if not self.graph.nodes:
            self.analyze()
        
        lines = ["flowchart TD"]
        
        # Add nodes with categories
        for skill in self.graph.nodes.values():
            shape = "([" if skill.category == "core" else "["
            end_shape = "])" if skill.category == "core" else "]"
            lines.append(f"    {skill.name.replace('-', '_')}{shape}{skill.name}{end_shape}")
        
        # Add edges
        for edge in self.graph.edges:
            if edge["to"] in self.graph.nodes:
                from_node = edge["from"].replace('-', '_')
                to_node = edge["to"].replace('-', '_')
                lines.append(f"    {from_node} --> {to_node}")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """Generate JSON output."""
        return json.dumps(self.analyze(), indent=2)


def main():
    parser = argparse.ArgumentParser(description="Analyze skill dependencies")
    parser.add_argument("path", help="Path to skill directory")
    parser.add_argument("--include", "-i", action="append", default=[],
                        help="Additional paths to include")
    parser.add_argument("--format", "-f", choices=["markdown", "json", "mermaid"],
                        default="markdown", help="Output format")
    parser.add_argument("--skill", "-s", help="Analyze specific skill only")
    parser.add_argument("--match", "-m", help="Find skill matching goal")
    
    args = parser.parse_args()
    
    analyzer = SkillDependencyAnalyzer(args.path, args.include)
    
    if args.skill:
        result = analyzer.get_dependencies(args.skill)
        print(json.dumps(result, indent=2))
    elif args.match:
        result = analyzer.match_skill(args.match)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No matching skill found")
    elif args.format == "markdown":
        print(analyzer.to_markdown())
    elif args.format == "json":
        print(analyzer.to_json())
    elif args.format == "mermaid":
        print(analyzer.to_mermaid())


if __name__ == "__main__":
    main()
