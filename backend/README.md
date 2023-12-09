# Backend

## Setup

The following must be available on the path:

- Python 3.11+ (`python3`)
- MicroPython (`micropython`)
- [Poetry](https://python-poetry.org/) (`poetry`)

Install requirements (includes dev dependencies used in the helper scripts):

```shell
poetry install --no-root
```

## Debugging

A convenience script for starting a backend server with a sensible configuration can be used:

```
../scripts/run-test-backend-server.sh
```
