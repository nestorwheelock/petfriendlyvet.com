"""Views for the reports app."""
from django.views.generic import TemplateView

from apps.accounts.mixins import ModulePermissionMixin


class ReportsPermissionMixin(ModulePermissionMixin):
    """Mixin requiring reports module permission."""
    required_module = 'reports'
    required_action = 'view'


class ReportsDashboardView(ReportsPermissionMixin, TemplateView):
    """Main reports dashboard."""

    template_name = 'reports/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_reports'] = [
            {
                'name': 'Sales Report',
                'name_es': 'Reporte de Ventas',
                'description': 'Revenue and sales analytics',
                'icon': '💰',
                'url_name': 'reports:sales',
            },
            {
                'name': 'Appointments Report',
                'name_es': 'Reporte de Citas',
                'description': 'Appointment statistics and trends',
                'icon': '📅',
                'url_name': 'reports:appointments',
            },
            {
                'name': 'Inventory Report',
                'name_es': 'Reporte de Inventario',
                'description': 'Stock levels and movements',
                'icon': '📦',
                'url_name': 'reports:inventory',
            },
            {
                'name': 'Customer Report',
                'name_es': 'Reporte de Clientes',
                'description': 'Customer analytics and activity',
                'icon': '👥',
                'url_name': 'reports:customers',
            },
        ]
        return context


class SalesReportView(ReportsPermissionMixin, TemplateView):
    """Sales and revenue report."""

    template_name = 'reports/sales.html'


class AppointmentsReportView(ReportsPermissionMixin, TemplateView):
    """Appointments statistics report."""

    template_name = 'reports/appointments.html'


class InventoryReportView(ReportsPermissionMixin, TemplateView):
    """Inventory levels report."""

    template_name = 'reports/inventory.html'


class CustomersReportView(ReportsPermissionMixin, TemplateView):
    """Customer analytics report."""

    template_name = 'reports/customers.html'
