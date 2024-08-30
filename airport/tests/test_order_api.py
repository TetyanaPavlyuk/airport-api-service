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
from airport.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderSerializer
)

ORDER_URL = reverse("airport:order-list")

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


def detail_url(order_id):
    return reverse("airport:order-detail", args=[order_id])


class UnauthenticatedOrderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ORDER_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser@mail.com",
            password="Password12345",
        )
        self.client.force_authenticate(user=self.user)

    def test_order_list(self):
        flight = sample_flight()
        order1 = Order.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            row=5,
            seat=3,
            flight=flight,
            order=order1
        )
        Ticket.objects.create(
            row=6,
            seat=3,
            flight=flight,
            order=order1
        )
        order2 = Order.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            row=7,
            seat=3,
            flight=flight,
            order=order2
        )

        response = self.client.get(ORDER_URL)

        orders = Order.objects.all().order_by("id")
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data["results"], serializer.data)

    def test_retrieve_order_detail(self):
        flight = sample_flight()
        order = Order.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            row=5,
            seat=3,
            flight=flight,
            order=order
        )
        Ticket.objects.create(
            row=6,
            seat=3,
            flight=flight,
            order=order
        )
        url = detail_url(order.id)
        response = self.client.get(url)
        serializer = OrderDetailSerializer(order)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_order(self):
        flight = sample_flight()

        payload = {
            "tickets": [
                {
                    "row": 5,
                    "seat": 1,
                    "flight": flight.id
                },
                {
                    "row": 5,
                    "seat": 2,
                    "flight": flight.id
                }
            ]
        }

        response = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=response.data["id"])
        serializer = OrderSerializer(order)

        for ticket in response.data["tickets"]:
            self.assertIn(ticket, serializer.data["tickets"])

        self.assertEqual(
            response.data["created_at"],
            serializer.data["created_at"]
        )

    def test_put_order_not_allowed(self):
        flight = sample_flight()
        order = Order.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            row=5,
            seat=3,
            flight=flight,
            order=order
        )
        payload = {
            "tickets": [
                {
                    "row": 5,
                    "seat": 1,
                    "flight": flight.id
                }
            ]
        }

        url = detail_url(order.id)

        response = self.client.put(url, payload)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_order(self):
        flight = sample_flight()
        order = Order.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            row=5,
            seat=3,
            flight=flight,
            order=order
        )

        url = detail_url(order.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
