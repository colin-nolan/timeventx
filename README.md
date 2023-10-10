# Garden Water

This system is designed to be ran on a RP2040 microcontroller, specifically a [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/).

| Area             | Status                                                                                                                                                                                          |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Build Status     | [![Build Status](https://ci.colinnolan.uk/api/badges/colin-nolan/garden-watering/status.svg)](https://ci.colinnolan.uk/colin-nolan/garden-watering)                                             |
| Backend Coverage | [![Backend Coverage](https://codecov.io/gh/colin-nolan/garden-watering/graph/badge.svg?token=UKCB5SVPED&flag=backend)](https://app.codecov.io/gh/colin-nolan/garden-watering/tree/main/backend) |
|                  |                                                                                                                                                                                                 |

## Usage

To build files for a device:

```text
GARDEN_WATER_WIFI_SSID=<wifi_ssid> GARDEN_WATER_WIFI_PASSWORD=<wifi_password> \
    make build API_SERVER_LOCATION=<backend_api_location> [ARCH=architecture (default: any)]
```

where `ARCH=any` does not compile the Python code for the target platform.

_Note: because the frontend is static, and compiled, the location of the deployed backend must be known at build time._

To subsequently deploy the files to a device:

```shell
./scripts/deploy.sh -d [architecture (default: any)] [device (default: /dev/ttyACM0)]
```

To manually interact with the RP2040 device:

- `mpremote`

## Legal

AGPL v3 (contact for other licencing). Copyright 2023 Colin Nolan.

This work is in no way related to any company that I may work for.
