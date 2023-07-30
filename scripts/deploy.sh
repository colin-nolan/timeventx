#!/usr/bin/env bash

set -eu -o pipefail

architecture="${1:-x64}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build"
lib_install_directory="${build_directory}/lib"

rm -rf "${build_directory}"
mkdir -p "${build_directory}"

pushd "${project_directory}" > /dev/null

>&2 echo "Packaging as wheel..."
poetry build --format wheel
cp dist/*.whl "${build_directory}"

>&2 echo "Downloading Poetry requirements..."
pip3 install -t "${lib_install_directory}" "${build_directory}"/*.whl
rm -rf "${lib_install_directory}"/*.dist-info

>&2 echo "Downloading mip requirements..."
docker run --rm \
    -v "${lib_install_directory}:/install" \
    -v "${project_directory}/mips-requirements.py:/mips-requirements.py:ro" \
    micropython/unix:latest \
    micropython /mips-requirements.py /install
# MicroPython complained about permission issues when running as non-root user so correcting file ownership in next step
docker run --rm \
    -v "${lib_install_directory}:/install" \
    alpine:latest \
    chown -R "$(id -u):$(id -g)" /install

>&2 echo "Pre-compiling libs..."
# Find py files, compile them, and remove the original
find "${lib_install_directory}" -name "*.py" -type f \
    -exec sh -c "mpy-cross -march=\"${architecture}\" \"\$0\"; rm \"\$0\"" {} \;

popd > /dev/null

>&2 echo "Complete!"
