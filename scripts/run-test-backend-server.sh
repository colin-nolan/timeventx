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

TIMEVENTX_TIMERS_DATABASE_LOCATION="${database_location}" \
    TIMEVENTX_LOG_FILE_LOCATION="${log_location}" \
    TIMEVENTX_BACKEND_PORT="${port}" \
    TIMEVENTX_FRONTEND_ROOT_DIRECTORY="${frontend_directory}" \
    TIMEVENTX_BACKEND_INTERFACE=127.0.0.1 \
    TIMEVENTX_RESTART_ON_ERROR=false \
    TIMEVENTX_LOG_LEVEL=10 \
    TIMEVENTX_ACTION_CONTROLLER_MODULE=timeventx.actions.noop \
    TIMEVENTX_BASE64_ENCODED_CREDENTIALS="$(echo -n 'user:pass' | base64),$(echo -n 'user2:pass2' | base64)" \
    PYTHONPATH=. coverage run timeventx/main.py
