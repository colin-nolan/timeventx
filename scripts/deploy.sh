#!/usr/bin/env bash

# Not setting -f as deliberately globbing
set -eu -o pipefail

architecture="${1:-any}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build/${architecture}"
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
micropython "${project_directory}/mips-requirements.py" "${lib_install_directory}"

if [[ "${architecture}" == "any" ]]; then
    >&2 echo "Not pre-compiling libs to be architecture agnostic"
else
    >&2 echo "Pre-compiling libs for ${architecture}..."
    # Find py files, compile them, and remove the original
    find "${lib_install_directory}" -name "*.py" -type f \
        -exec sh -c "mpy-cross -march=\"${architecture}\" \"\$0\"; rm \"\$0\"" {} \;
fi

popd > /dev/null

>&2 echo "Complete!"