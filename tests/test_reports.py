"""Tests for Reports & Analytics app (TDD first)."""
import pytest
from datetime import date, timedelta
from django.utils import timezone

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestReportDefinitionModel:
    """Tests for ReportDefinition model."""

    def test_create_report_definition(self, user):
        """Test creating a report definition."""
        from apps.reports.models import ReportDefinition

        report = ReportDefinition.objects.create(
            name='Monthly Revenue',
            report_type='financial',
            description='Monthly revenue breakdown',
            query_config={'metrics': ['revenue', 'transactions']},
            created_by=user,
        )

        assert report.name == 'Monthly Revenue'
        assert report.report_type == 'financial'

    def test_report_definition_is_active(self, user):
        """Test report definition active status."""
        from apps.reports.models import ReportDefinition

        report = ReportDefinition.objects.create(
            name='Active Report',
            report_type='operational',
            created_by=user,
        )

        assert report.is_active is True


class TestGeneratedReportModel:
    """Tests for GeneratedReport model."""

    def test_create_generated_report(self, user, report_definition):
        """Test creating a generated report."""
        from apps.reports.models import GeneratedReport

        generated = GeneratedReport.objects.create(
            definition=report_definition,
            generated_by=user,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            data={'revenue': 50000, 'transactions': 150},
        )

        assert generated.status == 'completed'

    def test_generated_report_status_flow(self, user, report_definition):
        """Test report status transitions."""
        from apps.reports.models import GeneratedReport

        report = GeneratedReport.objects.create(
            definition=report_definition,
            generated_by=user,
            status='pending',
        )

        assert report.status == 'pending'
        report.status = 'processing'
        report.save()
        assert report.status == 'processing'


class TestDashboardModel:
    """Tests for Dashboard model."""

    def test_create_dashboard(self, user):
        """Test creating a dashboard."""
        from apps.reports.models import Dashboard

        dashboard = Dashboard.objects.create(
            name='Main Dashboard',
            owner=user,
            is_default=True,
        )

        assert dashboard.name == 'Main Dashboard'
        assert dashboard.is_default is True

    def test_dashboard_layout(self, user):
        """Test dashboard layout configuration."""
        from apps.reports.models import Dashboard

        layout = {
            'columns': 3,
            'rows': 2,
            'widgets': [
                {'id': 'revenue', 'x': 0, 'y': 0, 'w': 1, 'h': 1},
            ]
        }
        dashboard = Dashboard.objects.create(
            name='Custom Layout',
            owner=user,
            layout=layout,
        )

        assert dashboard.layout['columns'] == 3


class TestDashboardWidgetModel:
    """Tests for DashboardWidget model."""

    def test_create_widget(self, dashboard):
        """Test creating a dashboard widget."""
        from apps.reports.models import DashboardWidget

        widget = DashboardWidget.objects.create(
            dashboard=dashboard,
            widget_type='chart',
            title='Revenue Chart',
            config={'chart_type': 'line', 'metric': 'revenue'},
            position=1,
        )

        assert widget.widget_type == 'chart'
        assert widget.title == 'Revenue Chart'


class TestScheduledReportModel:
    """Tests for ScheduledReport model."""

    def test_create_scheduled_report(self, user, report_definition):
        """Test creating a scheduled report."""
        from apps.reports.models import ScheduledReport

        scheduled = ScheduledReport.objects.create(
            definition=report_definition,
            frequency='weekly',
            recipients=['admin@clinic.com'],
            is_active=True,
        )

        assert scheduled.frequency == 'weekly'
        assert 'admin@clinic.com' in scheduled.recipients

    def test_scheduled_report_next_run(self, user, report_definition):
        """Test scheduled report next run calculation."""
        from apps.reports.models import ScheduledReport

        scheduled = ScheduledReport.objects.create(
            definition=report_definition,
            frequency='daily',
            next_run=timezone.now() + timedelta(days=1),
        )

        assert scheduled.next_run is not None


class TestMetricSnapshotModel:
    """Tests for MetricSnapshot model."""

    def test_create_metric_snapshot(self):
        """Test creating a metric snapshot."""
        from apps.reports.models import MetricSnapshot

        snapshot = MetricSnapshot.objects.create(
            metric_name='daily_revenue',
            metric_value=1500.00,
            date=date.today(),
            metadata={'appointments': 12},
        )

        assert snapshot.metric_name == 'daily_revenue'
        assert snapshot.metric_value == 1500.00


class TestReportsAITools:
    """Tests for Reports AI tools."""

    def test_get_dashboard_metrics_tool_exists(self):
        """Test get_dashboard_metrics tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_dashboard_metrics')
        assert tool is not None

    def test_generate_report_tool_exists(self):
        """Test generate_report tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('generate_report')
        assert tool is not None

    def test_get_analytics_summary_tool_exists(self):
        """Test get_analytics_summary tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_analytics_summary')
        assert tool is not None


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='reportuser',
        email='report@example.com',
        password='testpass123',
        first_name='Report',
        last_name='User',
    )


@pytest.fixture
def report_definition(user):
    """Create a report definition."""
    from apps.reports.models import ReportDefinition
    return ReportDefinition.objects.create(
        name='Test Report',
        report_type='financial',
        created_by=user,
    )


@pytest.fixture
def dashboard(user):
    """Create a dashboard."""
    from apps.reports.models import Dashboard
    return Dashboard.objects.create(
        name='Test Dashboard',
        owner=user,
    )
