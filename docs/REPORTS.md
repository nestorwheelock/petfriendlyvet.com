# Reports Module

The `apps.reports` module provides business intelligence capabilities including report definitions, generated reports, dashboards, scheduled delivery, and metric tracking.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [ReportDefinition](#reportdefinition)
  - [GeneratedReport](#generatedreport)
  - [Dashboard](#dashboard)
  - [DashboardWidget](#dashboardwidget)
  - [ScheduledReport](#scheduledreport)
  - [MetricSnapshot](#metricsnapshot)
- [Workflows](#workflows)
  - [Creating Report Definitions](#creating-report-definitions)
  - [Generating Reports](#generating-reports)
  - [Building Dashboards](#building-dashboards)
  - [Scheduling Reports](#scheduling-reports)
  - [Tracking Metrics](#tracking-metrics)
- [Report Types](#report-types)
- [Widget Types](#widget-types)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The reports module provides comprehensive business intelligence:

- **Report Definitions** - Reusable report templates
- **Generated Reports** - Report instances with data and exports
- **Dashboards** - Customizable visual dashboards
- **Dashboard Widgets** - Charts, metrics, tables, calendars
- **Scheduled Reports** - Automated report delivery
- **Metric Snapshots** - Historical metric tracking

```
┌─────────────────────────────────────────────────────────────┐
│                   REPORTS ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              ReportDefinition                        │   │
│   │     (template with query config, filters, columns)   │   │
│   └─────────────────────────┬───────────────────────────┘   │
│                             │                                │
│         ┌───────────────────┼───────────────────┐           │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐      │
│   │ Generated │      │ Scheduled │      │  Manual   │      │
│   │  Report   │      │  Report   │      │  Export   │      │
│   └───────────┘      └───────────┘      └───────────┘      │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                   Dashboard                          │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│   │  │ Widget  │ │ Widget  │ │ Widget  │ │ Widget  │   │   │
│   │  │ (chart) │ │(metric) │ │ (table) │ │ (list)  │   │   │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              MetricSnapshot                          │   │
│   │         (daily historical values)                    │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Models

Location: `apps/reports/models.py`

### ReportDefinition

Saved report templates with query configuration.

```python
REPORT_TYPES = [
    ('financial', 'Financial'),
    ('operational', 'Operational'),
    ('clinical', 'Clinical'),
    ('inventory', 'Inventory'),
    ('marketing', 'Marketing'),
    ('custom', 'Custom'),
]

class ReportDefinition(models.Model):
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)

    # Configuration
    query_config = models.JSONField(default=dict)  # Query parameters
    filters = models.JSONField(default=dict)        # Available filters
    columns = models.JSONField(default=list)        # Column definitions
    grouping = models.JSONField(default=list)       # Grouping options

    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)  # Shared with all users

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `query_config` | JSONField | Query parameters and data sources |
| `filters` | JSONField | Available filter options |
| `columns` | JSONField | Column definitions with formatting |
| `grouping` | JSONField | Grouping/aggregation options |
| `is_public` | Boolean | Visible to all staff users |

### GeneratedReport

Instances of generated reports.

```python
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

class GeneratedReport(models.Model):
    definition = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name='generated_reports')

    # Period
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    data = models.JSONField(default=dict)      # Report data
    summary = models.JSONField(default=dict)   # Summary statistics

    # Export file
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    file_format = models.CharField(max_length=10, blank=True)  # pdf, xlsx, csv

    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    error_message = models.TextField(blank=True)  # If failed
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `data` | JSONField | Raw report data |
| `summary` | JSONField | Aggregated statistics |
| `file` | FileField | Exported file (PDF, Excel, CSV) |
| `status` | CharField | Processing status |

### Dashboard

Customizable dashboard configurations.

```python
class Dashboard(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')

    layout = models.JSONField(default=dict)    # Grid layout configuration
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `layout` | JSONField | Grid layout configuration |
| `is_default` | Boolean | User's default dashboard |
| `is_public` | Boolean | Visible to all staff |

### DashboardWidget

Individual dashboard widgets.

```python
WIDGET_TYPES = [
    ('chart', 'Chart'),
    ('metric', 'Single Metric'),
    ('table', 'Data Table'),
    ('list', 'List'),
    ('calendar', 'Calendar'),
    ('map', 'Map'),
]

class DashboardWidget(models.Model):
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')

    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=200)
    config = models.JSONField(default=dict)  # Widget-specific configuration

    # Layout
    position = models.IntegerField(default=0)
    width = models.IntegerField(default=1)   # Grid columns
    height = models.IntegerField(default=1)  # Grid rows

    refresh_interval = models.IntegerField(default=0)  # Seconds, 0 = no auto-refresh
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `config` | JSONField | Widget-specific settings (data source, colors, etc.) |
| `position` | Integer | Order in dashboard |
| `width` / `height` | Integer | Grid size |
| `refresh_interval` | Integer | Auto-refresh in seconds |

### ScheduledReport

Automated report delivery configuration.

```python
FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
]

class ScheduledReport(models.Model):
    definition = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name='schedules')

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.IntegerField(null=True, blank=True)   # 0-6 for weekly
    day_of_month = models.IntegerField(null=True, blank=True)  # 1-31 for monthly
    hour = models.IntegerField(default=8)  # Hour to run (0-23)

    recipients = models.JSONField(default=list)  # Email addresses
    file_format = models.CharField(max_length=10, default='pdf')

    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `frequency` | CharField | How often to run |
| `day_of_week` | Integer | Day for weekly (0=Monday) |
| `day_of_month` | Integer | Day for monthly |
| `recipients` | JSONField | List of email addresses |

### MetricSnapshot

Daily metric snapshots for trend analysis.

```python
class MetricSnapshot(models.Model):
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()

    metadata = models.JSONField(default=dict)  # Additional context
    source = models.CharField(max_length=50, blank=True)  # Data source

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['metric_name', 'date']
        indexes = [
            models.Index(fields=['metric_name', 'date']),
        ]
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `metric_name` | CharField | Metric identifier |
| `metric_value` | Decimal | Value for the date |
| `metadata` | JSONField | Additional context data |

## Workflows

### Creating Report Definitions

```python
from apps.reports.models import ReportDefinition

# Create financial report definition
report_def = ReportDefinition.objects.create(
    name='Monthly Revenue Report',
    report_type='financial',
    description='Monthly breakdown of revenue by service category',
    query_config={
        'model': 'billing.Invoice',
        'aggregations': ['total', 'count'],
        'date_field': 'created_at',
    },
    filters={
        'date_range': {'type': 'daterange', 'required': True},
        'status': {'type': 'choice', 'choices': ['paid', 'pending']},
    },
    columns=[
        {'field': 'category', 'label': 'Category', 'format': 'text'},
        {'field': 'total', 'label': 'Revenue', 'format': 'currency'},
        {'field': 'count', 'label': 'Invoices', 'format': 'number'},
    ],
    grouping=['category', 'week'],
    is_public=True,
    created_by=admin_user,
)
```

### Generating Reports

```python
from apps.reports.models import ReportDefinition, GeneratedReport
from datetime import date

# Generate report from definition
definition = ReportDefinition.objects.get(name='Monthly Revenue Report')

report = GeneratedReport.objects.create(
    definition=definition,
    period_start=date(2025, 12, 1),
    period_end=date(2025, 12, 31),
    status='processing',
    generated_by=staff_user,
)

# Run report generation (async task)
try:
    data = generate_report_data(definition, report.period_start, report.period_end)
    summary = calculate_summary(data)

    report.data = data
    report.summary = summary
    report.status = 'completed'
    report.save()
except Exception as e:
    report.status = 'failed'
    report.error_message = str(e)
    report.save()
```

### Building Dashboards

```python
from apps.reports.models import Dashboard, DashboardWidget

# Create dashboard
dashboard = Dashboard.objects.create(
    name='Operations Overview',
    description='Daily operations metrics',
    owner=staff_user,
    layout={
        'columns': 4,
        'rows': 'auto',
    },
    is_default=True,
)

# Add widgets
DashboardWidget.objects.create(
    dashboard=dashboard,
    widget_type='metric',
    title='Today\'s Appointments',
    config={
        'query': 'appointments.today.count',
        'color': 'blue',
        'icon': 'calendar',
    },
    position=0,
    width=1,
    height=1,
)

DashboardWidget.objects.create(
    dashboard=dashboard,
    widget_type='chart',
    title='Weekly Revenue',
    config={
        'chart_type': 'line',
        'query': 'billing.revenue.weekly',
        'period': 'last_7_days',
    },
    position=1,
    width=2,
    height=2,
)

DashboardWidget.objects.create(
    dashboard=dashboard,
    widget_type='table',
    title='Recent Orders',
    config={
        'query': 'store.orders.recent',
        'limit': 10,
        'columns': ['order_number', 'customer', 'total', 'status'],
    },
    position=3,
    width=2,
    height=2,
    refresh_interval=60,  # Refresh every minute
)
```

### Scheduling Reports

```python
from apps.reports.models import ScheduledReport
from datetime import datetime, timedelta

# Schedule weekly report
schedule = ScheduledReport.objects.create(
    definition=report_def,
    frequency='weekly',
    day_of_week=0,  # Monday
    hour=8,         # 8 AM
    recipients=['manager@clinic.com', 'owner@clinic.com'],
    file_format='pdf',
    is_active=True,
    next_run=calculate_next_run_date(),
)

# Monthly report on 1st of month
schedule = ScheduledReport.objects.create(
    definition=inventory_report,
    frequency='monthly',
    day_of_month=1,
    hour=6,
    recipients=['inventory@clinic.com'],
    file_format='xlsx',
)
```

### Tracking Metrics

```python
from apps.reports.models import MetricSnapshot
from datetime import date

# Record daily metrics
MetricSnapshot.objects.create(
    metric_name='daily_revenue',
    metric_value=Decimal('15000.00'),
    date=date.today(),
    source='billing',
)

MetricSnapshot.objects.create(
    metric_name='appointments_completed',
    metric_value=Decimal('25'),
    date=date.today(),
    source='appointments',
)

MetricSnapshot.objects.create(
    metric_name='new_customers',
    metric_value=Decimal('5'),
    date=date.today(),
    metadata={'source_breakdown': {'website': 3, 'referral': 2}},
    source='crm',
)
```

## Report Types

| Type | Description | Example Reports |
|------|-------------|-----------------|
| `financial` | Revenue, expenses, payments | Monthly Revenue, Outstanding Invoices |
| `operational` | Day-to-day operations | Appointments Summary, Staff Utilization |
| `clinical` | Medical and health data | Vaccination Status, Treatment Outcomes |
| `inventory` | Stock and supplies | Stock Levels, Expiring Items |
| `marketing` | Customer acquisition, campaigns | Email Campaign Results, Referral Sources |
| `custom` | User-defined reports | Custom queries and aggregations |

## Widget Types

| Type | Description | Use Cases |
|------|-------------|-----------|
| `chart` | Line, bar, pie charts | Trends, comparisons, distributions |
| `metric` | Single value display | KPIs, counts, totals |
| `table` | Data table | Lists, detailed records |
| `list` | Simple list | Recent items, tasks |
| `calendar` | Calendar view | Appointments, schedules |
| `map` | Geographic map | Delivery zones, customer locations |

## Integration Points

### With Billing Module

```python
from apps.reports.models import MetricSnapshot, GeneratedReport
from apps.billing.models import Invoice
from django.db.models import Sum
from datetime import date

# Daily revenue snapshot
revenue = Invoice.objects.filter(
    created_at__date=date.today(),
    status='paid'
).aggregate(total=Sum('total'))['total'] or 0

MetricSnapshot.objects.create(
    metric_name='daily_revenue',
    metric_value=revenue,
    date=date.today(),
    source='billing',
)
```

### With Appointments Module

```python
from apps.reports.models import MetricSnapshot
from apps.appointments.models import Appointment
from datetime import date

# Daily appointments metrics
today = date.today()
MetricSnapshot.objects.create(
    metric_name='appointments_scheduled',
    metric_value=Appointment.objects.filter(date=today).count(),
    date=today,
    source='appointments',
)
```

### With Inventory Module

```python
from apps.reports.models import MetricSnapshot
from apps.inventory.models import StockBatch
from datetime import date, timedelta

# Low stock alert count
low_stock = StockBatch.objects.filter(
    quantity__lte=F('reorder_level')
).count()

MetricSnapshot.objects.create(
    metric_name='low_stock_items',
    metric_value=low_stock,
    date=date.today(),
    source='inventory',
)
```

## Query Examples

### Report Definition Queries

```python
from apps.reports.models import ReportDefinition

# Public reports
public = ReportDefinition.objects.filter(is_active=True, is_public=True)

# Reports by type
financial = ReportDefinition.objects.filter(report_type='financial', is_active=True)

# User's reports (own + public)
from django.db.models import Q
user_reports = ReportDefinition.objects.filter(
    Q(created_by=user) | Q(is_public=True),
    is_active=True
)
```

### Generated Report Queries

```python
from apps.reports.models import GeneratedReport
from datetime import timedelta
from django.utils import timezone

# Recent reports
recent = GeneratedReport.objects.filter(
    generated_at__gte=timezone.now() - timedelta(days=7)
).select_related('definition', 'generated_by')

# Failed reports
failed = GeneratedReport.objects.filter(status='failed')

# Reports by definition
definition_reports = GeneratedReport.objects.filter(
    definition=definition
).order_by('-generated_at')
```

### Metric Snapshot Queries

```python
from apps.reports.models import MetricSnapshot
from datetime import date, timedelta
from django.db.models import Avg, Max, Min

# Last 30 days of revenue
revenue_trend = MetricSnapshot.objects.filter(
    metric_name='daily_revenue',
    date__gte=date.today() - timedelta(days=30)
).order_by('date')

# Average daily revenue
avg_revenue = MetricSnapshot.objects.filter(
    metric_name='daily_revenue',
    date__gte=date.today() - timedelta(days=30)
).aggregate(
    avg=Avg('metric_value'),
    max=Max('metric_value'),
    min=Min('metric_value')
)

# Compare metrics across periods
this_month = MetricSnapshot.objects.filter(
    metric_name='appointments_completed',
    date__month=date.today().month
).aggregate(total=Sum('metric_value'))

last_month = MetricSnapshot.objects.filter(
    metric_name='appointments_completed',
    date__month=date.today().month - 1
).aggregate(total=Sum('metric_value'))
```

### Dashboard Queries

```python
from apps.reports.models import Dashboard, DashboardWidget

# User's default dashboard
default = Dashboard.objects.filter(
    owner=user,
    is_default=True
).prefetch_related('widgets').first()

# Visible widgets
visible_widgets = DashboardWidget.objects.filter(
    dashboard=dashboard,
    is_visible=True
).order_by('position')

# Auto-refresh widgets
auto_refresh = DashboardWidget.objects.filter(
    dashboard=dashboard,
    refresh_interval__gt=0
)
```

### Scheduled Report Queries

```python
from apps.reports.models import ScheduledReport
from django.utils import timezone

# Due for execution
due_now = ScheduledReport.objects.filter(
    is_active=True,
    next_run__lte=timezone.now()
)

# Weekly reports
weekly = ScheduledReport.objects.filter(frequency='weekly', is_active=True)

# Reports for a definition
definition_schedules = ScheduledReport.objects.filter(definition=definition)
```

## Testing

### Unit Tests

Location: `tests/test_reports.py`

```bash
# Run reports unit tests
python -m pytest tests/test_reports.py -v
```

### Key Test Scenarios

1. **Report Definitions**
   - Create report definition
   - Configure query, filters, columns
   - Public vs private visibility

2. **Report Generation**
   - Generate from definition
   - Handle processing states
   - Store data and summary
   - Export to file

3. **Dashboards**
   - Create dashboard
   - Add/remove widgets
   - Configure layout
   - Default dashboard

4. **Widgets**
   - Different widget types
   - Configuration options
   - Positioning and sizing
   - Auto-refresh

5. **Scheduled Reports**
   - Schedule creation
   - Frequency calculations
   - Next run calculation
   - Recipient management

6. **Metric Snapshots**
   - Daily recording
   - Trend queries
   - Unique constraint (metric + date)
