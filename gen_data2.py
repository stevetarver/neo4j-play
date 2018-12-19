#!/usr/bin/env python3
"""
Create a dataset for neo4j

1. Setup a process that can scale to many items to test performance
2. Establish data format - experiment with different load techniques: cypher, etl
3. Define the data that will be collected and output format

This should be the optimal theoretical implementation

"""
from _datetime import datetime
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple, Dict, Any, Union, List, Optional
from pprint import pprint, pformat
import json
from random import randint

# Change the printed output to include brief info for debugging dir recursion
DEBUG_DIRS_PROCESSING = False
EXCLUDED_DIRS = {'neo4j_docker_volume'}
ROOT = "/Users/starver/code/appomni/neo4j-play"


# ROOT = "/Users/starver"


class Node(NamedTuple):
    id: int
    name: str
    stem: str
    extension: str
    path: str
    parent: str
    size: int
    owner: int
    group: int
    created: datetime
    accessed: datetime
    modified: datetime
    tag: str
    ref: str  # a unique reference used when creating cypher statements
    
    def args(self) -> str:
        """ Cypher fields as used in ON CREATE SET """
        args = [f"{k} = {v}" for k, v in self._quoted_as_dict().items()]
        return ", ".join(args)
    
    def node(self) -> str:
        """ A cypher fully specified node """
        args = ', '.join([f'{k}: {v}' for k, v in self._quoted_as_dict().items()])
        return f"({self.ref}:{self.tag} {{{args}}})"
    
    def short_node(self) -> str:
        """ Uniquely identifies a node, for MATCH and relationships"""
        return f"({self.ref}:{self.tag} {{id: {self.id}}})"
    
    def var(self) -> str:
        """ Print self's variable for node generation: (n123)"""
        return f"({self.ref})"
    
    def _quoted_as_dict(self) -> OrderedDict:
        d = self._asdict()
        del d['ref']
        for k, v in d.items():
            if not isinstance(v, int):
                d[k] = f"'{v}'"
        return d
    
    def __str__(self):
        if DEBUG_DIRS_PROCESSING:
            # return f"(:{self.tag} {{path: '{self.path}'}})"
            return f"{self.tag[:3]} {self.path}"
        else:
            args = []
            for f in self._fields:
                value = getattr(self, f)
                if not isinstance(value, int):
                    value = f"'{value}'"
                args.append(f"{f}: {value}")
            return f"({self.ref}:{self.tag} {{{', '.join(args)}}})"
    
    def __repr__(self):
        # Pretty cool, but Neo4j doesn't like the double quoted property names
        return f"({self.ref}:{self.tag} {json.dumps(self._asdict(), sort_keys=True, default=str)})"


class TreeNode(NamedTuple):
    me: Node
    files: List[Node]
    dirs: List["TreeNode"]
    
    def add(self, p: Path) -> Optional["TreeNode"]:
        """
        Add an item to the proper collection in this node
        :param p: Path object to add
        :return: a TreeNode object if one was created (to hold a Dir Node)
        """
        node = None
        try:
            node = Node(**get_info(p))
        except:
            pass
        if node:
            if p.is_dir():
                self.dirs.append(TreeNode(me=node, files=[], dirs=[]))
                return self.dirs[-1]
            else:
                self.files.append(node)
    
    def iter(self):
        """
        A recursive generator - producing nodes (stripping out the TreeNode part)
        Recursing a TreeNode structure can be tedious - capture that logic here
        """
        yield self.me
        for d in self.dirs:
            yield from d.iter()
        for f in self.files:
            yield f
    
    def print(self, indent=0) -> None:
        print(f"{' ' * indent}{self.me}")
        for d in self.dirs:
            d.print(indent + 2)  # recurse subtree
        for f in self.files:
            print(f"{' ' * (indent + 2)}{f}")
    
    def _cypher_recurse(self) -> None:
        """
        The protected method is the part that actually recurses
        """
        # create children
        for i in self.files + [x.me for x in self.dirs]:
            print(f"MERGE {self.me.var()} - [:PARENT_OF] -> {i}")

        # tell child dirs to cypher
        for d in self.dirs:
            d._cypher_recurse()

    def cypher(self) -> None:
        """
        Represent myself and all children as cypher nodes and relationships
        """
        # create self
        print(f"MERGE {self.me}")
        self._cypher_recurse()


def ref():
    """ Return a new, unique int for each call """
    ref.counter += 1
    return f"n{ref.counter}"


# initialize the ref counter
ref.counter = 0


def get_info(p: Path) -> Dict[str, Any]:
    stats = p.resolve().stat()
    return {
        "ref": ref(),
        "tag": "Directory" if p.is_dir() else "File",
        "id": stats.st_ino,
        "name": p.name,
        "stem": p.stem,
        "extension": p.suffix[1:],  # omit the leading dot
        "path": p.absolute(),
        "parent": p.parent,
        "size": stats.st_size,
        "created": datetime.fromtimestamp(stats.st_ctime),
        "accessed": datetime.fromtimestamp(stats.st_atime),
        "modified": datetime.fromtimestamp(stats.st_mtime),
        "owner": stats.st_uid,
        "group": stats.st_gid,
    }


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


def constraints():
    """
    TODO: when we have enterprise version, need to add Property existence constraints to ensure some properties always exist
    :return:
    """
    constraint = "CREATE CONSTRAINT ON ({var}:{label}) ASSERT {var}.id IS UNIQUE;"
    data = {
        'd': 'Directory',
        'f': 'File',
        'c': 'Classification',
    }
    return "\n".join([constraint.format(var=k, label=v) for k, v in data.items()])


def gen_data():
    """
    Generate hierarchical file data
    """
    root = Path(ROOT)
    result = TreeNode(me=Node(**get_info(root)), files=[], dirs=[])
    
    process_dir(root, result)
    result.cypher()


gen_data()
