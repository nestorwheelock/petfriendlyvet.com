# EPOCH: Delivery Management Module

**Version**: v2.0.0 (Delivery Epoch)
**Status**: IN PROGRESS
**Start Date**: 2024-12-24
**Priority**: High

---

## Overview

Comprehensive delivery management system for the veterinary practice store, enabling:
- Delivery tracking with proof of delivery (photos + GPS)
- Driver management (employees and contractors)
- Customer delivery scheduling
- Route optimization for drivers
- Integration with accounting (A/P for contractors)

---

## Scope

### IN SCOPE

**Phase 1: Core Infrastructure**
- StoreSettings singleton model (configurable shipping cost, tax)
- Delivery app with 8 core models
- Admin interfaces
- Basic checkout integration

**Phase 2: Driver Experience**
- Driver mobile dashboard with map
- Route optimization (all stops on map)
- Status update API with GPS
- Proof of delivery (photo + browser GPS)
- External navigation links

**Phase 3: Customer Experience**
- Slot selection in checkout
- Real-time tracking page
- Notification integration
- Rating system

**Phase 4: Operations & Admin**
- Admin dashboard with live map
- Auto-assignment logic
- Reports and analytics
- Zone/slot management UI

**Phase 5: Contractor Management**
- Contractor onboarding (RFC/CURP, contracts)
- Rate configuration (per delivery, per km)
- Vendor creation in accounting
- Contractor payment reports

### OUT OF SCOPE
- Real-time driver location tracking (future enhancement)
- Multiple warehouse support
- Cross-city deliveries
- Third-party delivery integrations (DoorDash, etc.)

---

## User Stories

| ID | Story | Priority | Phase |
|----|-------|----------|-------|
| S-027 | Delivery Module Core | High | 1 |
| S-028 | Driver Mobile Experience | High | 2 |
| S-029 | Customer Delivery Tracking | Medium | 3 |
| S-030 | Delivery Operations Dashboard | Medium | 4 |
| S-031 | Contractor Driver Management | Medium | 5 |

---

## Task Breakdown

### Phase 1: Core Infrastructure (Current)

| Task | Description | Status |
|------|-------------|--------|
| T-066 | Create StoreSettings model with tests | Pending |
| T-067 | Create delivery app structure | Pending |
| T-068 | Implement DeliveryZone and DeliverySlot models | Pending |
| T-069 | Implement DeliveryDriver model | Pending |
| T-070 | Implement Delivery model and status workflow | Pending |
| T-071 | Implement supporting models (Proof, Rating, etc.) | Pending |
| T-072 | Create admin interfaces | Pending |
| T-073 | Integrate checkout with StoreSettings | Pending |

### Phase 2: Driver Experience

| Task | Description | Status |
|------|-------------|--------|
| T-074 | Driver dashboard views and API | Pending |
| T-075 | Map integration with route display | Pending |
| T-076 | Status update API with GPS | Pending |
| T-077 | Proof of delivery upload (photo + GPS) | Pending |
| T-078 | External navigation links | Pending |

### Phase 3-5: (To be detailed when Phase 2 completes)

---

## Data Models

### Core Models

```
StoreSettings (singleton)
├── default_shipping_cost
├── free_shipping_threshold
├── tax_rate
└── default_max_order_quantity

DeliveryZone
├── code, name
├── delivery_fee
└── estimated_time_minutes

DeliverySlot
├── date, start_time, end_time
├── zone (FK)
└── capacity, booked_count

DeliveryDriver
├── user, phone
├── driver_type (employee/contractor)
├── staff_profile (FK, for employees)
├── vendor (FK, for contractors)
├── rfc, curp (Mexican tax IDs)
├── rate_per_delivery, rate_per_km
├── vehicle_type, license_plate
└── is_active, is_available

Delivery
├── delivery_number
├── order (OneToOne)
├── driver, slot, zone
├── status (state machine)
├── address, latitude, longitude
├── scheduled_date, scheduled_time
└── status timestamps

DeliveryStatusHistory
├── delivery (FK)
├── from_status, to_status
└── changed_by, latitude, longitude

DeliveryProof
├── delivery (FK)
├── proof_type (photo/signature)
├── image, signature_data
├── recipient_name
└── latitude, longitude

DeliveryRating
├── delivery (FK)
├── rating (1-5)
└── feedback

DeliveryNotification
├── delivery (FK)
├── notification_type
├── sent_at
└── channel (sms/whatsapp/email)
```

### Status Flow

```
pending → assigned → picked_up → out_for_delivery → arrived → delivered
                                                           ↘ failed → returned
```

---

## Integration Points

1. **Order Model**: Create Delivery when order.fulfillment_method='delivery'
2. **Communications**: Trigger notifications on status changes
3. **Practice App**: Link drivers to StaffProfile for employees
4. **Accounting A/P**: Contractors linked to Vendor model

---

## Acceptance Criteria

### StoreSettings
- [ ] Singleton model enforced (pk=1)
- [ ] Admin interface for configuration
- [ ] Used by Order creation and checkout template

### Delivery Module
- [ ] Delivery created when order placed with delivery
- [ ] Customer can select slot during checkout
- [ ] Driver can update status from mobile
- [ ] Proof of delivery with photo and GPS
- [ ] Customer tracking page with timeline
- [ ] Status change notifications
- [ ] Admin assignment and dashboard
- [ ] Rating system works
- [ ] >95% test coverage

---

## TDD Requirements

All tasks MUST follow the TDD Stop Gate:
1. Read task documentation
2. Write failing tests FIRST
3. Run pytest and show failures
4. Write minimal code to pass
5. Run pytest and show passes
6. Git commit and push

See: [TDD_STOP_GATE.md](TDD_STOP_GATE.md)
