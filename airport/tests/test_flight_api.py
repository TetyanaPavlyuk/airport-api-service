from django.test import TestCase
from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from airport.models import (
    Flight,
    Airport,
    Route,
    AirplaneManufacturer,
    AirplaneType,
    Airplane,
    CrewPosition,
    Crew,
    Order,
    Ticket
)

from airport.serializers import FlightListSerializer


FLIGHT_URL = reverse("airport:flight-list")

fake = Faker()


def sample_crew():
    crew_position = CrewPosition.objects.create(
        name=fake.unique.job(),
    )

    return Crew.objects.create(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        position=crew_position
    )


def sample_flight(**params):
    airport1 = Airport.objects.create(
        name=fake.unique.company(),
        closest_big_city=fake.city()
    )

    airport2 = Airport.objects.create(
        name=fake.unique.company(),
        closest_big_city=fake.city()
    )

    route = Route.objects.create(
        source=airport1,
        destination=airport2,
        distance=600
    )

    airplane_manufacturer = AirplaneManufacturer.objects.create(
        name=fake.unique.company(),
    )

    airplane_type = AirplaneType.objects.create(
        name=fake.unique.name(),
        manufacturer=airplane_manufacturer
    )

    airplane = Airplane.objects.create(
        name=fake.unique.name(),
        rows=20,
        seats_in_row=6,
        airplane_type=airplane_type
    )

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": "2024-08-25 14:00:00+03:00",
        "arrival_time": "2024-08-25 16:00:00+03:00",
    }

    defaults.update(params)
    flight = Flight.objects.create(**defaults)

    crew1 = sample_crew()
    crew2 = sample_crew()
    flight.crew.add(crew1, crew2)
    flight.save()
    return flight


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(FLIGHT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser@mail.com",
            password="Password12345",
        )
        self.client.force_authenticate(user=self.user)

    def test_flight_list(self):
        flight1 = sample_flight()
        flight2 = sample_flight()
        order = Order.objects.create(
            user=self.user,
        )
        ticket = Ticket.objects.create(
            row=5,
            seat=3,
            flight=flight1,
            order=order
        )

        response = self.client.get(FLIGHT_URL)

        flights = Flight.objects.all()
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

