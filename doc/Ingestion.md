# Neo4j Ingestion

## Strategies

Note: the 'I*' keys are 'Ingestion {strategy num}' and used throughout the test code

### Ingest 1: One create group

_Description:_ A `run()` execution whose statements are only CREATE node, then CREATE relationship. CREATEs avoid the lookup penalty for a MERGE and are theoretically faster. Content of a single `run()` is limited by server memory and configuration.

Implementation is two passes:

* CREATE stmts for all nodes
* CREATE stmts for all edges

This strategy's benefit is that we don't have to define nodes or edges in any particular order; don't need to ensure an element has been created prior to reference. There are no dependencies between node CREATE statements and no dependencies between edge CREATE statements. As long as all nodes are defined prior to being referenced during edge creation, we are good.

A decent strategy for up to 1750 nodes with default tuning.

Notes:

* The Neo4j config allows allocating a transaction memory heap to allow this size to grow
* If we get 2000 elements/api call from Dropbox, we could boost memory and just use this mechanism for each api result.

### Ingest 2: Create groups

_Description:_ Every statement is a create, but organized into groups that can be `run()` separately.

After writing Ingest 1, I added the `parent_id` to each node and eliminated cypher generation dependency on hierarchy traversal - because a node always knows its parent, a directory can always generate itself, its files, link to parent and link to files.

This strategy uses that new ability and groups each directory's cypher statements so they can be processed in chunks appropriate to Neo4j write tuning.

This strategy started out as a way to break the individual `run()` size limits. Unexpectedly, node reference variable lifetime is longer than a run(), a session, and a ';'. This means we could break a large dataset at any convenient point omitting the need for line spacing. This strategy can tackle potentially unbounded datasets.

**TODO**: What is a node variable lifetime?
      In our naive use, a session.run() is an autocommit
      Node reference variable lifetime is longer than run(), session, and ';'


### Ingest 3: Match perfect data - **DON'T USE**

_Description:_ assumes that all data is known prior to ingestion, but too large to ingest in a single puff. Use a combination of CREATE and MATCH because we count on sequential stmt execution.

This strategy started as mitigation for the `run()` size limit and assumed that variables would be invalidated. The strategy fails because of complications with MATCH and MERGE.

* MATCH requires a WITH clause that rescopes variables, groups aggregates and frustrates subsequent statements
* MERGE requires a unique variable name. We are using `n[self.id]` so if the node or edge has been referenced before, we see `Variable 'n9768633' already declared`.

We can generate a new variable with an `m` prefix to avoid the MERGE problem, but results from Ingest 2 prove that it is not needed - a CREATE should always be faster because there is no index lookup required.

### Ingest 4: Merge imperfect data

_Description:_ assumes no order to information delivery and incomplete data. E.g. Dropbox returns a batch of json objects describing individual elements, but not in we don't know the order of statement execution or if we have all information at the time of create. We create what we know and then update nodes as more data is available.

```cypher
# Us the single constrained property to match any existing node.
# Otherwise, we could fail to match [because some properties were not defined earlier] and create a duplicate node
MERGE (n123:Directory {id: 123})
# If the node does not exist - set all properties
ON CREATE SET
    name = '', ...
# If the node already existed - update all properties to lates values
ON MATCH SET
    name = '', ...
```

### Ingest 5: Merge imperfect data spray

_Description:_ same as above, but use a session pool to have many workers on the same job.


### Ingest 6: CSV

_Description:_ we can generate a CSV of perfect data and a small set of statements that generate everything, one line at a time. Because we specify types in col headers and neo4j has all the data already parsed, there could be some hidden advantages.


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
