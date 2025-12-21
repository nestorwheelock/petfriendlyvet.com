# S-017: Reports & Analytics

**Story Type:** User Story
**Priority:** Medium
**Epoch:** 6 (with Practice Management)
**Status:** PENDING
**Module:** django-vet-clinic + django-ai-assistant

## User Story

**As a** clinic owner
**I want to** see comprehensive business reports
**So that** I can make data-driven decisions

**As a** clinic owner
**I want to** ask questions about my business in natural language
**So that** I can get insights without navigating complex dashboards

**As a** practice manager
**I want to** track key performance indicators
**So that** I can monitor clinic health and trends

## Acceptance Criteria

### Dashboard Overview
- [ ] Daily/weekly/monthly summary at a glance
- [ ] Key metrics with trend indicators
- [ ] Comparison to previous periods
- [ ] Goal tracking and progress
- [ ] Real-time data updates

### Revenue Reports
- [ ] Revenue by time period
- [ ] Revenue by service type
- [ ] Revenue by product category
- [ ] Payment method breakdown
- [ ] Outstanding balances and collections
- [ ] Revenue forecasting

### Appointment Analytics
- [ ] Appointment volume trends
- [ ] Booking lead time
- [ ] No-show rate
- [ ] Cancellation analysis
- [ ] Popular time slots
- [ ] Service type distribution
- [ ] Vet utilization rate

### Client Analytics
- [ ] New vs returning clients
- [ ] Client acquisition sources
- [ ] Client retention rate
- [ ] Client lifetime value
- [ ] Geographic distribution
- [ ] Pet species breakdown

### Product/Inventory Reports
- [ ] Best-selling products
- [ ] Inventory turnover
- [ ] Low stock alerts
- [ ] Category performance
- [ ] Margin analysis

### AI-Powered Insights
- [ ] Natural language queries
- [ ] Trend explanations
- [ ] Anomaly detection
- [ ] Predictive analytics
- [ ] Actionable recommendations

### Export & Scheduling
- [ ] Export to PDF, Excel, CSV
- [ ] Scheduled report emails
- [ ] Custom report builder
- [ ] Report templates

## Technical Requirements

### Models

```python
class ReportDefinition(models.Model):
    """Saved/custom report definitions"""
    REPORT_TYPES = [
        ('revenue', 'Revenue Report'),
        ('appointments', 'Appointment Report'),
        ('clients', 'Client Report'),
        ('inventory', 'Inventory Report'),
        ('marketing', 'Marketing Report'),
        ('custom', 'Custom Report'),
    ]

    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)

    # Configuration
    metrics = models.JSONField(default=list)
    # ["revenue", "appointment_count", "avg_ticket", ...]
    dimensions = models.JSONField(default=list)
    # ["date", "service_type", "staff_member", ...]
    filters = models.JSONField(default=dict)
    # {"date_range": "last_30_days", "service_type": "consultation"}

    # Visualization
    chart_type = models.CharField(max_length=50, default='table')
    # table, bar, line, pie, area
    visualization_options = models.JSONField(default=dict)

    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule = models.CharField(max_length=50, blank=True)
    # daily, weekly, monthly
    recipients = models.JSONField(default=list)  # Email list

    # Access
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)  # Visible to all staff

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReportExecution(models.Model):
    """Report execution history"""
    report = models.ForeignKey(
        ReportDefinition, on_delete=models.CASCADE, null=True, blank=True
    )
    report_type = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict)

    # Execution
    executed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    execution_time_ms = models.IntegerField()
    row_count = models.IntegerField()

    # Result
    result_summary = models.JSONField(default=dict)
    # Cached key metrics for quick display

    # Export
    export_file = models.FileField(upload_to='reports/', null=True, blank=True)
    export_format = models.CharField(max_length=10, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class DailyMetrics(models.Model):
    """Pre-aggregated daily metrics for fast querying"""
    date = models.DateField(unique=True)

    # Revenue
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    product_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pharmacy_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Appointments
    appointments_booked = models.IntegerField(default=0)
    appointments_completed = models.IntegerField(default=0)
    appointments_cancelled = models.IntegerField(default=0)
    appointments_no_show = models.IntegerField(default=0)
    new_appointments_online = models.IntegerField(default=0)

    # Clients
    new_clients = models.IntegerField(default=0)
    returning_clients = models.IntegerField(default=0)
    new_pets_registered = models.IntegerField(default=0)

    # Products
    products_sold = models.IntegerField(default=0)
    orders_placed = models.IntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Communications
    messages_received = models.IntegerField(default=0)
    messages_sent = models.IntegerField(default=0)
    ai_conversations = models.IntegerField(default=0)
    ai_escalations = models.IntegerField(default=0)

    # Website
    website_visits = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)

    # Reviews
    reviews_received = models.IntegerField(default=0)
    average_rating = models.FloatField(null=True)

    updated_at = models.DateTimeField(auto_now=True)


class KPIGoal(models.Model):
    """Key Performance Indicator goals"""
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    metric = models.CharField(max_length=50)
    # revenue, appointments, new_clients, etc.
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    target_value = models.DecimalField(max_digits=12, decimal_places=2)

    # Thresholds for display
    warning_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.9)
    # Below 90% = warning
    critical_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.75)
    # Below 75% = critical

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class AnalyticsInsight(models.Model):
    """AI-generated insights"""
    INSIGHT_TYPES = [
        ('trend', 'Trend Identified'),
        ('anomaly', 'Anomaly Detected'),
        ('opportunity', 'Opportunity'),
        ('warning', 'Warning'),
        ('achievement', 'Achievement'),
    ]

    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    metric = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField()
    recommendation = models.TextField(blank=True)

    # Data
    data_points = models.JSONField(default=dict)
    comparison_period = models.CharField(max_length=50, blank=True)
    change_percentage = models.FloatField(null=True)

    # Validity
    valid_from = models.DateField()
    valid_until = models.DateField()

    # Priority
    priority = models.CharField(max_length=20, default='medium')
    is_actionable = models.BooleanField(default=True)

    # Status
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class ScheduledReport(models.Model):
    """Scheduled report deliveries"""
    report = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE)

    # Schedule
    frequency = models.CharField(max_length=20)
    # daily, weekly, monthly
    day_of_week = models.IntegerField(null=True, blank=True)  # 0=Monday
    day_of_month = models.IntegerField(null=True, blank=True)
    time = models.TimeField()
    timezone = models.CharField(max_length=50, default='America/Cancun')

    # Delivery
    recipients = models.JSONField(default=list)
    format = models.CharField(max_length=10, default='pdf')
    include_comparison = models.BooleanField(default=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
```

### AI Tools

```python
ANALYTICS_TOOLS = [
    {
        "name": "get_dashboard_summary",
        "description": "Get overview dashboard metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "default": "today"}
            }
        }
    },
    {
        "name": "query_analytics",
        "description": "Query analytics with natural language",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "get_revenue_report",
        "description": "Get detailed revenue report",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "group_by": {"type": "string"},
                "breakdown": {"type": "string"}
            }
        }
    },
    {
        "name": "get_appointment_analytics",
        "description": "Get appointment analytics",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "include_forecast": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "get_client_analytics",
        "description": "Get client/pet analytics",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string"},
                "metrics": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    {
        "name": "compare_periods",
        "description": "Compare metrics between two periods",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string"},
                "period1": {"type": "string"},
                "period2": {"type": "string"}
            },
            "required": ["metric", "period1", "period2"]
        }
    },
    {
        "name": "get_insights",
        "description": "Get AI-generated insights",
        "parameters": {
            "type": "object",
            "properties": {
                "insight_type": {"type": "string"},
                "limit": {"type": "integer", "default": 5}
            }
        }
    },
    {
        "name": "generate_report",
        "description": "Generate and export a report",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {"type": "string"},
                "parameters": {"type": "object"},
                "format": {"type": "string", "enum": ["pdf", "excel", "csv"]}
            },
            "required": ["report_type"]
        }
    },
    {
        "name": "set_kpi_goal",
        "description": "Set or update a KPI goal",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string"},
                "period": {"type": "string"},
                "target": {"type": "number"}
            },
            "required": ["metric", "period", "target"]
        }
    },
    {
        "name": "forecast_metric",
        "description": "Forecast a metric based on historical data",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string"},
                "periods_ahead": {"type": "integer", "default": 3}
            },
            "required": ["metric"]
        }
    }
]
```

## Example AI Conversations

### Daily Summary
```
Dr. Pablo: How did we do today?

AI: Here's your daily summary for Friday, January 24, 2025:

    💰 Revenue: $12,450 MXN
    ├── Services: $7,200 (58%)
    ├── Products: $3,850 (31%)
    └── Pharmacy: $1,400 (11%)

    📈 vs Last Friday: +18%
    📈 vs Daily Goal: 104% ✓

    📅 Appointments: 8 completed
    ├── Consultations: 4
    ├── Vaccinations: 3
    └── Surgery: 1
    No-shows: 0 🎉

    👥 Clients Today: 8
    ├── New: 2
    └── Returning: 6

    ⭐ Reviews: 2 new (both 5-star!)

    🔔 Alerts:
    • Low stock: Frontline Plus (3 remaining)
    • 2 appointments pending confirmation for Monday

    Great day! Revenue exceeded your goal.
```

### Natural Language Query
```
Dr. Pablo: What were our busiest days last month?

AI: Here are the busiest days in December 2024 by
    appointment volume:

    | Date | Day | Appointments | Revenue |
    |------|-----|--------------|---------|
    | Dec 21 | Sat | 14 | $18,200 |
    | Dec 14 | Sat | 12 | $15,400 |
    | Dec 7  | Sat | 11 | $14,100 |
    | Dec 18 | Wed | 10 | $12,800 |
    | Dec 23 | Mon | 10 | $11,500 |

    Pattern Detected:
    Saturdays are consistently your busiest days,
    averaging 11.5 appointments vs 7.2 on weekdays.

    💡 Insight: Consider adding Saturday capacity or
    incentivizing weekday appointments to balance load.

    Would you like me to analyze a specific day or
    compare to November?
```

### Trend Analysis
```
Dr. Pablo: Are we getting more new clients?

AI: Let me analyze your client acquisition trends:

    📊 New Client Trend (Last 6 Months)

    Month    | New Clients | Change
    ---------|-------------|--------
    Jul 2024 | 18          | -
    Aug 2024 | 22          | +22%
    Sep 2024 | 19          | -14%
    Oct 2024 | 25          | +32%
    Nov 2024 | 31          | +24%
    Dec 2024 | 38          | +23%

    📈 Overall Trend: Strong growth (+111% since July)

    🔍 Analysis:
    Your new client growth accelerated after launching
    the website in September. The AI chat feature has
    directly led to 23 new client conversions.

    Acquisition Sources (December):
    • Website/AI Chat: 15 (39%)
    • Referrals: 12 (32%)
    • Walk-ins: 8 (21%)
    • Google Search: 3 (8%)

    💡 Recommendation:
    Your referral program is strong. Consider increasing
    the referral bonus to accelerate growth further.
```

### Revenue Forecast
```
Dr. Pablo: What's our revenue forecast for next month?

AI: Revenue Forecast for February 2025:

    📊 Projected Revenue: $285,000 - $315,000 MXN

    Based on:
    • Historical February performance
    • Current booking pipeline
    • Seasonal trends
    • Growth trajectory

    Breakdown by Category:
    | Category | Forecast | Confidence |
    |----------|----------|------------|
    | Services | $165,000 | High |
    | Products | $95,000  | Medium |
    | Pharmacy | $45,000  | High |

    📅 February Factors:
    ✓ Valentine's grooming boost expected
    ⚠️ 3 fewer working days than January
    ✓ Vaccination campaign scheduled

    Compared to February 2024: +42% projected

    📈 To reach $320,000:
    • Need 15% more product sales
    • Or 2 additional surgeries
    • Or 10% increase in average ticket

    Would you like specific strategies to maximize
    February revenue?
```

### Comparative Analysis
```
Dr. Pablo: Compare this quarter to last quarter

AI: Q4 2024 vs Q3 2024 Comparison:

    | Metric | Q3 2024 | Q4 2024 | Change |
    |--------|---------|---------|--------|
    | Revenue | $680K | $845K | +24% 📈 |
    | Appointments | 312 | 398 | +28% 📈 |
    | New Clients | 66 | 94 | +42% 📈 |
    | Products Sold | 423 | 612 | +45% 📈 |
    | Avg Rating | 4.6 | 4.8 | +0.2 📈 |
    | No-Show Rate | 8% | 5% | -3% 📈 |

    🏆 Key Wins:
    1. Revenue broke $800K first time ever
    2. Online booking reduced no-shows
    3. E-commerce sales exceeded target

    ⚠️ Areas to Watch:
    1. Pharmacy margin decreased 3%
    2. Wednesday utilization still low
    3. Emergency after-hours increasing

    🔮 If Q4 trends continue:
    Projected 2025 revenue: $3.6M - $3.9M MXN

    Would you like a detailed breakdown of any metric?
```

## Dashboard Widgets

### Key Metrics
- Revenue (today, MTD, YTD)
- Appointments (today, this week)
- New clients (this month)
- Average rating
- Revenue vs goal

### Charts
- Revenue trend (line)
- Appointments by type (pie)
- Revenue by category (bar)
- Client acquisition (funnel)
- Appointment heatmap (by day/hour)

### Alerts
- Below-target KPIs
- Low inventory
- Unconfirmed appointments
- Pending reviews

## Definition of Done

- [ ] Dashboard with key metrics
- [ ] Revenue reporting
- [ ] Appointment analytics
- [ ] Client analytics
- [ ] Natural language queries
- [ ] Trend analysis
- [ ] AI-generated insights
- [ ] Report generation (PDF, Excel)
- [ ] Scheduled reports
- [ ] KPI goal tracking
- [ ] Period comparisons
- [ ] Forecasting
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- All previous stories (aggregates data from all)
- S-008: Practice Management (staff metrics)

## Notes

- Pre-aggregate daily metrics for performance
- Consider data warehouse for complex queries
- Mobile-friendly dashboard essential
- Real-time updates for key metrics
- Consider integration with Google Analytics
- Celery for async report generation
