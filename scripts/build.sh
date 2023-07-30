#!/usr/bin/env bash

# Not setting -f as deliberately globbing
set -eu -o pipefail

architecture="${1:-any}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build/${architecture}"
lib_install_directory="${build_directory}/lib"
project_name="$(poetry version | cut -d ' ' -f 1)"

rm -rf "${build_directory}"
mkdir -p "${build_directory}"

pushd "${project_directory}" > /dev/null

>&2 echo "Packaging as wheel..."
poetry build --format wheel
cp dist/*.whl "${build_directory}"

>&2 echo "Downloading Poetry requirements..."
pip3 install -t "${lib_install_directory}" "${build_directory}"/*.whl
rm -rf "${lib_install_directory}"/*.dist-info
find "${lib_install_directory}" -type d -name __pycache__ -exec rm -r {} +

>&2 echo "Downloading mip requirements..."
micropython "${project_directory}/mips-requirements.py" "${lib_install_directory}"

>&2 echo "Creating entrypoint..."
cp "${lib_install_directory}/${project_name/-/_}/main.py" "${lib_install_directory}"

>&2 echo "Creating configuration..."
PYTHONPATH="${project_directory}" python -c "
from garden_water.configuration import Configuration
from garden_water.main import DEFAULT_CONFIGURATION_FILE_NAME

Configuration.write_env_to_config_file(f'${lib_install_directory}/{DEFAULT_CONFIGURATION_FILE_NAME}')
"

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
