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

class AccountInfo(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    display_name = models.CharField(max_length=32, blank=True)
    resy_api_key = models.CharField(max_length=128, blank=True)
    resy_auth_token = models.CharField(max_length=512, blank=True)
    resy_payment_id = models.CharField(max_length=32, blank=True)
    tock_email = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f'{self.display_name}'

class SchedulingPreference(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    display_name = models.CharField(max_length=32, blank=True)

    class Frequency(models.IntegerChoices):
            HOURLY = 0
            DAILY = 1

    frequency = models.IntegerField(choices=Frequency.choices)
    mon_run = models.BooleanField(default=True)
    tue_run = models.BooleanField(default=True)
    wed_run = models.BooleanField(default=True)
    thu_run = models.BooleanField(default=True)
    fri_run = models.BooleanField(default=True)
    sat_run = models.BooleanField(default=True)
    sun_run = models.BooleanField(default=True)
    specific_time = models.TimeField()
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)

    def __str__(self):
            return f'{self.display_name}'

class ReservationRequest(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    booked_venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    decision_preference = models.ForeignKey(DecisionPreference, on_delete=models.PROTECT, null=True)
    scheduling_preference = models.ForeignKey(SchedulingPreference, on_delete=models.PROTECT, null=True)
    account = models.ForeignKey(AccountInfo, on_delete=models.PROTECT, null=True)
    party_size = models.IntegerField(default=2)
    status = models.CharField(max_length=32)
    confirmation = models.CharField(max_length=32, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.booked_venue} for {self.party_size} | {self.decision_preference}'

class RunHistory(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    request = models.ForeignKey(ReservationRequest, on_delete=models.CASCADE)
    log = models.TextField()
