How vet EHRs are usually organized (the common pattern)
1) The core “people + pets” graph

Most systems start with:

Client (owner/guardian): contact info, invoices, consents, communication log

Patient (pet): species/breed/sex/DOB, microchip, allergies, problem list

Relationships: one client can have many patients; sometimes shared ownership

2) The visit is the “unit of work”

Almost everything hangs off a Visit / Encounter (often called a Consultation):

It’s the medical note + charges + orders bundle.

Example: IDEXX Neo explicitly frames a consultation as “the appointment visit record and invoice for the patient,” and uses templates to keep exam notes consistent. 
IDEXX Neo Support

So in practice: open appointment → start consultation/visit → document + order labs + add treatments → invoice auto-builds.

3) Two parallel timelines (that constantly cross)

Most vet systems keep both:

A) Clinical timeline

SOAP note (or similar structure)

Diagnoses/problems

Medications + prescriptions

Vaccinations

Lab/imaging results

Attachments (PDFs, photos, images)

B) Financial timeline

Line items (services/products)

Estimates

Invoices/receipts/refunds

Inventory movements

Old-school systems (ex: AVImark) literally call it Medical History entries, where you add treatments/diagnoses and can attach files; it also has explicit support for a Medical Condition Record (SOAP) prompt. 
Covetrus.com
+2
Covetrus.com
+2

4) Codes + templates are the secret sauce (and also the pain)

Clinics don’t want to type. They want:

Procedure/charge templates (exam types, vaccines, surgery packs)

Clinical templates (SOAP macros, discharge instructions)

Inventory-linked items (when you bill it, stock decrements)

Triggers (billing triggered by clinical record actions)

Modern cloud systems lean hard on templating. ezyVet, for example, documents a full template variable system and ties sales templates to clinical record billing triggers. 
ezyVet Knowledge Center
+1

They’re even rolling out “AI-assisted notes” to draft SOAP notes. 
ezyVet

5) Integrations are not optional anymore

Big buckets:

Diagnostics (IDEXX, etc.): results land inside the patient record, often with two-way ordering/results. 
IDEXX
+1

Imaging (DICOM viewers)

Payments

Client comms (SMS/email reminders, patient portal)

How to design your own Django version (so it doesn’t turn into spaghetti)
Data model (minimum viable, sane)

Use these as first-class models:

Client

Patient

Appointment

Encounter (aka visit/consultation)

Problem (diagnosis/problem list)

Observation (vitals, measurements)

Note (SOAP sections or structured fields)

Order (labs/imaging/referrals)

Result (lab values + attachments)

Medication + Prescription

ProcedurePerformed (clinical action)

ChargeLineItem (financial)

Invoice + Payment

InventoryItem + StockMovement

Document / Attachment (generic, linked to encounter/result/etc.)

Key rule: Encounter is the hub. Don’t let everything attach to everything.

Record organization UX (what users expect)

Veterinary staff usually want:

A left-to-right flow: Check-in → Vitals → Exam/SOAP → Orders → Treatments → Discharge → Invoice

A timeline view for quick scanning (vaccines, labs, meds, prior visits)

A problem list that persists across visits

Templates everywhere (exam types, discharge, vaccines)

Auditability (you’ll thank yourself later)

Medical records become legal records fast.

Immutable-ish event log for edits (who changed what, when)

Soft-delete + “entered in error”

Store original lab payloads when importing results

Multi-tenant reality (if this is SaaS)

Decide early:

One database per clinic or shared DB with organization_id everywhere.

Permission model: receptionist vs tech vs vet vs admin.

What systems exist (so you can steal the right ideas)

A non-exhaustive list of widely used PIMS/EHR platforms:

IDEXX Neo (cloud, consultation-centered) 
IDEXX Neo Support
+1

IDEXX Cornerstone (established, deep diagnostics integrations) 
Passpaw
+1

ezyVet (templates + billing triggers + lots of customization) 
ezyVet Knowledge Center
+2
ezyVet Knowledge Center
+2

AVImark (legacy-heavy but still common; medical history + SOAP hooks) 
Covetrus.com
+2
Covetrus.com
+2

Covetrus Pulse (emphasizes EMR + comms history in record) 
Covetrus.com

(There are others like Vetspire/Shepherd/Hippo/Digitail, but the architecture rhymes.)

What I can still do right now: if you paste just these files (or upload a zip), I’ll give you a real architecture review instead of vibes:

pyproject.toml / requirements*.txt

settings.py (or split settings folder)

your core app models.py + migrations

URL routes + any API layer you’re using

anything that handles Encounter/Consultation + billing linkages

Until then: if your design doesn’t revolve around Encounter as the hub that produces both clinical record + invoice, you’ll end up rewriting it anyway, which is the traditional developer holiday activity.

Skip to content
Chat history
You said:
what electronic health records for pets/vetrinarians do their systems have how do they work how are they organized because i"m writing my own
ChatGPT said:

Veterinary EHRs (usually bundled into a PIMS: Practice Information/Management System) are basically “everything the clinic does” glued together so the invoice and the medical record can’t drift apart. Humans love drifting. Software exists to stop them.

Here’s how the mainstream ones tend to work and how they’re organized, using real patterns you’ll see in systems like IDEXX Cornerstone (legacy/on-prem)
IDEXX Veterinary Software+1
and cloud platforms like Covetrus Pulse
Covetrus.com+1
and ezyVet
ezyVet+1
.
1) The core objects every vet EHR is built around
Client (owner)

    Contact info, communication preferences (SMS/email), consent flags.

    Billing profile: invoices, estimates, payments, credits, memberships/wellness plans.

Patient (pet)

    Species/breed/sex/DOB/weight trend.

    Allergies, chronic problems, “alerts” (bite risk, fractious, med warnings).

    Microchip, vaccination status, travel certificates.

Encounter / Visit (the “chart note container”)

This is the anchor. Everything hangs off the encounter:

    SOAP note (Subjective, Objective, Assessment, Plan) is the common structure.

    Tasks performed, meds dispensed, discharge instructions.

    Attachments: images, PDFs, consent forms.

Orders & Results

    Lab orders, imaging orders, external referrals.

    Results come back and get attached to the patient record and often to the specific encounter (so you can answer “why did we order this?”).

Treatments / Whiteboard / Treatment Board

Clinics need a live operations view: who’s here, what’s pending, what’s next.

    Cornerstone literally trains “patient visit list / whiteboard” workflows.
    IDEXX

    Pulse markets an integrated digital treatment board updating in real time.
    Covetrus.com

Billing items (charges)

This is the part nobody admits is medically important… until it’s missing.

    Many systems link medical actions to billable items (invoice items) so the record and the money match. Cornerstone explicitly talks about invoice items and setup knowledge around EMR workflows.
    Cornerstone Help Hub+1

2) How the medical record is typically organized in the UI

Most vet EHRs present the patient chart in a few predictable “tabs”:

    Summary

    Active problems, allergies, current meds, last visit, last weight.

    Timeline / Clinical Record

    Reverse-chronological list of encounters, notes, lab results, images, attachments.

    Think “event log” more than “one long document.”

    SOAP notes & templates

    Template-driven notes (vaccines, wellness, sick visit, surgery).

    Increasingly, systems also bolt on dictation/AI note drafting (because typing is misery). ezyVet even advertises AI-assisted SOAP drafting from recordings.
    ezyVet

    (You don’t need AI. But humans love shiny things.)

    Diagnostics

    Lab/imaging results, often pulled in via integrations so staff don’t retype values. IDEXX positions diagnostic integration as reducing data entry mistakes.
    IDEXX Veterinary Software

    Medications

    Prescriptions, refills, controlled drug logs, pharmacy connections. Pulse explicitly calls out EMR content including prescriptions and diagnostic results.
    Covetrus.com

    Documents

    Consent forms, euthanasia forms, travel certs, discharge instructions.

    Comms

    Reminders, SMS threads, email history. Pulse highlights “full communications histories” inside the medical record.
    Covetrus.com

3) The workflow most systems are built to support

A clinic day is basically a conveyor belt:

Book → Check-in → Roomed → Exam → Orders → Results → Treatments → Invoice → Pay → Remind

Covetrus literally markets the “book/prepare/consult/diagnose/treat/pay/remind” flow.
Covetrus.com

If you’re writing your own, the key is: design for state changes. You’re not just storing notes, you’re moving an animal through a pipeline with humans who forget things.
4) What matters most in your data model (so you don’t hate yourself later)

If you want something that scales beyond your own brain:
A) Event-sourced-ish “clinical timeline”

Store everything as time-stamped events (note created, weight recorded, lab result received, med dispensed).

    Then build “views” (Summary tab, Med list, Problem list) from those events.

B) Separate “clinical truth” from “billing truth”

Link them, don’t merge them.

    Example: a “ProcedurePerformed” clinical event can reference one or more billable line items.

    Sometimes you do something medically but comp it, discount it, or bundle it.

C) Encounters as containers, but allow cross-encounter continuity

    Problems persist across visits (atopy, heart murmur, lymphoma).

    Medications have durations, refills, stop reasons.

D) Make integrations first-class citizens

Labs/imaging are huge in vet med.

    Systems like Cornerstone emphasize diagnostic + imaging integrations.
    IDEXX Veterinary Software

    Your model should treat “Result from external system” as a normal object with provenance (source, timestamps, reference IDs).

5) Features you’ll see in real products (useful as a checklist)

    Scheduling + multi-resource calendar (doctor/room/equipment)

    Patient chart (SOAP, templates)

    Orders/results + attachments

    Inventory + dispensing (ties to charges)

    Reminders/comms

    Treatment board / hospitalization flows
    Covetrus.com

    Reporting (revenue, compliance, medical KPIs)

    Permissions/audit trail (who edited what, when)

    Multi-location, multi-provider

(Cloud systems like Pulse and ezyVet pitch “all-in-one” plus integrations rather than being just “medical notes.”
Covetrus.com+1
)
6) A sane “minimum viable” EHR you can actually build

If you’re building this yourself, don’t start by recreating a giant clinic ERP. Start with:

    Client + Patient CRUD

    Encounter + SOAP note (with templates)

    Orders/results (attach PDFs/images; simple lab panel structure later)

    Med list + dispensing log

    Timeline view (everything in one chronological stream)

    Audit log + roles

Everything else is “phase 2” (inventory, reminders, payments, boards).

If you build those six cleanly, you’ll already be ahead of half the commercial software that costs clinics a small fortune and still manages to feel like it was designed during the dial-up era.
You said:
take a look at this project I am building with claAUDE ON DJANGO https://github.com/nestorwheelock/petfriendlyvet.com
ChatGPT said:

You’re basically rebuilding a veterinary practice management system (PIMS) plus the medical record (EHR/EMR) part. Humans keep reinventing this wheel because they hate paying monthly subscriptions. Respect.
How vet EHRs are usually organized (the common pattern)
1) The core “people + pets” graph

Most systems start with:

    Client (owner/guardian): contact info, invoices, consents, communication log

    Patient (pet): species/breed/sex/DOB, microchip, allergies, problem list

    Relationships: one client can have many patients; sometimes shared ownership

2) The visit is the “unit of work”

Almost everything hangs off a Visit / Encounter (often called a Consultation):

    It’s the medical note + charges + orders bundle.

    Example: IDEXX Neo explicitly frames a consultation as “the appointment visit record and invoice for the patient,” and uses templates to keep exam notes consistent.
    IDEXX Neo Support

So in practice: open appointment → start consultation/visit → document + order labs + add treatments → invoice auto-builds.
3) Two parallel timelines (that constantly cross)

Most vet systems keep both:

A) Clinical timeline

    SOAP note (or similar structure)

    Diagnoses/problems

    Medications + prescriptions

    Vaccinations

    Lab/imaging results

    Attachments (PDFs, photos, images)

B) Financial timeline

    Line items (services/products)

    Estimates

    Invoices/receipts/refunds

    Inventory movements

Old-school systems (ex: AVImark) literally call it Medical History entries, where you add treatments/diagnoses and can attach files; it also has explicit support for a Medical Condition Record (SOAP) prompt.
Covetrus.com+2Covetrus.com+2
4) Codes + templates are the secret sauce (and also the pain)

Clinics don’t want to type. They want:

    Procedure/charge templates (exam types, vaccines, surgery packs)

    Clinical templates (SOAP macros, discharge instructions)

    Inventory-linked items (when you bill it, stock decrements)

    Triggers (billing triggered by clinical record actions)

Modern cloud systems lean hard on templating. ezyVet, for example, documents a full template variable system and ties sales templates to clinical record billing triggers.
ezyVet Knowledge Center+1

They’re even rolling out “AI-assisted notes” to draft SOAP notes.
ezyVet
5) Integrations are not optional anymore

Big buckets:

    Diagnostics (IDEXX, etc.): results land inside the patient record, often with two-way ordering/results.
    IDEXX+1

    Imaging (DICOM viewers)

    Payments

    Client comms (SMS/email reminders, patient portal)

How to design your own Django version (so it doesn’t turn into spaghetti)
Data model (minimum viable, sane)

Use these as first-class models:

    Client

    Patient

    Appointment

    Encounter (aka visit/consultation)

    Problem (diagnosis/problem list)

    Observation (vitals, measurements)

    Note (SOAP sections or structured fields)

    Order (labs/imaging/referrals)

    Result (lab values + attachments)

    Medication + Prescription

    ProcedurePerformed (clinical action)

    ChargeLineItem (financial)

    Invoice + Payment

    InventoryItem + StockMovement

    Document / Attachment (generic, linked to encounter/result/etc.)

Key rule: Encounter is the hub. Don’t let everything attach to everything.
Record organization UX (what users expect)

Veterinary staff usually want:

    A left-to-right flow: Check-in → Vitals → Exam/SOAP → Orders → Treatments → Discharge → Invoice

    A timeline view for quick scanning (vaccines, labs, meds, prior visits)

    A problem list that persists across visits

    Templates everywhere (exam types, discharge, vaccines)

Auditability (you’ll thank yourself later)

Medical records become legal records fast.

    Immutable-ish event log for edits (who changed what, when)

    Soft-delete + “entered in error”

    Store original lab payloads when importing results

Multi-tenant reality (if this is SaaS)

Decide early:

    One database per clinic or shared DB with organization_id everywhere.

    Permission model: receptionist vs tech vs vet vs admin.

What systems exist (so you can steal the right ideas)

A non-exhaustive list of widely used PIMS/EHR platforms:

    IDEXX Neo (cloud, consultation-centered)
    IDEXX Neo Support+1

    IDEXX Cornerstone (established, deep diagnostics integrations)
    Passpaw+1

    ezyVet (templates + billing triggers + lots of customization)
    ezyVet Knowledge Center+2ezyVet Knowledge Center+2

    AVImark (legacy-heavy but still common; medical history + SOAP hooks)
    Covetrus.com+2Covetrus.com+2

    Covetrus Pulse (emphasizes EMR + comms history in record)
    Covetrus.com

    (There are others like Vetspire/Shepherd/Hippo/Digitail, but the architecture rhymes.)

About your repo link (petfriendlyvet.com)

I tried to open and read the code directly from GitHub, but GitHub is throwing the “There was an error while loading” wall in the web viewer for your files, so I can’t reliably see your Django models/settings right now from this interface.

What I can still do right now: if you paste just these files (or upload a zip), I’ll give you a real architecture review instead of vibes:

    pyproject.toml / requirements*.txt

    settings.py (or split settings folder)

    your core app models.py + migrations

    URL routes + any API layer you’re using

    anything that handles Encounter/Consultation + billing linkages

Until then: if your design doesn’t revolve around Encounter as the hub that produces both clinical record + invoice, you’ll end up rewriting it anyway, which is the traditional developer holiday activity.
You said:
anything else I should tell claude?
ChatGPT said:

Yes. There are a few very specific things you should tell Claude, otherwise it will cheerfully build you a beautiful disaster and call it “clean architecture.”

This is the part where you act like the grumpy senior engineer and Claude is the enthusiastic intern who read half a blog post.
1) Tell Claude what this is not

Claude loves overengineering unless you fence it in.

Explicitly say:

    This is not a hospital EHR clone

    This is not a billing-first accounting system

    This is not a single giant MedicalRecord blob

    This is not optimized for US insurance claims

Veterinary EHRs are workflow-first, not compliance-first. If you don’t say that, Claude will invent abstractions that only make sense to insurers and philosophers.
2) Make “Encounter is the hub” non-negotiable

Say this verbatim or close to it:

    The Encounter (Visit/Consultation) is the central aggregate root.
    Clinical notes, observations, orders, results, procedures, medications, and billable items must all be linked to an Encounter.
    Patients and Problems persist across Encounters.

If you don’t state this clearly, Claude will:

    Attach labs directly to patients

    Attach meds directly to owners

    Invent three competing “visit” concepts

You only want one.
3) Tell Claude to separate clinical truth from financial truth

This is the #1 mistake DIY EHRs make.

Tell it:

    Clinical actions and financial charges are separate models.
    A clinical event may reference zero or more billable items.
    Billing must never overwrite or distort the clinical record.

Why this matters:

    Discounts, comps, bundles, refunds happen

    Medical history must stay accurate even if money changes

    Clinics do things medically that never get billed

If you don’t say this, you’ll end up with Procedure = Charge and hate yourself later.
4) Demand an append-only clinical timeline

Say this clearly:

    The medical record must be modeled as an append-only, timestamped event stream with soft corrections (“entered in error”), not destructive edits.

That unlocks:

    Legal defensibility

    “What did we know at the time?”

    A clean patient timeline UI

Claude will default to mutable rows unless told otherwise, because most CRUD apps are lies.
5) Force structured data and free text

Vet med is messy. Don’t let Claude pretend otherwise.

Tell it:

    SOAP notes must support structured fields and free-text simultaneously.
    Vitals, weights, meds, problems should be queryable.
    Narrative context must never be forced into enums.

This avoids:

    Everything becoming JSONField soup

    Or worse, everything becoming enums that no vet will use

6) Tell Claude to design for state transitions, not screens

Important.

Say:

    Model patient and visit workflow as explicit state transitions
    (scheduled → checked in → in exam → diagnostics → treatment → discharge → closed).
    UI derives from state, not the other way around.

Otherwise you’ll get:

    Pretty forms

    Zero operational awareness

    No treatment board or hospitalization logic

7) Make integrations first-class, not “later”

Even if you don’t implement them yet.

Tell Claude:

    External lab and imaging results must be stored with source metadata, raw payloads, and reference IDs.
    Imported data must never overwrite clinician-entered data.

This prevents:

    Lost lab context

    Silent overwrites

    “Why does this value look different than the PDF?”

8) Multi-tenant reality check

Even if this is single-clinic now, say this:

    The data model must be organization-scoped from day one.
    No global tables without an organization or clinic boundary.

Claude will otherwise happily write something that only works for one happy clinic on one happy laptop.
9) Permissions matter more than features

Say:

    Role-based access is required: reception, tech, vet, admin.
    Editing medical records must be auditable and permission-limited.

This is where many “DIY EHRs” quietly die.
10) Finally, tell Claude how to think

This is the magic sentence:

    Favor boring, explicit models over clever abstractions.
    Optimize for clinic staff comprehension, not developer elegance.

That single line prevents 40% of nonsense.
A copy-paste prompt you can actually use

You can hand Claude this and save yourself two rewrites:

You are helping build a veterinary EHR/PIMS in Django.

Constraints:
- Encounter (Visit/Consultation) is the central aggregate root.
- Clinical data and financial data must be separate but linkable.
- Medical records are append-only with auditability and soft corrections.
- Support structured data AND free text in SOAP notes.
- Model workflow as explicit state transitions.
- Design for multi-tenant clinics from day one.
- External labs/imaging are first-class entities with source metadata.
- Favor boring, explicit models over clever abstractions.

Do not over-engineer. Optimize for real clinic workflows.

If Claude still goes off the rails after that, that’s not an AI problem. That’s just software development, where everyone learns the hard way.

And yes, this is absolutely the right project to be building instead of paying Covetrus forever.


ChatGPT can make mistakes. Check important info. See Cookie Preferences.

