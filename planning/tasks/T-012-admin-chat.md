# T-012: Admin Chat Interface

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement admin/staff AI chat with elevated permissions
**Related Story**: S-002
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/, templates/admin/, apps/dashboard/
**Forbidden Paths**: None

### Deliverables
- [ ] Full-page admin chat interface
- [ ] Elevated tool access
- [ ] Tool execution visibility
- [ ] Conversation history browser
- [ ] Quick commands palette
- [ ] Data modification confirmations
- [ ] Audit trail display

### Implementation Details

#### Admin Chat Page
Full-page layout optimized for Dr. Pablo's mobile use:
- Large message area
- Easy-to-tap quick commands
- Recent conversations sidebar
- Tool execution logs

#### Quick Commands
```python
ADMIN_QUICK_COMMANDS = [
    {"label": "Today's appointments", "command": "show today's appointments"},
    {"label": "Low stock items", "command": "show products with low stock"},
    {"label": "Pending invoices", "command": "show unpaid invoices"},
    {"label": "Recent messages", "command": "show unread messages"},
    {"label": "Add new pet", "command": "I need to add a new pet"},
    {"label": "Search client", "command": "search for client"},
]
```

#### Tool Execution Visibility
For admin users, show what tools the AI is calling:
```html
<div class="tool-execution">
    <span class="tool-name">Calling: search_clients</span>
    <span class="tool-params">{"query": "García"}</span>
    <span class="tool-result">Found 3 clients</span>
</div>
```

#### Confirmation Dialogs
For data-modifying operations:
```python
REQUIRES_CONFIRMATION = [
    "create_appointment",
    "update_pet_record",
    "process_refund",
    "delete_*",
]
```

#### Conversation Browser
- List of all conversations (staff can see all, Dr. Pablo is admin)
- Filter by customer, date, topic
- Search within conversations
- Export conversation as PDF

### Permission Matrix
| Tool Category | Customer | Staff | Admin |
|---------------|----------|-------|-------|
| Info queries | ✓ | ✓ | ✓ |
| Pet records (own) | ✓ | ✓ | ✓ |
| Pet records (all) | ✗ | ✓ | ✓ |
| Appointments | Limited | ✓ | ✓ |
| Billing | Limited | ✓ | ✓ |
| Reports | ✗ | Limited | ✓ |
| System settings | ✗ | ✗ | ✓ |

### Test Cases
- [ ] Admin page loads
- [ ] Elevated tools available
- [ ] Tool execution visible
- [ ] Confirmation dialogs work
- [ ] Conversation history loads
- [ ] Search works
- [ ] Mobile layout optimized
- [ ] Audit trail recorded

### Definition of Done
- [ ] Admin chat fully functional
- [ ] Permission escalation works
- [ ] Tool visibility working
- [ ] Confirmations in place
- [ ] Mobile-optimized for Dr. Pablo
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-009: AI Service Layer
- T-010: Tool Calling Framework
- T-011: Customer Chat Widget
