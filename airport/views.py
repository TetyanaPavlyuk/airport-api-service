from django.shortcuts import render
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

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
from airport.serializers import (
    AirportSerializer,
    RouteSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    CrewPositionSerializer,
    CrewSerializer,
    CrewListSerializer,
    FlightSerializer,
    FlightListSerializer,
    TicketSerializer,
    TicketListSerializer,
    TicketSeatsSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer
)


class AirportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    # permission_classes = []


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    # permission_classes =


class AirplaneTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    # permission_classes = []


class AirplaneViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    # permission_classes = []

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        return AirplaneSerializer


class CrewPositionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = CrewPosition.objects.all()
    serializer_class = CrewPositionSerializer
    # permission_classes = []


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Crew.objects.select_related("position")
    serializer_class = CrewSerializer
    # permission_classes = []

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        return CrewSerializer
