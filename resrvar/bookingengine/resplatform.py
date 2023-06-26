import requests
from datetime import datetime

class ResPlatform:

    def __init__(self, headers, debug=False):
        if headers is not None:
            self.session = requests.Session()
            self.session.headers.update(headers)
        self.debug = debug

    def update_headers(self, headers):
        self.session.headers.update(headers)

class OpenTable(ResPlatform):
    pass
