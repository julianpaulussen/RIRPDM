from typing import Any, cast
from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = "http://localhost:7200/repositories/rirpdo"
PREFIX = "PREFIX rirpdo: <http://www.example.org/rirpdo#>"

QUERIES = {
    "CQ01 — Researchers at institution X publishing on topic Y": f"""
{PREFIX}
SELECT ?researcherName ?publicationTitle
WHERE {{
    ?researcher   rirpdo:name           ?researcherName ;
                  rirpdo:affiliatedWith  ?institution .
    ?institution  rirpdo:name           ?institutionName .
    ?publication  rirpdo:hasAuthor      ?researcher ;
                  rirpdo:hasTopic       ?topic ;
                  rirpdo:title          ?publicationTitle .
    ?topic        rirpdo:name           ?topicName .
    FILTER(?institutionName = "Fraunhofer FOKUS")
    FILTER(?topicName = "Semantic Web")
}}
""",
    "CQ02 — Projects and their research infrastructure": f"""
{PREFIX}
SELECT ?projectName ?infraName
WHERE {{
    ?project a rirpdo:Project ;
             rirpdo:name ?projectName ;
             rirpdo:usesInfrastructure ?infra .
    ?infra   rirpdo:name ?infraName .
}}
ORDER BY ?infraName
""",
    "CQ03 — Publications sharing a topic with Pub_LOPDF": f"""
{PREFIX}
SELECT DISTINCT ?relatedTitle ?sharedTopicName
WHERE {{
    rirpdo:Pub_LOPDF rirpdo:hasTopic ?sharedTopic .
    ?related a rirpdo:Publication ;
             rirpdo:hasTopic ?sharedTopic ;
             rirpdo:title ?relatedTitle .
    ?sharedTopic rirpdo:name ?sharedTopicName .
    FILTER (?related != rirpdo:Pub_LOPDF)
}}
""",
    "CQ04 — Datasets produced by projects and via which infrastructure": f"""
{PREFIX}
SELECT ?projectName ?datasetName ?infraName
WHERE {{
    ?project  rirpdo:name               ?projectName ;
              rirpdo:producedDataset    ?dataset ;
              rirpdo:usesInfrastructure ?infra .
    ?dataset  rirpdo:name               ?datasetName .
    ?infra    rirpdo:name               ?infraName .
}}
""",
    "CQ05 — Co-authors": f"""
{PREFIX}
SELECT DISTINCT ?name1 ?name2 ?publicationTitle
WHERE {{
    ?publication  rirpdo:hasAuthor  ?r1 ;
                  rirpdo:hasAuthor  ?r2 ;
                  rirpdo:title      ?publicationTitle .
    ?r1           rirpdo:name       ?name1 .
    ?r2           rirpdo:name       ?name2 .
    FILTER (?r1 != ?r2)
    FILTER (STR(?r1) < STR(?r2))
}}
""",
    "CQ06 — Research topics ranked by publication count": f"""
{PREFIX}
SELECT ?topicName (COUNT(?publication) AS ?publicationCount)
WHERE {{
    ?publication a rirpdo:Publication ;
                 rirpdo:hasTopic ?topic .
    ?topic rirpdo:name ?topicName .
}}
GROUP BY ?topicName
ORDER BY DESC(?publicationCount)
""",
    "CQ07 — Institutions ranked by researcher count": f"""
{PREFIX}
SELECT ?institutionName (COUNT(?researcher) AS ?researcherCount)
WHERE {{
    ?researcher a rirpdo:Researcher ;
                rirpdo:affiliatedWith ?institution .
    ?institution rirpdo:name ?institutionName .
}}
GROUP BY ?institutionName
ORDER BY DESC(?researcherCount)
""",
}


def run_queries():
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setReturnFormat(JSON)

    for title, query in QUERIES.items():
        print(f"\n{'='*60}")
        print(f"{title}")
        print('='*60)

        sparql.setQuery(query)
        results = cast(dict[str, Any], sparql.query().convert())
        bindings = results["results"]["bindings"]

        if not bindings:
            print("  (no results)")
            continue

        vars_ = results["head"]["vars"]
        for row in bindings:
            values = [row.get(v, {}).get("value", "-") for v in vars_]
            print("  " + " | ".join(values))


if __name__ == "__main__":
    run_queries()
