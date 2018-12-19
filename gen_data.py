#!/usr/bin/env python3
"""
I create datasets of TreeNode hierarchies and pickle them for later use

"""
import argparse
import pickle
from pathlib import Path

from node import TreeNode, new_node

# The directory I scan. It has many things pruned for this purpose - hence the pickles, so data is reproducible
ROOT = "/Users/starver/code/public/cpython"
EXCLUDED_DIRS = {}

CASE_STATS = {
    'case_100': {'nodes': 97, 'dirs': 35, 'files': 62},
    'case_200': {'nodes': 205, 'dirs': 35, 'files': 170},
    'case_300': {'nodes': 313, 'dirs': 56, 'files': 257},
    'case_400': {'nodes': 411, 'dirs': 61, 'files': 350},
    'case_500': {'nodes': 512, 'dirs': 45, 'files': 467},
    'case_750': {'nodes': 827, 'dirs': 87, 'files': 740},
    'case_1000': {'nodes': 976, 'dirs': 103, 'files': 873},
    'case_1250': {'nodes': 1274, 'dirs': 83, 'files': 1191},
    'case_1500': {'nodes': 1534, 'dirs': 122, 'files': 1412},
    'case_1750': {'nodes': 1767, 'dirs': 141, 'files': 1626},
    'case_2000': {'nodes': 1973, 'dirs': 149, 'files': 1824},
    'case_2500': {'nodes': 2514, 'dirs': 140, 'files': 2374},
    'case_3000': {'nodes': 2931, 'dirs': 166, 'files': 2765},
    'case_4000': {'nodes': 3957, 'dirs': 216, 'files': 3741},
    'case_5000': {'nodes': 5015, 'dirs': 289, 'files': 4726},
}

# Conditionally exclude directories from target to hit goal node counts
CASE_DIR_EXCLUSIONS = dict(
    case_100={'Doc', 'Include', 'Lib', 'Mac', 'Misc', 'Modules', 'Objects', 'PC', 'PCbuild', 'Parser', 'Python', 'Tools'},
    case_200={'Doc', 'Include', 'Lib', 'Mac', 'Misc', 'Modules', 'Objects', 'PC', 'Parser', 'Python', 'Tools'},
    case_300={'Doc', 'Include', 'Lib', 'Modules', 'NEWS.d', 'Objects', 'PC', 'Parser', 'Python', 'Tools'},
    case_400={'Doc', 'Include', 'Lib', 'Modules', 'NEWS.d', 'Objects', 'Parser', 'Python', 'Tools'},
    case_500={'.git', 'Doc', 'Lib', 'Modules', 'NEWS.d', 'PC', 'PCBuild', 'Python', 'Tools'},
    case_750={'.git', 'Doc', 'Lib', 'Modules', 'NEWS.d', 'PC', 'PCbuild'},
    case_1000={'Doc', 'Lib', 'Modules', 'NEWS.d', 'PC'},
    case_1250={'Lib', 'Modules', 'PC', 'Tools', 'next'},
    case_1500={'Lib', 'Misc', 'Modules', 'PC'},
    case_1750={'Lib', 'Misc', 'PC', '_ctypes', 'clinic', 'libmpdec'},
    case_2000={'Lib', 'NEWS.d', 'PC'},
    case_2500={'Lib', 'Modules'},
    case_3000={'Lib'},
    case_4000={'Include', 'Modules', 'Objects', 'PC', 'Python', 'Tools'},
    case_5000={'PC'},
)


def collect_data_recurse(p: Path, tree_node: TreeNode) -> None:
    """
    Recurse dirs starting at tree_node, collecting information
    
    :param p: Path object for this dir
    :param tree_node: where tree_node.me == p
    """
    for item in p.iterdir():
        child = tree_node.add(item)
        if item.is_dir() and item.name not in EXCLUDED_DIRS:
            collect_data_recurse(item, child)


def collect_data() -> TreeNode:
    """
    Generate hierarchical file data
    """
    root = Path(ROOT)
    result = TreeNode(me=new_node(root), files=[], dirs=[])
    collect_data_recurse(root, result)
    return result


def pickle_datasets() -> None:
    global EXCLUDED_DIRS
    for case, exclusions in CASE_DIR_EXCLUSIONS.items():
        EXCLUDED_DIRS = exclusions
        result = collect_data()
        
        files = 0
        dirs = 0
        for item in result.iter():
            if "Directory" == item.tag:
                dirs += 1
            else:
                files += 1
        print(f"'{case}': {{'nodes': {dirs + files}, 'dirs': {dirs}, 'files': {files}}},")
        
        with open(f"pickles/gd1_{case}.pickle", "wb") as f:
            pickle.dump(collect_data(), f)


def dir_counts_recurse(node: TreeNode, indent: int=0) -> None:
    """
    Print all directories and node counts
    """
    fc = len(node.files)
    dc = len(node.dirs)
    print(f"{dc: >4}  {fc: >4}  {fc + dc: >4}  {' ' * indent}{str(node.me.path)[len(ROOT):]}")
    for d in node.dirs:
        dir_counts_recurse(d, indent + 2)


def dir_counts() -> None:
    """
    Print all directories and node counts
    - create initial state for dir_counts_recurse recursion
    
    This aids in generating datasets with a target size
    """
    root = collect_data()
    print(f"Dirs Files Total  Path")
    dir_counts_recurse(root)


def main():
    parser = argparse.ArgumentParser(description="Generate Neo4j datasets")
    parser.add_argument('-l', action='store_true', default=False, help='list node count for each dir in target dir')
    args = parser.parse_args()
    if args.l:
        dir_counts()
    else:
        pickle_datasets()


if __name__ == "__main__":
    main()
