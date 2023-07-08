from django.core.management.base import BaseCommand, CommandError
from scheduler.models import *
from bookingengine.resy import Resy
from bookingengine.tock import Tock
from bookingengine.decision_engine import DecisionEngine
import traceback
from dotenv import dotenv_values

class Command(BaseCommand):
    help = "Run booking engine"


    def handle(self, *args, **options):

        open_requests = ReservationRequest.objects.filter(
                active = True,
                status__in = ['Open']
                )

        for request in open_requests:
            log = []
            # TODO: This will change when wecreate FK for AccountInfo in ResRequests
            try:
                account_info = AccountInfo.objects.filter(owner = request.owner)[0]

                venue = Venue.objects.get(id = request.booked_venue_id)
                decision_prefs = DecisionPreference.objects.get(id = request.decision_preference_id)

                if venue.res_platform == 1: # Resy
                    options = {
                            'venue_id': venue.venue_id,
                            'party_size': request.party_size
                            }

                    # TODO: Find a way to import auth token / api key
                    auth_options = {
                            'api_key': '',
                            'auth_token':'',
                            }
                    booking_engine = Resy(**options)

                elif venue.res_platform == 0: # Tock:
                    options = {
                            'venue_id': venue.venue_id,
                            'venue_name': venue.venue_name,
                            'res_type': venue.reservation_type,
                            'party_size': request.party_size
                            }
                    # TODO: Come up with a way to store credentials better
                    auth_options = {
                            **dotenv_values('.tock.env')
                            }
                    booking_engine = Tock(**options)
                else:
                    log.append('Res Platform not implemented')

                booking_engine.authenticate(**auth_options)
                available_times = booking_engine.get_available_times()
                found_times = len(available_times)

                log.append(f'found {found_times} times')

                de = DecisionEngine(decision_prefs)
                selected_time_slot = de.select_time(available_times)
                log.append(f'selecting time slot {selected_time_slot}')

                success, confirmation = booking_engine.book(selected_time_slot)
                # Change Status based on result
                if success:
                    request.status = 'Completed'
                    request.confirmation = confirmation

                request.save()
            except Exception as e:
                log.append("Exception thrown when running request")
                log.append(traceback.format_exc())
            finally:
                # Create record in RunHistory with Status
                history_object = RunHistory(owner = request.owner, request=request, log=' | '.join(log))
                history_object.save()
