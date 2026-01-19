"""
CRUD operations for managing Agent Skills.

Usage:
    from manage_skills import list_skills, create_skill, delete_skill, create_version
    
    # List all skills
    skills = list_skills(client)
    
    # Create a skill
    skill = create_skill(client, "/path/to/skill", "My Skill")
    
    # Delete a skill
    delete_skill(client, "skill_01AbC...")
"""

import anthropic
from anthropic.lib import files_from_dir
from pathlib import Path
from typing import List, Optional


def list_skills(client: anthropic.Anthropic,
               source: Optional[str] = None,
               verbose: bool = True) -> List[dict]:
    """
    List all available skills.
    
    Args:
        client: Anthropic client instance
        source: Filter by source ("anthropic" or "custom")
        verbose: Whether to print skill information
        
    Returns:
        List of skill dictionaries
    """
    params = {"betas": ["skills-2025-10-02"]}
    
    if source:
        params["source"] = source
    
    skills_response = client.beta.skills.list(**params)
    
    skills_list = []
    
    for skill in skills_response.data:
        skill_info = {
            "id": skill.id,
            "display_title": skill.display_title,
            "source": skill.source,
            "latest_version": skill.latest_version,
            "created_at": skill.created_at
        }
        skills_list.append(skill_info)
        
        if verbose:
            print(f"{'📦' if skill.source == 'custom' else '🏢'} {skill.display_title}")
            print(f"   ID: {skill.id}")
            print(f"   Source: {skill.source}")
            print(f"   Version: {skill.latest_version}")
            print()
    
    return skills_list


def get_skill(client: anthropic.Anthropic,
             skill_id: str,
             verbose: bool = True) -> Optional[dict]:
    """
    Retrieve details about a specific skill.
    
    Args:
        client: Anthropic client instance
        skill_id: ID of the skill to retrieve
        verbose: Whether to print skill details
        
    Returns:
        Skill information dictionary or None if not found
    """
    try:
        skill = client.beta.skills.retrieve(
            skill_id=skill_id,
            betas=["skills-2025-10-02"]
        )
        
        skill_info = {
            "id": skill.id,
            "display_title": skill.display_title,
            "source": skill.source,
            "latest_version": skill.latest_version,
            "created_at": skill.created_at
        }
        
        if verbose:
            print(f"✅ Skill found: {skill.display_title}")
            print(f"   ID: {skill.id}")
            print(f"   Source: {skill.source}")
            print(f"   Latest version: {skill.latest_version}")
            print(f"   Created: {skill.created_at}")
        
        return skill_info
        
    except anthropic.NotFoundError:
        if verbose:
            print(f"❌ Skill not found: {skill_id}")
        return None


def create_skill(client: anthropic.Anthropic,
                skill_path: str,
                display_title: str,
                verbose: bool = True) -> Optional[dict]:
    """
    Create a new custom skill.
    
    Args:
        client: Anthropic client instance
        skill_path: Path to the skill directory
        display_title: Display title for the skill
        verbose: Whether to print progress messages
        
    Returns:
        Created skill information dictionary or None if failed
    """
    try:
        if verbose:
            print(f"⬆️  Uploading skill: {display_title}")
            print(f"   Path: {skill_path}")
        
        skill = client.beta.skills.create(
            display_title=display_title,
            files=files_from_dir(skill_path),
            betas=["skills-2025-10-02"]
        )
        
        skill_info = {
            "id": skill.id,
            "display_title": skill.display_title,
            "source": skill.source,
            "latest_version": skill.latest_version,
            "created_at": skill.created_at
        }
        
        if verbose:
            print(f"✅ Skill created successfully!")
            print(f"   ID: {skill.id}")
            print(f"   Version: {skill.latest_version}")
        
        return skill_info
        
    except Exception as e:
        if verbose:
            print(f"❌ Error creating skill: {e}")
        return None


def delete_skill(client: anthropic.Anthropic,
                skill_id: str,
                verbose: bool = True) -> bool:
    """
    Delete a skill and all its versions.
    
    Args:
        client: Anthropic client instance
        skill_id: ID of the skill to delete
        verbose: Whether to print progress messages
        
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        # First, delete all versions
        if verbose:
            print(f"🗑️  Deleting all versions for skill: {skill_id}")
        
        versions = client.beta.skills.versions.list(
            skill_id=skill_id,
            betas=["skills-2025-10-02"]
        )
        
        for version in versions.data:
            client.beta.skills.versions.delete(
                skill_id=skill_id,
                version=version.version,
                betas=["skills-2025-10-02"]
            )
            if verbose:
                print(f"   ✅ Deleted version: {version.version}")
        
        # Then delete the skill
        client.beta.skills.delete(
            skill_id=skill_id,
            betas=["skills-2025-10-02"]
        )
        
        if verbose:
            print(f"✅ Skill deleted: {skill_id}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Error deleting skill: {e}")
        return False


def create_version(client: anthropic.Anthropic,
                  skill_id: str,
                  skill_path: str,
                  verbose: bool = True) -> Optional[dict]:
    """
    Create a new version of an existing skill.
    
    Args:
        client: Anthropic client instance
        skill_id: ID of the skill to version
        skill_path: Path to the updated skill directory
        verbose: Whether to print progress messages
        
    Returns:
        Version information dictionary or None if failed
    """
    try:
        if verbose:
            print(f"⬆️  Creating new version for skill: {skill_id}")
            print(f"   Path: {skill_path}")
        
        version = client.beta.skills.versions.create(
            skill_id=skill_id,
            files=files_from_dir(skill_path),
            betas=["skills-2025-10-02"]
        )
        
        version_info = {
            "skill_id": skill_id,
            "version": version.version,
            "created_at": version.created_at
        }
        
        if verbose:
            print(f"✅ Version created successfully!")
            print(f"   Version: {version.version}")
            print(f"   Created: {version.created_at}")
        
        return version_info
        
    except Exception as e:
        if verbose:
            print(f"❌ Error creating version: {e}")
        return None


def list_versions(client: anthropic.Anthropic,
                 skill_id: str,
                 verbose: bool = True) -> List[dict]:
    """
    List all versions of a skill.
    
    Args:
        client: Anthropic client instance
        skill_id: ID of the skill
        verbose: Whether to print version information
        
    Returns:
        List of version dictionaries
    """
    try:
        versions_response = client.beta.skills.versions.list(
            skill_id=skill_id,
            betas=["skills-2025-10-02"]
        )
        
        versions_list = []
        
        for version in versions_response.data:
            version_info = {
                "skill_id": skill_id,
                "version": version.version,
                "created_at": version.created_at
            }
            versions_list.append(version_info)
            
            if verbose:
                print(f"📌 Version: {version.version}")
                print(f"   Created: {version.created_at}")
        
        return versions_list
        
    except Exception as e:
        if verbose:
            print(f"❌ Error listing versions: {e}")
        return []


def update_skill_workflow(client: anthropic.Anthropic,
                         skill_id: str,
                         skill_path: str,
                         verbose: bool = True) -> bool:
    """
    Complete workflow for updating a skill:
    1. Create new version
    2. Optionally delete old versions
    
    Args:
        client: Anthropic client instance
        skill_id: ID of the skill to update
        skill_path: Path to the updated skill directory
        verbose: Whether to print progress messages
        
    Returns:
        True if update successful, False otherwise
    """
    if verbose:
        print("🔄 Updating skill...")
        print("="*60)
    
    # Create new version
    new_version = create_version(client, skill_id, skill_path, verbose)
    
    if not new_version:
        return False
    
    if verbose:
        print("\n✅ Skill updated successfully!")
        print(f"   New version: {new_version['version']}")
        print("\nTo use this version in your API calls:")
        print(f"""
container={{
    "skills": [
        {{"type": "custom", "skill_id": "{skill_id}", "version": "{new_version['version']}"}}
    ]
}}
        """)
    
    return True


# Example usage
if __name__ == "__main__":
    import os
    
    # Initialize client
    client = anthropic.Anthropic()
    
    # Example 1: List all skills
    print("Example 1: List all skills")
    print("="*60)
    all_skills = list_skills(client)
    print(f"\nTotal skills: {len(all_skills)}\n")
    
    # Example 2: List only custom skills
    print("\nExample 2: List custom skills")
    print("="*60)
    custom_skills = list_skills(client, source="custom")
    print(f"\nCustom skills: {len(custom_skills)}\n")
    
    # Example 3: Get specific skill
    if custom_skills:
        print("\nExample 3: Get skill details")
        print("="*60)
        skill_id = custom_skills[0]["id"]
        get_skill(client, skill_id)
    
    # Example 4: List versions
    if custom_skills:
        print("\nExample 4: List skill versions")
        print("="*60)
        skill_id = custom_skills[0]["id"]
        versions = list_versions(client, skill_id)
        print(f"\nTotal versions: {len(versions)}\n")
