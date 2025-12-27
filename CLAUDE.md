# PetFriendlyVet - Claude Code Instructions

## Required Reading (MANDATORY)

Before starting ANY work on this project, read:

1. **[SYSTEM_CHARTER.md](SYSTEM_CHARTER.md)** - Non-negotiable architectural rules
2. **[planning/CODING_STANDARDS.md](planning/CODING_STANDARDS.md)** - Development standards
3. **[planning/TDD_STOP_GATE.md](planning/TDD_STOP_GATE.md)** - TDD enforcement

## Key Architectural Rules

From SYSTEM_CHARTER.md:
- **Party Pattern** is foundational - Person/Organization/Group/PartyRelationship
- **User vs Person** - Authentication (User) is separate from identity (Person)
- **Clinical truth** - Encounter is aggregate root, records are append-only
- **Soft Delete** - All models use BaseModel with reversible deletion
- **RBAC Hierarchy** - Users can only manage users with lower hierarchy levels

## Development Workflow

1. All development follows the **26-step TDD cycle**
2. Create GitHub issues for all tasks and bugs
3. Use "Addresses #X" for bug commits (NOT "Closes")
4. Test coverage must exceed 95%

## Quick Commands

```bash
# Run tests
pytest

# Run specific app tests
pytest apps/pets/tests/

# Check migrations
python manage.py makemigrations --check

# Run development server
python manage.py runserver
```
