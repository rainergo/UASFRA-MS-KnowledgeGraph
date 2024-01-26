import pathlib
from src.A_read_xbrl import XBRL, XHTMLName
from src.C_read_data import get_data_dicts
from src.D_graph_construction import GraphConstruction
from src.F_graph_bot import GraphBot
from src.G_graph_queries import GraphQueries, ESRS, Stats, Company

from src.models.Ontologies.onto4.params import unique_node_keys, node_value_props
from settings import path_base, path_ontos, path_data


def read_xbrl_into_json(xhtml_name: XHTMLName):
    xbrl = XBRL()
    """ XHTMLName is a StrEnum. Just choose between the Enum.name such as XHTMLName.Adidas or XHTMLName.BASF, etc. """
    xbrl.read_xbrl_to_json(xhtml_name=xhtml_name)


def load_onto_and_show_schema(onto_file_path_or_url: str, path_is_url: bool = False):
    """ Loads ontology and schema into NEO4J.
    Attention: All existing data in the Knowledge-Graph will be deleted !
    """
    print('Loading Ontology ... . This might take a few seconds, please be patient!')
    kg = GraphConstruction(path_to_onto=onto_file_path_or_url)
    kg.delete_graph()
    kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    kg.load_onto_or_rdf(path=onto_file_path_or_url, path_is_url=path_is_url, load_onto_only=True)
    print('Done! Ontology can now be inspected with one of the following Cypher queries:'
          ' "MATCH (n) RETURN n" or'
          ' "CALL db.schema.visualization()"')


def load_data_into_knowledge_graph(onto_file_path_or_url: str,
                                   path_to_jsons: str,
                                   list_of_json_names: list,
                                   delete_and_init_graph: bool = True,
                                   show_queries: bool = False):
    """ Loads data into NEO4J. The data must be in JSON-format and located in '/src/data/JSONs/'
    (see: 'README-data.md-file'). The path to these JSON-files and the names of the JSON-files must be provided in
    'path_to_jsons' and 'list_of_json_names'. Cypher queries can be shown if 'show_queries' is set to 'True' """
    print('Loading data into NEO4J ... . This might take a few seconds, please be patient!')
    kg = GraphConstruction(path_to_onto=onto_file_path_or_url)
    all_json_paths: list = [pathlib.Path(path_to_jsons, item).as_posix() for item in list_of_json_names]
    node_data, relation_data = get_data_dicts(all_json_paths=all_json_paths)
    if delete_and_init_graph:
        kg.delete_graph()
        kg.init_graph(handle_vocab_uris="MAP", handle_mult_vals="ARRAY", multi_val_prop_list=["industries"])
    kg.load_data_into_knowledge_graph(unique_node_keys=unique_node_keys, node_value_props=node_value_props,
                                      nodes_data=node_data, rels_data=relation_data, show_queries=show_queries)
    print('Done! Loaded data can now be inspected with this Cypher query: "MATCH (n) RETURN n"')


def load_wikidata_data(onto_file_path_or_url: str):
    """ Loads external data from wikidata for Company Nodes: Industries, Countries and ISINs """
    """IMPORTANT: This must be run ONLY AFTER a knowledge graph has been created and filled with data !!! """
    print('Enriching NEO4J-Graph with wikidata data ... . This might take a few seconds, please be patient!')
    kg = GraphConstruction(path_to_onto=onto_file_path_or_url)
    kg.import_wikidata_id()
    industry = {"node_label": "Company", "prop_name": "LEI", "prop_wiki_id": "P1278", "new_prop_name": "industries",
                "new_prop_wiki_id": "P452", "use_new_prop_label": True, "new_prop_is_list": True}
    country = {"node_label": "Company", "prop_name": "LEI", "prop_wiki_id": "P1278", "new_prop_name": "country",
               "new_prop_wiki_id": "P17", "use_new_prop_label": True, "new_prop_is_list": False}
    isin = {"node_label": "Company", "prop_name": "LEI", "prop_wiki_id": "P1278", "new_prop_name": "ISIN",
            "new_prop_wiki_id": "P946", "use_new_prop_label": True, "new_prop_is_list": False}
    kg.import_data_from_wikidata(**industry)
    kg.import_data_from_wikidata(**country)
    kg.import_data_from_wikidata(**isin)
    print('Done! Industries, Countries and ISINs data loaded into NEO4J.')


def load_dbpedia_data(onto_file_path_or_url: str):
    """ Loads external data from dbpedia for Company Nodes: abstract ("Company description") """
    """IMPORTANT: This must be run ONLY AFTER a knowledge graph has been created and filled with data !!! """
    print('Enriching NEO4J-Graph with dbpedia data ... . This might take a few seconds, please be patient!')
    kg = GraphConstruction(path_to_onto=onto_file_path_or_url)
    kg.import_wikidata_id()
    company_abstract = {
        "node_label": "Company",
        "prop_name": "wikidataID",
        "prop_dbp_id": f"owl:sameAs",
        "new_prop_name": "abstract",
        "new_prop_dbp_id": f"dbo:abstract",
        "new_prop_is_list": False
    }
    kg.import_data_from_dbpedia(**company_abstract)
    print('Done! Abstract ("Company Description") loaded into NEO4J.')


def create_text_embedding(onto_file_path_or_url: str, node_label: str,
                          node_primary_prop_name: str, prop_to_embed: str):
    """ Creates text embeddings for a string property of a Node. """
    """IMPORTANT: This must be run ONLY AFTER a knowledge graph has been created and the respective Node ('node_label') 
    has a string/text property ('prop_to_embed') !!! """
    print(f'Creating text embedding for property "{prop_to_embed}" of Node "{node_label}" ... . '
          f'This might take a few seconds, please be patient!')
    kg = GraphConstruction(path_to_onto=onto_file_path_or_url)
    kg.create_text_embedding(node_label=node_label, node_primary_prop_name=node_primary_prop_name,
                             prop_to_embed=prop_to_embed)
    print(f'Done! Text embedding for property "{prop_to_embed}" of Node "{node_label}" was created.')


def ask_graph_bot(question: str):
    bot = GraphBot()
    print('QUESTION:\n', question)
    ans = bot.ask_question(question=question)
    print('ANSWER:\n', ans)


def execute_graph_queries(esrs_1: ESRS, company: Company, periods: list, return_df: bool,
                          stat: Stats = None, by_period: bool = True, esrs_2: ESRS = ESRS.NetRevenue):
    q = GraphQueries()
    esrs_data = q.get_esrs_data(esrs=ESRS.EmissionsToAirByPollutant, company=Company.Adidas,
                          periods=['2022', '2023'], return_df=return_df)
    print(f'ESRS data for "{esrs_1.name}", company "{company.name}" and {periods} is: \n{esrs_data}')

    print('-------------------------------------------------------------------------------')
    stat_by_comp = q.get_statistics_by_company(esrs=esrs_1, stat=stat,
                                        periods=periods, return_df=return_df)
    print(f'Statistics "{stat}" by company for "{esrs_1.name}" and {periods} is: \n{stat_by_comp}')
    print('-------------------------------------------------------------------------------')
    stat_by_label = q.get_statistics_by_esrs_data(esrs=esrs_1, stat=stat,
                                        periods=periods, by_period=by_period, return_df=return_df)
    print(f'Statistics "{stat}" by label for "{esrs_1.name}" and {periods} is: \n{stat_by_label}')
    print('-------------------------------------------------------------------------------')
    ratio = q.get_ratio_of_two_esrs(esrs_numerator=esrs_1, esrs_denominator=esrs_2,
                                  company=company, periods=None, return_df=return_df)
    print(f'Ratio of "{esrs_1.name}" to "{esrs_2.name}" for company "{company.name}" is: \n{ratio}')


if __name__ == '__main__':
    # TODO: UNCOMMENT THOSE FUNCTIONS YOU WANT TO RUN
    """ 0. Read XBRL-file into JSON-file. Please see: README-data.md-file. """
    # read_xbrl_into_json(xhtml_name=XHTMLName.Adidas)

    """ -----------------------------------  NEO4J ----------------------------------------------- """
    # onto_file_path_or_url: str = path_ontos.as_posix() + "/onto4/Ontology4.ttl"

    """ 1. Load ontology and show schema of knowledge graph in browser. Please see: README-models.md-file. """
    # load_onto_and_show_schema(onto_file_path_or_url=onto_file_path_or_url, path_is_url=False)

    """ 2. Load JSON-files/Company data into the NEO4J Knowledge-Graph. Please see: README-data.md-file. """
    # path_to_jsons: str = path_data.as_posix() + "/JSONs/"
    # json_names: list = ['Adidas_2022.json', "BASF_2022.json", 'Adidas_2023.json', "BASF_2023.json",
    #                     "Puma_2022.json", 'Puma_2023.json']
    # load_data_into_knowledge_graph(onto_file_path_or_url=onto_file_path_or_url,
    #                                path_to_jsons=path_to_jsons,
    #                                list_of_json_names=json_names,
    #                                show_queries=False)

    """ 3. Enrich NEO4J Knowledge-Graph with external data from wikidata. """
    # load_wikidata_data(onto_file_path_or_url=onto_file_path_or_url)

    """ 4. Enrich NEO4J Knowledge-Graph with external data from dbpedia. """
    # load_dbpedia_data(onto_file_path_or_url=onto_file_path_or_url)

    """ 5. Create text embedding for one of the text properties. """
    # create_text_embedding(onto_file_path_or_url=onto_file_path_or_url, node_label="Company",
    #                       node_primary_prop_name="LEI", prop_to_embed="abstract")

    """ 6. GraphBot: RAG (Retrieval Augmented Generation) with NEO4J Graph """
    # question = "How much of TotalUseOfLandArea did BASF have in the year 2023?"
    # question = "How much did EmissionsToSoilByPolllutant for Adidas change from the year 2022 to the year 2023?"
    # question = "Which industry had the most GrossScope1GHGEmissions in 2023?"
    # ask_graph_bot(question=question)

    """ 7. GraphQueries: Query NEO4J Graph with Python functions """
    execute_graph_queries(esrs_1=ESRS.EmissionsToAirByPollutant, company=Company.Adidas, periods=['2022', '2023'],
                          return_df=True, stat=Stats.SUM, esrs_2=ESRS.NetRevenue)