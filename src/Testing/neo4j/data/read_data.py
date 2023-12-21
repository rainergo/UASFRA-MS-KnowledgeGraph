import json


def get_data_dicts(all_json_paths: list[str]) -> tuple[list, list]:
    
    node_data: list = list()
    relationship_data: list = list()
    periods_processed: list = list()
    companies_processed: list = list()
    
    for json_path in all_json_paths:
    
        with open(file=json_path, mode="r", encoding="utf-8") as file:
            company: dict = json.load(file)

        if (company['LEI'], company['label']) not in companies_processed:
            company_template = [{"Company": {"LEI": company['LEI'], "label": company['label']}}]
            node_data += company_template
            companies_processed.append((company['LEI'], company['label']))
    
        if company['period'] not in periods_processed:
    
            node_template = [
                {"EnergyFromFossilSources": {"label": "TotalEnergyConsumptionFromFossilSources", "period": company['period']}},
                {"EnergyFromNuclearSources": {"label": "TotalEnergyConsumptionFromNuclearSources", "period": company['period']}},
                {"EnergyFromRenewableSources": {"label": "TotalEnergyConsumptionFromRenewableSources", "period": company['period']}},
                {"Asset": {"label": "AssetsAtMaterialPhysicalRiskBeforeClimateChangeAdaptationActions", "period": company['period']}},
                {"Asset": {"label": "AssetsAtMaterialTransitionRiskBeforeClimateMitigationActions", "period": company['period']}},
                {"Expenditure": {"label": "FinancialResourcesAllocatedToActionPlanOpEx", "period": company['period']}},
                {"Expenditure": {"label": "FinancialResourcesAllocatedToActionPlanCapEx", "period": company['period']}},
                {"Revenue": {"label": "NetRevenueUsedToCalculateGHGIntensity", "period": company['period']}},
                {"Revenue": {"label": "NetRevenue", "period": company['period']}},
                {"GHGEmission": {"label": "TotalGHGEmissions", "period": company['period']}},
                {"GHGReduction": {"label": "AbsoluteValueOfTotalGHGEmissionsReduction", "period": company['period']}},
                {"Scope1": {"label": "GrossScope1GHGEmissions", "period": company['period']}},
                {"Scope2": {"label": "GrossLocationBasedScope2GHGEmissions", "period": company['period']}},
                {"Scope2": {"label": "GrossMarketBasedScope2GHGEmissions", "period": company['period']}},
                {"Scope3": {"label": "GrossScope3GHGEmissions", "period": company['period']}},
                {"Land": {"label": "TotalUseOfLandArea", "period": company['period']}},
                {"Water": {"label": "TotalWaterConsumption", "period": company['period']}},
                {"Substance": {"label": "TotalAmountOfSubstancesOfConcernGenerated", "period": company['period']}},
                {"Waste": {"label": "EmissionsToAirByPollutant", "period": company['period']}},
                {"Waste": {"label": "EmissionsToSoilByPollutant", "period": company['period']}},
                {"Waste": {"label": "EmissionsToWaterByPollutant", "period": company['period']}}
            ]

            node_data += node_template
            periods_processed.append(company['period'])

        relationship_template = [
            {"Company_consumes_EnergyFromFossilSources": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"EnergyFromFossilSources": {"period": company['period'], "label": "TotalEnergyConsumptionFromFossilSources", "MWh": company["TotalEnergyConsumptionFromFossilSources"]}}}},
            {"Company_consumes_EnergyFromNuclearSources": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"EnergyFromNuclearSources": {"period": company['period'], "label": "TotalEnergyConsumptionFromNuclearSources", "MWh": company["TotalEnergyConsumptionFromNuclearSources"]}}}},
            {"Company_consumes_EnergyFromRenewableSources": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"EnergyFromRenewableSources": {"period": company['period'], "label": "TotalEnergyConsumptionFromRenewableSources", "MWh": company["TotalEnergyConsumptionFromRenewableSources"]}}}},
            {"Company_owns_Asset": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Asset": {"period": company['period'], "label": "AssetsAtMaterialPhysicalRiskBeforeClimateChangeAdaptationActions", "EUR": company["AssetsAtMaterialPhysicalRiskBeforeClimateChangeAdaptationActions"]}}}},
            {"Company_owns_Asset": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Asset": {"period": company['period'], "label": "AssetsAtMaterialTransitionRiskBeforeClimateMitigationActions", "EUR": company["AssetsAtMaterialTransitionRiskBeforeClimateMitigationActions"]}}}},
            {"Company_spends_Expenditure": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Expenditure": {"period": company['period'], "label": "FinancialResourcesAllocatedToActionPlanOpEx", "EUR": company["FinancialResourcesAllocatedToActionPlanOpEx"]}}}},
            {"Company_spends_Expenditure": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Expenditure": {"period": company['period'], "label": "FinancialResourcesAllocatedToActionPlanCapEx", "EUR": company["FinancialResourcesAllocatedToActionPlanCapEx"]}}}},
            {"Company_receives_Revenue": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Revenue": {"period": company['period'], "label": "NetRevenueUsedToCalculateGHGIntensity", "EUR": company["NetRevenueUsedToCalculateGHGIntensity"]}}}},
            {"Company_receives_Revenue": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Revenue": {"period": company['period'], "label": "NetRevenue", "EUR": company["NetRevenue"]}}}},
            {"Company_emits_GHGEmission": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"GHGEmission": {"period": company['period'], "label": "TotalGHGEmissions", "tonsCO2Eq": company["TotalGHGEmissions"]}}}},
            {"Company_contributesTo_GHGReduction": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"GHGReduction": {"period": company['period'], "label": "AbsoluteValueOfTotalGHGEmissionsReduction", "tonsCO2Eq": company["AbsoluteValueOfTotalGHGEmissionsReduction"]}}}},
            {"Company_emits_Scope1": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope1": {"period": company['period'], "label": "GrossScope1GHGEmissions", "tonsCO2Eq": company["GrossScope1GHGEmissions"]}}}},
            {"Company_indirectlyEmits_Scope2": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope2": {"period": company['period'], "label": "GrossLocationBasedScope2GHGEmissions", "tonsCO2Eq": company["GrossLocationBasedScope2GHGEmissions"]}}}},
            {"Company_indirectlyEmits_Scope2": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope2": {"period": company['period'], "label": "GrossMarketBasedScope2GHGEmissions", "tonsCO2Eq": company["GrossMarketBasedScope2GHGEmissions"]}}}},
            {"Company_indirectlyEmits_Scope3": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope3": {"period": company['period'], "label": "GrossScope3GHGEmissions", "tonsCO2Eq": company["GrossScope3GHGEmissions"]}}}},
            {"Company_exhausts_Land": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Land": {"period": company['period'], "label": "TotalUseOfLandArea", "hectares": company["TotalUseOfLandArea"]}}}},
            {"Company_exhausts_Water": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Water": {"period": company['period'], "label": "TotalWaterConsumption", "cubicmetres": company["TotalWaterConsumption"]}}}},
            {"Company_disposes_Substance": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Substance": {"period": company['period'], "label": "TotalAmountOfSubstancesOfConcernGenerated", "tons": company["TotalAmountOfSubstancesOfConcernGenerated"]}}}},
            {"Company_disposes_Waste": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Waste": {"period": company['period'], "label": "EmissionsToAirByPollutant", "tons": company["EmissionsToAirByPollutant"]}}}},
            {"Company_disposes_Waste": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Waste": {"period": company['period'], "label": "EmissionsToSoilByPollutant", "tons": company["EmissionsToSoilByPollutant"]}}}},
            {"Company_disposes_Waste": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Waste": {"period": company['period'], "label": "EmissionsToWaterByPollutant", "tons": company["EmissionsToWaterByPollutant"]}}}}
        ]
        relationship_data += relationship_template

    return node_data, relationship_data


if __name__ == '__main__':
    from pprint import pprint
    json_paths = ['Adidas_2022.json', 'BASF_2022.json']
    n_data, rel_data = get_data_dicts(all_json_paths=json_paths)
    pprint(n_data)
    print('------------------------------------------------')
    pprint(rel_data)