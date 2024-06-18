from django.core.management.base import BaseCommand, CommandError
from scheduler.models import *
from bookingengine.resy import Resy
from bookingengine.tock import Tock
from bookingengine.decision_engine import DecisionEngine
import traceback
from dotenv import dotenv_values
from pytz import timezone
import random

class Command(BaseCommand):
    help = "Run booking engine"


    def handle(self, *args, **options):

        open_requests = ReservationRequest.objects.filter(
                active = True,
                status__in = ['Open', 'Created']
                )

        for request in open_requests:
            log = []
            try:
                log.append(f'{request.booked_venue} for {request.party_size} | {request.decision_preference} // ')
                # Skip if request is not scheduled to run
                if not self.is_scheduled(request.last_run, request.scheduling_preference):
                    log.append('Not scheduled to run - skipping request')
                    continue

                account_info = AccountInfo.objects.filter(owner = request.owner)[0]

                venue = Venue.objects.get(id = request.booked_venue_id)
                decision_prefs = DecisionPreference.objects.get(id = request.decision_preference_id)
                auth_options = {
                        **dotenv_values('.accounts.env')
                        }
                if venue.res_platform == 1: # Resy
                    options = {
                            'venue_id': venue.venue_id,
                            'party_size': request.party_size
                            }

                    # TODO: Find a way to import auth token / api key
                    auth_options.update({
                            'api_key': request.account.resy_api_key,
                            'auth_token': request.account.resy_auth_token
                            })
                    booking_engine = Resy(**options)

                elif venue.res_platform == 0: # Tock:
                    options = {
                            'venue_id': venue.venue_id,
                            'venue_name': venue.venue_name,
                            'res_type': venue.reservation_type,
                            'party_size': request.party_size
                            }

                    booking_engine = Tock(**options)
                else:
                    log.append('Res Platform not implemented')

                result = booking_engine.authenticate(**auth_options)
                if venue.res_platform == 1: # Resy
                    if result != request.account.resy_auth_token:
                        account_info.resy_auth_token = result
                        account_info.save()

                available_times = booking_engine.get_available_times()
                found_times = len(available_times)

                log.append(f'found {found_times} total times')
                if found_times != 0:
                    de = DecisionEngine(decision_prefs, log)
                    de_times = de.rank_by_time(available_times)
                    if len(de_times) > 0:
                        selected_time_slot = de_times[0]
                        log.append(f'selecting time slot {selected_time_slot}')

                        success, confirmation = booking_engine.book(selected_time_slot)
                        # Change Status based on result
                        if success:
                            #request.status = 'Completed'
                            request.confirmation = confirmation
                    else:
                        log.append('No times to select')
                    request.save()
            except Exception as e:
                log.append("Exception thrown when running request")
                log.append(traceback.format_exc())
            finally:
                # Create record in RunHistory with Status
                history_object = RunHistory(owner = request.owner, request=request, log=' | '.join(log))
                history_object.save()


    def is_scheduled(self, last_run_utc, schedule):
        current_utc = datetime.now()
        local_time = datetime.now(tz=timezone('US/Eastern'))

        if schedule.frequency == 0: # Hourly
            pass
            # Wait at least 30 min since last run
            try:
                since_last_run = current_utc - last_run_utc
                min_since_last_run = since_last_run.seconds / 60
                if min_since_last_run < 30:
                    return False
            except TypeError:
                pass
            # Make sure current time is inside start - end time range
            start = local_time.replace(hour=schedule.start_time.hour, minute=schedule.start_time.minute,
                                       second=schedule.start_time.second)
            end = local_time.replace(hour=schedule.end_time.hour, minute=schedule.end_time.minute,
                                      second=schedule.end_time.second)
            if local_time < start: # Has not passed start time
                return False

            if local_time > end: # Has passed end time
                return False

            # Give 1/30 chance of running

            r = random.randint(1, 30)
            if r != 1:
                return False

            return True

        elif schedule.frequency == 1: # Daily
            day_dict = {'Mon': schedule.mon_run, 'Tue': schedule.tue_run, 'Wed': schedule.wed_run,
                        'Thu': schedule.thu_run, 'Fri': schedule.fri_run, 'Sat': schedule.sat_run,
                        'Sun': schedule.sun_run}
            # If schedule to run on day:
            dow = local_time.strftime('%a')
            if not day_dict[dow]:
                return False

            delta = schedule.specific_time - local_time

            # Run if within a minute of specified time
            if delta.seconds < -60 or delta.seconds > 60:
                return False

            return True
