from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirportViewSet,
    RouteViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    CrewPositionViewSet,
    CrewViewSet
)


router = routers.DefaultRouter()
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("crew_positions", CrewPositionViewSet)
router.register("crews", CrewViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "airport"
