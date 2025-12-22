"""Core app configuration."""
import os

from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

    def ready(self):
        """Run startup tasks."""
        # Skip license check in test mode
        if getattr(settings, 'SCC_SKIP_LICENSE_CHECK', False):
            return

        # Skip if running management commands that don't need license
        import sys
        skip_commands = ['makemigrations', 'migrate', 'collectstatic', 'test', 'shell']
        if len(sys.argv) > 1 and sys.argv[1] in skip_commands:
            return

        self._validate_license()

    def _validate_license(self):
        """Validate SCC license at startup."""
        import subprocess
        import json
        from django.core.exceptions import ImproperlyConfigured

        license_file = getattr(settings, 'SCC_LICENSE_FILE', 'license.key')
        validator_path = getattr(settings, 'SCC_LICENSE_BINARY', 'rust/target/release/scc-license')

        # Skip if validator doesn't exist (development without Rust build)
        if not os.path.exists(validator_path):
            import warnings
            warnings.warn(
                f"SCC license validator not found at {validator_path}. "
                "Build with: cd rust && cargo build --release"
            )
            return

        if not os.path.exists(license_file):
            raise ImproperlyConfigured(
                f"License file not found: {license_file}. "
                "Generate with: scc-license-generate --type developer --output license.key"
            )

        try:
            result = subprocess.run(
                [validator_path, license_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                raise ImproperlyConfigured(
                    f"License validation failed: {result.stderr}"
                )

            # Parse license info and store in environment
            license_info = json.loads(result.stdout)
            os.environ['SCC_LICENSE_TYPE'] = str(license_info.get('license_type', 'unknown'))
            os.environ['SCC_LICENSEE'] = str(license_info.get('licensee', 'unknown'))

        except subprocess.TimeoutExpired:
            raise ImproperlyConfigured("License validation timed out")
        except json.JSONDecodeError:
            raise ImproperlyConfigured("Invalid license response format")
        except FileNotFoundError:
            import warnings
            warnings.warn("License validator binary not found, skipping validation")
