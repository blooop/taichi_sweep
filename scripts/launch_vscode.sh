#! /bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" #gets the current directory
cd $SCRIPT_DIR/..

CONTAINER_NAME=${PWD##*/}  

echo "stopping existing container" $CONTAINER_NAME 
docker stop $CONTAINER_NAME || true

container_hex_id=$(printf $CONTAINER_NAME | xxd -p | tr '\n' ' ' | sed 's/\\s//g' | tr -d ' ');

# rocker --x11 --user --home --pull --name $CONTAINER_NAME --mode non-interactive ubuntu:22.04 
# rocker --x11 --user --home --pull --name $CONTAINER_NAME ubuntu:22.04 
rocker --nvidia --x11 --user --home --pull --git --name $CONTAINER_NAME --oyr-run-arg " --detach" --deps-dependencies ubuntu:22.04 


code --folder-uri vscode-remote://attached-container+$container_hex_id/${PWD}