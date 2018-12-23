
CREATE CONSTRAINT ON (d:Directory) ASSERT d.id IS UNIQUE;
CREATE CONSTRAINT ON (f:File)      ASSERT f.id IS UNIQUE;

USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:///i6_case_5000_dir.csv" as row

CREATE (d:Directory {
    name: row.name,
    tag: row.tag,
    id: toInteger(row.id),
    parent_id: toInteger(row.parent_id),
    stem: row.stem,
    extension: row.extension,
    path: row.path,
    size: toInteger(row.size),
    owner: toInteger(row.owner),
    group: toInteger(row.group),
    created: toInteger(row.created),
    accessed: toInteger(row.accessed),
    modified: toInteger(row.modified)
})

// Avoid NULL error for root node
FOREACH (pid IN (CASE row.parent_id WHEN NULL THEN [] ELSE [1] END) |
  MERGE (p:Directory {id: toInteger(row.parent_id)})
  MERGE (p)-[:PARENT_OF]->(d)
);


USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:///i6_case_5000_file.csv" as row

CREATE (f:File {
    name: row.name,
    tag: row.tag,
    id: toInteger(row.id),
    parent_id: toInteger(row.parent_id),
    stem: row.stem,
    extension: row.extension,
    path: row.path,
    size: toInteger(row.size),
    owner: toInteger(row.owner),
    group: toInteger(row.group),
    created: toInteger(row.created),
    accessed: toInteger(row.accessed),
    modified: toInteger(row.modified)
})

MERGE (p:Directory {id: toInteger(row.parent_id)})
MERGE (p) - [:PARENT_OF] -> (f);
