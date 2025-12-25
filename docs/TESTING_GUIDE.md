# Comprehensive Testing Guide

**Pet-Friendly Veterinary Clinic - Test Documentation**
**Version**: 1.0.0
**Last Updated**: 2025-12-25

---

## Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Running Tests](#running-tests)
4. [E2E Journey Simulations](#e2e-journey-simulations)
5. [Browser Tests](#browser-tests)
6. [Test Fixtures](#test-fixtures)
7. [Writing New Tests](#writing-new-tests)
8. [QA Process](#qa-process)

---

## Overview

The testing framework provides comprehensive coverage through multiple testing layers:

| Layer | Purpose | Speed | Coverage |
|-------|---------|-------|----------|
| Unit Tests | Isolated component logic | Fast | Models, services, utilities |
| Integration Tests | Cross-component flows | Medium | API endpoints, signal handlers |
| E2E Journey Tests | Complete user workflows | Medium | Business process validation |
| Browser Tests | UI rendering, JavaScript | Slow | Visual correctness, accessibility |

**Total Test Count**: ~600 tests
- E2E Journey Tests: ~112 tests
- Browser Tests: ~333 tests
- Unit/Integration: ~155 tests

---

## Test Architecture

```
tests/
├── unit/                         # Unit tests
│   ├── apps/                     # Per-app unit tests
│   │   ├── appointments/
│   │   ├── billing/
│   │   ├── pets/
│   │   └── ...
│   └── services/                 # Service layer tests
│
├── integration/                  # Integration tests
│   ├── test_billing_signals.py
│   ├── test_appointment_signals.py
│   └── test_order_signals.py
│
├── e2e/                          # End-to-end tests
│   ├── conftest.py               # E2E fixtures
│   ├── test_*_journey.py         # Journey simulations (14 files)
│   │
│   └── browser/                  # Playwright browser tests
│       ├── conftest.py           # Browser fixtures
│       └── test_*.py             # Browser tests (16 files)
│
└── fixtures/                     # Shared test data
    └── *.json
```

---

## Running Tests

### All Tests
```bash
pytest
```

### By Layer
```bash
# Unit tests only
pytest tests/unit/ -v

# E2E journey tests (no browser)
pytest tests/e2e/ --ignore=tests/e2e/browser/ -v

# Browser tests (headless)
pytest tests/e2e/browser/ -v

# Browser tests (visible browser)
pytest tests/e2e/browser/ -v --headed
```

### By Category
```bash
# Specific journey
pytest tests/e2e/test_appointment_flow.py -v

# Specific browser test file
pytest tests/e2e/browser/test_authentication.py -v

# Only tests matching pattern
pytest -k "loyalty" -v
```

### With Coverage
```bash
pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

### Watch Mode (Development)
```bash
pytest-watch -- tests/e2e/browser/test_authentication.py
```

---

## E2E Journey Simulations

Journey tests simulate complete user workflows using Django's test client. They validate business logic without browser overhead.

### 1. Appointment Flow (`test_appointment_flow.py`)

**Purpose**: Validate appointment → invoice → payment flow

| Test Class | Simulations |
|------------|-------------|
| `TestAppointmentCreatesInvoice` | Completed appointment creates invoice |
| | Completed appointment has line item |
| | In-progress appointment no invoice |
| | Cancelled appointment no invoice |
| | No-show appointment may create invoice |
| `TestAppointmentInvoiceUpdates` | Completing later doesn't duplicate invoice |
| `TestAppointmentWithProducts` | Appointment invoice can add products |
| `TestVaccinationAppointment` | Vaccination appointment creates invoice |
| `TestAPIAppointmentFlow` | Staff complete appointment creates invoice |
| | Appointment detail includes invoice link |
| `TestAppointmentPaymentFlow` | Full appointment payment flow |
| | Partial payment on appointment invoice |

---

### 2. Clinical Notes Journey (`test_clinical_notes_journey.py`)

**Purpose**: Validate clinical documentation workflow

| Test Class | Simulations |
|------------|-------------|
| `TestClinicalNotesJourney` | Complete clinical notes journey |
| `TestClinicalNoteTypes` | Note types available (SOAP, progress, surgical) |
| `TestPetDocuments` | Multiple document types (lab, xray, certificate) |

**Complete Journey Simulation**:
1. Create appointment with pet
2. Vet starts clinical notes (SOAP format)
3. Add vital signs (weight, temperature, heart rate)
4. Add diagnosis
5. Add treatment plan
6. Add prescription
7. Upload lab results
8. Complete appointment
9. Verify all notes linked to medical record

---

### 3. Customer Journey (`test_customer_journey.py`)

**Purpose**: Validate complete customer lifecycle

| Test Class | Simulations |
|------------|-------------|
| `TestFullCustomerJourney` | Complete customer journey (registration → appointment → payment) |
| `TestCustomerJourneyVariations` | Partial payment journey |
| | Cancelled appointment no invoice |
| | Multiple pets multiple appointments |
| `TestJourneyEdgeCases` | Same day appointment |
| | Appointment without pet |

**Complete Journey Simulation**:
1. Customer registers account
2. Customer adds pet profile
3. Customer books appointment
4. Staff confirms appointment
5. Customer arrives, checks in
6. Vet completes consultation
7. Invoice generated
8. Customer pays
9. Customer receives receipt

---

### 4. Delivery Driver Journey (`test_delivery_driver_journey.py`)

**Purpose**: Validate delivery driver workflow

| Test Class | Simulations |
|------------|-------------|
| `TestDeliveryDriverJourney` | Complete driver delivery journey |
| `TestDriverContractorWorkflow` | Contractor driver onboarding |
| `TestDeliveryFailureScenarios` | Delivery failed customer not home |
| | Delivery rescheduled after failure |

**Complete Journey Simulation**:
1. Driver logs in to driver app
2. Driver views assigned deliveries
3. Driver picks up order from clinic
4. Driver updates status to "picked up"
5. Driver navigates to customer
6. Driver arrives, updates status
7. Customer receives delivery
8. Driver captures photo proof
9. Driver marks as delivered
10. Customer rates delivery

---

### 5. Delivery Lifecycle (`test_delivery_lifecycle.py`)

**Purpose**: Validate delivery order processing

| Test Class | Simulations |
|------------|-------------|
| `TestOrderCreatesDelivery` | Delivery order creates delivery record |
| | Pickup order no delivery record |
| `TestDriverAssignment` | Assign driver to delivery |
| `TestDriverDeliveryWorkflow` | Full delivery lifecycle |
| | Invalid status transition raises error |
| | Failed delivery with reason |
| `TestProofOfDelivery` | Add photo proof |
| | Add signature proof |
| `TestCustomerTracking` | Customer can view delivery status |
| `TestCustomerRating` | Customer can rate completed delivery |
| | Cannot rate undelivered |
| `TestAPIDeliveryWorkflow` | Driver API list assigned deliveries |
| | Driver API update status |
| | Driver API submit proof |
| | Customer API rate delivery |
| `TestDeliverySlotBooking` | Booking updates slot count |
| | Slot available capacity |

---

### 6. Emergency Journey (`test_emergency_journey.py`)

**Purpose**: Validate emergency triage workflow

| Test Class | Simulations |
|------------|-------------|
| `TestEmergencyTriageJourney` | Complete emergency triage journey |
| `TestEmergencyReferral` | Referral to 24-hour hospital |
| `TestEmergencySymptoms` | Symptom severity levels (critical, urgent, routine) |

**Complete Journey Simulation**:
1. Customer reports emergency symptoms
2. System performs triage assessment
3. Symptoms classified by severity
4. If critical → immediate callback scheduled
5. If urgent → same-day appointment offered
6. If routine → next available slot offered
7. Emergency contact record created
8. On-call vet notified
9. If needed, referral to 24-hour hospital

---

### 7. Inventory Journey (`test_inventory_journey.py`)

**Purpose**: Validate inventory management workflow

| Test Class | Simulations |
|------------|-------------|
| `TestInventoryReorderJourney` | Complete reorder journey |
| `TestInventoryExpiryManagement` | Batch expiry tracking |
| `TestInventoryStockMovements` | Stock movement types (received, sold, adjusted, transferred) |

**Complete Journey Simulation**:
1. Stock level drops below reorder point
2. System flags low stock alert
3. Staff reviews and creates purchase order
4. PO sent to supplier
5. Stock received at clinic
6. Staff records stock receipt
7. Stock batch created with lot number and expiry
8. Stock levels updated
9. Alert cleared

---

### 8. Loyalty Journey (`test_loyalty_journey.py`)

**Purpose**: Validate loyalty program workflow

| Test Class | Simulations |
|------------|-------------|
| `TestLoyaltyProgramJourney` | Complete loyalty journey |
| `TestLoyaltyPointTransactions` | Transaction types (earned, redeemed, expired, bonus) |
| `TestLoyaltyRewards` | Reward redemption statuses |

**Complete Journey Simulation**:
1. Customer enrolled in loyalty program
2. Customer makes purchase
3. Points earned based on spend
4. Points added to account
5. Customer reaches new tier
6. Tier upgrade notification sent
7. Customer browses reward catalog
8. Customer redeems points for reward
9. Redemption record created
10. Points deducted from balance

---

### 9. Order to Invoice (`test_order_to_invoice.py`)

**Purpose**: Validate store order billing

| Test Class | Simulations |
|------------|-------------|
| `TestOrderCreatesInvoice` | Paid order creates invoice automatically |
| | Cash order creates pending invoice |
| | Delivery order creates invoice with shipping |
| `TestOrderStatusUpdatesInvoice` | Order marked paid updates invoice |
| `TestPaymentRecordingUpdatesInvoice` | Partial payment updates invoice balance |
| | Full payment marks invoice paid |
| | Multiple payments sum correctly |
| `TestInvoiceLineItemsFromOrder` | Invoice has correct line items |
| `TestAPIOrderToInvoiceFlow` | Checkout API creates order and invoice |
| | Order detail includes invoice link |
| | Record payment API updates invoice |

---

### 10. Prescription Journey (`test_prescription_journey.py`)

**Purpose**: Validate prescription workflow

| Test Class | Simulations |
|------------|-------------|
| `TestPrescriptionJourney` | Complete prescription journey |
| `TestPrescriptionEdgeCases` | Prescription expires |
| | No refills remaining |
| | Controlled medication extra verification |
| | Multiple active prescriptions |

**Complete Journey Simulation**:
1. Vet prescribes medication during appointment
2. Prescription created with dosage, refills
3. Pharmacy staff reviews prescription
4. Medication dispensed
5. Refill count decremented
6. Customer picks up or delivery scheduled
7. Customer requests refill
8. If refills remaining → dispense again
9. If no refills → request vet authorization

---

### 11. Referral Journey (`test_referral_journey.py`)

**Purpose**: Validate specialist referral workflow

| Test Class | Simulations |
|------------|-------------|
| `TestSpecialistReferralJourney` | Complete referral journey |
| `TestInboundReferral` | Inbound referral from external vet |
| `TestReferralUrgencyScenarios` | Emergency referral same day |
| | Routine referral scheduled weeks out |

**Complete Journey Simulation**:
1. Vet determines specialist needed
2. Vet searches specialist directory
3. Referral created with medical records
4. Referral documents attached
5. Referral sent to specialist
6. Specialist receives notification
7. Specialist reviews and schedules
8. Patient visits specialist
9. Specialist sends report back
10. Referring vet receives report

---

### 12. Staff Journey (`test_staff_journey.py`)

**Purpose**: Validate staff management workflow

| Test Class | Simulations |
|------------|-------------|
| `TestStaffShiftJourney` | Complete shift journey |
| `TestStaffScheduleConflicts` | Overlapping shifts detected |
| | Time entry without shift |
| | Late arrival flagged |
| `TestStaffTaskManagement` | Task priority ordering |
| | Task linked to pet |
| | Task status transitions |
| | Overdue tasks identified |

**Complete Journey Simulation**:
1. Staff clocks in for shift
2. Staff views assigned tasks
3. Staff starts highest priority task
4. Staff completes task, updates status
5. Staff takes break (time tracked)
6. Staff continues with next task
7. Staff clocks out at end of shift
8. Manager reviews time entries
9. Payroll data generated

---

### 13. Staff Workflows (`test_staff_workflows.py`)

**Purpose**: Validate CRM and customer management

| Test Class | Simulations |
|------------|-------------|
| `TestCustomerNotes` | Staff can create customer note |
| | Staff can pin important note |
| | Staff can create private note |
| `TestInteractionLogging` | Staff can record phone call |
| | Staff can record WhatsApp message |
| | Staff can record in-person visit |
| | Interaction history ordered by date |
| `TestCustomerTagging` | Staff can add tag to customer |
| | Staff can remove tag from customer |
| | Staff can create new tag |
| | Multiple tags on customer |
| | Filter customers by tag |
| `TestCustomerHistory` | Staff can view customer visits |
| | Staff can view customer orders |
| | Staff can view customer spending |
| `TestFollowUpReminders` | Interaction with follow-up |
| | Query pending follow-ups |
| `TestAPIStaffWorkflows` | Staff API add note |
| | Staff API log interaction |
| | Staff API add tag |
| | Staff API view customer history |
| `TestCRMAnalytics` | Customer lifetime value tracking |
| | Referral tracking |
| | Customer segments |

---

### 14. Store Order Journey (`test_store_order_journey.py`)

**Purpose**: Validate e-commerce order flow

| Test Class | Simulations |
|------------|-------------|
| `TestStoreOrderJourney` | Complete delivery order journey |
| | Complete pickup order journey |
| `TestOrderEdgeCases` | Order with out of stock item |
| | Order cancellation restores stock |

**Complete Journey Simulation**:
1. Customer browses store
2. Customer adds items to cart
3. Customer proceeds to checkout
4. Customer selects delivery or pickup
5. Customer enters payment
6. Order created with line items
7. Invoice generated
8. Payment processed
9. Order confirmed
10. If delivery → delivery record created
11. If pickup → pickup notification sent

---

### 15. Vaccination Journey (`test_vaccination_journey.py`)

**Purpose**: Validate vaccination workflow

| Test Class | Simulations |
|------------|-------------|
| `TestVaccinationReminderJourney` | Complete vaccination reminder journey |
| `TestVaccinationOverdueScenarios` | Overdue vaccination alert |
| | Multiple vaccines due |
| | Puppy vaccination schedule |
| `TestVaccinationWeightTracking` | Weight recorded during vaccination |

**Complete Journey Simulation**:
1. Pet vaccination record created
2. Next due date calculated
3. System checks for upcoming vaccinations
4. Reminder notification sent (7 days before)
5. Customer receives WhatsApp/email reminder
6. Customer books vaccination appointment
7. Vet administers vaccination
8. Vaccination record updated
9. Next due date set
10. Vaccination certificate generated

---

## Browser Tests

Browser tests validate actual UI rendering using Playwright.

### Test Files Overview

| File | Purpose | Tests |
|------|---------|-------|
| `test_admin_users.py` | Admin user management | 25 |
| `test_appointment_booking.py` | Appointment booking UI | 28 |
| `test_authentication.py` | Login, register, profile | 20 |
| `test_billing.py` | Invoice viewing | 15 |
| `test_checkout_flow.py` | Store checkout | 12 |
| `test_clinical_notes.py` | Clinical notes UI (admin) | 8 |
| `test_driver_dashboard.py` | Driver mobile UI | 10 |
| `test_emergency.py` | Emergency (admin only*) | 8 |
| `test_inventory.py` | Inventory (admin only*) | 12 |
| `test_loyalty.py` | Loyalty (admin only*) | 10 |
| `test_orders.py` | Order history | 10 |
| `test_pet_management.py` | Pet profile UI | 15 |
| `test_pharmacy.py` | Pharmacy info | 8 |
| `test_referrals.py` | Referrals (admin only*) | 8 |
| `test_staff_management.py` | Staff pages (admin only*) | 8 |
| `test_vaccination_reminders.py` | Vaccination UI | 10 |

*Note: Admin only until customer URLs are implemented (T-074 through T-078)

---

## Test Fixtures

### Authentication Fixtures

```python
@pytest.fixture
def owner_user(db):
    """Regular customer user."""
    return User.objects.create_user(...)

@pytest.fixture
def staff_user(db):
    """Staff member with is_staff=True."""
    return User.objects.create_user(..., is_staff=True)

@pytest.fixture
def admin_user(db):
    """Superuser for admin access."""
    return User.objects.create_superuser(...)
```

### Page Fixtures

```python
@pytest.fixture
def authenticated_page(page, live_server, owner_user):
    """Browser page with logged-in customer."""
    page.goto(f'{live_server.url}/accounts/login/')
    page.fill('input[name="username"]', owner_user.email)
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    return page

@pytest.fixture
def admin_page(page, live_server, admin_user):
    """Browser page with logged-in admin."""
    # Similar to authenticated_page with admin credentials
```

### Data Fixtures

```python
@pytest.fixture
def pet_with_owner(db, owner_user):
    """Pet linked to customer."""
    return Pet.objects.create(owner=owner_user, ...)

@pytest.fixture
def appointment_with_pet(db, pet_with_owner, staff_user):
    """Appointment with associated pet."""
    return Appointment.objects.create(pet=pet_with_owner, ...)

@pytest.fixture
def invoice_for_user(db, owner_user):
    """Invoice for customer."""
    return Invoice.objects.create(customer=owner_user, ...)
```

---

## Writing New Tests

### Journey Test Template

```python
@pytest.mark.django_db(transaction=True)
class TestNewJourney:
    """Test [feature] complete journey."""

    def test_complete_journey(self, db, owner_user, staff_user):
        """Simulate complete [feature] workflow."""
        # Step 1: Setup
        # ...

        # Step 2: Action
        # ...

        # Step 3: Verify
        assert result.status == 'completed'
```

### Browser Test Template

```python
@pytest.mark.browser
class TestNewFeature:
    """Test [feature] browser functionality."""

    def test_page_loads(self, authenticated_page, live_server):
        """Verify page loads correctly."""
        page = authenticated_page
        page.goto(f"{live_server.url}/feature/")

        # ALWAYS verify content, not just visibility
        expect(page.locator('h1')).to_contain_text('Expected Title')
        expect(page.locator('h1')).not_to_contain_text('Not Found')

    def test_form_submits(self, authenticated_page, live_server):
        """Verify form submission works."""
        page = authenticated_page
        page.goto(f"{live_server.url}/feature/create/")
        page.fill('input[name="field"]', 'value')
        page.click('button[type="submit"]')
        expect(page.locator('.success')).to_be_visible()
```

### Common Assertions

```python
# Page content
expect(page.locator('h1')).to_contain_text('Title')
expect(page.locator('.message')).to_be_visible()
expect(page.locator('form')).to_be_visible()

# Form fields
expect(page.locator('input[name="email"]')).to_have_value('test@example.com')
expect(page.locator('select[name="type"]')).to_have_value('option1')

# Navigation
expect(page).to_have_url(re.compile(r'/success/'))
expect(page).to_have_title(re.compile(r'Success'))

# NOT assertions (critical for QA)
expect(page.locator('h1')).not_to_contain_text('Not Found')
expect(page.locator('.error')).not_to_be_visible()
```

---

## QA Process

### 1. Test Coverage Check

Before marking any feature complete:
```bash
pytest --cov=apps/[app] --cov-report=term-missing
```

Target: >95% coverage

### 2. Browser Test Validation

Every customer-facing URL must have:
- Page load test
- Content verification (not just `body.to_be_visible()`)
- 404 detection (`not_to_contain_text('Not Found')`)

### 3. Journey Test Validation

Every user workflow must have:
- Happy path test (complete flow)
- Edge case tests (failures, cancellations)
- State transition tests (status changes)

### 4. QA Discovery Pattern

When browser tests fail due to 404:
1. Document in `planning/issues/`
2. Create task for missing URLs
3. Update tests to verify admin (temporary)
4. Implement customer URLs
5. Update tests to verify customer URLs

---

## Related Documents

- `planning/EPOCH_TESTING_FRAMEWORK.md` - Testing epoch overview
- `planning/STORY_TO_TASK_CHECKLIST.md` - Ensuring views built with models
- `planning/issues/MISSING_CUSTOMER_URLS.md` - QA discoveries
- `tests/e2e/conftest.py` - E2E fixtures
- `tests/e2e/browser/conftest.py` - Browser fixtures
