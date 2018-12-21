"""
Trinity talks to Neo... A LOT

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


class Trinity:
    """
    Trinity encapsulates Neo connection details and simplifies driver use
    As written, this class is intended to be short lived - cause sessions should be short lived.

    NOTE: we don't have to close the driver or session - the base classes override __del__() to do that.

    We could also have a long lived driver class that used sessions in a short-lived fashion
    """
    _constraints = "CONSTRAINT ON ({var}:{label}) ASSERT {var}.id IS UNIQUE;"
    _labels = ("Directory", "File", "Classification")

    def __init__(self, url: str="bolt://localhost", user: str="neo4j", password: str="Admin1234!"):
        self._driver = GraphDatabase.driver(url, auth=basic_auth(user, password))

    def clean(self) -> None:
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
        self.drop_constraints()

    def create_constraints(self):
        """ Create constraints on the db """
        with self.session() as session:
            for c in [self._constraints.format(var=x.lower(), label=x) for x in self._labels]:
                session.run("CREATE " + c)

    def drop_constraints(self):
        """ Drop constraints on the db """
        with self.session() as session:
            for c in [self._constraints.format(var=x.lower(), label=x) for x in self._labels]:
                try:
                    session.run("DROP " + c)
                except:
                    # If the constraint does not exist, this will throw an exception - we don't care
                    pass

    def session(self):
        """
        Get a driver session. Expected use is:
            with trinity.session() as session:
            
        TODO: we can pass "read" or "write" to the session to control tx type
              in testing, saw no difference
        """
        return self._driver.session()

