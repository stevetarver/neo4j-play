#!/usr/bin/env python3
"""
Generate example graphs displaying use cases
"""
import argparse
from argparse import RawDescriptionHelpFormatter

from neo4j import BoltStatementResult

from generator import cypher_file
from trinity import Trinity


def load_case_100() -> None:
    """ Load the 100 node use case - easy to inspect """
    with open(cypher_file('case_100', 'i1'), "r") as f:
        Trinity().clean().run(f.read()).create_constraints()
        

def classification_1():
    load_case_100()
    code = """
        MERGE (c:Classification {id: 'code', name: 'code', rule: 'extension IN [c, py, sh]'})
        WITH c
        MATCH (f:File)
        WHERE f.extension IN ['c', 'py', 'sh']
        MERGE (f) - [:IS_CLASSIFIED] -> (c);"""
    id = """
        MERGE (c:Classification {id: 'id', name: 'id', rule: 'id IN [9775512, 9775213]'})
        WITH c
        MATCH (n)
        WHERE n.id IN [9775512, 9775213]
        MERGE (n) - [:IS_CLASSIFIED] -> (c);"""
    size = """
        MERGE (c:Classification {id: 'big', name: 'big', rule: 'size > 5000'})
        WITH c
        MATCH (f:File)
        WHERE f.size > 5000
        MERGE (f) - [:IS_CLASSIFIED] -> (c);"""
    # stretching on utility - cpython doesn't offer meaningful uses of this
    # Note: we could use this for subtree identification on the path attribute
    regex = """
        MERGE (c:Classification {id: 'py', name: 'py', rule: 'n.stem =~ .*[Pp]y.*'})
        WITH c
        MATCH (n)
        WHERE n.stem =~ '.*[Pp]y.*' AND (n:Directory OR n:File)
        MERGE (n) - [:IS_CLASSIFIED] -> (c);"""

    # TODO: can't use: with Trinity().session as session:
    #       cause: neobolt.exceptions.ServiceUnavailable: Connection pool closed
    t = Trinity()
    with t.session() as session:
        for stmt in [code, id, size, regex]:
            session.run(stmt)
            
        print("===> All nodes classified 'code'")
        query = """
            MATCH (n) - [:IS_CLASSIFIED] -> (:Classification {id: 'code'})
            RETURN n
        """
        # This is a BoltStatementResult
        result = session.run(query)
        for item in result.value():
            print(item)
        

# TODO: classify some data, create a perspecitve tied to what they can read, report on security questions


def help() -> str:
    return """Generate example graphs
    
1  Basic node classification. Includes matching by node id, extension, size, regular expression
"""


def main():
    parser = argparse.ArgumentParser(description=help(), formatter_class=RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--example', type=int, help='which example to generate')
    args = parser.parse_args()
    
    if 1 == args.example:
        classification_1()


if __name__ == "__main__":
    main()
