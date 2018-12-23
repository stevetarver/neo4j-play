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

TODO:
    - validate results
    - sprayers - session pool that suports unordered data, but also indexing cause it is MERGE
"""
import argparse
from argparse import RawDescriptionHelpFormatter
from timeit import default_timer as timer
from typing import List

from generator import CASE_INFO, cypher_file
from trinity import Trinity


class Bench:
    
    def __init__(self, strategy: int, iterations: int, batch_size: int, cases: List[str]):
        self.trinity = Trinity()
        self.trinity.clean()
        self.strategy = f"i{strategy}"
        self.iterations = iterations
        self.batch_size = batch_size
        self.cases = [f"case_{x}" for x in cases]
        
        # TODO: ingest 1 is the only thing we want gulped at the moment
        if 1 == strategy:
            self.ingest_func = self.gulp
        else:
            self.ingest_func = self.batch
        
    def batch(self, filename: str) -> float:
        """
        Given a filename, iterate over it, collecting batch_size elements, execute
        each batch and return the time the entire process took.
        """
        self.trinity.clean()
        start = timer()
        with self.trinity.session() as session:
            with open(filename, "r") as f:
                stmts = ""
                for index, line in enumerate(f):
                    stmts += line
                    if index % self.batch_size == 0:
                        session.run(stmts)
                        stmts = ""
            # run overflow stmts
            if stmts.strip():
                session.run(stmts)
        return timer() - start

    def gulp(self, filename: str) -> float:
        """
        Read a single file into a string and return the time it takes trinity to execute those statements

        This works as long as there is 0, or 1 semicolon at the end
        """
        with open(filename, "r") as f:
            stmts = f.read()
        
        self.trinity.clean()
        start = timer()
        with self.trinity.session() as session:
            session.run(stmts)
        return timer() - start

    def report_header(self) -> None:
        print("Case\tNodes\tDuration\tNodes/sec")

    def report(self, case: str, duration: float) -> None:
        nc = CASE_INFO[case]['nodes']
        nps = int(nc / duration)
        print(f"{self.strategy}_{case}\t{nc}\t{duration:.4f}\t{nps}")

    def timeit(self) -> None:
        self.report_header()
        # ingest is the only strategy that can be gulped
        for case in self.cases:
            fn = cypher_file(case, self.strategy)
            duration = 0
            for _ in range(self.iterations):
                duration += self.ingest_func(fn)
        
            self.report(case, duration / self.iterations)
            
    def validate_run(self, case: str) -> None:
        labels = {"File": "files", "Directory": "dirs"}
        
        # Validate the run
        with self.trinity.session() as session:
            result = session.run("match (n) return head(labels(n)) as label, count(*);").values()
        
        error = False
        if len(result) > 2:
            print(f"Unexpected end state: too many node types: {len(result)}")
            error = True
        for item in result:
            if CASE_INFO[case][labels[item[0]]] != item[1]:
                print(f"Incorrect number of {item[0]} generated: {item[1]}")
                error = True
        if error:
            print(result)


def help() -> str:
    return '''Benchmark ingestion strategies

USE:
    Benchmark ingestion strategy 2, running 3 iterations per case, with batch size 1000
    ./bench.py -s2 -i3 -b1000 -c 100
'''


def main():
    # TODO: use this to verify case info: match (n) return head(labels(n)) as label, count(*);
    
    parser = argparse.ArgumentParser(description=help(), formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--strategy',
                        type=int,
                        default=1,
                        help='Ingestion strategy: [1..7]')
    parser.add_argument('-i', '--iterations',
                        type=int,
                        default=1,
                        help='How many times to run each case - results are averaged')
    parser.add_argument('-b', '--batch_size',
                        type=int,
                        default=1000,
                        help='How many statements to include in each run()')
    parser.add_argument('-c', '--cases',
                        nargs='+',
                        default=[100],
                        help='Which use cases, e.g. 100 1750')
    args = parser.parse_args()
    
    if args.strategy not in (1,2,4,6):
        print(f"Strategy not available: {args.strategy}")
        exit(1)
    if args.batch_size < 100 or args.batch_size > 10_000:
        print(f"Batch size inappropriate: {args.batch_size}")
        exit(1)
    for case in args.cases:
        if f"case_{case}" not in CASE_INFO:
            print(f"Case not found: {case}.")
            print(f"Valid cases are {', '.join(CASE_INFO)}")
            exit(1)
        try:
            cypher_file(f"case_{case}", f"i{args.strategy}")
        except Exception as e:
            print(f"Case {case} not available: {e}")
            exit(1)
    if args.iterations < 1:
        print(f"Invalid iterations: {args.iterations}")
        exit(1)

    b = Bench(args.strategy, args.iterations, args.batch_size, args.cases)
    b.timeit()


if __name__ == "__main__":
    main()
