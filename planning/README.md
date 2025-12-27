“Treat planning/EMR_ARCHITECTURE.md as authoritative, do not drift.”
AI-ASSISTED DEVELOPMENT RULES (MANDATORY)
YOu should be familiar with the SYSTEM_CHARTER.md and AI_CONTRACT.md

This project uses AI tools (for example Claude) for implementation assistance.
Speed without control causes architectural drift. These rules are non-negotiable.

AI IS AN IMPLEMENTATION ASSISTANT, NOT THE ARCHITECT

All architectural decisions are defined in:

SYSTEM_CHARTER.md

planning/EMR_ARCHITECTURE.md

AI must not invent new abstractions, simplify existing ones, or reinterpret scope.
If a design decision is unclear, AI must stop and ask.

HARD STOP AFTER EACH FILE CHANGE

AI must stop after each file modification.

Forbidden:

Writing multiple models at once

Generating migrations automatically

Continuing to “finish” related features

Required workflow:

Propose change

Wait for approval

Apply exactly one approved change

Stop

PLAN → APPROVE → IMPLEMENT (NO EXCEPTIONS)

Before writing any code, AI must list:

Files to be modified or created

Models or fields to be added

Migrations that will eventually be required

Cross-app dependencies or assumptions

Implementation must not begin until explicitly approved.

SCOPE IS EXPLICIT AND ENFORCED

Each phase has a strict scope.

Example (Phase 1 – EMR Foundation):
Allowed:

Encounter

PatientProblem

Not allowed:

SOAP notes

Orders or results

Services

Inventory links

Billing links

If something is needed later, add a TODO comment only.

NO MIGRATIONS UNTIL MODELS ARE APPROVED

AI must not generate migrations automatically.
Schema decisions are reviewed before migrations exist.
Migrations are created only after explicit approval.

This prevents fossilizing bad schema decisions.

APPEND-ONLY MEDICAL RECORDS ARE SACRED

Medical records are legal records.

Rules:

No destructive updates

No silent overwrites

Corrections are new records (entered_in_error, addenda, supersedes)

Finalized records are immutable

If unsure, append. Never edit.

PERMISSIONS ARE NEVER BYPASSED

RBAC hierarchy applies to all EMR features.

Forbidden:

Temporary permission bypasses

Superuser shortcuts

Writing EMR views without permission checks

SPEED IS NOT A SUCCESS METRIC

Fast output is meaningless if it violates:

SYSTEM_CHARTER.md

EMR append-only rules

Separation of concerns

Multi-tenant scoping

Correctness matters more than speed.

HOW TO USE AI ON THIS PROJECT

At the start of every AI session, state:

“Read SYSTEM_CHARTER.md and planning/EMR_ARCHITECTURE.md.
Follow the AI-Assisted Development Rules in README.
Stop after each file change.”

If AI ignores these rules, discard the output.

WHY THIS EXISTS

This project is a clinical system.
Mistakes are expensive, hard to unwind, and legally meaningful.

These rules protect:

Architecture integrity

Data correctness

Long-term maintainability

Developer sanity

That’s it. No markdown, no decoration, no wiggle room.
