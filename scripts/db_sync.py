#!/usr/bin/env python3
"""
Database Sync Utilities for Django Sites
Handles bidirectional sync between local and production databases.

Usage:
    python db_sync.py [command] [options]

Commands:
    pull        Pull production database to local
    push        Push local database to production
    backup      Create backup of specified database
    compare     Compare local and production databases
    tables      List tables and row counts
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str
    port: str
    name: str
    user: str
    password: str
    container: str = None


class DatabaseSync:
    def __init__(self, local_config: DatabaseConfig, remote_config: DatabaseConfig,
                 backup_dir: Path, remote_host: str, remote_password: str):
        self.local = local_config
        self.remote = remote_config
        self.backup_dir = Path(backup_dir)
        self.remote_host = remote_host
        self.remote_password = remote_password

        # Tables to exclude from sync
        self.exclude_tables = [
            'django_session',
            'django_admin_log',
        ]

    def log(self, message, level='INFO'):
        colors = {
            'INFO': '\033[0;34m',
            'SUCCESS': '\033[0;32m',
            'WARNING': '\033[1;33m',
            'ERROR': '\033[0;31m',
        }
        nc = '\033[0m'
        print(f"{colors.get(level, '')}{level}{nc}: {message}")

    def ssh_command(self, command, timeout=300):
        """Execute command on remote server via SSH using paramiko."""
        try:
            import paramiko
        except ImportError:
            self.log("paramiko not installed. Install with: pip install paramiko", 'ERROR')
            sys.exit(1)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Extract user and host from remote_host
            user, host = self.remote_host.split('@')
            client.connect(host, username=user, password=self.remote_password, timeout=30)

            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            output = stdout.read().decode()
            errors = stderr.read().decode()

            if errors and 'warning' not in errors.lower():
                self.log(f"Remote error: {errors[:500]}", 'WARNING')

            return output, errors

        finally:
            client.close()

    def local_docker_exec(self, command):
        """Execute command in local Docker container."""
        full_cmd = f"docker exec {self.local.container} {command}"
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr

    def remote_docker_exec(self, command, timeout=300):
        """Execute command in remote Docker container."""
        full_cmd = f"docker exec {self.remote.container} {command}"
        return self.ssh_command(full_cmd, timeout)

    def create_backup(self, source='local', backup_name=None):
        """Create a database backup."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source}_{timestamp}.sql"

        backup_path = self.backup_dir / backup_name

        self.log(f"Creating backup: {backup_path}")

        if source == 'local':
            cmd = f"pg_dump -U {self.local.user} {self.local.name}"
            output, errors = self.local_docker_exec(cmd)
        else:
            cmd = f"pg_dump -U {self.remote.user} {self.remote.name}"
            output, errors = self.remote_docker_exec(cmd, timeout=600)

        if output:
            with open(backup_path, 'w') as f:
                f.write(output)
            size = backup_path.stat().st_size
            self.log(f"Backup created: {backup_path} ({size / 1024 / 1024:.1f}MB)", 'SUCCESS')
            return backup_path
        else:
            self.log(f"Backup failed: {errors}", 'ERROR')
            return None

    def pull(self, dry_run=False):
        """Pull production database to local."""
        self.log("Starting database pull from production...")

        # Step 1: Backup local database
        self.log("Step 1/4: Backing up local database...")
        local_backup = self.create_backup('local', f"local_pre_pull_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

        if not local_backup:
            self.log("Failed to backup local database. Aborting.", 'ERROR')
            return False

        # Step 2: Export production database
        self.log("Step 2/4: Exporting production database...")
        prod_backup = self.create_backup('remote', f"prod_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

        if not prod_backup:
            self.log("Failed to export production database. Aborting.", 'ERROR')
            return False

        if dry_run:
            self.log("DRY RUN: Would import production backup to local", 'WARNING')
            return True

        # Step 3: Drop and recreate local database
        self.log("Step 3/4: Recreating local database...")

        # Terminate connections
        terminate_cmd = f"psql -U {self.local.user} -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{self.local.name}' AND pid <> pg_backend_pid();\""
        self.local_docker_exec(terminate_cmd)

        # Drop and recreate
        drop_cmd = f"psql -U {self.local.user} -d postgres -c \"DROP DATABASE IF EXISTS {self.local.name};\""
        self.local_docker_exec(drop_cmd)

        create_cmd = f"psql -U {self.local.user} -d postgres -c \"CREATE DATABASE {self.local.name} OWNER {self.local.user};\""
        self.local_docker_exec(create_cmd)

        # Step 4: Import production dump
        self.log("Step 4/4: Importing production database...")

        # Copy dump file into container
        copy_cmd = f"docker cp {prod_backup} {self.local.container}:/tmp/import.sql"
        subprocess.run(copy_cmd, shell=True, check=True)

        # Import
        import_cmd = f"psql -U {self.local.user} -d {self.local.name} -f /tmp/import.sql"
        output, errors = self.local_docker_exec(import_cmd)

        # Cleanup
        cleanup_cmd = "rm /tmp/import.sql"
        self.local_docker_exec(cleanup_cmd)

        self.log("Database pull complete!", 'SUCCESS')
        return True

    def push(self, dry_run=False, force=False):
        """Push local database to production."""
        self.log("Starting database push to production...")

        if not force:
            self.log("WARNING: This will REPLACE the production database!", 'WARNING')
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                self.log("Aborted.", 'WARNING')
                return False

        # Step 1: Backup production database
        self.log("Step 1/4: Backing up production database...")
        prod_backup = self.create_backup('remote', f"prod_pre_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

        if not prod_backup:
            self.log("Failed to backup production database. Aborting.", 'ERROR')
            return False

        # Step 2: Export local database
        self.log("Step 2/4: Exporting local database...")
        local_backup = self.create_backup('local', f"local_for_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")

        if not local_backup:
            self.log("Failed to export local database. Aborting.", 'ERROR')
            return False

        if dry_run:
            self.log("DRY RUN: Would push local backup to production", 'WARNING')
            return True

        # Step 3: Upload to server
        self.log("Step 3/4: Uploading to server...")

        try:
            import paramiko
        except ImportError:
            self.log("paramiko not installed.", 'ERROR')
            return False

        user, host = self.remote_host.split('@')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=self.remote_password, timeout=30)

        sftp = client.open_sftp()
        sftp.put(str(local_backup), '/root/db_import.sql')
        sftp.close()

        # Step 4: Import on production
        self.log("Step 4/4: Importing to production...")

        # Drop and recreate production database
        drop_cmd = f"docker exec {self.remote.container} psql -U {self.remote.user} -d postgres -c \"DROP DATABASE IF EXISTS {self.remote.name};\""
        self.ssh_command(drop_cmd)

        create_cmd = f"docker exec {self.remote.container} psql -U {self.remote.user} -d postgres -c \"CREATE DATABASE {self.remote.name} OWNER {self.remote.user};\""
        self.ssh_command(create_cmd)

        # Copy dump into container
        copy_cmd = f"docker cp /root/db_import.sql {self.remote.container}:/tmp/import.sql"
        self.ssh_command(copy_cmd)

        # Import
        import_cmd = f"docker exec {self.remote.container} psql -U {self.remote.user} -d {self.remote.name} -f /tmp/import.sql"
        self.ssh_command(import_cmd, timeout=600)

        # Cleanup
        cleanup_cmd = f"rm /root/db_import.sql && docker exec {self.remote.container} rm /tmp/import.sql"
        self.ssh_command(cleanup_cmd)

        client.close()

        self.log("Database push complete!", 'SUCCESS')
        return True

    def compare(self):
        """Compare local and production databases."""
        self.log("Comparing local and production databases...")

        # Get local table counts
        local_cmd = f"""psql -U {self.local.user} -d {self.local.name} -t -c "
            SELECT table_name, (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
            FROM (
                SELECT table_name,
                    query_to_xml(format('select count(*) as cnt from %I.%I', 'public', table_name), false, true, '') as xml_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
            ) t
            ORDER BY table_name;
        " """
        local_output, _ = self.local_docker_exec(local_cmd)

        # Get remote table counts
        remote_cmd = f"""psql -U {self.remote.user} -d {self.remote.name} -t -c "
            SELECT table_name, (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
            FROM (
                SELECT table_name,
                    query_to_xml(format('select count(*) as cnt from %I.%I', 'public', table_name), false, true, '') as xml_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
            ) t
            ORDER BY table_name;
        " """
        remote_output, _ = self.remote_docker_exec(remote_cmd)

        # Parse and compare
        local_tables = self._parse_table_counts(local_output)
        remote_tables = self._parse_table_counts(remote_output)

        all_tables = set(local_tables.keys()) | set(remote_tables.keys())

        print("\n" + "=" * 60)
        print(f"{'Table':<35} {'Local':>10} {'Remote':>10}")
        print("=" * 60)

        for table in sorted(all_tables):
            local_count = local_tables.get(table, 0)
            remote_count = remote_tables.get(table, 0)
            diff = local_count - remote_count
            diff_str = f"(+{diff})" if diff > 0 else f"({diff})" if diff < 0 else ""

            print(f"{table:<35} {local_count:>10} {remote_count:>10} {diff_str}")

        print("=" * 60)

    def _parse_table_counts(self, output):
        """Parse table count output from psql."""
        tables = {}
        for line in output.strip().split('\n'):
            parts = line.strip().split('|')
            if len(parts) >= 2:
                table = parts[0].strip()
                try:
                    count = int(parts[1].strip())
                    tables[table] = count
                except (ValueError, IndexError):
                    pass
        return tables

    def list_tables(self, source='local'):
        """List tables and row counts."""
        if source == 'local':
            cmd = f"""psql -U {self.local.user} -d {self.local.name} -c "
                SELECT table_name,
                    (xpath('/row/cnt/text()', query_to_xml(format('select count(*) as cnt from %I.%I', 'public', table_name), false, true, '')))[1]::text::int as row_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY row_count DESC;
            " """
            output, _ = self.local_docker_exec(cmd)
        else:
            cmd = f"""psql -U {self.remote.user} -d {self.remote.name} -c "
                SELECT table_name,
                    (xpath('/row/cnt/text()', query_to_xml(format('select count(*) as cnt from %I.%I', 'public', table_name), false, true, '')))[1]::text::int as row_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY row_count DESC;
            " """
            output, _ = self.remote_docker_exec(cmd)

        print(f"\n{source.upper()} DATABASE TABLES:")
        print(output)


def load_config():
    """Load configuration from deploy.conf."""
    script_dir = Path(__file__).parent
    config_path = script_dir / 'deploy.conf'

    config = {
        'REMOTE_HOST': 'root@108.61.224.251',
        'REMOTE_PASSWORD': '',
        'DB_CONTAINER': 'bruno-db-1',
        'DB_NAME': 'nestorwheelock',
        'DB_USER': 'nestor',
        'DB_PASSWORD': '',
        'LOCAL_DB_CONTAINER': 'nestorwheelockcom_db_1',
        'LOCAL_DB_USER': 'nestor',
        'LOCAL_DB_PASSWORD': '',
        'BACKUP_DIR': str(Path.home() / '.deploy_backups/nestorwheelock'),
    }

    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key in config:
                    config[key] = value

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Database sync utilities for Django sites'
    )
    parser.add_argument('command', choices=['pull', 'push', 'backup', 'compare', 'tables'],
                       help='Command to execute')
    parser.add_argument('--source', choices=['local', 'remote'], default='local',
                       help='Source database for backup/tables commands')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')

    args = parser.parse_args()

    config = load_config()

    local_config = DatabaseConfig(
        host='localhost',
        port='5432',
        name=config['DB_NAME'],
        user=config['LOCAL_DB_USER'],
        password=config['LOCAL_DB_PASSWORD'],
        container=config['LOCAL_DB_CONTAINER'],
    )

    remote_config = DatabaseConfig(
        host='bruno-db-1',
        port='5432',
        name=config['DB_NAME'],
        user=config['DB_USER'],
        password=config['DB_PASSWORD'],
        container=config['DB_CONTAINER'],
    )

    sync = DatabaseSync(
        local_config=local_config,
        remote_config=remote_config,
        backup_dir=Path(config['BACKUP_DIR']),
        remote_host=config['REMOTE_HOST'],
        remote_password=config['REMOTE_PASSWORD'],
    )

    if args.command == 'pull':
        sync.pull(dry_run=args.dry_run)
    elif args.command == 'push':
        sync.push(dry_run=args.dry_run, force=args.force)
    elif args.command == 'backup':
        sync.create_backup(source=args.source)
    elif args.command == 'compare':
        sync.compare()
    elif args.command == 'tables':
        sync.list_tables(source=args.source)


if __name__ == '__main__':
    main()
