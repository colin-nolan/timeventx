#!/usr/bin/env bash

set -euf -o pipefail

backend_api_root="$1"
build_directory="$2"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
dist_directory="${build_directory}/dist"
frontend_directory="${dist_directory}/frontend"

mkdir -p "${frontend_directory}"

pushd "${project_directory}/frontend" > /dev/null

>&2 echo "Building frontend..."
VITE_BACKEND_API_ROOT="${backend_api_root}" \
    yarn build --base / --outDir "${frontend_directory}"

popd > /dev/null
