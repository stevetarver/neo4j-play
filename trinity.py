#!/usr/bin/env python3
"""
Trinity talks to Neo... A LOT

Questions
- What is the fastest way to ingest n nodes, relationships?
- Does that vary by collection size?

Python driver choices:
 See https://neo4j.com/developer/python/#_neo4j_community_drivers

What driver should we use?
- should use bolt - binary protocols are always faster

Learnings:
- a statement is terminated by a ';' - there can be only one per run()
- many clauses can be in a single statement (CREATE, MERGE, etc)
- we jam as many clauses into a statement cause each run() has an auto commit - slow if we don't
- a merge either matches everything, or tries to create everything in the pattern.
- WITH rescopes variables groups some collections - probably no use in ingestion because we
  have many clauses it would affect
"""
from timeit import default_timer as timer
from timeit import timeit

from neo4j import GraphDatabase, basic_auth

from constraints import Constraint
from gen_data import CASE_STATS

# class Trinity:
#     """
#     Trinity encapsulates Neo connection details and simplifies communication
#     As written, this class is intended to be short lived - cause sessions should be short lived.
#
#     NOTE: we don't have to close the driver or session - the base classes override __del__() to do that.
#
#     We could also have a long lived driver class that used sessions in a short-lived fashion
#     """
#     def __init__(self):
#         self._driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "Admin1234!"))
#         self._session = self._driver.session()
#
#     def run(self, stmt: str):
#         return self._session.run(stmt)


def clean(driver) -> None:
    """
    Clean the database in preparation for a test run
    - Remove all existing nodes and relationships
    - Do not remove constraints or their implied indices - this is an assumed initial condition
    
    NOTES:
    - Creating the same constraint multiple times does not error, dropping a non-existent constraint does.
    
    The first run always takes very much longer. Although we delete all nodes, I expect there is some caching
    
    :param driver: a GraphDatabase.driver
    """
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        c = Constraint()
        c.drop(session)
        # c.create(session)


def single_batch(filename: str) -> float:
    """
    One file as a single, large statement
    This works as long as there is 0 or 1 semicolon at the end

    This approach uses a ref var for items it knows have been created, but larger files will exhaust system
    memory - we need chunking
    Alternatively, we could chunk node creates with matching rel creates
    
    NOTES:
    - you can set a tx type with session("write"), but it appears to make little difference
    """
    with open(filename, "r") as f:
        stmts = f.read()
    
    with GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "Admin1234!")) as db:
        clean(db)
        start = timer()
        # with db.session("write") as session:
        with db.session() as session:
            session.run(stmts)
    end = timer()
    
    return end - start


# def single_batch_timeit(filename: str) -> None:
#     """ An attempt at timeit - not working"""
#     setup = f'''
# from neo4j import GraphDatabase, basic_auth
# from constraints import Constraint
#
# with GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "Admin1234!")) as db:
#     with db.session() as session:
#         session.run("MATCH (n) DETACH DELETE n")
#         c = Constraint()
#         c.drop(session)
#         c.create(session)
#
# with open("{filename}", "r") as f:
#     stmts = f.read()
#     print(stmts)
#     '''
#     code = '''
# with GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "Admin1234!")) as db:
#     with db.session() as session:
#         session.run(stmts)
#     '''
#     print(timeit(setup=setup, stmt=code, number=3))


def multiple_batches():
    """
    This strategy uses id matching for each stmt lhs so statement count per batch can be adjusted
    
    Timing
    Statements 131
    BATCH_SIZE = 1
    Elapsed: 1.630646701
    """
    BATCH_SIZE = 300
    fn = "./gen_data3.txt"
    with GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "Admin1234!")) as db:
        clean(db)
        with db.session() as session:
            start = timer()
            with open(fn, "r") as f:
                stmts = ""
                for i, line in enumerate(f):
                    stmts += line
                    if not i % BATCH_SIZE:
                        try:
                            session.run(stmts)
                            stmts = ""
                        except:
                            print(f"session.run() failure at line {i}")
                            raise
                if len(stmts):
                    session.run(stmts)
            end = timer()
            print(f"Elapsed: {end - start}")


def multiple_batches_new():
    """
    This strategy uses id matching for each stmt lhs so statement count per batch can be adjusted
    """
    BATCH_SIZE = 1
    fn = "./gen_data3.txt"
    with GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "Admin1234!")) as db:
        clean(db)
        with db.session() as session:
            start = timer()
            with open(fn, "r") as f:
                for i, line in enumerate(f):
                    try:
                        session.run(line)
                    except:
                        print(f"session.run() failure at line {i}")
                        print(line)
                        raise
            end = timer()
            print(f"Elapsed: {end - start}")


def run_single_batch(iterations):
    for i in range(1,8):
        fn = f"data/gd1_case_{i}.txt"
        duration = 0
        for _ in range(iterations):
            duration += single_batch(fn)
        duration /= iterations
        nc = CASE_STATS[f'case_{i}']['nodes']
        nps = nc/duration
        print(f"gd1_case_{i}\t{nc}\t{duration}\t{nps}")


if __name__ == "__main__":
    run_single_batch(3)
