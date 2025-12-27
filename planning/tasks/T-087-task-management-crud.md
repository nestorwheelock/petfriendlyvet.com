# T-087: Task Management CRUD Operations

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
**Objective**: Add create, edit, and delete operations for staff tasks
**User Request**: Task management for staff assignments

### Context

Currently:
- Tasks can be listed and viewed (task_list, task_detail exist)
- No create/edit/delete for tasks
- Task model has: title, description, priority, status, due_date, assigned_to, etc.

### Constraints

**Allowed File Paths**:
- `apps/practice/forms.py` (MODIFY - add TaskForm)
- `apps/practice/views.py` (MODIFY)
- `apps/practice/urls.py` (MODIFY)
- `templates/practice/task_form.html` (CREATE)
- `templates/practice/task_confirm_delete.html` (CREATE)
- `apps/practice/tests/test_task_crud.py` (CREATE)

**Forbidden Paths**: None

### Deliverables

- [ ] `TaskForm` - Create/edit tasks
- [ ] `task_create` view
- [ ] `task_edit` view
- [ ] `task_delete` view
- [ ] Templates for create/edit/delete
- [ ] URL routes added

### URL Routes

```python
path('tasks/add/', views.task_create, name='task_create'),
path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
```

### Form Fields

```python
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'status',
            'due_date', 'assigned_to', 'pet', 'appointment'
        ]
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
```

### Definition of Done

- [ ] TaskForm added to forms.py
- [ ] All views created
- [ ] URLs added
- [ ] Templates created with proper styling
- [ ] created_by set automatically to current user
- [ ] Tests written FIRST (>95% coverage)
- [ ] All tests passing

### Test Cases

```python
class TaskCRUDTests(TestCase):
    """Test task CRUD operations."""

    def test_task_create_page_loads(self):
        pass

    def test_task_create_valid_form(self):
        pass

    def test_task_create_sets_created_by(self):
        """created_by is set to current user."""
        pass

    def test_task_edit_valid_form(self):
        pass

    def test_task_delete_confirmation(self):
        pass

    def test_task_complete_action(self):
        """Quick action to mark task complete."""
        pass
```

### Notes

- Add "Add Task" button to task_list.html
- Consider quick actions: Mark Complete, Reassign
- Filter tasks by assignee on task_list
