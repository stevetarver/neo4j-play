#!/usr/bin/env python3
"""
Key: Ingest strategy 4: Merge imperfect data

Use case:
Assumes no order to information delivery and incomplete data. E.g. Dropbox returns a batch of json objects describing
individual elements, but not in we don't know the order of statement execution or if we have all information at the
time of create. We create what we know and then update nodes as more data is available.

Strategy:
- using only MERGE stmts, set or update all properties
- use globally unique node vars to avoid: Variable `n9768633` already declared
- because of var scope, we should be able to break the file anywhere and still have all vars defined

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

"""
import pickle
import sys
from pathlib import Path
from random import randint

from generator import pickle_file
from node import TreeNode, Node, RandomNode


def rand_ref():
    return f"n{randint(0, 999_999_999)}"


def gen(origin: TreeNode) -> None:
    # Note: single line is hard to read, but easy to break into chunks
    me = RandomNode(**origin.me._asdict())
    print(f"MERGE {me.node_ref()} ON CREATE SET {me.equal_args()} ON MATCH SET {me.equal_args()}")

    # If no parent_id, I am the root node and don't have a PARENT_OF relationship
    if origin.me.parent_id:
        # need two MERGEs here - entire pattern must match existing or all are created
        parent_ref = rand_ref()
        print(f"MERGE ({parent_ref}:Directory {{id: {me.parent_id}}})")
        print(f"MERGE ({parent_ref}) - [:PARENT_OF] -> {me.ref}")
    for f in origin.files:
        rf = RandomNode(**f._asdict())
        print(f"MERGE {rf.node_ref()} ON CREATE SET {rf.equal_args()} ON MATCH SET {rf.equal_args()}")
        print(f"MERGE {me.ref} - [:PARENT_OF] -> {rf.ref}")

    for d in origin.dirs:
        gen(d)


def gen_cypher(root: TreeNode) -> None:
    """
    I need to create the top level because we cannot modify the named tuple structure - can't
    """
    gen(root)


# Include a small dataset so we can verify the graph
pickles = [
    Path(pickle_file('case_100')),
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

