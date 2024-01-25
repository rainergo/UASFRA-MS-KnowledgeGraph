import os
import pathlib
from dotenv import load_dotenv

import pandas as pd
from neo4j import GraphDatabase, Result, Record, ResultSummary

from settings import path_base, path_data, path_ontos


class GraphQueries:

    def __init__(self, path_to_onto: str, neo4j_db_name: str='neo4j'):
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

    def _query_return_df(self, query: str) -> pd.DataFrame:
        df: pd.DataFrame = self.driver.execute_query(query_=query,
                                                     database_=self.neo4j_db_name,
                                                     result_transformer_=Result.to_df)
        return df

    def _query(self, query: str) -> tuple[Record, ResultSummary, list]:
        records, summary, keys = self.driver.execute_query(query_=query, database_=self.neo4j_db_name)
        return records, summary, keys


if __name__ == '__main__':
    onto_file_path_or_url: str = path_ontos.as_posix() + "/onto4/Ontology4.ttl"
    gq = GraphQueries(path_to_onto=onto_file_path_or_url)

    query = f"""
        MATCH (source:Company)-[rel:emits]->(target:Scope1 {{label: "GrossScope1GHGEmissions"}}) 
        RETURN source.label AS comp, target.period as year, rel.tonsCO2Eq as tonsCO2Eq
        """
    # df = gq._query_return_df(query=query)
    recs, su, k = gq._query(query=query)
    for rec in recs:
        print(rec)
    print('--------------')
    print(su.query)
    print(float(su.result_available_after))
    print('--------------')
    print(k)