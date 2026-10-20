---
name: coding-standards
description: Apply personal architecture and testing rules when implementing, refactoring, or reviewing Python/FastAPI or Go services and applications. For scripts and small utilities, apply only relevant simplicity rules.
---

# Coding Standards

## Scope and Existing Code
- Architecture rules guide responsibility and dependency boundaries. They do not require a separate class, interface, DTO, package, or file for every responsibility. Preserve existing boundaries; introduce new structure only when the current task requires it.
- Apply these architecture rules to services and applications.
- Keep scripts and small utilities simple; do not force a layered architecture.
- Follow the existing project structure and conventions without weakening its layer boundaries.
- Do not broaden a local change into an architectural refactor without approval.

## Layers and Dependencies
- Separate Domain, Application, Infrastructure, and Presentation responsibilities.
- Enforce dependency direction; create separate packages or modules only when useful.
- Keep Domain independent of Application, Infrastructure, and Presentation.
- Access databases, external services, and other infrastructure through ports defined in Domain or Application, according to who owns the contract.
- Do not create interfaces for ordinary internal calls without a concrete need.

## Domain
- Keep business rules, invariants, and business validation in Domain.
- Do not depend on frameworks, ORM, databases, HTTP clients, or external SDKs.
- Small libraries without I/O are acceptable.
- In Python, use plain classes or dataclasses; do not use Pydantic in Domain.
- In Go, use plain structs without JSON or database tags.
- Keep context.Context out of entity and value-object methods. It is acceptable in infrastructure ports for cancellation and timeouts.

## Application and Infrastructure
- Put business use-case orchestration in Application.
- Application defines transaction boundaries; Infrastructure implements them.
- Introduce a Unit of Work only when a concrete use case requires it.
- Keep persistence, external clients, and technical logging in Infrastructure.
- Keep request-format validation, DTO mapping, and transaction mechanics outside domain entities.

## Presentation and Data Models
- Keep HTTP handlers focused on request parsing, invocation, and response mapping.
- Simple CRUD may call infrastructure ports directly when it contains no business rules.
- Separate API, persistence, and domain models where contracts, meaning, or dependencies differ.
- Do not create identical intermediate DTOs solely for layer transitions.
- Do not expose transport or ORM models to Domain.
- Use FastAPI Depends at the outer boundary.
- In Go, prefer explicit dependency injection through constructors.

## Errors
- Domain and Application errors express business meaning without HTTP dependencies.
- Presentation maps errors to HTTP status codes and response bodies.
- Do not expose internal infrastructure errors to clients.
- Introduce custom error types only when callers need to distinguish them.

## Tests and Verification
- Test primary business scenarios and significant failure cases.
- Cover changed business rules with focused unit tests.
- Add integration tests when changing database or external-integration behavior.
- Add end-to-end tests when cross-layer behavior requires verification.
- For bug fixes, add a regression test when practical.
- Do not test every method, trivial mapping, or implementation detail, or require tests at every layer for every change.
- Run the smallest useful set of checks for the change.

## Simplicity
- Prefer explicit dependencies, straightforward code, and composition.
- Do not introduce CQRS, mediators, generic repositories, DI containers, or speculative abstractions without a concrete need.
- Add only what the current task requires.
