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
* [Neo4j worst practices](https://neo4j.com/blog/dark-side-neo4j-worst-practices/)
* [Quackit tutorial](https://www.quackit.com/neo4j/tutorial/)

Tips & Tricks

* [Common confusion](https://neo4j.com/blog/common-confusions-cypher/)

Reference

* [Cypher manual](https://neo4j.com/docs/cypher-manual/3.5/)
* [Neo4j graph algorithms](https://neo4j.com/docs/graph-algorithms/3.4/)
* [Neo4j ops manual](https://neo4j.com/docs/operations-manual/current/)
* [Cypher Style Guide](https://github.com/opencypher/openCypher/blob/master/docs/style-guide.adoc)
* [APOC](https://github.com/neo4j-contrib/neo4j-apoc-procedures)

Perf Tuning

* [Ops manual: perf](https://neo4j.com/docs/operations-manual/current/performance/#memory-tuning)


Interesting

* [Modeling files and permissions](https://maxdemarzi.com/2013/03/18/permission-resolution-with-neo4j-part-1/)

**TODO** a useful cheat sheet I should steal from: 

* https://gist.github.com/DaniSancas/1d5265fc159a95ff457b940fc5046887
* https://www.remwebdevelopment.com/blog/sql/some-basic-and-useful-cypher-queries-for-neo4j-201.html

## Modeling

What are the key design decisions?

* [https://neo4j.com/blog/data-modeling-basics/](https://neo4j.com/blog/data-modeling-basics/)

## Queries

**NOTE**: These queries use the neo4j-play test set

### Syntax notes

Nodes are wrapped by parens

* `()`, `(p)` - empty node, referenced node
* `(p:Person)` - referenced node with single label (or tag)
* `(p:Person:Mammal)` - referenced node with multiple labels
* `(p:Person {name: 'Bob'})` - referenced node with tag and properties

References are added to elements so you can refer to those elements later in a query - e.g. the `p` in `(p:Person)`.


Relationships are wrapped with square brackets

* `-[:CHILD_OF]->` - named, directed relationship
* `(p1)-[c:CHILD_OF]->(p2)` - named, directed relationship between nodes
* `(p1)<-[:PARENT_OF]-(p2)` - directions can be specified


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

**Notes**: 

* CREATEs will throw errors if the node, edge already exists, so we must write more resilient CREATE statements.
* No unique constraints on relationships - always use MERGE to create a relationship

```
// Each node instance is unique, as identified by its id
// Creates an index on id
CREATE CONSTRAINT ON (d:Directory)      ASSERT d.id IS UNIQUE;
CREATE CONSTRAINT ON (f:File)           ASSERT f.id IS UNIQUE;
CREATE CONSTRAINT ON (c:Classification) ASSERT c.id IS UNIQUE;

// Remove these constraints
DROP CONSTRAINT ON (d:Directory)      ASSERT d.id IS UNIQUE;
DROP CONSTRAINT ON (f:File)           ASSERT f.id IS UNIQUE;
DROP CONSTRAINT ON (c:Classification) ASSERT c.id IS UNIQUE;
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
MERGE (d) - [:PARENT_OF] -> (f)
```

Create directed graph entry - combining the two above into a single statment

```
CREATE (:Directory {name:'etc'})  - [:PARENT_OF] -> (:Directory {name:'conf.d'})
CREATE (:Directory {name:'etc'}) <- [:CHILD_OF]  -  (:Directory {name:'conf.d'})

# No - an undirected relationship is not supported as a create
CREATE (:Directory {name:'etc'})  - [:NEAR]   -  (:Directory {name:'conf.d'})
```

**Notes**: 

* You can create a node with multiple labels - where it makes sense: `CREATE (:Directory:SymLink {id: 'xxxxx'})`

## Merging nodes

MERGE statements combine CREATE and MATCH; if the node does not exist, it is created, if it does exist, it is matched. All elements of the MERGE pattern must be met for it to be matched. Because we ensure the `id` is unique on all nodes, we can simply match on the `id`.

MERGE provides conditional blocks for both CREATE and MATCH, allowing different actions to be taken in each case.

Multiple create statements for the same node. Use case: we may get full data from an api call multiple times - using MERGE ON CREATE SET allows us to create the node without violating constraints and generating an error. Two forms are shown.

```
// This merge matches nodes given all elements. If the node was previously created and some data
// has changed, it generates a constraint violation.
MERGE (:File {id: 94475611, name: 'foo.xml', stem: 'foo', extension: '.xml'})

// This merge matches only the unique identifier and will avoid the constraint violation
MERGE (f:File {id: 94475611})
ON CREATE SET
    f.name = 'foo.xml', f.stem = 'foo', f.extension = '.xml'
```

Create a node with partial data, then later add remaining data. Use case: we get partial data returned from an api call, and a later call provides more data. Or, we don't know if the existing node has all data.

```
// Pass 1: we are only give the item id - we form the property list with the information provided
MERGE (f:File {id: 94475612})
RETURN f

// Later, we are given full information and include that in the ON MATCH SET.
// This could be used in the distant future to capture
MERGE (f:File {id: 94475612})
ON MATCH SET
    f.name = 'bar.xml', f.stem = 'bar', f.extension = '.xml'
RETURN f
```

### Creating relationships

Create a relationship with possibly sparse data:

* The nodes may have already been specified
* The nodes may not exist
* The relationship between the nodes is given

```
MERGE (d:Directory {id: 444})
MERGE (f:File {id: 555})
MERGE (f) - [:CHILD_OF] -> (d) - [:PARENT_OF] -> (f)
RETURN d,f
```

Note: because we MERGEd the relationship, no duplicate relationships are created


### Apply classifications

Two approaches:

* Create a node per classification
    * Simple to reason about
    * Clear to view if we put the graph in the UI
    * Suspect it will be more performant with large number of classifications - reduced nodes/edges to process
* Create a classification node and edges define the classification

Example of single classification node - just fyi - won't use

```
CREATE (c:Classification {id: 'classifications', name: 'classifications'})
WITH c
MATCH (code:File {extension: 'py'}), (text:File {extension: 'txt'})
MERGE (code) - [:IS_CODE] -> (c);
MERGE (text) - [:IS_TEXT] -> (c);
```

Attach a new classification `code` to every python file

```
CREATE (c:Classification {id: 'code', name: 'code'})
WITH c
MATCH (f:File {extension: 'py'})
MERGE (f) - [:IS_CLASSIFIED] -> (c);

CREATE (c:Classification {id: 'text', name: 'text'})
WITH c
MATCH (f:File {extension: 'txt'})
MERGE (f) - [:IS_CLASSIFIED] -> (c);
```

If the classification does not already exist, these could also be written on one line:

```cypher
MATCH (f:File {extension: 'py'}) MERGE (f) - [:IS_CLASSIFIED] -> (:Classification {id: 'code', name: 'code'});
MATCH (f:File {extension: 'rst'}) MERGE (f) - [:IS_CLASSIFIED] -> (:Classification {id: 'doc', name: 'doc'});
```

If the classification may already exist, or you are matching multiple groups of objects (including groups of the same label), you must MERGE the classification:

```cypher
MERGE (c:Classification {id: 'code', name: 'code'}) 
WITH c 
MATCH (f:File) 
WHERE f.extension IN ['c', 'py'] 
MERGE (f) - [:IS_CLASSIFIED] -> (c);

MERGE (c:Classification {id: 'code', name: 'code'}) WITH c MATCH (f:File) WHERE f.extension IN ['c', 'py', 'sh'] MERGE (f) - [:IS_CLASSIFIED] -> (c);
MERGE (c:Classification {id: 'doc', name: 'doc'}) WITH c MATCH (f:File) WHERE f.extension IN ['rst', 'md'] MERGE (f) - [:IS_CLASSIFIED] -> (c);
```

Any qualification (WHERE clause) can be used

```
CREATE (c:Classification {id: 'big', name: 'big'})
WITH c
MATCH (f:File)
WHERE f.size > 10000
MERGE (f) - [:IS_CLASSIFIED] -> (c);
```

Even regex - all items that have `neo` in the name

```
CREATE (c:Classification {id: 'neo', name: 'neo'})
WITH c
MATCH (n)
WHERE n.name =~ '.*[Nn]eo.*' AND (n:Directory OR n:File)
MERGE (n) - [:IS_CLASSIFIED] -> (c);
```

**NOTES**:

* String comparisons (also allows NOT)
    * STARTS WITH
    * ENDS WITH
    * CONTAINS
* List comprehensions (and ranges)
* Many python idioms - makes Cypher very expressive

Delete a single classification and all relationships

```
MATCH (c:Classification {id: 'neo'})
DETACH DELETE c
```

### Use case queries

**Assumptions**

* Data loaded is what perspective can see

Count items monitored, classifications

```
MATCH (n)
WHERE n:Directory OR n:File
RETURN COUNT(*) as monitored_count

MATCH (n)
WHERE n:Classification
RETURN COUNT(*) as classification_count
```

Items that are / are not classified

```
// Any type of classification
MATCH (n) - [:IS_CLASSIFIED] -> (:Classification)
WHERE n:File OR n:Directory
RETURN n

// Include the classifications in result
MATCH (n) - [:IS_CLASSIFIED] -> (c:Classification)
WHERE n:File OR n:Directory
RETURN n,c

// Unclassified things - including classification in result for verfication
MATCH (n), (c:Classification)
WHERE 
    (n:File OR n:Directory)
    AND NOT exists ((n) - [:IS_CLASSIFIED] -> ())
RETURN n,c
```

**TODO** ^^^ verify on clean data

Find items with Classification `code`

```
MATCH (n) - [:IS_CLASSIFIED] -> (c:Classification {id: 'code'})
RETURN n,c
```

Find items without Classification `code`

**TODO**
```
MATCH (n), (c:Classification {id: 'code'})
WHERE 
    (n:Directory OR n:File)
    AND NOT exists((n)-[:IS_CLASSIFIED]->(c))
return n

// You can check results with this, verifying 2 python files not present, code class node disconnected
MATCH (n), (all_c:Classification), (c:Classification {id: 'code'})
WHERE 
    (n:Directory OR n:File)
    AND NOT exists((n)-[:IS_CLASSIFIED]->(c))
return n,all_c,c
```

Find decendents of (sub-tree)

```
MATCH (d:Directory {name: '.git'}) - [:PARENT_OF*] -> (n)
RETURN d,n

// Or
MATCH (d:Directory {name: '.git'}) <- [:CHILD_OF*] - (n)
RETURN d,n
```

Find all decendent files (selective sub-tree)

```
MATCH (d:Directory {name: '.git'}) - [:PARENT_OF*] -> (n {owner: 501})
RETURN d,n

// Or
MATCH (d:Directory {name: '.git'}) <- [:CHILD_OF*] - (n {owner: 501})
RETURN d,n
```

Find ancestors of

```
MATCH (n) - [:PARENT_OF*] -> (d:Directory {name: 'hooks'})
RETURN n,d

// Or
MATCH (n) <- [:CHILD_OF*] - (d:Directory {name: 'hooks'})
RETURN n,d
```

**NOTE**: The above prove that we only need a PARENT_OF relationship

## Set operations

1. Identify the root of each sub-tree: id
1. Identify the properties that make nodes "identical": name

The `diff_trees` directory is set up to provide comparisons

* `diff_trees/a`: id = 9666518
* `diff_trees/b`: id = 9666529

Difference

```
MATCH (a:Directory {id: 9666518}) - [:PARENT_OF*] -> (a_child)
MATCH (b:Directory {id: 9666529}) - [:PARENT_OF*] -> (b_child)
WITH collect(DISTINCT b_child.name) as b_names, collect(DISTINCT a_child.name) as a_names
RETURN filter(x IN a_names WHERE not(x in b_names))
```

Intersection

```
```

Union

```
MATCH (d:Directory) - [:PARENT_OF*] -> (child)
WHERE d.id IN [9666518, 9666529]
// Can return all matching properties (exclude timestamps)
RETURN DISTINCT child.name, child.owner
```

Note: separate MATCH statements avoid building a cartesian product

## Misc queries

Return this path and the nodes that match

```
// Returns all dirs that are parent dirs
MATCH  (d:Directory) - [:PARENT_OF] -> (:Directory)
RETURN d

// Returns all dirs that are parent dirs and the child dir under two columns (d, dd)
MATCH  (d:Directory) - [:PARENT_OF] -> (dd:Directory)
RETURN d,dd

// Returns all dirs that are parents of a dir, and the child dir, in a single column 'path'
MATCH  path = (:Directory) - [:PARENT_OF] -> (:Directory)
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



# TODO

* How to keep each customer's data separate?
* hierarchical classifications
* See APOC library for 400 user defined functions


## Versioning graphs

How do we take snapshots of a given point in time?

## Indexes

Create an index on an attribute in a collection

```
CREATE INDEX ON :Directory(name)
```

**NOTES**:

* Creating an index constraint implies a 'pk' index

**TODO** Identify common query patterns and index appropriate fields



## Deployment

* Neo4j has a google cloud launcher [here](https://neo4j.com/developer/neo4j-cloud-google-cloud-launcher/#_deploy_neo4j_enterprise) and a [startup program](https://neo4j.com/startup-program/?ref=developers)



# Db organization

* How should this be organized for customer isolation, etc.
* What is best use of separate databases
* 

# Python drivers

* neo4j-driver (currently recommended on neo4j website)
* py2neo


# Neo4j queries in python


# Ops

Useful commands

* `:sysinfo` - system metrics


