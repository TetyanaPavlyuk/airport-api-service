from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    Airplane,
    AirplaneType,
    AirplaneManufacturer,
    Airport,
    Route,
    CrewPosition,
    Crew,
    Order,
    Flight,
    Ticket,
)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(source="source.name_city", read_only=True)
    destination = serializers.CharField(
        source="destination.name_city", read_only=True
    )


class AirplaneManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneManufacturer
        fields = ["id", "name"]


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name", "manufacturer"]


class AirplaneTypeListSerializer(AirplaneTypeSerializer):
    manufacturer = serializers.CharField(
        source="manufacturer.name", read_only=True
    )


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "image"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type"]


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name", read_only=True
    )
    airplane_manufacturer = serializers.CharField(
        source="airplane_type.manufacturer.name", read_only=True
    )

    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "airplane_manufacturer",
        ]


class AirplaneDetailSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(many=False, read_only=True)
    airplane_manufacturer = serializers.CharField(
        source="airplane_type__manufacturer.name", read_only=True
    )

    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "airplane_manufacturer",
            "image",
        ]


class CrewPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewPosition
        fields = ["id", "name"]


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "position"]


class CrewListSerializer(CrewSerializer):
    position = serializers.CharField(source="position.name", read_only=True)

    class Meta:
        model = Crew
        fields = ["id", "position", "first_name", "last_name"]


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        ]

    def validate(self, attrs):
        data = super(FlightSerializer, self).validate(attrs=attrs)
        if attrs["departure_time"] >= attrs["arrival_time"]:
            raise ValidationError("Arrival time must be later than "
                                  "departure time.")
        return data


class FlightListSerializer(FlightSerializer):
    route_source = serializers.CharField(
        source="route.source", read_only=True
    )
    route_dest = serializers.CharField(
        source="route.destination", read_only=True
    )
    airplane_name = serializers.CharField(
        source="airplane.name", read_only=True
    )
    airplane_capacity = serializers.CharField(
        source="airplane.capacity", read_only=True
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = [
            "id",
            "route_source",
            "route_dest",
            "departure_time",
            "arrival_time",
            "airplane_name",
            "airplane_capacity",
            "tickets_available",
        ]


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "flight"]


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat"]


class FlightDetailSerializer(FlightListSerializer):
    airplane = AirplaneListSerializer(many=False, read_only=True)
    crew = serializers.SerializerMethodField()
    taken_places = TicketSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    def get_crew(self, obj):
        crew_members = obj.crew.select_related("position").all()
        return [member.position_name for member in crew_members]

    class Meta:
        model = Flight
        fields = [
            "id",
            "route_source",
            "route_dest",
            "departure_time",
            "arrival_time",
            "airplane",
            "crew",
            "taken_places",
        ]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ["id", "created_at", "tickets"]

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class FlightForOrderSerializer(FlightSerializer):
    tickets = TicketSeatsSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "tickets",
        ]


class OrderDetailSerializer(OrderSerializer):
    flights = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "created_at", "flights"]

    def get_flights(self, obj):
        flights = {}
        for ticket in obj.tickets.all():
            flight = ticket.flight
            if flight.id not in flights.keys():
                flights[flight.id] = {
                    "id": flight.id,
                    "route": flight.route.source_dest,
                    "airplane": flight.airplane.name,
                    "departure_time": flight.departure_time,
                    "arrival_time": flight.arrival_time,
                    "tickets": [],
                }
            flights[flight.id]["tickets"].append(
                TicketSeatsSerializer(ticket).data
            )
        return list(flights.values())
