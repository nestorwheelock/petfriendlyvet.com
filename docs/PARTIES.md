# Parties Module

The `apps.parties` module implements the **Party Pattern** - an enterprise-grade data model for managing people, organizations, groups, and their relationships. This is the foundation for all identity and ownership in the system.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Models](#models)
  - [Person](#person)
  - [Organization](#organization)
  - [Group](#group)
  - [PartyRelationship](#partyrelationship)
  - [Address](#address)
  - [Phone](#phone)
  - [Email](#email)
  - [Demographics](#demographics)
  - [PartyURL](#partyurl)
- [Key Design Decisions](#key-design-decisions)
- [Person vs User](#person-vs-user)
- [Ownership Patterns](#ownership-patterns)
- [Relationship Types](#relationship-types)
- [Query Examples](#query-examples)
- [Integration Points](#integration-points)
- [Migration from Legacy Models](#migration-from-legacy-models)

## Overview

The parties module provides a unified approach to managing all entities that can:

- **Own things** (pets, vehicles, property)
- **Have relationships** (employee, vendor, customer)
- **Do business** (buy, sell, contract)
- **Be billed or bill others**

This pattern is used in enterprise systems like Salesforce (Account/Contact), SAP (Business Partner), and healthcare (HL7 FHIR).

```
┌─────────────────────────────────────────────────────────────────┐
│                    PARTIES APP (Identity)                       │
│                                                                 │
│   Person ─────────────┐                                        │
│   Organization ───────┼──► Party (abstract base)               │
│   Group ──────────────┘                                        │
│                                                                 │
│   PartyRelationship → connects any parties                     │
│   Address, Phone, Email, Demographics, PartyURL → normalized   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ACCOUNTS APP (Auth only)                     │
│                                                                 │
│   User (login account) ──► FK to Person (optional)             │
│   One Person can have MANY User accounts                       │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

### Party Types

| Type | Description | Examples |
|------|-------------|----------|
| **Person** | Individual human being | Juan Garcia, Dr. Maria Lopez |
| **Organization** | Formal business entity | ABC Veterinary Clinic, PetFood Inc, City Zoo |
| **Group** | Informal grouping | The Martinez Household, Family trust |

### Core Principle: Identity vs Authentication

The system separates **identity** (who you are) from **authentication** (how you log in):

- **Person** = real-world human identity (in `parties` app)
- **User** = login account (in `accounts` app)

This allows:
- One Person can have multiple User accounts (email login + Google OAuth)
- A Person can exist without any User account (contacts, leads)
- A User can exist without a Person (API/service accounts)

## Models

### Person

Location: `apps/parties/models.py`

A human being - the real-world identity separate from login accounts.

```python
class Person(Party):
    """A human being - the real-world identity."""

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)
    preferred_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=300, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
```

**Key Methods:**

```python
# Get full name
person.get_full_name()  # "Juan Carlos Garcia"

# Get preferred name
person.get_short_name()  # "Juanito" or first_name

# Calculate age
person.age  # 35 (from date_of_birth)

# Check for login accounts
person.has_account  # True/False
person.primary_account  # First active User account
person.accounts.all()  # All User accounts for this person
```

### Organization

Location: `apps/parties/models.py`

A formal business entity - company, clinic, school, supplier.

```python
class Organization(Party):
    """A formal business entity."""

    ORGANIZATION_TYPES = [
        ('clinic', 'Veterinary Clinic'),
        ('rescue', 'Animal Rescue/Shelter'),
        ('supplier', 'Supplier/Distributor'),
        ('school', 'School/Institution'),
        ('partner', 'Business Partner'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPES)
    website = models.URLField(blank=True)
    tax_id = models.CharField(max_length=20, blank=True)  # RFC in Mexico
    legal_name = models.CharField(max_length=255, blank=True)
    api_account = models.OneToOneField('accounts.User', null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### Group

Location: `apps/parties/models.py`

An informal grouping of people - household, family, partnership.

```python
class Group(Party):
    """An informal grouping of people."""

    GROUP_TYPES = [
        ('household', 'Household'),
        ('family', 'Family'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES)
    primary_contact = models.ForeignKey('Person', null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### PartyRelationship

Location: `apps/parties/models.py`

Links any two parties with a typed relationship.

```python
class PartyRelationship(models.Model):
    """Relationship between any two parties."""

    RELATIONSHIP_TYPES = [
        # Person → Organization
        ('employee', 'Employee'),
        ('contractor_individual', 'Individual Contractor (1099)'),
        ('contact', 'Contact'),
        ('owner', 'Owner/Executive'),
        # Organization → Organization
        ('contractor_org', 'Contractor Organization'),
        ('vendor', 'Vendor/Supplier'),
        ('partner', 'Business Partner'),
        ('client', 'Client/Customer'),
        # Person → Group
        ('member', 'Member'),
        ('head', 'Head of Household'),
        ('spouse', 'Spouse/Partner'),
        ('dependent', 'Dependent'),
        # Person → Person
        ('emergency_contact', 'Emergency Contact'),
        ('guardian', 'Guardian'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
    ]

    # From party
    from_person = models.ForeignKey('Person', null=True, blank=True)
    from_organization = models.ForeignKey('Organization', null=True, blank=True)

    # To party
    to_person = models.ForeignKey('Person', null=True, blank=True)
    to_organization = models.ForeignKey('Organization', null=True, blank=True)
    to_group = models.ForeignKey('Group', null=True, blank=True)

    relationship_type = models.CharField(max_length=30, choices=RELATIONSHIP_TYPES)
    title = models.CharField(max_length=100, blank=True)  # Job title

    # Contract details
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    contract_signed = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
```

### Address

Location: `apps/parties/models.py`

Normalized address table - any party can have multiple addresses.

```python
class Address(models.Model):
    """Physical or mailing address for any party."""

    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('mailing', 'Mailing'),
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
        ('other', 'Other'),
    ]

    # Link to party (one must be set)
    person = models.ForeignKey('Person', null=True, blank=True, related_name='addresses')
    organization = models.ForeignKey('Organization', null=True, blank=True)
    group = models.ForeignKey('Group', null=True, blank=True)

    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES)
    is_primary = models.BooleanField(default=False)

    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Mexico')

    # Geolocation
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
```

### Phone

Location: `apps/parties/models.py`

Normalized phone table with SMS/WhatsApp capabilities.

```python
class Phone(models.Model):
    """Phone number for any party."""

    PHONE_TYPES = [
        ('mobile', 'Mobile'),
        ('home', 'Home'),
        ('work', 'Work'),
        ('fax', 'Fax'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Other'),
    ]

    person = models.ForeignKey('Person', null=True, blank=True, related_name='phone_numbers')
    organization = models.ForeignKey('Organization', null=True, blank=True)
    group = models.ForeignKey('Group', null=True, blank=True)

    phone_type = models.CharField(max_length=20, choices=PHONE_TYPES)
    is_primary = models.BooleanField(default=False)

    country_code = models.CharField(max_length=5, default='+52')
    number = models.CharField(max_length=20)
    extension = models.CharField(max_length=10, blank=True)

    is_verified = models.BooleanField(default=False)
    can_receive_sms = models.BooleanField(default=True)
    can_receive_whatsapp = models.BooleanField(default=False)
```

### Email

Location: `apps/parties/models.py`

Normalized email table with marketing preferences.

```python
class Email(models.Model):
    """Email address for any party."""

    EMAIL_TYPES = [
        ('personal', 'Personal'),
        ('work', 'Work'),
        ('billing', 'Billing'),
        ('newsletter', 'Newsletter'),
        ('other', 'Other'),
    ]

    person = models.ForeignKey('Person', null=True, blank=True, related_name='email_addresses')
    organization = models.ForeignKey('Organization', null=True, blank=True)
    group = models.ForeignKey('Group', null=True, blank=True)

    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)
    is_primary = models.BooleanField(default=False)
    email = models.EmailField()

    is_verified = models.BooleanField(default=False)
    receives_marketing = models.BooleanField(default=False)
    receives_transactional = models.BooleanField(default=True)
```

### Demographics

Location: `apps/parties/models.py`

Extended demographics for a Person.

```python
class Demographics(models.Model):
    """Extended demographics for a Person."""

    person = models.OneToOneField('Person', on_delete=models.CASCADE, related_name='demographics')

    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)

    nationality = models.CharField(max_length=100, blank=True)
    country_of_birth = models.CharField(max_length=100, blank=True)
    ethnicity = models.CharField(max_length=100, blank=True)

    preferred_language = models.CharField(max_length=10, default='es')
    additional_languages = models.JSONField(default=list)

    education_level = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=200, blank=True)

    household_size = models.PositiveIntegerField(null=True, blank=True)
    has_children = models.BooleanField(null=True, blank=True)
    number_of_children = models.PositiveIntegerField(null=True, blank=True)
```

### PartyURL

Location: `apps/parties/models.py`

Websites and social media profiles.

```python
class PartyURL(models.Model):
    """Website or social media URL for any party."""

    URL_TYPES = [
        ('website', 'Website'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('whatsapp', 'WhatsApp Business'),
        ('google_maps', 'Google Maps'),
        ('yelp', 'Yelp'),
        ('github', 'GitHub'),
        ('portfolio', 'Portfolio'),
        ('blog', 'Blog'),
        ('other', 'Other'),
    ]

    person = models.ForeignKey('Person', null=True, blank=True, related_name='urls')
    organization = models.ForeignKey('Organization', null=True, blank=True)
    group = models.ForeignKey('Group', null=True, blank=True)

    url_type = models.CharField(max_length=20, choices=URL_TYPES)
    url = models.URLField(max_length=500)
    username = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
```

## Key Design Decisions

### 1. Person Separate from User

**Why:** A Person (real-world identity) is different from a User (login account).

| Scenario | Person | User Accounts |
|----------|--------|---------------|
| Customer with email + Google login | 1 | 2 |
| Business contact (no login) | 1 | 0 |
| API service account | 0 | 1 |
| Family sharing one login | 3 | 1 |

### 2. Explicit Foreign Keys vs Generic Relations

**Why:** Better performance, cleaner queries, database integrity.

```python
# We use explicit FKs
class Pet:
    owner_person = ForeignKey('Person')
    owner_group = ForeignKey('Group')
    owner_organization = ForeignKey('Organization')

# Instead of GenericForeignKey (avoided)
class Pet:
    owner_content_type = ForeignKey(ContentType)
    owner_object_id = PositiveIntegerField()
    owner = GenericForeignKey()
```

### 3. Normalized Contact Tables

**Why:** People/orgs have multiple addresses, phones, emails with different purposes.

```python
# One person with multiple addresses
person.addresses.filter(address_type='home')
person.addresses.filter(address_type='work')

# Primary email for billing
person.email_addresses.filter(is_primary=True, email_type='billing')
```

## Person vs User

### User Model (accounts app)

The User model is for **authentication only**:

```python
class User(AbstractUser):
    """Login account - for authentication."""

    person = models.ForeignKey('parties.Person', null=True, related_name='accounts')
    auth_method = models.CharField(choices=['email', 'phone', 'google', 'api_key'])
    # Django auth fields: username, password, is_active, etc.
```

### Person Model (parties app)

The Person model is for **identity**:

```python
class Person(Party):
    """Real-world human - for identity and business."""

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    # Business relationships, contact info, demographics
```

### Linking Them

```python
# Create a person
person = Person.objects.create(
    first_name='Juan',
    last_name='Garcia'
)

# Create a login account for that person
user = User.objects.create(
    person=person,
    email='juan@example.com',
    auth_method='email'
)

# Person can have multiple accounts
User.objects.create(
    person=person,
    auth_method='google'
)

# Get person from user
user.person.get_full_name()  # "Juan Garcia"

# Get accounts from person
person.accounts.all()  # [User(email), User(google)]
```

## Ownership Patterns

### Pet Ownership Examples

```python
from apps.pets.models import Pet, PetResponsibility
from apps.parties.models import Person, Organization, Group

# 1. Individual owns a pet
person = Person.objects.get(pk=1)
pet = Pet.objects.create(
    owner_person=person,
    name='Max',
    species='dog'
)

# 2. Household owns a pet (spouses sharing)
household = Group.objects.create(
    name='The Smith Household',
    group_type='household'
)
pet = Pet.objects.create(
    owner_group=household,
    name='Bella',
    species='cat'
)

# 3. Organization owns animals (zoo)
zoo = Organization.objects.create(
    name='City Zoo',
    org_type='other'
)
elephant = Pet.objects.create(
    owner_organization=zoo,
    name='Dumbo',
    species='other'
)

# Multiple responsible parties
PetResponsibility.objects.create(
    pet=elephant,
    person=head_keeper,
    responsibility_type='primary'
)
PetResponsibility.objects.create(
    pet=elephant,
    person=assistant_keeper,
    responsibility_type='secondary'
)
```

## Relationship Types

### Person → Organization

```python
# Employee relationship
PartyRelationship.objects.create(
    from_person=juan,
    to_organization=clinic,
    relationship_type='employee',
    title='Veterinary Technician',
    is_primary=True
)

# Contractor relationship
PartyRelationship.objects.create(
    from_person=maria,
    to_organization=clinic,
    relationship_type='contractor_individual',
    contract_start=date(2024, 1, 1),
    contract_end=date(2024, 12, 31)
)
```

### Person → Group

```python
# Household members
PartyRelationship.objects.create(
    from_person=juan,
    to_group=household,
    relationship_type='head'
)
PartyRelationship.objects.create(
    from_person=maria,
    to_group=household,
    relationship_type='spouse'
)
```

### Organization → Organization

```python
# Vendor relationship
PartyRelationship.objects.create(
    from_organization=supplier,
    to_organization=clinic,
    relationship_type='vendor'
)
```

## Query Examples

### Find All Employees of an Organization

```python
from apps.parties.models import PartyRelationship

# Get all employee relationships
employees = PartyRelationship.objects.filter(
    to_organization=clinic,
    relationship_type='employee',
    is_active=True
).select_related('from_person')

for rel in employees:
    print(f"{rel.from_person.get_full_name()} - {rel.title}")
```

### Find All Organizations a Person Works For

```python
orgs = PartyRelationship.objects.filter(
    from_person=person,
    relationship_type__in=['employee', 'contractor_individual'],
    is_active=True
).select_related('to_organization')
```

### Find Household Members

```python
members = PartyRelationship.objects.filter(
    to_group=household,
    is_active=True
).select_related('from_person')
```

### Find Primary Contact Info

```python
# Primary email
email = person.email_addresses.filter(is_primary=True).first()

# Primary phone
phone = person.phone_numbers.filter(is_primary=True).first()

# Primary address
address = person.addresses.filter(is_primary=True).first()
```

## Integration Points

### With Pets Module

```python
from apps.pets.models import Pet

# Get all pets owned by a person
pets = Pet.objects.filter(owner_person=person)

# Get all pets a person is responsible for
from apps.pets.models import PetResponsibility
responsibilities = PetResponsibility.objects.filter(
    person=person,
    is_active=True
).select_related('pet')
```

### With HR Module

```python
from apps.hr.models import EmploymentDetails

# Get employment details via relationship
relationship = PartyRelationship.objects.get(
    from_person=person,
    to_organization=clinic,
    relationship_type='employee'
)
employment = relationship.employment_details
```

### With Accounts Module

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Get person from authenticated user
person = request.user.person

# Check if person has any login accounts
if person.has_account:
    accounts = person.accounts.all()
```

## Migration from Legacy Models

### Migrating User Data to Person

For existing systems where User contains identity data:

```python
from apps.accounts.models import User
from apps.parties.models import Person

def migrate_users_to_persons():
    for user in User.objects.filter(person__isnull=True):
        person = Person.objects.create(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email or '',
            phone=user.phone_number or '',
        )
        user.person = person
        user.save()
```

### Migrating Pet Ownership

For existing systems where Pet.owner points to User:

```python
from apps.pets.models import Pet
from apps.parties.models import Person

def migrate_pet_ownership():
    for pet in Pet.objects.filter(owner__isnull=False, owner_person__isnull=True):
        if pet.owner.person:
            pet.owner_person = pet.owner.person
            pet.save()
```
