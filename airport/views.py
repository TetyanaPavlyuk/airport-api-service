from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

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
)
from airport.serializers import (
    AirportSerializer,
    RouteSerializer,
    RouteListSerializer,
    AirplaneManufacturerSerializer,
    AirplaneTypeSerializer,
    AirplaneTypeListSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    AirplaneImageSerializer,
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


class AirportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer


class AirplaneManufacturerViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = AirplaneManufacturer.objects.all()
    serializer_class = AirplaneManufacturerSerializer


class AirplaneTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = AirplaneType.objects.select_related("manufacturer")
    serializer_class = AirplaneTypeSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneTypeListSerializer
        return AirplaneTypeSerializer


class AirplaneViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_queryset(self):
        if self.action == "list":
            return Airplane.objects.select_related(
                "airplane_type__manufacturer"
            )
        return self.queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneDetailSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve the flights with filters"""
        source_airport = self.request.query_params.get("source_airport")
        destination_airport = self.request.query_params.get(
            "destination_airport"
        )
        source_city = self.request.query_params.get("source_city")
        destination_city = self.request.query_params.get("destination_city")
        airplane = self.request.query_params.get("airplane")
        crew = self.request.query_params.get("crew")
        date_departure = self.request.query_params.get("date_departure")
        date_arrival = self.request.query_params.get("date_arrival")

        if self.action == "list":
            queryset = self.queryset.prefetch_related("tickets")
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
            dc = destination_city
            queryset = queryset.filter(
                route__destination__closest_big_city__icontains=dc
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
            ).date()
            queryset = queryset.filter(
                arrival_time__gte=date_arrival
            )
        return queryset.distinct().order_by("departure_time")

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="source_airport",
                description="Filter by source airport",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="destination_airport",
                description="Filter by destination airport",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="source_city",
                description="Filter by source city",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="destination_city",
                description="Filter by destination city",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="airplane",
                description="Filter by airplane",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="crew",
                description="Filter by crew id (ex. ?crew=2,3)",
                required=False,
                type={"type": "array", "items": {"type": "number"}},
            ),
            OpenApiParameter(
                name="date_departure",
                description="Filter from departure date and later "
                            "(ex. ?date_departure=2024-08-25)",
                required=False,
                type=OpenApiTypes.DATE
            ),
            OpenApiParameter(
                name="date_arrival",
                description="Filter from arrival date and later "
                            "(ex. ?date_arrival=2024-09-03)",
                required=False,
                type=OpenApiTypes.DATE
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = (queryset
                        .select_related()
                        .prefetch_related(
                            "tickets__flight__route__source",
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
