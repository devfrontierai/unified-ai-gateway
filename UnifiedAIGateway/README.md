# Provider-Neutral Enterprise AI Gateway

An enterprise AI gateway that provides a stable OpenAI-compatible API to applications, while abstracting model providers, routing, governance, cost, audit, security and future capabilities behind that API.

## Core Features
* OpenAI-compatible API (Applications require zero code changes)
* Provider abstraction (OpenAI, Anthropic, Gemini, etc.)
* Routing engine (Static, Weighted, Round Robin, Fallback, etc.)
* Plugin system (Cost metering, Audit events, Governance hooks)
* Configuration-driven model registry

## Quick Start
```bash
# Clone the repository
git clone <repository_url>
cd ai-gateway

# Install dependencies
pip install -e .

# Copy environment variables
cp .env.example .env

# Start the gateway
ai-gateway start --config config.yaml
```
