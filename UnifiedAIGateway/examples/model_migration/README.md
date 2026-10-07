# Model Migration Example

This example demonstrates how to seamlessly migrate an application from OpenAI to Gemini without changing any application code.

## Setup
1. Define your original models in `config.yaml` using OpenAI.
2. Change the provider to `gemini` in `config.yaml`.
3. Run `python app.py` to see the same request routed to Gemini.

## Data
Synthetic prompts are stored in `data/prompts.json`.
