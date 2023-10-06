#!/usr/bin/env bash

# Not setting -f as deliberately globbing
set -eu -o pipefail

backend_api_root="$1"
architecture="${2:-any}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build/${architecture}"
dist_directory="${build_directory}/dist"

rm -rf "${build_directory}"
mkdir -p "${build_directory}"

>&2 echo "Building backend..."
"${script_directory}/build-backend.sh" "${architecture}" "${build_directory}"

>&2 echo "Building frontend..."
"${script_directory}/build-frontend.sh" "${backend_api_root}" "${build_directory}"

pushd "${dist_directory}" > /dev/null

>&2 echo "Creating md5sums..."
find . -type f -exec md5sum {} + > md5sums.txt

popd > /dev/null

>&2 echo "Complete!"
echo "${dist_directory}"