import logging
import sys
import os

from .client import Client


HANDLE = int(sys.argv[1])

def run(url_suffix="", retry=0):
    url = sys.argv[0]

    logging.debug("Running action: %s" % (url))

    if '/clear_cookies' in url:
        client = Client()
        cookies = client._locate_cookies()
        logging.info("Removing cookies from %s" % (cookies))
        if os.path.isfile(cookies):
            os.remove(cookies)
            logging.info("Successfully removed cookies file")
