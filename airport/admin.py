from django.contrib import admin
from models import (
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


admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Airport)
admin.site.register(Route)
admin.site.register(CrewPosition)
admin.site.register(Crew)
admin.site.register(Order)
admin.site.register(Flight)
admin.site.register(Ticket)
