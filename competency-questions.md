# Competency Questions

Prefix declarations assumed in all queries:
```sparql
PREFIX rirpdo: <http://www.example.org/rirpdo#>
```

---

## CQ01 [Publications] — Which researchers affiliated with institution X have published about topic Y?

```sparql
SELECT ?researcherName ?publicationTitle
WHERE {
    ?researcher   rirpdo:name           ?researcherName ;
                  rirpdo:affiliatedWith  ?institution .
    ?institution  rirpdo:name           ?institutionName .
    ?publication  rirpdo:hasAuthor      ?researcher ;
                  rirpdo:hasTopic       ?topic ;
                  rirpdo:title          ?publicationTitle .
    ?topic        rirpdo:name           ?topicName .
    FILTER(?institutionName = "Fraunhofer FOKUS")
    FILTER(?topicName = "Knowledge Graphs")
}
```

---

## CQ02 [Infrastructure] — Which research infrastructure does institution X operate?

```sparql
SELECT ?infraName ?infraType
WHERE {
    ?researcher   rirpdo:affiliatedWith   ?institution .
    ?institution  rirpdo:name             ?institutionName .
    ?project      rirpdo:hasParticipant   ?researcher ;
                  rirpdo:usesInfrastructure ?infra .
    ?infra        rirpdo:name             ?infraName ;
                  a                       ?infraType .
    FILTER(?institutionName = "Technische Universität Berlin")
    FILTER(?infraType IN (rirpdo:Laboratory, rirpdo:ResearchDataRepository))
}
```

---

## CQ03 [Both] — Which publications resulted from projects that used infrastructure of type X?

Bridges publications and infrastructure — core to the ontology's dual purpose.

```sparql
SELECT ?publicationTitle ?projectName ?infraName
WHERE {
    ?project      rirpdo:name                ?projectName ;
                  rirpdo:usesInfrastructure  ?infra ;
                  rirpdo:hasParticipant      ?researcher .
    ?infra        a                          rirpdo:Laboratory ;
                  rirpdo:name                ?infraName .
    ?publication  rirpdo:hasAuthor           ?researcher ;
                  rirpdo:title               ?publicationTitle .
}
```

---

## CQ04 [Infrastructure] — Which datasets were produced by project X and stored in which repository?

```sparql
SELECT ?datasetName ?repoName
WHERE {
    ?project  rirpdo:name               ?projectName ;
              rirpdo:producedDataset    ?dataset ;
              rirpdo:usesInfrastructure ?repo .
    ?dataset  rirpdo:name               ?datasetName .
    ?repo     a                         rirpdo:ResearchDataRepository ;
              rirpdo:name               ?repoName .
    FILTER(?projectName = "LOPDF Project")
}
```

---

## CQ05 [Publications] — Which researchers have co-authored at least one publication?

```sparql
SELECT DISTINCT ?name1 ?name2 ?publicationTitle
WHERE {
    ?publication  rirpdo:hasAuthor  ?r1 ;
                  rirpdo:hasAuthor  ?r2 ;
                  rirpdo:title      ?publicationTitle .
    ?r1           rirpdo:name       ?name1 .
    ?r2           rirpdo:name       ?name2 .
    FILTER (?r1 != ?r2)
    FILTER (STR(?r1) < STR(?r2))
}
```