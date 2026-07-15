# Coding Guidelines

## General Principles

- Prefer simple, readable code over clever abstractions.
- Keep modules small and focused.
- Add type hints for public functions.
- Use Pydantic models for structured data validation.
- Write tests for important business logic.
- Avoid hardcoding API keys or secrets.

## Python Style

- Use Python 3.11+.
- Follow PEP 8.
- Prefer descriptive names.
- Use dataclasses or Pydantic models where appropriate.

## Error Handling

- Handle external API failures gracefully.
- Log errors with enough context for debugging.
- Avoid swallowing exceptions silently.

## Testing

- Use pytest.
- Keep unit tests fast.
- Mock external API calls.
- Add integration tests separately when needed.

## Data

- Do not commit raw downloaded data.
- Do not commit API keys.
- Store example environment variables in `.env.example`.