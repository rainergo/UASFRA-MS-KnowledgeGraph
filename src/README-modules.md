## INFO
This README explains the logic and some implementation details of the individual modules.

 ---
### A_read_xbrl.py:
###### The module is used for converting data in XBRL-files into standardized JSON-files that later can be used to populate a Knowledge Graph. The parameter for the only method "read_xbrl_to_json()" of the class XBRL is a Python Enum named "XHTMLName". This enum contains the names of the XHTML-files in the "reports"-folder, where all XHTML-files of XBRL-packages must be stored. Please refer to the README-data.md-file in the "/src/data/" directory. If reports are added there, their file names must also be added in this "XHTMLName"-Enum.

 ---
### B_rdf_graph.py:
###### The module primarily uses the Python [rdflib](https://rdflib.readthedocs.io/en/stable/) library. The class RDFGraph and its method fulfill three primary functions:
    1) read the triples from the ontology-file into a graph: Method -> "rdf_graph.parse()" at instantiation
    2) create JSON-files for the "data_needed"-folder: Method -> "create_json_files_for_data_needed()"
    3) create cypher "data import"-query-templates: Method -> "create_query_templates()"

###### The class at instantiation needs a path to an ontology-file in Turtle-format, in our case the "Ontology4.ttl"-file. In addition, the methods also need the following Python dictionaries which, for the provided ontology, are currently located in "/src/models/Ontologies/onto4/params.py":
    - unique_node_keys
    - node_value_props
    
###### Please refer to the README-models.md-file for further details. 
###### The results of the relevant methods of the class are printed if the module's main method is executed. 
###### In these query templates, there are lines such as:

    - WITH $node_data AS node_data ...
    - WITH $rel_data AS rel_data ...

###### There, the "$node_data" or "$rel_data" refer to the dictionaries created in the "get_data_dicts()"-method of the module "C_read_data.py". The Cypher command "WITH" loads this dictionary data into memory.

 ---
### C_read_data.py:
###### The module's only method "get_data_dicts()" reads the JSON-files in "src/data/JSONs/" into Python dictionaries. These dictionaries are passed as parameters to the "load_data_into_knowledge_graph()"-method of the module "D_graph_construction.py" to populate the knowledge graph. Please refer to the "README-models.md"-file.

 ---
### D_graph_construction.py:
###### The module has two primary responsibilities:
    1) construct the NEO4j Knowledge Graph ("KG"): 
        Methods:
            -> init_graph()
            -> load_onto_or_rdf()
    2) load data into the NEO4J Knowledge Graph ("KG"):
        Methods:
            -> load_data_into_knowledge_graph()
            -> import_data_from_wikidata() 
                -> Please note: In order to import the data, the method "import_wikidata_id()" must be run before.
            -> import_data_from_dbpedia()
            -> create_text_embedding()

init_graph()
###### This method sets all basic KG configurations. Please refer to the NEO4J neosemantics [documentation](https://neo4j.com/labs/neosemantics/4.0/config/) for ontology-related settings. 

load_onto_or_rdf()
###### This method imports the provided ontology into a NEO4J KG and creates the KG schema. 
###### After executing both methods, "init_graph()" and "load_onto_or_rdf()", the KG schema (without data) can be displayed in the browser with the url "localhost:7474": [NEO4J in browser](http://localhost:7474)

load_data_into_knowledge_graph()
###### This method loads the data from the JSON-files in "/src/data/JSONs/" into the KG as previously discussed and also laid out in the README-data.md and README-models.md-files.

import_data_from_wikidata() 
###### This method imports external data from wikidata into the KG via SPARQL queries.  
###### In most cases, only some of the seven parameters need to be provided:
    Default parameters that most often are left untouched:
        - node_label: The label of the Node where properties shall be stored. Mostly this is "Company"
        - prop_name: The Node property in wikidata. For Node "Company" this is "LEI"
        - prop_wiki_id: The wikidata-id for the above Node property. For "LEI", this is "P1278"
    Parameters that must be set:
        - new_prop_name: The name of the new property from wikidata such as "country" or "ISIN"
        - new_prop_wiki_id: The wikidata-id for the new data such as "P17" for "country" or "P946" for "ISIN"
        - use_new_prop_label: Bool if the new wikidata data or its label shall be used. For "country" the label would be the name of the country (i.e. "Germany"), the data itself is another wikidata-id such as "Q183" (for the country "Germany")
        - new_prop_is_list: Bool if new wikidata data are multiple items or just one item

import_data_from_dbpedia()
###### This method imports external data from dbpedia into the KG via SPARQL queries. 
###### Here too, most often only some of the six parameters need to be provided:
    Default parameters that most often are left untouched:
        - node_label: The label of the Node where properties shall be stored. Mostly this is "Company"
        - prop_name: This is always the name of the class GraphConstruction instance property "label_wikidata_id" (currently set to: "wikidataID") as this links wikidata and dbpedia
    Parameters that must be set:
        - prop_dbp_id: The predicate that connects the "wikidataID" to the new dbpedia "property" such as "owl:sameAs"
        - new_prop_name: The name of the new property from dbpedia such as "abstract" for the description of a company
        - new_prop_dbp_id: The dbpedia-id for the new data such as "dbo:abstract" for "abstract"
        - new_prop_is_list: Bool if new dbpedia data are multiple items or just one item

create_text_embedding()
###### This method enables to create text embeddings from LLMs for selected Node properties. Currently, the method creates a text embedding for the Node property "abstract" (i.e. a text description of the company) of Node "Company". This enables similarity search of Nodes in respect to their property "abstract". This method currently is not used actively as the similarity between company descriptions (i.e. "abstracts") does not make sense in our opinion. But it could make sense to do similarity search in the future if other text properties of the ESG data need to be compared.
###### The parameters of this method are:
    - node_label: The label of the Node for which a property shall be embedded. Mostly this is "Company"
    - node_primary_prop_name: The primary and unique property name of the Node. This is "LEI" for the Node "Company" 
    - prop_to_embed: The name of the Node text property to be embedded. In the example, this is "abstract", i.e. the description of the company.
    - vector_size: Size of the embedding vector depending on the LLM to be used. Currently for "bert-based-uncased", this is 768.
    - similarity_method: Similarity method to be used. Currently this is "cosine" for "cosine similarity".

 ---
### E_embeddings.py:
##### As outlined above, text properties of Nodes can be embedded. This module creates these text embeddings using the [transformer](https://huggingface.co/docs/transformers/index) library and the pretrained "bert-base-uncased"-model. Please refer to the [documentation](https://huggingface.co/bert-base-uncased) for further information.

 ---
### F_graph_bot.py:
###### This method uses the Python [LangChain](https://www.langchain.com/) library and the [OpenAI API](https://platform.openai.com/docs/overview) to create a KG bot. In order to execute the functions, an OpenAI API KEY needs to be provided in the "secrets.env"-file. Please refer to the project's README.md-file.
###### The bot can be asked text questions which will be converted into cypher queries and sent to the KG. The query response from the KG is then again translated into a text message to be readable by humans.
###### The class GraphBot's "ask_question()"-method must be passed a question as string. It prints the question, the intermediate steps such as the created Cypher queries and the answer.

 ---
### G_graph_queries.py:
###### In this module, the class GraphQueries' methods create parameterized Cypher queries that can be used to answer a wide range of different questions. Some common parameters are:

    esrs: -> An ESRS-Enum, see project's README.md. Must always be provided.
    periods: Must be a list. Can be ['2022', '2023'] for multiple years or ['2022'] for a single year.
    company: An Company-Enum. If set to "None", the result is shown for all comapnies in the KG.
    stat: A Stats-Enum ("Statistics"). If set to "None", indivdual values will be shown.
    return_df: If set to "True", a pandas "DataFrame" will be returned, else a NEO4J "Record"-object.

###### Some examples of possible questions to be answered by these queries can be found in the "main.py"-file under: 
    """ 7. GraphQueries: Query NEO4J Graph with Python functions """
