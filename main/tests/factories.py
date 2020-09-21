import uuid

import factory.fuzzy


class UserFactory(factory.django.DjangoModelFactory):
    first_name = factory.fuzzy.FuzzyText()
    last_name = factory.fuzzy.FuzzyText()
    email = factory.LazyAttribute(
        lambda u: "{}.{}@example.com".format(u.first_name, u.last_name).lower()
    )

    class Meta:
        model = "custom_usermodel.User"


class BuildingFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText()

    class Meta:
        model = "main.Building"


class FloorFactory(factory.django.DjangoModelFactory):
    building = factory.SubFactory(BuildingFactory)
    name = factory.fuzzy.FuzzyText()
    nr_of_desks = factory.fuzzy.FuzzyInteger(low=0)

    class Meta:
        model = "main.Floor"


class BookingFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    on_behalf_of_name = factory.fuzzy.FuzzyText()
    on_behalf_of_dit_email = factory.LazyAttribute(lambda _: f"{uuid.uuid4()}@example.com")
    building = factory.SubFactory(BuildingFactory)
    floor = factory.SubFactory(FloorFactory)
    directorate = factory.fuzzy.FuzzyText()
    group = factory.fuzzy.FuzzyText()
    business_unit = factory.fuzzy.FuzzyText()

    class Meta:
        model = "main.Booking"
