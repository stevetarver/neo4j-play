from pathlib import Path
from typing import NamedTuple, List, Optional, Dict, Any
import json


class Node(NamedTuple):
    """
    Common ways to reference self and parts
    n123                            var - uniquely identifies this node, used in most other constructs
    (n123)                          ref - once a node is created/merged/matched, use this
    (n123:Directory)                ??? - not sure we ever need this
    (n123:Directory {id: 123})      node_ref - match with this (sometimes merge)
    (n123:Directory {id: 123, ...}) node - create node syntax
    """
    name: str
    tag: str
    id: int
    parent_id: Optional[int] # None for root node
    stem: str
    extension: str
    path: str
    size: int
    owner: int
    group: int
    created: int
    accessed: int
    modified: int
    
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
        return f"({self.var}:{self.tag} {{{self.colon_args()}}})"
    
    @property
    def ref(self) -> str:
        """ The node ref used when constructing relationships """
        return f"({self.var})"
    
    def node_ref(self) -> str:
        """ A minimally specified node. For MATCH, MERGE """
        return f"({self.var}:{self.tag} {{id: {self.id}}})"

    @property
    def var(self):
        """ The node variable name I am normally created with """
        return f"n{self.id}"

    def _asdict_quoted(self) -> Dict:
        """ _asdict() but strings, dates are quoted """
        # Note: this strategy destroys the OrderedDictness
        return {k: v if isinstance(v, int) else f"'{v}'" for k, v in self._asdict().items()}
        # d = self._asdict()
        # for k, v in d.items():
        #     if not isinstance(v, int):
        #         d[k] = f"'{v}'"
        # return d
    
    def __str__(self):
        return self.node()
    
    def __repr__(self):
        # Pretty cool, but Neo4j doesn't like the double quoted property names
        return f"({self.var}:{self.tag} {json.dumps(self._asdict(), sort_keys=True, default=str)})"


def new_node(p: Path) -> Node:
    stats = p.stat()
    data = {
        "tag": "Directory" if p.is_dir() else "File",
        "id": stats.st_ino,
        "parent_id": p.parent.stat().st_ino if p.parent else None,
        "name": p.name,
        "stem": p.stem,
        "extension": p.suffix[1:],  # omit the leading dot
        "path": p.absolute(),
        "size": stats.st_size,
        "created": int(stats.st_ctime),
        "accessed": int(stats.st_atime),
        "modified": int(stats.st_mtime),
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
