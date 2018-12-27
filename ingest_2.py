#!/usr/bin/env python3
"""
Key: Ingest strategy 2: Create groups

Strategy:
- using only create stmts, create separable groups to fit within optimal batch size (~1000 nodes)

Process:
Only process the largest data set
- for each dir:
    create self
    create parent link (if parent_id - root should not have one)
    create file nodes
    create file parent links (to current dir)
    print newline - we can safely break at any one of these
    for each dir, recurse

NOTES:
- CREATEs are the most efficient because you don't have to first check if the node/edge exists (avoid lookup cost)

TODO:
- turns out we could break cypher file at any point - remove the spaces and change trinity
"""
import pickle
import sys
from timeit import default_timer as timer

from generator import cypher_file, pickle_file
from node import TreeNode


def gen(origin: TreeNode) -> None:
    """
    TODO: What is a node variable lifetime?
          In our naive use, a session.run() is an autocommit
          Node reference variable lifetime is longer than run(), session, and ';'
    """
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
    # TODO: this is not needed because of lifetime of variables
    # print()
    for d in origin.dirs:
        gen(d)


def gen_cypher(root: TreeNode) -> None:
    gen(root)


# Include a small dataset so we can verify the graph
cases = [
    "case_100",
    "case_5000",
    "case_2mil",
]
for c in cases:
    with open(pickle_file(c), "rb") as infile:
        with open(cypher_file(c, "i2", False), "w") as outfile:
            sys.stdout, tmp = outfile, sys.stdout
            start = timer()
            gen_cypher(pickle.load(infile))
            end = timer()
            sys.stdout = tmp
            print(f"generated i2_{c}.cypher in {end - start:.2f} seconds")

