import logging
import time
from threading import Thread

import backoff
import ntptime
import network

_logger = logging.getLogger(__name__)


def connect_to_wifi(ssid: str, password: str):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    while not wlan.isconnected():
        wlan.connect(ssid, password)


# XXX: it would be better to use a more precise exception type here
@backoff.on_exception(backoff.expo, Exception)
def sync_time(timezone: int = 0):
    ntptime.settime(timezone=timezone)
    _logger.info(f"Time synchronised: {time.localtime()}")


def main():
    connect_to_wifi("ssid", "password")

    # TODO: run periodically?
    time_sync_thread = Thread(target=sync_time)
    time_sync_thread.start()
