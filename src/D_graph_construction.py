import os
import pathlib
from dotenv import load_dotenv

from neo4j import GraphDatabase, Record

from settings import path_base, path_data
from src.B_rdf_graph import RDFGraph
from src.E_embeddings import Embedder


class GraphConstruction:
    """ Constructs a NEO4J Knowledge Graph ("KG"). Methods populate the KG with data from JSON-files (please see:
    README-data.md), with external data from wikidata/dbpedia and with text embeddings of a Node's text property. The
    methods thereby use parameterized cypher queries. """

    def __init__(self, path_to_onto: str, neo4j_db_name: str = 'neo4j'):
        path_to_secrets: pathlib.Path = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        self.neo4j_db_name: str = neo4j_db_name
        auth = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PW'))
        self.driver = GraphDatabase.driver(uri, auth=auth)
        if not pathlib.Path(path_to_onto).is_file():
            raise ValueError(f"Provided path to Ontology '{path_to_onto}' does not exist!")
        self.path_to_onto: str = path_to_onto

    def init_graph(self, handle_vocab_uris: str = "MAP", handle_mult_vals: str = "ARRAY",
                   multi_val_prop_list: list = None, handle_rdf_types: str = "LABELS",
                   keep_lang_tag: bool = False, keep_cust_dtypes: bool = False, apply_neo4j_naming: bool = False):
        query_init = f"""CALL n10s.graphconfig.init(
            {{  handleVocabUris: '{handle_vocab_uris}',
                handleMultival: '{handle_mult_vals}',
                multivalPropList: {list() if multi_val_prop_list is None else multi_val_prop_list},
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
        self.driver.execute_query(query_=query_init, database_=self.neo4j_db_name)
        self.driver.execute_query(query_=query_constraint, database_=self.neo4j_db_name)

    def delete_graph(self):
        query_delete = f"""MATCH(n) DETACH DELETE n"""
        query_drop_constr = f"""DROP CONSTRAINT n10s_unique_uri IF EXISTS"""
        self.driver.execute_query(query_=query_delete, database_=self.neo4j_db_name)
        self.driver.execute_query(query_=query_drop_constr, database_=self.neo4j_db_name)
        constraints: list[Record] = self.driver.execute_query("SHOW CONSTRAINT", database_=self.neo4j_db_name).records
        for constraint in constraints:
            self.driver.execute_query(query_="DROP CONSTRAINT " + constraint['name'], database_=self.neo4j_db_name)
        indexes: list[Record] = self.driver.execute_query("SHOW INDEXES", database_=self.neo4j_db_name).records
        for index in indexes:
            self.driver.execute_query("DROP INDEX " + index['name'], database_=self.neo4j_db_name)

    def load_onto_or_rdf(self, path: str, path_is_url: bool = False,
                         load_onto_only: bool = True, serialization_type: str = "Turtle"):
        query_load = f"""
        CALL n10s.{'onto' if load_onto_only else 'rdf'}.import.fetch("{("file:///" if not path_is_url else "") + path}", 
        "{serialization_type}")
        """
        self.driver.execute_query(query_=query_load, database_=self.neo4j_db_name)

    def import_wikidata_id(self, label_wikidata_id: str = "wikidataID"):

        # """BIND(STRAFTER(STR(?company), STR(wd:)) AS ?{label_wikidata_id}) ."""

        query = rf"""
                MATCH (node:Company)
                WITH 
                    "SELECT ?LEI ?{label_wikidata_id}
                        WHERE {{
                            FILTER contains(?LEI, \"" + node.LEI + "\")
                            ?{label_wikidata_id}   wdt:P1278   ?LEI .
                      }}"     
                AS sparql
                CALL apoc.load.jsonParams(
                    "https://query.wikidata.org/sparql?query=" + 
                      apoc.text.urlencode(sparql),
                    {{ Accept: "application/sparql-results+json"}}, null)
                YIELD value
                UNWIND value['results']['bindings'] as row
                WITH row['LEI']['value'] as prop_val, 
                     row['{label_wikidata_id}']['value'] as new_prop_val
                MERGE (n:Company {{ LEI: prop_val }})
                SET n.{label_wikidata_id} = new_prop_val;
                """
        self.driver.execute_query(query_=query, database_=self.neo4j_db_name)

    def import_data_from_wikidata(self, node_label: str, prop_name: str, prop_wiki_id: str,
                                  new_prop_name: str, new_prop_wiki_id: str,
                                  use_new_prop_label: bool, new_prop_is_list: bool):
        query = rf"""
        MATCH (node:{node_label})
        WITH 
            "SELECT ?{prop_name} ?{new_prop_name}{"Label" if use_new_prop_label else ""}
                WHERE {{
                    FILTER contains(?{prop_name}, \"" + node.{prop_name} + "\")
                    ?company wdt:{prop_wiki_id}     ?{prop_name} ;
                             wdt:{new_prop_wiki_id} ?{new_prop_name} .
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
              }}"     
        AS sparql
        CALL apoc.load.jsonParams(
            "https://query.wikidata.org/sparql?query=" + 
              apoc.text.urlencode(sparql),
            {{ Accept: "application/sparql-results+json"}}, null)
        YIELD value
        UNWIND value['results']['bindings'] as row
        WITH row['{prop_name}']['value'] as prop_val, 
             {'collect(' if new_prop_is_list else ''}row['{new_prop_name}{"Label" if use_new_prop_label else ""}']['value']{')' if new_prop_is_list else ''} as new_prop_val
        MERGE (n:{node_label} {{ {prop_name}: prop_val }})
        SET n.{new_prop_name} = new_prop_val;
        """
        self.driver.execute_query(query_=query, database_=self.neo4j_db_name)

    def import_data_from_dbpedia(self, node_label: str, prop_name: str, prop_dbp_id: str,
                                 new_prop_name: str, new_prop_dbp_id: str,
                                 new_prop_is_list: bool):
        query = rf"""
        MATCH (node:{node_label})
        WITH
            "PREFIX wd: <http://www.wikidata.org/entity/>
             SELECT ?{prop_name} ?{new_prop_name}
                    WHERE {{
                        BIND(<"+node.{prop_name}+"> AS ?wikidataID)
                        ?dbpcomp   {prop_dbp_id}   ?wikidataID ;
                                   {new_prop_dbp_id} ?{new_prop_name} .
                    FILTER langMatches( lang(?{new_prop_name}), \"en\" )
                  }}"   
        AS sparql
        CALL apoc.load.jsonParams(
            "https://dbpedia.org/sparql?query=" + 
              apoc.text.urlencode(sparql),
            {{ Accept: "application/sparql-results+json"}}, null)
        YIELD value
        UNWIND value['results']['bindings'] as row
        WITH row['{prop_name}']['value'] as prop_val, 
             {'collect(' if new_prop_is_list else ''}row['{new_prop_name}']['value']{')' if new_prop_is_list else ''} as new_prop_val
        MERGE (n:{node_label} {{ {prop_name}: prop_val }})
        SET n.{new_prop_name} = new_prop_val;
        """
        self.driver.execute_query(query_=query, database_=self.neo4j_db_name)

    def create_text_embedding(self, node_label: str, node_primary_prop_name: str, prop_to_embed: str,
                              vector_size: int = 768,
                              similarity_method: str = "cosine"):
        name_embedded_prop = prop_to_embed + "_embedding"
        query_index = f"""CALL db.index.vector.createNodeIndex('{"NodeIndex" + "_" + node_label + "_" + prop_to_embed}',
                          '{node_label}', '{name_embedded_prop}', {vector_size}, '{similarity_method}' ) ; """
        query_prop_to_embed = f"""
        MATCH (n:{node_label})     
        RETURN n.{node_primary_prop_name} AS {node_primary_prop_name}, n.{prop_to_embed} AS {prop_to_embed}
        """
        session = self.driver.session(database=self.neo4j_db_name)
        try:
            res = self.driver.execute_query(query_=query_index, database_=self.neo4j_db_name)
        except Exception as e:
            print(f'INFO: Index already exists: {e}')
        embed_nodes_and_props: list[dict] = session.run(query=query_prop_to_embed).data()

        embedder = Embedder()
        for item in embed_nodes_and_props:
            embedding = embedder.get_embedding(text=item[f'{prop_to_embed}'])
            query_set_embed_prop = f"""
            MATCH (n:{node_label})
            WHERE n.{node_primary_prop_name} = '{item[f'{node_primary_prop_name}']}'
            SET n.{name_embedded_prop} = {embedding} ;
            """
            session.run(query=query_set_embed_prop)

    def load_data_into_knowledge_graph(self, unique_node_keys: dict[str:str] = None,
                                       node_value_props: dict[str:str] = None,
                                       nodes_data: list[dict] = None, rels_data: list[dict] = None,
                                       show_queries: bool = False):
        # if nodes_data is None:
        #     nodes_data = {}
        # if rels_data is None:
        #     rels_data = {}

        g = RDFGraph(path_to_onto=self.path_to_onto)
        constraint_queries, node_queries, rel_queries, ns_queries = g.create_query_templates(
            unique_node_keys=unique_node_keys, node_value_props=node_value_props)

        session = self.driver.session(database=self.neo4j_db_name)

        for ns_query in ns_queries:
            if show_queries:
                print('ns_query:', ns_query)
            session.run(ns_query)

        for constraint_query in constraint_queries:
            if show_queries:
                print('Constraint_Query: ', constraint_query)
            res0 = session.run(constraint_query)

        for node_data in nodes_data:
            node = list(node_data.keys())[0]
            node_query = node_queries[node]
            if show_queries:
                print('node:', node)
                print('Node_Query:', node_query)
            res1 = session.run(node_query, parameters={'node_data': node_data})

        for rel_data in rels_data:
            rel = list(rel_data.keys())[0]
            rel_query = rel_queries[rel]
            if show_queries:
                print('rel:', rel)
                print('Rels_Query: ', rel_query)
            res2 = session.run(rel_query, parameters={'rel_data': rel_data})

        session.close()


if __name__ == '__main__':
    pass
    ########################### Load ontology and show schema of knowledge graph  ####################################
    # # path_to_onto: str = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session4/ontos/movies-onto.ttl"
    # # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/rail.ttl"
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # kg = KnowledgeGraph(path_to_onto=path_to_onto)
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    # kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False, load_onto_only=True)
    # print('Done!')
    #################################### Load data into Konwledge Graph ###############################################
    # from data.read_data import get_data_dicts
    # all_jsons = ['data/Adidas_2022.json', "data/BASF_2022.json", 'data/Adidas_2023.json', "data/BASF_2023.json"]
    # # all_jsons = ["data/BASF_2022.json", 'data/Adidas_2022.json']
    # all_jsons = ["data/Puma_2022.json", 'data/Puma_2023.json']
    # n_data, r_data = get_data_dicts(all_json_paths=all_jsons)
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # kg = KnowledgeGraph(path_to_onto=path_to_onto)
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="MAP", handle_mult_vals="ARRAY", multi_val_prop_list=["industries"])
    # kg.load_data_into_knowledge_graph(unique_node_keys=unique_node_keys, node_value_props=node_value_props, nodes_data=n_data, rels_data=r_data)
    # print("Done!")
    #################################### Load additional data from wikidata ###########################################
    # """IMPORTANT: This must be run ONLY AFTER a knowledge graph has been created and filled with data !!! """
    # path_to_onto: str = path_base.as_posix() + "/src/models/Ontologies/onto4/Ontology4.ttl"
    # print(path_to_onto)
    # kg = GraphConstruction(path_to_onto=path_to_onto)
    # kg.delete_graph()

    ## Get data from wikidata:
    # kg.import_wikidata_id()
    ################ SET industries #######################
    # industry = {"node_label": "Company",
    #             "prop_name": "LEI",
    #             "prop_wiki_id": "P1278",
    #             "new_prop_name": "industries",
    #             "new_prop_wiki_id": "P452",
    #             "use_new_prop_label": True,
    #             # new_prop usually is an id such as Q12345 -> True: prop label ("Name") is used
    #             "new_prop_is_list": True}
    # ################ SET country ############################
    # country = {"node_label": "Company",
    #            "prop_name": "LEI",
    #            "prop_wiki_id": "P1278",
    #            "new_prop_name": "country",
    #            "new_prop_wiki_id": "P17",
    #            "use_new_prop_label": True,
    #            # new_prop usually is an id such as Q12345 -> True: prop label ("Name") is used
    #            "new_prop_is_list": False}
    # ################ Set ISIN  #################################
    # isin = {"node_label": "Company",
    #         "prop_name": "LEI",
    #         "prop_wiki_id": "P1278",
    #         "new_prop_name": "ISIN",
    #         "new_prop_wiki_id": "P946",
    #         "use_new_prop_label": True,  # new_prop usually is an id such as Q12345 -> True: prop label ("Name") is used
    #         "new_prop_is_list": False}
    ##############################################################
    # wiki_data = [industry, country, isin]
    # for d in wiki_data:
    #     kg.import_data_from_wikidata(**d)
    #################  Load DBPedia data #########################
    # node_label = "Company"
    # prop_name = "wikidataID"
    # prop_dbp_id = "owl:sameAs"
    # new_prop_name = "abstract"
    # new_prop_dbp_id = "dbo:abstract"
    # new_prop_is_list: bool = False
    # kg.import_data_from_dbpedia(node_label=node_label, prop_name=prop_name, prop_dbp_id=prop_dbp_id,
    #                             new_prop_name=new_prop_name, new_prop_dbp_id=new_prop_dbp_id,
    #                             new_prop_is_list=new_prop_is_list)
    # print("Done!")
    ################# Create text embedding  ####################
    # kg.create_text_embedding(node_label="Company", node_primary_prop_name="LEI", prop_to_embed="abstract")
    # print("Done!")
