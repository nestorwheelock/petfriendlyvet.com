# Pet-Friendly Veterinary Clinic - Database Schema

**Prepared by:** Nestor Wheelock - South City Computer
**Last Updated:** December 2025

---

## Overview

This document describes the complete database schema for the Pet-Friendly veterinary clinic platform. The schema is organized into 9 Django apps that can be packaged as reusable modules.

---

## Entity Relationship Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CORE ENTITIES                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    User      │───────│ OwnerProfile │───────│    Pet       │
│  (Django)    │  1:1  │   (CRM)      │  1:N  │ (vet_clinic) │
└──────────────┘       └──────────────┘       └──────────────┘
       │                      │                      │
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ StaffProfile │       │LoyaltyMember │       │MedicalRecord │
│   (staff)    │       │  (loyalty)   │       │ (vet_clinic) │
└──────────────┘       └──────────────┘       └──────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           APPOINTMENTS MODULE                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │ ServiceType  │
                         │              │
                         └──────────────┘
                                │
                                │ N:1
                                ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    User      │───────│ Appointment  │───────│     Pet      │
│              │  N:1  │              │  N:1  │              │
└──────────────┘       └──────────────┘       └──────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Reminder │ │ Invoice  │ │ Clinical │
             │          │ │          │ │   Note   │
             └──────────┘ └──────────┘ └──────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                           E-COMMERCE MODULE                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Category   │───────│   Product    │───────│  StockLevel  │
│              │  1:N  │              │  1:1  │              │
└──────────────┘       └──────────────┘       └──────────────┘
                                │
                                │ N:M
                                ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│     Cart     │───────│  CartItem    │       │  StockBatch  │
│              │  1:N  │              │       │  (expiry)    │
└──────────────┘       └──────────────┘       └──────────────┘
       │
       │
       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    Order     │───────│  OrderItem   │───────│   Payment    │
│              │  1:N  │              │  N:1  │              │
└──────────────┘       └──────────────┘       └──────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                          BILLING MODULE                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Invoice    │───────│InvoiceLineItm│       │  CouponCode  │
│              │  1:N  │              │       │              │
└──────────────┘       └──────────────┘       └──────────────┘
       │
       ├──────────────────────────────┐
       ▼                              ▼
┌──────────────┐               ┌──────────────┐
│   Payment    │               │    CFDI      │
│              │               │  (Mexican)   │
└──────────────┘               └──────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                        COMMUNICATIONS MODULE                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Channel    │───────│ Conversation │───────│   Message    │
│ (email/SMS/  │  1:N  │              │  1:N  │              │
│  WhatsApp)   │       └──────────────┘       └──────────────┘
└──────────────┘              │
                              │
                              ▼
                       ┌──────────────┐
                       │MessageTemplate│
                       │              │
                       └──────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ACCOUNTING MODULE                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Account    │───────│ JournalEntry │───────│ JournalLine  │
│ (Chart of    │  N:M  │              │  1:N  │              │
│  Accounts)   │       └──────────────┘       └──────────────┘
└──────────────┘
       │
       │
       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    Vendor    │───────│     Bill     │───────│  BillPayment │
│              │  1:N  │              │  1:N  │              │
└──────────────┘       └──────────────┘       └──────────────┘
```

---

## Module: django-multilingual

### Translation
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| content_type | FK(ContentType) | Generic relation |
| object_id | PositiveInteger | Object ID |
| field_name | CharField(100) | Field being translated |
| language | CharField(5) | Language code (es, en, de, fr, it) |
| translation | TextField | Translated content |
| is_ai_generated | Boolean | True if AI generated |
| reviewed_by | FK(User) | Staff who reviewed |
| reviewed_at | DateTime | Review timestamp |
| created_at | DateTime | Creation timestamp |

### Language
| Field | Type | Description |
|-------|------|-------------|
| code | CharField(5) | ISO code (es, en, de) |
| name | CharField(100) | Display name |
| native_name | CharField(100) | Name in native language |
| is_core | Boolean | Pre-translated language |
| is_active | Boolean | Available for selection |
| order | Integer | Display order |

---

## Module: django-vet-clinic

### Pet
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | FK(User) | Pet owner |
| name | CharField(100) | Pet name |
| species | CharField(20) | dog, cat, bird, rabbit, other |
| breed | CharField(100) | Breed |
| color | CharField(100) | Color/markings |
| date_of_birth | Date | Birth date |
| gender | CharField(10) | male, female, unknown |
| weight_kg | Decimal(6,2) | Current weight |
| microchip_number | CharField(50) | Microchip ID |
| photo | ImageField | Pet photo |
| notes | TextField | General notes |
| is_deceased | Boolean | Deceased flag |
| deceased_date | Date | Date of death |
| is_active | Boolean | Active in system |
| created_at | DateTime | Created timestamp |
| updated_at | DateTime | Updated timestamp |

### MedicalRecord
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| pet | FK(Pet) | Related pet |
| record_type | CharField(20) | exam, vaccination, surgery, lab, prescription |
| date | Date | Record date |
| title | CharField(200) | Record title |
| description | TextField | Details |
| diagnosis | TextField | Diagnosis |
| treatment | TextField | Treatment given |
| notes | TextField | Additional notes |
| internal_notes | TextField | Staff-only notes |
| attachments | JSONField | List of file paths |
| created_by | FK(User) | Recording staff |
| created_at | DateTime | Created timestamp |

### VaccinationRecord
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| pet | FK(Pet) | Related pet |
| vaccine_name | CharField(200) | Vaccine name |
| vaccine_type | CharField(50) | Type/category |
| manufacturer | CharField(200) | Manufacturer |
| lot_number | CharField(100) | Lot number |
| administered_date | Date | Date given |
| expiry_date | Date | Vaccine expiry |
| next_due_date | Date | Next dose due |
| administered_by | FK(User) | Veterinarian |
| site | CharField(100) | Injection site |
| notes | TextField | Notes |

### Allergy
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| pet | FK(Pet) | Related pet |
| allergen | CharField(200) | Allergen |
| reaction | TextField | Reaction description |
| severity | CharField(20) | mild, moderate, severe |
| diagnosed_date | Date | Diagnosis date |
| notes | TextField | Notes |

### Medication
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| pet | FK(Pet) | Related pet |
| name | CharField(200) | Medication name |
| dosage | CharField(100) | Dosage |
| frequency | CharField(100) | Frequency |
| route | CharField(50) | oral, injection, topical |
| start_date | Date | Start date |
| end_date | Date | End date |
| is_ongoing | Boolean | Ongoing medication |
| prescribed_by | FK(User) | Prescribing vet |
| notes | TextField | Instructions |

---

## Module: django-appointments

### ServiceCategory
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Category name |
| slug | SlugField | URL slug |
| description | TextField | Description |
| icon | CharField(50) | Icon class/name |
| order | Integer | Display order |
| is_active | Boolean | Active status |

### ServiceType
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| category | FK(ServiceCategory) | Category |
| name | CharField(200) | Service name |
| slug | SlugField | URL slug |
| description | TextField | Description |
| duration_minutes | Integer | Duration |
| price | Decimal(10,2) | Base price |
| price_varies | Boolean | Price varies flag |
| requires_consultation | Boolean | Needs consult first |
| species | JSONField | Applicable species |
| is_emergency | Boolean | Emergency service |
| is_active | Boolean | Active status |

### Appointment
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | FK(User) | Pet owner |
| pet | FK(Pet) | Pet |
| service_type | FK(ServiceType) | Service |
| date | Date | Appointment date |
| start_time | Time | Start time |
| end_time | Time | End time |
| status | CharField(20) | pending, confirmed, completed, cancelled, no_show |
| notes | TextField | Appointment notes |
| internal_notes | TextField | Staff notes |
| created_via | CharField(20) | web, ai, phone, walk_in |
| confirmed_at | DateTime | Confirmation timestamp |
| reminder_sent | Boolean | Reminder sent flag |
| created_at | DateTime | Created timestamp |
| updated_at | DateTime | Updated timestamp |

### Reminder
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| appointment | FK(Appointment) | Related appointment |
| reminder_type | CharField(20) | appointment, vaccination, followup |
| channel | CharField(20) | email, sms, whatsapp |
| scheduled_for | DateTime | Scheduled time |
| sent_at | DateTime | Sent timestamp |
| status | CharField(20) | pending, sent, failed, confirmed |
| response | TextField | Customer response |

---

## Module: django-simple-store

### Category (Store)
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Category name |
| slug | SlugField | URL slug |
| parent | FK(self) | Parent category |
| description | TextField | Description |
| image | ImageField | Category image |
| is_active | Boolean | Active status |
| order | Integer | Display order |

### Product
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Product name |
| slug | SlugField | URL slug |
| sku | CharField(50) | SKU |
| barcode | CharField(50) | Barcode |
| category | FK(Category) | Category |
| description | TextField | Description |
| short_description | CharField(500) | Short description |
| price | Decimal(10,2) | Retail price |
| cost_price | Decimal(10,2) | Cost price |
| compare_at_price | Decimal(10,2) | Original price |
| species | JSONField | Applicable species |
| requires_prescription | Boolean | Rx required |
| is_controlled | Boolean | Controlled substance |
| weight_kg | Decimal(6,3) | Shipping weight |
| is_active | Boolean | Active status |
| is_featured | Boolean | Featured product |
| created_at | DateTime | Created timestamp |

### ProductImage
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| product | FK(Product) | Related product |
| image | ImageField | Image file |
| alt_text | CharField(200) | Alt text |
| order | Integer | Display order |
| is_primary | Boolean | Primary image |

### StockLevel
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| product | FK(Product) | Related product |
| quantity | Integer | Current quantity |
| reorder_point | Integer | Reorder threshold |
| reorder_quantity | Integer | Quantity to reorder |
| location | CharField(100) | Storage location |
| last_count_date | Date | Last inventory count |

### StockBatch
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| product | FK(Product) | Related product |
| batch_number | CharField(100) | Batch/lot number |
| quantity | Integer | Quantity in batch |
| expiry_date | Date | Expiration date |
| received_date | Date | Date received |
| cost_per_unit | Decimal(10,2) | Unit cost |

### Cart
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | FK(User) | Cart owner (nullable) |
| session_key | CharField(255) | Session for guests |
| created_at | DateTime | Created timestamp |
| updated_at | DateTime | Updated timestamp |

### CartItem
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| cart | FK(Cart) | Related cart |
| product | FK(Product) | Product |
| quantity | Integer | Quantity |
| added_at | DateTime | Added timestamp |

### Order
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| order_number | CharField(50) | Order number |
| owner | FK(User) | Customer |
| status | CharField(20) | pending, processing, shipped, delivered, cancelled |
| subtotal | Decimal(10,2) | Subtotal |
| discount_amount | Decimal(10,2) | Discount |
| tax_amount | Decimal(10,2) | Tax (IVA) |
| shipping_amount | Decimal(10,2) | Shipping cost |
| total | Decimal(10,2) | Total |
| shipping_address | JSONField | Address details |
| notes | TextField | Order notes |
| created_at | DateTime | Created timestamp |
| shipped_at | DateTime | Shipped timestamp |
| delivered_at | DateTime | Delivered timestamp |

### OrderItem
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| order | FK(Order) | Related order |
| product | FK(Product) | Product |
| quantity | Integer | Quantity |
| unit_price | Decimal(10,2) | Price at purchase |
| total | Decimal(10,2) | Line total |

---

## Module: django-billing

### Invoice
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| invoice_number | CharField(50) | Invoice number |
| owner | FK(User) | Customer |
| pet | FK(Pet) | Related pet (optional) |
| appointment | FK(Appointment) | Related appointment |
| order | FK(Order) | Related order |
| subtotal | Decimal(10,2) | Subtotal |
| discount_amount | Decimal(10,2) | Discount |
| tax_amount | Decimal(10,2) | IVA 16% |
| total | Decimal(10,2) | Total |
| amount_paid | Decimal(10,2) | Amount paid |
| status | CharField(20) | draft, sent, paid, partial, overdue, cancelled |
| due_date | Date | Payment due date |
| cfdi_uuid | UUID | CFDI fiscal folio |
| cfdi_xml | TextField | CFDI XML content |
| cfdi_pdf | FileField | CFDI PDF |
| created_at | DateTime | Created timestamp |
| paid_at | DateTime | Paid timestamp |

### InvoiceLineItem
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| invoice | FK(Invoice) | Related invoice |
| description | CharField(500) | Line description |
| quantity | Decimal(10,2) | Quantity |
| unit_price | Decimal(10,2) | Unit price |
| discount_percent | Decimal(5,2) | Discount % |
| line_total | Decimal(10,2) | Line total |
| service | FK(ServiceType) | Related service |
| product | FK(Product) | Related product |
| clave_producto_sat | CharField(10) | SAT product code |
| clave_unidad_sat | CharField(5) | SAT unit code |

### Payment
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| invoice | FK(Invoice) | Related invoice |
| amount | Decimal(10,2) | Payment amount |
| payment_method | CharField(20) | stripe_card, cash, manual_card, account_credit |
| stripe_payment_intent | CharField(100) | Stripe PI ID |
| stripe_charge_id | CharField(100) | Stripe charge ID |
| reference_number | CharField(100) | Reference number |
| notes | TextField | Payment notes |
| cash_discount_applied | Decimal(10,2) | Cash discount |
| recorded_by | FK(User) | Staff who recorded |
| created_at | DateTime | Created timestamp |

### CouponCode
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| code | CharField(50) | Coupon code |
| description | CharField(200) | Description |
| discount_type | CharField(10) | percent, fixed |
| discount_value | Decimal(10,2) | Discount value |
| minimum_purchase | Decimal(10,2) | Minimum order |
| max_uses | Integer | Max total uses |
| max_uses_per_customer | Integer | Max per customer |
| valid_from | DateTime | Valid from |
| valid_until | DateTime | Valid until |
| is_active | Boolean | Active status |
| times_used | Integer | Usage count |

---

## Module: django-crm-lite

### OwnerProfile
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | OneToOne(User) | Related user |
| phone | CharField(20) | Phone number |
| alternate_phone | CharField(20) | Alt phone |
| address | TextField | Address |
| preferred_language | CharField(5) | Language preference |
| preferred_channel | CharField(20) | email, sms, whatsapp |
| tier | CharField(20) | new, regular, vip, premium |
| lifetime_value | Decimal(10,2) | Total spent |
| visit_count | Integer | Visit count |
| last_visit_date | Date | Last visit |
| days_since_last_visit | Integer | Days inactive |
| churn_risk | CharField(20) | low, medium, high |
| tags | JSONField | Custom tags |
| notes | TextField | CRM notes |
| created_at | DateTime | Created timestamp |

### OwnerInteraction
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | FK(User) | Related owner |
| pet | FK(Pet) | Related pet |
| interaction_type | CharField(20) | visit, call_in, call_out, email, whatsapp |
| direction | CharField(10) | inbound, outbound |
| subject | CharField(500) | Subject |
| summary | TextField | Summary |
| outcome | CharField(100) | Outcome |
| sentiment | CharField(20) | positive, neutral, negative |
| requires_follow_up | Boolean | Follow-up needed |
| follow_up_date | Date | Follow-up date |
| follow_up_completed | Boolean | Follow-up done |
| handled_by | FK(User) | Staff member |
| created_at | DateTime | Created timestamp |

### CustomerSegment
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Segment name |
| slug | SlugField | URL slug |
| description | TextField | Description |
| rules | JSONField | Segmentation rules |
| member_count | Integer | Cached count |
| last_calculated | DateTime | Last calculation |
| is_dynamic | Boolean | Dynamic segment |
| is_active | Boolean | Active status |

---

## Module: django-omnichannel

### Channel
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(100) | Channel name |
| channel_type | CharField(20) | email, sms, whatsapp, voice |
| is_active | Boolean | Active status |
| config | JSONField | Channel configuration |

### Conversation
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | FK(User) | Customer |
| channel | FK(Channel) | Communication channel |
| status | CharField(20) | active, waiting, resolved, escalated |
| subject | CharField(500) | Subject/topic |
| assigned_to | FK(User) | Assigned staff |
| priority | CharField(20) | low, normal, high, urgent |
| last_message_at | DateTime | Last message time |
| resolved_at | DateTime | Resolution time |
| created_at | DateTime | Created timestamp |

### Message
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| conversation | FK(Conversation) | Related conversation |
| direction | CharField(10) | inbound, outbound |
| sender_type | CharField(20) | customer, staff, system, ai |
| sender | FK(User) | Sender (nullable) |
| content | TextField | Message content |
| content_type | CharField(20) | text, image, document, template |
| attachments | JSONField | Attachment list |
| external_id | CharField(200) | External message ID |
| status | CharField(20) | pending, sent, delivered, read, failed |
| sent_at | DateTime | Sent timestamp |
| delivered_at | DateTime | Delivered timestamp |
| read_at | DateTime | Read timestamp |
| created_at | DateTime | Created timestamp |

### MessageTemplate
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Template name |
| slug | SlugField | URL slug |
| channel | FK(Channel) | For which channel |
| category | CharField(50) | Template category |
| subject | CharField(200) | Email subject |
| content | TextField | Template content |
| variables | JSONField | Available variables |
| whatsapp_template_id | CharField(100) | WhatsApp template ID |
| is_approved | Boolean | WhatsApp approval status |
| is_active | Boolean | Active status |

---

## Module: django-loyalty

### LoyaltyTier
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(100) | Tier name |
| slug | SlugField | URL slug |
| min_points | Integer | Minimum points required |
| min_lifetime_spending | Decimal(10,2) | Minimum spend |
| points_multiplier | Decimal(3,2) | Points multiplier |
| discount_percent | Decimal(5,2) | Tier discount |
| free_services | JSONField | Free services list |
| color | CharField(20) | Display color |
| icon | CharField(50) | Icon |
| order | Integer | Display order |

### LoyaltyMembership
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | OneToOne(User) | Related user |
| tier | FK(LoyaltyTier) | Current tier |
| current_points | Integer | Available points |
| lifetime_points | Integer | Total earned |
| points_expiring_soon | Integer | Expiring points |
| next_expiry_date | Date | Next expiry |
| referral_code | CharField(20) | Unique referral code |
| referrals_count | Integer | Referral count |
| enrolled_at | DateTime | Enrollment date |

### PointsTransaction
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| membership | FK(LoyaltyMembership) | Related membership |
| transaction_type | CharField(20) | earn, redeem, expire, bonus, referral |
| points | Integer | Points (+ or -) |
| balance_after | Integer | Balance after |
| description | CharField(500) | Description |
| order | FK(Order) | Related order |
| invoice | FK(Invoice) | Related invoice |
| expires_at | Date | Expiry date |
| created_at | DateTime | Created timestamp |

### Reward
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Reward name |
| description | TextField | Description |
| reward_type | CharField(20) | discount, free_service, free_product |
| points_cost | Integer | Points required |
| discount_percent | Decimal(5,2) | Discount % |
| discount_amount | Decimal(10,2) | Fixed discount |
| free_service | FK(ServiceType) | Free service |
| free_product | FK(Product) | Free product |
| min_tier | FK(LoyaltyTier) | Minimum tier required |
| quantity_available | Integer | Available quantity |
| valid_until | DateTime | Expiry date |
| is_active | Boolean | Active status |

---

## Module: django-accounting

### Account
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| code | CharField(20) | Account code |
| name | CharField(200) | Account name |
| account_type | CharField(20) | asset, liability, equity, revenue, expense |
| parent | FK(self) | Parent account |
| is_bank | Boolean | Bank account flag |
| is_ar | Boolean | Accounts receivable |
| is_ap | Boolean | Accounts payable |
| is_cash | Boolean | Cash account |
| balance | Decimal(15,2) | Current balance |
| is_active | Boolean | Active status |

### JournalEntry
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| entry_number | CharField(50) | Entry number |
| date | Date | Entry date |
| description | TextField | Description |
| entry_type | CharField(20) | manual, invoice, payment, adjustment |
| invoice | FK(Invoice) | Related invoice |
| bill | FK(Bill) | Related bill |
| is_posted | Boolean | Posted status |
| posted_at | DateTime | Posted timestamp |
| posted_by | FK(User) | Posted by |
| created_by | FK(User) | Created by |
| created_at | DateTime | Created timestamp |

### JournalLine
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| entry | FK(JournalEntry) | Related entry |
| account | FK(Account) | Account |
| debit | Decimal(15,2) | Debit amount |
| credit | Decimal(15,2) | Credit amount |
| description | CharField(200) | Line description |

### Vendor
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Vendor name |
| rfc | CharField(13) | Tax ID (RFC) |
| contact_name | CharField(200) | Contact name |
| email | EmailField | Email |
| phone | CharField(20) | Phone |
| payment_terms | CharField(20) | net15, net30, net60 |
| default_expense_account | FK(Account) | Default expense |
| balance | Decimal(15,2) | Current balance |
| is_active | Boolean | Active status |

### Bill
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| vendor | FK(Vendor) | Vendor |
| bill_number | CharField(100) | Bill number |
| bill_date | Date | Bill date |
| due_date | Date | Due date |
| subtotal | Decimal(15,2) | Subtotal |
| tax | Decimal(15,2) | Tax amount |
| total | Decimal(15,2) | Total |
| amount_paid | Decimal(15,2) | Paid amount |
| status | CharField(20) | draft, pending, paid, cancelled |
| cfdi_uuid | UUID | Vendor CFDI UUID |
| created_at | DateTime | Created timestamp |

---

## Module: django-ai-assistant

### KnowledgeBase
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| title | CharField(500) | Title |
| slug | SlugField | URL slug |
| category | CharField(100) | Category |
| content | TextField | Knowledge content |
| keywords | JSONField | Search keywords |
| language | CharField(5) | Language |
| is_public | Boolean | Public visibility |
| is_active | Boolean | Active status |
| view_count | Integer | View count |
| helpful_count | Integer | Helpful votes |
| created_at | DateTime | Created timestamp |

### ChatSession
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| owner | FK(User) | Chat user (nullable) |
| session_key | CharField(255) | Session for guests |
| context | JSONField | Session context |
| started_at | DateTime | Start time |
| ended_at | DateTime | End time |
| message_count | Integer | Message count |
| resolved | Boolean | Resolution status |

### ChatMessage
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| session | FK(ChatSession) | Related session |
| role | CharField(20) | user, assistant, system |
| content | TextField | Message content |
| tool_calls | JSONField | Tool calls made |
| tool_results | JSONField | Tool results |
| tokens_used | Integer | Tokens consumed |
| model | CharField(100) | AI model used |
| created_at | DateTime | Created timestamp |

---

## Indexes

### Performance-Critical Indexes

```sql
-- Appointments
CREATE INDEX idx_appointment_date_status ON appointments_appointment(date, status);
CREATE INDEX idx_appointment_owner ON appointments_appointment(owner_id);
CREATE INDEX idx_appointment_pet ON appointments_appointment(pet_id);

-- Products
CREATE INDEX idx_product_category ON store_product(category_id);
CREATE INDEX idx_product_sku ON store_product(sku);
CREATE INDEX idx_product_active ON store_product(is_active);

-- Orders
CREATE INDEX idx_order_owner ON store_order(owner_id);
CREATE INDEX idx_order_status ON store_order(status);
CREATE INDEX idx_order_created ON store_order(created_at);

-- Invoices
CREATE INDEX idx_invoice_owner ON billing_invoice(owner_id);
CREATE INDEX idx_invoice_status ON billing_invoice(status);
CREATE INDEX idx_invoice_due_date ON billing_invoice(due_date);

-- Messages
CREATE INDEX idx_message_conversation ON communications_message(conversation_id);
CREATE INDEX idx_message_created ON communications_message(created_at);

-- Journal Entries
CREATE INDEX idx_journal_date ON accounting_journalentry(date);
CREATE INDEX idx_journal_posted ON accounting_journalentry(is_posted);

-- Pets
CREATE INDEX idx_pet_owner ON vet_clinic_pet(owner_id);
CREATE INDEX idx_pet_species ON vet_clinic_pet(species);
```

---

## Data Relationships Summary

### One-to-One
- User ↔ OwnerProfile
- User ↔ StaffProfile
- User ↔ LoyaltyMembership
- Product ↔ StockLevel
- ClinicalNote ↔ VitalSigns

### One-to-Many
- User → Pet (owner)
- User → Appointment (owner)
- User → Order (owner)
- Pet → MedicalRecord
- Pet → VaccinationRecord
- Appointment → Reminder
- Order → OrderItem
- Invoice → InvoiceLineItem
- Invoice → Payment
- Conversation → Message
- JournalEntry → JournalLine
- Vendor → Bill
- Bill → BillPayment

### Many-to-Many
- Product ↔ Category (through category hierarchy)
- ServiceType ↔ StaffProfile (services offered)
- EmailCampaign ↔ CustomerSegment (targeting)

---

## Migration Strategy

### Initial Setup
1. Create all Django apps with empty models
2. Run `makemigrations` for each app
3. Apply migrations in dependency order
4. Load initial fixtures (service types, categories, chart of accounts)

### Migration Order
1. `accounts` (User model extensions)
2. `multilingual` (translation infrastructure)
3. `vet_clinic` (Pet, MedicalRecord)
4. `appointments` (ServiceType, Appointment)
5. `store` (Product, Order)
6. `billing` (Invoice, Payment)
7. `communications` (Channel, Message)
8. `loyalty` (Tier, Membership)
9. `crm` (OwnerProfile, Segment)
10. `competitive` (Competitor tracking)
11. `marketing` (Campaigns, Sequences)
12. `staff` (StaffProfile, Scheduling)
13. `accounting` (Account, JournalEntry)
14. `ai_assistant` (Knowledge, Chat)
15. `reports` (Report, Dashboard)

---

*Total Tables: ~75*
*Total Relationships: ~150*
*Estimated Storage: 1-5 GB for first year*
