"""EMR (Electronic Medical Records) module.

Canonical home for clinical models per SYSTEM_CHARTER.md:
- Encounter is the aggregate root (all clinical activity links to Encounter)
- ClinicalNote is a document, NOT the visit
- Medical records are append-only with soft corrections
- Every EMR record scoped by parties.Organization

This module is SEPARATE from Practice module UI. Clinical/EMR features
should have their own section with Encounter-centric workflows.
"""
