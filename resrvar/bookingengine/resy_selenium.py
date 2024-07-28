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

        # Make selenium headless, set window size to 1920x1080 so elements will load
        # Set user agent to get around cloudflare verification
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        options.add_argument(f'--user-agent={user_agent}')

        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 5)

        super().__init__(None)

    def authenticate(self, *args, **kwargs):

        driver.get('https://resy.com')
        login_button_xp = '//button[@data-test-id="menu_container-button-log_in"]'
        login_button = wait.until(ec.presence_of_element_located((By.XPATH, login_button_xp)))
        login_button.click()

        use_email_pw_xp = '//div[@class="AuthView__Footer"]/button'
        use_email_pw = wait.until(ec.presence_of_element_located((By.XPATH, use_email_pw_xp)))
        use_email_pw.click()

        email_input = wait.until(ec.presence_of_element_located((By.ID, 'email')))
        email_input.send_keys('conorpbrady@gmail.com')
        pass_input = wait.until(ec.presence_of_element_located((By.ID, 'password')))
        pass_input.send_keys('G@t0rade##')

        driver.find_element(By.XPATH, '//button[text()="Continue"]').click()
        wait.until(ec.presence_of_element_located((By.XPATH, '//div[@class="ProfilePhoto"]')))

    def book(self, time_slot):
        pass

    def get_available_days(self):
        fmt = '%B %d, %Y'
        months = 3
        base_url = 'https://resy.com/cities/philadelphia-pa/venues/picnic'
        driver.get(base_url)
        calendar_button = wait.until(ec.presence_of_element_located(
            (By.ID, 'VenuePage__calendar__quick-picker__ellipsis')))
        calendar_button.click()


        all_days = []

        for i in range(months):
            calendar_table_xp = '//table[@class="CalendarMonth__Table"]'
            calendar_table = wait.until(ec.presence_of_element_located((By.XPATH, calendar_table_xp)))

            available_day_elements = calendar_table.find_elements(By.XPATH,
                './/button[contains(@class, "ResyCalendar-day--available")' \
                'or contains(@class, "ResyCalendar-day--selected__available")]')

            for ade in available_day_elements:
                al = ade.get_attribute('aria-label')

                # Truncate everything after the period in the aria label
                al = al[:al.find('.')]
                all_days.append(datetime.strptime(al, fmt))

            next_month_xp = '//button[contains(@class, "ResyCalendar__nav_right")]'
            driver.find_element(By.XPATH, next_month_xp).click()

        return all_days

    def get_available_times(self):
        days = get_available_days(self)
        # For all days
        # Call https://resy.com/cities/philadelphia-pa/venues/picnic?date=2024-08-07&seats=2
        # Get all times and res types
        # May need a flag to say any res type or specific one
