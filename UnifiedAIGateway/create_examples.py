import os

examples = {
    "examples/model_migration/README.md": """# Model Migration Example

This example demonstrates how to seamlessly migrate an application from OpenAI to Gemini without changing any application code.

## Setup
1. Define your original models in `config.yaml` using OpenAI.
2. Change the provider to `gemini` in `config.yaml`.
3. Run `python app.py` to see the same request routed to Gemini.

## Data
Synthetic prompts are stored in `data/prompts.json`.
""",
    "examples/model_migration/data/prompts.json": """[
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "user", "content": "Write a python script to reverse a string."}
]""",
    "examples/model_migration/config.yaml": """gateway:
  host: 0.0.0.0
  port: 8080
providers:
  mock_openai:
    type: mock
  mock_gemini:
    type: mock
models:
  # The application hardcodes "gpt-4" but we route it to gemini here!
  gpt-4:
    provider: mock_gemini
    model: gemini-1.5-pro
""",
    "examples/model_migration/app.py": """import urllib.request, json
# Pretend we are the OpenAI client calling the Gateway
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    print("Migration successful! Received:", response.read().decode())
""",

    "examples/routing/README.md": """# Routing Example

Demonstrates weighted and fallback routing across multiple models.
""",
    "examples/routing/config.yaml": """gateway:
  host: 0.0.0.0
  port: 8080
providers:
  openai:
    type: mock
  anthropic:
    type: mock
routing:
  enterprise-reasoning:
    strategy: weighted
    providers:
      - openai
      - anthropic
    weights: [0.7, 0.3]
""",
    "examples/routing/app.py": """import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "enterprise-reasoning", "messages": [{"role": "user", "content": "Solve this math problem"}]}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
for _ in range(5):
    with urllib.request.urlopen(req) as response:
        print("Routed to:", json.loads(response.read())['model'])
""",
    "examples/routing/data/tasks.json": """[{"task": "Solve math problem"}]""",

    "examples/cost_monitoring/README.md": """# Cost Monitoring Example

Demonstrates how the Cost Plugin logs estimated cost across different providers.
Run the gateway, then run the app, and check the gateway logs.
""",
    "examples/cost_monitoring/config.yaml": """gateway:
  host: 0.0.0.0
  port: 8080
providers:
  mock:
    type: mock
models:
  expensive-model:
    provider: mock
    model: mock-gpt-4o
""",
    "examples/cost_monitoring/app.py": """import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "expensive-model", "messages": [{"role": "user", "content": "Write a long essay."}]}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    print("Check gateway logs for cost estimation.")
""",
    "examples/cost_monitoring/data/payloads.json": """[{"payload": "long essay"}]""",

    "examples/activity_monitoring/README.md": """# Activity Monitoring (Audit) Example

Demonstrates how the Audit plugin emits events for every request.
""",
    "examples/activity_monitoring/config.yaml": """gateway:
  host: 0.0.0.0
  port: 8080
providers:
  mock:
    type: mock
models:
  default:
    provider: mock
    model: mock-model
""",
    "examples/activity_monitoring/app.py": """import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data = {"model": "default", "messages": [{"role": "user", "content": "Hi"}], "user": "alice-123"}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    print("Check gateway logs for Audit Event tracking alice-123.")
""",
    "examples/activity_monitoring/data/users.json": """[{"user_id": "alice-123"}]""",
    
    "examples/task_routing/README.md": """# Task Routing Example

Demonstrates routing to different models based on the task type using different aliases.
""",
    "examples/task_routing/config.yaml": """gateway:
  host: 0.0.0.0
  port: 8080
providers:
  mock_fast:
    type: mock
  mock_smart:
    type: mock
models:
  summarization-task:
    provider: mock_fast
    model: mock-haiku
  coding-task:
    provider: mock_smart
    model: mock-opus
""",
    "examples/task_routing/app.py": """import urllib.request, json
url = "http://localhost:8080/v1/chat/completions"
data_summary = {"model": "summarization-task", "messages": [{"role": "user", "content": "Summarize this."}]}
req_s = urllib.request.Request(url, data=json.dumps(data_summary).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_s) as response:
    print("Summary task routed to:", json.loads(response.read())['model'])

data_coding = {"model": "coding-task", "messages": [{"role": "user", "content": "Write code."}]}
req_c = urllib.request.Request(url, data=json.dumps(data_coding).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req_c) as response:
    print("Coding task routed to:", json.loads(response.read())['model'])
""",
    "examples/task_routing/data/tasks.json": """[{"type": "summarization"}, {"type": "coding"}]"""
}

for filepath, content in examples.items():
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Examples created successfully!")
