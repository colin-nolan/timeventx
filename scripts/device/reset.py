import sys
from time import sleep

import machine

print("Resetting device - expect to see an error message", file=sys.stderr)
# Small sleep to allow the printed message to be flushed
sleep(0.25)

machine.reset()
