import requests
from datetime import datetime

class ResPlatform:

    def __init__(self, headers, debug=False):
        if headers is not None:
            self.session = requests.Session()
            self.session.headers.update(headers)
        self.debug = debug

    def set_headers(self, headers):
        self.session.headers = headers

    def update_headers(self, headers):
        self.session.headers.update(headers)

    def get_headers(self):
        return self.session.headers

class OpenTable(ResPlatform):
    pass
