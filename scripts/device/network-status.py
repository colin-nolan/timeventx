import network

wlan = network.WLAN(network.STA_IF)
print(f"Connected: {wlan.isconnected()}")
print(f"ifconfig: {wlan.ifconfig()}")
