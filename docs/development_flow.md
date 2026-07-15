# Development Workflow

## Before Writing Code

Understand the existing architecture.

If requirements are ambiguous:

- Ask questions.
- Explain assumptions.

For larger features:

- Describe the implementation plan before coding.

## During Implementation

Keep changes focused.

Avoid unrelated refactoring.

Use meaningful commit-sized changes.

## Testing

Business logic should include unit tests.

External APIs should be mocked.

Avoid tests that depend on internet access.

## Documentation

When architecture changes:

- Update architecture.md

When a milestone is completed:

- Update roadmap.md

## Code Reviews

New code should:

- be readable
- include type hints
- include logging where appropriate
- handle expected failures gracefully