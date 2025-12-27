# T-086: Shift Management CRUD Operations

> **REQUIRED READING:** Before implementation, review [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-008 Practice Management
**Priority**: Medium
**Status**: Pending
**Estimate**: 3 hours
**Dependencies**: T-085 (Staff CRUD)

---

## AI Coding Brief

**Role**: Backend/Frontend Developer
**Objective**: Add CRUD operations for staff work shifts
**User Request**: Work schedule management for staff

### Context

Currently:
- Shifts can only be listed (shift_list view exists)
- Schedule view shows weekly calendar (read-only)
- No create/edit/delete for shifts
- Shift model exists with staff, date, start_time, end_time fields

### Constraints

**Allowed File Paths**:
- `apps/practice/forms.py` (MODIFY - add ShiftForm)
- `apps/practice/views.py` (MODIFY)
- `apps/practice/urls.py` (MODIFY)
- `templates/practice/shift_form.html` (CREATE)
- `templates/practice/shift_detail.html` (CREATE)
- `templates/practice/shift_confirm_delete.html` (CREATE)
- `apps/practice/tests/test_shift_crud.py` (CREATE)

**Forbidden Paths**: None

### Deliverables

- [ ] `ShiftForm` - Create/edit shifts
- [ ] `shift_create` view
- [ ] `shift_detail` view
- [ ] `shift_edit` view
- [ ] `shift_delete` view
- [ ] Templates for all views
- [ ] URL routes added

### URL Routes

```python
path('shifts/add/', views.shift_create, name='shift_create'),
path('shifts/<int:pk>/', views.shift_detail, name='shift_detail'),
path('shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'),
path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),
```

### Form Fields

```python
class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['staff', 'date', 'start_time', 'end_time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
```

### Definition of Done

- [ ] ShiftForm added to forms.py
- [ ] All views created
- [ ] URLs added
- [ ] Templates created with proper styling
- [ ] Validation: end_time > start_time
- [ ] Validation: no overlapping shifts for same staff
- [ ] Tests written FIRST (>95% coverage)
- [ ] All tests passing

### Test Cases

```python
class ShiftCRUDTests(TestCase):
    """Test shift CRUD operations."""

    def test_shift_create_page_loads(self):
        pass

    def test_shift_create_valid_form(self):
        pass

    def test_shift_create_end_before_start(self):
        """End time before start time shows error."""
        pass

    def test_shift_create_overlapping(self):
        """Overlapping shift for same staff shows error."""
        pass

    def test_shift_detail_page_loads(self):
        pass

    def test_shift_edit_valid_form(self):
        pass

    def test_shift_delete_confirmation(self):
        pass
```

### Notes

- Add "Add Shift" button to shift_list.html and schedule.html
- Consider bulk shift creation (recurring shifts) as future enhancement
- Link from schedule view to shift detail/edit
