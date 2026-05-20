import rdflib
from pathlib import Path

ROOT = Path(__file__).parent.parent

g = rdflib.Graph()
g.parse(ROOT / "ontology" / "rirpdo.ttl", format="turtle")
g.serialize(destination=str(ROOT / "ontology" / "rirpdo.owl"), format="xml")
print("Written: rirpdo.owl")
