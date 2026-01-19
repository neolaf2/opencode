#!/usr/bin/env python3
"""
Copy Skill - Level 1 Skill Acquisition

Copies skills from external sources to local catalog.

Usage:
    python copy_skill.py <source> <target>

Examples:
    # Copy from plugin
    python copy_skill.py ~/.claude/plugins/agent-sdk-toolkit/skills/agent-sdk-basics ~/.claude/skills/

    # Copy from another project
    python copy_skill.py /path/to/project/user/some-skill ./user/

    # Copy with explicit name
    python copy_skill.py /source/skill ./target/ --name my-custom-name
"""

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SkillMetadata:
    """Metadata for a copied skill."""
    name: str
    source_path: str
    target_path: str
    copied_at: str
    source_type: str  # "plugin", "project", "user", "remote"
    files_copied: List[str]


def find_skill_md(skill_path: Path) -> Optional[Path]:
    """Find SKILL.md in skill directory."""
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        return skill_md
    return None


def parse_skill_frontmatter(skill_md: Path) -> Dict:
    """Parse YAML frontmatter from SKILL.md."""
    content = skill_md.read_text()

    if not content.startswith("---"):
        return {}

    # Find end of frontmatter
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}

    frontmatter = content[3:end_idx].strip()

    # Simple YAML parsing (key: value)
    result = {}
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()

    return result


def validate_skill(skill_path: Path) -> tuple[bool, List[str]]:
    """Validate skill structure."""
    issues = []

    if not skill_path.exists():
        issues.append(f"Source path does not exist: {skill_path}")
        return False, issues

    if not skill_path.is_dir():
        issues.append(f"Source is not a directory: {skill_path}")
        return False, issues

    skill_md = find_skill_md(skill_path)
    if not skill_md:
        issues.append("Missing SKILL.md file")
        return False, issues

    # Parse and validate frontmatter
    meta = parse_skill_frontmatter(skill_md)
    if not meta.get("name"):
        issues.append("SKILL.md missing 'name' in frontmatter")
    if not meta.get("description"):
        issues.append("SKILL.md missing 'description' in frontmatter")

    return len(issues) == 0, issues


def determine_source_type(source_path: Path) -> str:
    """Determine the type of skill source."""
    path_str = str(source_path)

    if ".claude/plugins" in path_str:
        return "plugin"
    elif ".claude/skills" in path_str:
        return "user"
    elif "user/" in path_str or "/user/" in path_str:
        return "project"
    elif path_str.startswith("http"):
        return "remote"
    else:
        return "local"


def copy_skill(
    source: Path,
    target: Path,
    name: Optional[str] = None,
    dry_run: bool = False
) -> SkillMetadata:
    """
    Copy a skill from source to target.

    Args:
        source: Source skill directory
        target: Target directory (skill will be copied as subdirectory)
        name: Optional custom name for the copied skill
        dry_run: If True, only show what would be done

    Returns:
        Metadata about the copy operation
    """
    source = Path(source).resolve()
    target = Path(target).resolve()

    # Validate source
    valid, issues = validate_skill(source)
    if not valid:
        raise ValueError(f"Invalid skill: {', '.join(issues)}")

    # Get skill name
    if name:
        skill_name = name
    else:
        meta = parse_skill_frontmatter(source / "SKILL.md")
        skill_name = meta.get("name", source.name)

    # Normalize skill name (kebab-case)
    skill_name = skill_name.lower().replace(" ", "-").replace("_", "-")

    # Target skill directory
    target_skill_dir = target / skill_name

    if target_skill_dir.exists():
        raise ValueError(f"Target already exists: {target_skill_dir}")

    # Collect files to copy
    files_to_copy = []
    for item in source.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(source)
            files_to_copy.append(str(rel_path))

    if dry_run:
        print(f"[DRY RUN] Would copy skill '{skill_name}'")
        print(f"  Source: {source}")
        print(f"  Target: {target_skill_dir}")
        print(f"  Files: {len(files_to_copy)}")
        for f in files_to_copy[:10]:
            print(f"    - {f}")
        if len(files_to_copy) > 10:
            print(f"    ... and {len(files_to_copy) - 10} more")
    else:
        # Create target directory
        target_skill_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files
        for item in source.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(source)
                dest = target_skill_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

        print(f"✓ Copied skill '{skill_name}' to {target_skill_dir}")

    # Build metadata
    metadata = SkillMetadata(
        name=skill_name,
        source_path=str(source),
        target_path=str(target_skill_dir),
        copied_at=datetime.now(timezone.utc).isoformat(),
        source_type=determine_source_type(source),
        files_copied=files_to_copy
    )

    return metadata


def save_acquisition_record(metadata: SkillMetadata, target: Path):
    """Save acquisition record for tracking."""
    records_file = target / ".skill-acquisitions.json"

    records = []
    if records_file.exists():
        with open(records_file) as f:
            records = json.load(f)

    records.append({
        "name": metadata.name,
        "source_path": metadata.source_path,
        "target_path": metadata.target_path,
        "copied_at": metadata.copied_at,
        "source_type": metadata.source_type,
        "strategy": "copy"
    })

    with open(records_file, "w") as f:
        json.dump(records, f, indent=2)


def list_available_skills(search_paths: List[Path]) -> List[Dict]:
    """List available skills in search paths."""
    skills = []

    for search_path in search_paths:
        if not search_path.exists():
            continue

        for item in search_path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                meta = parse_skill_frontmatter(item / "SKILL.md")
                skills.append({
                    "name": meta.get("name", item.name),
                    "path": str(item),
                    "source_type": determine_source_type(item),
                    "description": meta.get("description", "")[:100]
                })

    return skills


def main():
    parser = argparse.ArgumentParser(
        description="Copy skills between catalogs (Level 1 Skill Acquisition)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Copy command
    copy_parser = subparsers.add_parser("copy", help="Copy a skill")
    copy_parser.add_argument("source", help="Source skill directory")
    copy_parser.add_argument("target", help="Target directory")
    copy_parser.add_argument("--name", help="Custom name for copied skill")
    copy_parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    # List command
    list_parser = subparsers.add_parser("list", help="List available skills")
    list_parser.add_argument("--paths", nargs="+", help="Paths to search")

    # Default: treat positional args as copy
    if len(sys.argv) > 1 and sys.argv[1] not in ["copy", "list", "-h", "--help"]:
        sys.argv.insert(1, "copy")

    args = parser.parse_args()

    if args.command == "copy":
        try:
            metadata = copy_skill(
                Path(args.source),
                Path(args.target),
                name=args.name,
                dry_run=args.dry_run
            )

            if not args.dry_run:
                save_acquisition_record(metadata, Path(args.target))
                print(f"  Source type: {metadata.source_type}")
                print(f"  Files copied: {len(metadata.files_copied)}")

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        # Default search paths
        home = Path.home()
        default_paths = [
            home / ".claude" / "skills",
            home / ".claude" / "plugins",
            Path.cwd() / "user",
            Path.cwd() / ".claude" / "skills",
        ]

        search_paths = [Path(p) for p in args.paths] if args.paths else default_paths

        skills = list_available_skills(search_paths)

        if not skills:
            print("No skills found in search paths")
        else:
            print(f"Found {len(skills)} skills:\n")
            for skill in skills:
                print(f"  {skill['name']}")
                print(f"    Path: {skill['path']}")
                print(f"    Type: {skill['source_type']}")
                if skill['description']:
                    print(f"    Desc: {skill['description']}")
                print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
