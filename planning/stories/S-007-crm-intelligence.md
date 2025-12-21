# S-007: Owner CRM + Intelligence

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 5
**Status:** PENDING

## User Story

**As a** clinic staff member
**I want to** have detailed profiles of pet owners with their history and preferences
**So that** I can provide personalized service and targeted marketing

**As a** business owner
**I want to** understand customer behavior and trends
**So that** I can make informed decisions about services and inventory

## Acceptance Criteria

### Owner Profiles
- [ ] Complete contact information (phone, email, address)
- [ ] Communication preferences and history
- [ ] All pets linked to owner
- [ ] Appointment history
- [ ] Purchase history
- [ ] Total lifetime value calculated
- [ ] Notes and tags for segmentation

### Customer Intelligence
- [ ] Purchase frequency analysis
- [ ] Preferred products tracking
- [ ] Visit patterns (seasonal, regular, emergency)
- [ ] Response rates to communications
- [ ] Churn risk indicators

### Marketing Automation
- [ ] Segment customers by criteria
- [ ] Automated birthday/anniversary messages
- [ ] Lapsed customer re-engagement
- [ ] New product announcements to relevant segments
- [ ] Loyalty program tracking

### AI Capabilities
- [ ] AI can search and retrieve owner profiles
- [ ] AI can add notes and tags
- [ ] AI can identify high-value customers
- [ ] AI can suggest marketing actions
- [ ] AI can generate reports

## Technical Requirements

### Package: django-crm-lite

```python
# models.py

class OwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Contact info
    phone_primary = models.CharField(max_length=20, blank=True)
    phone_secondary = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=10, default='es')

    # Communication preferences
    contact_preference = models.CharField(max_length=20, default='whatsapp')
    marketing_opt_in = models.BooleanField(default=True)
    reminder_preference = models.CharField(max_length=20, default='24h')

    # Segmentation
    customer_type = models.CharField(max_length=50, blank=True)  # regular, vip, new, lapsed
    acquisition_source = models.CharField(max_length=100, blank=True)
    referral_source = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    # Social
    instagram_handle = models.CharField(max_length=100, blank=True)
    facebook_url = models.URLField(blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OwnerTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    description = models.TextField(blank=True)


class OwnerProfileTag(models.Model):
    profile = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(OwnerTag, on_delete=models.CASCADE)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)


class OwnerNote(models.Model):
    profile = models.ForeignKey(OwnerProfile, on_delete=models.CASCADE, related_name='notes_history')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    is_internal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerMetrics(models.Model):
    """Calculated metrics, updated periodically"""
    profile = models.OneToOneField(OwnerProfile, on_delete=models.CASCADE)

    # Financial
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_count = models.IntegerField(default=0)

    # Engagement
    total_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    no_show_count = models.IntegerField(default=0)
    last_visit_date = models.DateField(null=True)
    last_purchase_date = models.DateField(null=True)

    # Communication
    messages_sent = models.IntegerField(default=0)
    messages_responded = models.IntegerField(default=0)
    response_rate = models.FloatField(default=0)

    # Derived
    days_since_last_visit = models.IntegerField(default=0)
    churn_risk_score = models.FloatField(default=0)  # 0-1, higher = more likely to churn
    lifetime_value_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)


class MarketingCampaign(models.Model):
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=50)  # email, sms, whatsapp
    status = models.CharField(max_length=20, default='draft')

    # Targeting
    target_segment = models.JSONField(default=dict)  # Filters for who receives
    target_count = models.IntegerField(default=0)

    # Content
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()

    # Scheduling
    scheduled_for = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)

    # Results
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoyaltyProgram(models.Model):
    profile = models.OneToOneField(OwnerProfile, on_delete=models.CASCADE)
    points_balance = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, default='bronze')  # bronze, silver, gold, platinum
    points_earned_total = models.IntegerField(default=0)
    points_redeemed_total = models.IntegerField(default=0)


class LoyaltyTransaction(models.Model):
    loyalty = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20)  # earn, redeem, expire
    points = models.IntegerField()
    description = models.CharField(max_length=200)
    related_order = models.ForeignKey('store.Order', null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools (Epoch 5)

```python
CRM_TOOLS = [
    {
        "name": "get_owner_profile",
        "description": "Get detailed profile of a pet owner",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "search_owners",
        "description": "Search for owners by name, phone, email, or pet name",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "filters": {"type": "object"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_owner_note",
        "description": "Add a note to an owner's profile",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "note": {"type": "string"},
                "is_internal": {"type": "boolean", "default": True}
            },
            "required": ["user_id", "note"]
        }
    },
    {
        "name": "tag_owner",
        "description": "Add or remove tags from an owner profile",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "add_tags": {"type": "array", "items": {"type": "string"}},
                "remove_tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_customer_insights",
        "description": "Get analytics and insights about customers",
        "parameters": {
            "type": "object",
            "properties": {
                "insight_type": {
                    "type": "string",
                    "enum": ["top_customers", "at_risk", "new_customers", "lapsed", "high_value"]
                },
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["insight_type"]
        }
    },
    {
        "name": "get_segment",
        "description": "Get list of customers matching criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "properties": {
                        "min_spent": {"type": "number"},
                        "days_since_visit": {"type": "integer"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "pet_species": {"type": "string"}
                    }
                }
            }
        }
    },
    {
        "name": "generate_report",
        "description": "Generate business reports",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["revenue", "appointments", "products", "customers", "retention"]
                },
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            },
            "required": ["report_type"]
        }
    }
]
```

## Example AI Conversations

### Customer Lookup
```
Dr. Pablo: Tell me about María García
AI: Here's María García's profile:

    👤 **María García**
    📱 998-123-4567 (WhatsApp preferred)
    📧 maria.garcia@email.com
    📍 Calle Coral 45, Puerto Morelos

    🐕 **Pets:** Max (Poodle, 5 years)

    💰 **Customer Value:**
    • Total Spent: $12,450 MXN
    • 8 orders, avg $1,556 MXN
    • 15 appointments (0 no-shows)
    • Customer since: March 2023

    📊 **Recent Activity:**
    • Last visit: Nov 15, 2025 (Max annual checkup)
    • Last purchase: Nov 15, 2025 (Royal Canin)

    🏷️ Tags: VIP, Regular, Dog Owner

    Would you like to see more details?
```

### At-Risk Customers
```
Dr. Pablo: Who haven't we seen in a while?
AI: Here are customers at risk of churning:

    ⚠️ **At-Risk Customers** (no visit in 90+ days)

    1. **Carlos Mendez** - Last visit 120 days ago
       Pets: Buddy (Labrador)
       Spent: $8,200 MXN lifetime
       → Vaccination due in 2 weeks

    2. **Sarah Johnson** - Last visit 95 days ago
       Pets: Mittens (Cat), Whiskers (Cat)
       Spent: $5,400 MXN lifetime
       → Usually buys food monthly, no order in 45 days

    3. **Roberto Sánchez** - Last visit 92 days ago
       Pets: Thor (German Shepherd)
       Spent: $15,800 MXN lifetime
       → VIP customer, should follow up

    Would you like me to send re-engagement messages to any of them?
```

## Definition of Done

- [ ] Owner profiles with complete information
- [ ] Customer metrics calculated and updated
- [ ] Tags and notes system working
- [ ] Purchase and visit history aggregated
- [ ] Churn risk scoring implemented
- [ ] AI can search and retrieve profiles
- [ ] AI can generate business reports
- [ ] Marketing campaigns can be created
- [ ] Loyalty points tracking (basic)
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation + AI Core
- S-003: Pet Profiles
- S-004: Appointment Booking
- S-005: E-Commerce Store
- S-006: Omnichannel Communications

## Notes

- Metrics should be recalculated nightly via cron job
- Consider GDPR/privacy compliance for marketing
- Social media enrichment could use APIs or manual entry
- Loyalty program is basic - could expand in future
