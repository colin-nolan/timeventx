#!/usr/bin/env bash

# Not setting -f as deliberately globbing
set -eu -o pipefail

architecture="${1:-any}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
backend_directory="${project_directory}/backend"

build_directory="${project_directory}/build/${architecture}"
dist_directory="${build_directory}/dist"
packaged_libs_directory="${dist_directory}/libs/packaged"
stdlib_libs_directory="${dist_directory}/libs/stdlib"
frontend_directory="${dist_directory}/frontend"

rm -rf "${build_directory}"
mkdir -p "${build_directory}" "${packaged_libs_directory}" "${stdlib_libs_directory}" "${frontend_directory}"

# Build the backend --------------------------------------------------
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

# FIXME: sort
>&2 echo "Applying custom MicroPython module patches..."
find "${backend_directory}/micropython" -type f -name "*.diff" -exec patch -d "${stdlib_libs_directory}" -i {} \;

project_name="$(poetry version | cut -d ' ' -f 1)"
python_module_name="${project_name/-/_}"
>&2 echo "Creating entrypoint..."
cp "${project_directory}/scripts/device/main.py" "${dist_directory}/main.py"

>&2 echo "Creating configuration..."
PYTHONPATH="${backend_directory}" "${script_directory}/create-config.py" "${dist_directory}"

if [[ "${architecture}" == "any" ]]; then
    >&2 echo "Not pre-compiling libs to be architecture agnostic"
else
    >&2 echo "Pre-compiling libs for ${architecture}..."
    # Find py files, compile them, and remove the original
    find "${dist_directory}" -name "*.py" -type f \
        -exec sh -c "mpy-cross -march=\"${architecture}\" \"\$0\"; rm \"\$0\"" {} \;
fi

popd > /dev/null

# Build the frontend --------------------------------------------------
pushd "${project_directory}/frontend" > /dev/null

>&2 echo "Building frontend..."
yarn build --base / --outDir "${frontend_directory}"

popd > /dev/null

# Finalise --------------------------------------------------
pushd "${dist_directory}" > /dev/null

>&2 echo "Creating md5sums..."
find . -type f -exec md5sum {} + > md5sums.txt

popd > /dev/null

>&2 echo "Complete!"
