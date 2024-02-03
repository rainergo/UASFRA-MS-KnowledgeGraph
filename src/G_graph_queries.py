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


class CompProp(StrEnum):
    Country = "country"
    Industries = 'industries'


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


def check_periods_type(periods: object or None):
    if periods:
        if not isinstance(periods, list):
            raise ValueError('"periods" must be of type: "list"')
        else:
            if not isinstance(periods[0], str):
                raise ValueError(
                    f'"periods" (years) must be of type "str" like ["2022", "2023"] but are of type: "{type(periods[0])}"')


def check_periods_length_and_order(periods: object or None, required_len: int = 2):
    if periods:
        if not len(periods) == required_len:
            raise ValueError(f'"periods" must be of length: "{required_len}" for comparison, but are of length: "{len(periods)}"')
    return sorted(periods)


class GraphQueries:

    def __init__(self, neo4j_db_name: str = 'neo4j', print_queries: bool = False):
        path_to_secrets: pathlib.Path = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        self.neo4j_db_name: str = neo4j_db_name
        auth = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PW'))
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.print_queries = print_queries

    def _query(self, query: str) -> tuple[Record, ResultSummary, list[str]]:
        """ Returns: tuple[Record, ResultSummary, list[keys]] """
        records, summary, keys = self.driver.execute_query(query_=query, database_=self.neo4j_db_name)
        return records, summary, keys

    def _query_df(self, query: str) -> pd.DataFrame:
        """ Return pandas DataFrame """
        df: pd.DataFrame = self.driver.execute_query(query_=query,
                                                     database_=self.neo4j_db_name,
                                                     result_transformer_=Result.to_df)
        return df

    def get_esrs_data(self, esrs: ESRS, company: Company or None = None, periods: list or None = None,
                      return_df: bool = False, limit: int = 10) -> list[Record] or pd.DataFrame:
        check_periods_type(periods=periods)
        where_clause: str = '' if periods is None else f'WHERE target.period IN {periods}'
        company_str: str = '' if company is None else f'{{label: "{company.name}"}}'
        query = f"""
            MATCH (source:Company{company_str})-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}})
            {where_clause}
            RETURN source.label AS company, target.period AS year, rel.{esrs.value['UNIT']} AS {esrs.value['UNIT']}_{esrs.name}
            ORDER by {esrs.value['UNIT']}_{esrs.name} DESC
            LIMIT {limit}
            """
        if self.print_queries:
            print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_statistics_by_company(self, esrs: ESRS, stat: Stats, periods: list or None = None,
                                  return_df: bool = False, limit: int = 10) -> list[Record] or pd.DataFrame:
        check_periods_type(periods=periods)
        where_clause: str = '' if periods is None else f'WHERE target.period IN {periods}'
        with_period: str = ', target' if stat in [Stats.MAX, Stats.MIN] else ''
        return_period: str = 'target.period AS year, ' if stat in [Stats.MAX, Stats.MIN] else ''
        sort_order: str = "ASC" if stat == Stats.MIN else "DESC"
        limit_str = f'LIMIT {limit}' if return_df else 'LIMIT 1'
        query = f"""
            MATCH (source:Company)-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}})
            {where_clause}
            WITH source, {stat.name}(rel.{esrs.value['UNIT']}) AS {stat.name}_{esrs.name}{with_period}
            RETURN source.label AS company, {return_period} {stat.name}_{esrs.name} 
            ORDER by {stat.name}_{esrs.name} {sort_order}
            {limit_str}
            """
        if self.print_queries:
            print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_statistics_by_esrs_data(self, esrs: ESRS, stat: Stats, periods: list or None = None,
                                    by_period: bool = False, return_df: bool = False,
                                    limit: int = 10) -> list[Record] or pd.DataFrame:
        check_periods_type(periods=periods)
        where_clause: str = '' if periods is None else f'WHERE target.period IN {periods}'
        with_period: str = '' if periods is None or not by_period else ', target.period as year'
        return_period: str = '' if periods is None or not by_period else 'year,'
        sort_order: str = "ASC" if stat == Stats.MIN else "DESC"
        limit_str = f'LIMIT {limit}' if return_df else 'LIMIT 1'
        query = f"""
            MATCH (source:Company)-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}})
            {where_clause}
            WITH {stat.name}(rel.{esrs.value['UNIT']}) AS {stat.name}_{esrs.name}, target.label AS label{with_period}
            RETURN label, {return_period} {stat.name}_{esrs.name} 
            ORDER by {stat.name}_{esrs.name} {sort_order}
            {limit_str}
            """
        if self.print_queries:
            print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_ratio_of_two_esrs(self, esrs_numerator: ESRS, esrs_denominator: ESRS, company: Company or None = None,
                              periods: list or None = None, return_df: bool = False, stat: Stats = None, limit: int = 10):
        check_periods_type(periods=periods)
        if stat is not None:
            periods = check_periods_length_and_order(periods=periods)
        company_str: str = '' if company is None else f'{{label: "{company.name}"}}'
        period_str: str = f' AND target_1.period IN {periods}' if periods else ''
        return_label: str = '' if stat is not None else 'source.label AS label, '
        stat_str: str = stat.name if stat is not None and company is None else ''
        query = f"""
        MATCH (source:Company{company_str})-[rel_numerator:{esrs_numerator.value['REL']}]->(target_1:{esrs_numerator.value['NODE']} {{label: "{esrs_numerator.name}"}})
        MATCH (source:Company{company_str})-[rel_denominator:{esrs_denominator.value['REL']}]->(target_2:{esrs_denominator.value['NODE']} {{label: "{esrs_denominator.name}"}})
        WHERE target_1.period = target_2.period{period_str}
        RETURN {return_label}target_1.period AS year, toFloat( {stat_str}(rel_numerator.{esrs_numerator.value['UNIT']}) / {stat_str}(rel_denominator.{esrs_denominator.value['UNIT']}) ) AS ratio{'_' + stat_str if stat_str != '' else ''}_{esrs_numerator.name}_to{'_' + stat_str if stat_str != '' else ''}_{esrs_denominator.name}
        ORDER BY ratio{'_' + stat_str if stat_str != '' else ''}_{esrs_numerator.name}_to{'_' + stat_str if stat_str != '' else ''}_{esrs_denominator.name} DESC
        LIMIT {limit}
        """
        if self.print_queries:
            print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_difference_of_two_periods(self, esrs: ESRS, periods: list,
                                      company: Company or None = None, stat: Stats = None,
                                      return_df: bool = False, limit: int = 10):
        check_periods_type(periods=periods)
        periods = check_periods_length_and_order(periods=periods, required_len=2)
        company_str: str = '' if company is None else f'{{label: "{company.name}"}}'
        return_label: str = '' if stat is not None else 'source.label AS label, '
        stat_str: str = stat.name if stat is not None and company is None else ''
        query = f"""
        MATCH (source:Company{company_str})-[rel_1:{esrs.value['REL']}]->(target_1:{esrs.value['NODE']} {{label: "{esrs.name}"}})
        MATCH (source:Company{company_str})-[rel_2:{esrs.value['REL']}]->(target_2:{esrs.value['NODE']} {{label: "{esrs.name}"}})
        WHERE target_1.period = "{periods[0]}" AND target_2.period = "{periods[1]}"
        RETURN {return_label}( {stat_str}(rel_2.{esrs.value['UNIT']}) - {stat_str}(rel_1.{esrs.value['UNIT']}) ) AS diff{'_' + stat_str if stat_str != '' else ''}_{esrs.value['UNIT']}_{periods[1]}_to_{periods[0]},
        round( toFloat( toFloat( {stat_str}(rel_2.{esrs.value['UNIT']}) - {stat_str}(rel_1.{esrs.value['UNIT']}) ) / {stat_str}(rel_1.{esrs.value['UNIT']}) ), 5) AS change{'_' + stat_str if stat_str != '' else ''}_pct_{periods[1]}_to_{periods[0]}
        ORDER BY diff{'_' + stat_str if stat_str != '' else ''}_{esrs.value['UNIT']}_{periods[1]}_to_{periods[0]} DESC
        LIMIT {limit}
        """
        if self.print_queries:
            print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]

    def get_esrs_by_company_property(self, esrs: ESRS, comp_prop: CompProp, periods: list, stat: Stats = None,
                                     return_df: bool = False, limit: int = 10):
        check_periods_type(periods=periods)
        stat_str: str = stat.name if stat is not None else ''
        var_name: str = f'{(stat_str + "_") if stat else ""}{esrs.name}{ "_" + "_".join(sorted(periods))} '
        return_str_1: str = f', source.label AS company' if stat is None else ''
        return_str_2: str = f', target.period AS year' if stat is None else ''
        return_str_3: str = f', {stat_str}(rel.{esrs.value["UNIT"]}) {"AS " + var_name}'
        query = f"""
        MATCH (source:Company) 
        UNWIND source.{comp_prop.value} AS colls 
        WITH collect(DISTINCT colls) AS colls
        UNWIND colls AS coll
        MATCH (source:Company)-[rel:{esrs.value['REL']}]->(target:{esrs.value['NODE']} {{label: "{esrs.name}"}}) 
        WHERE coll in source.{comp_prop.value} AND target.period in {periods}
        RETURN coll{return_str_1}{return_str_2}{return_str_3}
        ORDER by {var_name} DESC
        LIMIT {limit}
        """
        if self.print_queries:
            print(query)
        return self._query_df(query=query) if return_df else self._query(query=query)[0]


if __name__ == '__main__':
    q = GraphQueries(print_queries=True)
    # res = q.get_esrs_data(esrs=ESRS.EmissionsToAirByPollutant, company=Company.Adidas,
    #                       periods=['2022', '2023'], return_df=True)
    # res = q.get_statistics_by_company(esrs=ESRS.EmissionsToAirByPollutant, stat=Stats.AVG,
    #                                     periods=['2022', '2023'], return_df=True)
    # res = q.get_statistics_by_esrs_data(esrs=ESRS.NetRevenue, stat=Stats.SUM,
    #                                     periods=['2022', '2023'], by_period=True, return_df=True)
    res = q.get_ratio_of_two_esrs(esrs_numerator=ESRS.TotalGHGEmissions, esrs_denominator=ESRS.GrossScope1GHGEmissions,
                                  company=None, periods=['2022', '2023'], stat=None, return_df=True)
    # res = q.get_difference_of_two_periods(esrs=ESRS.NetRevenue, periods=['2023', '2022'], stat=Stats.SUM,
    #                                       company=None,  return_df=True)
    # res = q.get_esrs_by_company_property(esrs=ESRS.GrossScope1GHGEmissions, comp_prop=CompProp.Industries,
    #                                      periods=['2023'], stat=None,
    #                                      return_df=True)
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
