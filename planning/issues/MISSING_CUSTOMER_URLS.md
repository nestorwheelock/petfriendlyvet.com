# Missing Customer-Facing URLs - QA Discovery

**Discovered By**: Playwright browser tests
**Date**: 2025-12-25
**Priority**: High - Core functionality missing

## Summary

Browser E2E tests revealed that several apps only have Django admin interfaces but no customer-facing views. Users cannot access loyalty programs, emergency info, inventory status, or referral information through the frontend.

---

## Issue 1: Loyalty App Missing Customer URLs

**App**: `apps/loyalty`
**Current State**: Models exist, admin works, no customer views
**Impact**: Customers cannot view their points, redeem rewards, or see tier benefits

### Required URLs
| URL | View | Description |
|-----|------|-------------|
| `/loyalty/` | `dashboard` | Points balance, current tier, recent activity |
| `/loyalty/rewards/` | `rewards_catalog` | Available rewards to redeem |
| `/loyalty/history/` | `transaction_history` | Points earned/spent history |
| `/loyalty/tiers/` | `tier_benefits` | All tiers and their benefits |
| `/loyalty/referrals/` | `referral_program` | Referral link, stats, pending referrals |

### Files to Create
- `apps/loyalty/urls.py`
- `apps/loyalty/views.py`
- `templates/loyalty/dashboard.html`
- `templates/loyalty/rewards.html`
- `templates/loyalty/history.html`
- `templates/loyalty/tiers.html`
- `templates/loyalty/referrals.html`

---

## Issue 2: Emergency App Missing Customer URLs

**App**: `apps/emergency`
**Current State**: Models exist, admin works, no public views
**Impact**: Pet owners cannot find emergency contact info or report emergencies online

### Required URLs
| URL | View | Description |
|-----|------|-------------|
| `/emergency/` | `emergency_info` | Emergency phone, hours, what to do |
| `/emergency/contact/` | `emergency_contact_form` | Report symptoms, request callback |
| `/emergency/triage/` | `triage_questionnaire` | Self-triage questions |
| `/emergency/hospitals/` | `referral_hospitals` | 24-hour hospitals nearby |

### Files to Create
- `apps/emergency/urls.py`
- `apps/emergency/views.py`
- `templates/emergency/info.html`
- `templates/emergency/contact_form.html`
- `templates/emergency/triage.html`
- `templates/emergency/hospitals.html`

---

## Issue 3: Inventory App Missing Staff URLs

**App**: `apps/inventory`
**Current State**: Models exist, admin works, no staff dashboard
**Impact**: Staff must use admin for all inventory tasks (slow, not optimized)

### Required URLs (Staff-facing)
| URL | View | Description |
|-----|------|-------------|
| `/inventory/` | `dashboard` | Stock overview, alerts |
| `/inventory/alerts/` | `low_stock_alerts` | Items below reorder point |
| `/inventory/purchase-orders/` | `po_list` | Purchase orders |
| `/inventory/batches/` | `batch_list` | Stock batches |
| `/inventory/expiring/` | `expiring_soon` | Batches expiring soon |
| `/inventory/movements/` | `movement_log` | Stock movement history |
| `/inventory/suppliers/` | `supplier_list` | Supplier directory |

### Files to Create
- `apps/inventory/urls.py`
- `apps/inventory/views.py`
- `templates/inventory/dashboard.html`
- `templates/inventory/alerts.html`
- `templates/inventory/purchase_orders.html`
- `templates/inventory/batches.html`
- `templates/inventory/expiring.html`
- `templates/inventory/movements.html`
- `templates/inventory/suppliers.html`

---

## Issue 4: Referrals App Missing URLs

**App**: `apps/referrals`
**Current State**: Models exist, admin works, no views
**Impact**: Staff cannot manage referrals efficiently, specialists have no portal

### Required URLs
| URL | View | Description |
|-----|------|-------------|
| `/referrals/` | `referral_list` | All referrals |
| `/referrals/pending/` | `pending_referrals` | Awaiting action |
| `/referrals/create/` | `create_referral` | New referral form |
| `/referrals/specialists/` | `specialist_directory` | Find specialists |
| `/referrals/inbound/` | `inbound_referrals` | Referrals TO us |
| `/referrals/<id>/` | `referral_detail` | Single referral |

### Files to Create
- `apps/referrals/urls.py`
- `apps/referrals/views.py`
- `templates/referrals/list.html`
- `templates/referrals/pending.html`
- `templates/referrals/create.html`
- `templates/referrals/specialists.html`
- `templates/referrals/inbound.html`
- `templates/referrals/detail.html`

---

## Issue 5: Practice App Empty URLs

**App**: `apps/practice`
**Current State**: urls.py exists but empty, models exist
**Impact**: Staff have no dashboard, time tracking, or task management UI

### Required URLs
| URL | View | Description |
|-----|------|-------------|
| `/staff/dashboard/` | `staff_dashboard` | Today's schedule, tasks |
| `/staff/schedule/` | `schedule_view` | Shift calendar |
| `/staff/timeclock/` | `time_clock` | Clock in/out |
| `/staff/timesheet/` | `timesheet` | Hours worked |
| `/staff/tasks/` | `task_list` | Assigned tasks |

### Files to Create
- Update `apps/practice/urls.py`
- `apps/practice/views.py`
- `templates/practice/dashboard.html`
- `templates/practice/schedule.html`
- `templates/practice/timeclock.html`
- `templates/practice/timesheet.html`
- `templates/practice/tasks.html`

---

## Recommended Implementation Order

1. **Emergency** (Critical - safety) - See [T-074](../tasks/T-074-emergency-customer-urls.md)
2. **Loyalty** (High - customer engagement) - See [T-075](../tasks/T-075-loyalty-customer-urls.md)
3. **Inventory** (High - operations) - See [T-076](../tasks/T-076-inventory-staff-urls.md)
4. **Practice/Staff** (Medium - internal efficiency) - See [T-077](../tasks/T-077-practice-staff-urls.md)
5. **Referrals** (Medium - specialist workflow) - See [T-078](../tasks/T-078-referrals-urls.md)

---

## Test Coverage Status

Once URLs are implemented, the following browser tests will validate them:
- `tests/e2e/browser/test_loyalty.py`
- `tests/e2e/browser/test_emergency.py`
- `tests/e2e/browser/test_inventory.py`
- `tests/e2e/browser/test_referrals.py`
- `tests/e2e/browser/test_staff_management.py`

Currently these tests are configured to test admin pages only (workaround until customer URLs exist).
