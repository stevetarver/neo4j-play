#!/bin/sh
#
# Start neo4j using a volume mount in our project directory
#
if [ "$(uname -s)" = "Darwin" ]; then
    # If called through a symlink, this will point to the symlink
    THIS_SCRIPT_DIR="$( cd "$( dirname "${0}" )" && pwd )"
else
    THIS_SCRIPT_DIR=$(dirname $(readlink -f "${0}"))
fi
(
    # Run from project root
    cd ${THIS_SCRIPT_DIR}/..

    NEO4J_DATA_DIR="neo4j/docker/data"
    PROJECT_DIR=$(pwd)
    DATA_DIR="${PROJECT_DIR}/${NEO4J_DATA_DIR}"
    CTNR_NAME="neo"

    # A start is a restart; stop the container, blow away data, fresh plate
    # Kill any existing container
    EXISTING=$(docker ps -aqf "name=${CTNR_NAME}")
    if [ "${EXISTING}" ]; then
        echo "Removing running container ${EXISTING}"
        docker rm -f ${EXISTING}
    fi

    if [ -d "${NEO4J_DATA_DIR}" ]; then
        echo "Deleting existing data in ${NEO4J_DATA_DIR}"
        rm -rf "${NEO4J_DATA_DIR}"
    fi
    mkdir -p "${NEO4J_DATA_DIR}"
    ERROR="${?}"
    if [ 0 -ne ${ERROR} ]; then
        exit ${ERROR}
    fi

    echo "Running Neo4j"
    docker run -d                   \
        -p 7474:7474                \
        -p 7687:7687                \
        -v ${PROJECT_DIR}:/project  \
        -v ${DATA_DIR}:/data        \
        --name ${CTNR_NAME}         \
        neo4j:latest
)



