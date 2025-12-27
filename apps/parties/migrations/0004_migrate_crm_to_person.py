# Generated manually for T-083: Migrate CRM customers to Party Person records

from django.db import migrations


def migrate_crm_customers_to_person(apps, schema_editor):
    """Create Person records for all CRM customers and link to their pets."""
    User = apps.get_model('accounts', 'User')
    Person = apps.get_model('parties', 'Person')
    OwnerProfile = apps.get_model('crm', 'OwnerProfile')
    Pet = apps.get_model('pets', 'Pet')

    created_count = 0
    linked_pets_count = 0

    # Get all users with OwnerProfile (CRM customers)
    for owner_profile in OwnerProfile.objects.select_related('user').all():
        user = owner_profile.user
        if not user:
            continue

        # Skip if user already has a Person linked
        if user.person_id:
            person = Person.objects.get(pk=user.person_id)
        else:
            # Create Person from User data
            person = Person.objects.create(
                first_name=user.first_name or '',
                last_name=user.last_name or '',
                email=user.email or '',
                is_active=user.is_active,
            )
            created_count += 1

            # Link User to Person
            user.person = person
            user.save(update_fields=['person'])

        # Link pets from deprecated owner field to owner_person
        pets_to_update = Pet.objects.filter(owner=user, owner_person__isnull=True)
        for pet in pets_to_update:
            pet.owner_person = person
            pet.save(update_fields=['owner_person'])
            linked_pets_count += 1

    print(f"Created {created_count} Person records from CRM customers")
    print(f"Linked {linked_pets_count} pets to Person records")


def reverse_migration(apps, schema_editor):
    """Reverse: unlink users from persons (don't delete persons)."""
    User = apps.get_model('accounts', 'User')
    OwnerProfile = apps.get_model('crm', 'OwnerProfile')

    # Get all users with OwnerProfile and unlink their Person
    for owner_profile in OwnerProfile.objects.select_related('user').all():
        user = owner_profile.user
        if user and user.person_id:
            user.person = None
            user.save(update_fields=['person'])


class Migration(migrations.Migration):

    dependencies = [
        ('parties', '0003_person_address_is_billing_person_address_is_home_and_more'),
        ('accounts', '0007_user_person_alter_user_auth_method'),  # Ensure User.person field exists
        ('crm', '0001_initial'),
        ('pets', '0007_pet_owner_group_pet_owner_organization_and_more'),
    ]

    operations = [
        migrations.RunPython(
            migrate_crm_customers_to_person,
            reverse_migration,
        ),
    ]
