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

architecture="${1:-armv6m}"
device="${2:-/dev/ttyACM0}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
project_directory="$(cd "${script_directory}/.." > /dev/null 2>&1 && pwd)"
build_directory="${project_directory}/build/${architecture}"
dist_directory="${build_directory}/dist"


function delete_directory_contents() {
    local directory="$1"

    mpremote fs ls --no-verbose "${directory}" | dos2unix | awk '{print $2}' | while read -r source; do
        if [[ "${source}" == */ ]]; then
            delete_directory_contents "${directory}${source}"
            mpremote fs rmdir "${directory}${source}"
        else
            mpremote fs rm "${directory}${source}"
        fi
    done
}

# TODO: implement intelligent sync using md5sums.txt

if "${delete_existing_files}"; then
    delete_directory_contents /
fi

pushd "${dist_directory}" > /dev/null

mpremote fs cp -r . :

popd > /dev/null

mpremote df

>&2 echo "Complete!"
