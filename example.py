#!/usr/bin/env python3
"""
Generate example graphs displaying use cases
"""
import argparse
from argparse import RawDescriptionHelpFormatter
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
            
        print("===> All nodes classified 'code'")
        query = """
            MATCH (n) - [:IS_CLASSIFIED] -> (:Classification {id: 'code'})
            RETURN n
        """
        # This is a BoltStatementResult
        result = session.run(query)
        for item in result.value():
            print(item)


def class_pii() -> None:
    """ Define a classification hierarchy for PII and classify files """
    t = Trinity()
    t.clean().create_constraints()
    with t.session() as session:
        with open("./cypher/i1_pii.cypher") as f:
            session.run(f.read())

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
    # CREATE (pii:Classification {name: 'pii'})
    create = "CREATE ({}:Classification {{name: '{}'}})"
    # CREATE (pii)  - [:INCLUDES] -> (pii_s) - [:IS_CLASSIFIED] -> (pii)
    rel = "CREATE ({})  - [:INCLUDES] -> ({}) - [:IS_CLASSIFIED] -> ({})"
    def gen_classes(values: Dict) -> List[str]:
        stmts = []
        for parent,children in values.items():
            stmts.append(create.format(parent, parent))
            for grandchild in children:
                stmts.append(create.format(grandchild, grandchild))
                stmts.append(rel.format(parent, grandchild, parent))
            stmts.extend(gen_classes(children))
        return stmts
    with t.session() as session:
        session.run("\n".join(gen_classes(hier)))

    # classes = ['pii', 'pii_sensitive', 'pifi', 'ssn', 'passport', 'credit_card', 'bank_account', 'pii_non_sensitive', 'phone', 'address']
    # with t.session() as session:
    #     for c in classes:
    #         session.run(f"CREATE (pii_s:Classification {{name: '{c}'}})")

    # classes = """
    # // matches must be done before creates
    # MATCH (f_addr:File) WHERE f_addr.name =~ '.*address.*'
    # MATCH (f_cc:File) WHERE f_cc.name =~ 'credit.*card.*'
    # MATCH (f_pp:File) WHERE f_pp.name =~ '.*passport.*'
    # MATCH (f_phone:File) WHERE f_phone.name =~ '.*phone.*'
    # MATCH (f_ssn:File) WHERE f_ssn.name =~ '.*ssn.*'
    #
    # CREATE (pii:Classification {name: 'pii'})
    #
    # // could result in harm to the individual whose privacy has been breached
    # CREATE (pii_s:Classification {name: 'pii_sensitive'})
    # CREATE (pii)  - [:INCLUDES] -> (pii_s) - [:IS_CLASSIFIED] -> (pii)
    #
    # CREATE (pifi:Classification {name: 'pifi'})
    # CREATE (pii_s)  - [:INCLUDES] -> (pifi) - [:IS_CLASSIFIED] -> (pii_s)
    #
    # CREATE (ssn:Classification {name: 'ssn'})
    # CREATE (pii_s)  - [:INCLUDES] -> (ssn) - [:IS_CLASSIFIED] -> (pii_s)
    #
    # CREATE (passport:Classification {name: 'passport'})
    # CREATE (pii_s)  - [:INCLUDES] -> (passport) - [:IS_CLASSIFIED] -> (pii_s)
    #
    # CREATE (cc:Classification {name: 'credit_card'})
    # CREATE (pifi)  - [:INCLUDES] -> (cc) - [:IS_CLASSIFIED] -> (pifi)
    #
    # CREATE (ba:Classification {name: 'bank_account'})
    # CREATE (pifi)  - [:INCLUDES] -> (ba) - [:IS_CLASSIFIED] -> (pifi)
    #
    # // public records, phone books, corporate directories and websites
    # CREATE (pii_ns:Classification {name: 'pii_non_sensitive'})
    # CREATE (pii) - [:INCLUDES] -> (pii_ns) - [:IS_CLASSIFIED] -> (pii)
    #
    # CREATE (phone:Classification {name: 'phone'})
    # CREATE (pii_ns)  - [:INCLUDES] -> (phone) - [:IS_CLASSIFIED] -> (pii_ns)
    #
    # CREATE (address:Classification {name: 'address'})
    # CREATE (pii_ns)  - [:INCLUDES] -> (address) - [:IS_CLASSIFIED] -> (pii_ns)
    #
    # // classify the data files
    # CREATE (f_addr) - [:IS_CLASSIFIED] -> (address)
    # CREATE (f_cc) - [:IS_CLASSIFIED] -> (cc)
    # CREATE (f_pp) - [:IS_CLASSIFIED] -> (passport)
    # CREATE (f_phone) - [:IS_CLASSIFIED] -> (phone)
    # CREATE (f_ssn) - [:IS_CLASSIFIED] -> (ssn)
    # """
    # with t.session() as session:
    #     session.run(classes)

    print("""
    Queries:
    - Classification hierarchy:
        MATCH (c:Classification {name: 'pii'}) - [:INCLUDES*] -> (cc:Classification) RETURN *
    - All PII classifications and classified files:
        MATCH (n) - [:IS_CLASSIFIED*] -> (c:Classification {name: 'pii'})  RETURN n
    - PII sub-classifications and classified files
        MATCH (n:File) - [:IS_CLASSIFIED] -> (c:Classification) - [:IS_CLASSIFIED*] -> (:Classification {name: 'pii'})  RETURN n,c
    - Just the classified files:
        MATCH (n:File) - [:IS_CLASSIFIED*] -> (:Classification {name: 'pii'})  RETURN n
    - Classified files and their classifications as attributes
        MATCH (n:File) - [:IS_CLASSIFIED] -> (c:Classification) - [:IS_CLASSIFIED*] -> (:Classification {name: 'pii'})  RETURN c.name, n.path
    """)


# TODO: classify some data, create a perspecitve tied to what they can read, report on security questions


def help() -> str:
    return """Generate example graphs
    
1  Basic node classification. Includes matching by node id, extension, size, regular expression.
2  A classification hierarchy for PII. Includes classified files and example queries.
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


if __name__ == "__main__":
    main()
