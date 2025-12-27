# S-100: Unified People Module Architecture

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

> **STATUS: PLANNING** - Architectural decision needed

**Story Type:** Architecture Refactor
**Priority:** High
**Impact:** Multiple modules (HR, Delivery, Practice, Accounts)

## Core Insight

> "One module that's just for people. Others link to people and attach domain-specific objects."

Instead of scattering person-related models across apps, create a **single `people` module** that owns the "person" concept. Other modules add their domain-specific relationships.

---

## The Problem

We have fragmented "person" concepts across modules:

| Model | Module | Purpose |
|-------|--------|---------|
| `User` | accounts | Django auth - identity |
| `CustomerProfile` | accounts | Pet owner info (if exists) |
| `Employee` | hr | HR record (hire date, department, position) |
| `StaffProfile` | practice | Veterinary credentials (license, DEA) |
| `DeliveryDriver` | delivery | Driver capability (zones, vehicle, rates) |

**Problems:**
1. Same person can't easily have multiple roles
2. Juan is a customer AND a driver - need two separate records?
3. DeliveryDriver duplicates HR concepts (contractor info, payment rates)
4. No single view of "all people connected to this clinic"

---

## Real-World Scenarios

### Scenario 1: Part-Time Driver Who's Also a Customer
- Juan brings his dog Luna for checkups (Customer)
- Juan also delivers pet food on weekends (Driver)
- Currently: Two separate records with no connection

### Scenario 2: Vet Tech Who Does Deliveries
- Maria is a full-time vet tech (Employee + StaffProfile)
- Maria sometimes does emergency deliveries (Driver)
- Currently: Would need Employee + StaffProfile + DeliveryDriver

### Scenario 3: Contractor with Multiple Roles
- Carlos is a freelance groomer (Contractor via HR)
- Carlos also refers customers (Referrer)
- Carlos brings his own pets too (Customer)
- Currently: Fragmented across modules

---

## Proposed Architecture

### Core Principle
**User is the Person. Roles are capabilities attached to that person.**

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
│  (The Person - single source of identity)                   │
│  - email, name, phone, auth                                 │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ CustomerProfile │  │    Employee     │  │    Referrer     │
│ (Pet Owner)     │  │   (HR Record)   │  │ (Referral Code) │
│ - pets          │  │ - hire_date     │  │ - referral_code │
│ - billing       │  │ - department    │  │ - commission    │
│ - preferences   │  │ - position      │  │ - stats         │
└─────────────────┘  │ - employment_   │  └─────────────────┘
                     │   type          │
                     │ - contractor    │
                     │   info          │
                     └────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ VetCredent- │  │   Driver    │  │   Other     │
     │ ials        │  │ Capability  │  │ Capability  │
     │ (License,   │  │ (Zones,     │  │ (Future)    │
     │  DEA, etc)  │  │  Vehicle)   │  │             │
     └─────────────┘  └─────────────┘  └─────────────┘
```

### Key Changes

#### 1. User remains the Person
```python
# accounts/models.py - No change needed
class User(AbstractUser):
    # The person's identity
    email = ...
    first_name = ...
    phone = ...
```

#### 2. Employee is the HR Record (for ALL workers)
```python
# hr/models.py
class Employee(models.Model):
    """HR record for anyone who works for/with the clinic."""

    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contractor', 'Contractor'),
        ('freelance', 'Freelance'),
        ('volunteer', 'Volunteer'),
        ('intern', 'Intern'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)

    # HR basics
    department = models.ForeignKey(Department, ...)
    position = models.ForeignKey(Position, ...)
    employment_type = models.CharField(choices=EMPLOYMENT_TYPES)
    hire_date = models.DateField()

    # Contractor-specific (moved from DeliveryDriver)
    is_contractor = models.BooleanField(default=False)
    rfc = models.CharField(max_length=13, blank=True)  # Tax ID
    curp = models.CharField(max_length=18, blank=True)  # Personal ID
    contract_signed = models.BooleanField(default=False)

    # Status
    status = models.CharField(...)  # active, on_leave, terminated
```

#### 3. VetCredentials (renamed from StaffProfile)
```python
# practice/models.py
class VetCredentials(models.Model):
    """Veterinary-specific credentials for clinical staff."""

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    # Links to Employee, not User

    license_number = models.CharField(...)
    license_state = models.CharField(...)
    dea_number = models.CharField(...)

    # Clinical permissions
    can_prescribe = models.BooleanField(default=False)
    can_perform_surgery = models.BooleanField(default=False)
```

#### 4. DriverCapability (replaces DeliveryDriver)
```python
# delivery/models.py
class DriverCapability(models.Model):
    """Delivery driver capability for an employee."""

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    # Links to Employee, not User

    # Driver-specific
    zones = models.ManyToManyField(DeliveryZone, blank=True)
    vehicle_type = models.CharField(...)
    license_plate = models.CharField(...)

    # Rates (for contractors - HR has base contractor info)
    rate_per_delivery = models.DecimalField(...)
    rate_per_km = models.DecimalField(...)

    # Operational
    is_available = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    max_deliveries_per_day = models.IntegerField(default=10)

    # Real-time location
    current_latitude = models.DecimalField(...)
    current_longitude = models.DecimalField(...)
    location_updated_at = models.DateTimeField(...)
```

#### 5. CustomerProfile stays as-is
```python
# accounts/models.py
class CustomerProfile(models.Model):
    """Pet owner profile."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Links to User directly (customers don't need to be Employees)

    preferred_location = ...
    billing_address = ...
    # etc.
```

---

## Migration Path

### Phase 1: Add DriverCapability
1. Create `DriverCapability` model linked to `Employee`
2. Keep `DeliveryDriver` temporarily for backwards compatibility
3. Add data migration to create `DriverCapability` from `DeliveryDriver` where Employee exists

### Phase 2: Ensure All Drivers are Employees
1. For each `DeliveryDriver` without an `Employee`, create one
2. Employment type = 'contractor' for independent drivers
3. Link their `DriverCapability` to the new `Employee`

### Phase 3: Update Views and APIs
1. Update `DriverRequiredMixin` to check `Employee.driver_capability`
2. Update delivery views to use new model
3. Update driver dashboard

### Phase 4: Rename StaffProfile to VetCredentials
1. Create `VetCredentials` model
2. Migrate data from `StaffProfile`
3. Link to `Employee` instead of `User`

### Phase 5: Deprecate Old Models
1. Remove `DeliveryDriver` model
2. Remove `StaffProfile` model (after full migration)

---

## Benefits

### 1. Single Person Record
- One User = One Person
- No duplicate people across modules

### 2. Multiple Roles
- Juan can be: Customer + Employee with DriverCapability
- Maria can be: Employee with VetCredentials + DriverCapability
- Carlos can be: Customer + Employee (contractor) + Referrer

### 3. Unified HR Management
- All workers (employees, contractors, freelancers) in HR
- Single place for: hire date, tax info, contracts, departments
- Driver-specific stuff is a "capability" on the Employee

### 4. Cleaner Queries
```python
# Find all drivers
drivers = Employee.objects.filter(
    driver_capability__isnull=False,
    status='active'
)

# Find employees who are also customers
employee_customers = Employee.objects.filter(
    user__customer_profile__isnull=False
)

# Find all vets who can also drive
vet_drivers = Employee.objects.filter(
    vet_credentials__isnull=False,
    driver_capability__isnull=False
)
```

### 5. Better Reporting
- "How many people work for us?" → Count Employees
- "How many are contractors?" → Filter by employment_type
- "Who can do deliveries?" → Filter by driver_capability

---

## Questions to Decide

1. **Should DriverCapability link to Employee or User?**
   - Employee: Cleaner, all workers must be in HR first
   - User: More flexible, but bypasses HR

   **Recommendation:** Link to Employee - drivers should be in HR

2. **Should VetCredentials require Employee?**
   - Yes: All clinical staff must be HR employees
   - No: Could have visiting vets who aren't employees

   **Recommendation:** Yes, but visiting vets can be employment_type='contractor'

3. **What about Referrers?**
   - Should link to User (customers can refer without being employees)
   - Separate from Employee system

4. **Backwards Compatibility?**
   - Keep old models during transition?
   - Or do a clean break?

   **Recommendation:** Phased migration with backwards compatibility

---

## Definition of Done

- [ ] DriverCapability model created, linked to Employee
- [ ] Migration to convert DeliveryDriver → DriverCapability
- [ ] All drivers have Employee records in HR
- [ ] VetCredentials model created (from StaffProfile)
- [ ] Views updated to use new models
- [ ] DeliveryDriver model deprecated/removed
- [ ] StaffProfile model deprecated/removed
- [ ] Tests updated and passing
- [ ] Documentation updated

---

## Related Stories

- S-097: HR Module (existing)
- S-102-S-107: Delivery Module (needs update)
- S-025b: Customer Referral Program (uses Referrer, not Employee)
