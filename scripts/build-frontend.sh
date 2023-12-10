#!/usr/bin/env bash

set -euf -o pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"

backend_api_root="$1"
build_directory="${2:-"${project_directory}/build"}"

mkdir -p "${build_directory}"

pushd "${project_directory}/frontend" > /dev/null

>&2 echo "Packaging frontend..."
VITE_BACKEND_API_ROOT="${backend_api_root}" \
    yarn build --base / --emptyOutDir --outDir "${build_directory}/dist/frontend"

popd > /dev/null
