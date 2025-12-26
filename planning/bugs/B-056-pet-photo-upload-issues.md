# B-056: Pet Photo Upload and Management Issues

**Severity**: High
**Affected Component**: apps/pets
**Type**: Bug + Missing Feature (CRUD Gap)
**Status**: Open
**Correlates With Error Tracker**: **B-031** (Server Error on /en/pets/add/) - 5 occurrences

## Bug Description

Multiple issues with pet photo functionality:

1. **500 Error on Upload**: Server error when uploading pet photo during new pet creation
2. **Cannot Remove Photo**: No way to delete an existing pet photo
3. **Cannot Cancel Pending Upload**: No way to remove a selected photo from the form before submission
4. **Cannot Set Primary Photo**: If multiple photos allowed, no way to designate which is primary

## Steps to Reproduce

### Issue 1: 500 Error on Photo Upload
1. Log in as a customer
2. Navigate to /pets/add/
3. Fill in pet details
4. Select a photo file
5. Submit form
6. **Result**: 500 Server Error

### Issue 2: Cannot Remove Existing Photo
1. Log in as a customer
2. Navigate to /pets/{id}/edit/
3. View pet with existing photo
4. Attempt to remove the photo
5. **Result**: No remove/delete button exists

### Issue 3: Cannot Cancel Pending Upload
1. Log in as a customer
2. Navigate to /pets/add/ or /pets/{id}/edit/
3. Select a photo file
4. Change mind, want to submit without photo
5. **Result**: Cannot clear the file input, must refresh page

### Issue 4: Cannot Set Primary Photo
1. If Pet model supports multiple photos
2. Upload multiple photos
3. Attempt to set one as primary
4. **Result**: No UI to manage primary photo

## Expected Behavior

1. Photo upload should work without errors
2. Users should be able to remove existing photos
3. File input should have a "clear" button
4. If multiple photos: UI to set primary photo

## Technical Investigation Needed

Check the following for root cause of 500 error:
- `apps/pets/forms.py` - PetForm photo field handling
- `apps/pets/views.py` - PetCreateView file upload handling
- `apps/pets/models.py` - Pet.photo field configuration
- File upload settings in Django settings
- Media storage configuration
- Image processing library (Pillow) installation

## Proposed Solution

### Fix 500 Error (Priority 1)
1. Check if `MEDIA_ROOT` and `MEDIA_URL` configured correctly
2. Verify Pillow is installed for image processing
3. Check file size limits in settings
4. Add proper error handling in view
5. Test with various image formats (jpg, png, webp)

### Add Photo Removal (Priority 2)
1. Add "Remove Photo" checkbox to PetForm
2. Handle `photo-clear` in view to set photo to None
3. Add delete button in pet_edit.html template
4. Add confirmation before removal

### Add Clear Button for File Input (Priority 3)
1. Add JavaScript to clear file input
2. Or use Django ClearableFileInput widget
3. Show "No file selected" when cleared

### Add Primary Photo Support (Priority 4 - if applicable)
1. If Pet model has multiple photos (PetImage model)
2. Add "Set as Primary" button for each photo
3. Or radio button selection in edit form

## Files to Modify

- `apps/pets/forms.py` - Fix PetForm, add ClearableFileInput
- `apps/pets/views.py` - Fix file upload handling, add photo removal
- `apps/pets/models.py` - Verify photo field config
- `templates/pets/pet_form.html` - Add clear button, remove button
- `templates/pets/pet_edit.html` - Add photo management UI
- `config/settings/base.py` - Verify media settings
- `tests/test_pets_views.py` - Add upload tests

## Error Tracker Reference

```
B-031: [open] Server Error on /en/pets/add/ (count: 5)
B-049: [open] Server Error on /en/pets/{id}/edit/ (count: 1)
```

These are likely the same root cause - photo upload failing.

## Definition of Done

- [ ] 500 error on photo upload fixed
- [ ] Root cause documented
- [ ] Photo removal functionality added
- [ ] Clear button for file input added
- [ ] Form works with and without photo
- [ ] Error handling for invalid files (wrong format, too large)
- [ ] Tests with >95% coverage
- [ ] B-031 and B-049 marked resolved in error tracker
- [ ] Manual testing with various image types/sizes
