"""

"""


class Constraint:
    _cypher = "CONSTRAINT ON ({var}:{label}) ASSERT {var}.id IS UNIQUE;"
    _labels = ("Directory", "File", "Classification")

    def __init__(self):
        self.constraints = [self._cypher.format(var=x.lower(), label=x) for x in self._labels]

    def create(self, session):
        for c in self.constraints:
            session.run("CREATE " + c)

    def drop(self, session):
        for c in self.constraints:
            try:
                session.run("DROP " + c)
            except:
                pass
