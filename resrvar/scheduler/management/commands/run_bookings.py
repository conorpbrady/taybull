from django.core.management.base import BaseCommand, CommandError
from scheduler.models import *
from bookingengine.resy import Resy
from bookingengine.tock import Tock
from bookingengine.decision_engine import DecisionEngine
import traceback
from dotenv import dotenv_values
from pytz import timezone
from django.utils import timezone as django_tz
import random

import logging

logging.basicConfig(format="%(levelname)s | %(asctime)s | %{message)s",
                    filename='log.log',
                    datefmt="%Y-%m-%dT%H:%M:%SZ")

logger = logging.getLogger('scheduler')
class Command(BaseCommand):
    help = "Run booking engine"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Skip random checks to always run')
        parser.add_argument('--show-browser', action='store_true', help='Do not run in headless mode. Launch browser window')

    def handle(self, *args, **options):

        logger.info("Run booking invoked")
        open_requests = ReservationRequest.objects.filter(
                active = True,
                status__in = ['Open', 'Created']
                )
        logger.info(f'Found {len(open_requests)} open requests')
        for request in open_requests:
            log = []
            logging.info(f'{request.booked_venue} for {request.party_size} ' \
            f'| {request.decision_preference} // {request.scheduling_preference}')

            try:
                log.append(f'{request.booked_venue} for {request.party_size} | {request.decision_preference} // ')
                # Skip if request is not scheduled to run
                if options['force']:
                    on_schedule = True
                    schedule_log = ['Force run']
                else:
                    on_schedule, schedule_log = self.is_scheduled(request.last_run, request.scheduling_preference)
                log += schedule_log
                if not on_schedule:
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
                            'party_size': request.party_size,
                            'payment_id': account_info.resy_payment_id
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
                    headless = not options['show-browser']

                    booking_engine = Tock(headless=headless, **options)
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
                            log.append(f'Booking confirmation {confirmation}')
                            request.status = 'Completed'
                            request.confirmation = confirmation
                    else:
                        log.append('No times to select')

                    request.last_run = django_tz.now()
                    request.save()
            except Exception as e:
                log.append("Exception thrown when running request")
                log.append(traceback.format_exc())
            finally:
                # Create record in RunHistory with Status
                history_object = RunHistory(owner = request.owner, request=request, log=' | '.join(log))
                history_object.save()
                logger.info("Completed run")

    def is_scheduled(self, last_run_utc, schedule):
        log = []
        current_utc = datetime.now(tz=timezone('UTC'))
        local_time = datetime.now(tz=timezone('US/Eastern'))

        if schedule.frequency == 0: # Hourly
            # Wait at least 30 min since last run
            if last_run_utc is not None:
                since_last_run = current_utc - last_run_utc
                min_since_last_run = since_last_run.seconds / 60
                if min_since_last_run < 30:
                    log.append('Has run in the past 30 min')
                    return False, log

            # Make sure current time is inside start - end time range
            start = local_time.replace(hour=schedule.start_time.hour, minute=schedule.start_time.minute,
                                       second=schedule.start_time.second)
            end = local_time.replace(hour=schedule.end_time.hour, minute=schedule.end_time.minute,
                                      second=schedule.end_time.second)
            if local_time < start: # Has not past start time
                log.append('Earlier thani start time')
                return False, log

            if local_time > end: # Has past end time
                log.append('Later than end time')
                return False, log

            # Give 1/30 chance of running

            r = random.randint(1, 30)
            log.append(f'random {r}')
            if r != 1:
                log.append('unlucky roll')
                return False, log

            return True, log

        elif schedule.frequency == 1: # Daily
            day_dict = {'Mon': schedule.mon_run, 'Tue': schedule.tue_run, 'Wed': schedule.wed_run,
                        'Thu': schedule.thu_run, 'Fri': schedule.fri_run, 'Sat': schedule.sat_run,
                        'Sun': schedule.sun_run}
            # If schedule to run on day:
            dow = local_time.strftime('%a')
            if not day_dict[dow]:
                log.append('Not the right day of week')
                return False, log

            delta = local_time.replace(hour=schedule.specific_time.hour, minute=schedule.specific_time.minute, second=schedule.specific_time.second) - local_time

            # Run if within a minute of specified time
            print(delta.seconds)
            if not (delta.seconds < 61 or delta.seconds > 86339):
                log.append('Not specified time')
                return False, log

            return True, log
