import rdflib
import time
import pathlib
from dotenv import load_dotenv
import os

from settings import path_base

# %%
path_to_secrets = pathlib.Path(path_base, 'secrets.env')
try:
    load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
except:
    print('secrets could not be loaded!')


# %%
# utility function to get the local part of a URI (stripping out the namespace)

def getLocalPart(uri):
    pos = -1
    pos = uri.rfind('#')
    if pos < 0:
        pos = uri.rfind('/')
    if pos < 0:
        pos = uri.rindex(':')
    return uri[pos + 1:]


def getNamespacePart(uri):
    pos = -1
    pos = uri.rfind('#')
    if pos < 0:
        pos = uri.rfind('/')
    if pos < 0:
        pos = uri.rindex(':')
    return uri[0:pos + 1]


# quick test
print(getLocalPart("http://onto.neo4j.com/rail#Station"))
print(getNamespacePart("http://onto.neo4j.com/rail#Station"))
# %%
# Own ontology:
# path_to_ontology = pathlib.Path(path_base, "models/Ontologies/Ontology4.ttl").as_posix()
path_to_ontology = pathlib.Path(path_base, "models/Ontologies/rail.ttl").as_posix()
# From tutorial:
# path_to_ontology = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/ontos/rail.ttl"
# %%
g = rdflib.Graph()
g.parse(source=path_to_ontology, format='turtle')
#%%
#############################################################################
aClass = rdflib.URIRef("http://www.w3.org/2002/07/owl#Class")
rdfType = rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

for triple in g.triples((None, rdfType, aClass)):
    print(triple)

#############################################################################
#%%
simple_query = """
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 

SELECT DISTINCT ?c
  WHERE {
    ?c rdf:type owl:Class .
  } """

for row in g.query(simple_query):
    print('URI: ', str(row.c), 'CLASS: ', getLocalPart(str(row.c)), 'NAMESPACE: ', getNamespacePart(str(row.c)))
    print('-----------------------------------------------------------')

# %%
# read the onto and generate cypher (complete without mappings)

g = rdflib.Graph()
g.parse(path_to_ontology, format='turtle')

classes_and_props_query = """
prefix owl: <http://www.w3.org/2002/07/owl#> 
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?curi (GROUP_CONCAT(DISTINCT ?propTypePair ; SEPARATOR=",") AS ?props)
WHERE {
    ?curi rdf:type owl:Class .
    optional { 
      ?prop rdfs:domain ?curi ;
        a owl:DatatypeProperty ;
        rdfs:range ?range .
      BIND (concat(str(?prop),';',str(?range)) AS ?propTypePair)
    }
  } 
GROUP BY ?curi  """

query_result_classes_and_props = g.query(classes_and_props_query)
print("Vars:", query_result_classes_and_props.vars)

for binding in query_result_classes_and_props.bindings:
    print("Binding:", binding)
    print('-------------')
# %%
cypher_list = []

for row in query_result_classes_and_props:
    cypher = []
    cypher.append("unwind $records AS record")
    cypher.append("merge (n:" + getLocalPart(row.curi) + " { `<id_prop>`: record.`<col with id>`} )")
    print('row.curi:', row.curi)
    print('row.props:', row.props)
    for pair in row.props.split(","):
        propName = pair.split(";")[0]
        print('propName:', propName)
        propType = pair.split(";")[1]
        print('propType:', propType)
        cypher.append(
            "set n." + getLocalPart(propName) + " = record.`<col with value for " + getLocalPart(propName) + ">`")
        print('getLocalPart(propName):', getLocalPart(propName))
        print('     ----- inner ------')
    print('----- OUTER -----')
    cypher.append("return count(*) as total")
    cypher_list.append(' \n'.join(cypher))

# %%
rels_query = """
prefix owl: <http://www.w3.org/2002/07/owl#> 
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 

SELECT DISTINCT ?rel ?dom ?ran #(GROUP_CONCAT(DISTINCT ?relTriplet ; SEPARATOR=",") AS ?rels)
WHERE {
    ?rel a ?propertyClass .
    filter(?propertyClass in (rdf:Property, owl:ObjectProperty, owl:FunctionalProperty, owl:AsymmetricProperty, 
           owl:InverseFunctionalProperty, owl:IrreflexiveProperty, owl:ReflexiveProperty, owl:SymmetricProperty, owl:TransitiveProperty))

    ?rel rdfs:domain ?dom ;
      rdfs:range ?ran .

    #BIND (concat(str(?rel),';',str(?dom),';',str(?range)) AS ?relTriplet)

  }"""

query_result_relations = g.query(rels_query)
print(query_result_relations.vars)
# %%
for row in query_result_relations:
    cypher = []
    cypher.append("unwind $records AS record")
    cypher.append("match (source:" + getLocalPart(row.dom) + " { `<id_prop>`: record.`<col with source id>`} )")
    cypher.append("match (target:" + getLocalPart(row.ran) + " { `<id_prop>`: record.`<col with target id>`} )")
    cypher.append("merge (source)-[r:`" + getLocalPart(row.rel) + "`]->(target)")
    cypher.append("return count(*) as total")
    for item in cypher:
        print('cypher-item:\n', item)
    print('---------------------------------------')
    cypher_list.append(' \n'.join(cypher))

# %%
for q in cypher_list:
    print("\n\n" + q)
# %%
railMappings = {}

stationMapping = {}
stationMapping[
    "@fileName"] = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/data/nr-stations-all.csv"
stationMapping["@uniqueId"] = "stationCode"
stationMapping["lat"] = "lat"
stationMapping["long"] = "long"
stationMapping["stationAddress"] = "address"
stationMapping["stationCode"] = "crs"
stationMapping["stationName"] = "name"
railMappings["Station"] = stationMapping

eventMapping = {}
eventMapping["@fileName"] = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/data/nr-events.csv"
eventMapping["@uniqueId"] = "eventId"
eventMapping["eventDescription"] = "desc"
eventMapping["eventId"] = "id"
eventMapping["timestamp"] = "ts"
eventMapping["eventType"] = "type"
railMappings["Event"] = eventMapping

linkMapping = {}
linkMapping[
    "@fileName"] = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/data/nr-station-links.csv"
linkMapping["@from"] = "origin"
linkMapping["@to"] = "destination"
railMappings["link"] = linkMapping

affectsMapping = {}
affectsMapping["@fileName"] = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/data/nr-events.csv"
affectsMapping["@from"] = "id"
affectsMapping["@to"] = "Station"
railMappings["affects"] = affectsMapping

# show it?
railMappings


# %%
# copy of previous but using the mappings
def getLoadersFromOnto(onto, rdf_format, mappings):
    g = rdflib.Graph()
    g.parse(onto, format=rdf_format)

    classes_and_props_query = """
    prefix owl: <http://www.w3.org/2002/07/owl#> 
    prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 

    SELECT DISTINCT ?curi (GROUP_CONCAT(DISTINCT ?propTypePair ; SEPARATOR=",") AS ?props)
    WHERE {
      ?curi rdf:type owl:Class .
      optional { 
        ?prop rdfs:domain ?curi ;
          a owl:DatatypeProperty ;
          rdfs:range ?range .
        BIND (concat(str(?prop),';',str(?range)) AS ?propTypePair)
      }
    } GROUP BY ?curi  """

    cypher_import = {}
    export_ns = set()
    export_mappings = {}

    for row in g.query(classes_and_props_query):
        export_ns.add(getNamespacePart(row.curi))
        export_mappings[getLocalPart(row.curi)] = str(row.curi)
        cypher = []
        cypher.append("unwind $records AS record")
        cypher.append("merge (n:" + getLocalPart(row.curi) + " { `" + mappings[getLocalPart(row.curi)][
            "@uniqueId"] + "`: record.`" + mappings[getLocalPart(row.curi)][
                          mappings[getLocalPart(row.curi)]["@uniqueId"]] + "`} )")
        for pair in row.props.split(","):
            propName = pair.split(";")[0]
            propType = pair.split(";")[1]
            export_ns.add(getNamespacePart(propName))
            export_mappings[getLocalPart(propName)] = propName
            # if a mapping (a column in the source file) is defined for the property and property is not a unique id
            if getLocalPart(propName) in mappings[getLocalPart(row.curi)] and getLocalPart(propName) != \
                    mappings[getLocalPart(row.curi)]["@uniqueId"]:
                cypher.append("set n." + getLocalPart(propName) + " = record.`" + mappings[getLocalPart(row.curi)][
                    getLocalPart(propName)] + "`")
        cypher.append("return count(*) as total")
        cypher_import[getLocalPart(row.curi)] = ' \n'.join(cypher)
        print('CYPHER in classes_and_props_query:\n', cypher)

    rels_query = """
    prefix owl: <http://www.w3.org/2002/07/owl#> 
    prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 

    SELECT DISTINCT ?rel ?dom ?ran #(GROUP_CONCAT(DISTINCT ?relTriplet ; SEPARATOR=",") AS ?rels)
    WHERE {
      ?rel a ?propertyClass .
      filter(?propertyClass in (rdf:Property, owl:ObjectProperty, owl:FunctionalProperty, owl:AsymmetricProperty, 
            owl:InverseFunctionalProperty, owl:IrreflexiveProperty, owl:ReflexiveProperty, owl:SymmetricProperty, owl:TransitiveProperty))

      ?rel rdfs:domain ?dom ;
        rdfs:range ?ran .

      #BIND (concat(str(?rel),';',str(?dom),';',str(?range)) AS ?relTriplet)

    }"""

    for row in g.query(rels_query):
        export_ns.add(getNamespacePart(row.rel))
        export_mappings[getLocalPart(row.rel)] = str(row.rel)
        cypher = []
        cypher.append("unwind $records AS record")
        cypher.append("match (source:" + getLocalPart(row.dom) + " { `" + mappings[getLocalPart(row.dom)][
            "@uniqueId"] + "`: record.`" + mappings[getLocalPart(row.rel)]["@from"] + "`} )")
        cypher.append("match (target:" + getLocalPart(row.ran) + " { `" + mappings[getLocalPart(row.ran)][
            "@uniqueId"] + "`: record.`" + mappings[getLocalPart(row.rel)]["@to"] + "`} )")
        cypher.append("merge (source)-[r:`" + getLocalPart(row.rel) + "`]->(target)")
        cypher.append("return count(*) as total")
        cypher_import[getLocalPart(row.rel)] = ' \n'.join(cypher)
        print('CYPHER in rels_query:\n', cypher)

    nscount = 0
    mapping_export_cypher = []

    for ns in export_ns:
        mapping_export_cypher.append("call n10s.nsprefixes.add('ns" + str(nscount) + "','" + ns + "');")
        nscount += 1

    for k in export_mappings.keys():
        mapping_export_cypher.append("call n10s.mapping.add('" + export_mappings[k] + "','" + k + "');")

    return cypher_import, mapping_export_cypher


# %%
cypher_import, mapping_defs = getLoadersFromOnto(
    "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/ontos/rail.ttl", "turtle", railMappings)

print("#LOADERS:\n\n")
for q in cypher_import.keys():
    print(q + ": \n\nfile: " + railMappings[q]["@fileName"] + "\n\n" + cypher_import[q] + "\n\n")

print("#EXPORT MAPPINGS (for RDF API):\n\n")
for md in mapping_defs:
    print(md)


# %%
# Utility function to write to Neo4j in batch mode.

def insert_data(session, query, frame, batch_size=500):
    print('QUERY:\n', query)
    print('---------------------------')

    total = 0
    batch = 0
    start = time.time()
    result = None

    while batch * batch_size < len(frame):
        res = session.write_transaction(lambda tx: tx.run(query,
                                                          parameters={'records': frame[batch * batch_size:(
                                                                                                                      batch + 1) * batch_size].to_dict(
                                                              'records')}).data())

        total += res[0]['total']
        batch += 1
        result = {"total": total,
                  "batches": batch,
                  "time": time.time() - start}
        print(result)

    return result


# %%
import pandas as pd
from neo4j import GraphDatabase, basic_auth

uri = "neo4j://localhost:7687"
auth = ("neo4j", os.getenv('NEO4J_PW'))
driver = GraphDatabase.driver(uri, auth=auth)

session = driver.session(database="neo4j")

cypher_import, mapping_defs = getLoadersFromOnto(
    "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session5/ontos/rail.ttl", "turtle", railMappings)

from pprint import pprint

pprint(cypher_import)
print('----------------------------------')
pprint(mapping_defs)
# %%

# for q in cypher_import.keys():
#     print("about to import " + q + " from file " + railMappings[q]["@fileName"])
#     df = pd.read_csv(railMappings[q]["@fileName"])
#     result = insert_data(session, cypher_import[q], df, batch_size=300)
#     print(result)
#
# for md in mapping_defs:
#     session.run(md)