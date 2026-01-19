# Custom Skills Creation Guide

Detailed guide for creating, uploading, and managing custom Agent Skills.

## Skill Structure

Every custom skill must follow this structure:

```
my-skill/
├── SKILL.md (required)
├── scripts/ (optional)
│   └── helper.py
├── references/ (optional)
│   └── documentation.md
└── assets/ (optional)
    └── template.json
```

## SKILL.md Requirements

The `SKILL.md` file is mandatory and must include YAML frontmatter:

```markdown
---
name: my-skill
description: Complete description of what the skill does and when to use it
---

# My Skill

Instructions for using the skill...
```

### Frontmatter Rules

**name:**
- Maximum 64 characters
- Lowercase letters, numbers, hyphens only
- No XML tags
- Cannot use reserved words: "anthropic", "claude"
- Examples: `financial-analysis`, `brand-guidelines`, `data-pipeline`

**description:**
- Maximum 1024 characters
- Must be non-empty
- No XML tags
- Should be comprehensive - this is how Claude determines when to use the skill
- Include both what the skill does AND when to use it

### Good Description Examples

✅ Good:
```yaml
description: Financial DCF (Discounted Cash Flow) analysis tool. Use when analyzing company valuations, building financial models with DCF methodology, or performing investment analysis requiring present value calculations. Handles revenue projections, WACC calculations, and terminal value computations.
```

✅ Good:
```yaml
description: Company brand guidelines enforcer. Use when creating presentations, documents, or any content that should follow company branding standards. Applies correct colors (primary: #0066CC, secondary: #FF6600), typography (Helvetica for headings, Arial for body), and logo usage rules.
```

❌ Bad (too vague):
```yaml
description: A skill for financial analysis
```

❌ Bad (doesn't specify when to use):
```yaml
description: Performs DCF analysis with revenue projections and WACC calculations
```

## Upload Methods

### Method 1: Using files_from_dir (Recommended for Python)

```python
from anthropic.lib import files_from_dir

skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=files_from_dir("/path/to/my-skill"),
    betas=["skills-2025-10-02"]
)

print(f"Created skill: {skill.id}")
print(f"Latest version: {skill.latest_version}")
```

### Method 2: Using a Zip File

```python
skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=[("skill.zip", open("my-skill.zip", "rb"))],
    betas=["skills-2025-10-02"]
)
```

### Method 3: Using File Tuples

```python
skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=[
        ("my-skill/SKILL.md", open("my-skill/SKILL.md", "rb"), "text/markdown"),
        ("my-skill/scripts/analyze.py", open("my-skill/scripts/analyze.py", "rb"), "text/x-python"),
        ("my-skill/references/schema.md", open("my-skill/references/schema.md", "rb"), "text/markdown"),
    ],
    betas=["skills-2025-10-02"]
)
```

**Important:** All file paths must share a common root directory (e.g., `my-skill/`)

## Size Limits

- Total upload size: 8MB (all files combined)
- No individual file size limits
- Compress large reference files if needed

## Skill Organization Patterns

### Pattern 1: Scripts-Heavy Skill

For skills that primarily execute code:

```
pdf-processor/
├── SKILL.md (instructions)
├── scripts/
│   ├── rotate.py
│   ├── merge.py
│   ├── extract_text.py
│   └── fill_form.py
└── references/
    └── pypdf_api.md
```

### Pattern 2: Reference-Heavy Skill

For skills with extensive documentation:

```
company-knowledge/
├── SKILL.md (overview)
├── references/
│   ├── database_schema.md
│   ├── api_documentation.md
│   ├── business_rules.md
│   └── policies.md
└── scripts/
    └── query_builder.py
```

### Pattern 3: Template-Based Skill

For skills that use templates:

```
brand-styling/
├── SKILL.md (guidelines)
├── assets/
│   ├── template.pptx
│   ├── logo.png
│   └── fonts/
│       ├── corporate-regular.ttf
│       └── corporate-bold.ttf
└── references/
    └── brand_manual.md
```

## Progressive Disclosure

Keep SKILL.md concise (under 500 lines). Move detailed information to `references/`:

**In SKILL.md:**
```markdown
## Data Analysis

Use `scripts/analyze.py` for statistical analysis.

For detailed API documentation, see `references/api_docs.md`.
For example queries, see `references/examples.md`.
```

**In references/api_docs.md:**
```markdown
# Complete API Reference

[Detailed documentation...]
```

## Example: Creating a Financial Analysis Skill

```python
import anthropic
from anthropic.lib import files_from_dir

client = anthropic.Anthropic()

# 1. Prepare skill files
# Create directory structure:
#   financial-dcf/
#   ├── SKILL.md
#   ├── scripts/
#   │   └── dcf_calculator.py
#   └── references/
#       └── valuation_methods.md

# 2. Upload skill
skill = client.beta.skills.create(
    display_title="Financial DCF Analysis",
    files=files_from_dir("./financial-dcf"),
    betas=["skills-2025-10-02"]
)

print(f"Skill created: {skill.id}")

# 3. Use skill in API request
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "custom", "skill_id": skill.id, "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Build a DCF model for a SaaS company with $10M ARR growing at 30% annually"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

## Testing Your Skill

Before deploying, test the skill:

```python
# 1. Create skill
skill = client.beta.skills.create(...)

# 2. Test with various prompts
test_prompts = [
    "Analyze this company's valuation",
    "Build a DCF model",
    "What's the enterprise value?"
]

for prompt in test_prompts:
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02"],
        container={
            "skills": [{"type": "custom", "skill_id": skill.id, "version": "latest"}]
        },
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
    )
    
    # Verify skill was used correctly
    print(f"Prompt: {prompt}")
    print(f"Response: {response.content[0].text[:200]}...")
    print("---")
```

## Common Pitfalls

### ❌ Missing SKILL.md
```
my-skill/
└── scripts/
    └── helper.py
```
Error: "Skill must include SKILL.md"

### ❌ Invalid YAML frontmatter
```yaml
---
name: My Skill  # Contains space and capital letters
description: 
---
```
Error: "Invalid skill name" or "Description cannot be empty"

### ❌ Inconsistent root directories
```python
files=[
    ("skill/SKILL.md", ...),
    ("different-skill/script.py", ...)  # Different root!
]
```
Error: "All files must share common root directory"

### ❌ File too large
```
Total size: 10MB
```
Error: "Skill exceeds 8MB size limit"

## Best Practices

1. **Start simple**: Begin with just SKILL.md, add resources as needed
2. **Test scripts**: Run all scripts locally before uploading
3. **Document clearly**: Write descriptions assuming Claude knows nothing about your domain
4. **Version management**: Create new versions instead of deleting/recreating
5. **Organize references**: Split large documentation into focused files
6. **Use templates**: Store reusable templates in `assets/`
7. **Keep it lean**: Remove unused example files and directories
