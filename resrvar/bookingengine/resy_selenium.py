from bookingengine.resplatform import ResPlatform
import logging
from datetime import datetime
from sys import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

logger = logging.getLogger(__name__)



class ResySelenium(ResPlatform):

    def __init__(self, headless=False, *args, **kwargs):
        if platform == "darwin":
            CHROME_PATH = 'bookingengine/chromedriver_mac64/chromedriver'
        else:
            CHROME_PATH = '/usr/lib/chromium-browser/chromedriver'

        service = webdriver.ChromeService(executable_path=CHROME_PATH)
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--user-data-dir=chrome-data")

        # Make selenium headless, set window size to 1920x1080 so elements will load
        # Set user agent to get around cloudflare verification
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        options.add_argument(f'--user-agent={user_agent}')

        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 5)


        self.party_size = kwargs.get('party_size')
        self.first_available = kwargs.get('first_available')
        self.venue_url = kwargs.get('venue_url')
        self.specific_date = kwargs.get('specific_date')
        self.time_slots = {}

        super().__init__(None)

    def authenticate(self, *args, **kwargs):

        # Skipping auth for now. Too many successful logins will result in an account lockout
        # Need to save cookies w/ selenium and stay logged in
        return

        self.driver.get('https://resy.com')
        login_button_xp = '//button[@data-test-id="menu_container-button-log_in"]'
        login_button = self.wait.until(ec.presence_of_element_located((By.XPATH, login_button_xp)))
        login_button.click()

        use_email_pw_xp = '//div[@class="AuthView__Footer"]/button'
        use_email_pw = self.wait.until(ec.presence_of_element_located((By.XPATH, use_email_pw_xp)))
        use_email_pw.click()

        email_input = self.wait.until(ec.presence_of_element_located((By.ID, 'email')))
        email_input.send_keys(kwargs.get('resy_email'))
        pass_input = self.wait.until(ec.presence_of_element_located((By.ID, 'password')))
        pass_input.send_keys(kwargs.get('resy_password'))

        self.driver.find_element(By.XPATH, '//button[text()="Continue"]').click()
        self.wait.until(ec.presence_of_element_located((By.XPATH, '//div[@class="ProfilePhoto"]')))

    def book(self, time_slot):
        day = time_slot.strftime('%Y-%M-%d')
        res_id = self.time_slots[time_slot]

        url = f'{self.venue_url}?date={day}&seats={self.party_size}'
        self.driver.get(url)
        res_button = self.wait.until(ec.presence_of_element_located((By.ID, res_id)))
        res_button.click()
        return
        book_button = self.wait.until(ec.presence_of_element_Located((By.ID, 'order_summary_page-button-book')))
        book_button.click()


    def get_available_days(self):
        fmt = '%B %d, %Y'
        months = 3
        today = datetime.now().strftime('%Y-%m-%d')
        url = f'{self.venue_url}?date={today}&seats={self.party_size}'
        self.driver.get(url)

        # Check for newsletter popup and close
        # try:
        #    close = self.wait.until(ec.presence_of_element_located((By.XPATH, '//button[@aria-label="Close"]')))
        #    close.click()
        #except:
        #    pass

        calendar_button = self.wait.until(ec.presence_of_element_located(
            (By.ID, 'VenuePage__calendar__quick-picker__ellipsis')))
        calendar_button.click()


        all_days = []

        for i in range(months):
            calendar_table_xp = '//table[@class="CalendarMonth__Table"]'
            calendar_table = self.wait.until(ec.presence_of_element_located((By.XPATH, calendar_table_xp)))

            available_day_elements = calendar_table.find_elements(By.XPATH,
                './/button[contains(@class, "ResyCalendar-day--available")' \
                'or contains(@class, "ResyCalendar-day--selected__available")]')

            for ade in available_day_elements:
                al = ade.get_attribute('aria-label')

                # Truncate everything after the period in the aria label
                al = al[:al.find('.')]
                all_days.append(datetime.strptime(al, fmt))

            next_month_xp = '//button[contains(@class, "ResyCalendar__nav_right")]'
            self.driver.find_element(By.XPATH, next_month_xp).click()

        return all_days

    def get_available_times(self):
        if self.specific_date is not None:
            days = [self.specific_date]
        else:
            days = self.get_available_days()
        # For all days
        # Call https://resy.com/cities/philadelphia-pa/venues/picnic?date=2024-08-07&seats=2
        # Get all times and res types
        # May need a flag to say any res type or specific one

        for day in days:
            day_string = day.strftime('%Y-%m-%d')
            url = f'{self.venue_url}?date={day_string}&seats={self.party_size}'
            self.driver.get(url)
            selector_xp = '//div[@class="VenuePage__Selector-Wrapper"]'
            none_available_xp = '//div[@class="VenuePage__context-text"]'

            self.wait.until(ec.presence_of_element_located((By.XPATH, selector_xp)))
            if self.driver.find_element(By.XPATH, selector_xp + none_available_xp):
                continue
            shift_container_xp = '//div[@class="ReservationButtonList ShiftInventory__shift__slots"]'
            shift_container = self.wait.until(ec.presence_of_element_located((By.XPATH, shift_container_xp)))
            shifts = shift_container.find_elements(By.XPATH, './button[contains(@class, "primary")]')
            for shift in shifts:
                res_id = shift.get_attribute('id')
                # rgs://resy/5408/1125119/2/2024-08-07/2024-08-07/17:00:00/2/Patio
                split = res_id.split('/')
                time_slot = datetime.strptime(f'{split[7]} {split[8]}', '%Y-%m-%d %H:%M:%S')
                self.time_slots[time_slot] = res_id

        # Not a huge fan of this. Right now the date/time is the key, but there could be multiple
        # res types for a single time slot e.g. Patio / Indoor Dining both at 8/4/24 20:30

        return self.time_slots.keys()

    def close(self):
            self.driver.close()
