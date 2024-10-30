from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirportViewSet,
    RouteViewSet,
    AirplaneManufacturerViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    CrewPositionViewSet,
    CrewViewSet,
    FlightViewSet,
    OrderViewSet
)


router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("airplane_manufacturers", AirplaneManufacturerViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("crew_positions", CrewPositionViewSet)
router.register("crews", CrewViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "airport"
