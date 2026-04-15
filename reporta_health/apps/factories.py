"""
Factory Boy factories for all Reporta Health models.

These are registered as pytest fixtures in conftest_factories.py.
Import pattern: use the *_factory fixtures in your tests, never
instantiate factories directly — keeps DB lifecycle tied to pytest-django.

Usage in tests:
    def test_something(facility_factory):
        f = facility_factory(name="Test Clinic", is_verified=True)
"""

import factory
import factory.fuzzy
from django.contrib.gis.geos import Point
from factory.django import DjangoModelFactory


# ---------------------------------------------------------------------------
# UserFactory
# ---------------------------------------------------------------------------

class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'users.User'
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    phone_number = factory.Faker('numerify', text='+234##########')
    is_verified = True
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password — default is 'testpass123' unless overridden."""
        pwd = extracted or 'testpass123'
        obj.set_password(pwd)
        if create:
            obj.save()


# ---------------------------------------------------------------------------
# FacilityFactory
# ---------------------------------------------------------------------------

class FacilityFactory(DjangoModelFactory):
    class Meta:
        model = 'facilities.Facility'

    name = factory.Sequence(lambda n: f'Test Clinic {n}')
    facility_type = factory.fuzzy.FuzzyChoice([
        'hospital', 'clinic', 'pharmacy', 'laboratory', 'maternity'
    ])
    address = factory.Faker('street_address')
    state = 'Lagos'
    lga = factory.Faker('city')

    # Default location: central Lagos
    location = factory.LazyFunction(lambda: Point(3.3792, 6.5244, srid=4326))
    phone_number = factory.Faker('numerify', text='+234##########')
    email = factory.Sequence(lambda n: f'facility{n}@example.com')
    is_verified = True
    is_active = True

    # Operating hours — default: open Mon–Fri 8am–5pm
    operating_hours = factory.LazyFunction(lambda: {
        'monday':    {'open': '08:00', 'close': '17:00'},
        'tuesday':   {'open': '08:00', 'close': '17:00'},
        'wednesday': {'open': '08:00', 'close': '17:00'},
        'thursday':  {'open': '08:00', 'close': '17:00'},
        'friday':    {'open': '08:00', 'close': '17:00'},
        'saturday':  None,
        'sunday':    None,
    })


# ---------------------------------------------------------------------------
# ReviewFactory
# ---------------------------------------------------------------------------

class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = 'reviews.Review'

    user = factory.SubFactory(UserFactory)
    facility = factory.SubFactory(FacilityFactory)
    rating = factory.fuzzy.FuzzyInteger(1, 5)
    body = factory.Faker('paragraph', nb_sentences=3)
    is_anonymous = False
    is_published = True
    flag_count = 0


# ---------------------------------------------------------------------------
# ReportFactory
# ---------------------------------------------------------------------------

class ReportFactory(DjangoModelFactory):
    class Meta:
        model = 'reports.FacilityReport'

    reporter = factory.SubFactory(UserFactory)
    facility = factory.SubFactory(FacilityFactory)
    reason = factory.fuzzy.FuzzyChoice([
        'fake', 'closed', 'wrong_info', 'inappropriate', 'duplicate', 'spam', 'other'
    ])
    
    description = factory.Faker('paragraph', nb_sentences=4)
    status = 'pending'
