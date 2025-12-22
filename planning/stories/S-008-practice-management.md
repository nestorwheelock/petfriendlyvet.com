# S-008: Practice Management

> **REQUIRED READING:** Before implementation, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

**Story Type:** User Story
**Priority:** Low
**Epoch:** 6
**Status:** PENDING

## User Story

**As a** clinic owner
**I want to** manage staff schedules and internal operations
**So that** the clinic runs efficiently

**As a** regulatory compliance officer
**I want to** access audit logs and generate compliance reports
**So that** the clinic meets legal requirements

## Acceptance Criteria

### Staff Management
- [ ] Staff profiles with roles and permissions
- [ ] Work schedule management
- [ ] Time-off requests and approvals
- [ ] Staff availability reflected in booking

### Internal Clinical Notes
- [ ] Notes visible only to clinical staff
- [ ] Linked to visits and pets
- [ ] Searchable and filterable
- [ ] Templates for common note types

### Inventory Management
- [ ] Stock levels tracked
- [ ] Low stock alerts
- [ ] Reorder suggestions
- [ ] Expiry date tracking
- [ ] Usage linked to visits/sales

### Compliance & Auditing
- [ ] Immutable audit log for all actions
- [ ] Exportable records for inspections
- [ ] Retention policies configurable
- [ ] GDPR data export/deletion support

### Reporting
- [ ] Daily/weekly/monthly summaries
- [ ] Revenue reports
- [ ] Service utilization reports
- [ ] Inventory reports
- [ ] Staff productivity (optional)

## Technical Requirements

### Models

```python
# Staff Management
class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # veterinarian, assistant, receptionist, admin
    hire_date = models.DateField()
    license_number = models.CharField(max_length=50, blank=True)
    specializations = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)


class WorkSchedule(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)


class TimeOffRequest(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='pending')
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


# Audit Logging
class AuditLog(models.Model):
    """Immutable audit log for compliance"""
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # create, update, delete, view
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)  # Before/after for updates
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        # Prevent deletion/modification
        managed = True


# Inventory (extension of store.Product)
class InventoryMovement(models.Model):
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20)  # sale, restock, adjustment, expired
    quantity = models.IntegerField()  # Positive for in, negative for out
    reference = models.CharField(max_length=100, blank=True)  # Order ID, visit ID, etc.
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class InventoryAlert(models.Model):
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20)  # low_stock, expiring, out_of_stock
    threshold = models.IntegerField(null=True)
    expiry_date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    acknowledged_at = models.DateTimeField(null=True)


# Compliance
class DataRetentionPolicy(models.Model):
    model_name = models.CharField(max_length=100)
    retention_days = models.IntegerField()
    action = models.CharField(max_length=20)  # delete, anonymize, archive
    is_active = models.BooleanField(default=True)


class DataExportRequest(models.Model):
    """GDPR data export/deletion requests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20)  # export, delete
    status = models.CharField(max_length=20, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    export_file = models.FileField(upload_to='exports/', null=True)
```

### AI Tools (Epoch 6)

```python
PRACTICE_MANAGEMENT_TOOLS = [
    {
        "name": "get_staff_schedule",
        "description": "Get staff work schedule for a date",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
                "staff_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_inventory_status",
        "description": "Get current inventory status and alerts",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "show_alerts_only": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "record_inventory_adjustment",
        "description": "Record an inventory adjustment",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "integer"},
                "reason": {"type": "string"}
            },
            "required": ["product_id", "quantity", "reason"]
        }
    },
    {
        "name": "get_audit_log",
        "description": "Search audit logs",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "action": {"type": "string"},
                "model": {"type": "string"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            }
        }
    },
    {
        "name": "generate_compliance_report",
        "description": "Generate compliance/regulatory reports",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["audit_summary", "data_access", "medical_records", "inventory"]
                },
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "format": {"type": "string", "enum": ["pdf", "csv", "json"]}
            },
            "required": ["report_type"]
        }
    },
    {
        "name": "get_daily_summary",
        "description": "Get daily business summary",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"}
            }
        }
    }
]
```

## Example AI Conversations

### Daily Summary
```
Dr. Pablo: How did we do today?
AI: Here's today's summary (December 20, 2025):

    📊 **Daily Summary**

    💰 **Revenue:** $8,450 MXN
    • Services: $4,200 MXN (6 appointments)
    • Products: $4,250 MXN (8 orders)

    📅 **Appointments:**
    • Completed: 6 of 7 (1 no-show)
    • Services: 3 checkups, 2 vaccinations, 1 surgery

    🛒 **Top Products Sold:**
    • Royal Canin (3 bags)
    • Frontline Plus (4 units)
    • Dog toys (5 items)

    ⚠️ **Alerts:**
    • Low stock: Frontline Plus (2 remaining)
    • Expiring soon: Rabies vaccine batch (expires Jan 15)

    Compared to last Friday: Revenue up 12%
```

### Inventory Alert
```
AI: ⚠️ Inventory Alert

    The following items need attention:

    🔴 **Out of Stock:**
    • Hills Prescription Diet k/d

    🟡 **Low Stock (reorder recommended):**
    • Frontline Plus Large Dog (2 left, threshold: 5)
    • Royal Canin Gastrointestinal (3 left, threshold: 5)

    🟠 **Expiring Within 30 Days:**
    • Rabies Vaccine Batch #R2024-15 (8 doses, expires Jan 15)
    • Ketamine Batch #K2024-08 (expires Jan 20)

    Would you like me to create a reorder list?
```

## Definition of Done

- [ ] Staff schedules manageable
- [ ] Time-off requests working
- [ ] Audit logging capturing all actions
- [ ] Audit logs immutable and exportable
- [ ] Inventory movements tracked
- [ ] Low stock and expiry alerts working
- [ ] Daily summary report available
- [ ] GDPR export/delete implemented
- [ ] AI can query all practice data
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- All previous epochs (S-001 through S-007)
- Full system operational

## Notes

- Audit logs must be truly immutable (consider append-only table)
- GDPR compliance important for EU tourists
- Integration with OkVet.co TBD (may need research)
- Consider separate compliance database for long-term retention

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.
