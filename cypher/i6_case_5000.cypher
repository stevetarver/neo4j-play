
// NOTE: Someone should have established constraints
USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:///i6_case_5000_dir.csv" as row

CREATE (d:Directory {
    id: toInteger(row.id),
    tag: row.tag,
    name: row.name,
    parent_id: toInteger(row.parent_id),
    stem: row.stem,
    extension: row.extension,
    path: row.path,
    size: toInteger(row.size),
    owner: toInteger(row.owner),
    group: toInteger(row.group),
    created: toInteger(row.created),
    accessed: toInteger(row.accessed),
    modified: toInteger(row.modified),
    owner_perm: toInteger(row.owner_perm),
    group_perm: toInteger(row.group_perm),
    other_perm: toInteger(row.other_perm)
})

// Avoid NULL error for root node
FOREACH (pid IN (CASE row.parent_id WHEN NULL THEN [] ELSE [1] END) |
  MERGE (p:Directory {id: toInteger(row.parent_id)})
  MERGE (p)-[:PARENT_OF]->(d)
)


USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM "file:///i6_case_5000_file.csv" as row

CREATE (f:File {
    id: toInteger(row.id),
    tag: row.tag,
    name: row.name,
    parent_id: toInteger(row.parent_id),
    stem: row.stem,
    extension: row.extension,
    path: row.path,
    size: toInteger(row.size),
    owner: toInteger(row.owner),
    group: toInteger(row.group),
    created: toInteger(row.created),
    accessed: toInteger(row.accessed),
    modified: toInteger(row.modified),
    owner_perm: toInteger(row.owner_perm),
    group_perm: toInteger(row.group_perm),
    other_perm: toInteger(row.other_perm)
})

MERGE (p:Directory {id: toInteger(row.parent_id)})
MERGE (p) - [:PARENT_OF] -> (f)
