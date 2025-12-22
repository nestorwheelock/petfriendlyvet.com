# AI Tool Schemas - Pet-Friendly Veterinary Clinic

## Overview

This document defines all AI tool schemas used by the Pet-Friendly AI assistants. Tools are organized by module and follow OpenAI function calling format for compatibility with Claude/OpenRouter.

**Total Tools**: 156 tools across 9 modules

---

## Tool Architecture

### Tool Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Query** | Read-only data retrieval | `get_pet_profile`, `search_products` |
| **Action** | Create, update, delete operations | `book_appointment`, `add_to_cart` |
| **Report** | Generate reports and analytics | `generate_revenue_report` |
| **Communication** | Send messages and notifications | `send_reminder`, `send_message` |

### Permission Levels

| Level | Description | Tools Available |
|-------|-------------|-----------------|
| **public** | No auth required | `get_clinic_info`, `search_products` |
| **customer** | Authenticated pet owner | `book_appointment`, `get_my_pets` |
| **staff** | Clinic staff member | `update_appointment`, `add_clinical_note` |
| **admin** | Dr. Pablo / administrators | `generate_reports`, `manage_users` |

### Standard Tool Response Format

```python
class ToolResponse:
    success: bool
    data: Optional[dict]
    error: Optional[str]
    message: Optional[str]  # Human-readable message for AI to relay
```

---

## Module 1: django-ai-assistant (S-001, S-002)

### Core Tools

```json
{
  "name": "get_clinic_info",
  "description": "Get clinic information including hours, location, contact, and services",
  "parameters": {
    "type": "object",
    "properties": {
      "info_type": {
        "type": "string",
        "enum": ["hours", "location", "contact", "services", "about", "all"],
        "description": "Type of information to retrieve"
      },
      "language": {
        "type": "string",
        "enum": ["es", "en"],
        "default": "es"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "search_knowledge_base",
  "description": "Search the knowledge base for pet care information, FAQs, and clinic policies",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query in natural language"
      },
      "category": {
        "type": "string",
        "enum": ["pet_care", "services", "policies", "faq", "all"],
        "default": "all"
      },
      "species": {
        "type": "string",
        "enum": ["dog", "cat", "bird", "reptile", "other"],
        "description": "Filter by pet species if relevant"
      },
      "limit": {
        "type": "integer",
        "default": 5,
        "maximum": 10
      }
    },
    "required": ["query"]
  }
}
```

```json
{
  "name": "get_service_details",
  "description": "Get detailed information about a specific veterinary service",
  "parameters": {
    "type": "object",
    "properties": {
      "service_id": {
        "type": "integer",
        "description": "Service ID"
      },
      "service_name": {
        "type": "string",
        "description": "Service name to search for"
      },
      "include_pricing": {
        "type": "boolean",
        "default": true
      },
      "language": {
        "type": "string",
        "enum": ["es", "en"],
        "default": "es"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_current_user",
  "description": "Get information about the currently authenticated user",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

---

## Module 2: django-vet-clinic (S-003, S-022)

### Pet Profile Tools

```json
{
  "name": "get_pet_profile",
  "description": "Get detailed profile information for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer",
        "description": "Pet ID"
      },
      "include_medical": {
        "type": "boolean",
        "default": true,
        "description": "Include medical history summary"
      },
      "include_vaccinations": {
        "type": "boolean",
        "default": true
      },
      "include_documents": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "list_user_pets",
  "description": "List all pets belonging to the current user",
  "parameters": {
    "type": "object",
    "properties": {
      "include_summary": {
        "type": "boolean",
        "default": true,
        "description": "Include health summary for each pet"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "add_pet",
  "description": "Add a new pet to the user's account",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Pet's name"
      },
      "species": {
        "type": "string",
        "enum": ["dog", "cat", "bird", "reptile", "small_mammal", "other"]
      },
      "breed": {
        "type": "string"
      },
      "date_of_birth": {
        "type": "string",
        "format": "date",
        "description": "YYYY-MM-DD format"
      },
      "gender": {
        "type": "string",
        "enum": ["male", "female"]
      },
      "weight_kg": {
        "type": "number"
      },
      "is_neutered": {
        "type": "boolean",
        "default": false
      },
      "microchip_id": {
        "type": "string"
      }
    },
    "required": ["name", "species", "gender"]
  }
}
```

```json
{
  "name": "update_pet",
  "description": "Update pet information",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "weight_kg": {
        "type": "number"
      },
      "is_neutered": {
        "type": "boolean"
      },
      "photo_url": {
        "type": "string"
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "get_vaccination_status",
  "description": "Get vaccination status and upcoming due dates for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "include_history": {
        "type": "boolean",
        "default": true
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "get_visit_history",
  "description": "Get visit history for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "limit": {
        "type": "integer",
        "default": 10
      },
      "include_notes": {
        "type": "boolean",
        "default": true,
        "description": "Include visit notes (owner-visible only)"
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "get_pet_medications",
  "description": "Get current and past medications for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "active_only": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "get_pet_conditions",
  "description": "Get medical conditions and allergies for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      }
    },
    "required": ["pet_id"]
  }
}
```

### Staff Pet Tools

```json
{
  "name": "search_pets",
  "description": "Search for pets by name, owner, or criteria (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query (pet name or owner name)"
      },
      "species": {
        "type": "string",
        "enum": ["dog", "cat", "bird", "reptile", "small_mammal", "other"]
      },
      "owner_id": {
        "type": "integer"
      },
      "limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "add_visit_record",
  "description": "Record a new visit for a pet (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "reason": {
        "type": "string"
      },
      "diagnosis": {
        "type": "string"
      },
      "treatment": {
        "type": "string"
      },
      "weight_kg": {
        "type": "number"
      },
      "follow_up_date": {
        "type": "string",
        "format": "date"
      },
      "internal_notes": {
        "type": "string",
        "description": "Internal notes not visible to owner"
      }
    },
    "required": ["pet_id", "reason"]
  }
}
```

```json
{
  "name": "add_vaccination",
  "description": "Record a vaccination for a pet (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "vaccine_name": {
        "type": "string"
      },
      "batch_number": {
        "type": "string"
      },
      "next_due_date": {
        "type": "string",
        "format": "date"
      },
      "notes": {
        "type": "string"
      }
    },
    "required": ["pet_id", "vaccine_name"]
  }
}
```

```json
{
  "name": "add_clinical_note",
  "description": "Add internal clinical note to a visit (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "visit_id": {
        "type": "integer"
      },
      "content": {
        "type": "string"
      },
      "is_internal": {
        "type": "boolean",
        "default": true,
        "description": "If true, not visible to pet owner"
      }
    },
    "required": ["visit_id", "content"]
  }
}
```

### Travel Certificate Tools (S-022)

```json
{
  "name": "check_travel_requirements",
  "description": "Check travel requirements for a destination country",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "destination_country": {
        "type": "string",
        "description": "ISO country code (e.g., US, DE, FR)"
      },
      "travel_date": {
        "type": "string",
        "format": "date"
      },
      "airline": {
        "type": "string",
        "description": "Airline code if known"
      }
    },
    "required": ["pet_id", "destination_country"]
  }
}
```

```json
{
  "name": "create_travel_plan",
  "description": "Create a travel plan with checklist for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "destination_country": {
        "type": "string"
      },
      "travel_date": {
        "type": "string",
        "format": "date"
      },
      "return_date": {
        "type": "string",
        "format": "date"
      },
      "airline": {
        "type": "string"
      }
    },
    "required": ["pet_id", "destination_country", "travel_date"]
  }
}
```

```json
{
  "name": "get_travel_checklist",
  "description": "Get travel preparation checklist for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "travel_plan_id": {
        "type": "integer"
      }
    },
    "required": ["travel_plan_id"]
  }
}
```

```json
{
  "name": "generate_health_certificate",
  "description": "Generate health certificate for travel (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "travel_plan_id": {
        "type": "integer"
      },
      "include_vaccinations": {
        "type": "boolean",
        "default": true
      }
    },
    "required": ["travel_plan_id"]
  }
}
```

```json
{
  "name": "get_airline_requirements",
  "description": "Get airline-specific pet travel requirements",
  "parameters": {
    "type": "object",
    "properties": {
      "airline_code": {
        "type": "string"
      },
      "pet_species": {
        "type": "string"
      },
      "cabin_or_cargo": {
        "type": "string",
        "enum": ["cabin", "cargo"]
      }
    },
    "required": ["airline_code"]
  }
}
```

---

## Module 3: django-appointments (S-004)

### Customer Appointment Tools

```json
{
  "name": "check_availability",
  "description": "Check available appointment slots",
  "parameters": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "format": "date",
        "description": "Date to check (YYYY-MM-DD)"
      },
      "service_type": {
        "type": "string",
        "description": "Type of service (consultation, vaccination, surgery, etc.)"
      },
      "veterinarian_id": {
        "type": "integer",
        "description": "Specific vet if preferred"
      },
      "duration_minutes": {
        "type": "integer",
        "default": 30
      }
    },
    "required": ["date"]
  }
}
```

```json
{
  "name": "book_appointment",
  "description": "Book an appointment for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "date": {
        "type": "string",
        "format": "date"
      },
      "time": {
        "type": "string",
        "description": "Time in HH:MM format"
      },
      "service_type": {
        "type": "string"
      },
      "reason": {
        "type": "string",
        "description": "Reason for visit"
      },
      "notes": {
        "type": "string",
        "description": "Additional notes for the vet"
      }
    },
    "required": ["pet_id", "date", "time", "service_type"]
  }
}
```

```json
{
  "name": "get_user_appointments",
  "description": "Get upcoming appointments for the current user",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer",
        "description": "Filter by specific pet"
      },
      "include_past": {
        "type": "boolean",
        "default": false
      },
      "limit": {
        "type": "integer",
        "default": 10
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "cancel_appointment",
  "description": "Cancel an existing appointment",
  "parameters": {
    "type": "object",
    "properties": {
      "appointment_id": {
        "type": "integer"
      },
      "reason": {
        "type": "string",
        "description": "Reason for cancellation"
      }
    },
    "required": ["appointment_id"]
  }
}
```

```json
{
  "name": "reschedule_appointment",
  "description": "Reschedule an existing appointment",
  "parameters": {
    "type": "object",
    "properties": {
      "appointment_id": {
        "type": "integer"
      },
      "new_date": {
        "type": "string",
        "format": "date"
      },
      "new_time": {
        "type": "string"
      }
    },
    "required": ["appointment_id", "new_date", "new_time"]
  }
}
```

### Staff Appointment Tools

```json
{
  "name": "get_daily_schedule",
  "description": "Get all appointments for a date (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "format": "date"
      },
      "veterinarian_id": {
        "type": "integer"
      }
    },
    "required": ["date"]
  }
}
```

```json
{
  "name": "confirm_appointment",
  "description": "Confirm a pending appointment (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "appointment_id": {
        "type": "integer"
      },
      "send_confirmation": {
        "type": "boolean",
        "default": true
      }
    },
    "required": ["appointment_id"]
  }
}
```

```json
{
  "name": "block_time",
  "description": "Block a time slot (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "format": "date"
      },
      "start_time": {
        "type": "string"
      },
      "end_time": {
        "type": "string"
      },
      "reason": {
        "type": "string"
      }
    },
    "required": ["date", "start_time", "end_time"]
  }
}
```

```json
{
  "name": "check_in_appointment",
  "description": "Mark patient as arrived (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "appointment_id": {
        "type": "integer"
      }
    },
    "required": ["appointment_id"]
  }
}
```

```json
{
  "name": "complete_appointment",
  "description": "Mark appointment as complete (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "appointment_id": {
        "type": "integer"
      },
      "notes": {
        "type": "string"
      },
      "follow_up_needed": {
        "type": "boolean"
      },
      "follow_up_days": {
        "type": "integer"
      }
    },
    "required": ["appointment_id"]
  }
}
```

---

## Module 4: django-simple-store (S-005, S-024)

### Customer Store Tools

```json
{
  "name": "search_products",
  "description": "Search for products in the store",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string"
      },
      "category": {
        "type": "string",
        "enum": ["food", "medication", "accessories", "hygiene", "toys", "all"]
      },
      "species": {
        "type": "string",
        "enum": ["dog", "cat", "bird", "reptile", "all"]
      },
      "min_price": {
        "type": "number"
      },
      "max_price": {
        "type": "number"
      },
      "in_stock_only": {
        "type": "boolean",
        "default": true
      },
      "limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_product_details",
  "description": "Get detailed information about a product",
  "parameters": {
    "type": "object",
    "properties": {
      "product_id": {
        "type": "integer"
      },
      "include_reviews": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["product_id"]
  }
}
```

```json
{
  "name": "add_to_cart",
  "description": "Add a product to the shopping cart",
  "parameters": {
    "type": "object",
    "properties": {
      "product_id": {
        "type": "integer"
      },
      "quantity": {
        "type": "integer",
        "default": 1
      }
    },
    "required": ["product_id"]
  }
}
```

```json
{
  "name": "get_cart",
  "description": "Get current shopping cart contents",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

```json
{
  "name": "update_cart_item",
  "description": "Update quantity of an item in cart",
  "parameters": {
    "type": "object",
    "properties": {
      "cart_item_id": {
        "type": "integer"
      },
      "quantity": {
        "type": "integer"
      }
    },
    "required": ["cart_item_id", "quantity"]
  }
}
```

```json
{
  "name": "remove_from_cart",
  "description": "Remove an item from cart",
  "parameters": {
    "type": "object",
    "properties": {
      "cart_item_id": {
        "type": "integer"
      }
    },
    "required": ["cart_item_id"]
  }
}
```

```json
{
  "name": "apply_coupon",
  "description": "Apply a coupon code to the cart",
  "parameters": {
    "type": "object",
    "properties": {
      "coupon_code": {
        "type": "string"
      }
    },
    "required": ["coupon_code"]
  }
}
```

```json
{
  "name": "get_recommendations",
  "description": "Get product recommendations for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "category": {
        "type": "string"
      },
      "limit": {
        "type": "integer",
        "default": 5
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_order_history",
  "description": "Get user's past orders",
  "parameters": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "default": 10
      },
      "status": {
        "type": "string",
        "enum": ["pending", "processing", "shipped", "delivered", "cancelled", "all"]
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_order_details",
  "description": "Get details of a specific order",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "integer"
      }
    },
    "required": ["order_id"]
  }
}
```

```json
{
  "name": "reorder",
  "description": "Add items from a previous order to cart",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "integer"
      }
    },
    "required": ["order_id"]
  }
}
```

### Inventory Tools (S-024)

```json
{
  "name": "check_stock_level",
  "description": "Check stock level for a product (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "product_id": {
        "type": "integer"
      }
    },
    "required": ["product_id"]
  }
}
```

```json
{
  "name": "get_low_stock_products",
  "description": "Get products below reorder point (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string"
      },
      "limit": {
        "type": "integer",
        "default": 50
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_expiring_products",
  "description": "Get products expiring within specified days (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "days_ahead": {
        "type": "integer",
        "default": 90
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "record_stock_adjustment",
  "description": "Record inventory adjustment (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "product_id": {
        "type": "integer"
      },
      "quantity_change": {
        "type": "integer",
        "description": "Positive for add, negative for remove"
      },
      "reason": {
        "type": "string",
        "enum": ["sale", "damage", "expired", "count_correction", "received", "returned"]
      },
      "notes": {
        "type": "string"
      }
    },
    "required": ["product_id", "quantity_change", "reason"]
  }
}
```

```json
{
  "name": "receive_stock",
  "description": "Record stock receipt from supplier (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "product_id": {
        "type": "integer"
      },
      "quantity": {
        "type": "integer"
      },
      "batch_number": {
        "type": "string"
      },
      "expiry_date": {
        "type": "string",
        "format": "date"
      },
      "supplier": {
        "type": "string"
      },
      "cost_per_unit": {
        "type": "number"
      }
    },
    "required": ["product_id", "quantity"]
  }
}
```

```json
{
  "name": "generate_reorder_list",
  "description": "Generate suggested reorder list (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "include_below_minimum": {
        "type": "boolean",
        "default": true
      },
      "include_expiring": {
        "type": "boolean",
        "default": true
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "create_purchase_order",
  "description": "Create a purchase order for supplier (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "supplier_id": {
        "type": "integer"
      },
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "product_id": {"type": "integer"},
            "quantity": {"type": "integer"}
          }
        }
      }
    },
    "required": ["supplier_id", "items"]
  }
}
```

```json
{
  "name": "get_stock_valuation",
  "description": "Get current inventory valuation (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string"
      },
      "valuation_method": {
        "type": "string",
        "enum": ["fifo", "average"],
        "default": "average"
      }
    },
    "required": []
  }
}
```

---

## Module 5: django-omnichannel (S-006, S-012)

### Communication Tools

```json
{
  "name": "send_message",
  "description": "Send message to a user via their preferred channel",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer"
      },
      "message": {
        "type": "string"
      },
      "channel": {
        "type": "string",
        "enum": ["whatsapp", "sms", "email", "auto"],
        "default": "auto"
      },
      "template": {
        "type": "string",
        "description": "Message template ID"
      },
      "template_vars": {
        "type": "object",
        "description": "Variables for template"
      }
    },
    "required": ["user_id", "message"]
  }
}
```

```json
{
  "name": "get_unread_messages",
  "description": "Get unread incoming messages (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "channel": {
        "type": "string",
        "enum": ["whatsapp", "sms", "email", "all"]
      },
      "limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_conversation_history",
  "description": "Get message history with a user (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer"
      },
      "limit": {
        "type": "integer",
        "default": 50
      },
      "channel": {
        "type": "string"
      }
    },
    "required": ["user_id"]
  }
}
```

```json
{
  "name": "check_message_status",
  "description": "Check delivery status of a message",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "message_id": {
        "type": "string"
      }
    },
    "required": ["message_id"]
  }
}
```

### Reminder Tools (S-012)

```json
{
  "name": "get_notification_preferences",
  "description": "Get user's notification preferences",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer",
        "description": "Required for staff, auto for customer"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "update_notification_preferences",
  "description": "Update notification preferences",
  "parameters": {
    "type": "object",
    "properties": {
      "preferred_channel": {
        "type": "string",
        "enum": ["whatsapp", "sms", "email"]
      },
      "appointment_reminders": {
        "type": "boolean"
      },
      "vaccination_reminders": {
        "type": "boolean"
      },
      "marketing_messages": {
        "type": "boolean"
      },
      "reminder_hours_before": {
        "type": "integer",
        "description": "Hours before appointment to send reminder"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "schedule_reminder",
  "description": "Schedule a reminder for a user (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer"
      },
      "reminder_type": {
        "type": "string",
        "enum": ["appointment", "vaccination", "medication", "follow_up", "custom"]
      },
      "message": {
        "type": "string"
      },
      "send_at": {
        "type": "string",
        "format": "date-time"
      },
      "related_pet_id": {
        "type": "integer"
      }
    },
    "required": ["user_id", "reminder_type", "send_at"]
  }
}
```

```json
{
  "name": "get_upcoming_reminders",
  "description": "Get upcoming scheduled reminders",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer",
        "description": "Required for staff, auto for customer"
      },
      "days_ahead": {
        "type": "integer",
        "default": 30
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_unconfirmed_appointments",
  "description": "Get appointments pending confirmation (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "hours_until": {
        "type": "integer",
        "default": 48
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "escalate_reminder",
  "description": "Escalate unresponded reminder to next channel (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "reminder_id": {
        "type": "integer"
      }
    },
    "required": ["reminder_id"]
  }
}
```

---

## Module 6: django-crm-lite (S-007, S-016)

### CRM Tools

```json
{
  "name": "get_owner_profile",
  "description": "Get detailed profile of a pet owner (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "owner_id": {
        "type": "integer"
      },
      "include_pets": {
        "type": "boolean",
        "default": true
      },
      "include_purchase_history": {
        "type": "boolean",
        "default": true
      },
      "include_communication_history": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["owner_id"]
  }
}
```

```json
{
  "name": "search_owners",
  "description": "Search for pet owners (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Name, email, or phone"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"}
      },
      "segment": {
        "type": "string",
        "enum": ["vip", "at_risk", "new", "inactive", "all"]
      },
      "limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "add_owner_note",
  "description": "Add note to owner's profile (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "owner_id": {
        "type": "integer"
      },
      "content": {
        "type": "string"
      },
      "is_pinned": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["owner_id", "content"]
  }
}
```

```json
{
  "name": "tag_owner",
  "description": "Add or remove tags from owner profile (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "owner_id": {
        "type": "integer"
      },
      "add_tags": {
        "type": "array",
        "items": {"type": "string"}
      },
      "remove_tags": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "required": ["owner_id"]
  }
}
```

```json
{
  "name": "get_customer_insights",
  "description": "Get customer analytics and insights (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "insight_type": {
        "type": "string",
        "enum": ["top_customers", "at_risk", "new_customers", "ltv_distribution", "acquisition_sources"]
      },
      "date_range": {
        "type": "string",
        "enum": ["30d", "90d", "1y", "all"]
      },
      "limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": ["insight_type"]
  }
}
```

```json
{
  "name": "get_segment",
  "description": "Get customers matching segment criteria (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "segment_id": {
        "type": "integer"
      },
      "criteria": {
        "type": "object",
        "description": "Custom criteria for ad-hoc segment"
      }
    },
    "required": []
  }
}
```

### Loyalty Program Tools (S-016)

```json
{
  "name": "get_loyalty_status",
  "description": "Get user's loyalty program status",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer",
        "description": "Required for staff, auto for customer"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_points_balance",
  "description": "Get current points balance and history",
  "parameters": {
    "type": "object",
    "properties": {
      "include_history": {
        "type": "boolean",
        "default": false
      },
      "history_limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_available_rewards",
  "description": "Get rewards available for redemption",
  "parameters": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string",
        "enum": ["discount", "product", "service", "all"]
      },
      "affordable_only": {
        "type": "boolean",
        "default": true,
        "description": "Only show rewards user can afford"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "redeem_reward",
  "description": "Redeem points for a reward",
  "parameters": {
    "type": "object",
    "properties": {
      "reward_id": {
        "type": "integer"
      }
    },
    "required": ["reward_id"]
  }
}
```

```json
{
  "name": "get_tier_benefits",
  "description": "Get benefits for a loyalty tier",
  "parameters": {
    "type": "object",
    "properties": {
      "tier": {
        "type": "string",
        "enum": ["bronze", "silver", "gold", "platinum"]
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_referral_code",
  "description": "Get user's referral code and stats",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

```json
{
  "name": "apply_referral_code",
  "description": "Apply a referral code to new account",
  "parameters": {
    "type": "object",
    "properties": {
      "referral_code": {
        "type": "string"
      }
    },
    "required": ["referral_code"]
  }
}
```

```json
{
  "name": "add_points",
  "description": "Add points to user's account (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "integer"
      },
      "points": {
        "type": "integer"
      },
      "reason": {
        "type": "string"
      },
      "related_order_id": {
        "type": "integer"
      }
    },
    "required": ["user_id", "points", "reason"]
  }
}
```

---

## Module 7: Billing & Invoicing (S-020)

### Customer Billing Tools

```json
{
  "name": "get_invoice",
  "description": "Get invoice details",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_id": {
        "type": "integer"
      }
    },
    "required": ["invoice_id"]
  }
}
```

```json
{
  "name": "get_my_invoices",
  "description": "Get user's invoices",
  "parameters": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": ["pending", "paid", "overdue", "all"]
      },
      "limit": {
        "type": "integer",
        "default": 10
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_account_balance",
  "description": "Get user's account credit balance",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

```json
{
  "name": "get_payment_methods",
  "description": "Get user's saved payment methods",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### Staff Billing Tools

```json
{
  "name": "create_invoice",
  "description": "Create an invoice (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "owner_id": {
        "type": "integer"
      },
      "pet_id": {
        "type": "integer"
      },
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "description": {"type": "string"},
            "quantity": {"type": "number"},
            "unit_price": {"type": "number"},
            "service_id": {"type": "integer"},
            "product_id": {"type": "integer"}
          }
        }
      },
      "due_date": {
        "type": "string",
        "format": "date"
      },
      "apply_discounts": {
        "type": "boolean",
        "default": true
      }
    },
    "required": ["owner_id", "items"]
  }
}
```

```json
{
  "name": "record_payment",
  "description": "Record a payment against an invoice (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_id": {
        "type": "integer"
      },
      "amount": {
        "type": "number"
      },
      "payment_method": {
        "type": "string",
        "enum": ["cash", "card", "stripe", "account_credit"]
      },
      "reference": {
        "type": "string"
      }
    },
    "required": ["invoice_id", "amount", "payment_method"]
  }
}
```

```json
{
  "name": "generate_cfdi",
  "description": "Generate CFDI (Mexican tax invoice) (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_id": {
        "type": "integer"
      },
      "rfc": {
        "type": "string",
        "description": "Customer's RFC (tax ID)"
      },
      "uso_cfdi": {
        "type": "string",
        "default": "G03"
      }
    },
    "required": ["invoice_id"]
  }
}
```

```json
{
  "name": "send_payment_reminder",
  "description": "Send payment reminder for overdue invoice (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_id": {
        "type": "integer"
      },
      "channel": {
        "type": "string",
        "enum": ["email", "sms", "whatsapp", "auto"]
      }
    },
    "required": ["invoice_id"]
  }
}
```

```json
{
  "name": "get_overdue_invoices",
  "description": "Get all overdue invoices (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "days_overdue": {
        "type": "integer",
        "default": 1
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "apply_discount",
  "description": "Apply discount to invoice (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_id": {
        "type": "integer"
      },
      "discount_type": {
        "type": "string",
        "enum": ["percent", "fixed"]
      },
      "discount_value": {
        "type": "number"
      },
      "reason": {
        "type": "string"
      }
    },
    "required": ["invoice_id", "discount_type", "discount_value"]
  }
}
```

```json
{
  "name": "get_b2b_account_status",
  "description": "Get professional/B2B account status (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "account_id": {
        "type": "integer"
      }
    },
    "required": ["account_id"]
  }
}
```

---

## Module 8: Reports & Analytics (S-017)

### Report Tools

```json
{
  "name": "get_dashboard_summary",
  "description": "Get dashboard summary with KPIs (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "date_range": {
        "type": "string",
        "enum": ["today", "week", "month", "quarter", "year"]
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "query_analytics",
  "description": "Query analytics using natural language (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language query like 'revenue this month' or 'top selling products'"
      }
    },
    "required": ["query"]
  }
}
```

```json
{
  "name": "get_revenue_report",
  "description": "Get revenue report (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "format": "date"
      },
      "end_date": {
        "type": "string",
        "format": "date"
      },
      "group_by": {
        "type": "string",
        "enum": ["day", "week", "month"]
      },
      "breakdown_by": {
        "type": "string",
        "enum": ["service", "product", "category", "none"]
      }
    },
    "required": ["start_date", "end_date"]
  }
}
```

```json
{
  "name": "get_appointment_analytics",
  "description": "Get appointment analytics (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "format": "date"
      },
      "end_date": {
        "type": "string",
        "format": "date"
      },
      "include_no_shows": {
        "type": "boolean",
        "default": true
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "compare_periods",
  "description": "Compare metrics between two periods (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "metric": {
        "type": "string",
        "enum": ["revenue", "appointments", "new_customers", "orders"]
      },
      "period1_start": {
        "type": "string",
        "format": "date"
      },
      "period1_end": {
        "type": "string",
        "format": "date"
      },
      "period2_start": {
        "type": "string",
        "format": "date"
      },
      "period2_end": {
        "type": "string",
        "format": "date"
      }
    },
    "required": ["metric", "period1_start", "period1_end", "period2_start", "period2_end"]
  }
}
```

```json
{
  "name": "forecast_metric",
  "description": "Forecast future metric values (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "metric": {
        "type": "string",
        "enum": ["revenue", "appointments", "inventory_needs"]
      },
      "periods_ahead": {
        "type": "integer",
        "default": 3
      }
    },
    "required": ["metric"]
  }
}
```

```json
{
  "name": "generate_report",
  "description": "Generate a predefined report (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "report_type": {
        "type": "string",
        "enum": ["daily_summary", "weekly_summary", "monthly_summary", "inventory", "customer_ltv", "service_performance"]
      },
      "date_range": {
        "type": "string"
      },
      "format": {
        "type": "string",
        "enum": ["json", "pdf", "excel"],
        "default": "json"
      }
    },
    "required": ["report_type"]
  }
}
```

---

## Module 9: Accounting (S-026)

### Accounting Tools

```json
{
  "name": "get_account_balance_accounting",
  "description": "Get balance for an accounting account (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "account_id": {
        "type": "integer"
      },
      "account_code": {
        "type": "string"
      },
      "as_of_date": {
        "type": "string",
        "format": "date"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_financial_statement",
  "description": "Get financial statement (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "statement_type": {
        "type": "string",
        "enum": ["profit_loss", "balance_sheet", "cash_flow"]
      },
      "start_date": {
        "type": "string",
        "format": "date"
      },
      "end_date": {
        "type": "string",
        "format": "date"
      },
      "compare_to_prior": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["statement_type", "start_date", "end_date"]
  }
}
```

```json
{
  "name": "get_ar_aging",
  "description": "Get accounts receivable aging report (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "as_of_date": {
        "type": "string",
        "format": "date"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "get_ap_aging",
  "description": "Get accounts payable aging report (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "as_of_date": {
        "type": "string",
        "format": "date"
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "record_bill",
  "description": "Record a vendor bill (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "vendor_id": {
        "type": "integer"
      },
      "bill_number": {
        "type": "string"
      },
      "bill_date": {
        "type": "string",
        "format": "date"
      },
      "due_date": {
        "type": "string",
        "format": "date"
      },
      "items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "description": {"type": "string"},
            "amount": {"type": "number"},
            "expense_account_id": {"type": "integer"}
          }
        }
      }
    },
    "required": ["vendor_id", "bill_date", "items"]
  }
}
```

```json
{
  "name": "pay_bill",
  "description": "Record payment for a vendor bill (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "bill_id": {
        "type": "integer"
      },
      "amount": {
        "type": "number"
      },
      "payment_method": {
        "type": "string",
        "enum": ["check", "transfer", "cash", "card"]
      },
      "bank_account_id": {
        "type": "integer"
      },
      "reference": {
        "type": "string"
      }
    },
    "required": ["bill_id", "amount", "payment_method", "bank_account_id"]
  }
}
```

```json
{
  "name": "create_journal_entry",
  "description": "Create manual journal entry (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "format": "date"
      },
      "reference": {
        "type": "string"
      },
      "description": {
        "type": "string"
      },
      "lines": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "account_id": {"type": "integer"},
            "debit": {"type": "number"},
            "credit": {"type": "number"},
            "description": {"type": "string"}
          }
        }
      }
    },
    "required": ["date", "lines"]
  }
}
```

```json
{
  "name": "reconcile_bank",
  "description": "Start or continue bank reconciliation (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "bank_account_id": {
        "type": "integer"
      },
      "statement_date": {
        "type": "string",
        "format": "date"
      },
      "statement_balance": {
        "type": "number"
      }
    },
    "required": ["bank_account_id", "statement_date", "statement_balance"]
  }
}
```

```json
{
  "name": "get_budget_variance",
  "description": "Get budget vs actual variance report (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "year": {
        "type": "integer"
      },
      "month": {
        "type": "integer"
      },
      "account_type": {
        "type": "string",
        "enum": ["revenue", "expense", "all"]
      }
    },
    "required": ["year"]
  }
}
```

---

## Additional Specialized Tools

### Emergency Services (S-015)

```json
{
  "name": "assess_emergency",
  "description": "AI-assisted emergency triage assessment",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "symptoms": {
        "type": "array",
        "items": {"type": "string"}
      },
      "description": {
        "type": "string"
      },
      "onset": {
        "type": "string",
        "enum": ["just_now", "hours", "days"]
      }
    },
    "required": ["symptoms", "description"]
  }
}
```

```json
{
  "name": "get_emergency_contact",
  "description": "Get emergency contact information",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### Pharmacy (S-010)

```json
{
  "name": "get_pet_prescriptions",
  "description": "Get active prescriptions for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "include_expired": {
        "type": "boolean",
        "default": false
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "request_refill",
  "description": "Request a prescription refill",
  "parameters": {
    "type": "object",
    "properties": {
      "prescription_id": {
        "type": "integer"
      },
      "notes": {
        "type": "string"
      }
    },
    "required": ["prescription_id"]
  }
}
```

```json
{
  "name": "check_drug_interactions",
  "description": "Check for drug interactions (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "new_medication": {
        "type": "string"
      }
    },
    "required": ["pet_id", "new_medication"]
  }
}
```

### Referral Network (S-025)

```json
{
  "name": "find_specialist",
  "description": "Find a specialist for referral",
  "parameters": {
    "type": "object",
    "properties": {
      "specialty": {
        "type": "string",
        "enum": ["oncology", "cardiology", "orthopedics", "ophthalmology", "dermatology", "neurology", "emergency"]
      },
      "location": {
        "type": "string"
      }
    },
    "required": ["specialty"]
  }
}
```

```json
{
  "name": "get_visiting_schedule",
  "description": "Get visiting specialist schedule",
  "parameters": {
    "type": "object",
    "properties": {
      "specialty": {
        "type": "string"
      },
      "date_range_days": {
        "type": "integer",
        "default": 30
      }
    },
    "required": []
  }
}
```

```json
{
  "name": "create_referral",
  "description": "Create a referral to specialist (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "specialist_id": {
        "type": "integer"
      },
      "reason": {
        "type": "string"
      },
      "urgency": {
        "type": "string",
        "enum": ["routine", "soon", "urgent"]
      },
      "include_records": {
        "type": "boolean",
        "default": true
      }
    },
    "required": ["pet_id", "specialist_id", "reason"]
  }
}
```

### Competitive Intelligence (S-009)

```json
{
  "name": "get_competitor_info",
  "description": "Get information about local competitors (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "competitor_id": {
        "type": "integer"
      }
    },
    "required": ["competitor_id"]
  }
}
```

```json
{
  "name": "compare_pricing",
  "description": "Compare pricing with competitors (admin only)",
  "permission": "admin",
  "parameters": {
    "type": "object",
    "properties": {
      "service_type": {
        "type": "string"
      }
    },
    "required": ["service_type"]
  }
}
```

### Document Management (S-013)

```json
{
  "name": "upload_document",
  "description": "Upload a document for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "document_type": {
        "type": "string",
        "enum": ["lab_result", "xray", "certificate", "vaccination_card", "other"]
      },
      "title": {
        "type": "string"
      },
      "file_url": {
        "type": "string"
      }
    },
    "required": ["pet_id", "document_type", "title", "file_url"]
  }
}
```

```json
{
  "name": "get_pet_documents",
  "description": "Get documents for a pet",
  "parameters": {
    "type": "object",
    "properties": {
      "pet_id": {
        "type": "integer"
      },
      "document_type": {
        "type": "string"
      }
    },
    "required": ["pet_id"]
  }
}
```

```json
{
  "name": "process_document_ocr",
  "description": "Extract data from uploaded document using OCR/Vision (staff only)",
  "permission": "staff",
  "parameters": {
    "type": "object",
    "properties": {
      "document_id": {
        "type": "integer"
      },
      "extraction_type": {
        "type": "string",
        "enum": ["vaccination_card", "lab_result", "prescription", "auto"]
      }
    },
    "required": ["document_id"]
  }
}
```

---

## Tool Registration

All tools are registered in the AI service layer:

```python
# ai_service/tools/__init__.py

from .core import CORE_TOOLS
from .vet_clinic import VET_CLINIC_TOOLS
from .appointments import APPOINTMENT_TOOLS
from .store import STORE_TOOLS
from .communications import COMMUNICATION_TOOLS
from .crm import CRM_TOOLS
from .billing import BILLING_TOOLS
from .reports import REPORT_TOOLS
from .accounting import ACCOUNTING_TOOLS
from .pharmacy import PHARMACY_TOOLS
from .emergency import EMERGENCY_TOOLS
from .referral import REFERRAL_TOOLS
from .documents import DOCUMENT_TOOLS

ALL_TOOLS = {
    **CORE_TOOLS,
    **VET_CLINIC_TOOLS,
    **APPOINTMENT_TOOLS,
    **STORE_TOOLS,
    **COMMUNICATION_TOOLS,
    **CRM_TOOLS,
    **BILLING_TOOLS,
    **REPORT_TOOLS,
    **ACCOUNTING_TOOLS,
    **PHARMACY_TOOLS,
    **EMERGENCY_TOOLS,
    **REFERRAL_TOOLS,
    **DOCUMENT_TOOLS,
}

def get_tools_for_user(user):
    """Return tools available based on user permissions."""
    available = []
    for tool in ALL_TOOLS.values():
        permission = tool.get('permission', 'public')
        if permission == 'public':
            available.append(tool)
        elif permission == 'customer' and user.is_authenticated:
            available.append(tool)
        elif permission == 'staff' and user.is_staff:
            available.append(tool)
        elif permission == 'admin' and user.is_superuser:
            available.append(tool)
    return available
```

---

## Summary

| Module | Customer Tools | Staff Tools | Admin Tools | Total |
|--------|---------------|-------------|-------------|-------|
| Core (S-001, S-002) | 4 | 0 | 0 | 4 |
| Vet Clinic (S-003, S-022) | 12 | 5 | 0 | 17 |
| Appointments (S-004) | 5 | 5 | 0 | 10 |
| Store/Inventory (S-005, S-024) | 11 | 7 | 1 | 19 |
| Communications (S-006, S-012) | 3 | 6 | 0 | 9 |
| CRM/Loyalty (S-007, S-016) | 7 | 5 | 2 | 14 |
| Billing (S-020) | 4 | 7 | 0 | 11 |
| Reports (S-017) | 0 | 2 | 5 | 7 |
| Accounting (S-026) | 0 | 0 | 9 | 9 |
| Emergency (S-015) | 2 | 0 | 0 | 2 |
| Pharmacy (S-010) | 2 | 1 | 0 | 3 |
| Referral (S-025) | 2 | 1 | 0 | 3 |
| Documents (S-013) | 2 | 1 | 0 | 3 |
| Competitive Intel (S-009) | 0 | 0 | 2 | 2 |
| **TOTAL** | **54** | **40** | **19** | **113** |

*Note: Some tools have dual permissions (customer can use with own data, staff can use with any data)*

---

*Last Updated: December 21, 2025*
