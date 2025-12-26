# B-050: Missing Pet Delete/Archive Functionality

**Severity**: Medium
**Affected Component**: apps/pets
**Type**: Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: No direct correlation

## Bug Description

Users cannot delete or archive their pets from the customer portal. Once a pet is added, it remains visible in the pet list indefinitely with no way to remove it.

## Steps to Reproduce

1. Log in as a customer
2. Navigate to /pets/ or /portal/
3. View pet list
4. Attempt to delete or archive a pet
5. No delete/archive option exists

## Expected Behavior

Users should be able to:
- Soft-delete (archive) pets they no longer want to see
- Optionally hard-delete pets with confirmation
- View archived pets separately if needed

## Actual Behavior

No delete or archive functionality exists. Users are stuck with all pets visible forever, including deceased pets or pets they no longer own.

## Impact

- Users with deceased pets see constant reminders
- Users who transferred pet ownership cannot remove pets
- Pet list becomes cluttered over time
- Poor user experience

## Proposed Solution

1. Add `is_archived` boolean field to Pet model
2. Create `PetArchiveView` with confirmation
3. Add archive button to pet_detail.html and pet_list.html
4. Filter archived pets from default list view
5. Add "View Archived" option to see archived pets
6. Optionally add hard delete for archived pets only

## Files to Modify

- `apps/pets/models.py` - Add is_archived field
- `apps/pets/views.py` - Add PetArchiveView, PetDeleteView
- `apps/pets/urls.py` - Add archive/delete routes
- `templates/pets/pet_detail.html` - Add archive button
- `templates/pets/pet_list.html` - Filter archived, add button
- `tests/test_pets_views.py` - Add tests

## Definition of Done

- [ ] Pet model has is_archived field with migration
- [ ] PetArchiveView toggles archive status
- [ ] Archived pets hidden from default list
- [ ] "View Archived" shows only archived pets
- [ ] Archive/unarchive buttons in templates
- [ ] Tests with >95% coverage
- [ ] Manual testing complete
