import logging
import time
from threading import Thread

_logger = logging.getLogger(__name__)


def connect_to_wifi(ssid: str, password: str):
    # Deferring import to allow testing using MicroPython without a network module
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # TODO: harden
    while not wlan.isconnected():
        wlan.connect(ssid, password)
        time.sleep(1)


def sync_time(timezone: int = 0):
    # Deferring import to allow testing using MicroPython without a network module
    import ntptime

    # TODO: harden
    ntptime.settime(timezone=timezone)
    _logger.info(f"Time synchronised: {time.localtime()}")


def main():
    connect_to_wifi("ssid", "password")

    # TODO: run periodically?
    time_sync_thread = Thread(target=sync_time)
    time_sync_thread.start()


if __name__ == "__main__":
    main()
