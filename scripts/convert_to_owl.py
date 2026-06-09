import rdflib
from pathlib import Path

# Convert the RIRPDM ontology from Turtle to OWL/XML format for better compatibility with some tools.
ROOT = Path(__file__).parent.parent

g = rdflib.Graph()
g.parse(ROOT / "ontology" / "rirpdm.ttl", format="turtle")
g.serialize(destination=str(ROOT / "ontology" / "rirpdm.owl"), format="xml")
print("Written: rirpdm.owl")
