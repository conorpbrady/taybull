from django.core.management.base import BaseCommand, CommandError
from scheduler.models import *
from bookingengine.resy import Resy
from bookingengine.tock import Tock
from bookingengine.resy_selenium import ResySelenium
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
        parser.add_argument('--show_browser', action='store_true', help='Do not run in headless mode. Launch browser window')
        parser.add_argument('--test', action='store_true', help='Test mode. Will exit before making booking')

    def handle(self, *args, **kwargs):
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

            # Check to see if request should run. This is in a separate try block so that the exception will post on web log.
            # If this is successful, and the request should not be ran, then do not show on the web log.
            try:
                log.append(f'{request.booked_venue} for {request.party_size} | {request.decision_preference} // {request.scheduling_preference}')
                # Skip if request is not scheduled to run
                if kwargs['force']:
                    on_schedule = True
                    log.append('Force run')
                else:
                    on_schedule = self.is_scheduled(request.last_run, request.scheduling_preference)
                if not on_schedule:
                    log.append('Not scheduled to run - skipping request')
                    continue
            except:
                history_object = RunHistory(owner = request.owner, request=request, log=' | '.join(log))
                history_object.save()


            try:
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
                            'payment_id': account_info.resy_payment_id,
                            'first_available': decision_prefs.first_available
                            }

                    # TODO: Find a way to import auth token / api key
                    auth_options.update({
                            'api_key': request.account.resy_api_key,
                            'auth_token': request.account.resy_auth_token
                            })
                    booking_engine = Resy(**options)

                elif venue.res_platform == 2: # Resy Selenium Flow
                    options = {
                            'venue_id': venue.venue_id,
                            'party_size': request.party_size,
                            'payment_id': account_info.resy_payment_id,
                            'first_available': decision_prefs.first_available,
                            'venue_url': venue.resy_url
                            }
                    options.update(auth_options)
                    booking_engine = ResySelenium(**options)

                elif venue.res_platform == 0: # Tock:
                    day_to_select = None
                    if decision_prefs.specific_date_flag:
                        day_to_select = decision_prefs.specific_date
                    options = {
                            'venue_id': venue.venue_id,
                            'venue_name': venue.venue_name,
                            'res_type': venue.reservation_type,
                            'party_size': request.party_size,
                            'card_cvv': request.account.card_cvv,
                            'tock_multiple_res_types': venue.tock_multiple_res_types,
                            'tock_type_to_select': venue.tock_type_to_select,
                            'specific_date': day_to_select,
                            'first_available': decision_prefs.first_available
                            }
                    headless = True
                    if kwargs['show_browser']:
                        headless = False

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
                        if not kwargs['test']:
                            success, confirmation = booking_engine.book(selected_time_slot)
                            # Change Status based on result
                            if success:
                                log.append(f'Booking confirmation {confirmation}')
                                request.status = 'Completed'
                                request.confirmation = confirmation
                        else:
                            log.append('Test Mode. Backing out before booking')
                    else:
                        log.append('No times to select')

                if not kwargs['test']:
                    request.last_run = django_tz.now()
                    request.save()

            except Exception as e:
                log.append("Exception thrown when running request")
                log.append(traceback.format_exc())
            finally:
                # Create record in RunHistory with Status
                history_object = RunHistory(owner = request.owner, request=request, log=' | '.join(log))
                history_object.save()
                try:
                    booking_engine.close()
                    logger.info("Closing booking engine instance")
                except:
                    pass
                logger.info("Completed run")

    def is_scheduled(self, last_run_utc, schedule):
        current_utc = datetime.now(tz=timezone('UTC'))
        local_time = datetime.now(tz=timezone('US/Eastern'))

        if schedule.specific_time is None: # Hourly
            wait_time = int(schedule.frequency / 2) # Wait for half the frequency time
            if last_run_utc is not None:
                since_last_run = current_utc - last_run_utc
                min_since_last_run = since_last_run.seconds / 60
                if min_since_last_run < wait_time:
                    logger.info(f'Has run in the past {wait_time} min')
                    return False

            # Make sure current time is inside start - end time range
            start = local_time.replace(hour=schedule.start_time.hour, minute=schedule.start_time.minute,
                                       second=schedule.start_time.second)
            end = local_time.replace(hour=schedule.end_time.hour, minute=schedule.end_time.minute,
                                      second=schedule.end_time.second)
            if local_time < start: # Has not past start time
                logger.info('Earlier than start time')
                return False

            if local_time > end: # Has past end time
                logger.info('Later than end time')
                return False

            # Give 1 / {half_frequency} chance of running

            r = random.randint(1, wait_time)
            logger.info(f'random {r}')
            if r != 1:
                logger.info('unlucky roll')
                return False

            return True

        else: # Daily check at specified time
            day_dict = {'Mon': schedule.mon_run, 'Tue': schedule.tue_run, 'Wed': schedule.wed_run,
                        'Thu': schedule.thu_run, 'Fri': schedule.fri_run, 'Sat': schedule.sat_run,
                        'Sun': schedule.sun_run}
            # If schedule to run on day:
            dow = local_time.strftime('%a')
            if not day_dict[dow]:
                logger.info('Not the right day of week')
                return False

            delta = local_time.replace(hour=schedule.specific_time.hour, minute=schedule.specific_time.minute, second=schedule.specific_time.second) - local_time

            # Run if within a minute of specified time
            if not (delta.seconds < 61 or delta.seconds > 86339):
                logger.info('Not specified time')
                return False

            return True
