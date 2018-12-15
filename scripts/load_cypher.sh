#!/bin/sh
#
# Load a cypher script into a running neo4j
# - the script should be at project root
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

    # Assumptions:
    # - neo4j started with 'run_neo4j.sh', so
    #   - 'neo' is container name
    #   - this project dir mounted at `/project`
    #   - creds
    docker exec -it neo bash -c "cat /project/${1} | /var/lib/neo4j/bin/cypher-shell -u neo4j -p Admin1234!"

)



