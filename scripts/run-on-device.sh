#!/usr/bin/env bash

set -euf -o pipefail

script_location="$1"
device="${2:-/dev/ttyACM0}"

ampy --port "${device}" run "${script_location}"
