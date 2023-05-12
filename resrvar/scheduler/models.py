from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

# Create your models here.
class BaseModel(models.Model):
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)

class DecisionPreference(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    ideal_time = models.CharField(max_length=16)
    specific_date_flag = models.BooleanField(default=False)
    specific_date = models.DateField()
    threshold = models.IntegerField()

class DayOfWeekPreference(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(DecisionPreference, on_delete=models.CASCADE, null=True)
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0
        TUESDAY = 1
        WEDNESDAY = 2
        THURSDAY = 3
        FRIDAY = 4
        SATURDAY = 5
        SUNDAY = 6

    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    rank = models.IntegerField()

class Venue(BaseModel):
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

class ReservationRequest(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    status = models.CharField(max_length=32)
    confirmation = models.CharField(max_length=32)

class RunHistory(BaseModel):
    request = models.ForeignKey(ReservationRequest, on_delete=models.CASCADE)
    log = models.TextField()
