#!/usr/bin/env bash

set -euf -o pipefail

delete_existing_files=false
while getopts "d" options; do
    case "${options}" in
        d)
            delete_existing_files=true
            ;;
        ?)
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

architecture="${1:-any}"
device="${2:-/dev/ttyACM0}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build/${architecture}"
lib_install_directory="${build_directory}/lib"

# TODO: implement intelligent sync using md5sums.txt

if "${delete_existing_files}"; then
    >&2 echo "Clearing storage..."
    # Seems to work - and very quickly - but errors
    ampy --port "${device}" rmdir / 2> /dev/null || true

    # Removes any remaining files/directories in the case that the above command failed (perhaps for a reason other than
    # when it errors and is successful)
    if [[ $(ampy --port "${device}" ls -r / | wc -l) -ne 1 ]]; then
        ampy --port "${device}" ls -r / | while IFS= read -r file; do
            >&2 echo "Deleting file: ${file}..."
            ampy --port "${device}" rm "${file}"
        done
        ampy --port "${device}" ls / | while IFS= read -r directory; do
            >&2 echo "Deleting directory: ${directory}..."
            ampy --port "${device}" rmdir "${directory}"
        done
    fi
fi

find "${lib_install_directory}" -mindepth 1 -type d -print0 | while IFS= read -r -d '' source; do
    directory="${source/${lib_install_directory}\///}"
    >&2 echo "Creating directory: ${directory}..."
    ampy --port "${device}" mkdir --exists-okay "${directory}"
done

find "${lib_install_directory}" -type f -print0 | while IFS= read -r -d '' source; do
    destination="${source/${lib_install_directory}\///}"
    >&2 echo "Copying: ${destination/\///}..."
    ampy --port "${device}" put "${source}" "${destination}"
done

>&2 echo "Complete!"
