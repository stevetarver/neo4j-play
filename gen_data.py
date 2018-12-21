#!/usr/bin/env python3
"""
I create datasets of TreeNode hierarchies and pickle them for later use

"""
import argparse
import pickle
from pathlib import Path
from typing import Optional

from node import Node, TreeNode, new_node

# The directory I scan. It has many things pruned for this purpose - hence the pickles, so data is reproducible
ROOT = "/Users/starver/code/public/cpython"
EXCLUDED_DIRS = {'appomni'} # for home dir large dataset

CASE_INFO = {
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


def _get_filename(kind: str, case: str, ingest_key: Optional[str] = None) -> str:
    if case not in CASE_INFO:
        raise ValueError(f"Unknown case: {case}")
    if "pickle" == kind:
        fn = f"./pickles/{case}.pickle"
    elif "cypher" == kind:
        fn = f"./cypher/{ingest_key}_{case}.cypher"
    else:
        raise ValueError(f"Unknown file kind: {kind}")
    if not Path(fn).exists():
        raise ValueError(f"Pickle does not exist: {fn}")
    return fn


def pickle_file(case: str) -> str:
    """
    Generate a path to a valid pickle file
    :param case: a use case - a key from CASE_INFO
    :return: a cypher file name
    """
    return _get_filename("pickle", case)


def cypher_file(case: str, ingest_key: str) -> str:
    """
    Generate a path to a valid cypher file
    :param ingest_key: an ingest key, like i1, i2, i3
    :param case: a use case - a key from CASE_INFO
    :return: a cypher file name
    """
    return _get_filename("cypher", case, ingest_key)


# my home dir stats - not included in repo for privacy and size
# ./gen_data.py -r /Users/starver -n case_2mil
# 'case_2mil': {'nodes': 1912541, 'dirs': 538632, 'files': 1373909},

# Conditionally exclude directories from target to hit goal node counts
CASE_DIR_EXCLUSIONS = dict(
    case_100={'Doc', 'Include', 'Lib', 'Mac', 'Misc', 'Modules', 'Objects', 'PC', 'PCbuild', 'Parser', 'Python',
              'Tools'},
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
    """ Recurse dirs starting at tree_node, collecting information """
    for item in p.iterdir():
        child = tree_node.add(item)
        if item.is_dir() and item.name not in EXCLUDED_DIRS:
            collect_data_recurse(item, child)


def collect_data(p: Path) -> TreeNode:
    """ Generate hierarchical file data """
    result = TreeNode(me=new_node(p), files=[], dirs=[])
    collect_data_recurse(p, result)
    return result


def print_stats(root: TreeNode, case: str) -> None:
    """ Print case stats for CASE_INFO - for validating graph creation """
    files = 0
    dirs = 0
    for item in root.iter():
        if item.is_dir():
            dirs += 1
        else:
            files += 1
    print(f"'{case}': {{'nodes': {dirs + files}, 'dirs': {dirs}, 'files': {files}}},")


def remove_root_parent(root: TreeNode) -> TreeNode:
    # Ensure our root node does not have a parent id - to identify it as root
    od = root.me._asdict()
    od['parent_id'] = None
    return TreeNode(Node(**od), root.files, root.dirs)


def pickle_dataset(p: Path, case: str) -> None:
    root = collect_data(p)
    print_stats(root, case)  # so you can add to CASE_INFO
    with open(pickle_file(case), "wb") as f:
        pickle.dump(remove_root_parent(root), f)


def pickle_default_datasets(p: Path) -> None:
    global EXCLUDED_DIRS
    for case, exclusions in CASE_DIR_EXCLUSIONS.items():
        EXCLUDED_DIRS = exclusions
        pickle_dataset(p, case)


def dir_counts_recurse(node: TreeNode, indent: int = 0) -> None:
    """ Print all directories and node counts """
    fc = len(node.files)
    dc = len(node.dirs)
    descendants = 0
    for item in node.iter():
        descendants += 1
    print(f"{dc: >4}  {fc: >4}  {descendants: >4}  {' ' * indent}/{node.me.name}")
    for d in node.dirs:
        dir_counts_recurse(d, indent + 2)


def dir_counts(p: Path) -> None:
    """
    Print all directories and node counts
    - create initial state for dir_counts_recurse recursion
    
    This aids in generating datasets with a target size
    """
    root = collect_data(p)
    print("  Dirs       : directories in current directory")
    print("  Files      : files in current directory")
    print("  Descendants: count of all descendants from current directory")
    print(f"Dirs Files Descendants Path")
    dir_counts_recurse(root)


def main():
    parser = argparse.ArgumentParser(description="Collect dir/file metadata and pickle")
    parser.add_argument('-r', '--root',
                        default="/Users/starver/code/public/cpython",
                        help='root directory - where to start parsing')
    parser.add_argument('-n', '--name',
                        default="funky-karmikel",
                        help='pickle file name')
    parser.add_argument('-d', '--default',
                        action='store_true',
                        default=False,
                        help='generate default datasets (using default dir)')
    parser.add_argument('-l', '--list',
                        action='store_true',
                        default=False,
                        help='list node count for each dir in target dir')
    args = parser.parse_args()
    
    if args.default:
        print("===> Generating default datasets")
        pickle_default_datasets(Path(ROOT))
        exit(0)
    
    p = Path(args.root)
    if not p.exists():
        print(f"Directory {p} does not exist. Cannot continue.")
        exit(1)
    if not p.is_dir():
        print(f"{p} is not a directory, cannot continue.")
        exit(1)
    
    if args.list:
        dir_counts(p)
    elif args.root:
        print(f"===> Collecting {p} into a {args.name} pickle")
        pickle_dataset(p, args.name)


if __name__ == "__main__":
    main()
