import requests
from datetime import datetime, timedelta
import logging

class ResPlatform:

    def __init__(self, headers, de, debug=False):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.debug = debug
        self.de = de

    def update_headers(self, headers)
        self.session.headers.update(headers)

    def log_request(self, r):
        logging.info('%s | %s', r.status_code, r.request.url)

        logging.debug(r.request.headers)
        logging.debug(r.request.body)
        logging.debug(r.text)

class Tock(ResPlatform):
    pass

class OpenTable(ResPlatform):
    pass

class Resy(ResPlatform):

    DATE_FMT = '%Y-%m-%d'

    def __init__(self, venue_id, party_size, de, test_url=None, debug=False):
        headers = {
                'accept-encoding': 'gzip, deflate, br',
                'origin': 'https://widgets.resy.com',
                'referer': 'https://widgets.resy.com/',
                'x-origin': 'https://widgets.resy.com',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
                }
        self.test_url = test_url
        self.venue_id = venue_id
        self.party_size = party_size

        super().__init__(headers, de)

    def authenticate(self):
        api_key = ''
        auth_token  = ''
        headers = {
            'authorization': 'ResyAPI api_key="{}'.format(api_key)
            'x-resy-auth-token': auth_token,
            'x-resy-universal-auth': auth_token
            }
        self.update_headers(headers)

    def book_next_available(self, current_day):

        max_weeks = 8

        for i in range(max_weeks):
            num_weeks = timedelta(days=7*i)
            start = (current_day + num_weeks).strftime(self.DATE_FMT)
            end = (current_day + timedelta(days=7) + num_weeks).strftime(self.DATE_FMT)
            days = self.get_available_days(start, end)
            if len(days) > 0:
                logging.info('Found available days: %s', ','.join(days))
                break
            else:
                logging.info('No available days between %s and %s', start, end)

        if len(days) == 0:
            logging.info("No available days")
            return

        time_slots = {}
        for day in days:
            time_slots.update(self.find_bookings(day))

        if len(time_slots) == 0:
            logging.info('No available times')
            return

        selected_time = self.de.select_preferred_time(time_slots)

        logging.info('Found time %s', selected_time)

        bt = self.get_booking_token(
                selected_time,
                time_slots[selected_time]['token']
                )
        self.book(bt, test=True)

    def get_available_days(self, start, end):
        params = {
                'venue_id': self.venue_id,
                'num_seats': self.party_size,
                'start_date': start,
                'end_date': end
                }
        url = 'https://api.resy.com/4/venue/calendar'
        if self.test_url is not None:
            url = self.test_url

        r = self.session.get(url, params=params)

        # TODO: Some error handling for bad requests etc

        self.log_request(r)
        available_days = []
        data = r.json()

        for inventory_obj in data['scheduled']:
            logging.debug('Availability for %s on %s: %s', self.venue_id, inventory_obj['date'], inventory_obj['inventory']['reservation'])
            if inventory_obj['inventory']['reservation'] == 'available':
                available_days.append(inventory_obj['date'])
        return available_days

    def find_bookings(self, day):
        params = {
                'venue_id': self.venue_id,
                'day': day,
                'lat': 0,
                'long': 0,
                'party_size': self.party_size
                }
        r = self.session.get('https://api.resy.com/4/find', params=params)
        self.log_request(r)

        # TODO: Error handling, move to super class

        data = r.json()
        # TODO: See what happens when there are no time slots, or maybe this manifest since available_days
        # would not populate a day w/o open time slots

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

    def book(self, book_token, test=False):

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
            print(data)
        except:
            pass
