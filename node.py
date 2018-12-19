from datetime import datetime
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple, List, Optional, Dict, Any
import json


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
    
    def colon_args(self) -> str:
        """ Cypher properties with :, delimiters. As used in node prop lists """
        args = [f"{k}: {v}" for k, v in self._asdict_quoted().items()]
        return ", ".join(args)

    def equal_args(self) -> str:
        """ Cypher properties with =, delimiters. As used in ON CREATE SET """
        args = [f"{k} = {v}" for k, v in self._asdict_quoted().items()]
        return ", ".join(args)
    
    def is_dir(self):
        return self.tag.startswith("Dir")
    
    def node(self) -> str:
        """ A completely specified node """
        return f"({self.ref}:{self.tag} {{{self.colon_args()}}})"
    
    def short_node(self) -> str:
        """ A minimally specified node. For MATCH, MERGE """
        return f"({self.ref}:{self.tag} {{id: {self.id}}})"

    def var(self) -> str:
        """ Print self's variable for node generation: (n123)"""
        return f"({self.ref})"

    def _asdict_quoted(self) -> OrderedDict:
        """ _asdict() but strings, dates are quoted """
        # Note: this strategy destroys the OrderedDictness
        #return {k: v if isinstance(v, int) else f"'{v}'" for k, v in self._asdict() if k != 'ref'}
        d = self._asdict()
        del d['ref']
        for k, v in d.items():
            if not isinstance(v, int):
                d[k] = f"'{v}'"
        return d
    
    def __str__(self):
        return self.node()
    
    def __repr__(self):
        # Pretty cool, but Neo4j doesn't like the double quoted property names
        return f"({self.ref}:{self.tag} {json.dumps(self._asdict(), sort_keys=True, default=str)})"


def new_node(p: Path) -> Node:
    stats = p.stat()
    data = {
        "ref": f"n{stats.st_ino}",
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
    return Node(**data)


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
            node = new_node(p)
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
            print(f"MATCH {self.me.short_node()} - [:PARENT_OF] -> {i}")

        # tell child dirs to cypher
        for d in self.dirs:
            d._cypher_recurse()

    def cypher(self) -> None:
        """
        Represent myself and all children as cypher nodes and relationships
        """
        # create self
        print(f"CREATE {self.me}")
        self._cypher_recurse()
