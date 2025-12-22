# Module Interface Definitions - API Contracts

## Overview

This document defines the interfaces (API contracts) between the 9 pip-installable Django packages that make up the Pet-Friendly veterinary clinic system. Each module is designed to be reusable across different projects.

**Modules:**
1. django-ai-assistant
2. django-vet-clinic
3. django-appointments
4. django-simple-store
5. django-omnichannel
6. django-crm-lite
7. django-multilingual
8. django-competitive-intel
9. django-accounting

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Website   │  │  Admin UI   │  │   AI Chat   │  │  External APIs      │ │
│  │  (HTMX)     │  │  (Mobile)   │  │  Interface  │  │  (WhatsApp, etc.)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AI SERVICE LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    django-ai-assistant                               │   │
│  │  • Chat Interface  • Tool Calling  • Knowledge Base  • Translations  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOMAIN MODULES                                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ django-vet-     │  │ django-         │  │ django-simple-store         │ │
│  │ clinic          │  │ appointments    │  │                             │ │
│  │ • Pets          │  │ • Scheduling    │  │ • Products    • Inventory   │ │
│  │ • Medical       │  │ • Booking       │  │ • Cart        • Orders      │ │
│  │ • Vaccinations  │  │ • Reminders     │  │ • Checkout                  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ django-crm-     │  │ django-         │  │ django-accounting           │ │
│  │ lite            │  │ omnichannel     │  │                             │ │
│  │ • Customers     │  │ • Email         │  │ • GL          • AP/AR       │ │
│  │ • Loyalty       │  │ • SMS           │  │ • Reports     • Budget      │ │
│  │ • Segments      │  │ • WhatsApp      │  │ • CFDI                      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                                  │
│  │ django-         │  │ django-         │                                  │
│  │ multilingual    │  │ competitive-    │                                  │
│  │ • Translations  │  │ intel           │                                  │
│  │ • Languages     │  │ • Competitors   │                                  │
│  │ • AI Translate  │  │ • Pricing       │                                  │
│  └─────────────────┘  └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INFRASTRUCTURE LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐│
│  │  PostgreSQL  │  │    Redis     │  │   Celery     │  │  File Storage    ││
│  │  (Database)  │  │   (Cache)    │  │  (Tasks)     │  │  (S3/Local)      ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module 1: django-ai-assistant

### Purpose
Core AI chat interface with tool calling, knowledge base, and multilingual support.

### Package Info
```
Package: django-ai-assistant
Version: 1.0.0
Dependencies: openai, tiktoken, django>=4.2
```

### Provided Interfaces

#### ChatService
```python
class ChatService:
    """Main interface for AI chat functionality."""

    def process_message(
        self,
        message: str,
        user: Optional[User] = None,
        conversation_id: Optional[str] = None,
        language: str = "es"
    ) -> ChatResponse:
        """
        Process a user message and return AI response.

        Args:
            message: User's message text
            user: Authenticated user (optional for public queries)
            conversation_id: Existing conversation to continue
            language: Response language code

        Returns:
            ChatResponse with message, tool_calls, and metadata
        """
        pass

    def register_tools(self, tools: List[ToolDefinition]) -> None:
        """Register additional tools from other modules."""
        pass

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Message]:
        """Retrieve conversation history."""
        pass
```

#### ToolRegistry
```python
class ToolRegistry:
    """Registry for AI tools from all modules."""

    def register(
        self,
        name: str,
        handler: Callable,
        schema: dict,
        permission: str = "public"
    ) -> None:
        """
        Register a tool for AI use.

        Args:
            name: Unique tool name
            handler: Function to execute tool
            schema: OpenAI function schema
            permission: Required permission level
        """
        pass

    def get_tools_for_user(self, user: User) -> List[dict]:
        """Get tool schemas available to a user."""
        pass

    def execute_tool(
        self,
        name: str,
        params: dict,
        user: User
    ) -> ToolResult:
        """Execute a registered tool."""
        pass
```

#### KnowledgeBase
```python
class KnowledgeBase:
    """Interface for knowledge base queries."""

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[KnowledgeEntry]:
        """Search knowledge base with semantic matching."""
        pass

    def add_entry(
        self,
        title: str,
        content: str,
        category: str,
        metadata: Optional[dict] = None
    ) -> KnowledgeEntry:
        """Add entry to knowledge base."""
        pass
```

### Required Interfaces (Dependencies)

This module requires other modules to register their tools:

```python
# Signal for tool registration
ai_assistant_ready = Signal()

# Other modules connect to register tools
@receiver(ai_assistant_ready)
def register_vet_clinic_tools(sender, **kwargs):
    registry = kwargs['registry']
    registry.register('get_pet_profile', get_pet_profile_handler, PET_PROFILE_SCHEMA)
```

### Settings
```python
AI_ASSISTANT = {
    'PROVIDER': 'openrouter',  # or 'openai', 'anthropic'
    'MODEL': 'anthropic/claude-3-sonnet',
    'API_KEY': env('OPENROUTER_API_KEY'),
    'MAX_TOKENS': 4096,
    'TEMPERATURE': 0.7,
    'KNOWLEDGE_BASE_ENABLED': True,
    'CONVERSATION_TTL_HOURS': 24,
}
```

---

## Module 2: django-vet-clinic

### Purpose
Pet profiles, medical records, vaccinations, and veterinary-specific functionality.

### Package Info
```
Package: django-vet-clinic
Version: 1.0.0
Dependencies: django>=4.2, pillow
```

### Provided Interfaces

#### PetService
```python
class PetService:
    """Service for pet management."""

    def get_pet(self, pet_id: int, user: User) -> Pet:
        """Get pet by ID (enforces ownership)."""
        pass

    def get_user_pets(self, user: User) -> QuerySet[Pet]:
        """Get all pets for a user."""
        pass

    def create_pet(self, user: User, data: PetCreateData) -> Pet:
        """Create a new pet for user."""
        pass

    def update_pet(self, pet_id: int, user: User, data: PetUpdateData) -> Pet:
        """Update pet information."""
        pass

    def get_pet_summary(self, pet_id: int) -> PetSummary:
        """Get health summary for a pet."""
        pass
```

#### MedicalRecordService
```python
class MedicalRecordService:
    """Service for medical records (staff only)."""

    def add_visit(self, pet_id: int, data: VisitData, staff: User) -> Visit:
        """Record a new visit."""
        pass

    def add_vaccination(
        self,
        pet_id: int,
        data: VaccinationData,
        staff: User
    ) -> Vaccination:
        """Record a vaccination."""
        pass

    def get_vaccination_schedule(self, pet_id: int) -> List[VaccinationDue]:
        """Get upcoming vaccination due dates."""
        pass

    def add_clinical_note(
        self,
        visit_id: int,
        content: str,
        staff: User,
        is_internal: bool = True
    ) -> ClinicalNote:
        """Add note to a visit."""
        pass

    def get_visit_history(
        self,
        pet_id: int,
        include_internal: bool = False
    ) -> QuerySet[Visit]:
        """Get visit history (optionally with internal notes)."""
        pass
```

#### TravelCertificateService
```python
class TravelCertificateService:
    """Service for travel documentation."""

    def get_requirements(
        self,
        destination: str,
        pet_id: int
    ) -> TravelRequirements:
        """Get travel requirements for destination."""
        pass

    def create_travel_plan(
        self,
        pet_id: int,
        data: TravelPlanData
    ) -> TravelPlan:
        """Create a travel plan with checklist."""
        pass

    def generate_certificate(
        self,
        travel_plan_id: int,
        staff: User
    ) -> HealthCertificate:
        """Generate health certificate PDF."""
        pass
```

### Events Emitted
```python
# Signals for other modules to react to
pet_created = Signal()       # args: pet, user
pet_updated = Signal()       # args: pet, user, changes
visit_created = Signal()     # args: visit, pet
vaccination_given = Signal() # args: vaccination, pet
vaccination_due = Signal()   # args: pet, vaccine_name, due_date
```

### AI Tools Registered
- `get_pet_profile`
- `list_user_pets`
- `add_pet`
- `update_pet`
- `get_vaccination_status`
- `get_visit_history`
- `get_pet_medications`
- `get_pet_conditions`
- `search_pets` (staff)
- `add_visit_record` (staff)
- `add_vaccination` (staff)
- `add_clinical_note` (staff)
- `check_travel_requirements`
- `create_travel_plan`
- `generate_health_certificate` (staff)

---

## Module 3: django-appointments

### Purpose
Appointment scheduling, booking, reminders, and calendar management.

### Package Info
```
Package: django-appointments
Version: 1.0.0
Dependencies: django>=4.2, python-dateutil
```

### Provided Interfaces

#### AppointmentService
```python
class AppointmentService:
    """Service for appointment management."""

    def check_availability(
        self,
        date: date,
        service_type: Optional[str] = None,
        duration_minutes: int = 30,
        staff_id: Optional[int] = None
    ) -> List[TimeSlot]:
        """Get available time slots for a date."""
        pass

    def book_appointment(
        self,
        user: User,
        pet_id: int,
        date: date,
        time: time,
        service_type: str,
        reason: str,
        notes: Optional[str] = None
    ) -> Appointment:
        """Book an appointment."""
        pass

    def cancel_appointment(
        self,
        appointment_id: int,
        user: User,
        reason: Optional[str] = None
    ) -> Appointment:
        """Cancel an appointment."""
        pass

    def reschedule_appointment(
        self,
        appointment_id: int,
        user: User,
        new_date: date,
        new_time: time
    ) -> Appointment:
        """Reschedule an appointment."""
        pass

    def get_user_appointments(
        self,
        user: User,
        include_past: bool = False,
        pet_id: Optional[int] = None
    ) -> QuerySet[Appointment]:
        """Get appointments for a user."""
        pass
```

#### ScheduleService (Staff)
```python
class ScheduleService:
    """Service for schedule management (staff only)."""

    def get_daily_schedule(
        self,
        date: date,
        staff_id: Optional[int] = None
    ) -> DaySchedule:
        """Get all appointments for a day."""
        pass

    def block_time(
        self,
        date: date,
        start_time: time,
        end_time: time,
        reason: str,
        staff: User
    ) -> TimeBlock:
        """Block a time slot."""
        pass

    def confirm_appointment(
        self,
        appointment_id: int,
        staff: User
    ) -> Appointment:
        """Confirm a pending appointment."""
        pass

    def check_in_patient(
        self,
        appointment_id: int,
        staff: User
    ) -> Appointment:
        """Mark patient as arrived."""
        pass

    def complete_appointment(
        self,
        appointment_id: int,
        staff: User,
        notes: Optional[str] = None,
        follow_up_days: Optional[int] = None
    ) -> Appointment:
        """Mark appointment as complete."""
        pass
```

### Events Emitted
```python
appointment_booked = Signal()     # args: appointment
appointment_confirmed = Signal()  # args: appointment
appointment_cancelled = Signal()  # args: appointment, reason
appointment_completed = Signal()  # args: appointment
appointment_reminder_due = Signal() # args: appointment, hours_before
```

### Required Interfaces
```python
# Requires django-vet-clinic for pet validation
from vet_clinic.services import PetService

# Requires django-omnichannel for reminders
from omnichannel.services import NotificationService
```

### Settings
```python
APPOINTMENTS = {
    'DEFAULT_DURATION_MINUTES': 30,
    'BOOKING_HORIZON_DAYS': 60,
    'MIN_NOTICE_HOURS': 2,
    'REMINDER_HOURS_BEFORE': [24, 2],
    'WORKING_HOURS': {
        'start': '09:00',
        'end': '20:00',
    },
    'CLOSED_DAYS': [0],  # Monday
}
```

---

## Module 4: django-simple-store

### Purpose
E-commerce functionality including products, inventory, cart, and orders.

### Package Info
```
Package: django-simple-store
Version: 1.0.0
Dependencies: django>=4.2, stripe, pillow
```

### Provided Interfaces

#### ProductService
```python
class ProductService:
    """Service for product catalog."""

    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        species: Optional[str] = None,
        in_stock_only: bool = True,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None
    ) -> QuerySet[Product]:
        """Search products with filters."""
        pass

    def get_product(self, product_id: int) -> Product:
        """Get product details."""
        pass

    def get_recommendations(
        self,
        pet_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Product]:
        """Get product recommendations."""
        pass
```

#### CartService
```python
class CartService:
    """Service for shopping cart."""

    def get_cart(self, user: User) -> Cart:
        """Get or create cart for user."""
        pass

    def add_item(
        self,
        user: User,
        product_id: int,
        quantity: int = 1
    ) -> CartItem:
        """Add product to cart."""
        pass

    def update_item(
        self,
        user: User,
        cart_item_id: int,
        quantity: int
    ) -> CartItem:
        """Update cart item quantity."""
        pass

    def remove_item(self, user: User, cart_item_id: int) -> None:
        """Remove item from cart."""
        pass

    def apply_coupon(self, user: User, coupon_code: str) -> Cart:
        """Apply coupon code to cart."""
        pass

    def get_cart_total(self, user: User) -> CartTotal:
        """Calculate cart total with discounts and tax."""
        pass
```

#### OrderService
```python
class OrderService:
    """Service for order management."""

    def create_order(
        self,
        user: User,
        payment_method: str,
        shipping_address: Optional[Address] = None
    ) -> Order:
        """Create order from cart."""
        pass

    def get_user_orders(
        self,
        user: User,
        status: Optional[str] = None
    ) -> QuerySet[Order]:
        """Get user's orders."""
        pass

    def get_order(self, order_id: int, user: User) -> Order:
        """Get order details (enforces ownership)."""
        pass

    def update_order_status(
        self,
        order_id: int,
        status: str,
        staff: User
    ) -> Order:
        """Update order status (staff only)."""
        pass
```

#### InventoryService
```python
class InventoryService:
    """Service for inventory management (staff only)."""

    def check_stock(self, product_id: int) -> StockLevel:
        """Check current stock level."""
        pass

    def get_low_stock_products(
        self,
        category: Optional[str] = None
    ) -> QuerySet[Product]:
        """Get products below reorder point."""
        pass

    def get_expiring_products(
        self,
        days_ahead: int = 90
    ) -> QuerySet[StockBatch]:
        """Get products expiring soon."""
        pass

    def adjust_stock(
        self,
        product_id: int,
        quantity_change: int,
        reason: str,
        staff: User,
        notes: Optional[str] = None
    ) -> StockMovement:
        """Record stock adjustment."""
        pass

    def receive_stock(
        self,
        product_id: int,
        quantity: int,
        batch_number: Optional[str] = None,
        expiry_date: Optional[date] = None,
        cost_per_unit: Optional[Decimal] = None,
        staff: User
    ) -> StockBatch:
        """Record stock receipt."""
        pass
```

### Events Emitted
```python
order_created = Signal()      # args: order
order_paid = Signal()         # args: order
order_shipped = Signal()      # args: order
order_delivered = Signal()    # args: order
low_stock_alert = Signal()    # args: product, current_level
expiry_alert = Signal()       # args: batch, days_until_expiry
```

### Required Interfaces
```python
# For customer discounts
from crm.services import LoyaltyService

# For invoicing
from billing.services import InvoiceService

# For inventory valuation
from accounting.services import AccountingService
```

### Settings
```python
SIMPLE_STORE = {
    'CURRENCY': 'MXN',
    'TAX_RATE': Decimal('0.16'),  # IVA
    'LOW_STOCK_THRESHOLD': 10,
    'EXPIRY_ALERT_DAYS': 90,
    'STRIPE_PUBLIC_KEY': env('STRIPE_PUBLIC_KEY'),
    'STRIPE_SECRET_KEY': env('STRIPE_SECRET_KEY'),
}
```

---

## Module 5: django-omnichannel

### Purpose
Multi-channel communications: Email, SMS, WhatsApp, with unified inbox and escalation.

### Package Info
```
Package: django-omnichannel
Version: 1.0.0
Dependencies: django>=4.2, twilio, django-ses
```

### Provided Interfaces

#### MessageService
```python
class MessageService:
    """Service for sending messages."""

    def send_message(
        self,
        user_id: int,
        message: str,
        channel: str = 'auto',
        template: Optional[str] = None,
        template_vars: Optional[dict] = None
    ) -> Message:
        """
        Send message via specified or preferred channel.

        Args:
            user_id: Target user
            message: Message content
            channel: 'email', 'sms', 'whatsapp', or 'auto'
            template: Template ID for channel-specific formatting
            template_vars: Variables for template
        """
        pass

    def send_bulk_message(
        self,
        user_ids: List[int],
        message: str,
        channel: str = 'auto'
    ) -> List[Message]:
        """Send message to multiple users."""
        pass

    def get_message_status(self, message_id: str) -> MessageStatus:
        """Check delivery status."""
        pass
```

#### InboxService
```python
class InboxService:
    """Service for unified inbox (staff only)."""

    def get_unread_messages(
        self,
        channel: Optional[str] = None,
        limit: int = 20
    ) -> List[IncomingMessage]:
        """Get unread incoming messages."""
        pass

    def get_conversation(
        self,
        user_id: int,
        limit: int = 50
    ) -> Conversation:
        """Get full conversation with a user."""
        pass

    def mark_read(self, message_ids: List[str]) -> None:
        """Mark messages as read."""
        pass

    def reply(
        self,
        conversation_id: int,
        message: str,
        staff: User
    ) -> Message:
        """Reply to a conversation."""
        pass
```

#### ReminderService
```python
class ReminderService:
    """Service for scheduling reminders."""

    def schedule_reminder(
        self,
        user_id: int,
        reminder_type: str,
        send_at: datetime,
        message: Optional[str] = None,
        related_object_id: Optional[int] = None,
        related_object_type: Optional[str] = None
    ) -> Reminder:
        """Schedule a reminder."""
        pass

    def cancel_reminder(self, reminder_id: int) -> None:
        """Cancel a scheduled reminder."""
        pass

    def get_pending_reminders(
        self,
        user_id: Optional[int] = None,
        reminder_type: Optional[str] = None
    ) -> QuerySet[Reminder]:
        """Get pending reminders."""
        pass

    def escalate_reminder(
        self,
        reminder_id: int
    ) -> Reminder:
        """Escalate unresponded reminder to next channel."""
        pass
```

#### NotificationPreferenceService
```python
class NotificationPreferenceService:
    """Service for user notification preferences."""

    def get_preferences(self, user_id: int) -> NotificationPreferences:
        """Get user's notification preferences."""
        pass

    def update_preferences(
        self,
        user_id: int,
        data: PreferenceUpdateData
    ) -> NotificationPreferences:
        """Update notification preferences."""
        pass

    def get_preferred_channel(self, user_id: int) -> str:
        """Get user's preferred communication channel."""
        pass
```

### Events Emitted
```python
message_sent = Signal()       # args: message
message_delivered = Signal()  # args: message
message_failed = Signal()     # args: message, error
message_received = Signal()   # args: incoming_message
reminder_sent = Signal()      # args: reminder
reminder_confirmed = Signal() # args: reminder
```

### Webhook Handlers
```python
# WhatsApp webhook
def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages."""
    pass

# Twilio SMS webhook
def sms_webhook(request):
    """Handle incoming SMS."""
    pass

# Email webhook (SES)
def email_webhook(request):
    """Handle email bounces/complaints."""
    pass
```

### Settings
```python
OMNICHANNEL = {
    'DEFAULT_CHANNEL': 'whatsapp',
    'ESCALATION_ORDER': ['whatsapp', 'sms', 'email'],
    'ESCALATION_WAIT_HOURS': 24,
    'TWILIO_ACCOUNT_SID': env('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': env('TWILIO_AUTH_TOKEN'),
    'TWILIO_PHONE_NUMBER': env('TWILIO_PHONE_NUMBER'),
    'WHATSAPP_BUSINESS_PHONE': env('WHATSAPP_BUSINESS_PHONE'),
    'AWS_SES_REGION': 'us-east-1',
}
```

---

## Module 6: django-crm-lite

### Purpose
Customer relationship management, loyalty program, segmentation, and marketing.

### Package Info
```
Package: django-crm-lite
Version: 1.0.0
Dependencies: django>=4.2
```

### Provided Interfaces

#### CustomerService
```python
class CustomerService:
    """Service for customer profiles."""

    def get_profile(
        self,
        user_id: int,
        include_pets: bool = True,
        include_purchase_history: bool = False
    ) -> CustomerProfile:
        """Get detailed customer profile."""
        pass

    def search_customers(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        segment: Optional[str] = None
    ) -> QuerySet[CustomerProfile]:
        """Search customers."""
        pass

    def add_note(
        self,
        user_id: int,
        content: str,
        staff: User,
        is_pinned: bool = False
    ) -> CustomerNote:
        """Add note to customer profile."""
        pass

    def add_tag(self, user_id: int, tag: str) -> None:
        """Add tag to customer."""
        pass

    def remove_tag(self, user_id: int, tag: str) -> None:
        """Remove tag from customer."""
        pass

    def calculate_ltv(self, user_id: int) -> Decimal:
        """Calculate customer lifetime value."""
        pass
```

#### LoyaltyService
```python
class LoyaltyService:
    """Service for loyalty program."""

    def get_member(self, user_id: int) -> LoyaltyMember:
        """Get loyalty member profile."""
        pass

    def get_points_balance(self, user_id: int) -> int:
        """Get current points balance."""
        pass

    def add_points(
        self,
        user_id: int,
        points: int,
        reason: str,
        order_id: Optional[int] = None
    ) -> PointsTransaction:
        """Add points to member."""
        pass

    def redeem_points(
        self,
        user_id: int,
        reward_id: int
    ) -> Redemption:
        """Redeem points for a reward."""
        pass

    def get_tier(self, user_id: int) -> LoyaltyTier:
        """Get current loyalty tier."""
        pass

    def get_available_rewards(
        self,
        user_id: int,
        affordable_only: bool = True
    ) -> List[Reward]:
        """Get rewards available to member."""
        pass

    def get_discount_percent(self, user_id: int) -> Decimal:
        """Get loyalty discount percentage for user."""
        pass
```

#### SegmentService
```python
class SegmentService:
    """Service for customer segmentation."""

    def get_segment(
        self,
        segment_id: Optional[int] = None,
        segment_name: Optional[str] = None
    ) -> QuerySet[User]:
        """Get customers in a segment."""
        pass

    def create_segment(
        self,
        name: str,
        criteria: SegmentCriteria
    ) -> Segment:
        """Create a new segment."""
        pass

    def get_insights(
        self,
        insight_type: str,
        date_range: Optional[str] = None
    ) -> InsightReport:
        """Get customer insights."""
        pass
```

### Events Emitted
```python
customer_created = Signal()   # args: user
tier_upgraded = Signal()      # args: member, old_tier, new_tier
points_earned = Signal()      # args: member, points, reason
reward_redeemed = Signal()    # args: member, reward
referral_completed = Signal() # args: referrer, referred
```

### Required Interfaces
```python
# For purchase history
from simple_store.services import OrderService

# For communication
from omnichannel.services import MessageService
```

### Settings
```python
CRM_LITE = {
    'LOYALTY_ENABLED': True,
    'POINTS_PER_CURRENCY_UNIT': 1,  # 1 point per peso
    'TIERS': [
        {'name': 'bronze', 'min_spend': 0, 'discount': 0},
        {'name': 'silver', 'min_spend': 5000, 'discount': 5},
        {'name': 'gold', 'min_spend': 15000, 'discount': 10},
        {'name': 'platinum', 'min_spend': 30000, 'discount': 15},
    ],
    'REFERRAL_POINTS': 500,
}
```

---

## Module 7: django-multilingual

### Purpose
AI-powered translation, language management, and content localization.

### Package Info
```
Package: django-multilingual
Version: 1.0.0
Dependencies: django>=4.2
```

### Provided Interfaces

#### TranslationService
```python
class TranslationService:
    """Service for AI-powered translation."""

    def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """Translate text to target language."""
        pass

    def translate_object(
        self,
        obj: Model,
        target_language: str,
        fields: List[str]
    ) -> dict:
        """Translate multiple fields of an object."""
        pass

    def get_cached_translation(
        self,
        content_hash: str,
        target_language: str
    ) -> Optional[str]:
        """Get cached translation if available."""
        pass
```

#### LanguageService
```python
class LanguageService:
    """Service for language management."""

    def get_available_languages(self) -> List[Language]:
        """Get all available languages."""
        pass

    def get_user_language(self, user: User) -> str:
        """Get user's preferred language."""
        pass

    def set_user_language(self, user: User, language: str) -> None:
        """Set user's preferred language."""
        pass

    def detect_language(self, text: str) -> str:
        """Detect language of text."""
        pass
```

### Template Tags
```python
# Usage in templates
{% load multilingual %}

{% translate "Hello" to=user_language %}
{% translate_field object.description to=user_language %}
```

### Settings
```python
MULTILINGUAL = {
    'DEFAULT_LANGUAGE': 'es',
    'CORE_LANGUAGES': ['es', 'en', 'de', 'fr', 'it'],
    'AI_TRANSLATE_ENABLED': True,
    'CACHE_TRANSLATIONS': True,
    'CACHE_TTL_DAYS': 30,
}
```

---

## Module 8: django-competitive-intel

### Purpose
Competitor tracking, pricing comparison, and market intelligence.

### Package Info
```
Package: django-competitive-intel
Version: 1.0.0
Dependencies: django>=4.2
```

### Provided Interfaces

#### CompetitorService
```python
class CompetitorService:
    """Service for competitor tracking (admin only)."""

    def get_competitors(self) -> QuerySet[Competitor]:
        """Get all tracked competitors."""
        pass

    def get_competitor(self, competitor_id: int) -> Competitor:
        """Get competitor details."""
        pass

    def add_competitor(self, data: CompetitorData) -> Competitor:
        """Add a new competitor."""
        pass

    def log_pricing(
        self,
        competitor_id: int,
        service: str,
        price: Decimal,
        source: str
    ) -> PricingRecord:
        """Log competitor pricing."""
        pass

    def compare_pricing(
        self,
        service_type: str
    ) -> PricingComparison:
        """Compare pricing with competitors."""
        pass
```

#### VisitorIntelligenceService
```python
class VisitorIntelligenceService:
    """Service for visitor intelligence (admin only)."""

    def log_visit(
        self,
        ip_address: str,
        user_agent: str,
        page: str
    ) -> Visit:
        """Log a website visit."""
        pass

    def get_competitor_visits(
        self,
        days: int = 30
    ) -> List[CompetitorVisit]:
        """Get visits from competitor IP ranges."""
        pass

    def get_insights(self) -> CompetitiveInsights:
        """Get AI-generated competitive insights."""
        pass
```

### Settings
```python
COMPETITIVE_INTEL = {
    'TRACK_VISITOR_IPS': True,
    'COMPETITOR_IP_RANGES': [],  # Populated from competitor records
    'INSIGHTS_REFRESH_HOURS': 24,
}
```

---

## Module 9: django-accounting

### Purpose
Full double-entry accounting, financial statements, AP/AR, bank reconciliation.

### Package Info
```
Package: django-accounting
Version: 1.0.0
Dependencies: django>=4.2
```

### Provided Interfaces

#### GeneralLedgerService
```python
class GeneralLedgerService:
    """Service for general ledger operations (admin only)."""

    def get_account(
        self,
        account_id: Optional[int] = None,
        account_code: Optional[str] = None
    ) -> Account:
        """Get account by ID or code."""
        pass

    def get_account_balance(
        self,
        account_id: int,
        as_of_date: Optional[date] = None
    ) -> Decimal:
        """Get account balance."""
        pass

    def create_journal_entry(
        self,
        date: date,
        lines: List[JournalLineData],
        reference: Optional[str] = None,
        description: Optional[str] = None
    ) -> JournalEntry:
        """Create a journal entry."""
        pass

    def post_entry(self, entry_id: int, user: User) -> JournalEntry:
        """Post a journal entry."""
        pass
```

#### FinancialStatementService
```python
class FinancialStatementService:
    """Service for financial statements (admin only)."""

    def get_profit_loss(
        self,
        start_date: date,
        end_date: date,
        compare_prior: bool = False
    ) -> ProfitLossStatement:
        """Generate profit & loss statement."""
        pass

    def get_balance_sheet(
        self,
        as_of_date: date,
        compare_prior: bool = False
    ) -> BalanceSheet:
        """Generate balance sheet."""
        pass

    def get_cash_flow(
        self,
        start_date: date,
        end_date: date
    ) -> CashFlowStatement:
        """Generate cash flow statement."""
        pass
```

#### PayablesService
```python
class PayablesService:
    """Service for accounts payable (admin only)."""

    def create_bill(
        self,
        vendor_id: int,
        data: BillData
    ) -> Bill:
        """Create a vendor bill."""
        pass

    def pay_bill(
        self,
        bill_id: int,
        amount: Decimal,
        payment_method: str,
        bank_account_id: int,
        reference: Optional[str] = None
    ) -> BillPayment:
        """Record payment for a bill."""
        pass

    def get_aging_report(
        self,
        as_of_date: Optional[date] = None
    ) -> AgingReport:
        """Get AP aging report."""
        pass
```

#### ReceivablesService
```python
class ReceivablesService:
    """Service for accounts receivable (admin only)."""

    def get_aging_report(
        self,
        as_of_date: Optional[date] = None
    ) -> AgingReport:
        """Get AR aging report."""
        pass

    def get_customer_balance(self, user_id: int) -> Decimal:
        """Get customer outstanding balance."""
        pass
```

#### BankReconciliationService
```python
class BankReconciliationService:
    """Service for bank reconciliation (admin only)."""

    def start_reconciliation(
        self,
        bank_account_id: int,
        statement_date: date,
        statement_balance: Decimal
    ) -> BankReconciliation:
        """Start a bank reconciliation."""
        pass

    def match_transaction(
        self,
        reconciliation_id: int,
        bank_transaction_id: int,
        gl_transaction_id: int
    ) -> None:
        """Match a bank transaction to GL."""
        pass

    def complete_reconciliation(
        self,
        reconciliation_id: int,
        user: User
    ) -> BankReconciliation:
        """Complete and lock reconciliation."""
        pass
```

#### BudgetService
```python
class BudgetService:
    """Service for budget management (admin only)."""

    def get_budget(
        self,
        year: int,
        account_id: Optional[int] = None
    ) -> Budget:
        """Get budget for a year."""
        pass

    def set_budget(
        self,
        year: int,
        account_id: int,
        monthly_amounts: List[Decimal]
    ) -> Budget:
        """Set monthly budget for an account."""
        pass

    def get_variance_report(
        self,
        year: int,
        month: Optional[int] = None
    ) -> VarianceReport:
        """Get budget vs actual variance."""
        pass
```

### Events Emitted
```python
journal_posted = Signal()      # args: entry
bill_created = Signal()        # args: bill
bill_paid = Signal()           # args: bill, payment
period_closed = Signal()       # args: period
reconciliation_completed = Signal() # args: reconciliation
```

### Required Interfaces
```python
# For invoice integration
from billing.services import InvoiceService

# For inventory valuation
from simple_store.services import InventoryService
```

### Settings
```python
ACCOUNTING = {
    'FISCAL_YEAR_START_MONTH': 1,
    'DEFAULT_CURRENCY': 'MXN',
    'TAX_RATE': Decimal('0.16'),  # IVA
    'CFDI_PROVIDER': 'facturama',
    'CFDI_ENVIRONMENT': 'sandbox',  # or 'production'
}
```

---

## Inter-Module Communication

### Event-Driven Integration

Modules communicate primarily through Django signals:

```python
# In django-appointments
from vet_clinic.signals import vaccination_due

@receiver(vaccination_due)
def schedule_vaccination_reminder(sender, pet, vaccine_name, due_date, **kwargs):
    """Schedule reminder when vaccination is due."""
    ReminderService().schedule_reminder(
        user_id=pet.owner_id,
        reminder_type='vaccination',
        send_at=due_date - timedelta(days=7),
        message=f"{pet.name} needs {vaccine_name} vaccination"
    )
```

### Service Injection

For direct service calls, use dependency injection:

```python
# In django-simple-store
class CheckoutService:
    def __init__(
        self,
        loyalty_service: Optional[LoyaltyService] = None,
        invoice_service: Optional[InvoiceService] = None
    ):
        self.loyalty_service = loyalty_service or LoyaltyService()
        self.invoice_service = invoice_service or InvoiceService()

    def complete_checkout(self, user: User, cart: Cart) -> Order:
        # Apply loyalty discount
        discount = self.loyalty_service.get_discount_percent(user.id)

        # Create order
        order = self._create_order(user, cart, discount)

        # Create invoice
        invoice = self.invoice_service.create_from_order(order)

        # Award points
        self.loyalty_service.add_points(
            user.id,
            int(order.total),
            'purchase',
            order_id=order.id
        )

        return order
```

### Shared Models

Some models are shared across modules via abstract base classes:

```python
# In core app
class AuditMixin(models.Model):
    """Mixin for audit trail."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True

class TranslatableMixin(models.Model):
    """Mixin for translatable content."""

    def get_translated_field(self, field_name: str, language: str) -> str:
        """Get translated value for a field."""
        pass

    class Meta:
        abstract = True
```

---

## API Versioning

All public APIs are versioned:

```python
# URLs
urlpatterns = [
    path('api/v1/', include('api.v1.urls')),
]

# API views include version in response
class APIView:
    api_version = 'v1'
```

---

## Error Handling

Standardized error responses across all modules:

```python
class ServiceError(Exception):
    """Base exception for service errors."""
    code: str
    message: str
    status_code: int = 400

class NotFoundError(ServiceError):
    status_code = 404

class PermissionDeniedError(ServiceError):
    status_code = 403

class ValidationError(ServiceError):
    status_code = 422
```

---

## Testing Interfaces

Each module provides test utilities:

```python
# In django-vet-clinic
from vet_clinic.testing import PetFactory, VisitFactory

def test_pet_creation():
    pet = PetFactory(species='dog', name='Luna')
    assert pet.name == 'Luna'
```

---

*Last Updated: December 21, 2025*
