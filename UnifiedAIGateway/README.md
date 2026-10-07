# Unified AI Gateway

A production-quality, provider-neutral **Enterprise AI Gateway** written in Python.

The AI Gateway acts as a data plane between your AI applications and model providers (like OpenAI, Anthropic, Google Gemini). It provides a stable, OpenAI-compatible API to your applications while abstracting routing, cost monitoring, auditing, governance, and fallback strategies.

## Design Philosophy

> **Applications should have a stable AI API. The gateway should abstract model providers, routing, governance, cost, audit, security and future enterprise AI capabilities behind that API.**

Instead of:
`Application -> OpenAI`

You deploy:
`Application -> AI Gateway -> (OpenAI | Anthropic | Gemini | Future Providers)`

## Features

- **Zero-Code Application Changes**: Exposes an OpenAI-compatible API (chat, embeddings, models).
- **Multi-Provider Support**: Seamlessly integrate with OpenAI, Anthropic (Claude), Google Gemini, and mock providers.
- **Advanced Routing**: Support for static, round-robin, weighted, and fallback routing strategies.
- **Enterprise Extensibility**: Built-in plugin architecture for intercepting requests across the lifecycle.
- **Core Plugins Included**:
  - `CostPlugin`: Tracks estimated costs based on token usage.
  - `AuditPlugin`: Generates normalized event logs for every request.
  - `GovernancePlugin`: Evaluates policies to block non-compliant requests.

## Installation & Build

Requires Python 3.12+.

To install from source for development:

```bash
git clone https://github.com/your-org/unifiedai-gateway.git
cd unifiedai-gateway
pip install -e .
```

To build a distribution:

```bash
pip install build
python -m build
```

## Configuration

The gateway is entirely configuration-driven using YAML. You define providers, map model aliases, and set up routing rules.

Example `config.yaml`:

```yaml
gateway:
  host: 0.0.0.0
  port: 8080

providers:
  openai_prod:
    type: openai
    api_key_env: OPENAI_API_KEY
  anthropic_prod:
    type: anthropic
    api_key_env: ANTHROPIC_API_KEY

models:
  # Route traffic for this specific alias directly to a model
  enterprise-default:
    provider: openai_prod
    model: gpt-4o

routing:
  # Route traffic across multiple providers with a fallback strategy
  enterprise-reasoning:
    strategy: fallback
    providers:
      - anthropic_prod
      - openai_prod
```

## Usage

Start the gateway server using the provided CLI:

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

ai-gateway start --config config.yaml
```

Connect your application using the standard OpenAI client:

```python
from openai import OpenAI

# Point the client to your locally running AI Gateway
client = OpenAI(
    api_key="gateway-key", # The gateway authenticates you
    base_url="http://localhost:8080/v1"
)

# The gateway handles routing this alias to the correct provider
response = client.chat.completions.create(
    model="enterprise-reasoning", 
    messages=[
        {"role": "user", "content": "Explain AI gateways"}
    ]
)
print(response)
```

## High-Level Interfaces and Customization

The core gateway is designed as a library, allowing you to embed it in custom gateway projects.

### 1. Custom Providers
Implement the `ModelProvider` interface to add new LLM backends.
```python
from ai_gateway.providers.base import ModelProvider

class MyCustomProvider(ModelProvider):
    async def chat_completion(self, request):
        ...
```

### 2. Custom Plugins
Implement the `GatewayPlugin` interface to add security, caching, or RAG.
```python
from ai_gateway.plugins.base import GatewayPlugin

class CachingPlugin(GatewayPlugin):
    async def before_provider_call(self, context):
        # Check cache and optionally bypass the provider
        pass
```

## Examples

We provide ready-to-run examples in the `examples/` directory to help you get started:

- **`model_migration/`**: Transparently swap an application from OpenAI to Gemini.
- **`routing/`**: Distribute traffic using weighted load balancing.
- **`task_routing/`**: Route different tasks (coding vs summarization) to different models.
- **`cost_monitoring/`**: Intercept responses to calculate and log token costs.
- **`activity_monitoring/`**: Track every request via the Audit plugin for compliance.

Check the `README.md` inside each example folder for run instructions.

## License

This project is licensed under the Apache License 2.0 - see the `LICENSE` file for details.
