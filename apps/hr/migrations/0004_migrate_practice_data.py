"""
Data migration to copy Practice Shift and TimeEntry data to HR module.

This migration:
1. Copies Practice Shift → HR Shift (where Employee exists for StaffProfile.user)
2. Copies Practice TimeEntry → HR TimeEntry (where Employee exists for StaffProfile.user)

Note: This does NOT delete the source data. The Practice models will be deprecated
in a future release after verification.
"""
from django.db import migrations


def migrate_shifts(apps, schema_editor):
    """Migrate Practice Shift data to HR Shift."""
    PracticeShift = apps.get_model('practice', 'Shift')
    HRShift = apps.get_model('hr', 'Shift')
    Employee = apps.get_model('hr', 'Employee')

    migrated = 0
    skipped = 0

    for ps in PracticeShift.objects.all():
        # Find Employee via StaffProfile → User
        try:
            employee = Employee.objects.get(user=ps.staff.user)
        except Employee.DoesNotExist:
            skipped += 1
            continue

        # Check if already migrated (avoid duplicates)
        existing = HRShift.objects.filter(
            employee=employee,
            date=ps.date,
            start_time=ps.start_time,
            end_time=ps.end_time,
        ).exists()

        if existing:
            continue

        # Map is_confirmed to status
        status = 'confirmed' if ps.is_confirmed else 'scheduled'

        HRShift.objects.create(
            employee=employee,
            date=ps.date,
            start_time=ps.start_time,
            end_time=ps.end_time,
            shift_type='regular',
            status=status,
            notes=ps.notes,
        )
        migrated += 1

    print(f"Shifts migrated: {migrated}, skipped (no Employee): {skipped}")


def migrate_time_entries(apps, schema_editor):
    """Migrate Practice TimeEntry data to HR TimeEntry."""
    PracticeTimeEntry = apps.get_model('practice', 'TimeEntry')
    HRTimeEntry = apps.get_model('hr', 'TimeEntry')
    Employee = apps.get_model('hr', 'Employee')

    migrated = 0
    skipped = 0

    for pte in PracticeTimeEntry.objects.all():
        # Find Employee via StaffProfile → User
        try:
            employee = Employee.objects.get(user=pte.staff.user)
        except Employee.DoesNotExist:
            skipped += 1
            continue

        # Check if already migrated (avoid duplicates)
        existing = HRTimeEntry.objects.filter(
            employee=employee,
            clock_in=pte.clock_in,
        ).exists()

        if existing:
            continue

        # Determine approval status
        if pte.is_approved:
            approval_status = 'approved'
        else:
            approval_status = 'pending'

        HRTimeEntry.objects.create(
            employee=employee,
            date=pte.clock_in.date(),
            clock_in=pte.clock_in,
            clock_out=pte.clock_out,
            break_minutes=pte.break_minutes or 0,
            notes=pte.notes,
            is_approved=pte.is_approved,
            approved_by=pte.approved_by,
            approval_status=approval_status,
            # Note: task field not migrated as Practice TimeEntry doesn't have it
        )
        migrated += 1

    print(f"TimeEntries migrated: {migrated}, skipped (no Employee): {skipped}")


def reverse_migration(apps, schema_editor):
    """Reverse the migration by deleting migrated data."""
    # This is a destructive operation - only run if you're sure
    # The source data in Practice is preserved, so this just removes duplicates
    print("Note: Reverse migration does not delete HR data.")
    print("HR data should be manually cleaned if needed.")


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0003_add_task_and_employee_links'),
        ('practice', '0006_add_task_and_employee_links'),  # Practice has employee FK now
    ]

    operations = [
        migrations.RunPython(migrate_shifts, reverse_migration),
        migrations.RunPython(migrate_time_entries, reverse_migration),
    ]
