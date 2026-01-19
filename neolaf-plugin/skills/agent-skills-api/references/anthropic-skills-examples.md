# Anthropic Skills Examples

Complete examples for using each Anthropic pre-built skill.

## PowerPoint (pptx)

**Basic presentation creation:**
```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]
    },
    messages=[{
        "role": "user",
        "content": "Create a presentation about renewable energy with 5 slides"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

**Trigger phrases:**
- "Create a presentation..."
- "Make a PowerPoint..."
- "Build slides about..."

## Excel (xlsx)

**Data analysis and spreadsheet creation:**
```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{"type": "anthropic", "skill_id": "xlsx", "version": "latest"}]
    },
    messages=[{
        "role": "user",
        "content": "Create a budget spreadsheet with formulas for monthly expenses"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

**Trigger phrases:**
- "Create a spreadsheet..."
- "Analyze this data..."
- "Build an Excel file..."
- "Generate a financial model..."

## Word (docx)

**Document creation and editing:**
```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{"type": "anthropic", "skill_id": "docx", "version": "latest"}]
    },
    messages=[{
        "role": "user",
        "content": "Write a formal business proposal document"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

**Trigger phrases:**
- "Write a document..."
- "Create a report..."
- "Draft a proposal..."

## PDF (pdf)

**PDF manipulation:**
```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{"type": "anthropic", "skill_id": "pdf", "version": "latest"}]
    },
    messages=[{
        "role": "user",
        "content": "Extract text from this PDF and create a summary"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

**Trigger phrases:**
- "Extract from PDF..."
- "Merge PDFs..."
- "Fill PDF form..."

## Combined Workflow Example

**Financial analysis with multiple skills:**
```python
import anthropic

client = anthropic.Anthropic()

# Step 1: Analyze data in Excel
response1 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Analyze Q4 sales data and create a summary spreadsheet"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# Step 2: Create presentation from analysis
response2 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": response1.container.id,  # Reuse container
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
        ]
    },
    messages=[
        {"role": "user", "content": "Analyze Q4 sales data and create a summary spreadsheet"},
        {"role": "assistant", "content": response1.content},
        {"role": "user", "content": "Now create a presentation with the key findings"}
    ],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# Step 3: Download files
for file_id in extract_file_ids(response2):
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    file_metadata = client.beta.files.retrieve_metadata(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    file_content.write_to_file(file_metadata.filename)
```

## Version Pinning Example

**Using specific versions for stability:**
```python
# Production: Pin to specific version
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "20251013"}
    ]
}

# Development: Use latest
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
    ]
}
```
