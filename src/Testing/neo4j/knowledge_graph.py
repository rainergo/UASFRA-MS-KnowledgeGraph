import os
import pathlib
import json
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

    def load_data_with_ontology(self, unique_node_keys: dict[str:str] = None, node_value_props: dict[str:str] = None,
                                all_data: list[dict] = None):
        # if nodes_data is None:
        #     nodes_data = {}
        # if rels_data is None:
        #     rels_data = {}

        g = RDFGraph(path_to_onto=self.path_to_onto)
        constraint_queries, node_queries, rel_queries, ns_queries = g.create_queries(
            unique_node_keys=unique_node_keys, node_value_props=node_value_props)

        session = self.driver.session()

        print('Namespace_Queries:')
        for ns_query in ns_queries:
            print('ns_query:', ns_query)
            session.run(ns_query)

        for constraint_query in constraint_queries:
            print('Constraint_Query: ', constraint_query)
            res0 = session.run(constraint_query)

        # for node_data in nodes_data:
        #     node = list(node_data.keys())[0]
        #     print('node:', node)
        #     node_query = node_queries[node]
        #     print('Node_Query:', node_query)
        #     res1 = session.run(node_query, parameters={'node_data': node_data})

        # for rel_data in rels_data:
        #     rel = list(rel_data.keys())[0]
        #     print('rel:', rel)
        #     rel_query = rel_queries[rel]
        #     print('Rels_Query: ', rel_query)
        #     res2 = session.run(rel_query, parameters={'rel_data': rel_data})

        all_queries = node_queries | rel_queries

        for data in all_data:
            rel_or_node = list(data.keys())[0]
            print('Relation/Node:', rel_or_node)
            query = all_queries[rel_or_node]
            print('Query: ', query)
            res2 = session.run(query, parameters={'data': data})


class RDFGraph:

    def __init__(self, path_to_onto: str, rdf_format: str = "ttl"):
        self.rdf_graph: Graph = Graph()
        self.nodes_data_needed = dict()
        self.rels_data_needed = dict()
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

    def get_nodes_and_node_props(self) -> tuple[dict, list]:
        # Get classes and their DatatypeProperties
        nodes_with_props = dict()
        all_nodes = list()
        for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.Class)):
            all_nodes.append(self.get_local_part(subj1))
            for (subj2, pred2, obj2) in self.rdf_graph.triples((None, RDFS.domain, subj1)):
                for (subj3, pred3, obj3) in self.rdf_graph.triples((subj2, RDF.type, OWL.DatatypeProperty)):
                    node = self.get_local_part(subj1)
                    if not node in nodes_with_props:
                        nodes_with_props[node] = list()
                    nodes_with_props[node].append(self.get_local_part(subj3))
        nodes_without_props = [key for key in all_nodes if key not in nodes_with_props]
        return nodes_with_props, nodes_without_props

    def get_relationships(self) -> list:
        # Get ObjectProperties (Relationships) for each Class:
        relationships = list()
        for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.ObjectProperty)):
            for (subj2, pred2, obj2) in self.rdf_graph.triples((subj1, RDFS.domain, None)):
                for (subj3, pred3, obj3) in self.rdf_graph.triples((subj1, RDFS.range, None)):
                    relationships.append({'SOURCE': self.get_local_part(obj2), 'TARGET': self.get_local_part(obj3),
                                          'REL': self.get_local_part(subj1)})
        return relationships

    def get_namespaces(self) -> set:
        namespaces = set()
        for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.Class)):
            for (subj2, pred2, obj2) in self.rdf_graph.triples((None, RDFS.domain, subj1)):
                for (subj3, pred3, obj3) in self.rdf_graph.triples((subj2, RDF.type, OWL.DatatypeProperty)):
                    namespaces.add(subj1)
                    namespaces.add(subj3)
        for (subj11, pred11, obj11) in self.rdf_graph.triples((None, RDF.type, OWL.ObjectProperty)):
            namespaces.add(subj11)
        return namespaces

    def create_queries(self, unique_node_keys: dict[str:str] = None, node_value_props: dict[str:str] = None):
        """ Create three types of queries: classes_and_their_props, class_relationships and namespace_queries.
        :param: unique_node_keys: unique_node_keys are comparable to primary keys in relational databases and are the
        class attributes that must be unique. They must be provided for each class as a dictionary in the form:
        {"class_label":["class_property_name"]}. Example: {"Person":["name"]}
        :param: node_value_props: ToDo: Explain what they are and why needed
        """
        if unique_node_keys is None or node_value_props is None:
            raise ValueError("Either 'unique_node_keys' or 'node_value_props' or both are not provided!")

        def check_if_class_keys_are_set():
            nodes_and_nodes_props, nodes_without_props = self.get_nodes_and_node_props()
            error_messages = list()
            for node, node_props in nodes_and_nodes_props.items():
                if node in unique_node_keys:
                    if not unique_node_keys[node]:
                        error_messages.append(f'No key property provided for Node "{node}" in unique_node_keys.')
                    for prop in unique_node_keys[node]:
                        if prop in nodes_and_nodes_props[node]:
                            pass
                        else:
                            error_messages.append(
                                f'Provided key property "{prop}" is not a correct (key) property for Node "{node}"!')
                else:
                    error_messages.append(f'No key property provided for Node "{node}"!')
            if error_messages:
                raise ValueError(f'These errors must be corrected first: {error_messages}')

        def check_if_node_value_props_are_set():
            # Get target Nodes:
            targets: list = [rel["TARGET"] for rel in self.get_relationships()]
            node_and_node_props, nodes_without_props = self.get_nodes_and_node_props()
            nodes_without_props_in_targets = [item for item in targets if item in nodes_without_props]
            if nodes_without_props_in_targets:
                raise ValueError(
                    f'These target Nodes have no properties. Thus relation values cannot be set: {nodes_without_props_in_targets}')

            node_value_props_missing = [item for item in targets if item not in node_value_props]
            if node_value_props_missing:
                raise ValueError(f'node_value_props not set for these target Nodes: {node_value_props_missing}')

            node_value_props_incorrect = list()
            for node in targets:
                node_props: list = node_and_node_props[node]
                node_prop = node_value_props[node]
                if node_prop not in node_props:
                    node_value_props_incorrect.append(
                        f"Provided Node property '{node_prop}' is not valid for Node '{node}'!")
            if node_value_props_incorrect:
                raise ValueError(f'Please check these errors: {node_value_props_incorrect}')

        def create_node_property_constraint_queries():
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
            nodes_and_nodes_props, nodes_without_props = self.get_nodes_and_node_props()
            node_queries = dict()
            for node, node_props in nodes_and_nodes_props.items():
                key_properties: list = unique_node_keys[node]
                if node in node_value_props:
                    value_properties: list = node_value_props[node]
                else:
                    value_properties: list = list()
                props_queries = list()
                nodes_datapoint_needed = dict()
                for prop in node_props:
                    if prop not in value_properties:
                        nodes_datapoint_needed[prop] = f"<HERE_{prop}_VALUE>"
                        if prop not in key_properties:
                            props_queries.append(f'SET n.{prop} = data["{node}"]["{prop}"]')
                self.nodes_data_needed[node] = nodes_datapoint_needed
                props_queries.append("RETURN count(*) as total")
                query_part_2 = ' \n\t\t\t\t'.join(props_queries)
                additional_query_part_1 = ' { ' + ', '.join(
                    [f"{key_prop}: data['{node}']['{key_prop}']" for key_prop in
                     key_properties]) + ' } ' if key_properties else ''
                query_part_1 = f"""
                WITH $data AS data 
                MERGE (n:{node}{additional_query_part_1})
                """
                node_queries[node] = str(query_part_1 + query_part_2)
            return node_queries

        def create_query_template_for_class_relationships():
            # Get ObjectProperties (Relationships) for each Class:
            relationships = self.get_relationships()
            # Build the queries:
            relationship_queries = dict()
            for rel in relationships:
                source = rel['SOURCE']
                target = rel['TARGET']
                relation_only = rel['REL']
                relation = f"{source}_{rel['REL']}_{target}"
                rels_datapoint_needed = {"source": {f"{source}": dict()}, "target": {f"{target}": dict()}}
                # Data for source:
                if source in unique_node_keys and unique_node_keys[source]:
                    source_keys: list = unique_node_keys[source]
                    source_properties = list()
                    for source_key in source_keys:
                        source_property = f'{source_key}: data["{relation}"]["source"]["{source}"]["{source_key}"]'
                        source_properties.append(source_property)
                        rels_datapoint_needed['source'][source][source_key] = f"<HERE_{source_key}_VALUE>"
                    source_properties = " { " + ", ".join(source_properties) + " } "
                else:
                    source_properties = ''
                # Data for target:
                relation_property = None
                if target in unique_node_keys and unique_node_keys[target]:
                    target_keys: list = unique_node_keys[target]
                    target_properties = list()
                    for target_key in target_keys:
                        target_property = f'{target_key}: data["{relation}"]["target"]["{target}"]["{target_key}"]'
                        target_properties.append(target_property)
                        rels_datapoint_needed['target'][target][target_key] = f"<HERE_{target_key}_VALUE>"
                    target_properties = " { " + ", ".join(target_properties) + " } "
                else:
                    target_properties = ''

                """
                IMPORTANT:
                Data for relationship: Please note, that the values for the target will be stored in the relationship.
                For instance: (source:Company)-[r:emits]->(target:Scope1 {name:Scop1TotalGHGEmissions}), then the value
                for Scop1TotalGHGEmissions will be stored in the relationship: r:emits {value: <Value for Scop1TotalGHGEmissions>}, i.e. 
                the query will be: (source:Company)-[r:emits {value: <Value for Scop1TotalGHGEmissions>}]->(target:Scope1 {name:Scop1TotalGHGEmissions})
                """
                # Data for relationship:
                if target in node_value_props:
                    value_prop = node_value_props[target]
                    relation_property = f' {{ {value_prop}: data["{relation}"]["target"]["{target}"]["{value_prop}"] }}'
                    rels_datapoint_needed["target"][target][value_prop] = f"<HERE_{value_prop}_VALUE>"
                self.rels_data_needed[relation] = rels_datapoint_needed
                query = f"""
                WITH $data AS data
                MATCH (source:{source}{source_properties})
                MATCH (target:{target}{target_properties})
                MERGE (source)-[r:{relation_only}{relation_property}]->(target)
                RETURN count(*) as total
                """
                relationship_queries[relation] = query
            return relationship_queries

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

        check_if_class_keys_are_set()
        check_if_node_value_props_are_set()
        constraint_queries: list = create_node_property_constraint_queries()
        node_queries = create_query_template_for_classes_and_their_props()
        relationship_queries = create_query_template_for_class_relationships()
        namespaces = self.get_namespaces()
        namespace_queries = create_namespace_queries(namespaces=namespaces)

        return constraint_queries, node_queries, relationship_queries, namespace_queries

    def create_json_files_for_data_needed(self):
        # if len(self.nodes_data_needed) == 0 or len(self.rels_data_needed):
        #     raise ValueError("Please run 'create_queries()'-method first !")
        for k1, v1 in self.nodes_data_needed.items():
            with open(f'./jsons/{k1}.json', 'w') as file:
                d1 = {k1: v1}
                json.dump(d1, file)
        for k2, v2 in self.rels_data_needed.items():
            with open(f'./jsons/{k2}.json', 'w') as file:
                d2 = {k2: v2}
                json.dump(d2, file)


if __name__ == '__main__':
    # ## transport.ttl
    # unique_node_keys = {"transportFromGolgiToPlasma": ["transportProperty"]
    #                     }

    ## Ontology4.ttl:
    unique_node_keys = {"NuclearWaste": ["period", "label"],
                        "Energy": ["period", "label"],
                        "EnergyFromNuclearSources": ["period", "label"],
                        "EnergyFromFossileSources": ["period", "label"],
                        "GHGEmission": ["period", "label"],
                        "Scope1": ["period", "label"],
                        "Scope2": ["period", "label"],
                        "Scope3": ["period", "label"],
                        "Pollution": ["period", "label"],
                        "Company": ["LEI"],
                        }
    node_value_props = {"NuclearWaste": "tons",
                        "Energy": "MWh",
                        "EnergyFromNuclearSources": "MWh",
                        "EnergyFromFossileSources": "MWh",
                        "GHGEmission": "tonsCO2Eq",
                        "Scope1": "tonsCO2Eq",
                        "Scope2": "tonsCO2Eq",
                        "Scope3": "tonsCO2Eq",
                        "Pollution": "tons",
                        }
    # Adidas = [
    #         {"Company": {"LEI": "549300JSX0Z4CW0V5023", "label": "Adidas"}},
    #         {"Scope1": {"label": "Scope1TotalGHGEmissions", "period": "2022"}},
    #         {"Company_emits_Scope1": {"source": {"Company": {"LEI": "549300JSX0Z4CW0V5023"}}, "target": {
    #         "Scope1": {"period": "2022", "label": "Scope1TotalGHGEmissions", "tonsCO2Eq": "2.384"}}}}
    # ]
    Adidas = [{'Company': {'LEI': '549300JSX0Z4CW0V5023', 'label': 'Adidas'}}, {'Scope1': {'label': 'GrossScope1GHGEmissions', 'period': '2022'}}, {'Scope2': {'label': 'GrossLocationBasedScope2GHGEmissions', 'period': '2022'}}, {'Scope2': {'label': 'GrossMarketBasedScope2GHGemissions', 'period': '2022'}}, {'Scope3': {'label': 'GrossScope3GHGEmissions', 'period': '2022'}}, {'Company_emits_Scope1': {'source': {'Company': {'LEI': '549300JSX0Z4CW0V5023'}}, 'target': {'Scope1': {'period': '2022', 'label': 'GrossScope1GHGEmissions', 'tonsCO2Eq': 11.11}}}}, {'Company_emits_Scope2': {'source': {'Company': {'LEI': '549300JSX0Z4CW0V5023'}}, 'target': {'Scope2': {'period': '2022', 'label': 'GrossLocationBasedScope2GHGEmissions', 'tonsCO2Eq': 22.11}}}}, {'Company_emits_Scope2': {'source': {'Company': {'LEI': '549300JSX0Z4CW0V5023'}}, 'target': {'Scope2': {'period': '2022', 'label': 'GrossMarketBasedScope2GHGemissions', 'tonsCO2Eq': 22.22}}}}, {'Company_emits_Scope3': {'source': {'Company': {'LEI': '549300JSX0Z4CW0V5023'}}, 'target': {'Scope3': {'period': '2022', 'label': 'GrossScope3GHGEmissions', 'tonsCO2Eq': 33.11}}}}]
    BASF = [{'Company': {'LEI': '529900PM64WH8AF1E917', 'label': 'BASF'}}, {'Scope1': {'label': 'GrossScope1GHGEmissions', 'period': '2022'}}, {'Scope2': {'label': 'GrossLocationBasedScope2GHGEmissions', 'period': '2022'}}, {'Scope2': {'label': 'GrossMarketBasedScope2GHGemissions', 'period': '2022'}}, {'Scope3': {'label': 'GrossScope3GHGEmissions', 'period': '2022'}}, {'Company_emits_Scope1': {'source': {'Company': {'LEI': '529900PM64WH8AF1E917'}}, 'target': {'Scope1': {'period': '2022', 'label': 'GrossScope1GHGEmissions', 'tonsCO2Eq': 11.11}}}}, {'Company_emits_Scope2': {'source': {'Company': {'LEI': '529900PM64WH8AF1E917'}}, 'target': {'Scope2': {'period': '2022', 'label': 'GrossLocationBasedScope2GHGEmissions', 'tonsCO2Eq': 22.11}}}}, {'Company_emits_Scope2': {'source': {'Company': {'LEI': '529900PM64WH8AF1E917'}}, 'target': {'Scope2': {'period': '2022', 'label': 'GrossMarketBasedScope2GHGemissions', 'tonsCO2Eq': 22.22}}}}, {'Company_emits_Scope3': {'source': {'Company': {'LEI': '529900PM64WH8AF1E917'}}, 'target': {'Scope3': {'period': '2022', 'label': 'GrossScope3GHGEmissions', 'tonsCO2Eq': 33.11}}}}]




    # ## rail.ttl:
    # unique_node_keys = {"Event": ["eventId"],
    #                      "Station": ["stationCode"]}
    # nodes_data = [
    #               {'Event': {'eventDescription': 'EvDe1', 'eventId': 'Ev1', 'eventType': 'EvTy1', 'timestamp': '2022-02-02:02:02'}},
    #               {'Station': {'lat': 21.3, 'long': 22.4, 'stationAddress': 'Adress1', 'stationCode': 'St1', 'stationName': 'StNa1'}},
    #               {'Station': {'lat': 44.8, 'long': 65.9, 'stationAddress': 'Adress2', 'stationCode': 'St2', 'stationName': 'StNa2'}}
    #               ]
    #
    # rels_data = [
    #              {'affects': {'source': {'Event': {'eventId': 'Ev1'}}, 'target': {'Station': {'stationCode': 'St1'}}}},
    #              {'link': {'source': {'Station': {'stationCode': 'St1'}}, 'target': {'Station': {'stationCode': 'St2'}}}}
    #              ]

    ######################################
    # path_to_onto: str = "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session4/ontos/movies-onto.ttl"
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/rail.ttl"
    path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    kg = KnowledgeGraph(path_to_onto=path_to_onto)
    kg.delete_graph()
    kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False, load_onto_only=True)
    print('Done!')
    ########################################
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # kg = KnowledgeGraph(path_to_onto=path_to_onto)
    # # kg.delete_graph()
    # # kg.init_graph(handle_vocab_uris="MAP", handle_mult_vals="OVERWRITE")
    # kg.load_data_with_ontology(unique_node_keys=unique_node_keys, node_value_props=node_value_props, all_data=BASF)
    # print("Done!")
    ########################################
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # g = RDFGraph(path_to_onto=path_to_onto)
    # nodes_and_props, nodes_without_props = g.get_nodes_and_node_props()
    # print('Nodes with props:\n', len(nodes_and_props),"\n", nodes_and_props)
    # print('---------')
    # print('Nodes without props:\n', len(nodes_without_props), "\n", nodes_without_props)
    # print('---------')
    # relationships = g.get_relationships()
    # print('Relationships:\n', len(relationships),"\n", relationships)
    # print('---------')
    ######################################
    # path_to_onto: str = path_base.as_posix() + "/models/Ontologies/Ontology4.ttl"
    # g = RDFGraph(path_to_onto=path_to_onto)
    # # g.create_queries(unique_node_keys=unique_node_keys)
    # constr_queries, c_queries, rel_queries, ns_queries, = g.create_queries(unique_node_keys=unique_node_keys,
    #                                                                        node_value_props=node_value_props)
    # print('CONSTRAINT_QUERIES:')
    # for item000 in constr_queries:
    #     print(item000)
    # print('-----')
    # print('NAMESPACE_QUERIES:')
    # for item00 in ns_queries:
    #     print(item00)
    # print('-----')
    # print('NODE_QUERIES:')
    # for key, val in c_queries.items():
    #     print(key, val)
    #     print('-----')
    # print('RELATIONSHIP_QUERIES:')
    # for key, val in rel_queries.items():
    #     print(key)
    #     print(val)
    # print('-----')
    # print('NODES_DATA_NEEDED:')
    # print(g.nodes_data_needed)
    # print('------')
    # print('RELS_DATA_NEEDED:')
    # print(g.rels_data_needed)
    # g.create_json_files_for_data_needed()
