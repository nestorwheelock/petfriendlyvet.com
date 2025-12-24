# Delivery Module Testing Guide

## Quick Start

### 1. Start the Development Environment

```bash
docker compose up -d
```

### 2. Apply Migrations

```bash
docker compose exec web python manage.py migrate
```

### 3. Create Sample Data

```bash
docker compose exec web python manage.py populate_delivery_data --clear
```

This creates:
- 6 delivery zones (CDMX areas)
- 21 delivery slots (7 days x 3 slots per day)
- 4 drivers (2 employees, 2 contractors)

### 4. Access the Admin

- URL: http://localhost:7777/admin/
- Username: `devadmin`
- Password: `admin123`

---

## API Endpoints Reference

### Admin APIs (Staff Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/delivery/admin/deliveries/` | List all deliveries with filters |
| GET | `/api/delivery/admin/drivers/` | List all active drivers |
| POST | `/api/delivery/admin/assign/{id}/` | Assign driver to delivery |
| GET | `/api/delivery/admin/reports/` | Get delivery reports |
| GET | `/api/delivery/admin/reports/driver/{id}/` | Get driver-specific report |
| GET/POST/PUT/DELETE | `/api/delivery/admin/zones/` | CRUD for zones |
| GET/PUT/DELETE | `/api/delivery/admin/zones/{id}/` | Single zone operations |
| GET/POST | `/api/delivery/admin/slots/` | List/create slots |
| GET/PUT/DELETE | `/api/delivery/admin/slots/{id}/` | Single slot operations |
| POST | `/api/delivery/admin/slots/bulk/` | Bulk create slots |
| GET/POST | `/api/delivery/admin/contractors/` | List/create contractors |
| GET/PUT | `/api/delivery/admin/contractors/{id}/` | Update contractor |
| POST | `/api/delivery/admin/contractors/validate-rfc/` | Validate RFC |
| POST | `/api/delivery/admin/contractors/validate-curp/` | Validate CURP |
| GET | `/api/delivery/admin/contractors/payments/` | Payment summary |
| GET | `/api/delivery/admin/contractors/{id}/payments/` | Contractor payment detail |

### Driver APIs (Authenticated Drivers)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/driver/` | Get driver profile |
| PUT | `/api/driver/` | Update driver profile |
| GET | `/api/driver/deliveries/` | Get assigned deliveries |
| POST | `/api/driver/deliveries/{id}/status/` | Update delivery status |
| POST | `/api/driver/deliveries/{id}/proof/` | Upload proof of delivery |

### Customer APIs (Authenticated Customers)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/delivery/track/{delivery_number}/` | Track delivery |
| GET/POST | `/api/delivery/rate/{delivery_number}/` | Get/submit rating |
| GET | `/api/delivery/zones/` | Get available zones |
| GET | `/api/delivery/slots/` | Get available slots |

---

## Test Scenarios

### Scenario 1: Complete Delivery Lifecycle

1. **Create Order with Delivery**
   - Login as customer
   - Add items to cart
   - Select delivery as fulfillment method
   - Complete checkout

2. **Admin Assigns Driver**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/admin/assign/1/ \
     -H "Content-Type: application/json" \
     -d '{"driver_id": 1}'
   ```

3. **Driver Updates Status**
   ```bash
   # Picked up
   curl -X POST http://localhost:7777/api/driver/deliveries/1/status/ \
     -H "Content-Type: application/json" \
     -d '{"status": "picked_up", "latitude": "19.432608", "longitude": "-99.133209"}'

   # Out for delivery
   curl -X POST http://localhost:7777/api/driver/deliveries/1/status/ \
     -H "Content-Type: application/json" \
     -d '{"status": "out_for_delivery"}'

   # Arrived
   curl -X POST http://localhost:7777/api/driver/deliveries/1/status/ \
     -H "Content-Type: application/json" \
     -d '{"status": "arrived"}'

   # Delivered
   curl -X POST http://localhost:7777/api/driver/deliveries/1/status/ \
     -H "Content-Type: application/json" \
     -d '{"status": "delivered"}'
   ```

4. **Customer Rates Delivery**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/rate/DEL-2025-00001/ \
     -H "Content-Type: application/json" \
     -d '{"rating": 5, "comment": "Excelente servicio!"}'
   ```

### Scenario 2: Zone Management

1. **Create Zone**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/admin/zones/ \
     -H "Content-Type: application/json" \
     -d '{
       "code": "CDMX-TEST",
       "name": "Test Zone",
       "description": "Test zone for QA",
       "delivery_fee": "65.00",
       "estimated_minutes": 35
     }'
   ```

2. **Update Zone**
   ```bash
   curl -X PUT http://localhost:7777/api/delivery/admin/zones/1/ \
     -H "Content-Type: application/json" \
     -d '{"delivery_fee": "70.00"}'
   ```

3. **Delete Zone**
   ```bash
   curl -X DELETE http://localhost:7777/api/delivery/admin/zones/1/
   ```

### Scenario 3: Slot Management

1. **Create Single Slot**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/admin/slots/ \
     -H "Content-Type: application/json" \
     -d '{
       "date": "2025-12-30",
       "start_time": "09:00:00",
       "end_time": "12:00:00",
       "max_deliveries": 10
     }'
   ```

2. **Bulk Create Slots**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/admin/slots/bulk/ \
     -H "Content-Type: application/json" \
     -d '{
       "start_date": "2025-12-30",
       "end_date": "2026-01-05",
       "slots": [
         {"start_time": "09:00", "end_time": "12:00", "max_deliveries": 10},
         {"start_time": "12:00", "end_time": "15:00", "max_deliveries": 10},
         {"start_time": "15:00", "end_time": "18:00", "max_deliveries": 8}
       ]
     }'
   ```

### Scenario 4: Contractor Onboarding

1. **Create Contractor**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/admin/contractors/ \
     -H "Content-Type: application/json" \
     -d '{
       "username": "nuevo_contratista",
       "first_name": "Pedro",
       "last_name": "Gonzalez",
       "email": "pedro@example.com",
       "phone": "555-1234",
       "vehicle_type": "motorcycle",
       "vehicle_plate": "ABC-999",
       "rfc": "GOPD900101AAA",
       "curp": "GOPD900101HDFRDR00",
       "rate_per_delivery": "40.00",
       "rate_per_km": "6.00",
       "zone_ids": [1, 2, 3]
     }'
   ```

2. **Validate RFC**
   ```bash
   curl -X POST http://localhost:7777/api/delivery/admin/contractors/validate-rfc/ \
     -H "Content-Type: application/json" \
     -d '{"rfc": "GOPD900101AAA"}'
   ```

3. **View Contractor Payments**
   ```bash
   curl http://localhost:7777/api/delivery/admin/contractors/payments/?start_date=2025-12-01&end_date=2025-12-31
   ```

### Scenario 5: Failed Delivery & Reschedule

1. **Mark Delivery as Failed**
   ```bash
   curl -X POST http://localhost:7777/api/driver/deliveries/1/status/ \
     -H "Content-Type: application/json" \
     -d '{"status": "failed", "reason": "Customer not available"}'
   ```

2. **Reschedule (assign new slot and driver)**
   ```bash
   curl -X PUT http://localhost:7777/api/delivery/admin/deliveries/1/reschedule/ \
     -H "Content-Type: application/json" \
     -d '{"slot_id": 5, "driver_id": 2}'
   ```

---

## Running Tests

### All Delivery Tests

```bash
python -m pytest apps/delivery/tests.py -v
```

### E2E Tests Only

```bash
python -m pytest apps/delivery/tests.py -k "E2E or EdgeCase" -v
```

### Specific Test Class

```bash
python -m pytest apps/delivery/tests.py::DeliveryLifecycleE2ETests -v
```

### With Coverage

```bash
python -m pytest apps/delivery/tests.py --cov=apps/delivery --cov-report=html -v
```

---

## Test Users

| Username | Password | Role |
|----------|----------|------|
| devadmin | admin123 | Admin/Staff |
| driver_carlos | driver123 | Employee Driver |
| driver_maria | driver123 | Employee Driver |
| driver_contractor1 | driver123 | Contractor Driver |
| driver_contractor2 | driver123 | Contractor Driver |

---

## Status Flow

```
pending → assigned → picked_up → out_for_delivery → arrived → delivered
                                                           ↘ failed → returned
                                                                    ↘ assigned (reschedule)
```

## Valid Transitions

| From | To |
|------|----|
| pending | assigned |
| assigned | picked_up, pending |
| picked_up | out_for_delivery |
| out_for_delivery | arrived, failed |
| arrived | delivered, failed |
| failed | returned, assigned |
| returned | (terminal) |
| delivered | (terminal) |
