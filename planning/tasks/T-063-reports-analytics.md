# T-063: Reports & Analytics Dashboard

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement comprehensive reporting and analytics system
**Related Story**: S-017
**Epoch**: 6
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/reports/, templates/admin/reports/
**Forbidden Paths**: None

### Deliverables
- [ ] Report models
- [ ] Revenue reports
- [ ] Patient statistics
- [ ] Inventory reports
- [ ] Staff performance
- [ ] Export functionality
- [ ] Dashboard visualizations

### Wireframe Reference
See: `planning/wireframes/21-reports-dashboard.txt`

### Implementation Details

#### Models
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Report(models.Model):
    """Generated report records."""

    REPORT_TYPES = [
        ('revenue', 'Ingresos'),
        ('appointments', 'Citas'),
        ('patients', 'Pacientes'),
        ('inventory', 'Inventario'),
        ('staff', 'Personal'),
        ('marketing', 'Marketing'),
        ('custom', 'Personalizado'),
    ]
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    name = models.CharField(max_length=200)

    # Period
    period_start = models.DateField()
    period_end = models.DateField()

    # Parameters
    parameters = models.JSONField(default=dict)
    # {"group_by": "day", "include_cancelled": false, ...}

    # Results
    data = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)

    # Files
    pdf_file = models.FileField(
        upload_to='reports/', null=True, blank=True
    )
    csv_file = models.FileField(
        upload_to='reports/', null=True, blank=True
    )
    excel_file = models.FileField(
        upload_to='reports/', null=True, blank=True
    )

    # Metadata
    generated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    generation_time_ms = models.IntegerField(null=True)

    class Meta:
        ordering = ['-generated_at']


class ScheduledReport(models.Model):
    """Scheduled automatic reports."""

    report_type = models.CharField(max_length=20)
    name = models.CharField(max_length=200)

    # Schedule
    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
    ]
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    day_of_week = models.IntegerField(null=True)  # 0-6 for weekly
    day_of_month = models.IntegerField(null=True)  # 1-31 for monthly
    time_of_day = models.TimeField(default='08:00')

    # Parameters
    parameters = models.JSONField(default=dict)

    # Recipients
    email_recipients = models.JSONField(default=list)
    send_to_admins = models.BooleanField(default=True)

    # Export format
    export_format = models.CharField(max_length=10, default='pdf')
    # pdf, csv, excel

    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True)
    next_run = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class DashboardWidget(models.Model):
    """Configurable dashboard widgets."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    WIDGET_TYPES = [
        ('metric', 'Métrica'),
        ('chart', 'Gráfico'),
        ('table', 'Tabla'),
        ('list', 'Lista'),
    ]
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)

    # Data source
    data_source = models.CharField(max_length=100)
    # revenue_today, appointments_week, top_services, etc.

    # Display
    chart_type = models.CharField(max_length=20, blank=True)
    # line, bar, pie, donut
    display_options = models.JSONField(default=dict)

    # Position
    order = models.IntegerField(default=0)
    column_span = models.IntegerField(default=1)  # 1-4

    is_active = models.BooleanField(default=True)
```

#### Report Services
```python
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from decimal import Decimal


class ReportService:
    """Generate various reports."""

    def revenue_report(
        self,
        start_date,
        end_date,
        group_by: str = 'day'
    ) -> dict:
        """Generate revenue report."""

        from apps.billing.models import Invoice, Payment

        # Invoices in period
        invoices = Invoice.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status__in=['paid', 'partial']
        )

        # Group by period
        if group_by == 'day':
            trunc_func = TruncDate('created_at')
        elif group_by == 'week':
            trunc_func = TruncWeek('created_at')
        else:
            trunc_func = TruncMonth('created_at')

        revenue_by_period = invoices.annotate(
            period=trunc_func
        ).values('period').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('period')

        # Revenue by payment method
        payments = Payment.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        by_method = payments.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )

        # Revenue by service category
        from apps.billing.models import InvoiceLineItem

        by_service = InvoiceLineItem.objects.filter(
            invoice__in=invoices,
            service__isnull=False
        ).values(
            'service__category__name'
        ).annotate(
            total=Sum('line_total'),
            count=Count('id')
        )

        # Summary
        summary = {
            'total_revenue': invoices.aggregate(Sum('total'))['total__sum'] or 0,
            'invoice_count': invoices.count(),
            'average_invoice': invoices.aggregate(Avg('total'))['total__avg'] or 0,
            'outstanding': Invoice.objects.filter(
                status__in=['sent', 'partial', 'overdue']
            ).aggregate(
                total=Sum(F('total') - F('amount_paid'))
            )['total'] or 0
        }

        return {
            'revenue_by_period': list(revenue_by_period),
            'by_payment_method': list(by_method),
            'by_service': list(by_service),
            'summary': summary
        }

    def appointment_report(
        self,
        start_date,
        end_date
    ) -> dict:
        """Generate appointment statistics report."""

        from apps.appointments.models import Appointment

        appointments = Appointment.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        # By status
        by_status = appointments.values('status').annotate(
            count=Count('id')
        )

        # By service type
        by_service = appointments.values(
            'service_type__name'
        ).annotate(
            count=Count('id'),
            revenue=Sum('invoice__total')
        ).order_by('-count')

        # By day of week
        by_day = appointments.annotate(
            day=F('date__week_day')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        # By hour
        by_hour = appointments.annotate(
            hour=F('start_time__hour')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        # Staff utilization
        from apps.staff.models import StaffAssignment

        staff_stats = StaffAssignment.objects.filter(
            appointment__in=appointments
        ).values(
            'staff__user__first_name',
            'staff__user__last_name'
        ).annotate(
            appointments=Count('id'),
            revenue=Sum('appointment__invoice__total')
        ).order_by('-appointments')

        # No-show rate
        total = appointments.count()
        no_shows = appointments.filter(status='no_show').count()
        no_show_rate = (no_shows / total * 100) if total > 0 else 0

        summary = {
            'total_appointments': total,
            'completed': appointments.filter(status='completed').count(),
            'cancelled': appointments.filter(status='cancelled').count(),
            'no_shows': no_shows,
            'no_show_rate': round(no_show_rate, 1),
            'average_per_day': round(total / max((end_date - start_date).days, 1), 1)
        }

        return {
            'by_status': list(by_status),
            'by_service': list(by_service),
            'by_day': list(by_day),
            'by_hour': list(by_hour),
            'staff_stats': list(staff_stats),
            'summary': summary
        }

    def patient_report(
        self,
        start_date,
        end_date
    ) -> dict:
        """Generate patient statistics report."""

        from apps.vet_clinic.models import Pet

        # New patients
        new_pets = Pet.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        by_species = new_pets.values('species').annotate(
            count=Count('id')
        )

        # Active patients (visited in period)
        from apps.appointments.models import Appointment

        active_pet_ids = Appointment.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            status='completed'
        ).values_list('pet_id', flat=True).distinct()

        # Returning vs new
        returning = Appointment.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            pet__created_at__date__lt=start_date
        ).values('pet_id').distinct().count()

        # Vaccination compliance
        from apps.vet_clinic.models import VaccinationRecord

        due_vaccinations = VaccinationRecord.objects.filter(
            next_due_date__lte=end_date,
            next_due_date__gte=start_date
        ).count()

        completed_vaccinations = VaccinationRecord.objects.filter(
            administered_date__gte=start_date,
            administered_date__lte=end_date
        ).count()

        summary = {
            'new_patients': new_pets.count(),
            'active_patients': len(active_pet_ids),
            'returning_patients': returning,
            'total_patients': Pet.objects.filter(is_active=True).count(),
            'vaccinations_due': due_vaccinations,
            'vaccinations_given': completed_vaccinations
        }

        return {
            'new_by_species': list(by_species),
            'summary': summary
        }

    def inventory_report(self, as_of_date=None) -> dict:
        """Generate inventory report."""

        from apps.store.models import Product, StockLevel, StockBatch

        if not as_of_date:
            as_of_date = timezone.now().date()

        # Low stock items
        low_stock = Product.objects.filter(
            is_active=True,
            stock_levels__quantity__lte=F('reorder_point')
        ).distinct()

        # Expiring soon (30 days)
        expiring = StockBatch.objects.filter(
            expiry_date__lte=as_of_date + timedelta(days=30),
            expiry_date__gt=as_of_date,
            quantity__gt=0
        ).select_related('product')

        # Stock value
        stock_value = StockLevel.objects.aggregate(
            total_value=Sum(F('quantity') * F('product__cost_price')),
            total_retail=Sum(F('quantity') * F('product__price'))
        )

        # Top sellers
        from apps.billing.models import InvoiceLineItem

        top_products = InvoiceLineItem.objects.filter(
            product__isnull=False,
            invoice__created_at__date__gte=as_of_date - timedelta(days=30)
        ).values(
            'product__name'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('line_total')
        ).order_by('-revenue')[:10]

        # Dead stock (no movement in 90 days)
        from apps.store.models import StockMovement

        recent_movement = StockMovement.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=90)
        ).values_list('product_id', flat=True).distinct()

        dead_stock = Product.objects.filter(
            is_active=True,
            stock_levels__quantity__gt=0
        ).exclude(id__in=recent_movement)

        summary = {
            'total_products': Product.objects.filter(is_active=True).count(),
            'low_stock_count': low_stock.count(),
            'expiring_count': expiring.count(),
            'dead_stock_count': dead_stock.count(),
            'stock_value': stock_value['total_value'] or 0,
            'retail_value': stock_value['total_retail'] or 0
        }

        return {
            'low_stock': list(low_stock.values('name', 'sku', 'stock_levels__quantity')[:20]),
            'expiring': list(expiring.values('product__name', 'expiry_date', 'quantity')[:20]),
            'top_products': list(top_products),
            'summary': summary
        }


class DashboardService:
    """Generate dashboard widget data."""

    def get_widget_data(self, widget: DashboardWidget) -> dict:
        """Get data for a dashboard widget."""

        method_name = f"_get_{widget.data_source}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        return {}

    def _get_revenue_today(self) -> dict:
        from apps.billing.models import Payment
        today = timezone.now().date()

        total = Payment.objects.filter(
            created_at__date=today
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        yesterday = Payment.objects.filter(
            created_at__date=today - timedelta(days=1)
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        change = ((total - yesterday) / yesterday * 100) if yesterday else 0

        return {
            'value': float(total),
            'change': round(change, 1),
            'label': 'Ingresos Hoy'
        }

    def _get_appointments_today(self) -> dict:
        from apps.appointments.models import Appointment
        today = timezone.now().date()

        total = Appointment.objects.filter(date=today).count()
        completed = Appointment.objects.filter(
            date=today, status='completed'
        ).count()
        pending = Appointment.objects.filter(
            date=today, status__in=['confirmed', 'in_progress']
        ).count()

        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'label': 'Citas Hoy'
        }

    def _get_revenue_chart(self) -> dict:
        """Last 30 days revenue chart."""
        from apps.billing.models import Payment

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        data = Payment.objects.filter(
            created_at__date__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Sum('amount')
        ).order_by('date')

        return {
            'labels': [d['date'].strftime('%d/%m') for d in data],
            'values': [float(d['total']) for d in data],
            'label': 'Ingresos (30 días)'
        }
```

#### Report Views
```python
class ReportsDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Main reports dashboard."""

    template_name = 'admin/reports/dashboard.html'
    permission_required = 'reports.view_report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active widgets
        widgets = DashboardWidget.objects.filter(is_active=True).order_by('order')

        dashboard_service = DashboardService()
        context['widgets'] = [
            {
                'widget': w,
                'data': dashboard_service.get_widget_data(w)
            }
            for w in widgets
        ]

        # Quick reports
        context['quick_reports'] = [
            {'name': 'Ingresos Hoy', 'type': 'revenue', 'period': 'today'},
            {'name': 'Esta Semana', 'type': 'revenue', 'period': 'week'},
            {'name': 'Este Mes', 'type': 'revenue', 'period': 'month'},
        ]

        return context


class GenerateReportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Generate custom report."""

    template_name = 'admin/reports/generate.html'
    permission_required = 'reports.add_report'
    form_class = ReportGeneratorForm

    def form_valid(self, form):
        report_type = form.cleaned_data['report_type']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        service = ReportService()

        if report_type == 'revenue':
            data = service.revenue_report(start_date, end_date)
        elif report_type == 'appointments':
            data = service.appointment_report(start_date, end_date)
        elif report_type == 'patients':
            data = service.patient_report(start_date, end_date)
        elif report_type == 'inventory':
            data = service.inventory_report()

        report = Report.objects.create(
            report_type=report_type,
            name=f"{report_type.title()} Report",
            period_start=start_date,
            period_end=end_date,
            data=data,
            summary=data.get('summary', {}),
            generated_by=self.request.user
        )

        return redirect('reports:detail', pk=report.pk)
```

### Test Cases
- [ ] Revenue report calculates correctly
- [ ] Appointment stats are accurate
- [ ] Patient report counts correctly
- [ ] Inventory report identifies issues
- [ ] Dashboard widgets load data
- [ ] Report export works (PDF, CSV)
- [ ] Scheduled reports run correctly

### Definition of Done
- [ ] All report types implemented
- [ ] Dashboard with visualizations
- [ ] Export functionality working
- [ ] Scheduled reports functional
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-040: Billing/Invoicing
- T-020: Appointment Models
- T-041: Inventory Management
