Plan: Veterinary EMR Architecture

 Authoritative References

 1. SYSTEM_CHARTER.md - Non-negotiable architectural rules (source of truth)
 2. planning/EHRNOTES.md - Research on veterinary EHR patterns
 3. planning/stories/S-003-pet-profiles-medical-records.md - User-facing feature requirements

 Architectural Constraints (from SYSTEM_CHARTER.md)

 These are non-negotiable system rules defined in the charter:

 From SYSTEM_CHARTER.md:
 1. Encounter (Consultation) is the aggregate root - All clinical activity links to an Encounter
 2. ClinicalNote is a document, NOT the visit - Separate the note from the visit event
 3. Medical records are append-only with soft corrections - Never delete, use "entered in error"
 4. Clinical truth ≠ operational ≠ inventory ≠ accounting - Clear separation of concerns
 5. Clinical actions may reference billing items - Link, don't merge
 6. RBAC hierarchy is mandatory and enforced everywhere - Role-based access control
 7. AI may assist but never author medical truth - AI content must be explicitly accepted
 8. Party Pattern is foundational - Use parties.Organization for multi-tenant scoping
 9. All stock movements must be source-linked - Inventory tracking with provenance

 From EHRNOTES.md research (implementation guidance):
 10. State transitions, not screens - Model workflow as explicit states (scheduled → checked_in → in_exam → discharge)
 11. External labs/imaging are first-class - Store with source metadata, raw payloads, reference IDs
 12. Favor boring, explicit models - Optimize for clinic staff comprehension, not developer elegance

 Reconciling S-003 with SYSTEM_CHARTER

 S-003 defines what users see. SYSTEM_CHARTER defines how we build it.

 | S-003 User Requirement         | EMR Architecture Implementation                               |
 |--------------------------------|---------------------------------------------------------------|
 | Vaccination records with dates | PerformedService (vaccine type) linked to Encounter           |
 | Visit history with notes       | Encounter (pipeline history) + SOAPNote                       |
 | Medication history             | PatientMedication (current meds) + Prescription per encounter |
 | Allergies/conditions flagged   | PatientProblem (persists across encounters)                   |
 | Weight tracking over time      | VitalSigns.weight_kg captured per encounter                   |
 | Document storage               | MedicalDocument linked to encounter/result                    |
 | Clinical notes (internal)      | SOAPNote.is_finalized + role-based visibility                 |
 | Audit log for changes          | ClinicalEvent (append-only timeline)                          |

 Key difference from S-003's original model:
 - S-003 proposed Visit as a simple model
 - SYSTEM_CHARTER requires Encounter as aggregate root with pipeline states

 The EMR architecture delivers all S-003 features while complying with charter rules.

 Current State Analysis (CRITICAL ISSUES FOUND)

 Issue #1: SEVERE MODEL DUPLICATION

 Medical models are defined in BOTH apps/pets/models.py AND apps/practice/models.py:

 | Model            | pets/ version  | practice/ version   |
 |------------------|----------------|---------------------|
 | MedicalCondition | conditions     | medical_conditions  |
 | Vaccination      | vaccinations   | vaccination_records |
 | Visit            | visits         | visit_records       |
 | Medication       | medications    | medication_records  |
 | ClinicalNote     | clinical_notes | practice_notes      |
 | WeightRecord     | weight_records | weight_history      |

 Problem: No clear source of truth. Which version is canonical?

 Issue #2: NO ENCOUNTER MODEL EXISTS (VIOLATES CHARTER)

 The SYSTEM_CHARTER requires: "Encounter (Consultation) is the aggregate root."

 Current state:
 - Visit models exist (2 places) but are lightweight documents
 - Appointment is scheduling-focused, not clinical
 - NO Encounter model serving as medical event aggregate root

 Issue #3: NO APPEND-ONLY AUDIT TRAIL (VIOLATES CHARTER)

 The SYSTEM_CHARTER requires: "Medical records are append-only with soft corrections."

 Current state:
 - ClinicalNote has is_locked but no correction tracking
 - No evidence of immutable append-only pattern
 - No version/correction history

 Migration 0008 Status

 Migration apps/practice/migrations/0008_add_emr_models.py added practice versions of medical models, creating MORE duplication (not less).

 Resolution Strategy (USER DECISION)

 Decision: Create new apps/emr/ module with canonical models. Progressive migration approach:

 1. Keep migration 0008 - Do not roll back
 2. Freeze existing duplicates as legacy - Don't modify pets/ or practice/ medical models
 3. Create canonical EMR models in apps/emr/ - New module following SYSTEM_CHARTER
 4. Migrate data/links forward - Data migration to new EMR structure
 5. Deprecate gradually, then remove - Clean up legacy models once no longer referenced

 Model disposition:
 | Model            | pets/           | practice/               | NEW emr/                      |
 |------------------|-----------------|-------------------------|-------------------------------|
 | Visit            | FREEZE (legacy) | FREEZE (legacy)         | Encounter (canonical)         |
 | MedicalCondition | FREEZE          | FREEZE                  | PatientProblem (canonical)    |
 | ClinicalNote     | FREEZE          | FREEZE                  | SOAPNote (canonical)          |
 | Vaccination      | FREEZE          | FREEZE                  | PerformedService (canonical)  |
 | Medication       | FREEZE          | FREEZE                  | PatientMedication (canonical) |
 | WeightRecord     | FREEZE          | FREEZE                  | VitalSigns (canonical)        |
 | MedicalDocument  | FREEZE          | FREEZE                  | ClinicalDocument (canonical)  |
 | PatientRecord    | -               | KEEP (links Pet to EMR) | Reference via FK              |

 Vision

 Build a clinical EMR system where:
 - Encounter is the anchor - everything hangs off encounters
 - Event-sourced timeline - chronological clinical history
 - Pipeline/workflow design - patients move through states with tracking
 - Separate clinical from billing - linked but not merged
 - Integration-ready - labs, imaging, inventory as first-class citizens

 Architecture Overview

 ┌─────────────────────────────────────────────────────────────────┐
 │                         SCHEDULING                               │
 │   appointments.Appointment (scheduling intent)                   │
 │                          ↓ check-in                              │
 └─────────────────────────────────────────────────────────────────┘
                           ↓
 ┌─────────────────────────────────────────────────────────────────┐
 │                    EMR MODULE (NEW)                              │
 │                                                                  │
 │   Encounter (the anchor)                                         │
 │   ├── pipeline_state (scheduled→checked_in→roomed→exam→...)    │
 │   ├── VitalSigns (weight, temp, HR, RR, BP, pain score)         │
 │   ├── SOAPNote (subjective, objective, assessment, plan)        │
 │   ├── LabOrder → LabResult                                       │
 │   ├── ImagingOrder → ImagingResult                               │
 │   ├── PerformedService → ServiceConsumableUsage                  │
 │   ├── Prescription (from pharmacy)                               │
 │   └── DischargeInstructions                                      │
 │                                                                  │
 │   Patient-Level (persists across encounters):                    │
 │   ├── PatientProblem (active problems, allergies, alerts)        │
 │   ├── PatientMedication (current med list)                       │
 │   └── ClinicalEvent (timeline - event sourced)                   │
 └─────────────────────────────────────────────────────────────────┘
                           ↓
 ┌─────────────────────────────────────────────────────────────────┐
 │                    INTEGRATIONS                                  │
 │                                                                  │
 │   billing.Invoice (linked from Encounter at checkout)            │
 │   pharmacy.Prescription (linked to Encounter)                    │
 │   inventory.StockMovement (from consumable usage)                │
 └─────────────────────────────────────────────────────────────────┘

 Clinical Pipeline States

 SCHEDULED → CHECKED_IN → ROOMED → IN_EXAM → PENDING_ORDERS →
 AWAITING_RESULTS → TREATMENT → CHECKOUT → COMPLETED
                                     ↓
                               (or NO_SHOW / CANCELLED)

 Each state has timestamps for tracking wait times and workflow efficiency.

 Key Data Models

 1. Encounter (The Anchor)

 class Encounter(models.Model):
     """Central EMR anchor - every clinical activity hangs off this."""

     # Multi-tenant
     organization = ForeignKey('parties.Organization')

     # Links
     appointment = OneToOneField('appointments.Appointment', null=True)  # Walk-ins have no appointment
     patient = ForeignKey('practice.PatientRecord', on_delete=CASCADE)

     # Pipeline
     PIPELINE_STATES = [
         ('scheduled', 'Scheduled'),
         ('checked_in', 'Checked In'),
         ('roomed', 'Roomed'),
         ('in_exam', 'In Exam'),
         ('pending_orders', 'Pending Orders'),
         ('awaiting_results', 'Awaiting Results'),
         ('treatment', 'Treatment'),
         ('checkout', 'Checkout'),
         ('completed', 'Completed'),
         ('no_show', 'No Show'),
         ('cancelled', 'Cancelled'),
     ]
     pipeline_state = CharField(max_length=20, choices=PIPELINE_STATES)

     # Timestamps for each state
     scheduled_at = DateTimeField(null=True)
     checked_in_at = DateTimeField(null=True)
     roomed_at = DateTimeField(null=True)
     exam_started_at = DateTimeField(null=True)
     exam_ended_at = DateTimeField(null=True)
     discharged_at = DateTimeField(null=True)

     # Assignment
     assigned_vet = ForeignKey(User, related_name='encounters_as_vet')
     assigned_tech = ForeignKey(User, null=True, related_name='encounters_as_tech')
     room = CharField(max_length=50, blank=True)

     # Classification
     encounter_type = CharField()  # routine, urgent, emergency, follow_up, telehealth
     chief_complaint = TextField()

     # Billing link
     invoice = ForeignKey('billing.Invoice', null=True, blank=True)

 2. Clinical Event Timeline (Event-Sourced, Append-Only)

 class ClinicalEvent(models.Model):
     """Immutable event log for timeline views.

     Key principle: APPEND-ONLY. Never delete or update.
     Use 'entered_in_error' for corrections.
     """

     organization = ForeignKey('parties.Organization')  # Multi-tenant from day one
     patient = ForeignKey(PatientRecord)
     encounter = ForeignKey(Encounter, null=True)  # Patient-level events have no encounter

     event_type = CharField()  # vital, soap, lab_order, lab_result, imaging, procedure, rx, note
     event_subtype = CharField()  # e.g., "cbc", "xray_lateral", "vaccination"

     occurred_at = DateTimeField()
     recorded_at = DateTimeField(auto_now_add=True)
     recorded_by = ForeignKey(User)

     # Polymorphic reference to actual record
     content_type = ForeignKey(ContentType)
     object_id = PositiveIntegerField()
     content_object = GenericForeignKey()

     # Denormalized for fast display
     summary = CharField(max_length=500)
     is_significant = BooleanField()  # For "major events" view

     # Soft correction (NEVER delete medical records)
     is_entered_in_error = BooleanField(default=False)
     error_corrected_at = DateTimeField(null=True)
     error_corrected_by = ForeignKey(User, null=True, related_name='corrections')
     error_correction_reason = TextField(blank=True)
     superseded_by = ForeignKey('self', null=True)  # Points to correcting event

     class Meta:
         ordering = ['-occurred_at']

 3. Patient Problems (Cross-Encounter Continuity)

 class PatientProblem(models.Model):
     """Active problems/diagnoses that persist across encounters."""

     patient = ForeignKey(PatientRecord)

     problem_type = CharField()  # diagnosis, allergy, chronic, behavioral
     severity = CharField()  # low, moderate, high, critical

     name = CharField()  # "Diabetes Mellitus Type II"
     description = TextField(blank=True)

     onset_date = DateField(null=True)
     resolved_date = DateField(null=True)
     status = CharField()  # active, controlled, resolved, inactive

     # Alert display
     is_alert = BooleanField()
     alert_text = CharField()  # "ALLERGIC TO PENICILLIN"
     alert_severity = CharField()  # info, warning, danger

 4. Vital Signs

 class VitalSigns(models.Model):
     """Vitals recorded during encounter."""

     encounter = ForeignKey(Encounter)
     recorded_at = DateTimeField()
     recorded_by = ForeignKey(User)

     weight_kg = DecimalField()
     temperature_c = DecimalField()
     heart_rate_bpm = PositiveIntegerField()
     respiratory_rate = PositiveIntegerField()
     blood_pressure_systolic = PositiveIntegerField()
     blood_pressure_diastolic = PositiveIntegerField()
     pain_score = PositiveIntegerField()  # 0-10
     body_condition_score = PositiveIntegerField()  # 1-9

 5. SOAP Notes with Templates

 class SOAPNote(models.Model):
     """SOAP format clinical note."""

     encounter = ForeignKey(Encounter)

     subjective = TextField()
     objective = TextField()
     assessment = TextField()
     plan = TextField()

     template_used = ForeignKey(SOAPTemplate, null=True)

     is_finalized = BooleanField()
     finalized_at = DateTimeField(null=True)
     finalized_by = ForeignKey(User, null=True)

     author = ForeignKey(User)


 class SOAPTemplate(models.Model):
     """Reusable SOAP templates by species/encounter type."""

     name = CharField()
     species = JSONField()  # ["dog", "cat"]
     encounter_types = JSONField()  # ["routine", "emergency"]

     subjective_template = TextField()
     objective_template = TextField()
     assessment_template = TextField()
     plan_template = TextField()

 6. Orders & Results

 class LabOrder(models.Model):
     encounter = ForeignKey(Encounter)
     test_name = CharField()
     test_code = CharField()
     panel = ForeignKey(LabPanel, null=True)

     status = CharField()  # ordered, collected, sent, resulted, cancelled
     priority = CharField()  # routine, urgent, stat

     ordered_at = DateTimeField()
     ordered_by = ForeignKey(User)
     external_lab = CharField(blank=True)


 class LabResult(models.Model):
     order = ForeignKey(LabOrder)
     test_name = CharField()
     value = CharField()
     unit = CharField()
     reference_range = CharField()
     flag = CharField()  # H, L, HH, LL, A
     interpretation = TextField()

     # Integration provenance (store original data from external labs)
     external_source = CharField(blank=True)  # e.g., "IDEXX", "Antech"
     external_reference_id = CharField(blank=True)
     raw_payload = JSONField(null=True)  # Original API response, never overwrite
     imported_at = DateTimeField(null=True)


 class ImagingOrder(models.Model):
     encounter = ForeignKey(Encounter)
     modality = CharField()  # xray, ultrasound, mri
     body_part = CharField()
     views = CharField()  # "VD, Lateral"
     clinical_indication = TextField()
     status = CharField()


 class ImagingResult(models.Model):
     order = ForeignKey(ImagingOrder)
     findings = TextField()
     impression = TextField()
     images = JSONField()  # File paths/URLs

 7. Unified Service Catalog

 class ServiceCatalog(models.Model):
     """Replaces VetProcedure, Service, ServiceType."""

     code = CharField(unique=True)
     name = CharField()
     category = ForeignKey(ProcedureCategory)

     base_price = DecimalField()
     duration_minutes = PositiveIntegerField()

     requires_appointment = BooleanField()
     requires_vet_license = BooleanField()
     is_bookable_online = BooleanField()

     sat_product_code = ForeignKey(SATProductCode)
     sat_unit_code = ForeignKey(SATUnitCode)


 class PerformedService(models.Model):
     """Service actually performed during encounter."""

     encounter = ForeignKey(Encounter)
     service = ForeignKey(ServiceCatalog)

     performed_by = ForeignKey(User)
     performed_at = DateTimeField()

     actual_duration_minutes = PositiveIntegerField(null=True)
     actual_price = DecimalField(null=True)

     procedure_notes = TextField()
     invoice_line = ForeignKey(InvoiceLineItem, null=True)

 Model Consolidation

 Remove (after migration):

 | Old Model        | Old Location     | New Model                         |
 |------------------|------------------|-----------------------------------|
 | Visit            | pets/, practice/ | Encounter                         |
 | ClinicalNote     | pets/, practice/ | SOAPNote                          |
 | Medication       | pets/, practice/ | PatientMedication                 |
 | MedicalCondition | pets/, practice/ | PatientProblem                    |
 | Vaccination      | pets/, practice/ | PerformedService + PatientProblem |
 | WeightRecord     | pets/, practice/ | VitalSigns                        |
 | ServiceType      | appointments/    | ServiceCatalog                    |
 | Service          | services/        | ServiceCatalog                    |
 | VetProcedure     | practice/        | ServiceCatalog                    |

 Keep:

 | Model          | Location      | Role                            |
 |----------------|---------------|---------------------------------|
 | Pet            | pets/         | Identity/ownership              |
 | PatientRecord  | practice/     | Links Pet to EMR                |
 | VetCredentials | practice/     | Staff credentials               |
 | Appointment    | appointments/ | Scheduling (links to Encounter) |
 | Prescription   | pharmacy/     | Rx management                   |
 | Invoice        | billing/      | Billing                         |

 Integration Points

 1. Appointment → Encounter (check-in)

 def check_in_appointment(appointment):
     encounter = Encounter.objects.create(
         appointment=appointment,
         patient=appointment.pet.patient_record,
         scheduled_at=appointment.scheduled_start,
         checked_in_at=timezone.now(),
         pipeline_state='checked_in',
         chief_complaint=appointment.notes,
         assigned_vet=appointment.veterinarian,
     )
     appointment.status = 'in_progress'
     appointment.save()
     return encounter

 2. Encounter → Invoice (checkout)

 def generate_encounter_invoice(encounter):
     invoice = Invoice.objects.create(
         owner=encounter.patient.pet.owner,
         pet=encounter.patient.pet,
         appointment=encounter.appointment,
     )
     for service in encounter.services.filter(is_billable=True):
         InvoiceLineItem.objects.create(
             invoice=invoice,
             description=service.service.name,
             unit_price=service.actual_price or service.service.base_price,
         )
     encounter.invoice = invoice
     encounter.save()
     return invoice

 3. Consumable → Inventory

 def record_consumable_usage(performed_service, inventory_item, quantity, batch):
     movement = StockMovement.objects.create(
         batch=batch,
         movement_type='dispense',
         quantity=quantity,
         reference_type='performed_service',
         reference_id=performed_service.id,
     )
     ServiceConsumableUsage.objects.create(
         performed_service=performed_service,
         inventory_item=inventory_item,
         batch=batch,
         quantity_used=quantity,
         stock_movement=movement,
     )

 Implementation Phases

 Phase 1: Foundation (Core EMR Module)

 Create apps/emr/ as the canonical home for clinical models per SYSTEM_CHARTER.

 Tasks:
 1. Create apps/emr/ Django app structure
 2. Implement Encounter with pipeline states (aggregate root)
 3. Implement ClinicalEvent for append-only timeline
 4. Implement PatientProblem for persistent alerts/problems
 5. Register admin for new models

 Files to create:
 apps/emr/
 ├── __init__.py
 ├── apps.py
 ├── models.py          # Encounter, ClinicalEvent, PatientProblem
 ├── admin.py           # Admin registration
 ├── services.py        # Business logic
 ├── signals.py         # Event handling
 └── migrations/
     └── 0001_initial.py

 Key model: Encounter (aggregate root per charter)
 - Links to: practice.PatientRecord, appointments.Appointment
 - Has: pipeline_state, timestamps, assigned staff
 - Creates: ClinicalEvent on state transitions

 Phase 2: Clinical Documentation

 Add documentation models to EMR module.

 Tasks:
 1. Implement VitalSigns (per-encounter vitals)
 2. Implement SOAPNote + SOAPTemplate (clinical documentation)
 3. Implement DischargeInstructions
 4. Add views for clinical documentation

 Files to modify:
 - apps/emr/models.py - Add VitalSigns, SOAPNote, SOAPTemplate
 - apps/emr/admin.py - Register new models

 Phase 3: Orders & Results

 Add order tracking with integration provenance.

 Tasks:
 1. Implement LabOrder, LabResult, LabPanel
 2. Implement ImagingOrder, ImagingResult
 3. Add ClinicalDocument for attachments
 4. Store raw_payload for external integrations

 Phase 4: Services & Procedures

 Consolidate service models, link to inventory.

 Tasks:
 1. Implement ServiceCatalog (canonical service definition)
 2. Implement PerformedService (what was done in encounter)
 3. Implement ServiceConsumableUsage (inventory linkage)
 4. Add PatientMedication (current medication list)

 Integration points:
 - apps/inventory/models.py - Link stock movements to PerformedService
 - apps/pharmacy/models.py - Link Prescription to Encounter

 Phase 5: Appointment Integration

 Hook appointments to create Encounters on check-in.

 Tasks:
 1. Add check_in_appointment() service function
 2. Create Encounter when appointment status changes
 3. Update appointment views to show encounter link
 4. Add treatment board / whiteboard view

 Phase 6: Data Migration (After models stable)

 Migrate data from legacy models to canonical EMR.

 Tasks:
 1. Create data migration script
 2. Map legacy Visit → Encounter
 3. Map legacy MedicalCondition → PatientProblem
 4. Map legacy ClinicalNote → SOAPNote
 5. Verify data integrity
 6. Mark legacy models as deprecated

 Phase 7: Cleanup (After migration verified)

 Remove legacy models once no longer referenced.

 Tasks:
 1. Update all imports to use emr models
 2. Update templates to use new model paths
 3. Remove deprecated models from pets/
 4. Remove deprecated models from practice/
 5. Clean up orphaned migrations

 Minimum Viable EMR (First Release)

 Based on user guidance, the MVP includes:

 1. Client + Patient CRUD - Already have this
 2. Encounter + SOAP note with templates - Phase 1 + 2
 3. Orders/results (attach PDFs/images) - Phase 3 (simplified)
 4. Med list + dispensing log - PatientMedication + pharmacy integration
 5. Timeline view - ClinicalEvent (Phase 1)
 6. Audit log + roles - ClinicalEvent + existing auth

 Role-Based Access Control

 Medical records require strict access control. Align with existing staff roles:

 | Role           | Can View                | Can Create            | Can Edit     | Can Finalize |
 |----------------|-------------------------|-----------------------|--------------|--------------|
 | Reception      | Patient summary, vitals | Check-in, basic info  | Contact info | No           |
 | Vet Tech       | Full record             | Vitals, notes, orders | Draft notes  | No           |
 | Veterinarian   | Full record             | Everything            | Everything   | SOAP notes   |
 | Practice Admin | Full record + audit     | Everything            | Everything   | Everything   |

 Finalization Rule: Once a SOAP note is finalized (is_finalized=True), it becomes read-only. Only append corrections ("addendum" or "entered in error").

 Auditability Requirements

 Medical records become legal records. The system must track:

 1. Who created what, when - created_by, created_at on all records
 2. Who modified what - Edit history or append-only events
 3. Access logs - Who viewed which patient records (optional Phase 2)
 4. Signature/finalization - When notes were "signed off"

 Django's django-simple-history or manual audit tables can provide this.

 Success Criteria

 - Encounter model with pipeline states
 - Patients can be checked in, roomed, examined, discharged
 - VitalSigns captured per encounter
 - SOAP notes with templates
 - Patient problems/alerts persist across encounters
 - Clinical timeline shows all events chronologically
 - Services performed tracked with consumables
 - Invoices generated from encounter services
 - Lab/imaging orders with result attachments
 - Duplicate models deprecated and removed

 Critical Files

 New:
 - apps/emr/models.py - Core EMR models
 - apps/emr/services.py - Business logic
 - apps/emr/admin.py - Admin registration
 - templates/emr/ - EMR templates

 Modify:
 - apps/appointments/models.py - Add Encounter hook
 - apps/pharmacy/models.py - Add Encounter FK, batch FK
 - apps/inventory/models.py - Expand reference_type
 - apps/billing/models.py - Link to Encounter

 Deprecate (after migration):
 - apps/pets/models.py - Visit, Medication, ClinicalNote, etc.
 - apps/practice/models.py - Visit, Medication, ClinicalNote, etc.
 - apps/services/models.py - Service model
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

 Would you like to proceed?

 ❯ 1. Yes, and bypass permissions
   2. Yes, and manually approve edits
   3. Type here to tell Claude what to change

 ctrl-g to edit in Vim

