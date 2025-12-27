"""
Tests for the Party pattern models.

Tests the unified Person/Organization/Group architecture and its relationships.
"""

from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import date

from apps.parties.models import (
    Person, Organization, Group, PartyRelationship,
    Address, Phone, Email, Demographics, PartyURL
)
from apps.accounts.models import User
from apps.pets.models import Pet, PetResponsibility


class PersonModelTests(TestCase):
    """Tests for the Person model (core identity)."""

    def test_create_person_with_required_fields(self):
        """Person can be created with just first_name."""
        person = Person.objects.create(first_name="Juan")
        self.assertEqual(person.first_name, "Juan")
        self.assertTrue(person.is_active)

    def test_person_full_name(self):
        """get_full_name returns properly formatted name."""
        person = Person.objects.create(
            first_name="Juan",
            last_name="Garcia"
        )
        self.assertEqual(person.get_full_name(), "Juan Garcia")

    def test_person_full_name_with_middle(self):
        """get_full_name includes middle name when present."""
        person = Person.objects.create(
            first_name="Juan",
            middle_name="Carlos",
            last_name="Garcia"
        )
        self.assertEqual(person.get_full_name(), "Juan Carlos Garcia")

    def test_person_display_name_auto_generated(self):
        """display_name is auto-generated from full name if empty."""
        person = Person.objects.create(
            first_name="Juan",
            last_name="Garcia"
        )
        person.save()
        self.assertIn("Juan", str(person))

    def test_person_preferred_name(self):
        """preferred_name can override first_name in display."""
        person = Person.objects.create(
            first_name="Juan Carlos",
            preferred_name="JC",
            last_name="Garcia"
        )
        # The model should use preferred_name when set
        self.assertEqual(person.preferred_name, "JC")

    def test_person_str_representation(self):
        """__str__ returns display_name or full_name."""
        person = Person.objects.create(
            first_name="Maria",
            last_name="Lopez"
        )
        self.assertIn("Maria", str(person))

    def test_person_can_be_inactive(self):
        """is_active can be set to False."""
        person = Person.objects.create(
            first_name="Test",
            is_active=False
        )
        self.assertFalse(person.is_active)


class UserPersonRelationshipTests(TestCase):
    """Tests for the User-Person relationship (many accounts per person)."""

    def test_person_can_have_multiple_user_accounts(self):
        """One Person can have multiple User accounts (different auth methods)."""
        person = Person.objects.create(first_name="Juan", last_name="Garcia")

        # Create multiple User accounts for the same person
        user1 = User.objects.create_user(
            username="juan.email",
            email="juan@example.com",
            password="testpass123",
            auth_method="email",
            person=person
        )
        user2 = User.objects.create_user(
            username="juan.google",
            email="juan.google@gmail.com",
            password="testpass123",
            auth_method="google",
            person=person
        )

        self.assertEqual(person.accounts.count(), 2)
        self.assertIn(user1, person.accounts.all())
        self.assertIn(user2, person.accounts.all())

    def test_primary_account_returns_first_active(self):
        """primary_account property returns first active account."""
        person = Person.objects.create(first_name="Maria")

        user1 = User.objects.create_user(
            username="maria.inactive",
            email="maria.old@example.com",
            password="testpass123",
            person=person,
            is_active=False
        )
        user2 = User.objects.create_user(
            username="maria.active",
            email="maria@example.com",
            password="testpass123",
            person=person,
            is_active=True
        )

        self.assertEqual(person.primary_account, user2)

    def test_user_without_person_allowed(self):
        """User can exist without a Person (service accounts)."""
        user = User.objects.create_user(
            username="service.api",
            email="api@service.com",
            password="testpass123",
            person=None
        )
        self.assertIsNone(user.person)


class OrganizationModelTests(TestCase):
    """Tests for the Organization model."""

    def test_create_organization(self):
        """Organization can be created with name and type."""
        org = Organization.objects.create(
            name="ABC Veterinary Clinic",
            org_type="clinic"
        )
        self.assertEqual(org.name, "ABC Veterinary Clinic")
        self.assertEqual(org.org_type, "clinic")
        self.assertTrue(org.is_active)

    def test_organization_types(self):
        """All organization types are valid."""
        valid_types = ['clinic', 'rescue', 'supplier', 'school', 'partner', 'other']
        for org_type in valid_types:
            org = Organization.objects.create(
                name=f"Test {org_type}",
                org_type=org_type
            )
            self.assertEqual(org.org_type, org_type)

    def test_organization_with_tax_info(self):
        """Organization can store tax/legal info."""
        org = Organization.objects.create(
            name="PetFood Distributor",
            org_type="supplier",
            tax_id="XAXX010101000",
            legal_name="PetFood Mexico SA de CV"
        )
        self.assertEqual(org.tax_id, "XAXX010101000")
        self.assertEqual(org.legal_name, "PetFood Mexico SA de CV")

    def test_organization_str_representation(self):
        """__str__ returns organization name."""
        org = Organization.objects.create(
            name="Test Clinic",
            org_type="clinic"
        )
        self.assertIn("Test Clinic", str(org))


class GroupModelTests(TestCase):
    """Tests for the Group model (households, families)."""

    def test_create_group(self):
        """Group can be created for a household."""
        group = Group.objects.create(
            name="The Garcia Family",
            group_type="household"
        )
        self.assertEqual(group.name, "The Garcia Family")
        self.assertEqual(group.group_type, "household")

    def test_group_types(self):
        """All group types are valid."""
        valid_types = ['household', 'family', 'partnership', 'other']
        for group_type in valid_types:
            group = Group.objects.create(
                name=f"Test {group_type}",
                group_type=group_type
            )
            self.assertEqual(group.group_type, group_type)

    def test_group_with_primary_contact(self):
        """Group can have a primary contact (Person)."""
        person = Person.objects.create(first_name="Juan", last_name="Garcia")
        group = Group.objects.create(
            name="The Garcia Family",
            group_type="household",
            primary_contact=person
        )
        self.assertEqual(group.primary_contact, person)

    def test_group_str_representation(self):
        """__str__ returns group name."""
        group = Group.objects.create(
            name="Martinez Household",
            group_type="household"
        )
        self.assertIn("Martinez", str(group))


class PartyRelationshipTests(TestCase):
    """Tests for the PartyRelationship model."""

    def test_person_to_organization_employee(self):
        """Person can be an employee of an Organization."""
        person = Person.objects.create(first_name="Maria", last_name="Lopez")
        org = Organization.objects.create(name="ABC Clinic", org_type="clinic")

        rel = PartyRelationship.objects.create(
            from_person=person,
            to_organization=org,
            relationship_type="employee",
            is_active=True
        )

        self.assertEqual(rel.from_person, person)
        self.assertEqual(rel.to_organization, org)
        self.assertEqual(rel.relationship_type, "employee")

    def test_person_to_organization_contractor(self):
        """Person can be a contractor for an Organization."""
        person = Person.objects.create(first_name="Carlos", last_name="Contractor")
        org = Organization.objects.create(name="ABC Clinic", org_type="clinic")

        rel = PartyRelationship.objects.create(
            from_person=person,
            to_organization=org,
            relationship_type="contractor_individual",
            contract_start=date.today()
        )

        self.assertEqual(rel.relationship_type, "contractor_individual")
        self.assertEqual(rel.contract_start, date.today())

    def test_organization_to_organization_vendor(self):
        """Organization can be a vendor to another Organization."""
        clinic = Organization.objects.create(name="ABC Clinic", org_type="clinic")
        supplier = Organization.objects.create(name="PetFood Inc", org_type="supplier")

        rel = PartyRelationship.objects.create(
            from_organization=supplier,
            to_organization=clinic,
            relationship_type="vendor"
        )

        self.assertEqual(rel.from_organization, supplier)
        self.assertEqual(rel.to_organization, clinic)
        self.assertEqual(rel.relationship_type, "vendor")

    def test_person_to_group_member(self):
        """Person can be a member of a Group."""
        person = Person.objects.create(first_name="Ana", last_name="Garcia")
        group = Group.objects.create(name="Garcia Family", group_type="family")

        rel = PartyRelationship.objects.create(
            from_person=person,
            to_group=group,
            relationship_type="member"
        )

        self.assertEqual(rel.to_group, group)
        self.assertEqual(rel.relationship_type, "member")

    def test_person_to_person_relationship(self):
        """Person can have relationship to another Person."""
        person1 = Person.objects.create(first_name="Juan", last_name="Garcia")
        person2 = Person.objects.create(first_name="Maria", last_name="Lopez")

        rel = PartyRelationship.objects.create(
            from_person=person1,
            to_person=person2,
            relationship_type="referral"
        )

        self.assertEqual(rel.from_person, person1)
        self.assertEqual(rel.to_person, person2)


class ContactInfoTests(TestCase):
    """Tests for normalized contact info models (Address, Phone, Email)."""

    def setUp(self):
        self.person = Person.objects.create(first_name="Juan", last_name="Garcia")
        self.org = Organization.objects.create(name="ABC Clinic", org_type="clinic")

    def test_person_can_have_multiple_addresses(self):
        """Person can have home, work, and mailing addresses."""
        home = Address.objects.create(
            person=self.person,
            address_type="home",
            line1="123 Home St",
            city="Mexico City",
            is_primary=True
        )
        work = Address.objects.create(
            person=self.person,
            address_type="work",
            line1="456 Work Ave",
            city="Mexico City"
        )

        self.assertEqual(self.person.addresses.count(), 2)
        self.assertTrue(home.is_primary)

    def test_organization_can_have_address(self):
        """Organization can have addresses."""
        addr = Address.objects.create(
            organization=self.org,
            address_type="work",
            line1="789 Clinic Blvd",
            city="Mexico City",
            is_primary=True
        )

        self.assertEqual(self.org.addresses.count(), 1)

    def test_person_multiple_phone_numbers(self):
        """Person can have multiple phone numbers."""
        mobile = Phone.objects.create(
            person=self.person,
            phone_type="mobile",
            number="55 1234 5678",
            is_primary=True
        )
        home = Phone.objects.create(
            person=self.person,
            phone_type="home",
            number="55 8765 4321"
        )

        self.assertEqual(self.person.phone_numbers.count(), 2)

    def test_person_multiple_emails(self):
        """Person can have multiple email addresses."""
        personal = Email.objects.create(
            person=self.person,
            email_type="personal",
            email="juan.personal@gmail.com",
            is_primary=True
        )
        work = Email.objects.create(
            person=self.person,
            email_type="work",
            email="juan@abcclinic.com"
        )

        self.assertEqual(self.person.email_addresses.count(), 2)


class PetOwnershipTests(TestCase):
    """Tests for pet ownership using the Party pattern."""

    def setUp(self):
        self.person = Person.objects.create(first_name="Juan", last_name="Garcia")
        self.group = Group.objects.create(name="Garcia Family", group_type="household")
        self.org = Organization.objects.create(name="Zoo Mexico", org_type="other")

    def test_pet_owned_by_person(self):
        """Pet can be owned by a Person."""
        pet = Pet.objects.create(
            name="Max",
            species="dog",
            owner_person=self.person
        )

        self.assertEqual(pet.owner_person, self.person)
        self.assertIn(pet, self.person.owned_pets.all())

    def test_pet_owned_by_group(self):
        """Pet can be owned by a Group (household)."""
        pet = Pet.objects.create(
            name="Fluffy",
            species="cat",
            owner_group=self.group
        )

        self.assertEqual(pet.owner_group, self.group)
        self.assertIn(pet, self.group.owned_pets.all())

    def test_pet_owned_by_organization(self):
        """Pet can be owned by an Organization."""
        pet = Pet.objects.create(
            name="Leo",
            species="lion",
            owner_organization=self.org
        )

        self.assertEqual(pet.owner_organization, self.org)
        self.assertIn(pet, self.org.owned_pets.all())


class PetResponsibilityTests(TestCase):
    """Tests for PetResponsibility (multiple responsible parties per pet)."""

    def test_pet_can_have_multiple_responsible_parties(self):
        """Pet can have primary, secondary, and emergency contacts."""
        person1 = Person.objects.create(first_name="Juan", last_name="Garcia")
        person2 = Person.objects.create(first_name="Maria", last_name="Garcia")
        person3 = Person.objects.create(first_name="Carlos", last_name="Emergency")

        pet = Pet.objects.create(
            name="Max",
            species="dog",
            owner_person=person1
        )

        PetResponsibility.objects.create(
            pet=pet,
            person=person1,
            responsibility_type="primary"
        )
        PetResponsibility.objects.create(
            pet=pet,
            person=person2,
            responsibility_type="secondary"
        )
        PetResponsibility.objects.create(
            pet=pet,
            person=person3,
            responsibility_type="emergency"
        )

        self.assertEqual(pet.responsibilities.count(), 3)

    def test_responsibility_types(self):
        """All responsibility types are valid."""
        person = Person.objects.create(first_name="Test")
        pet = Pet.objects.create(name="Buddy", species="dog", owner_person=person)

        valid_types = ['primary', 'secondary', 'caretaker', 'emergency', 'veterinary', 'other']
        for idx, resp_type in enumerate(valid_types):
            responsible = Person.objects.create(first_name=f"Person{idx}")
            resp = PetResponsibility.objects.create(
                pet=pet,
                person=responsible,
                responsibility_type=resp_type
            )
            self.assertEqual(resp.responsibility_type, resp_type)

    def test_responsibility_unique_together(self):
        """Same person cannot have same responsibility type for same pet."""
        person = Person.objects.create(first_name="Juan")
        pet = Pet.objects.create(name="Max", species="dog", owner_person=person)

        PetResponsibility.objects.create(
            pet=pet,
            person=person,
            responsibility_type="primary"
        )

        # Same person, same pet, same type should fail
        with self.assertRaises(IntegrityError):
            PetResponsibility.objects.create(
                pet=pet,
                person=person,
                responsibility_type="primary"
            )

    def test_person_can_be_responsible_for_multiple_pets(self):
        """One person can be responsible for multiple pets."""
        person = Person.objects.create(first_name="Juan", last_name="Garcia")
        pet1 = Pet.objects.create(name="Max", species="dog", owner_person=person)
        pet2 = Pet.objects.create(name="Fluffy", species="cat", owner_person=person)

        PetResponsibility.objects.create(pet=pet1, person=person, responsibility_type="primary")
        PetResponsibility.objects.create(pet=pet2, person=person, responsibility_type="primary")

        self.assertEqual(person.pet_responsibilities.count(), 2)


class HouseholdPetScenarioTests(TestCase):
    """Integration tests for household pet ownership scenarios."""

    def test_husband_wife_share_pet(self):
        """Husband and wife can both be responsible for a pet via Group."""
        # Create the couple
        husband = Person.objects.create(first_name="Juan", last_name="Garcia")
        wife = Person.objects.create(first_name="Maria", last_name="Garcia")

        # Create their household
        household = Group.objects.create(
            name="The Garcia Household",
            group_type="household"
        )

        # Add both to household
        PartyRelationship.objects.create(
            from_person=husband,
            to_group=household,
            relationship_type="head"
        )
        PartyRelationship.objects.create(
            from_person=wife,
            to_group=household,
            relationship_type="member"
        )

        # Pet owned by household
        pet = Pet.objects.create(
            name="Buddy",
            species="dog",
            owner_group=household
        )

        # Both are responsible
        PetResponsibility.objects.create(
            pet=pet,
            person=husband,
            responsibility_type="primary"
        )
        PetResponsibility.objects.create(
            pet=pet,
            person=wife,
            responsibility_type="primary"
        )

        # Verify
        self.assertEqual(pet.owner_group, household)
        self.assertEqual(pet.responsibilities.count(), 2)
        self.assertIn(husband, [r.person for r in pet.responsibilities.all()])
        self.assertIn(wife, [r.person for r in pet.responsibilities.all()])

    def test_roommates_share_pet(self):
        """Roommates can share pet responsibility."""
        person1 = Person.objects.create(first_name="Alex")
        person2 = Person.objects.create(first_name="Jordan")

        household = Group.objects.create(
            name="Apt 4B Roommates",
            group_type="household"
        )

        pet = Pet.objects.create(
            name="Whiskers",
            species="cat",
            owner_group=household
        )

        # One is primary, other is secondary
        PetResponsibility.objects.create(
            pet=pet,
            person=person1,
            responsibility_type="primary"
        )
        PetResponsibility.objects.create(
            pet=pet,
            person=person2,
            responsibility_type="secondary"
        )

        self.assertEqual(pet.responsibilities.filter(responsibility_type="primary").count(), 1)
        self.assertEqual(pet.responsibilities.filter(responsibility_type="secondary").count(), 1)


class MultiAccountScenarioTests(TestCase):
    """Tests for multiple account scenarios."""

    def test_person_with_multiple_auth_methods(self):
        """Person can login via email, Google, and phone."""
        person = Person.objects.create(
            first_name="Tech",
            last_name="Savvy"
        )

        # Email account
        email_user = User.objects.create_user(
            username="tech.email",
            email="tech@example.com",
            password="pass123",
            auth_method="email",
            person=person
        )

        # Google account
        google_user = User.objects.create_user(
            username="tech.google",
            email="tech.savvy@gmail.com",
            password="pass123",
            auth_method="google",
            person=person
        )

        # Phone account
        phone_user = User.objects.create_user(
            username="tech.phone",
            email="",
            password="pass123",
            auth_method="phone",
            person=person
        )

        self.assertEqual(person.accounts.count(), 3)
        self.assertEqual(person.accounts.filter(auth_method="google").count(), 1)


class DemographicsTests(TestCase):
    """Tests for Demographics model."""

    def test_person_demographics(self):
        """Person can have demographic information."""
        person = Person.objects.create(first_name="Juan", last_name="Garcia")

        demographics = Demographics.objects.create(
            person=person,
            gender="M",
            marital_status="married",
            nationality="Mexican",
            occupation="Veterinarian",
            education_level="doctorate"
        )

        self.assertEqual(person.demographics.gender, "M")
        self.assertEqual(person.demographics.occupation, "Veterinarian")


class PartyURLTests(TestCase):
    """Tests for PartyURL model."""

    def test_person_social_links(self):
        """Person can have multiple URLs (website, social)."""
        person = Person.objects.create(first_name="Maria", last_name="Influencer")

        PartyURL.objects.create(
            person=person,
            url_type="website",
            url="https://maria-vet.com"
        )
        PartyURL.objects.create(
            person=person,
            url_type="linkedin",
            url="https://linkedin.com/in/maria-vet"
        )
        PartyURL.objects.create(
            person=person,
            url_type="instagram",
            url="https://instagram.com/maria_vet"
        )

        self.assertEqual(person.urls.count(), 3)

    def test_organization_urls(self):
        """Organization can have website and social links."""
        org = Organization.objects.create(name="ABC Clinic", org_type="clinic")

        PartyURL.objects.create(
            organization=org,
            url_type="website",
            url="https://abcclinic.com"
        )
        PartyURL.objects.create(
            organization=org,
            url_type="facebook",
            url="https://facebook.com/abcclinic"
        )

        self.assertEqual(org.urls.count(), 2)
