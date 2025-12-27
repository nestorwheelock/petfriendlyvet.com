# S-083: Practice-HR Integration

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** High
**Epoch:** 4
**Status:** IN PROGRESS

## User Story

**As an** administrator
**I want** staff profiles linked to HR employees
**So that** veterinary permissions and HR data are unified

**As a** staff member
**I want** a single source of truth for my employee data
**So that** I don't have duplicate profiles in different systems

**As a** practice manager
**I want** time tracking and scheduling consolidated in HR
**So that** I have one place to manage workforce operations

## Acceptance Criteria

### StaffProfile ↔ Employee Link
- [x] StaffProfile has optional FK to Employee
- [x] Can link existing StaffProfile to Employee
- [x] StaffProfile keeps veterinary-specific fields (DEA, license)
- [x] Employee keeps generic HR fields (hire_date, department)
- [ ] Admin UI to link StaffProfile to Employee

### Data Migration
- [ ] Practice Shift data migrated to HR Shift
- [ ] Practice TimeEntry data migrated to HR TimeEntry
- [ ] Data integrity verified after migration
- [ ] Rollback plan documented

### UI Updates
- [ ] Practice sidebar updated (remove migrated items)
- [ ] Links from Practice to HR for schedule/time tracking
- [ ] Old Practice time tracking URLs redirect to HR

### Deprecation
- [ ] Practice Shift model deprecated
- [ ] Practice TimeEntry model deprecated
- [ ] Deprecation warnings added to old views
- [ ] Old models kept for rollback safety

## Technical Implementation

### Schema Changes

**StaffProfile (apps/practice/models.py):**
```python
class StaffProfile(models.Model):
    # Existing veterinary-specific fields
    user = models.OneToOneField(User)
    role = models.CharField(...)
    dea_number = models.CharField(...)
    license_number = models.CharField(...)
    can_prescribe = models.BooleanField(...)

    # NEW: Link to HR Employee
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_profiles',
        help_text='Link to HR Employee record for unified tracking'
    )
```

**TimeEntry (apps/hr/models.py):**
```python
class TimeEntry(models.Model):
    employee = models.ForeignKey(Employee, ...)
    task = models.ForeignKey('practice.Task', ...)  # Link to tasks
```

### Migration Strategy

**Phase 1: Schema Updates (COMPLETED)**
1. Add employee FK to StaffProfile
2. Add task FK to HR TimeEntry
3. Run migrations

**Phase 2: Data Migration (PENDING)**
1. Create data migration script
2. For each Practice Shift:
   - Find matching Employee via User
   - Create HR Shift with same data
3. For each Practice TimeEntry:
   - Find matching Employee via StaffProfile.user
   - Create HR TimeEntry with same data
4. Verify row counts match
5. Verify data integrity

**Phase 3: UI Updates (PENDING)**
1. Update Practice sidebar template
2. Remove: Schedule & Shifts, Time Tracking links
3. Add: "HR & Time Tracking" link to HR module
4. Update Practice URLs to redirect to HR

**Phase 4: Deprecation (FUTURE)**
1. Add deprecation warnings to Practice Shift/TimeEntry
2. Keep models for 2 releases for rollback
3. Remove deprecated models in future release

## Data Migration Script

```python
# apps/hr/migrations/0004_migrate_practice_data.py

def migrate_shifts(apps, schema_editor):
    PracticeShift = apps.get_model('practice', 'Shift')
    HRShift = apps.get_model('hr', 'Shift')
    Employee = apps.get_model('hr', 'Employee')

    for ps in PracticeShift.objects.all():
        # Find Employee via StaffProfile → User
        try:
            employee = Employee.objects.get(user=ps.staff.user)
        except Employee.DoesNotExist:
            continue

        HRShift.objects.create(
            employee=employee,
            date=ps.date,
            start_time=ps.start_time,
            end_time=ps.end_time,
            notes=ps.notes,
            status='scheduled',
        )

def migrate_time_entries(apps, schema_editor):
    PracticeTimeEntry = apps.get_model('practice', 'TimeEntry')
    HRTimeEntry = apps.get_model('hr', 'TimeEntry')
    Employee = apps.get_model('hr', 'Employee')

    for pte in PracticeTimeEntry.objects.all():
        try:
            employee = Employee.objects.get(user=pte.staff.user)
        except Employee.DoesNotExist:
            continue

        HRTimeEntry.objects.create(
            employee=employee,
            date=pte.date,
            clock_in=pte.clock_in,
            clock_out=pte.clock_out,
            break_minutes=pte.break_minutes,
            notes=pte.notes,
            is_approved=pte.is_approved,
            approved_by=pte.approved_by,
        )
```

## Related Tasks

- T-097f: Practice → HR Integration

## GitHub Issues

- #12: T-097f Consolidate Practice time tracking and shifts into HR module

## Definition of Done

- [x] StaffProfile linked to Employee (optional FK)
- [ ] Practice Shift data migrated to HR Shift
- [ ] Practice TimeEntry data migrated to HR TimeEntry
- [ ] Practice sidebar updated (remove migrated items)
- [ ] No data loss during migration
- [ ] All tests pass
- [ ] Rollback documented

## Dependencies

- T-097a: HR Module Foundation (COMPLETED)
- T-097b: Employee Model (COMPLETED)
- T-097c: Time Tracking in HR (COMPLETED)
- T-097d: Shift Model (COMPLETED)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Keep source models, verify counts, backup first |
| User confusion with new navigation | Clear redirect messages, documentation |
| Incomplete Employee records | Log unlinked records, provide admin tool to link |

## Notes

- StaffProfile keeps veterinary-specific permissions (DEA, license, prescribing)
- Employee keeps generic HR data (hire_date, department, position)
- Time tracking is now centralized in HR module
- Task time tracking links to practice.Task for project costing
