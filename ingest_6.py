#!/usr/bin/env python3
"""
Key: Ingest strategy 6: LOAD CSV cypher script

Use case:
Does LOAD FROM CSV offer benefits over straight cypher statements?

NOTES:
- Need to mount the /var/lib/neo4j/import dir from the docker container and put csv's there
- Doc says: Use LOAD CSV for small to medium datasets - up to 10 million rows
- TODO: can we create disposable databases?
- neo4j-admin import essentially allows you to build an offline database. As Michael said, we’re skipping the
  transactional layer and building the actual store files of the database.
  Potentially, we could build the data store and move it into the database
  This means a distinct approach from LOAD CSV - but we could do it on any machine with neo4j-admin

CAVEATS:
- we cannot include type information in the csv for this strategy - header row is for names only

TODO:
    - provide an example CSV file
    - provide an example CSV file compressed
    - we can also load from json - directly from an api???
"""
import csv
import pickle
from pathlib import Path

from generator import pickle_file, cypher_file
from node import Node, TreeNode

# noinspection SqlNoDataSourceInspection
# TODO: Something between 10,000 and 100,000 updates per transaction are a good target.
# TODO: add constraints to file to improve relationship creation
# TODO: can I set variables during load to avoid having to index and lookup. Will that work with millions of nodes?
NODE_FIELDS = []
for k,v in Node._field_types.items():
    if v == str:
        NODE_FIELDS.append(f"    {k}: row.{k}")
    else:
        NODE_FIELDS.append(f"    {k}: toInteger(row.{k})")
NODE_FIELDS = ",\n".join(NODE_FIELDS)

CYPHER = f'''
// NOTE: Someone should have established constraints
USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:///i6_~CASE~_dir.csv" as row

CREATE (d:Directory {{
{NODE_FIELDS}
}})

// Avoid NULL error for root node
FOREACH (pid IN (CASE row.parent_id WHEN NULL THEN [] ELSE [1] END) |
  MERGE (p:Directory {{id: toInteger(row.parent_id)}})
  MERGE (p)-[:PARENT_OF]->(d)
);

USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:///i6_~CASE~_file.csv" as row

CREATE (f:File {{
{NODE_FIELDS}
}})

MERGE (p:Directory {{id: toInteger(row.parent_id)}})
MERGE (p) - [:PARENT_OF] -> (f);
'''


def gen_csv(root: TreeNode, case: str) -> None:
    # Must have separate files for each node type (label)
    dir = f"./neo4j/import/i6_{case}_dir.csv"
    file = f"./neo4j/import/i6_{case}_file.csv"
    with open(dir, "w") as d:
        with open(file, "w") as f:
            d.write(f"{','.join(Node._fields)}\n")
            f.write(f"{','.join(Node._fields)}\n")

            d_writer = csv.DictWriter(d, Node._fields)
            f_writer = csv.DictWriter(f, Node._fields)
            for item in root.iter():
                if item.is_dir():
                    d_writer.writerow(item._asdict())
                else:
                    f_writer.writerow(item._asdict())
    
    
def gen_cypher(case: str) -> None:
    with open(cypher_file(case, "i6", False), "w") as f:
        f.write(CYPHER.replace("~CASE~", case))
    

cases = [
    'case_100',
    'case_5000',
]
for c in cases:
    with open(pickle_file(c), "rb") as infile:
        root = pickle.load(infile)
        gen_csv(root, c)
        gen_cypher(c)

