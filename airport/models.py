import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Airport(models.Model):
    name = models.CharField(max_length=255, unique=True)
    closest_big_city = models.CharField(max_length=255)

    @property
    def name_city(self) -> str:
        return f"{self.name} ({self.closest_big_city})"

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"

    class Meta:
        ordering = ["name"]


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="source_routes"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="destination_routes"
    )
    distance = models.IntegerField()

    @property
    def source_dest(self) -> str:
        return f"{self.source} - {self.destination}"

    def __str__(self):
        return (f"{self.source.name} - {self.destination.name} "
                f"({self.distance} km)")

    class Meta:
        ordering = ["source", "destination"]


class AirplaneManufacturer(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.ForeignKey(
        AirplaneManufacturer,
        on_delete=models.SET_NULL,
        related_name="airplane_types",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.manufacturer})"

    class Meta:
        ordering = ["name", "manufacturer"]
        unique_together = ["name", "manufacturer"]


def airplane_image_path(instance: "Airplane", filename: str) -> str:
    _, extention = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extention}"
    return os.path.join("uploads/airplanes/", filename)


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes"
    )
    image = models.ImageField(null=True, upload_to=airplane_image_path)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type.name})"

    class Meta:
        ordering = ["name"]


class CrewPosition(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    position = models.ForeignKey(CrewPosition, on_delete=models.CASCADE)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def position_name(self) -> str:
        return f"{self.position}: {self.full_name}"

    def __str__(self):
        return f"{self.position}: {self.first_name} {self.last_name}"

    class Meta:
        ordering = ["position", "first_name", "last_name"]
        unique_together = ["position", "first_name", "last_name"]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    def __str__(self):
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")

    class Meta:
        ordering = ["-created_at"]


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew)

    @property
    def tickets_available(self) -> int:
        return self.airplane.capacity - self.tickets.count()

    def clean(self):
        if self.departure_time >= self.arrival_time:
            raise ValidationError("Arrival time must be later than "
                                  "departure time.")

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        return super(Flight, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return (f"{self.route.source} "
                f"({self.departure_time.strftime("%Y-%m-%d %H:%M:%S")}) - "
                f"{self.route.destination} "
                f"({self.arrival_time.strftime("%Y-%m-%d %H:%M:%S")})")

    class Meta:
        ordering = ["departure_time", "route", "airplane"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_name, ticket_attr_value, airplane_attr_name in [
            ("row", row, "rows"),
            ("seat", seat, "seats_in_row")
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (0 < ticket_attr_value < count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} number must"
                                          f"be in available range: "
                                          f"(1, {airplane_attr_name}): "
                                          f"(1, {count_attrs}"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return f"{self.flight} (seat: {self.seat}, row: {self.row})"

    class Meta:
        ordering = ["-order", "flight", "row", "seat"]
        unique_together = ["row", "seat", "flight"]
