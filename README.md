[![Build Status](https://nobadkitty.tplinkdns.com:8900/api/badges/colin-nolan/garden-watering/status.svg)](https://nobadkitty.tplinkdns.com:8900/colin-nolan/garden-watering)

# Garden Water

## Setup
The following must be available on the path:
- Python 3.11+ (`python3`)
- MicroPython (`micropython`)
- [Poetry](https://python-poetry.org/) (`poetry`)

Install requirements (includes dev dependencies used in the helper scripts):
```shell
poetry install --no-root
```

## Usage
To build files for a device:
```shell
./scripts/build.sh [architecture (default: any)]
```
where `any` does not compile the Python code.

To subsequently deploy the files to a device:
```shell
./scripts/deploy.sh -d [architecture (default: any)] [device (default: /dev/ttyACM0)]
```

To manually interact with the RP2040 device:
- `mpremote`
