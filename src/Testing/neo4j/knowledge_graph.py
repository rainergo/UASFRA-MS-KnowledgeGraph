import os
import pathlib
from dotenv import load_dotenv

from neo4j import GraphDatabase, RoutingControl
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import FOAF, XSD, RDFS, RDF, OWL, XMLNS

from settings import path_base, path_data


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

    def load_data_with_ontology(self, unique_node_keys: dict[str:str] = None, nodes_data: list[dict] = None, rels_data: list[dict] = None, print_data_needed: bool = False):
        if nodes_data is None:
            nodes_data = {}
        if rels_data is None:
            rels_data = {}

        g = RDFGraph(path_to_onto=self.path_to_onto)
        constraint_queries, node_queries, rel_queries, nodes_data_needed, rels_data_needed = g.create_queries(unique_node_keys=unique_node_keys)

        if print_data_needed:
            print(f'The following data is needed for Nodes: \n{nodes_data_needed}')
            print(f'The following data is needed for Relationships: \n{rels_data_needed}')
            print('---------------------------------------------------------------------')

        session = self.driver.session()
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
            print('node_query:', node_query)
            res1 = session.run(node_query, parameters={'node_data': node_data})

        for rel_data in rels_data:
            rel = list(rel_data.keys())[0]
            print('rel:', rel)
            rel_query = rel_queries[rel]
            print('Rels_Query: ', rel_query)
            res2 = session.run(rel_query, parameters={'rel_data':rel_data})


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

    def create_queries(self, unique_node_keys: dict[str:str] = None):
        """ Create three types of queries: classes_and_their_props, class_relationships and namespace_queries.
        :param: unique_node_keys: unique_node_keys are comparable to primary keys in relational databases and are the
        class attributes that must be unique. They must be provided for each class as a dictionary in the form:
        {"class_label":"class_property_name"}. Example: {"Person":"name"}
        """

        nodes_data_needed = dict()
        rels_data_needed = dict()
        # print('unique_node_keys:', unique_node_keys.items())
        
        def get_nodes_and_node_props() -> dict:
            # Get classes and their DatatypeProperties
            nodes_and_nodes_props = dict()
            for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.Class)):
                for (subj2, pred2, obj2) in self.rdf_graph.triples((None, RDFS.domain, subj1)):
                    for (subj3, pred3, obj3) in self.rdf_graph.triples((subj2, RDF.type, OWL.DatatypeProperty)):
                        if not subj1 in nodes_and_nodes_props:
                            nodes_and_nodes_props[subj1] = list()
                        nodes_and_nodes_props[subj1].append(subj3)
            return nodes_and_nodes_props

        def get_relationships() -> list:
            # Get ObjectProperties (Relationships) for each Class:
            relationships = list()
            for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.ObjectProperty)):
                for (subj2, pred2, obj2) in self.rdf_graph.triples((subj1, RDFS.domain, None)):
                    for (subj3, pred3, obj3) in self.rdf_graph.triples((subj1, RDFS.range, None)):
                        relationships.append({'SOURCE': obj2, 'TARGET': obj3, 'REL': subj1})
            return relationships

        def check_if_class_keys_are_set(unique_node_keys: dict[str:str] = unique_node_keys):
            nodes_and_nodes_props = get_nodes_and_node_props()
            nodes_and_nodes_props_locals = dict()
            error_messages = list()
            for uri_class, uri_property_list in nodes_and_nodes_props.items():
                node = self.get_local_part(uri=uri_class)
                nodes_and_nodes_props_locals[node] = list()
                for prop in uri_property_list:
                    p = self.get_local_part(uri=prop)
                    nodes_and_nodes_props_locals[node].append(p)
            for node, node_props in nodes_and_nodes_props_locals.items():
                if node in unique_node_keys:
                    for prop in unique_node_keys[node]:
                        if prop in nodes_and_nodes_props_locals[node]:
                            pass
                        else:
                            error_messages.append(f'Provided key property "{prop}" is not a correct (key) property for Node "{node}"!')
                else:
                    error_messages.append(f'No key property provided for Node "{node}"!')
            if error_messages:
                raise ValueError(f'These errors must be corrected first: {error_messages}')

        def create_node_property_constraint_queries(unique_node_keys: dict[str:str] = unique_node_keys):
            contraint_queries = list()
            for node, prop_list in unique_node_keys.items():
                if prop_list:
                    query = f"""
                    CREATE CONSTRAINT constraint_for_node_{node} IF NOT EXISTS
                    FOR (node:{node}) REQUIRE ({', '.join(['node.' + prop for prop in prop_list])}) IS UNIQUE;
                    """
                    contraint_queries.append(query)
            return contraint_queries

        def create_query_template_for_classes_and_their_props() -> (list[str], set):
            # Get nodes_and_nodes_props for each Class
            nodes_and_nodes_props = get_nodes_and_node_props()
            node_queries = dict()
            # namespaces = set()
            nodes_and_key_props = dict()
            for uri_class, uri_property_list in nodes_and_nodes_props.items():
                node = self.get_local_part(uri=uri_class)
                key_properties: list = unique_node_keys[node]
                # namespaces.add(uri_class)
                props = list()
                nodes_datapoint_needed = dict()
                for prop in uri_property_list:
                    # namespaces.add(prop)
                    p = self.get_local_part(uri=prop)
                    nodes_datapoint_needed[p] = "HERE_DATA_REFERENCE"
                    if not p in key_properties:
                        props.append(f"SET n.{p} = node_data['{node}']['{p}']")
                nodes_data_needed[node] = nodes_datapoint_needed
                props.append("RETURN count(*) as total")
                s2 = ' \n\t\t\t\t'.join(props)
                s11 = ', '.join([f" {{{fprop}: node_data['{node}']['{fprop}']}} " for fprop in
                                       key_properties]) if key_properties else ''
                # s11 = f" {{{key_property}: node_data['{node}']['{key_property}']}} " if key_property is not None else ''
                # s1 = f"""
                # UNWIND $node_data AS node_data
                # MERGE (n:{node}{s11})
                # """
                s1 = f"""
                WITH $node_data AS node_data 
                MERGE (n:{node}{s11})
                """
                node_queries[node] = str(s1 + s2)
            print(nodes_data_needed)
            return node_queries, nodes_and_key_props   # namespaces

        def create_query_template_for_class_relationships(unique_node_keys: dict[str:str] = unique_node_keys):
            # Get ObjectProperties (Relationships) for each Class:
            relationships = get_relationships()
            # Build the queries:
            relationship_queries = dict()
            # namespaces = set()
            for rel in relationships:
                # namespaces.add(rel['REL'])
                relation = self.get_local_part(uri=rel['REL'])
                source = self.get_local_part(uri=rel['SOURCE'])
                target = self.get_local_part(uri=rel['TARGET'])
                rels_datapoint_needed = {'source': {f"{source}": dict()}, 'target': {f'{target}': dict()}}
                if source in unique_node_keys and unique_node_keys[source]:
                    source_keys: list = unique_node_keys[source]
                    source_properties = list()
                    for source_key in source_keys:
                        source_property = f"{source_key}: rel_data['{relation}']['source']['{source}']['{source_key}']"
                        source_properties.append(source_property)
                        rels_datapoint_needed['source'][source][source_key] = "HERE_DATA_REFERENCE"
                    source_properties = " { " + ", ".join(source_properties) + " } "
                else:
                    source_properties = ''
                if target in unique_node_keys and unique_node_keys[target]:
                    target_keys: list = unique_node_keys[target]
                    target_properties = list()
                    for target_key in target_keys:
                        target_property = f"{target_key}: rel_data['{relation}']['target']['{target}']['{target_key}']"
                        target_properties.append(target_property)
                        rels_datapoint_needed['target'][target][target_key] = "HERE_DATA_REFERENCE"
                    target_properties = " { " + ", ".join(target_properties) + " } "
                else:
                    target_properties = ''
                rels_data_needed[relation] = rels_datapoint_needed
                # query = f"""
                # UNWIND $rels_data AS rel_data
                # MATCH (source:{source}{source_properties})
                # MATCH (target:{target}{target_properties})
                # MERGE (source)-[r:{relation}]->(target)
                # RETURN count(*) as total
                # """
                query = f"""
                WITH $rel_data AS rel_data
                MATCH (source:{source}{source_properties})
                MATCH (target:{target}{target_properties})
                MERGE (source)-[r:{relation}]->(target)
                RETURN count(*) as total
                """
                relationship_queries[relation] = query
            return relationship_queries  # namespaces

        # def create_namespace_queries(namespaces: set):
        #     queries = list()
        #     namespace_prefixes = {self.get_namespace_part(uri=uri) for uri in namespaces}
        #     counter = 0
        #     for ns_prefix in namespace_prefixes:
        #         query_prefix = f"CALL n10s.nsprefixes.add('ns{counter}','{ns_prefix}');"
        #         queries.append(query_prefix)
        #         counter += 1
        #     for ns in namespaces:
        #         query = f"CALL n10s.mapping.add('{ns}', '{self.get_local_part(ns)}');"
        #         queries.append(query)
        #     return queries

        check_if_class_keys_are_set()
        constraint_queries: list = create_node_property_constraint_queries()
        node_queries, class_key_props = create_query_template_for_classes_and_their_props()
        relationship_queries = create_query_template_for_class_relationships()
        ## namespaces = class_namespaces.union(relationship_namespaces)
        ## namespace_queries = create_namespace_queries(namespaces=namespaces)
        # print(f'The following data is needed for Nodes: \n{nodes_data_needed}')
        # print(f'The following data is needed for Relationships: \n{rels_data_needed}')
        return constraint_queries, node_queries, relationship_queries, nodes_data_needed, rels_data_needed

    def load_data_with_ontology(self):
        pass


if __name__ == '__main__':
    # unique_node_keys = {"Asset": ["assetName"],
    #                      "Company": ['name', 'LEI', 'year'],
    #                      "FromFossileSources": ['name'],
    #                      "FromNuclearSources": ['name'],
    #                      'GHGEmission': ['name'],
    #                      'Pollution': ['name']
    # }
    # unique_node_keys = {"Asset": ["name"],
    #                      "Biodiversity": ["name"],
    #                      "Company": ["name"],
    #                      "FromFossiles": ["name"],
    #                      "FromRenewables": ["name"],
    #                      "GHGEmission": ["name", "tonsCO2Eq"],
    #                      "Pollution": ["tons", "name"]}

    unique_node_keys = {"Event": ["eventId"],
                         "Station": ["stationCode"]}

    # nodes_data = [{'Asset': {'EUR': '100', 'assetName': 'ASS1'}, 'Asset': {'EUR': '100', 'assetName': 'ASS2'}}]
    nodes_data = [
                  {'Event': {'eventDescription': 'EvDe1', 'eventId': 'Ev1', 'eventType': 'EvTy1', 'timestamp': '2022-02-02:02:02'}},
                  {'Station': {'lat': 21.3, 'long': 22.4, 'stationAddress': 'Adress1', 'stationCode': 'St1', 'stationName': 'StNa1'}},
                  {'Station': {'lat': 44.8, 'long': 65.9, 'stationAddress': 'Adress2', 'stationCode': 'St2', 'stationName': 'StNa2'}}
                  ]

    rels_data = [
                 {'affects': {'source': {'Event': {'eventId': 'Ev1'}}, 'target': {'Station': {'stationCode': 'St1'}}}},
                 {'link': {'source': {'Station': {'stationCode': 'St1'}}, 'target': {'Station': {'stationCode': 'St2'}}}}
                 ]

    # rels_data = [{'consumes': {'source': {'Asset': {'assetName': 'ASS1'}}, 'target': {'EnergyConsumption': {}}}, 'disposes': {'source': {'FromNuclearSources': {'MWh': '45'}}, 'target': {'NuclearWaste': {'tons': '421'}}}, 'emits': {'source': {'Asset': {'assetName': 'ASS1'}}, 'target': {'Scope1': {'tonsCO2eq': '1234'}}}, 'forPeriod': {'source': {'EnvironmentalFootprint': {}}, 'target': {'ReportingPeriod': {'year': '2022'}}}, 'indirectlyEmits': {'source': {'FromFossileSources': {'MWh': '467'}}, 'target': {'Scope2': {'tonsCO2eq': '225'}}}, 'owns': {'source': {'Company': {'companyLEI': '123', 'reportingPeriod': '2022'}}, 'target': {'Asset': {'assetName': 'ASS1'}}}}]

    ######################################
    # kg = KnowledgeGraph()
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    # # path_to_onto: str = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session4/ontos/movies-onto.ttl"
    # # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/rail.ttl"
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology5.ttl"
    # kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False, load_onto_only=True)
    # print('Done!')
    ########################################
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/rail.ttl"
    # kg = KnowledgeGraph(path_to_onto=path_to_onto)
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    # kg.load_data_with_ontology(unique_node_keys=unique_node_keys, nodes_data=nodes_data, rels_data=rels_data)
    # print("Done!")
    ########################################
    path_to_onto: str = path_base.as_posix() + "/models/Ontologies/rail.ttl"
    g = RDFGraph(path_to_onto=path_to_onto)
    # g.create_queries(unique_node_keys=unique_node_keys)
    constr_queries, c_queries, rel_queries, nodes_data_needed, rels_data_needed = g.create_queries(unique_node_keys=unique_node_keys)
    print('CONSTRAINT_QUERIES:')
    for item00 in constr_queries:
        print(item00)
    print('-----')
    print('NODE_QUERIES:')
    for key, val in c_queries.items():
        print(key, val)
        print('-----')
    print('RELATIONSHIP_QUERIES:')
    for key2,val2 in rel_queries.items():
        print(key2, val2)
    print('-----')
    # print('NODES_DATA_NEEDED:')
    # print(nodes_data_needed)
    # print('------')
    # print('RELS_DATA_NEEDED:')
    # print(rels_data_needed)
