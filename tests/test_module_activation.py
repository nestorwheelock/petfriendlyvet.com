"""Tests for module activation and feature flag models."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.core.models import ModuleConfig, FeatureFlag


User = get_user_model()


@pytest.mark.django_db
class TestModuleConfigModel:
    """Tests for ModuleConfig model."""

    def test_create_module_config(self):
        """Test creating a module config."""
        module = ModuleConfig.objects.create(
            app_name='appointments',
            display_name='Appointments',
            section='operations',
        )
        assert module.app_name == 'appointments'
        assert module.display_name == 'Appointments'
        assert module.section == 'operations'

    def test_module_enabled_by_default(self):
        """Test that modules are enabled by default."""
        module = ModuleConfig.objects.create(
            app_name='billing',
            display_name='Billing',
        )
        assert module.is_enabled is True

    def test_disable_module_sets_timestamp(self):
        """Test that disabling a module sets the disabled_at timestamp."""
        module = ModuleConfig.objects.create(
            app_name='inventory',
            display_name='Inventory',
        )
        assert module.disabled_at is None

        # Disable the module
        module.disable()
        assert module.is_enabled is False
        assert module.disabled_at is not None

    def test_disable_module_with_user(self):
        """Test that disabling a module records the user who disabled it."""
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
        )
        module = ModuleConfig.objects.create(
            app_name='reports',
            display_name='Reports',
        )

        module.disable(user=user)
        assert module.disabled_by == user

    def test_enable_module_clears_disabled_fields(self):
        """Test that enabling a module clears disabled_at and disabled_by."""
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
        )
        module = ModuleConfig.objects.create(
            app_name='crm',
            display_name='CRM',
        )

        module.disable(user=user)
        assert module.disabled_at is not None
        assert module.disabled_by == user

        module.enable()
        assert module.is_enabled is True
        assert module.disabled_at is None
        assert module.disabled_by is None

    def test_module_unique_constraint(self):
        """Test that app_name must be unique."""
        ModuleConfig.objects.create(
            app_name='unique_module',
            display_name='Unique Module',
        )

        with pytest.raises(IntegrityError):
            ModuleConfig.objects.create(
                app_name='unique_module',
                display_name='Another Name',
            )

    def test_module_str_representation(self):
        """Test string representation of module config."""
        module = ModuleConfig.objects.create(
            app_name='patients',
            display_name='Patient Records',
        )
        assert str(module) == 'Patient Records (patients)'

    def test_module_timestamps(self):
        """Test that created_at and updated_at are set."""
        module = ModuleConfig.objects.create(
            app_name='communications',
            display_name='Communications',
        )
        assert module.created_at is not None
        assert module.updated_at is not None


@pytest.mark.django_db
class TestFeatureFlagModel:
    """Tests for FeatureFlag model."""

    def test_create_feature_flag(self):
        """Test creating a feature flag."""
        flag = FeatureFlag.objects.create(
            key='appointments.online_booking',
            description='Allow customers to book appointments online',
        )
        assert flag.key == 'appointments.online_booking'
        assert flag.description == 'Allow customers to book appointments online'

    def test_feature_enabled_by_default(self):
        """Test that features are enabled by default."""
        flag = FeatureFlag.objects.create(
            key='billing.recurring_invoices',
        )
        assert flag.is_enabled is True

    def test_feature_flag_with_module(self):
        """Test creating a feature flag linked to a module."""
        module = ModuleConfig.objects.create(
            app_name='appointments',
            display_name='Appointments',
        )
        flag = FeatureFlag.objects.create(
            key='appointments.sms_reminders',
            description='Send SMS reminders for appointments',
            module=module,
        )
        assert flag.module == module
        assert flag in module.feature_flags.all()

    def test_feature_flag_without_module(self):
        """Test that feature flags can exist without a module (global flags)."""
        flag = FeatureFlag.objects.create(
            key='global.dark_mode',
            description='Enable dark mode UI',
            module=None,
        )
        assert flag.module is None

    def test_feature_key_unique(self):
        """Test that feature key must be unique."""
        FeatureFlag.objects.create(
            key='unique.feature',
            description='A unique feature',
        )

        with pytest.raises(IntegrityError):
            FeatureFlag.objects.create(
                key='unique.feature',
                description='Another description',
            )

    def test_feature_flag_str_representation(self):
        """Test string representation of feature flag."""
        flag = FeatureFlag.objects.create(
            key='inventory.barcode_scanning',
            description='Enable barcode scanning',
        )
        assert str(flag) == 'inventory.barcode_scanning'

    def test_feature_flag_timestamps(self):
        """Test that created_at and updated_at are set."""
        flag = FeatureFlag.objects.create(
            key='test.timestamps',
        )
        assert flag.created_at is not None
        assert flag.updated_at is not None

    def test_disable_feature_flag(self):
        """Test disabling a feature flag."""
        flag = FeatureFlag.objects.create(
            key='test.disable',
        )
        assert flag.is_enabled is True

        flag.is_enabled = False
        flag.save()

        flag.refresh_from_db()
        assert flag.is_enabled is False

    def test_feature_flag_cascade_delete(self):
        """Test that feature flags are deleted when module is deleted."""
        module = ModuleConfig.objects.create(
            app_name='test_cascade',
            display_name='Test Cascade',
        )
        flag = FeatureFlag.objects.create(
            key='test_cascade.feature',
            module=module,
        )
        flag_id = flag.id

        module.delete()

        assert not FeatureFlag.objects.filter(id=flag_id).exists()


@pytest.mark.django_db
class TestModuleConfigQuerysets:
    """Tests for ModuleConfig manager and querysets."""

    def test_enabled_queryset(self):
        """Test filtering enabled modules."""
        enabled = ModuleConfig.objects.create(
            app_name='enabled_module',
            display_name='Enabled',
            is_enabled=True,
        )
        disabled = ModuleConfig.objects.create(
            app_name='disabled_module',
            display_name='Disabled',
            is_enabled=False,
        )

        enabled_modules = ModuleConfig.objects.enabled()
        assert enabled in enabled_modules
        assert disabled not in enabled_modules

    def test_disabled_queryset(self):
        """Test filtering disabled modules."""
        enabled = ModuleConfig.objects.create(
            app_name='enabled_module',
            display_name='Enabled',
            is_enabled=True,
        )
        disabled = ModuleConfig.objects.create(
            app_name='disabled_module',
            display_name='Disabled',
            is_enabled=False,
        )

        disabled_modules = ModuleConfig.objects.disabled()
        assert disabled in disabled_modules
        assert enabled not in disabled_modules

    def test_by_section_queryset(self):
        """Test filtering modules by section."""
        ops = ModuleConfig.objects.create(
            app_name='appointments',
            display_name='Appointments',
            section='operations',
        )
        finance = ModuleConfig.objects.create(
            app_name='billing',
            display_name='Billing',
            section='finance',
        )

        ops_modules = ModuleConfig.objects.by_section('operations')
        assert ops in ops_modules
        assert finance not in ops_modules
