from neo4j import GraphDatabase, RoutingControl
from dotenv import load_dotenv
import os
import pathlib

from settings import path_base


class KnowledgeGraph:

    def __init__(self):
        path_to_secrets = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        auth = ("neo4j", os.getenv('NEO4J_PW'))
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def init_graph(self, handle_vocab_uris: str = "MAP", handle_mult_vals: str = "ARRAY", handle_rdf_types: str = "LABELS",
                   keep_lang_tag: bool = False, keep_cust_dtypes: bool = False, apply_neo4j_naming: bool = False):
        query_init = f"""CALL n10s.graphconfig.init(
            {{  handleVocabUris: '{handle_vocab_uris}',
                handleMultival: '{handle_mult_vals}',
                handleRDFTypes: '{handle_rdf_types}',
                keepLangTag: {str(keep_lang_tag).lower()},
                keepCustomDataTypes: {str(keep_cust_dtypes).lower()}, 
                applyNeo4jNaming: {str(apply_neo4j_naming).lower()},
                classLabel: 'CLASS',
                subClassOfRel: 'IS_A',
                objectPropertyLabel: 'RELATION',
                subPropertyOfRel: 'Sub-Property',
                domainRel: 'FROM',
                rangeRel: 'TO'
              }})"""
        query_constraint = f"""CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE"""
        self.driver.execute_query(query_=query_init)
        self.driver.execute_query(query_=query_constraint)

    def delete_graph(self):
        query_delete = f"""MATCH(n) DETACH DELETE n"""
        query_drop_constr = f"""DROP CONSTRAINT n10s_unique_uri IF EXISTS"""
        self.driver.execute_query(query_=query_delete)
        self.driver.execute_query(query_=query_drop_constr)

    def load_onto_or_rdf(self, path: str, path_is_url: bool = False,
                         load_onto_only: bool = True, serialization_type: str = "Turtle"):
        query_load = f"""
        CALL n10s.{'onto' if load_onto_only else 'rdf'}.import.fetch("{("file:///" if not path_is_url else "") + path}", 
        "{serialization_type}")
        """
        self.driver.execute_query(query_=query_load)

    def import_data_from_wikidata(self):
        pass


if __name__ == '__main__':
    kg = KnowledgeGraph()
    kg.delete_graph()
    kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    # path_to_onto: str = "C:/Users/rainer/PycharmProjects/UASFRA-MS-PROJDIGI/models/Ontologies/neo4j.ttl"
    # path_to_onto: str = "C:/Users/rainer/PycharmProjects/UASFRA-MS-PROJDIGI/models/Ontologies/Ontology2.ttl"
    # path_to_onto: str = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session4/ontos/movies-onto.ttl"
    path_to_onto: str = "C:/Users/rainer/PycharmProjects/UASFRA-MS-PROJDIGI/models/Ontologies/Ontology_Simple.ttl"
    kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False)


