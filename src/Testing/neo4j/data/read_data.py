import json

with open(file="BASF.json", mode="r", encoding="utf-8") as file:
    company: dict = json.load(file)

gen = {"period": "2022"}

template = [
    {"Company": {"LEI": company['LEI'], "label": company['label']}},
    {"Scope1": {"label": "GrossScope1GHGEmissions", "period": gen['period']}},
    {"Scope2": {"label": "GrossLocationBasedScope2GHGEmissions", "period": gen['period']}},
    {"Scope2": {"label": "GrossMarketBasedScope2GHGemissions", "period": gen['period']}},
    {"Scope3": {"label": "GrossScope3GHGEmissions", "period": gen['period']}},
    {"Company_emits_Scope1": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope1": {"period": gen['period'], "label": "GrossScope1GHGEmissions","tonsCO2Eq": company['GrossScope1GHGEmissions']}}}},
    {"Company_emits_Scope2": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope2": {"period": gen['period'], "label": "GrossLocationBasedScope2GHGEmissions", "tonsCO2Eq": company['GrossLocationBasedScope2GHGEmissions']}}}},
    {"Company_emits_Scope2": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope2": {"period": gen['period'], "label": "GrossMarketBasedScope2GHGemissions", "tonsCO2Eq": company['GrossMarketBasedScope2GHGemissions']}}}},
    {"Company_emits_Scope3": {"source": {"Company": {"LEI": company['LEI']}}, "target": {"Scope3": {"period": gen['period'], "label": "GrossScope3GHGEmissions", "tonsCO2Eq": company['GrossScope3GHGEmissions']}}}}
]


if __name__ == '__main__':
    print(template)
