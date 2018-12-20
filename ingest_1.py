#!/usr/bin/env python3
"""
Key: Ingest strategy 1: One create group

Strategy:
- one file has all node, edge CREATE stmts, one run()

Process:
Process each dataset to find the optimal number of nodes per file, and the filesize limit
pass 1
    for each dir
    - create all child nodes with ref var
    - recurse for each dir
pass 2
    for each dir
    - create parent edge to self for each child
    - recurse for each dir
    
NOTES:
- very easy to reason about
- max # of stmts in a file heavily dependent on server RAM config
"""
import pickle
import sys
from pathlib import Path

from node import TreeNode


def gen_nodes(origin: TreeNode) -> None:
    """ Traverse tree, only creating nodes """
    for f in origin.files:
        print(f"CREATE {f.node()}")
    for d in origin.dirs:
        print(f"CREATE {d.me.node()}")
    for d in origin.dirs:
        gen_nodes(d)


def gen_edges(origin: TreeNode) -> None:
    """ Traverse tree, only creating edges """
    me = origin.me
    for i in origin.files + [x.me for x in origin.dirs]:
        print(f"CREATE ({me.ref}) - [:PARENT_OF] -> ({i.ref})")
    for d in origin.dirs:
        gen_edges(d)


def gen_cypher(origin: TreeNode) -> None:
    print(f"CREATE {origin.me.node()}")
    gen_nodes(origin)
    gen_edges(origin)


for p in sorted(Path('./pickles').iterdir()):
    with open(f"{p}", "rb") as infile:
        with open(f"cypher/i1_{p.stem}.cypher", "w") as outfile:
            sys.stdout, tmp = outfile, sys.stdout
            gen_cypher(pickle.load(infile))
            sys.stdout = tmp
            print(f"generated {p.stem}")

