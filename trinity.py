"""
Trinity talks to Neo... A LOT


NOTES:
- Many methods return self so they can be chained:
    Trinity().clean().run(stmts).create_constraints()

Python driver choices:
 See https://neo4j.com/developer/python/#_neo4j_community_drivers

What driver should we use?
- should use bolt - binary protocols are always faster

TODO: consume a TreeNode and provide processing for the following categories
- whole file readers
- line by line readers
- newline finders
- sprayers - session pool that suports unordered data, but also indexing cause it is MERGE
"""
from neo4j import GraphDatabase, basic_auth
from neobolt.exceptions import CypherError


class Trinity:
    """
    Trinity encapsulates Neo connection details and simplifies driver use
    As written, this class is intended to be short lived - cause sessions should be short lived.

    NOTE: we don't have to close the driver or session - the base classes override __del__() to do that.

    We could also have a long lived driver class that used sessions in a short-lived fashion
    """
    _constraints = "CONSTRAINT ON ({var}:{label}) ASSERT {var}.id IS UNIQUE;"
    _labels = ("Directory", "File", "Classification", "Perspective")

    def __init__(self, url: str="bolt://localhost", user: str="neo4j", password: str="Admin1234!"):
        self._driver = GraphDatabase.driver(url, auth=basic_auth(user, password))

    def clean(self) -> "Trinity":
        """
        Clean the database in preparation for a test run
        - Remove all existing nodes and relationships
        - Remove all constraints

        NOTES:
        - Creating the same constraint multiple times does not error, dropping a non-existent constraint does.
        
        TODO: How do we disable indexing as part of an ingestion
        """
        with self.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        self.drop_all_constraints()
        return self

    def create_constraints(self) -> "Trinity":
        """ Create constraints on the db """
        with self.session() as session:
            for c in [self._constraints.format(var=x.lower(), label=x) for x in self._labels]:
                session.run("CREATE " + c)
        return self

    def drop_constraints(self) -> "Trinity":
        """ Drop the constraints we created from the db """
        # TODO: This can error in a way that throws an exception even though we are passing
        #       Each with session block should be wrapped in a try-catch
        with self.session() as session:
            for c in [self._constraints.format(var=x.lower(), label=x) for x in self._labels]:
                try:
                    session.run("DROP " + c)
                except CypherError as ce:
                    if "No such constraint" not in f"{ce}":
                        print(f"Trinity.drop_all_constraints() exception: {ce}")
        return self

    def drop_all_constraints(self) -> "Trinity":
        """ Drop all constraints on the db - even those we did not create """
        with self.session() as session:
            # For all current constraints
            for c in session.run("CALL db.constraints").value():
                try:
                    session.run("DROP " + c)
                except CypherError as ce:
                    # If an exception occurs, the driver may close the connection and try again - throwing another ex
                    print(f"Trinity.drop_all_constraints() exception: {ce}")
        return self

    def session(self):
        """
        Get a driver session. Expected use is:
            with trinity.session() as session:
            
        TODO: we can pass "read" or "write" to the session to control tx type
              in testing, saw no difference
        """
        return self._driver.session()

    def run(self, stmts: str) -> "Trinity":
        with self.session() as session:
            session.run(stmts)
        return self

