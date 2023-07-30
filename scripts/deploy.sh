#!/usr/bin/env bash

set -eu -o pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build"

rm -rf "${build_directory}"
mkdir -p "${build_directory}"

pushd "${project_directory}" > /dev/null

>&2 echo "Packaging as wheel..."
poetry build --format wheel
cp dist/*.whl "${build_directory}"

>&2 echo "Installing into venv..."
python3 -m venv "${build_directory}/venv"
"${build_directory}/venv/bin/pip" install -t "${build_directory}/install" "${build_directory}"/*.whl

>&2 echo "Preparing install..."
rm -rf "${build_directory}/install"/*.dist-info


popd > /dev/null
