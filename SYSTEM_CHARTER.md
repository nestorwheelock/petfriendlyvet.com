# SYSTEM CHARTER – PetFriendlyVet

All development is done following the 23 step TDD process.  Any tasks or issues or bugs you create make sure to open them at github.

This file defines non-negotiable architectural rules.
All AI assistance must comply.

## Core Principles
- This is an enterprise-grade veterinary operating system.
- Favor auditability, reversibility, and correctness over speed.
- Optimize for real clinic workflows, not developer elegance.

## Identity & Ownership
- Party Pattern is foundational.
- Do NOT collapse Person / Organization / Group.
- All ownership, employment, guardianship, billing flows through PartyRelationship.

## Clinical Model
- Encounter (Consultation) is the aggregate root.
- ClinicalNote is a document, NOT the visit.
- Medical records are append-only with soft corrections.

## Separation of Concerns
- Clinical truth ≠ operational tasks ≠ inventory ≠ accounting.
- Clinical actions may reference billing items.
- Accounting is downstream and never blocks operations.

## Inventory
- All stock movements must be source-linked.
- No anonymous adjustments.
- Controlled substances require explicit authorization and audit trail.

## Permissions
- RBAC hierarchy is mandatory and enforced everywhere.
- No role escalation via convenience flags.

## AI Usage
- AI may assist but never author medical truth.
- AI-generated content must be marked and explicitly accepted.
- Never auto-save AI output into medical records.

## Multilingual
- Translations must not duplicate records.
- TranslatedContent is view-layer only.

## Error Handling
- Errors are first-class signals.
- Do not swallow exceptions or auto-retry silently.

## User vs Person
- User (accounts.User): Authentication/login account with auth method.
- Person (parties.Person): Real-world human identity, separate from login.
- One Person can have multiple Users (email + Google + phone logins).
- Person can exist without User (contacts, leads, patients).
- User can exist without Person (API/service accounts).
- User.person FK is nullable and optional.

## RBAC Hierarchy
- Role.hierarchy_level defines numeric power level (10-100).
- Users can only manage users with LOWER hierarchy levels.
- No escalation via convenience flags - all escalation requires role assignment.
- Standard levels:
  - 100: Superuser (system admin)
  - 80: Administrator (full system)
  - 60: Manager (team leads)
  - 40: Veterinarian (licensed professionals)
  - 30: Vet Technician (support staff)
  - 20: Receptionist (front desk)
  - 10: Pet Owner (customers)

## Soft Delete & Reversibility
- All domain models inherit from BaseModel.
- BaseModel includes deleted_at field for soft delete.
- Default managers exclude soft-deleted records.
- restore() method enables reversibility.
- hard_delete() for permanent removal (rare, audited).

## Staff Portal Security
- All staff access via /staff-{session_token}/{section}/{module}/.
- Direct module URLs (/admin, /practice, etc.) return 404.
- Session tokens generated per-session to obscure backend structure.
- 12 sections organized by function: Core, Operations, Customers, Finance, Admin.

## Module Configuration
- ModuleConfig controls app availability dynamically.
- Disabled modules return 404 for all routes.
- FeatureFlags for granular control within modules.
- Enables multi-tenancy (clinics can disable unused modules).

## Capability vs Employment
- Capabilities (e.g., DriverCapability, VetCredentials) attach to User.
- Employment flows through PartyRelationship + EmploymentDetails.
- These are independent - a person can have capability without employment.
- A person can be employed without having a specific capability.

## Singleton Settings
- Settings models enforce pk=1 to prevent multiple instances.
- Used in: StoreSettings, ClinicSettings, WAFConfig.
- Always access via get_instance() classmethod.

## Multilingual (Implementation Note)
- Current implementation uses field duplication (name, name_es, name_en).
- This conflicts with charter rule "Translations must not duplicate records."
- TODO: Decide whether to refactor to TranslatedContent or update this rule.
