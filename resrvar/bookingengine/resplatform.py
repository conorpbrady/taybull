import logging

class ResPlatform:

    def __init__(self, headers, debug=False):
        if headers is not None:
            self.session = requests.Session()
            self.session.headers.update(headers)
        self.debug = debug

    def update_headers(self, headers):
        self.session.headers.update(headers)

    def log_request(self, r):
        logging.info('%s | %s', r.status_code, r.request.url)

        logging.debug(r.request.headers)
        logging.debug(r.request.body)
        logging.debug(r.text)

class OpenTable(ResPlatform):
    pass
