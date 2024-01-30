""" Please also read the README-models.md-file. """

"""
Parameters for Ontology4.ttl:
:param: unique_node_keys: unique_node_keys are comparable to primary keys in relational databases and are the
        node properties that must be unique. They must be provided for each node as a dictionary in the form:
        {"node_label":["node_property_name"]}. Example: {"Company":["LEI"]}
:param: node_value_props: Of the datatype properties of target nodes (i.e. Nodes that have an incoming relationship
        from a source node), one such property is used for the property of the relationship. Example in cypher:
        MATCH (s:SourceNode)-[r:Relationship]->[t:TargetNode]. If the TargetNode 't' has a quantity property 'EUR' to
        express the value of the TargetNode 't', then this property is the quantity property of the Relationship 'r'. In
        the example here, 'EUR' would be the quantity property of the Relationship 'r', if 'EUR' would be set in the
        node_value_props dictionary like so: node_value_props = {'TargetNode':'EUR'}
"""

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
