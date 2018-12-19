#!/usr/bin/env python3
"""
I create datasets of TreeNode hierarchies and pickle them for later use

"""
import pickle
from pathlib import Path

from node import Node, TreeNode, new_node

# The directory I scan. It has many things pruned for this purpose - hence the pickles, so data is reproducible
ROOT = "/Users/starver/code/appomni/appomni"

CASE_STATS = {
    'case_1': {'nodes': 90, 'dirs': 24, 'files': 66},
    'case_2': {'nodes': 136, 'dirs': 27, 'files': 109},
    'case_3': {'nodes': 507, 'dirs': 182, 'files': 325},
    'case_4': {'nodes': 530, 'dirs': 204, 'files': 326},
    'case_5': {'nodes': 697, 'dirs': 256, 'files': 441},
    'case_6': {'nodes': 1232, 'dirs': 256, 'files': 976},
    'case_7': {'nodes': 1604, 'dirs': 286, 'files': 1318},
    'case_8': {'nodes': 2081, 'dirs': 311, 'files': 1770},
    'case_9': {'nodes': 2619, 'dirs': 525, 'files': 2094},
    'case_10': {'nodes': 3067, 'dirs': 529, 'files': 2538},
    'case_11': {'nodes': 3687, 'dirs': 529, 'files': 3158},
    'case_12': {'nodes': 4090, 'dirs': 529, 'files': 3561},
    'case_13': {'nodes': 4508, 'dirs': 529, 'files': 3979},
    'case_14': {'nodes': 5008, 'dirs': 529, 'files': 4479},
}

CASE_DIR_EXCLUSIONS = dict(
    case_1={'.git', 'web', 'scripts'},
    case_2={'.git', 'web', 'by_ip'},
    case_3={'.git', 'core', 'by_ip'},
    case_4={'.git', 'sfdc', 'by_ip'},
    case_5={'.git', 'by_ip'},
    case_6={'.git'},
    case_7={'objects'},  # .git/objects
    case_8={'web', 'logs', 'by_ip'} | {f"{hex(x)}"[2:] for x in range(200)},  # .git/objects/**
    case_9={'logs', 'by_ip'} | {f"{hex(x)}"[2:] for x in range(200)},
    case_10={'by_ip'} | {f"{hex(x)}"[2:] for x in range(185)},
    case_11={'by_ip'} | {f"{hex(x)}"[2:] for x in range(155)},
    case_12={'by_ip'} | {f"{hex(x)}"[2:] for x in range(135)},
    case_13={'by_ip'} | {f"{hex(x)}"[2:] for x in range(115)},
    case_14={'by_ip'} | {f"{hex(x)}"[2:] for x in range(90)},
)


def process_dir(p: Path, tree_node: TreeNode) -> None:
    """
    Traverse a directory, building a TreeNode hierarchy.
    Caller should have already set tree_node.me = p, I just process children
    
    :param p: Path object for this dir
    :param tree_node: where tree_node.me == p
    :return:
    """
    for item in p.iterdir():
        child = tree_node.add(item)
        if item.is_dir() and item.name not in EXCLUDED_DIRS:
            process_dir(item, child)


def gen_data() -> TreeNode:
    """
    Generate hierarchical file data
    """
    root = Path(ROOT)
    result = TreeNode(me=new_node(root), files=[], dirs=[])
    
    process_dir(root, result)
    return result


if __name__ == "__main__":
    for case, exclusions in CASE_DIR_EXCLUSIONS.items():
        EXCLUDED_DIRS = exclusions
        result = gen_data()
        
        files = 0
        dirs = 0
        for item in result.iter():
            if "Directory" == item.tag:
                dirs += 1
            else:
                files += 1
        print(f"'{case}': {{'nodes': {dirs + files}, 'dirs': {dirs}, 'files': {files}}},")
        
        with open(f"pickles/gd1_{case}.pickle", "wb") as f:
            pickle.dump(gen_data(), f)
