# T-109: Update SYSTEM_CHARTER.md with Implemented Architectural Patterns

## AI Coding Brief
**Role**: Technical Documentation
**Objective**: Document architectural patterns already implemented in codebase but missing from SYSTEM_CHARTER.md
**User Request**: "should we add anything to the project charter based on this project?"

## Background

Codebase exploration revealed multiple architectural patterns that are implemented but not documented in SYSTEM_CHARTER.md. These patterns are critical for maintaining consistency and onboarding.

## Proposed Additions

### 1. User vs Person Distinction
- User (accounts): Authentication/login account
- Person (parties): Real-world human identity
- One Person can have many Users (email + Google + phone logins)
- Person can exist without User (contacts, leads, patients)
- User can exist without Person (API/service accounts)
- User.person FK is nullable and optional

### 2. RBAC Hierarchy Levels
Document the numeric hierarchy levels used in Role model:
- 100: Superuser (system admin)
- 80: Administrator (full system)
- 60: Manager (team leads)
- 40: Veterinarian (licensed professionals)
- 30: Vet Technician (support staff)
- 20: Receptionist (front desk)
- 10: Pet Owner (customers)

Enforcement: Users can only manage users with LOWER hierarchy levels.

### 3. Soft Delete & Reversibility Pattern
- All domain models inherit from BaseModel
- BaseModel includes SoftDeleteModel with deleted_at field
- restore() method enables reversibility
- hard_delete() for permanent removal (rare)
- Default manager excludes soft-deleted records

### 4. Staff Portal Security Architecture
- All staff access via /staff-{session_token}/{section}/{module}/
- Direct module URLs (/admin, /practice, etc.) return 404
- Session tokens generated per-session to obscure backend structure
- 12 sections: Core, Operations (5), Customers (2), Finance (2), Admin (2)

### 5. Module Enable/Disable System
- ModuleConfig model controls app availability
- Disabled modules return 404 for all routes
- FeatureFlags for granular control within modules
- Enables multi-tenancy (clinic can disable unused modules)

### 6. Capability vs Employment Distinction
- DriverCapability: Ability to perform deliveries (attached to User)
- EmploymentDetails: Employment relationship (extends PartyRelationship)
- These are independent - a person can have one without the other
- Generalizes to other capabilities (e.g., VetCredentials for veterinarians)

### 7. Singleton Settings Pattern
- Settings models enforce pk=1 to prevent multiple instances
- Used in: StoreSettings, ClinicSettings, WAFConfig
- get_instance() classmethod for safe access

## Conflict to Resolve

**Multilingual Implementation**: Charter says "Translations must not duplicate records" but codebase uses field duplication (`name`, `name_es`, `name_en`). Need decision:
- Option A: Update charter to reflect current implementation
- Option B: Refactor to TranslatedContent pattern

## Constraints
**Allowed File Paths**: SYSTEM_CHARTER.md
**Forbidden Paths**: None

## Definition of Done
- [ ] Task document created (T-109)
- [ ] GitHub issue opened
- [ ] SYSTEM_CHARTER.md updated with all 7 sections
- [ ] Multilingual conflict noted for future decision
- [ ] Changes committed with issue reference

## Test Cases
N/A - Documentation task, no code changes requiring tests.
