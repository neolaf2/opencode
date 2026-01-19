"""
Template for creating and uploading custom Agent Skills.

Usage:
    python create_skill.py --path /path/to/skill --title "My Skill"
"""

import anthropic
from anthropic.lib import files_from_dir
import argparse
from pathlib import Path


def validate_skill_structure(skill_path):
    """Validate that skill has required structure."""
    path = Path(skill_path)
    
    if not path.exists():
        raise ValueError(f"Path does not exist: {skill_path}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {skill_path}")
    
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"Missing required SKILL.md file in {skill_path}")
    
    # Validate YAML frontmatter exists
    with open(skill_md, 'r') as f:
        content = f.read()
        if not content.startswith('---'):
            raise ValueError("SKILL.md must start with YAML frontmatter (---)")
    
    print(f"✅ Skill structure validated: {skill_path}")


def get_directory_size(path):
    """Calculate total size of directory in MB."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total += os.path.getsize(filepath)
    return total / (1024 * 1024)  # Convert to MB


def create_skill(skill_path, display_title, api_key=None):
    """Create and upload a custom skill."""
    
    # Validate structure
    validate_skill_structure(skill_path)
    
    # Check size
    size_mb = get_directory_size(skill_path)
    print(f"📦 Skill size: {size_mb:.2f} MB")
    
    if size_mb > 8:
        raise ValueError(f"Skill exceeds 8MB limit (current: {size_mb:.2f} MB)")
    
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Upload skill
    print(f"⬆️  Uploading skill: {display_title}")
    
    skill = client.beta.skills.create(
        display_title=display_title,
        files=files_from_dir(skill_path),
        betas=["skills-2025-10-02"]
    )
    
    print(f"✅ Skill created successfully!")
    print(f"   Skill ID: {skill.id}")
    print(f"   Latest version: {skill.latest_version}")
    print(f"   Created at: {skill.created_at}")
    
    return skill


def example_usage():
    """Show example usage of the created skill."""
    return """
# Example: Using your custom skill in API requests

import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "custom", "skill_id": "YOUR_SKILL_ID", "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": "Your request here"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
"""


def main():
    parser = argparse.ArgumentParser(
        description="Create and upload a custom Agent Skill"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the skill directory"
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Display title for the skill"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    try:
        skill = create_skill(args.path, args.title, args.api_key)
        
        print("\n" + "="*60)
        print("Next steps:")
        print("="*60)
        print(example_usage().replace("YOUR_SKILL_ID", skill.id))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import os
    exit(main())
