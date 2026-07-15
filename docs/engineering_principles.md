# Engineering Principles

These principles guide all architectural and implementation decisions in DailyFinance.

## Simplicity First

Prefer simple, maintainable solutions over complex abstractions.

Avoid introducing additional frameworks or patterns unless they provide clear long-term value.

## Modular Design

Each component should have a single responsibility.

Examples:

- Data collection
- Data processing
- Storage
- AI analysis
- API layer

These components should communicate through well-defined interfaces.

## AI Should Enhance, Not Replace

LLMs should enrich collected information rather than become the primary source of truth.

Whenever possible:

- Store raw data
- Preserve source attribution
- Make AI-generated results reproducible

## Raw Data Is Immutable

Collected data should never be modified directly.

Cleaning and enrichment should produce new processed representations.

## External Services Are Replaceable

Every external API should be wrapped behind an abstraction layer.

Business logic should never depend directly on a vendor SDK.

## Explicit Is Better Than Implicit

Prefer readable code and explicit data flow over clever implementations.

Future contributors should understand the system quickly.