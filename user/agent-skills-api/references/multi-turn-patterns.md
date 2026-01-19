# Multi-Turn Conversation Patterns

Patterns for using Skills across multiple conversation turns.

## Basic Container Reuse

Reuse the same container across turns to maintain state:

```python
import anthropic

client = anthropic.Anthropic()

# Turn 1: Initial request
response1 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": "Create a budget spreadsheet"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

container_id = response1.container.id

# Turn 2: Follow-up request
messages = [
    {"role": "user", "content": "Create a budget spreadsheet"},
    {"role": "assistant", "content": response1.content},
    {"role": "user", "content": "Add a row for quarterly projections"}
]

response2 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": container_id,  # Reuse container
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

## Handling pause_turn

Long-running operations may pause and require continuation:

```python
def handle_long_operation(client, initial_message, max_retries=10):
    """Handle Skills that may pause during execution."""
    
    messages = [{"role": "user", "content": initial_message}]
    container_id = None
    
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02"],
        container={
            "skills": [
                {"type": "custom", "skill_id": "skill_01AbC...", "version": "latest"}
            ]
        },
        messages=messages,
        tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
    )
    
    container_id = response.container.id
    
    # Handle pause_turn
    for i in range(max_retries):
        if response.stop_reason != "pause_turn":
            break
            
        print(f"Operation paused, continuing... (attempt {i+1}/{max_retries})")
        
        # Append response and continue
        messages.append({"role": "assistant", "content": response.content})
        
        response = client.beta.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            betas=["code-execution-2025-08-25", "skills-2025-10-02"],
            container={
                "id": container_id,
                "skills": [
                    {"type": "custom", "skill_id": "skill_01AbC...", "version": "latest"}
                ]
            },
            messages=messages,
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
        )
    
    return response

# Usage
response = handle_long_operation(
    client,
    "Process this 1000-page dataset"
)
```

## Adding Skills Mid-Conversation

Add new skills in later turns (note: breaks prompt cache):

```python
# Turn 1: Start with Excel
response1 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": "Analyze sales data"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# Turn 2: Add PowerPoint
messages = [
    {"role": "user", "content": "Analyze sales data"},
    {"role": "assistant", "content": response1.content},
    {"role": "user", "content": "Now create a presentation"}
]

response2 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": response1.container.id,
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"}  # Added
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

## Stateful Workflow Example

Complete workflow with file generation and download:

```python
import anthropic
from pathlib import Path

def extract_file_ids(response):
    """Extract file IDs from response."""
    file_ids = []
    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content
            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)
    return file_ids

def download_files(client, file_ids, output_dir="./outputs"):
    """Download all files from response."""
    Path(output_dir).mkdir(exist_ok=True)
    
    for file_id in file_ids:
        metadata = client.beta.files.retrieve_metadata(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )
        content = client.beta.files.download(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )
        
        filepath = Path(output_dir) / metadata.filename
        content.write_to_file(str(filepath))
        print(f"Downloaded: {filepath}")

# Main workflow
client = anthropic.Anthropic()
container_id = None
messages = []

# Step 1: Analyze data
messages.append({"role": "user", "content": "Analyze Q4 sales data"})

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

container_id = response.container.id
messages.append({"role": "assistant", "content": response.content})

# Step 2: Create summary
messages.append({"role": "user", "content": "Create a summary document"})

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": container_id,
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "anthropic", "skill_id": "docx", "version": "latest"}
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

messages.append({"role": "assistant", "content": response.content})

# Step 3: Create presentation
messages.append({"role": "user", "content": "Create a presentation with key findings"})

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": container_id,
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "anthropic", "skill_id": "docx", "version": "latest"},
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# Download all generated files
file_ids = extract_file_ids(response)
download_files(client, file_ids)
```

## Conversation Context Management

Manage growing conversation history:

```python
class SkillConversation:
    def __init__(self, client, skills, max_tokens=4096):
        self.client = client
        self.skills = skills
        self.container_id = None
        self.messages = []
        self.max_tokens = max_tokens
        
    def send(self, message):
        """Send a message and get response."""
        self.messages.append({"role": "user", "content": message})
        
        response = self.client.beta.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=self.max_tokens,
            betas=["code-execution-2025-08-25", "skills-2025-10-02"],
            container={
                "id": self.container_id if self.container_id else None,
                "skills": self.skills
            },
            messages=self.messages,
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
        )
        
        if not self.container_id:
            self.container_id = response.container.id
            
        self.messages.append({"role": "assistant", "content": response.content})
        return response
    
    def get_files(self):
        """Extract file IDs from last response."""
        if not self.messages:
            return []
        
        last_response_content = self.messages[-1]["content"]
        file_ids = []
        
        for item in last_response_content:
            if item.type == 'bash_code_execution_tool_result':
                content_item = item.content
                if content_item.type == 'bash_code_execution_result':
                    for file in content_item.content:
                        if hasattr(file, 'file_id'):
                            file_ids.append(file.file_id)
        
        return file_ids

# Usage
conv = SkillConversation(
    client=client,
    skills=[
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
        {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
    ]
)

response1 = conv.send("Analyze sales data")
response2 = conv.send("Create a presentation")
response3 = conv.send("Add a financial summary slide")

# Download files
for file_id in conv.get_files():
    download_files(client, [file_id])
```

## Best Practices

1. **Reuse containers**: Always specify `container.id` for follow-up requests
2. **Build message history**: Append all messages to maintain context
3. **Handle pauses**: Implement retry logic for `pause_turn`
4. **Monitor token usage**: Long conversations consume more tokens
5. **Clean up files**: Download and delete files after completion
6. **Cache awareness**: Changing skills mid-conversation breaks cache
