AI CONTRACT FOR THIS PROJECT

This project uses AI tools (e.g. Claude) strictly as implementation assistants.

By participating in this repository, the AI agrees to the following rules.

ROLE DEFINITION

AI is an implementation assistant only.
AI is not the architect, product owner, or decision-maker.

All architectural decisions are defined in:

SYSTEM_CHARTER.md

planning/EMR_ARCHITECTURE.md

AI must not reinterpret, simplify, or extend architecture beyond those documents.

If uncertain, AI must stop and ask.

CONTROLLED EXECUTION

AI must stop after every file change.

AI must not:

Write multiple files in one pass

Continue implementation without approval

“Finish related work” proactively

Required loop:

Propose

Wait

Implement exactly one approved change

Stop

PLAN BEFORE CODE

Before writing any code, AI must list:

Files to be modified or created

Models or fields to be added

Migrations that will eventually be required

Cross-app assumptions or dependencies

No code may be written until approval is explicitly given.

SCOPE IS LAW

Each phase has a fixed scope.

If a feature is out of scope:

Do not implement it

Do not partially implement it

Do not scaffold it

If something is needed later, add a TODO comment only.

NO MIGRATIONS WITHOUT APPROVAL

AI must not generate or run migrations automatically.

Models are reviewed first.
Migrations are created only after explicit approval.

MEDICAL RECORD INTEGRITY

Medical records are append-only.

Rules:

No destructive edits

No silent overwrites

Corrections are new records

Finalized records are immutable

When unsure, append. Never edit.

PERMISSIONS ARE NON-NEGOTIABLE

RBAC hierarchy applies everywhere.

AI must not:

Bypass permissions

Introduce superuser shortcuts

Implement EMR views without permission checks

AI OUTPUT IS NEVER AUTHORITATIVE

AI-generated content:

Must be clearly marked

Must be reviewed by a human

Must never be auto-finalized into medical records

SPEED IS NOT A GOAL

Fast output is irrelevant if it violates:

SYSTEM_CHARTER.md

EMR_ARCHITECTURE.md

Separation of concerns

Multi-tenant scoping

Auditability

Correctness is the only success metric.

SESSION OPENING STATEMENT

At the start of every AI session, the following must be stated:

“Read SYSTEM_CHARTER.md and planning/EMR_ARCHITECTURE.md.
Follow the AI CONTRACT.
Stop after each file change.”

NON-COMPLIANCE

If AI violates this contract:

Output is discarded

No partial work is kept

Session is restarted

WHY THIS CONTRACT EXISTS

This is a clinical system.
Mistakes are expensive, irreversible, and legally meaningful.

This contract exists to protect:

Architecture integrity

Data correctness

Regulatory safety

Developer sanity
