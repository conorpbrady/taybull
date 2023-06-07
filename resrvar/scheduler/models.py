from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import datetime

# Create your models here.
class BaseModel(models.Model):
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)

class DayOfWeekPreference(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    display_name = models.CharField(max_length = 32)

class DecisionPreference(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    active = models.BooleanField(default=True)
    display_name = models.CharField(max_length=32, null=True)
    ideal_time = models.CharField(max_length=16)
    specific_date_flag = models.BooleanField(default=False)
    specific_date = models.DateField()
    threshold = models.IntegerField()
    mon_rank = models.IntegerField(default=0)
    tue_rank = models.IntegerField(default=0)
    wed_rank = models.IntegerField(default=0)
    thu_rank = models.IntegerField(default=0)
    fri_rank = models.IntegerField(default=0)
    sat_rank = models.IntegerField(default=0)
    sun_rank = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.display_name}'

class Venue(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    venue_id = models.CharField(max_length = 32)
    reservation_type = models.CharField(max_length = 32, blank=True)
    venue_name = models.CharField(max_length = 64, blank=True)
    display_name = models.CharField(max_length = 64, blank=True)

    class ResPlatform(models.IntegerChoices):
        TOCK = 0
        RESY = 1
        OPENTABLE = 3

    res_platform = models.IntegerField(choices=ResPlatform.choices)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.display_name}'

class ReservationRequest(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    booked_venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    decision_preference = models.ForeignKey(DecisionPreference, on_delete=models.PROTECT, null=True)
    status = models.CharField(max_length=32)
    confirmation = models.CharField(max_length=32, blank=True)
    active = models.BooleanField(default=True)

class RunHistory(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    request = models.ForeignKey(ReservationRequest, on_delete=models.CASCADE)
    log = models.TextField()
