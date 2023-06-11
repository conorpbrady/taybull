from django.core.management.base import BaseCommand, CommandError
from scheduler.models import *
from bookingengine.bookingengine import BookingEngine

class Command(BaseCommand):
    help = "Run booking engine"


    def handle(self, *args, **options):

        open_requests = ReservationRequest.objects.filter(
                active = True,
                status__in = ['Open']
                )

        for request in open_requests:

            # TODO: This will change when wecreate FK for AccountInfo in ResRequests
            account_info = AccountInfo.objects.filter(owner = request.owner)[0]

            venue = Venue.objects.get(id = request.booked_venue_id)
            decision_pref = DecisionPreference.objects.get(id = request.decision_preference_id)

            # Run Booking Enging

            # Change Status based on result

            # Create record in RunHistory with Status
            history_object = RunHistory(owner = request.owner, request=request, log="Test Run")
            history_object.save()
