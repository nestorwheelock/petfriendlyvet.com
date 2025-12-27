"""Management command to scan codebase and sync module permissions."""
import os
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

User = get_user_model()

# Standard actions for module permissions
ACTIONS = ['view', 'create', 'edit', 'delete', 'approve', 'manage']


class Command(BaseCommand):
    """Scan codebase for permission usage and create missing permissions."""

    help = 'Scan codebase for permission usage and sync permissions to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output of discovered permissions',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        dry_run = options['dry_run']

        self.stdout.write('Scanning codebase for permission usage...\n')

        # Scan for permissions
        discovered = self.scan_codebase()

        if verbose:
            self.stdout.write(f'\nDiscovered {len(discovered)} unique module.action permissions:\n')
            for module, action in sorted(discovered):
                self.stdout.write(f'  - {module}.{action}\n')

        # Get existing permissions
        existing = set(
            DjangoPermission.objects.filter(
                codename__contains='.'
            ).values_list('codename', flat=True)
        )

        # Find missing permissions
        missing = set()
        for module, action in discovered:
            codename = f'{module}.{action}'
            if codename not in existing:
                missing.add((module, action))

        if missing:
            self.stdout.write(f'\nFound {len(missing)} missing permissions:\n')
            for module, action in sorted(missing):
                self.stdout.write(f'  - {module}.{action}\n')

            if not dry_run:
                self.create_permissions(missing)
                self.stdout.write(self.style.SUCCESS(
                    f'\nCreated {len(missing)} new permissions.\n'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    '\n(Dry run - no permissions created)\n'
                ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\nAll discovered permissions already exist in database.\n'
            ))

        # Summary
        total = len(existing) + (len(missing) if not dry_run else 0)
        self.stdout.write(f'\nPermission sync complete. Total module permissions: {total}\n')

    def scan_codebase(self):
        """Scan apps directory for permission usage patterns."""
        discovered = set()

        apps_dir = Path(settings.BASE_DIR) / 'apps'

        # Patterns to match
        # @require_permission('module', 'action')
        decorator_pattern = re.compile(
            r"@require_permission\s*\(\s*['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\s*\)"
        )

        # required_module = 'module' and required_action = 'action' in class
        mixin_module_pattern = re.compile(
            r"required_module\s*=\s*['\"](\w+)['\"]"
        )
        mixin_action_pattern = re.compile(
            r"required_action\s*=\s*['\"](\w+)['\"]"
        )

        # has_module_permission('module', 'action')
        method_pattern = re.compile(
            r"has_module_permission\s*\(\s*['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\s*\)"
        )

        # Scan all Python files in apps
        for py_file in apps_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            try:
                content = py_file.read_text()

                # Find decorator usages
                for match in decorator_pattern.finditer(content):
                    module, action = match.groups()
                    discovered.add((module, action))

                # Find method usages
                for match in method_pattern.finditer(content):
                    module, action = match.groups()
                    discovered.add((module, action))

                # Find mixin usages (module and action on separate lines)
                modules = mixin_module_pattern.findall(content)
                actions = mixin_action_pattern.findall(content)

                # If we find required_module, pair with actions found in same file
                for module in modules:
                    for action in actions:
                        discovered.add((module, action))

            except Exception as e:
                self.stderr.write(f'Error reading {py_file}: {e}\n')

        return discovered

    def create_permissions(self, permissions):
        """Create missing permissions in database."""
        content_type = ContentType.objects.get_for_model(User)

        for module, action in permissions:
            codename = f'{module}.{action}'
            name = f'Can {action} {module}'

            DjangoPermission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'content_type': content_type
                }
            )
