from django.forms import ModelForm
from django.contrib.auth import authenticate

from .models import *

class VenueForm(ModelForm):
    class Meta:
        model = Venue
        fields = ['venue_name', 'reservation_type', 'display_name', 'res_platform']
