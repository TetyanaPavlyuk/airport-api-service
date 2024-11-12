from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
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

from airport.serializers import FlightListSerializer, FlightDetailSerializer

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
        order = Order.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            row=5,
            seat=3,
            flight=flight1,
            order=order
        )
        flight1.save()
        flight2 = sample_flight()
        flight2.save()

        response = self.client.get(FLIGHT_URL)

        flights = Flight.objects.all()
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data["results"], serializer.data)

    def test_filter_flights_by_source_airport(self):
        airport_in = Airport.objects.create(name="Airport1")
        airport_out = Airport.objects.create(name="Airport2")
        route_in = Route.objects.create(
            source=airport_in,
            destination=airport_out,
            distance=600
        )
        route_out = Route.objects.create(
            source=airport_out,
            destination=airport_in,
            distance=600
        )
        flight_in = sample_flight(route=route_in)
        flight_out = sample_flight(route=route_out)

        response = self.client.get(
            FLIGHT_URL,
            {"source_airport": f"{airport_in.name}"}
        )

        serializer_in = FlightListSerializer(flight_in)
        serializer_out = FlightListSerializer(flight_out)
        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_flights_by_destination_airport(self):
        airport_in = Airport.objects.create(name="Airport1")
        airport_out = Airport.objects.create(name="Airport2")
        route_in = Route.objects.create(
            source=airport_out,
            destination=airport_in,
            distance=600
        )
        route_out = Route.objects.create(
            source=airport_in,
            destination=airport_out,
            distance=600
        )
        flight_in = sample_flight(route=route_in)
        flight_out = sample_flight(route=route_out)

        response = self.client.get(
            FLIGHT_URL,
            {"destination_airport": f"{airport_in.name}"}
        )

        serializer_in = FlightListSerializer(flight_in)
        serializer_out = FlightListSerializer(flight_out)

        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_flights_by_source_city(self):
        airport_in = Airport.objects.create(
            name="Airport1",
            closest_big_city="City1"
        )
        airport_out = Airport.objects.create(
            name="Airport2",
            closest_big_city="City2"
        )
        route_in = Route.objects.create(
            source=airport_in,
            destination=airport_out,
            distance=600
        )
        route_out = Route.objects.create(
            source=airport_out,
            destination=airport_in,
            distance=600
        )
        flight_in = sample_flight(route=route_in)
        flight_out = sample_flight(route=route_out)

        response = self.client.get(
            FLIGHT_URL,
            {"source_city": f"{airport_in.closest_big_city}"}
        )

        serializer_in = FlightListSerializer(flight_in)
        serializer_out = FlightListSerializer(flight_out)
        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_flights_by_destination_city(self):
        airport_in = Airport.objects.create(
            name="Airport1",
            closest_big_city="City1"
        )
        airport_out = Airport.objects.create(
            name="Airport2",
            closest_big_city="City2"
        )
        route_in = Route.objects.create(
            source=airport_out,
            destination=airport_in,
            distance=600
        )
        route_out = Route.objects.create(
            source=airport_in,
            destination=airport_out,
            distance=600
        )
        flight_in = sample_flight(route=route_in)
        flight_out = sample_flight(route=route_out)

        response = self.client.get(
            FLIGHT_URL,
            {"destination_city": f"{airport_in.closest_big_city}"}
        )

        serializer_in = FlightListSerializer(flight_in)
        serializer_out = FlightListSerializer(flight_out)

        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_flights_by_airplane(self):
        airplane_type = AirplaneType.objects.create(name="Airplane Type")

        airplane_in = Airplane.objects.create(
            name="Airplane1",
            rows=20,
            seats_in_row=8,
            airplane_type=airplane_type
        )
        airplane_out = Airplane.objects.create(
            name="Airplane2",
            rows=20,
            seats_in_row=8,
            airplane_type=airplane_type
        )

        flight_in = sample_flight(airplane=airplane_in)
        flight_out = sample_flight(airplane=airplane_out)

        response = self.client.get(
            FLIGHT_URL,
            {"airplane": f"{airplane_in.name}"}
        )

        serializer_in = FlightListSerializer(flight_in)
        serializer_out = FlightListSerializer(flight_out)

        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_flights_by_crew(self):
        crew_position = CrewPosition.objects.create(name="Crew Position")

        crew1 = Crew.objects.create(
            first_name="First Name 1",
            last_name="Last Name 1",
            position=crew_position
        )
        crew2 = Crew.objects.create(
            first_name="First Name 2",
            last_name="Last Name 2",
            position=crew_position
        )
        crew3 = Crew.objects.create(
            first_name="First Name 3",
            last_name="Last Name 3",
            position=crew_position
        )

        flight1_in = sample_flight()
        flight1_in.crew.add(crew1)
        flight2_in = sample_flight()
        flight2_in.crew.add(crew2)
        flight2_in.crew.add(crew3)
        flight_out = sample_flight()
        flight_out.crew.add(crew3)

        response = self.client.get(
            FLIGHT_URL,
            {"crew": f"{crew1.id}, {crew2.id}"}
        )

        serializer1_in = FlightListSerializer(flight1_in)
        serializer2_in = FlightListSerializer(flight2_in)
        serializer_out = FlightListSerializer(flight_out)

        self.assertIn(serializer1_in.data, response.data["results"])
        self.assertIn(serializer2_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_flights_by_date_departure(self):
        flight_eq = sample_flight(
            departure_time="2024-08-27 15:00:00+03:00",
            arrival_time="2024-08-27 17:00:00+03:00",
        )
        flight_qt = sample_flight(
            departure_time="2024-08-28 15:00:00+03:00",
            arrival_time="2024-08-28 17:00:00+03:00",
        )
        flight_lt = sample_flight(
            departure_time="2024-08-26 15:00:00+03:00",
            arrival_time="2024-08-26 17:00:00+03:00",
        )

        response = self.client.get(
            FLIGHT_URL, {"date_departure": "2024-08-27"}
        )

        serializer_eq = FlightListSerializer(flight_eq)
        serializer_qt = FlightListSerializer(flight_qt)
        serializer_lt = FlightListSerializer(flight_lt)

        self.assertIn(serializer_eq.data, response.data["results"])
        self.assertIn(serializer_qt.data, response.data["results"])
        self.assertNotIn(serializer_lt.data, response.data["results"])

    def test_filter_flights_by_date_arrival(self):
        flight_eq = sample_flight(
            departure_time="2024-08-27 15:00:00+03:00",
            arrival_time="2024-08-27 17:00:00+03:00",
        )
        flight_qt = sample_flight(
            departure_time="2024-08-28 15:00:00+03:00",
            arrival_time="2024-08-28 17:00:00+03:00",
        )
        flight_lt = sample_flight(
            departure_time="2024-08-26 15:00:00+03:00",
            arrival_time="2024-08-26 17:00:00+03:00",
        )

        response = self.client.get(
            FLIGHT_URL, {"date_arrival": "2024-08-27"}
        )

        serializer_eq = FlightListSerializer(flight_eq)
        serializer_qt = FlightListSerializer(flight_qt)
        serializer_lt = FlightListSerializer(flight_lt)

        self.assertIn(serializer_eq.data, response.data["results"])
        self.assertIn(serializer_qt.data, response.data["results"])
        self.assertNotIn(serializer_lt.data, response.data["results"])

    def test_retrieve_flight_detail(self):
        flight = sample_flight()
        url = detail_url(flight.id)
        response = self.client.get(url)
        serializer = FlightDetailSerializer(flight)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_flight_forbidden(self):
        airport1 = Airport.objects.create(name="Airport1")
        airport2 = Airport.objects.create(name="Airport2")
        route = Route.objects.create(
            source=airport1,
            destination=airport2,
            distance=600
        )
        airplane_manufacturer = AirplaneManufacturer.objects.create(
            name="Manufacturer"
        )
        airplane_type = AirplaneType.objects.create(
            name="Airplane Type",
            manufacturer=airplane_manufacturer
        )
        airplane = Airplane.objects.create(
            name="Airplane",
            rows=20,
            seats_in_row=8,
            airplane_type=airplane_type
        )
        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2024-08-27 15:00:00+03:00",
            "arrival_time": "2024-08-27 17:00:00+03:00",
        }

        response = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email="admin@mail.com",
            password="TestPassword12345",
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_flight(self):
        airport1 = Airport.objects.create(name="Airport1")
        airport2 = Airport.objects.create(name="Airport2")
        route = Route.objects.create(
            source=airport1,
            destination=airport2,
            distance=600
        )
        airplane_manufacturer = AirplaneManufacturer.objects.create(
            name="Manufacturer"
        )
        airplane_type = AirplaneType.objects.create(
            name="Airplane Type",
            manufacturer=airplane_manufacturer
        )
        airplane = Airplane.objects.create(
            name="Airplane",
            rows=20,
            seats_in_row=8,
            airplane_type=airplane_type
        )
        crew_position = CrewPosition.objects.create(
            name="Crew Position",
        )
        crew1 = Crew.objects.create(
            first_name="First Name1",
            last_name="Last Name1",
            position=crew_position,
        )
        crew2 = Crew.objects.create(
            first_name="First Name2",
            last_name="Last Name2",
            position=crew_position,
        )

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": "2024-08-27 15:00:00+03:00",
            "arrival_time": "2024-08-27 17:00:00+03:00",
            "crew": [crew1.id, crew2.id]
        }

        response = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        flight = Flight.objects.get(id=response.data["id"])
        for key in ["route", "airplane"]:
            self.assertEqual(payload[key], getattr(flight, key).id)

        for key in ["departure_time", "arrival_time"]:
            self.assertEqual(
                parse_datetime(payload[key]),
                getattr(flight, key)
            )

        crews = flight.crew.all()
        self.assertEqual(crews.count(), 2)
        self.assertIn(crew1, crews)
        self.assertIn(crew2, crews)

    def test_put_flight_not_allowed(self):
        payload = {
            "departure_time": "2024-08-27 10:00:00+03:00",
            "arrival_time": "2024-08-27 13:00:00+03:00",
        }

        flight = sample_flight()
        url = detail_url(flight.id)

        response = self.client.put(url, payload)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_flight_not_allowed(self):
        flight = sample_flight()
        url = detail_url(flight.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
