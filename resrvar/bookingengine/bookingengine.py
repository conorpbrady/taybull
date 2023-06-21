from bookingengine.resplatform import Resy, Tock
from datetime import datetime
from bookingengine.decision_engine import DecisionEngine
import logging
import os
from dotenv import load_dotenv

class BookingEngine:

    def __init__(self, platform):
        self.platform = platform
        logging.basicConfig(filename='log.log', level=logging.INFO)
        load_dotenv()

        if platform == 'Resy':
            username = os.environ['TOCK_USER']
            password = os.environ['TOCK_PASS']

        tock = Tock(**tock_venues['Fiorella'],  party_size=party_size, de=de, debug=DEBUG)
        tock.login(username, password)

        elif platform == 'Tock':
            pass
        else:
            raise(Exception)

    def load(self, venue_options, account_info, decision_prefs):
        pass
        self.platform.load(venue_options)
        # resy = Resy(venue_id=venue_id, party_size=party_size, de=de, debug=DEBUG)
        # resy.authenticate()

    def book(self):
        pass
        # if platform == 'Resy':

            # logging.info('Attempting to book in  Resy: %s with size %s', venue_id, party_size)
            # resy.book_next_available(datetime.today())

       # else:
            # preferred = datetime.strptime('2023-06-01 21:00', '%Y-%m-%d %H:%M')
            # success, confirmation = tock.book(preferred)
            # if success:
            #     print(confirmation)
            # else:
            #    print('No slots available')
