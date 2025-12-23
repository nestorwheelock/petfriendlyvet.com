"""Tests for core app configuration and license validation."""
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from django.core.exceptions import ImproperlyConfigured


class TestCoreConfigReady:
    """Test CoreConfig.ready() method."""

    def test_ready_skips_with_scc_skip_flag(self, settings):
        """ready() should skip license check when SCC_SKIP_LICENSE_CHECK is True."""
        from apps.core.apps import CoreConfig

        settings.SCC_SKIP_LICENSE_CHECK = True
        config = CoreConfig('apps.core', __import__('apps.core'))

        with patch.object(config, '_validate_license') as mock_validate:
            config.ready()
            mock_validate.assert_not_called()

    def test_ready_skips_for_management_commands(self, settings):
        """ready() should skip license check for certain management commands."""
        from apps.core.apps import CoreConfig

        settings.SCC_SKIP_LICENSE_CHECK = False
        config = CoreConfig('apps.core', __import__('apps.core'))

        for cmd in ['makemigrations', 'migrate', 'collectstatic', 'test', 'shell']:
            with patch('sys.argv', ['manage.py', cmd]):
                with patch.object(config, '_validate_license') as mock_validate:
                    config.ready()
                    mock_validate.assert_not_called()

    def test_ready_validates_license_for_runserver(self, settings):
        """ready() should validate license for runserver command."""
        from apps.core.apps import CoreConfig

        settings.SCC_SKIP_LICENSE_CHECK = False
        config = CoreConfig('apps.core', __import__('apps.core'))

        with patch('sys.argv', ['manage.py', 'runserver']):
            with patch.object(config, '_validate_license') as mock_validate:
                config.ready()
                mock_validate.assert_called_once()


class TestValidateLicense:
    """Test CoreConfig._validate_license() method."""

    def test_skips_when_validator_not_found(self, settings, tmp_path):
        """Should warn and skip when validator binary doesn't exist."""
        from apps.core.apps import CoreConfig

        settings.SCC_LICENSE_BINARY = str(tmp_path / 'nonexistent')
        settings.SCC_LICENSE_FILE = 'license.key'

        config = CoreConfig('apps.core', __import__('apps.core'))

        with pytest.warns(UserWarning, match='license validator not found'):
            config._validate_license()

    def test_raises_when_license_file_missing(self, settings, tmp_path):
        """Should raise ImproperlyConfigured when license file is missing."""
        from apps.core.apps import CoreConfig

        # Create a fake validator
        validator = tmp_path / 'scc-license'
        validator.touch()
        validator.chmod(0o755)

        settings.SCC_LICENSE_BINARY = str(validator)
        settings.SCC_LICENSE_FILE = str(tmp_path / 'missing.key')

        config = CoreConfig('apps.core', __import__('apps.core'))

        with pytest.raises(ImproperlyConfigured, match='License file not found'):
            config._validate_license()

    def test_raises_on_validation_failure(self, settings, tmp_path):
        """Should raise ImproperlyConfigured when validation fails."""
        from apps.core.apps import CoreConfig
        import subprocess

        # Create fake files
        validator = tmp_path / 'scc-license'
        validator.touch()
        validator.chmod(0o755)
        license_file = tmp_path / 'license.key'
        license_file.touch()

        settings.SCC_LICENSE_BINARY = str(validator)
        settings.SCC_LICENSE_FILE = str(license_file)

        config = CoreConfig('apps.core', __import__('apps.core'))

        # Mock subprocess to return failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = 'Invalid license'

        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(ImproperlyConfigured, match='License validation failed'):
                config._validate_license()

    def test_successful_validation(self, settings, tmp_path):
        """Should set environment variables on successful validation."""
        from apps.core.apps import CoreConfig

        # Create fake files
        validator = tmp_path / 'scc-license'
        validator.touch()
        validator.chmod(0o755)
        license_file = tmp_path / 'license.key'
        license_file.touch()

        settings.SCC_LICENSE_BINARY = str(validator)
        settings.SCC_LICENSE_FILE = str(license_file)

        config = CoreConfig('apps.core', __import__('apps.core'))

        # Mock successful subprocess
        license_info = {'license_type': 'developer', 'licensee': 'Test User'}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(license_info)

        with patch('subprocess.run', return_value=mock_result):
            config._validate_license()

            assert os.environ.get('SCC_LICENSE_TYPE') == 'developer'
            assert os.environ.get('SCC_LICENSEE') == 'Test User'

    def test_timeout_raises_error(self, settings, tmp_path):
        """Should raise ImproperlyConfigured on timeout."""
        from apps.core.apps import CoreConfig
        import subprocess

        # Create fake files
        validator = tmp_path / 'scc-license'
        validator.touch()
        validator.chmod(0o755)
        license_file = tmp_path / 'license.key'
        license_file.touch()

        settings.SCC_LICENSE_BINARY = str(validator)
        settings.SCC_LICENSE_FILE = str(license_file)

        config = CoreConfig('apps.core', __import__('apps.core'))

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 5)):
            with pytest.raises(ImproperlyConfigured, match='timed out'):
                config._validate_license()

    def test_invalid_json_raises_error(self, settings, tmp_path):
        """Should raise ImproperlyConfigured on invalid JSON response."""
        from apps.core.apps import CoreConfig

        # Create fake files
        validator = tmp_path / 'scc-license'
        validator.touch()
        validator.chmod(0o755)
        license_file = tmp_path / 'license.key'
        license_file.touch()

        settings.SCC_LICENSE_BINARY = str(validator)
        settings.SCC_LICENSE_FILE = str(license_file)

        config = CoreConfig('apps.core', __import__('apps.core'))

        # Mock subprocess with invalid JSON output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'not valid json'

        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(ImproperlyConfigured, match='Invalid license response'):
                config._validate_license()

    def test_file_not_found_warns(self, settings, tmp_path):
        """Should warn when subprocess raises FileNotFoundError."""
        from apps.core.apps import CoreConfig

        # Create fake files
        validator = tmp_path / 'scc-license'
        validator.touch()
        validator.chmod(0o755)
        license_file = tmp_path / 'license.key'
        license_file.touch()

        settings.SCC_LICENSE_BINARY = str(validator)
        settings.SCC_LICENSE_FILE = str(license_file)

        config = CoreConfig('apps.core', __import__('apps.core'))

        with patch('subprocess.run', side_effect=FileNotFoundError()):
            with pytest.warns(UserWarning, match='binary not found'):
                config._validate_license()
