from django.contrib import admin
from .models import Establishment, Reservation, PositiveReport

admin.site.register(Establishment)
admin.site.register(Reservation)
admin.site.register(PositiveReport)