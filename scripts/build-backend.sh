#!/usr/bin/env bash

# Note:  deliberately not setting -f as globbing
set -eu -o pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"

architecture="${1:-any}"
build_directory="${2:-"${project_directory}/build/backend"}"

backend_directory="${project_directory}/backend"
dist_directory="${build_directory}/dist"
packaged_libs_directory="${dist_directory}/libs/packaged"
stdlib_libs_directory="${dist_directory}/libs/stdlib"

mkdir -p "${build_directory}" "${packaged_libs_directory}" "${stdlib_libs_directory}"

pushd "${backend_directory}" > /dev/null

>&2 echo "Packaging as wheel..."
poetry build --format wheel
cp dist/*.whl "${build_directory}"

>&2 echo "Downloading Poetry requirements..."
pip3 install -t "${packaged_libs_directory}" "${build_directory}"/*.whl
rm -rf "${packaged_libs_directory}"/*.dist-info
find "${packaged_libs_directory}" -type d -name __pycache__ -exec rm -r {} +
rm "${packaged_libs_directory}/microdot_test_client.py"

>&2 echo "Downloading mip requirements..."
micropython mips-requirements.py "${stdlib_libs_directory}"

project_name="$(poetry version | cut -d ' ' -f 1)"
python_module_name="${project_name/-/_}"
>&2 echo "Creating entrypoint..."
cp "${project_directory}/scripts/device/main.py" "${dist_directory}/main.py"

>&2 echo "Creating configuration..."
PYTHONPATH="${backend_directory}" "${script_directory}/create-config.py" "${dist_directory}"

if [[ "${architecture}" == "any" ]]; then
    >&2 echo "Not pre-compiling libs to be architecture agnostic"
else
    # Note: RPi Pico's architecture is armv6m
    >&2 echo "Pre-compiling libs for ${architecture}..."
    # Find py files, compile them, and remove the original
    # Note: do not compile `main.py` as RPi Pico will not recognise it as the entrypoint
    find "${dist_directory}" -name "*.py" -type f ! -name main.py \
        -exec sh -c "mpy-cross -march=\"${architecture}\" \"\$0\"; rm \"\$0\"" {} \;
fi

popd > /dev/null
