import os
import pathlib
from dotenv import load_dotenv
from enum import Enum, StrEnum, auto

import pandas as pd
from neo4j import GraphDatabase, Result, Record, ResultSummary

from settings import path_base


class Company(StrEnum):
    Adidas = auto()
    BASF = auto()
    Puma = auto()


class Stats(StrEnum):
    MIN = auto()
    MAX = auto()
    AVG = auto()
    SUM = auto()


class ESRS(Enum):
    """ 21 sample ESRS data points, please see: README-data.md-file. Insert data for new ESRS-labels here. """
    AbsoluteValueOfTotalGHGEmissionsReduction = {'NODE': 'GHGReduction', 'REL': 'contributesTo', 'UNIT': 'tonsCO2Eq'}
    AssetsAtMaterialPhysicalRiskBeforeClimateChangeAdaptationActions = {'NODE': 'Asset', 'REL': 'owns', 'UNIT': 'EUR'}
    AssetsAtMaterialTransitionRiskBeforeClimateMitigationActions = {'NODE': 'Asset', 'REL': 'owns', 'UNIT': 'EUR'}
    EmissionsToAirByPollutant = {'NODE': 'Waste', 'REL': 'disposes', 'UNIT': 'tons'}
    EmissionsToSoilByPollutant = {'NODE': 'Waste', 'REL': 'disposes', 'UNIT': 'tons'}
    EmissionsToWaterByPolllutant = {'NODE': 'Waste', 'REL': 'disposes', 'UNIT': 'tons'}
    FinancialResourcesAllocatedToActionPlanCapEx = {'NODE': 'Expenditure', 'REL': 'spends', 'UNIT': 'EUR'}
    FinancialResourcesAllocatedToActionPlanOpEx = {'NODE': 'Expenditure', 'REL': 'spends', 'UNIT': 'EUR'}
    GrossLocationBasedScope2GHGEmissions = {'NODE': 'Scope2', 'REL': 'indirectlyEmits', 'UNIT': 'tonsCO2Eq'}
    GrossMarketBasedScope2GHGEmissions = {'NODE': 'Scope2', 'REL': 'indirectlyEmits', 'UNIT': 'tonsCO2Eq'}
    GrossScope1GHGEmissions = {'NODE': 'Scope1', 'REL': 'emits', 'UNIT': 'tonsCO2Eq'}
    GrossScope3GHGEmissions = {'NODE': 'Scope3', 'REL': 'indirectlyEmits', 'UNIT': 'tonsCO2Eq'}
    NetRevenue = {'NODE': 'Revenue', 'REL': 'receives', 'UNIT': 'EUR'}
    NetRevenueUsedToCalculateGHGIntensity = {'NODE': 'Revenue', 'REL': 'receives', 'UNIT': 'EUR'}
    TotalAmountOfSubstancesOfConcernGenerated = {'NODE': 'Substance', 'REL': 'disposes', 'UNIT': 'tons'}
    TotalEnergyConsumptionFromFossilSources = {'NODE': 'EnergyFromFossilSources', 'REL': 'consumes', 'UNIT': 'MWh'}
    TotalEnergyConsumptionFromNuclearSources = {'NODE': 'EnergyFromNuclearSources', 'REL': 'consumes', 'UNIT': 'MWh'}
    TotalEnergyConsumptionFromRenewableSources = {'NODE': 'EnergyFromRenewableSources', 'REL': 'consumes',
                                                  'UNIT': 'MWh'}
    TotalGHGEmissions = {'NODE': 'GHGEmission', 'REL': 'emits', 'UNIT': 'tonsCO2Eq'}
    TotalUseOfLandArea = {'NODE': 'Land', 'REL': 'exhausts', 'UNIT': 'hectares'}
    TotalWaterConsumption = {'NODE': 'Water', 'REL': 'exhausts', 'UNIT': 'cubicmeter'}


class GraphQueries:

    def __init__(self, neo4j_db_name: str = 'neo4j'):
        path_to_secrets: pathlib.Path = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        self.neo4j_db_name: str = neo4j_db_name
        auth = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PW'))
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def _query(self, query: str) -> tuple[Record, ResultSummary, list[str]]:
        """ Returns: tuple[Record, ResultSummary, list[str]] """
        records, summary, keys = self.driver.execute_query(query_=query, database_=self.neo4j_db_name)
        return records, summary, keys

    def _query_df(self, query: str) -> pd.DataFrame:
        """ Return pandas DataFrame """
        df: pd.DataFrame = self.driver.execute_query(query_=query,
                                                     database_=self.neo4j_db_name,
                                                     result_transformer_=Result.to_df)
        return df

    def _check_periods(self, periods: object or None):
        if periods:
            if not isinstance(periods, list):
                raise ValueError('"periods" must be of type: "list"')
            else:
                if not isinstance(periods[0], str):
                    raise ValueError(
                        f'The periods (years) in list "periods" must be of type "str" but are of type: {type(periods[0])}')

    def get_esrs_data(self, esrs: ESRS, company: Company or None = None, periods: list or None = None,
                      return_df: bool = False) -> list[Record] or pd.DataFrame:
        self._check_periods(periods=periods)
        where_clause: str = '' if periods is None else f'WHERE target.period IN {periods}'
        company_str: str = '' if company is None else f'{{label: "{company.name}"}}'
        query = f"""
            MATCH (source:Company{company_str})-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}})
            {where_clause}
            RETURN source.label AS company, target.period AS year, rel.{esrs.value['UNIT']} AS {esrs.value['UNIT']}_{esrs.name}
            ORDER by {esrs.value['UNIT']}_{esrs.name} DESC
            """
        # print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_statistics_by_company(self, esrs: ESRS, stat: Stats, periods: list or None = None,
                                  return_df: bool = False) -> list[Record] or pd.DataFrame:
        self._check_periods(periods=periods)
        where_clause: str = '' if periods is None else f'WHERE target.period IN {periods}'
        with_period: str = ', target' if stat in [Stats.MAX, Stats.MIN] else ''
        return_period: str = 'target.period AS year, ' if stat in [Stats.MAX, Stats.MIN] else ''
        sort_order: str = "ASC" if stat == Stats.MIN else "DESC"
        limit = '' if return_df else 'LIMIT 1'
        query = f"""
            MATCH (source:Company)-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}})
            {where_clause}
            WITH source, {stat.name}(rel.{esrs.value['UNIT']}) AS {stat.name}_{esrs.name}{with_period}
            RETURN source.label AS company, {return_period} {stat.name}_{esrs.name} 
            ORDER by {stat.name}_{esrs.name} {sort_order}
            {limit}
            """
        # print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_statistics_by_esrs_data(self, esrs: ESRS, stat: Stats, periods: list or None = None,
                                    by_period: bool = False,
                                    return_df: bool = False) -> list[Record] or pd.DataFrame:
        self._check_periods(periods=periods)
        where_clause: str = '' if periods is None else f'WHERE target.period IN {periods}'
        with_period: str = '' if periods is None or not by_period else ', target.period as year'
        return_period: str = '' if periods is None or not by_period else 'year,'
        sort_order: str = "ASC" if stat == Stats.MIN else "DESC"
        limit = '' if return_df else 'LIMIT 1'
        query = f"""
            MATCH (source:Company)-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}})
            {where_clause}
            WITH {stat.name}(rel.{esrs.value['UNIT']}) AS {stat.name}_{esrs.name}, target.label AS label{with_period}
            RETURN label, {return_period} {stat.name}_{esrs.name} 
            ORDER by {stat.name}_{esrs.name} {sort_order}
            {limit}
            """
        # print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_ratio_of_two_esrs(self, esrs_numerator: ESRS, esrs_denominator: ESRS, company: Company or None = None,
                              periods: list or None = None, return_df: bool = False):
        self._check_periods(periods=periods)
        company_str: str = '' if company is None else f'{{label: "{company.name}"}}'
        period_str: str = f' AND target_1.period IN {periods}' if periods else ''
        query = f"""
        MATCH (source:Company{company_str})-[rel_numerator:{esrs_numerator.value['REL']}]->(target_1:{esrs_numerator.value['NODE']} {{label: "{esrs_numerator.name}"}})
        MATCH (source:Company{company_str})-[rel_denominator:{esrs_denominator.value['REL']}]->(target_2:{esrs_denominator.value['NODE']} {{label: "{esrs_denominator.name}"}})
        WHERE target_1.period = target_2.period{period_str}
        RETURN source.label AS label, target_1.period AS year, (rel_numerator.{esrs_numerator.value['UNIT']} / rel_denominator.{esrs_denominator.value['UNIT']}) AS ratio_{esrs_numerator.name}_to_{esrs_denominator.name}
        ORDER BY ratio_{esrs_numerator.name}_to_{esrs_denominator.name} DESC
        """
        # print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]




if __name__ == '__main__':
    q = GraphQueries()
    # res = q.get_esrs_data(esrs=ESRS.EmissionsToAirByPollutant, company=Company.Adidas,
    #                       periods=['2022', '2023'], return_df=True)
    # res = q.get_statistics_by_company(esrs=ESRS.EmissionsToAirByPollutant, stat=Stats.AVG,
    #                                     periods=['2022', '2023'], return_df=True)
    # res = q.get_statistics_by_esrs_data(esrs=ESRS.NetRevenue, stat=Stats.SUM,
    #                                     periods=['2022', '2023'], by_period=True, return_df=True)
    res = q.get_ratio_of_two_esrs(esrs_numerator=ESRS.EmissionsToAirByPollutant, esrs_denominator=ESRS.NetRevenue,
                                  company=Company.Adidas, periods=None, return_df=True)
    print(res)
    # onto_file_path_or_url: str = path_ontos.as_posix() + "/onto4/Ontology4.ttl"
    # gq = GraphQueries()
    #
    # query = f"""
    #     MATCH (source:Company)-[rel:emits]->(target:Scope1 {{label: "GrossScope1GHGEmissions"}})
    #     RETURN source.label AS comp, target.period as year, rel.tonsCO2Eq as tonsCO2Eq
    #     """
    # # df = gq._query_df(query=query)
    # recs, su, k = gq._query(query=query)
    # for rec in recs:
    #     print(rec)
    # print('--------------')
    # print(su.query)
    # print(float(su.result_available_after))
    # print('--------------')
    # print(k)
