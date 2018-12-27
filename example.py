#!/usr/bin/env python3
"""
Generate example graphs displaying use cases
"""
import argparse
from argparse import RawDescriptionHelpFormatter
from pprint import pprint, pformat
from typing import Dict, Optional, List

from neo4j import BoltStatementResult

from generator import cypher_file
from trinity import Trinity


def load_case_100() -> None:
    """ Load the 100 node use case - easy to inspect """
    with open(cypher_file('case_100', 'i1'), "r") as f:
        Trinity().clean().run(f.read()).create_constraints()
        

def class_rules():
    """ Examples of different node matching techniques """
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
    # stretching on value - cpython doesn't offer meaningful uses of this
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
            
        query = "MATCH (n) - [:IS_CLASSIFIED] -> (:Classification {id: 'code'}) RETURN n"
        print("===> See graph with: MATCH (n) RETURN n")
        print("===> Fetching all nodes classified 'code' using query:")
        print(f"===>     {query}")
        # This is a BoltStatementResult
        result = session.run(query)
        for item in result.value():
            print(f"{','.join(item.labels)}\t{item['path']}")


def class_pii(show_help: bool=True) -> None:
    """ Define a classification hierarchy for PII and classify files """
    t = Trinity()
    t.clean().create_constraints()
    with t.session() as session:
        with open(cypher_file('pii', 'i1')) as f:
            session.run(f.read())

    # Show classifications as a dict to make the hierarchy clear (instead of cypher statements)
    hier = {
        'pii': {
            'pii_sensitive': {
                'pifi': {
                    'credit_card': {},
                    'bank_account': {},
                },
                'ssn': {},
                'passport': {},
            },
            'pii_non_sensitive': {
                'phone': {},
                'address': {},
            },
        }
    }
    def create_node(name: str) -> str:
        # CREATE (pii:Classification {name: 'pii'})
        return f"CREATE ({name}:Classification {{id: '{name}', name: '{name}'}})"
    def create_rels(parent: str, node: str) -> str:
        # CREATE (pii)  - [:INCLUDES] -> (pii_s) - [:IS_CLASSIFIED] -> (pii)
        return f"CREATE ({parent}) - [:INCLUDES] -> ({node}) - [:IS_CLASSIFIED] -> ({parent})"
    def gen_classes(parent, values: Dict) -> List[str]:
        """
        I get a parent variable name and a dict of children:
        - create classifications for each child
        - create links to the parent
        - recurse on all child value dicts
        :param parent: the key of the dict values - the parent of the keys in values
        :param values: a dict of parent's children and their children
        """
        stmts = []
        for child in values:
            stmts.append(create_node(child))
            stmts.append(create_rels(parent, child))
            stmts.extend(gen_classes(child, values[child]))
        return stmts
    
    classifications = [create_node('pii')]
    classifications.extend(gen_classes('pii', hier['pii']))
    # matches must be done before creates
    stmts = """
    MATCH (f_addr:File) WHERE f_addr.name =~ '.*address.*'
    MATCH (f_cc:File) WHERE f_cc.name =~ 'credit.*card.*'
    MATCH (f_pp:File) WHERE f_pp.name =~ '.*passport.*'
    MATCH (f_phone:File) WHERE f_phone.name =~ '.*phone.*'
    MATCH (f_ssn:File) WHERE f_ssn.name =~ '.*ssn.*'
    """
    # define classifications
    stmts += '\n'.join(classifications)
    # classify the data files
    stmts += """
    MERGE (f_addr) - [:IS_CLASSIFIED] -> (address)
    MERGE (f_cc) - [:IS_CLASSIFIED] -> (credit_card)
    MERGE (f_pp) - [:IS_CLASSIFIED] -> (passport)
    MERGE (f_phone) - [:IS_CLASSIFIED] -> (phone)
    MERGE (f_ssn) - [:IS_CLASSIFIED] -> (ssn)
    """
    with t.session() as session:
        session.run(stmts)

    help = """
    Queries:
    - Classification hierarchy:
        MATCH (c:Classification {id: 'pii'}) - [:INCLUDES*] -> (cc:Classification) RETURN *
    - All PII classifications and their classified files:
        MATCH (n) - [:IS_CLASSIFIED*] -> (c:Classification {id: 'pii'})  RETURN *
    - PII sub-classifications and their classified files
        MATCH (n:File) - [:IS_CLASSIFIED] -> (c:Classification) - [:IS_CLASSIFIED*] -> (:Classification {id: 'pii'})  RETURN n,c
    - Just the classified files:
        MATCH (n:File) - [:IS_CLASSIFIED*] -> (:Classification {name: 'pii'})  RETURN n
    - Classified files and their classifications as attributes
        MATCH (n:File) - [:IS_CLASSIFIED] -> (c:Classification) - [:IS_CLASSIFIED*] -> (:Classification {id: 'pii'})  RETURN c.name, n.path
    """
    if show_help:
        print("    Created this classification hierarchy:")
        print("   ", pformat(hier).replace("\n", "\n    "))
        print(help)


def perspective_pii():
    """ Add a perspective to the class_pii example """
    class_pii()
    perspectives = """
    CREATE (owner:Perspective {id: 'tom', name: 'tom', descr: 'owner'})
    CREATE (group:Perspective {id: 'sales', name: 'sales', descr: 'group'})
    CREATE (other:Perspective {id: 'internet', name: 'internet', descr: 'other'})
    """
    edge = """
    MATCH (p:Perspective)
    WHERE p.descr = '{perm}'
    MATCH (n)
    WHERE (n:File OR n:Directory)
        AND n.{perm}_perm >= {bits}
    MERGE (p) - [:{label}]  -> (n)
    """
    t = Trinity()
    with t.session() as session:
        session.run(perspectives)
        for perm in ['other', 'group', 'owner']:
            session.run(edge.format(perm=perm, label='CAN_READ', bits=4))
            session.run(edge.format(perm=perm, label='CAN_WRITE', bits=6))

    # TODO: standard security queries
    print("""
    Then, created an internet, sales, and tom perspective and drew edges to the things they could read and write.
    You can see the whole graph with:
        MATCH (n) RETURN n
    """)

    
# TODO: classify some data, create a perspecitve tied to what they can read, add_stat on security questions
# TODO: don't think we need the IS_CLASSIFIED edges inside the classification - change this


def help() -> str:
    return """Generate example graphs
    
1  Basic node classification. Includes matching by node id, extension, size, regular expression.
2  A classification hierarchy for PII. Includes classified files and example queries.
3  Using ex 2's structure, add Perspectives and graph their access
"""


def main():
    parser = argparse.ArgumentParser(description=help(), formatter_class=RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--example', type=int, help='which example to generate')
    args = parser.parse_args()
    
    if 1 == args.example:
        class_rules()
    elif 2 == args.example:
        class_pii()
    elif 3 == args.example:
        perspective_pii()


if __name__ == "__main__":
    main()
