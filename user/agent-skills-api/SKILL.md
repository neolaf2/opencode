---
name: agent-skills-api
description: Comprehensive guide for using Agent Skills with the Claude API, including both Anthropic pre-built skills and custom skills. Use when working with the Claude API to extend capabilities through Skills, create custom Skills, manage Skill versions, handle file downloads from Skills, or integrate Skills into multi-turn conversations. Covers setup, CRUD operations, file handling, versioning, error handling, and best practices.
---

# Agent Skills API Integration

This skill provides comprehensive guidance for using Agent Skills with the Claude API.

## Overview

Agent Skills extend Claude's capabilities through the API in two ways:

1. **Anthropic Skills** - Pre-built skills (docx, xlsx, pptx, pdf) maintained by Anthropic
2. **Custom Skills** - Skills you create and upload for your workspace

Both types integrate identically in the API using the `container` parameter with code execution.

## Quick Start Workflow

1. **Setup**: Enable required beta headers
2. **Choose Skills**: Use Anthropic skills or create custom skills
3. **Integrate**: Add skills to API requests via `container` parameter
4. **Execute**: Handle responses and download created files
5. **Iterate**: Manage versions and refine usage

## Core Integration Pattern

All skills use this structure in the Messages API:

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",  # or "custom"
                "skill_id": "xlsx",   # or skill_01AbC...
                "version": "latest"   # or specific version
            }
        ]
    },
    messages=[{"role": "user", "content": "Your request"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

**Key requirements:**
- Beta headers: `code-execution-2025-08-25` and `skills-2025-10-02`
- Code execution tool must be enabled
- Maximum 8 skills per request
- Skills specified in `container.skills` array

## Using Anthropic Skills

Anthropic provides pre-built skills for common document types:

**Available skills:**
- `pptx` - PowerPoint presentations
- `xlsx` - Excel spreadsheets
- `docx` - Word documents
- `pdf` - PDF manipulation

**Version format:** Date-based (e.g., `20251013`) or `"latest"`

See `references/anthropic-skills-examples.md` for complete usage examples.

## Creating Custom Skills

Follow this workflow to create custom skills:

1. **Prepare skill files**
   - Required: `SKILL.md` with YAML frontmatter
   - Optional: `scripts/`, `references/`, `assets/` directories
   - Total size limit: 8MB

2. **Upload skill**
   ```python
   from anthropic.lib import files_from_dir
   
   skill = client.beta.skills.create(
       display_title="My Skill",
       files=files_from_dir("/path/to/skill"),
       betas=["skills-2025-10-02"]
   )
   ```

3. **Use generated skill_id** in API requests

**YAML frontmatter requirements:**
- `name`: Max 64 chars, lowercase letters/numbers/hyphens, no XML tags, no reserved words
- `description`: Max 1024 chars, non-empty, no XML tags

See `references/custom-skills-guide.md` for detailed creation guidance and `scripts/create_skill.py` for a template.

## File Downloads

Skills that create documents return `file_id` values. Download files using the Files API:

```python
# Extract file IDs from response
file_ids = []
for item in response.content:
    if item.type == 'bash_code_execution_tool_result':
        for file in item.content.content:
            if hasattr(file, 'file_id'):
                file_ids.append(file.file_id)

# Download files
for file_id in file_ids:
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    file_content.write_to_file(f"output_{file_id}.xlsx")
```

**Files API beta:** `files-api-2025-04-14`

See `scripts/download_files.py` for a complete helper function.

## Multi-Turn Conversations

Reuse containers across turns by specifying the container ID:

```python
# First request
response1 = client.beta.messages.create(...)

# Continue with same container
response2 = client.beta.messages.create(
    container={"id": response1.container.id, "skills": [...]},
    messages=[
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": response1.content},
        {"role": "user", "content": "Follow-up message"}
    ],
    ...
)
```

**Handling long operations:**
- Watch for `stop_reason == "pause_turn"`
- Append response to messages and continue
- Maximum ~10 retries recommended

See `references/multi-turn-patterns.md` for complete examples.

## Version Management

**Anthropic skills:**
- Versions: Date format (e.g., `20251013`)
- Use `"latest"` for automatic updates
- Pin specific versions for stability

**Custom skills:**
- Versions: Epoch timestamps (e.g., `1759178010641129`)
- Create new versions when updating
- Use `"latest"` in development, pin in production

```python
# Create new version
new_version = client.beta.skills.versions.create(
    skill_id="skill_01AbC...",
    files=files_from_dir("/path/to/updated"),
    betas=["skills-2025-10-02"]
)
```

## Skill Management Operations

**List all skills:**
```python
skills = client.beta.skills.list(betas=["skills-2025-10-02"])
# Filter by source
custom_skills = client.beta.skills.list(
    source="custom",
    betas=["skills-2025-10-02"]
)
```

**Retrieve skill details:**
```python
skill = client.beta.skills.retrieve(
    skill_id="skill_01AbC...",
    betas=["skills-2025-10-02"]
)
```

**Delete skill:**
```python
# Must delete all versions first
versions = client.beta.skills.versions.list(skill_id="skill_01AbC...")
for version in versions.data:
    client.beta.skills.versions.delete(
        skill_id="skill_01AbC...",
        version=version.version,
        betas=["skills-2025-10-02"]
    )

# Then delete skill
client.beta.skills.delete(
    skill_id="skill_01AbC...",
    betas=["skills-2025-10-02"]
)
```

See `scripts/manage_skills.py` for CRUD operation helpers.

## Best Practices

**Skill selection:**
- Only include skills needed for the task
- Maximum 8 skills per request
- Combine related skills for workflows

**Version pinning:**
- Use `"latest"` in development
- Pin specific versions in production
- Document version dependencies

**Prompt caching:**
- Keep skill list consistent across requests
- Changing skills breaks cache
- Group related operations together

**Error handling:**
- Wrap API calls in try-except blocks
- Check for skill-specific error messages
- Validate file downloads completed

## Environment Constraints

Skills run in code execution containers with:
- No network access
- No runtime package installation
- Isolated environment per request
- Pre-installed packages only

## Common Patterns

**Data analysis + presentation:**
```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
        {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
    ]
}
```

**Custom domain logic + documents:**
```python
container={
    "skills": [
        {"type": "custom", "skill_id": "skill_01...", "version": "latest"},
        {"type": "anthropic", "skill_id": "docx", "version": "latest"}
    ]
}
```

## Available Resources

- **Scripts** (`scripts/`):
  - `create_skill.py` - Template for creating custom skills
  - `download_files.py` - Helper for downloading files from responses
  - `manage_skills.py` - CRUD operations for skills

- **References** (`references/`):
  - `anthropic-skills-examples.md` - Complete examples for each Anthropic skill
  - `custom-skills-guide.md` - Detailed guide for creating custom skills
  - `multi-turn-patterns.md` - Patterns for multi-turn conversations
  - `error-handling.md` - Common errors and solutions
