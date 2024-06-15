from bookingengine.resplatform import ResPlatform
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger('resy')

class Resy(ResPlatform):

    DATE_FMT = '%Y-%m-%d'
    HEADERS = {
                'accept-encoding': 'gzip, deflate, br',
                'origin': 'https://widgets.resy.com',
                'referer': 'https://widgets.resy.com/',
                'x-origin': 'https://widgets.resy.com',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
                }


    def __init__(self, *args, **kwargs):
                self.venue_id = kwargs.get('venue_id')
        self.party_size = kwargs.get('party_size')
        if self.venue_id is None or self.party_size is None:
            raise TypeError

        super().__init__(HEADERS)

    def authenticate(self, *args, **kwargs):
        auth_token = kwargs.get('auth_token')
        api_key = kwargs.get('api_key')
        if auth_token is None or api_key is None:
            raise TypeError

        headers = {
            'authorization': 'ResyAPI api_key="{}"'.format(api_key),
            'x-resy-auth-token': auth_token,
            'x-resy-universal-auth': auth_token
            }
        self.update_headers(headers)
        r = self.session.get('https://api.resy.com/3/user/lists/venue_ids')
        if r.status_code == 419 or r.status_code == 401:
            auth_token = self.login(kwargs.get('resy_email'), kwargs.get('resy_password'))
        return auth_token

    def login(self, email, password):

        login_url = 'https://api.resy.com/3/auth/password'
        data = {'email': email, 'password': password}
        r = request.post(login_url, data, headers=HEADERS)
        response_data = r.json()
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
                logging.info('Found available days: %s', ','.join(days))
                all_days += days
            else:
                logging.info('No available days between %s and %s', start, end)

        if len(all_days) == 0:
            logging.info("No available days")
            return {}

        self.time_slots = {}
        for day in all_days:
            self.time_slots.update(self.find_bookings(day))
        if len(self.time_slots) == 0:
            logging.info('No available times')

        time_slot_strs = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in self.time_slots.keys()]
        return time_slot_strs

    def book(self, time_slot):
        return True, "54321"
        booking_token = get_booking_token(time_slot, self.available_time_slots[time_slot]['token'])
        confirmation = self.make_booking(booking_token)
        return confirmation

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

        available_days = []
        data = r.json()
        # logging.self.log_request(r)
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
        payload = {
                'commit': 1,
                'config_id': config_token,
                'day': day_token[:day_token.find(" ")],
                'party_size': self.party_size
                }

        r = self.session.post(url, json=payload)
        self.log_request(r)
        data = r.json()
        book_token = data['book_token']['value']
        return book_token

    def make_booking(self, book_token, test=False):

        url = 'https://api.resy.com/3/book'
        if test:
            url='https://en7ghrdxqtapb.x.pipedream.net/'
        payload = {
                'book_token': book_token,
                'struct_payment_method': '{"id":16651865}',
                'source_id': 'resy.com-venue-details',
                }

        r = self.session.post(url, data=payload)
        self.log_request(r)

        try:
            data = r.json()

            # TODO: Log resy token and reservation DI
            return data
        except:
            pass
