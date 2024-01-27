#! /bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" #gets the current directory
cd "$SCRIPT_DIR"/..

CONTAINER_NAME=${PWD##*/}  

echo "stopping existing container" "$CONTAINER_NAME" 
docker stop "$CONTAINER_NAME" || true 

CONTAINER_HEX=$(printf $CONTAINER_NAME | xxd -p | tr '\n' ' ' | sed 's/\\s//g' | tr -d ' ');

rocker --nvidia --x11 --user --pull --git --name "$CONTAINER_NAME" --volume "${PWD}":/workspaces/"${CONTAINER_NAME}":Z --oyr-run-arg " --detach" --deps-dependencies ubuntu:22.04 

code --folder-uri vscode-remote://attached-container+"$CONTAINER_HEX"/workspaces/"${CONTAINER_NAME}"