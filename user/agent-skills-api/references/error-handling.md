# Error Handling Guide

Common errors when using Agent Skills and their solutions.

## Beta Headers Errors

### Missing Beta Headers

**Error:**
```
anthropic.BadRequestError: Missing required beta header
```

**Solution:**
Always include all required beta headers:

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=[
        "code-execution-2025-08-25",  # Required for skills
        "skills-2025-10-02",          # Required for skills
        "files-api-2025-04-14"         # Required for file downloads
    ],
    ...
)
```

### Incorrect Beta Version

**Error:**
```
anthropic.BadRequestError: Unknown beta version
```

**Solution:**
Use exact beta versions as documented:
- Code execution: `code-execution-2025-08-25`
- Skills: `skills-2025-10-02`
- Files API: `files-api-2025-04-14`

## Skill Configuration Errors

### Missing Code Execution Tool

**Error:**
```
anthropic.BadRequestError: Skills require code execution tool
```

**Solution:**
Always include the code execution tool:

```python
response = client.beta.messages.create(
    ...
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

### Invalid Skill ID

**Error:**
```
anthropic.BadRequestError: Skill not found: skill_01AbC...
```

**Solutions:**
1. Verify skill exists: `client.beta.skills.retrieve(skill_id="...")`
2. Check for typos in skill_id
3. Ensure you have access to the skill (custom skills are workspace-specific)

```python
# Verify skill exists
try:
    skill = client.beta.skills.retrieve(
        skill_id="skill_01AbC...",
        betas=["skills-2025-10-02"]
    )
    print(f"Skill found: {skill.display_title}")
except anthropic.NotFoundError:
    print("Skill not found - check skill_id")
```

### Too Many Skills

**Error:**
```
anthropic.BadRequestError: Maximum 8 skills per request
```

**Solution:**
Reduce skills to 8 or fewer:

```python
# Bad: 9 skills
container={
    "skills": [skill1, skill2, skill3, skill4, skill5, skill6, skill7, skill8, skill9]
}

# Good: 8 skills
container={
    "skills": [skill1, skill2, skill3, skill4, skill5, skill6, skill7, skill8]
}
```

## Skill Creation Errors

### Invalid YAML Frontmatter

**Error:**
```
anthropic.BadRequestError: Invalid YAML frontmatter in SKILL.md
```

**Solution:**
Ensure YAML is properly formatted:

```yaml
# Good
---
name: my-skill
description: Complete description of the skill
---

# Bad - missing closing ---
---
name: my-skill
description: Incomplete frontmatter

# Bad - invalid name
---
name: My Skill  # Contains space and capitals
description: Description here
---
```

### Missing SKILL.md

**Error:**
```
anthropic.BadRequestError: Skill must include SKILL.md file
```

**Solution:**
Ensure SKILL.md is at the root level:

```python
# Good structure
files=[
    ("my-skill/SKILL.md", ...),
    ("my-skill/scripts/helper.py", ...)
]

# Bad - SKILL.md in wrong location
files=[
    ("my-skill/docs/SKILL.md", ...),  # Wrong location
    ("my-skill/scripts/helper.py", ...)
]
```

### Skill Name Violations

**Error:**
```
anthropic.BadRequestError: Invalid skill name
```

**Solution:**
Follow naming rules:

```yaml
# Good names
name: financial-analysis
name: pdf-processor
name: brand-guidelines

# Bad names
name: Financial Analysis  # Contains spaces and capitals
name: pdf_processor       # Contains underscore
name: anthropic-skill     # Reserved word
name: very-long-skill-name-that-exceeds-the-maximum-character-limit-of-sixty-four  # Too long
```

### Empty Description

**Error:**
```
anthropic.BadRequestError: Description cannot be empty
```

**Solution:**
Provide comprehensive description:

```yaml
# Bad
description: 

# Bad
description: A skill

# Good
description: Financial DCF analysis tool for company valuations. Use when analyzing companies, building DCF models, or performing investment analysis requiring present value calculations.
```

### File Size Exceeded

**Error:**
```
anthropic.BadRequestError: Skill exceeds 8MB size limit
```

**Solution:**
Reduce total file size:

```python
# Check file sizes
import os

def get_directory_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total += os.path.getsize(filepath)
    return total

size_mb = get_directory_size("./my-skill") / (1024 * 1024)
print(f"Skill size: {size_mb:.2f} MB")

if size_mb > 8:
    print("❌ Exceeds 8MB limit")
    # Compress large files or remove unnecessary assets
```

### Inconsistent Root Directories

**Error:**
```
anthropic.BadRequestError: All files must share common root directory
```

**Solution:**
Ensure all paths start with same directory:

```python
# Good - consistent root
files=[
    ("my-skill/SKILL.md", ...),
    ("my-skill/scripts/helper.py", ...),
    ("my-skill/references/docs.md", ...)
]

# Bad - inconsistent roots
files=[
    ("my-skill/SKILL.md", ...),
    ("other-skill/scripts/helper.py", ...)  # Different root!
]
```

## File Download Errors

### Missing Files API Beta

**Error:**
```
anthropic.BadRequestError: Missing required beta header for files API
```

**Solution:**
Include files API beta header:

```python
file_content = client.beta.files.download(
    file_id=file_id,
    betas=["files-api-2025-04-14"]  # Required
)
```

### File Not Found

**Error:**
```
anthropic.NotFoundError: File not found
```

**Solutions:**
1. Verify file_id from response
2. Check that skill actually created the file
3. Ensure file wasn't already deleted

```python
# Extract and validate file IDs
def extract_file_ids(response):
    file_ids = []
    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content
            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)
                        print(f"Found file: {file.file_id}")
    
    if not file_ids:
        print("⚠️  No files in response")
    
    return file_ids
```

## Version Management Errors

### Invalid Version Format

**Error:**
```
anthropic.BadRequestError: Invalid version format
```

**Solution:**
Use correct version format for skill type:

```python
# Anthropic skills - date format or "latest"
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "20251013"},  # Good
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}     # Good
    ]
}

# Custom skills - epoch timestamp or "latest"
container={
    "skills": [
        {"type": "custom", "skill_id": "skill_01...", "version": "1759178010641129"},  # Good
        {"type": "custom", "skill_id": "skill_01...", "version": "latest"}            # Good
    ]
}
```

### Cannot Delete Skill with Versions

**Error:**
```
anthropic.BadRequestError: Cannot delete skill with existing versions
```

**Solution:**
Delete all versions first:

```python
# Step 1: List and delete all versions
versions = client.beta.skills.versions.list(
    skill_id="skill_01AbC...",
    betas=["skills-2025-10-02"]
)

for version in versions.data:
    client.beta.skills.versions.delete(
        skill_id="skill_01AbC...",
        version=version.version,
        betas=["skills-2025-10-02"]
    )
    print(f"Deleted version: {version.version}")

# Step 2: Delete the skill
client.beta.skills.delete(
    skill_id="skill_01AbC...",
    betas=["skills-2025-10-02"]
)
print("Skill deleted")
```

## General Error Handling Pattern

Comprehensive error handling:

```python
import anthropic

def safe_skill_request(client, skills, message):
    """Make a skill request with comprehensive error handling."""
    try:
        response = client.beta.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            betas=[
                "code-execution-2025-08-25",
                "skills-2025-10-02"
            ],
            container={"skills": skills},
            messages=[{"role": "user", "content": message}],
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
        )
        return response, None
        
    except anthropic.BadRequestError as e:
        error_msg = str(e)
        
        if "skill" in error_msg.lower():
            return None, f"Skill configuration error: {error_msg}"
        elif "beta" in error_msg.lower():
            return None, f"Beta header error: {error_msg}"
        elif "tool" in error_msg.lower():
            return None, f"Tool configuration error: {error_msg}"
        else:
            return None, f"Bad request: {error_msg}"
            
    except anthropic.NotFoundError as e:
        return None, f"Resource not found: {e}"
        
    except anthropic.APIError as e:
        return None, f"API error: {e}"
        
    except Exception as e:
        return None, f"Unexpected error: {e}"

# Usage
response, error = safe_skill_request(
    client=client,
    skills=[{"type": "anthropic", "skill_id": "xlsx", "version": "latest"}],
    message="Analyze this data"
)

if error:
    print(f"Error: {error}")
else:
    print(f"Success: {response.content[0].text}")
```

## Debugging Tips

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Verify Skill Exists

```python
def verify_skill(client, skill_id):
    """Verify skill exists and is accessible."""
    try:
        skill = client.beta.skills.retrieve(
            skill_id=skill_id,
            betas=["skills-2025-10-02"]
        )
        print(f"✅ Skill found: {skill.display_title}")
        print(f"   Latest version: {skill.latest_version}")
        return True
    except anthropic.NotFoundError:
        print(f"❌ Skill not found: {skill_id}")
        return False
    except Exception as e:
        print(f"❌ Error verifying skill: {e}")
        return False
```

### Validate File Creation

```python
def validate_files_created(response):
    """Check if any files were created."""
    file_ids = []
    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content
            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)
    
    if file_ids:
        print(f"✅ {len(file_ids)} file(s) created")
        for fid in file_ids:
            print(f"   - {fid}")
    else:
        print("⚠️  No files created in response")
    
    return file_ids
```
