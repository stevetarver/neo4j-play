# Neo4j

## Graph db choices

* Neo4j - oldest, most mature?
    * native graph database because it efficiently implements the property graph model down to the storage level
    * user defined aggregation functions - stored in db, allows us to optimize all operations
* JanusGraph - google backed, [home](http://janusgraph.org/). No docker image. Tediously complex. Not native graph execution like Neo4j.

## References

Education (links ordered as an educational journey)

* [Neo4j high level overview](https://www.youtube.com/watch?v=pMjwgKqMzi8)
* [Cypher overview](https://www.youtube.com/watch?v=pMjwgKqMzi8)
* [Neo4j beginner tutorial](https://www.youtube.com/watch?v=5Tl8WcaqZoc) (6 15 min parts)
* 
* [Quackit tutorial](https://www.quackit.com/neo4j/tutorial/)


Reference

* [Cypher manual](https://neo4j.com/docs/cypher-manual/3.5/)
* [Neo4j graph algorithms](https://neo4j.com/docs/graph-algorithms/3.4/)
* [Neo4j ops manual](https://neo4j.com/docs/operations-manual/current/)
* [Cypher Style Guide](https://github.com/opencypher/openCypher/blob/master/docs/style-guide.adoc)



## Modeling

What are the key design decisions?


## Generating data

### Python generated queries




## Transforming data


## Importing

* Paste cypher into http client - few hundred lines
* Load cypher file


### CSV import



## Queries

### Syntax notes

Nodes are wrapped by parens

* `()`, `(p)` - empty node, referenced node
* `(p:Person)` - referenced node with single label (or tag)
* `(p:Person:Mammal)` - referenced node with multiple labels
* `(p:Person {name: 'Bob'})` - referenced node with tag and properties

References are added to elements so you can refer to those elements later in a query - e.g. the `p` in `(p:Person)`.


Relationships are wrapped with square brackets

* `-[:CHILD]->` - named, directed relationship
* `(p1)-[c:CHILD]->(p2)` - named, directed relationship between nodes
* `(p1)<-[:PARENT]-(p2)` - directions can be specified


The basic relationship forms are:

```
() - [] - ()  # relationship exists
() - [] ->()  # directed relationship right
()<- [] - ()  # directed relationship left
```

### Style notes

From the [Style Guide](https://github.com/opencypher/openCypher/blob/master/docs/style-guide.adoc)

* Language keywords: uppercase
* Relationships: uppercase
* Node tags: proper case
* Functions, properties, vaiables, parameters: camel case
* Null, bool: lower case


### Constraints

Before adding data, we need to setup constraints to prevent creating duplicate nodes - we want each node to represent exactly one item ITRW.

Notes: 

* CREATEs will throw errors if the node, edge already exists, so we must write more resilient CREATE statements.
* No unique constraints on relationships - always use MERGE to create a relationship

```
# Each node instance is unique, as identified by its id
CREATE CONSTRAINT ON (d:Directory)      ASSERT d.id IS UNIQUE;
CREATE CONSTRAINT ON (f:File)           ASSERT f.id IS UNIQUE;
CREATE CONSTRAINT ON (c:Classification) ASSERT c.id IS UNIQUE;
```

**NOTE**: Node key and property constraints available only in enterprise edition (e.g. throw error when creating a node without an id)

### Create nodes

Create a node

```
CREATE (:File {id: 9447561, name: 'Project_Default.xml', stem: 'Project_Default', extension: '.xml'})
```

Create a relationship. Note: always use `MERGE` in this case to avoid creating duplicate relationships.

```
MATCH (d:Directory), (f:File)
WHERE d.id = 9437821 AND f.id = 9446967
MERGE (d) - [:PARENT] -> (f)
```

Create directed graph entry - combining the two above into a single statment

```
CREATE (:Directory {name:'etc'})  - [:PARENT] -> (:Directory {name:'conf.d'})
CREATE (:Directory {name:'etc'}) <- [:CHILD]  -  (:Directory {name:'conf.d'})

# No - an undirected relationship is not supported as a create
CREATE (:Directory {name:'etc'})  - [:NEAR]   -  (:Directory {name:'conf.d'})
```

Create a single node and many relationships to existing objects:

### Apply classifications

Two approaches:

* Create a node per classification
    * Simple to reason about
    * Clear to view if we put the graph in the UI
    * Suspect it will be more performant with large number of classifications - reduced nodes/edges to process
* Create a classification node and edges define the classification


```
# Attach a classification `code` to every python file
CREATE (:Classification {id: 'code', name: 'code'});

MATCH (f:File {extension: '.py'}), (c:Classification {id: 'code'})
MERGE (f) - [:IS_CLASSIFIED] -> (c);

# One more
CREATE (:Classification {id: 'text', name: 'text'});

MATCH (f:File {extension: '.txt'}), (c:Classification {id: 'text'})
MERGE (f) - [:IS_CLASSIFIED] -> (c);
```

Example of single classification node

```
CREATE (:Classification {id: 'id'});

MATCH (f:File {extension: '.py'}), (c:Classification {id: 'id'})
MERGE (f) - [:IS_CODE] -> (c);
```


**TODO** Finish this example vvv

Create a relationship when nodes may not exist. Because each node may have many children, we cannot use CREATE for each node relationship - the first will succeeed and the rest will fail the uniqueness constraint. We can always, safely use a MERGE and it will create what does not exist.

```
MERGE (d:Directory {id: 94378211}), (f:File {id: 94469671})
ON CREATE
    d.name = 'neo4j-play', d.stem = 'neo4j-play', d.extension = ''
    f.name = 'constraints.txt', f.stem = 'constraints', f.extension = 'txt'
MERGE 
    (d)  - [:PARENT] -> (f)
    (d) <- [:CHILD]  - (f)
```

Add a child to a node that may already exist (upsert)

```
MERGE  (d:Directory {id: 'guid', name:'conf.d'})
CREATE (d) - [:CHILD] -> (:File {id:'guid', name:'myconf.conf'})
```

Let's improve the above. If the merge results in a create, we want to properly initialize the directory

```
MERGE  (d:Directory {id: 'guid', name:'conf.d'})
ON CREATE SET
    d.access = 'perms'
    d.
CREATE (d) - [:CHILD] -> (:File {id:'guid', name:'myconf.conf'})
```

Finally, let's handle the case where the file exists before the directory

```
MERGE  (d:Directory {id: 'guid', name:'conf.d'})
ON CREATE SET
    d.access = 'perms'
    d.
MERGE (d) - [:CHILD] -> (:File {id:'guid', name:'myconf.conf'})
```

Create always bi-directional entry (parent-child)

### Set properties on an existing node

```
MATCH  (p:Directory)-[:Parent]->(f:File)
WHERE  
    d.name = 'conf.d'
    f.name = 'myconf.conf'
SET    f.access = 766
RETURN f

# could also set by object
SET f += {access: 766}
```

Return the path to an item

All files with a `conf` suffix

```
MATCH  (f:File)
WHERE  f.extension = "conf"
RETURN f

MATCH  (f:File {extension: 'conf'})
RETURN f

# perhaps this as well
MATCH  (File {extension: 'conf'})
```

Add an edge from an existing node to an existing node

Add classification to nodes

How to keep each customer's data separate?

Create a file in an existing directory

create (:Directory {name:'etc'}) - [:PARENT] -> (:Directory {name:'conf.d'})

### Advanced queries

Find items with Classification `code`

```
MATCH (n) - [:IS_CLASSIFIED] -> (:Classification {id: 'text'}) RETURN n

# For presentation, this includes the classification
MATCH (n) - [:IS_CLASSIFIED] -> (c:Classification {id: 'text'}) RETURN n,c
```

Find decendents of

```

```

Find ancestors of

```
```

Find all decendent files

```
```

Find everything a perspective can see. This is an attribute search, so we need to know the access model. E.g. is user the owner, in the group, or is the file publicly visible - more attributes mean simpler queries.

**TODO** enhance this to reflect comments

```
MATCH (n {owner: 501}) RETURN n
```

ops
create
classify (by reg ex)

whitelist clasification
all data in this classification (set of classes)
all data not in this classification (set of classes)
node by id

blacklist
subset of above

diff of trees
counts of all above

all classifications not included in this set



Return this path and the nodes that match

```
MATCH  path = (:Directory) - [:CHILD] -> (:Directory)
RETURN path
```

Return graph or tabular data

```
# return graph
MATCH (p:Person {name: 'Tom Hanks'})-[r:ACTED_IN | DIRECTED]-(m:Movie)
RETURN p, r, m;

# Or tabular result
MATCH (p:Person {name: 'Tom Hanks'})-[r:ACTED_IN | DIRECTED]-(m:Movie)
RETURN p.name, type(r), m.title;
```

Grouping is implict by any non-aggregate fields

```
RETURN p.name, count(*) as movie_count
```

See APOC library for 400 user defined functions

Where clause - much like SQL

null means does not exist - cannot assign null

**TODO** Add a classification - all files with perms x


## Indexes

**TODO** Identify common query patterns and index appropriate fields

```
CREATE INDEX ON :Album(Name)
```

## Exporting


## Deployment

* Neo4j has a google cloud launcher [here](https://neo4j.com/developer/neo4j-cloud-google-cloud-launcher/#_deploy_neo4j_enterprise) and a [startup program](https://neo4j.com/startup-program/?ref=developers)



# Bulk import

Cypher

* Paste into browser for small jobs
* For medium sized jobs
    ```
    docker exec -it neo bash -c "cat /project/${1} | /var/lib/neo4j/bin/cypher-shell -u neo4j -p Admin1234!"
    ```

CSV is the fastest, [this article](https://neo4j.com/blog/import-10m-stack-overflow-questions/) claiming 10^6 SO questions imported in 3 min.

See `:help load csv`, can gzip the files

# Imports

Create order

1. nodes
1. indexes
1. relations

# Python drivers

* neo4j-driver (currently recommended on neo4j website)
* py2neo


# Neo4j queries in python


# Ops

Useful commands

* `:sysinfo` - system metrics
