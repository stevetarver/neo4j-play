#!/usr/bin/env python3
"""
The bench runs and reports on ingest scripts

Questions
- What is the fastest way to ingest n nodes, relationships?
- Does that vary by collection size?

Learnings:
- a statement is terminated by a ';' - there can be only one per run()
- many clauses can be in a single statement (CREATE, MERGE, etc)
- we jam as many clauses into a statement cause each run() has an auto commit - slow if we don't
- a merge either matches everything, or tries to create everything in the pattern.
- WITH rescopes variables groups some collections - probably no use in ingestion because we
  have many clauses it would affect

TODO: categories
- whole file readers
- line by line readers
- newline finders
- sprayers - session pool that suports unordered data, but also indexing cause it is MERGE
"""
import argparse
from timeit import default_timer as timer

from generator import CASE_INFO
from trinity import Trinity


def ingest_1(filename: str) -> float:
    """
    Ingestion strategy 1: One create group
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
    
    trinity = Trinity()
    trinity.clean()
    start = timer()
    with trinity.session() as session:
        session.run(stmts)
    end = timer()
    
    return end - start


def ingest_2(filename: str) -> float:
    """
    Ingestion strategy 2: Create groups
    Used when ingesting large datasets, we have all data prior to create

    Accumulate statements till we have about 800, then look for a blank line and submit it.
    Batch size determined by ingest_1
    """
    BATCH_SIZE = 800
    trinity = Trinity()
    trinity.clean()
    start = timer()
    with trinity.session() as session:
        with open(filename, "r") as f:
            stmts = ""
            count = 0
            for line in f:
                stmts += line
                count += 1
                if count >= BATCH_SIZE and not line.strip():
                    session.run(stmts)
                    stmts = ""
                    count = 0
        # run overflow stmts
        if stmts:
            session.run(stmts)
    end = timer()
    
    return end - start


def run_ingest_1(iterations: int) -> None:
    print("Case\tNodes\tDuration\tNodes/sec")
    ingest_key = "i1"
    for case, case_info in CASE_INFO.items():
        # NOTE: current neo4j config causes death above about this many nodes - revisit during tuning
        if case_info['nodes'] < 1800:
            fn = f"cypher/{ingest_key}_{case}.cypher"
            duration = 0
            for _ in range(iterations):
                # d = ingest_1(fn)
                # print(d)
                # duration += d
                duration += ingest_1(fn)
            
            duration /= iterations
            nc = case_info['nodes']
            nps = int(nc / duration)
            print(f"{ingest_key}_{case}\t{nc}\t{duration:.4f}\t{nps}")
            return


def run_ingest_2(iterations: int) -> None:
    print("Case\tNodes\tDuration\tNodes/sec")
    ingest_key = "i2"
    case = "case_5000"
    fn = f"cypher/{ingest_key}_{case}.cypher"
    duration = 0
    for _ in range(iterations):
        # d = ingest_1(fn)
        # print(d)
        # duration += d
        duration += ingest_2(fn)
    
    duration /= iterations
    nc = CASE_INFO[case]['nodes']
    nps = int(nc / duration)
    print(f"{ingest_key}_{case}\t{nc}\t{duration:.4f}\t{nps}")


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-i', action='store_true', default=False, help='Ingestion strategy: [1..5]')
    # parser.add_argument('-c', action='store_true', default=False, help='Count of runs; iterations. Default=1')
    # parser.add_argument('--index', action='store_true', default=False, help='Indexing on')
    # args = parser.parse_args()
    # if args.l:
    #     dir_counts()
    # else:
    #     pickle_datasets()
    
    run_ingest_1(1)
    # run_ingest_2(1)


if __name__ == "__main__":
    main()
