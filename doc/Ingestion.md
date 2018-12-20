# Neo4j Ingestion

## Strategies

Note: the 'I*' keys are 'Ingestion {strategy num}' and used throughout the test code

* **One create group** I1: in a single file - every statement is a CREATE which avoids the lookup penalty for a MERGE. node count limited by server memory and configuration
* **Create groups** I2: - every statement is a create, but organized into groups that can be created without dependencies
* **Match perfect data** I3: - assumes that all data is known prior to ingestion, but too large to ingest in a single puff. Use a combination of CREATE and MATCH because we count on sequential stmt execution.
* **Merge imperfect data** I4: - assumes we don't know the order of statement execution or if we have all information at the time of create. We create what we know and then update nodes as more data is available.
* **Merge imperfect data spray** I5: - same as above, but use a session pool to have many workers on the same job.
* **CSV** I6 - we can generate a CSV of perfect data and a small set of statements that generate everything, one line at a time. Because we specify types in col headers and neo4j has all the data already parsed, there could be some hidden advantages.

## General perf tuning

* Turn indexing off for 3x perf gain
* Creates are faster than MERGE because there is no lookup
* Memory tuning

conf/neo4j.conf

* dbms.threads.worker_count
* memory

## CSV

* If we mount the imports directory, we can simply put the CSV in it. `dbms.directories.import=import`


## Drivers

* [neo4j-python-driver](https://github.com/neo4j/neo4j-python-driver): Official driver, replaces neo4j-driver, has bolt

## Fastest way to ingest live data

References:

* [Neo4j guidance](https://neo4j.com/developer/guide-import-csv/)

When we load storage data, we want that data available for query as quickly as possible. What are the options?

* Cannot dump/load - can't write that format
* Cannot use native LOAD

Strategies:

* Python Cypher statements
* Generate Cypher in file and load that
* Generate CSV & load it
* Generate many partial CSV's and load them

Notes:

* indexes and constraints are declared and online prior to MERGE
* prefix load statement with USING PERIODIC COMMIT 10000
* If possible, separate node creation from relationship creation into different statements
If your import is slow or runs into memory issues, see [Mark’s blog post on Eager loading](https://markhneedham.com/blog/2014/10/23/neo4j-cypher-avoiding-the-eager/).

Questions

* Should we load new data into its own database

TODO

* Neo4j can ingest from a URI - would this be simpler once the schema is setup?

## How fast can data load and export/import be?

Two use cases:

* Real


# Exports

References:

* [Neo4j basic process](https://neo4j.com/docs/operations-manual/current/tools/dump-load/)
* [Neo4j guidance](https://neo4j.com/developer/kb/export-sub-graph-to-cypher-and-import/)
* 

How do we snapshot the database for purge and reload?

* `neo4j-admin dump --to /project/tmp` <- only works if database is off, not so useful for moving things into and out of a db


Snapshotting a single database

The default database dump/load requires the database to be off
```
# Stop running container
docker stop neo

# Run it as a bash process
docker run -it --rm             \
    -p 7474:7474                \
    -p 7687:7687                \
    -v $(pwd):/project          \
    -v "$(pwd)/neo4j_docker_volume":/data  \
    --name neo-backup           \
    neo4j:latest                \
    bash

# Dump (note: only using one db, dumping everything)
./bin/neo4j-admin dump --to /project/tmp
```


A useful way to understand imports is to generate some exports

# Bulk import

Create order

1. nodes
1. indexes
1. relations

Cypher

* Paste into browser for small jobs
* For medium sized jobs
    ```
    docker exec -it neo bash -c "cat /project/${1} | /var/lib/neo4j/bin/cypher-shell -u neo4j -p Admin1234!"
    ```

CSV is the fastest, [this article](https://neo4j.com/blog/import-10m-stack-overflow-questions/) claiming 10^6 SO questions imported in 3 min.

See `:help load csv`, can gzip the files

Notes:

* Large dataset imports should use the offline tool
* `apoc.import.csv` can be used for small to medium datasets


# Lessons learned

## Imports

### Creates are faster than Merge

So the optimally performing strategy for small batches is:

1. Create all nodes with ref vars
1. Create all relationships using ref vars

This eliminates an initial search that must be done in the MERGE case - to determine if the element is matched or needs to be created.


### LOAD FROM CSV

Is not the magic bullet I thought it was - it just becomes a data source where you write a few queries fed by that data.
