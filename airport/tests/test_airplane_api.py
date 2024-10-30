import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.urls import reverse

from django.test import TestCase
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import AirplaneType, Airplane, AirplaneManufacturer
from airport.serializers import (
    AirplaneListSerializer,
    AirplaneDetailSerializer
)

AIRPLANE_URL = reverse("airport:airplane-list")

fake = Faker()


def sample_airplane(**kwargs):
    airplane_type = AirplaneType.objects.create(
        name=fake.unique.company(),
    )
    defaults = {
        "name": fake.unique.name(),
        "rows": 20,
        "seats_in_row": 8,
        "airplane_type": airplane_type,
    }
    defaults.update(**kwargs)
    return Airplane.objects.create(**defaults)


def image_upload_url(airplane_id):
    """Return URL for recipe image upload"""
    return reverse(
        "airport:airplane-upload-image",
        args=[airplane_id]
    )


def detail_url(airplane_id):
    return reverse("airport:airplane-detail", args=[airplane_id])


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@mail.com",
            "TestPassword12345",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplanes(self):
        sample_airplane()
        sample_airplane()

        response = self.client.get(AIRPLANE_URL)

        airplanes = Airplane.objects.order_by("id")
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_airplane_detail(self):
        airplane = sample_airplane()

        url = detail_url(airplane.id)
        response = self.client.get(url)

        serializer = AirplaneDetailSerializer(airplane)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = AirplaneType.objects.create(
            name="Airplane Type"
        )
        payload = {
            "name": "Airplane",
            "rows": 20,
            "seats_in_row": 8,
            "airplane_type": airplane_type,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@mail.com", "TestPassword12345", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_manufacturer = AirplaneManufacturer.objects.create(
            name="Manufacturer"
        )
        airplane_type = AirplaneType.objects.create(
            name="Airplane Type",
            manufacturer=airplane_manufacturer,
        )
        payload = {
            "name": "Airplane",
            "rows": 20,
            "seats_in_row": 8,
            "airplane_type": airplane_type.id,
        }
        response = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(id=response.data["id"])
        for key in payload.keys():
            if key == "airplane_type":
                self.assertEqual(payload[key], getattr(airplane, key).id)
            else:
                self.assertEqual(payload[key], getattr(airplane, key))

    def test_put_airplane_not_allowed(self):
        payload = {
            "name": "Airplane",
            "rows": "10",
            "seats_in_row": 4,
        }

        airplane = sample_airplane()
        url = detail_url(airplane.id)

        response = self.client.put(url, payload)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_airplane_not_allowed(self):
        airplane = sample_airplane()
        url = detail_url(airplane.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@mail.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.airplane = sample_airplane()

    def tearDown(self):
        self.airplane.image.delete()

    def test_upload_image_to_airplane(self):
        """Test uploading an image to airplane"""
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                url,
                {"image": ntf},
                format="multipart"
            )
        self.airplane.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.airplane.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.airplane.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_airplane_list_should_not_work(self):
        url = AIRPLANE_URL
        airplane_type = AirplaneType.objects.create(
            name="Airplane Type"
        )
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Airplane",
                    "rows": 20,
                    "seats_in_row": 8,
                    "airplane_type": airplane_type.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(name="Airplane")
        self.assertFalse(airplane.image)

    def test_image_url_is_shown_on_airplane_detail(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.airplane.id))

        self.assertIn("image", res.data)
