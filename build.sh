#!/usr/bin/env bash

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";

source "${SCRIPT_DIR}/.env"

image_name="${MOSBOT_REPO_URL}/${MOSBOT_REPO_NAME}"
if [ -z "$1" ]; then
  image_version="0.1"
else
  image_version="$1"
fi


if ! docker build . -t "${image_name}:${image_version}"; then
  echo "Failed to build the image."
  exit 1
fi

if ! docker push "${image_name}:${image_version}"; then
  echo "Failed to publish the image."
  exit 2
fi
