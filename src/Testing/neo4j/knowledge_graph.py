import os
import pathlib
from dotenv import load_dotenv

from neo4j import GraphDatabase

from settings import path_base, path_data
from rdf_graph import RDFGraph


class KnowledgeGraph:

    def __init__(self, path_to_onto: str):
        path_to_secrets: pathlib.Path = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        auth = ("neo4j", os.getenv('NEO4J_PW'))
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.path_to_onto: str = path_to_onto

    def init_graph(self, handle_vocab_uris: str = "MAP", handle_mult_vals: str = "ARRAY",
                   handle_rdf_types: str = "LABELS",
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
        # for constraint in self.driver.execute_query("SHOW CONSTRAINT"):
        #     self.driver.execute_query("DROP " + constraint[0])

    def load_onto_or_rdf(self, path: str, path_is_url: bool = False,
                         load_onto_only: bool = True, serialization_type: str = "Turtle"):
        query_load = f"""
        CALL n10s.{'onto' if load_onto_only else 'rdf'}.import.fetch("{("file:///" if not path_is_url else "") + path}", 
        "{serialization_type}")
        """
        self.driver.execute_query(query_=query_load)

    def import_data_from_wikidata(self):
        pass

    def load_data_into_knowledge_graph(self, unique_node_keys: dict[str:str] = None, node_value_props: dict[str:str] = None,
                                       nodes_data: list[dict] = None, rels_data: list[dict] = None):
        # if nodes_data is None:
        #     nodes_data = {}
        # if rels_data is None:
        #     rels_data = {}

        g = RDFGraph(path_to_onto=self.path_to_onto)
        constraint_queries, node_queries, rel_queries, ns_queries = g.create_queries(
            unique_node_keys=unique_node_keys, node_value_props=node_value_props)

        session = self.driver.session()

        # print('Namespace_Queries:')
        # for ns_query in ns_queries:
        #     print('ns_query:', ns_query)
        #     session.run(ns_query)

        for constraint_query in constraint_queries:
            print('Constraint_Query: ', constraint_query)
            res0 = session.run(constraint_query)

        for node_data in nodes_data:
            node = list(node_data.keys())[0]
            print('node:', node)
            node_query = node_queries[node]
            print('Node_Query:', node_query)
            res1 = session.run(node_query, parameters={'node_data': node_data})

        for rel_data in rels_data:
            rel = list(rel_data.keys())[0]
            print('rel:', rel)
            rel_query = rel_queries[rel]
            print('Rels_Query: ', rel_query)
            res2 = session.run(rel_query, parameters={'rel_data': rel_data})


if __name__ == '__main__':

    ## Ontology4.ttl:
    unique_node_keys = {"Company": ["LEI"],
                        "Waste": ["period", "label"],
                        "Substance": ["period", "label"],
                        "EnergyFromNuclearSources": ["period", "label"],
                        "EnergyFromFossilSources": ["period", "label"],
                        "EnergyFromRenewableSources": ["period", "label"],
                        "GHGEmission": ["period", "label"],
                        "Scope1": ["period", "label"],
                        "Scope2": ["period", "label"],
                        "Scope3": ["period", "label"],
                        "GHGReduction": ["period", "label"],
                        "Land": ["period", "label"],
                        "Water": ["period", "label"],
                        "Asset": ["period", "label"],
                        "Expenditure": ["period", "label"],
                        "Revenue": ["period", "label"],
                        }

    node_value_props = {"Waste": "tons",
                        "Substance": "tons",
                        "EnergyFromNuclearSources": "MWh",
                        "EnergyFromFossilSources": "MWh",
                        "EnergyFromRenewableSources": "MWh",
                        "GHGEmission": "tonsCO2Eq",
                        "Scope1": "tonsCO2Eq",
                        "Scope2": "tonsCO2Eq",
                        "Scope3": "tonsCO2Eq",
                        "GHGReduction": "tonsCO2Eq",
                        "Land": "hectares",
                        "Water": "cubicmetres",
                        "Asset": "EUR",
                        "Revenue": "EUR",
                        "Expenditure": "EUR"
                        }

    ########################### Load ontology and show schema of knowledge graph  ####################################
    # path_to_onto: str = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session4/ontos/movies-onto.ttl"
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/rail.ttl"
    path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    kg = KnowledgeGraph(path_to_onto=path_to_onto)
    kg.delete_graph()
    kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False, load_onto_only=True)
    print('Done!')
    #################################### Load data into Konwledge Graph ###############################################
    # from data.read_data import get_data_dicts
    # # all_jsons = ['data/Adidas_2022.json', "data/BASF_2022.json", 'data/Adidas_2023.json', "data/BASF_2023.json"]
    # all_jsons = ["data/BASF_2022.json", 'data/Adidas_2022.json']
    # n_data, r_data = get_data_dicts(all_json_paths=all_jsons)
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # kg = KnowledgeGraph(path_to_onto=path_to_onto)
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="MAP", handle_mult_vals="OVERWRITE")
    # kg.load_data_into_knowledge_graph(unique_node_keys=unique_node_keys, node_value_props=node_value_props, nodes_data=n_data, rels_data=r_data)
    # print("Done!")
    ########################################

