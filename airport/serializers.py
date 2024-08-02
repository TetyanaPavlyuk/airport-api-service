from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Route,
    CrewPosition,
    Crew,
    Order,
    Flight,
    Ticket
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
    source = serializers.CharField(
        source="source.name_city", read_only=True
    )
    destination = serializers.CharField(
        source="destination.name_city", read_only=True
    )


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type"]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type_name = serializers.CharField(
        source="airplane_type.name", read_only=True
    )

    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type_name"]


class CrewPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewPosition
        fields = ["id", "name"]


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "position"]


class CrewListSerializer(CrewSerializer):
    position = serializers.CharField(
        source="position.name", read_only=True
    )

    class Meta:
        model = Crew
        fields = ["id", "position", "full_name"]


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
        fields = ["id", "row", "seat", "flight", "order"]


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields =["row", "seat"]


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
            "taken_places"
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
