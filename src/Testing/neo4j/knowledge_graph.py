import os
import pathlib
from dotenv import load_dotenv

from neo4j import GraphDatabase, RoutingControl
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD, RDFS, RDF, OWL, XMLNS

from settings import path_base, path_data


class KnowledgeGraph:

    def __init__(self):
        path_to_secrets: pathlib.Path = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        auth = ("neo4j", os.getenv('NEO4J_PW'))
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.path_to_onto: str = pathlib.Path(path_base, 'models', 'Ontologies', 'Ontology4.ttl').as_posix()

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

    def load_onto_or_rdf(self, path: str, path_is_url: bool = False,
                         load_onto_only: bool = True, serialization_type: str = "Turtle"):
        query_load = f"""
        CALL n10s.{'onto' if load_onto_only else 'rdf'}.import.fetch("{("file:///" if not path_is_url else "") + path}", 
        "{serialization_type}")
        """
        self.driver.execute_query(query_=query_load)

    def import_data_from_wikidata(self):
        pass

    def load_data_with_ontology(self, unique_class_keys: dict[str:str] = None, nodes_data: list[dict] = None, rels_data: list[dict] = None):
        # nodes_data = [{"eventId": 1, "eventDescription": "Event 1", "eventType": "type1", "timestamp": "timestamp1", "stationCode": 11, "lat": 123, "long": 321, "stationAddress": "Penny Lane 12", "stationName": "Main Station"},
        #                                  {"eventId": 2, "eventDescription": "Event 2", "eventType": "type2", "timestamp": "timestamp2", "stationCode": 22, "lat": 456, "long": 654, "stationAddress": "Oxford Street 10", "stationName": "Zoo Station"}]
        #
        # rels_data = [{"affects_source_eventId": 1, "affects_target_stationCode": 11},
        #              {"affects_source_eventId": 2, "affects_target_stationCode": 22},
        #              {"link_source_stationCode": 11, "link_target_stationCode": 22}]
        if nodes_data is None:
            nodes_data = {}
        if rels_data is None:
            rels_data = {}

        g = RDFGraph(path_to_onto=self.path_to_onto)
        class_queries, rel_queries, ns_queries = g.create_queries(unique_class_keys=unique_class_keys)
        session = self.driver.session()
        # for ns_query in ns_queries:
        #     session.run(ns_query)
        for node_data in nodes_data:
            for cl_query in class_queries:
                print('Class_Query: ', cl_query)
                res1 = session.run(cl_query, parameters={f'nodes_data': node_data})
        for rel_data in rels_data:
            for rel_query in rel_queries:
                print('Rels_Query: ', rel_data)
                res2 = session.run(rel_query, parameters={'rels_data': rel_data})


class RDFGraph:

    def __init__(self, path_to_onto: str, rdf_format: str = "ttl"):
        self.rdf_graph: Graph = Graph()
        try:
            self.rdf_graph.parse(path_to_onto, format=rdf_format)
        except:
            print('rdf_graph could not be parsed!')

    def get_local_part(self, uri: str):
        pos = -1
        pos = uri.rfind('#')
        if pos < 0:
            pos = uri.rfind('/')
        if pos < 0:
            pos = uri.rindex(':')
        return uri[pos + 1:]

    def get_namespace_part(self, uri: str):
        pos = -1
        pos = uri.rfind('#')
        if pos < 0:
            pos = uri.rfind('/')
        if pos < 0:
            pos = uri.rindex(':')
        return uri[0:pos + 1]

    def create_queries(self, unique_class_keys: dict[str:str] = None):
        """ Create three types of queries: classes_and_their_props, class_relationships and namespace_queries.
        :param: unique_class_keys: unique_class_keys are comparable to primary keys in relational databases and are the
        class attributes that must be unique. They must be provided as a dictionary in the form:
        {"class_label":"class_property_name"}. Example: {"Person":"name"}
        """

        nodes_data_needed = list()
        rels_data_needed = list()

        def create_query_template_for_classes_and_their_props(unique_class_keys: dict[str:str]) -> (list[str], set):
            if unique_class_keys is None:
                unique_class_keys = dict()
            # Get data_properties for each Class
            data_properties = dict()
            for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.Class)):
                for (subj2, pred2, obj2) in self.rdf_graph.triples((None, RDFS.domain, subj1)):
                    for (subj3, pred3, obj3) in self.rdf_graph.triples((subj2, RDF.type, OWL.DatatypeProperty)):
                        if not subj1 in data_properties:
                            data_properties[subj1] = list()
                        data_properties[subj1].append(subj3)
            class_queries = list()
            namespaces = set()
            nodes_and_key_props = dict()
            for uri_class, uri_property_list in data_properties.items():
                key_property = None
                node = self.get_local_part(uri=uri_class)
                namespaces.add(uri_class)
                props = list()
                for prop in uri_property_list:
                    namespaces.add(prop)
                    p = self.get_local_part(uri=prop)
                    nodes_data_needed.append({node: p})
                    if node in unique_class_keys and p == unique_class_keys[node]:
                        key_property = p
                        nodes_and_key_props[node] = key_property
                    else:
                        props.append(f"SET n.{p} = nodes_data['{p}']")
                props.append("RETURN count(*) as total")
                s2 = ' \n\t\t\t'.join(props)
                s11 = f" {{{key_property}: nodes_data['{key_property}']}} " if key_property is not None else ''
                s1 = f"""
                UNWIND $nodes_data AS nodes_data
                MERGE (n:{node}{s11})
                """
                class_queries.append(s1 + s2)
            return class_queries, nodes_and_key_props, namespaces

        def create_query_template_for_class_relationships(nodes_and_key_props: dict):
            # Get ObjectProperties (Relationships) for each Class:
            relationships = list()
            for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.ObjectProperty)):
                for (subj2, pred2, obj2) in self.rdf_graph.triples((subj1, RDFS.domain, None)):
                    for (subj3, pred3, obj3) in self.rdf_graph.triples((subj1, RDFS.range, None)):
                        relationships.append({'SOURCE': obj2, 'TARGET': obj3, 'REL': subj1})
            # Build the queries:
            relationship_queries = list()
            namespaces = set()
            for rel in relationships:
                namespaces.add(rel['REL'])
                relation = self.get_local_part(uri=rel['REL'])
                source = self.get_local_part(uri=rel['SOURCE'])
                target = self.get_local_part(uri=rel['TARGET'])
                if source in nodes_and_key_props:
                    source_key = nodes_and_key_props[source]
                    source_key_part = f" {{ {source_key}: rels_data['{relation}_source_{source_key}'] }}"
                    rels_data_needed.append({relation: f'{relation}_source_{source_key}'})
                else:
                    source_key_part = ''
                if target in nodes_and_key_props:
                    target_key = nodes_and_key_props[target]
                    target_key_part = f" {{ {target_key}: rels_data['{relation}_target_{target_key}'] }}"
                    rels_data_needed.append({relation: f'{relation}_target_{target_key}'})
                else:
                    target_key_part = ''
                query = f"""
                UNWIND $rels_data AS rels_data
                MATCH (source: {source}{source_key_part})
                MATCH (target: {target}{target_key_part})
                MERGE (source)-[r:{relation}]->(target)
                RETURN count(*) as total
                """
                relationship_queries.append(query)
            return relationship_queries, namespaces

        def create_namespace_queries(namespaces: set):
            queries = list()
            namespace_prefixes = {self.get_namespace_part(uri=uri) for uri in namespaces}
            counter = 0
            for ns_prefix in namespace_prefixes:
                query_prefix = f"CALL n10s.nsprefixes.add('ns{counter}','{ns_prefix}');"
                queries.append(query_prefix)
                counter += 1
            for ns in namespaces:
                query = f"CALL n10s.mapping.add('{ns}', '{self.get_local_part(ns)}');"
                queries.append(query)
            return queries

        class_queries, class_key_props, class_namespaces = create_query_template_for_classes_and_their_props(
            unique_class_keys=unique_class_keys)
        relationship_queries, relationship_namespaces = create_query_template_for_class_relationships(nodes_and_key_props=class_key_props)
        namespaces = class_namespaces.union(relationship_namespaces)
        namespace_queries = create_namespace_queries(namespaces=namespaces)
        print(f'The following data is needed for Nodes: \n{nodes_data_needed}')
        print(f'The following data is needed for Relationships: \n{rels_data_needed}')
        return class_queries, relationship_queries, namespace_queries

    def load_data_with_ontology(self):
        pass


if __name__ == '__main__':
    # kg = KnowledgeGraph()
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    # # path_to_onto: str = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session4/ontos/movies-onto.ttl"
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False, load_onto_only=True)
    # print('Done!')
    ########################################
    kg = KnowledgeGraph()
    # unique_class_keys = {"Event": "eventId", "Station": "stationCode"}
    unique_class_keys = {"Company": "LEI"}
    nodes_data = [{'LEI': 123, "companyName": "BMW", 'reportingPeriod': "2023-01-01", "BaselineValue": 555, "BaselineYear": 2015}]
    rels_data = [{}]
    kg.load_data_with_ontology(unique_class_keys=unique_class_keys, nodes_data=nodes_data)
    ########################################
    # kg = KnowledgeGraph()
    # path_to_onto = kg.path_to_onto
    # g = RDFGraph(path_to_onto=path_to_onto)
    # class_queries, namespaces_classes = g.create_query_template_for_classes_and_their_props()
    # for node in class_queries:
    #     print(node)
    # for namespace in namespaces_classes:
    #     print(namespace)
    # print('------------------')
    # rels_queries, namespaces_rels = g.create_query_template_for_class_relationships()
    # for query in rels_queries:
    #     print(query)
    # for ns in namespaces_rels:
    #     print(ns)
    # print('--------------')
    # unique_class_keys = {"Event": "eventId", "Station": "stationCode"}
    # unique_class_keys = {}
    # c_queries, rel_queries, ns_queries = g.create_queries(unique_class_keys=unique_class_keys)
    # for item in rel_queries:
    #     print(item)
    # print(' '.join(c_queries))
