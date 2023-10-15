#!/usr/bin/env bash

set -euf -o pipefail

port="${1:-3005}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
backend_directory="${project_directory}/backend"

temp_directory="$(mktemp -d -t backend-XXXX)"
trap 'rm -rf "${database_location}"' EXIT

database_location="${temp_directory}/database"
log_location="${temp_directory}/log.txt"

frontend_directory="${temp_directory}/frontend"
mkdir "${frontend_directory}"
echo "Hello world" > "${frontend_directory}/index.html"

pushd "${backend_directory}" > /dev/null

GARDEN_WATER_TIMERS_DATABASE_LOCATION="${database_location}" \
    GARDEN_WATER_LOG_FILE_LOCATION="${log_location}" \
    GARDEN_WATER_BACKEND_PORT=${port} \
    GARDEN_WATER_FRONTEND_ROOT_DIRECTORY="${frontend_directory}" \
    GARDEN_WATER_BACKEND_INTERFACE=127.0.0.1 \
    GARDEN_WATER_RESTART_ON_ERROR=false \
    GARDEN_WATER_LOG_LEVEL=10 \
    GARDEN_WATER_ACTION_CONTROLLER_MODULE=garden_water.actions.noop \
    PYTHONPATH=. coverage run garden_water/main.py
