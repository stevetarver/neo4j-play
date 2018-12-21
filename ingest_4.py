#!/usr/bin/env python3
"""
Key: Ingest strategy 4: Merge imperfect data

Use case:
Assumes no order to information delivery and incomplete data. E.g. Dropbox returns a batch of json objects describing
individual elements, but not in we don't know the order of statement execution or if we have all information at the
time of create. We create what we know and then update nodes as more data is available.

Strategy:
- using only MERGE stmts, set or update all properties.
- print a newline after each statement to allow ingestion to properly separate runs

Process:
Only process the largest data set
    # Us the single constrained property to match any existing node.
    # Otherwise, we could fail to match [because some properties were not defined earlier] and create a duplicate node
    MERGE (n123:Directory {id: 123})
    # If the node does not exist - set all properties
    ON CREATE SET
        name = '', ...
    # If the node already existed - update all properties to lates values
    ON MATCH SET
        name = '', ...

NOTES:
- Following the Ingest 2 recursion strategy

TODO:
- Can our merge be on one line to avoid having to include spaces
"""
import pickle
import sys
from pathlib import Path

from node import TreeNode, Node


def gen(origin: TreeNode) -> None:
    me = origin.me
    print(f"CREATE {me.node()}")
    # If no parent_id, I am the root node and don't have a PARENT_OF relationship
    if origin.me.parent_id:
        print(f"CREATE (n{me.parent_id}) - [:PARENT_OF] -> ({me.var})")
    for f in origin.files:
        print(f"CREATE {f.node()}")
    for f in origin.files:
        print(f"CREATE ({me.var}) - [:PARENT_OF] -> ({f.var})")
    # Mark the end of a "create group"
    print()
    for d in origin.dirs:
        gen(d)


def gen_cypher(root: TreeNode) -> None:
    """
    I need to create the top level because we cannot modify the named tuple structure - can't
    """
    od = root.me._asdict()
    od['parent_id'] = None
    gen(TreeNode(Node(**od), root.files, root.dirs))


# Include a small dataset so we can verify the graph
pickles = [
    Path('./pickles/case_100.pickle'),
    # Path('./pickles/case_5000.pickle'),
    # Path('./pickles/case_2mil.pickle'),
]

for p in pickles:
    with open(f"{p}", "rb") as infile:
        with open(f"cypher/i4_{p.stem}.cypher", "w") as outfile:
            sys.stdout, tmp = outfile, sys.stdout
            gen_cypher(pickle.load(infile))
            sys.stdout = tmp
            print(f"generated i4_{p.stem}.cypher")
