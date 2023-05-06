from resplatform import Resy, Tock
from datetime import datetime
from decision_engine import DecisionEngine
import logging
import os
from dotenv import load_dotenv

# TODO: Set this from the application and not a global
DEBUG = False

def main():

    # My Loup - Resy - 69830
    # Forin - Resy - 69260
    # Little Fish = Resy - 4232
    # MC CLub - Resy - 52556
    logging.basicConfig(filename='log.log', level=logging.INFO)
    load_dotenv()
    # Fiorella
    # Name fiorellaphilly
    # ID 181982
    # Type indoor-dining-reservation
    de = DecisionEngine()

    party_size = '2'

    venue_name = 'fiorellaphilly'
    venue_id = '181982'
    res_type = 'indoor-dining-reservation'

    username = os.environ['TOCK_USER']
    password = os.environ['TOCK_PASS']

    tock = Tock(venue_name=venue_name, venue_id=venue_id, res_type=res_type, party_size=party_size, de=de, debug=DEBUG)
    tock.login(username, password)
    d = tock.get_available_dates()
    t = tock.get_available_times(d)
    for a in t:
        print(a)


    return
    venue_id = '69830'
    resy = Resy(venue_id=venue_id, party_size=party_size, de=de, debug=DEBUG)
    resy.authenticate()

    logging.info('Attempting to book in  Resy: %s with size %s', venue_id, party_size)
    resy.book_next_available(datetime.today())

    """
    Flat file  with sites, URLs, and platform
    Read file with preferred dates/times
    env file with logins / pws / cc data?

    Launch Sign in Page
    Login
    Launch Reservations Page
    Select with priority of preferred times
    Select Res
    Go through appropriate flow based off platform




    Phase 2:
    Read activation times - know when to fire
    """

if __name__ == '__main__':
    main()
