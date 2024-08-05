from datetime import datetime, timedelta

from django.db.models import F, Count
from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
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
)
from airport.serializers import (
    AirportSerializer,
    RouteSerializer,
    RouteListSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    CrewPositionSerializer,
    CrewSerializer,
    CrewListSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer
)

from airport.permissions import IsAdminOrIsAuthenticatedReadOnly


class AirportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer


class AirplaneTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]


class AirplaneViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]

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
    permission_classes = [IsAdminUser]


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Crew.objects.select_related("position")
    serializer_class = CrewSerializer
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        return CrewSerializer


class FlightPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class FlightViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = (Flight.objects
                .select_related(
                    "route__source",
                    "route__destination",
                    "airplane"
                    )
                )
    serializer_class = FlightSerializer
    pagination_class = FlightPagination
    permission_classes = [IsAdminOrIsAuthenticatedReadOnly]

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve the flights with filters"""
        source_airport = self.request.query_params.get("source_airport")
        destination_airport = self.request.query_params.get("destination_airport")
        source_city = self.request.query_params.get("source_city")
        destination_city = self.request.query_params.get("destination_city")
        airplane = self.request.query_params.get("airplane")
        crew = self.request.query_params.get("crew")
        date_departure = self.request.query_params.get("date_departure")
        date_arrival = self.request.query_params.get("date_arrival")

        if self.action == "list":
            queryset = (
                self.queryset.annotate(
                    tickets_available=(
                            F("airplane__rows") * F("airplane__seats_in_row")
                            - Count("tickets")
                    )
                )
            )
        elif self.action == "retrieve":
            queryset = (
                self.queryset
                .prefetch_related(
                    "crew__position",
                )
            )
        else:
            queryset = self.queryset

        if source_airport:
            queryset = queryset.filter(
                route__source__name__icontains=source_airport
            )
        if destination_airport:
            queryset = queryset.filter(
                route__destination__name__icontains=destination_airport
            )
        if source_city:
            queryset = queryset.filter(
                route__source__closest_big_city__icontains=source_city
            )
        if destination_city:
            queryset = queryset.filter(
                route__destination__closest_big_city__icontains=destination_city
            )
        if airplane:
            queryset = queryset.filter(airplane__name__icontains=airplane)
        if crew:
            crew_ids = self._params_to_ints(crew)
            queryset = queryset.filter(crew__id__in=crew_ids)
        if date_departure:
            date_departure = datetime.strptime(
                date_departure, "%Y-%m-%d"
            ).date()
            queryset = queryset.filter(
                departure_time__gte=date_departure
            )
        if date_arrival:
            date_arrival = datetime.strptime(
                date_arrival, "%Y-%m-%d"
            ).date() + timedelta(days=1)
            queryset = queryset.filter(
                arrival_time__lte=date_arrival
            )
        return queryset.distinct().order_by("departure_time")

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = (queryset.select_related()
                        .prefetch_related("tickets__flight__route__source",
                                          "tickets__flight__route__destination",
                                          "tickets__flight__airplane")
                        )
        queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
