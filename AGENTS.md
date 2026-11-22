# HazeGuard Development Instructions

## Project Purpose

HazeGuard is a GNSS security monitoring platform for detecting, ingesting, storing, and visualizing GNSS spoofing and jamming observations.

The expected high-level flow is:

GNSS detection nodes → MQTT / Mosquitto → FastAPI backend → PostgreSQL → React dashboard

Preserve this architecture unless an architectural change has been discussed and agreed upon first.

Preserve this architecture unless an architectural change has been discussed and agreed upon first.

## Technology Boundaries

- Frontend: React, TypeScript, and Vite.
- Backend: Python and FastAPI.
- Database: PostgreSQL.
- Messaging: MQTT, using Mosquitto.
- Frontend and backend must remain independently structured and deployable.

Do not mix frontend application code into backend modules or backend application logic into frontend modules.

## Architecture and Code Organization

- Follow clean architecture principles and modular coding practices.
- Keep responsibilities separated:
  - API routes/controllers handle HTTP concerns.
  - Services contain application and business logic.
  - Data-access modules handle PostgreSQL persistence.
  - MQTT modules handle broker connections, subscriptions, and message processing.
  - Schemas validate and define external data contracts.
  - Frontend features own their pages, components, hooks, API clients, and types.
- Prefer small, cohesive modules over large multi-purpose files.
- Avoid circular dependencies.
- Keep reusable utilities isolated from feature-specific code.

## API and Data Contracts

- Do not invent API endpoints, MQTT topics, database fields, or payload fields without agreement on the API/data contract.
- Treat documented schemas as the source of truth.
- When a required field or endpoint is undefined, raise the ambiguity for discussion before implementing it.
- Keep frontend types and backend validation schemas aligned with agreed contracts.

## GNSS Observation Handling

- Validate all incoming GNSS observation data before it is accepted, processed, relayed, or persisted.
- Validate required fields, data types, timestamps, confidence values, coordinates, signal classifications, and metadata structure according to the agreed schema.
- Handle malformed MQTT messages safely: log useful context without exposing sensitive content, reject invalid data, and avoid crashing the consumer.
- Preserve raw observation context only when it is part of the agreed data model.

## Security and Configuration

- Never hardcode passwords, API keys, tokens, connection strings, or other secrets.
- Use environment variables or approved secret-management mechanisms for configuration.
- Keep local `.env` files untracked.
- Do not expose PostgreSQL credentials, MQTT credentials, or internal infrastructure details in frontend bundles.
- Apply authentication, authorization, TLS, broker ACLs, and input validation according to the agreed security design.

## Code Quality

- Write maintainable, documented, and testable code.
- Add concise documentation for public modules, non-obvious decisions, external interfaces, and configuration requirements.
- Prefer clear names and straightforward control flow over clever abstractions.
- Add or update tests when behavior changes.
- Keep tests deterministic and independent of external services where practical.
- Format, lint, type-check, and test the relevant area before declaring implementation work complete.

## Scope Control

- Do not modify unrelated files.
- Preserve existing project structure unless a requested change requires an agreed architectural update.
- Explain the intended changes before making significant architectural modifications, such as changing service boundaries, database design, communication patterns, deployment topology, or public contracts.
- Keep commits focused on one concern.

## Git Workflow

- Never commit directly to `main`.
- Use feature branches for frontend, backend, infrastructure, and documentation work.
- Keep frontend and backend work independently reviewable where possible.
- Do not overwrite or discard existing user changes without explicit approval.

## Repository Awareness

- Inspect the existing repository structure before creating, moving, renaming, or deleting files.
- Do not assume that planned directories, modules, or configuration files already exist.
- Prefer extending the existing structure over introducing a new structure without discussion.

## Dependencies and Database Changes

- Add only dependencies that are necessary for the requested functionality.
- Document new dependencies and their purpose in the appropriate dependency files.
- Do not change dependency versions unnecessarily.
- Treat database schema changes as deliberate changes requiring review.
- Document database migrations and ensure existing data is not unintentionally lost.

## Git and Change Safety

- Before making changes, inspect the current Git branch and working-tree status.
- Do not overwrite, discard, reset, or revert existing user changes without explicit approval.
- Do not commit or push changes unless explicitly requested.
- Never use destructive Git commands without explaining their impact and obtaining approval.

## Implementation Completion Reports

After completing a task, report:

- What was implemented.
- Which files were created, modified, or deleted.
- Which commands, tests, formatters, or checks were run.
- Whether those checks passed or failed.
- Any outstanding issues, assumptions, or work requiring discussion.