from bookingengine.resplatform import ResPlatform
import logging
import requests
from datetime import datetime, timedelta
import urllib3
import json
logger = logging.getLogger(__name__)

from http.client import HTTPConnection

# This is needed to drop the 'Accept-Encoding' header. Resy seems to reject requests to /details
# when this header is set. Setting this header to None will drop it from the request

def drop_accept_encoding_on_putheader(http_connection_putheader):
    def wrapper(self, header, *values):
        if header == "Accept-Encoding" and "identity" in values:
            return
        return http_connection_putheader(self, header, *values)

    return wrapper


class Resy(ResPlatform):

    DATE_FMT = '%Y-%m-%d'
    HEADERS = {
                'Origin': 'https://widgets.resy.com',
                'Referer': 'https://widgets.resy.com/',
                'X-Origin': 'https://widgets.resy.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                }


    def __init__(self, *args, **kwargs):
        self.venue_id = kwargs.get('venue_id')
        self.party_size = kwargs.get('party_size')
        self.payment_id = kwargs.get('payment_id')
        if self.venue_id is None or self.party_size is None:
            raise TypeError

        super().__init__(self.HEADERS)

    def authenticate(self, *args, **kwargs):
        auth_token = kwargs.get('auth_token')
        api_key = kwargs.get('api_key')
        if auth_token is None or api_key is None:
            raise TypeError

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Authorization': 'ResyAPI api_key="{}"'.format(api_key),
            'X-Resy-Auth-Token': auth_token,
            'X-Resy-Universal-Auth': auth_token
            }
        self.update_headers(headers)
        r = self.session.get('https://api.resy.com/3/user/lists/venue_ids')
        print(f'checking if auth_token is valid {r.status_code}')
        if r.status_code == 419 or r.status_code == 401:
            auth_token = self.login(kwargs.get('resy_email'), kwargs.get('resy_password'))
        return auth_token

    def login(self, email, password):

        login_url = 'https://api.resy.com/3/auth/password'
        data = {'email': email, 'password': password}
        r = request.post(login_url, data, headers=self.HEADERS)
        response_data = r.json()
        print(f'attempting to login {r.status_code}')
        token = response_data['token']
        return token

    def get_available_times(self):
        max_weeks = 8
        current_day = datetime.today()
        all_days = []
        for i in range(max_weeks):
            num_weeks = timedelta(days=7*i)
            start = (current_day + num_weeks).strftime(self.DATE_FMT)
            end = (current_day + timedelta(days=7) + num_weeks).strftime(self.DATE_FMT)
            days = self.get_available_days(start, end)
            if len(days) > 0:
                logger.info('Found available days: %s', ','.join(days))
                all_days += days
            else:
                logger.info('No available days between %s and %s', start, end)

        if len(all_days) == 0:
            logger.info("No available days")
            return {}

        self.time_slots = {}
        for day in all_days:
            self.time_slots.update(self.find_bookings(day))
        if len(self.time_slots) == 0:
            logger.info('No available times')

        time_slot_strs = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in self.time_slots.keys()]
        return time_slot_strs

    def book(self, time_slot):
        slot_str = time_slot.strftime('%Y-%m-%d %H:%M:%S')
        booking_token = self.get_booking_token(slot_str, self.time_slots[slot_str]['token'])
        confirmation = self.make_booking(booking_token)
        return True, confirmation

    def get_available_days(self, start, end):
        params = {
                'venue_id': self.venue_id,
                'num_seats': self.party_size,
                'start_date': start,
                'end_date': end
                }
        url = 'https://api.resy.com/4/venue/calendar'

        r = self.session.get(url, params=params)

        # TODO: Some error handling for bad requests etc

        logger.info(f'{r.status_code} || {r.url}')
        available_days = []
        data = r.json()
        if r.status_code != 200:
            return []
        # TODO: See what happens when there are no time slots, or maybe this manifest since available_days
        # would not populate a day w/o open time slots
        for dateObj in data['scheduled']:
            if dateObj['inventory']['reservation'] == 'available':
                available_days.append(dateObj['date'])
        return available_days

    def find_bookings(self, day):

        params = {
            'lat': '0',
            'long': '0',
            'day': day,
            'party_size': self.party_size,
            'venue_id': self.venue_id
            }
        url = 'https://api.resy.com/4/find'


        r = self.session.get(url, params = params)
        # TODO: Handle Bad Requests
        data = r.json()
        time_slots = data['results']['venues'][0]['slots']

        token_obj = {}
        for ts in time_slots:
            token = ts['config']['token']
            dining_type = ts['config']['type']
            key = ts['date']['start']
            token_obj[key] = {
                    'type': dining_type,
                    'token': token
                    }
        return token_obj


    def get_booking_token(self, day_token, config_token):
        url = 'https://api.resy.com/3/details'
        # url = 'https://enjpl1x9mc03.x.pipedream.net'
        payload = {
                'commit': 1, # 0 for info, 1 to try and book
                'config_id': config_token,
                'day': day_token[:day_token.find(" ")],
                'party_size': self.party_size
                }
        new_headers = {
                'Accept-Encoding': None,
                }
        self.update_headers(new_headers)

        HTTPConnection.putheader = drop_accept_encoding_on_putheader(HTTPConnection.putheader)

        # Making the request from the session object fails for whatever reason
        # Performing the request directly until that's figured out

        #r = self.session.post(url, json=payload)
        r = requests.post(url, headers=self.get_headers(), json=payload)

        # logging.info(f'{r.status_code} || {r.url} || {r.text} || {r.request.headers} || {payload}')
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise requests.exceptions.HTTPError
        else:

            data = r.json()
            book_token = data['book_token']['value']
            return book_token

    def make_booking(self, book_token, test=False):

        url = 'https://api.resy.com/3/book'
        payload = {
                'book_token': book_token,
                'struct_payment_method': '{"id":' + self.payment_id + '}',
                'source_id': 'resy.com-venue-details',
                'venue_marketing_opt_in': 0
                }
        self.update_headers({'Content-Encoding': 'gzip, deflate, br'})
        r = requests.post(url, headers=self.get_headers(), data=payload)

        # logging.info(f'{r.status_code} || {r.url} || {r.text} || {r.request.headers} || {payload}')
        # TODO: Check status code here - 201 Created indicates successful creation
        # 412 Precondition Failed could be already created
        # Raise exception on 500/400/401 etc
        try:
            data = r.json()

            # TODO: Log resy token and reservation DI
            return data['reservation_id']
        except:
            pass

    def close(self):
        pass
