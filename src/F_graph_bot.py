import os
import pathlib
from dotenv import load_dotenv

from langchain.chains import GraphCypherQAChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.graphs import Neo4jGraph

from settings import path_base, path_data


class GraphBot:
    # rels_explanation = """
    # # Relationship 1: (:Company)-[consumes:MWh]->(:EnergyFromFossilSources)
    # # Relationship 1 explanation: A Company consumed EnergyFromFossilSources which is measured in MWh.
    # # Relationship 2: (:Company)-[consumes:MWh]->(:EnergyFromNuclearSources)
    # # Relationship 2 explanation: A Company consumed EnergyFromNuclearSources which is measured in MWh.
    # # Relationship 3: (:Company)-[consumes:MWh]->(:EnergyFromRenewableSources)
    # # Relationship 3 explanation: A Company consumed EnergyFromRenewableSources which is measured in MWh.
    # # Relationship 4: (:Company)-[contributesTo:tonsCO2Eq]->(:GHGReduction)
    # # Relationship 4 explanation: A Company contributed to a GHGReduction which is measured in tonsCO2Eq.
    # # Relationship 5: (:Company)-[disposes:tons]->(:Substance)
    # # Relationship 5 explanation: A Company disposed a Substance which is measured in tons.
    # # Relationship 6: (:Company)-[disposes:tons]->(:Waste)
    # # Relationship 6 explanation: A Company disposed Waste which is measured in tons.
    # # Relationship 7: (:Company)-[emits:tonsCO2Eq]->(:GHGEmission)
    # # Relationship 7 explanation: A Company emitted GHGEmission which is measured in tonsCO2Eq.
    # # Relationship 8: (:Company)-[emits:tonsCO2Eq]->(:Scope1)
    # # Relationship 8 explanation: A Company emitted Scope1 which is measured in tonsCO2Eq.
    # # Relationship 9: (:Company)-[exhausts:hectares]->(:Land)
    # # Relationship 9 explanation: A Company exhausted Land which is measured in hectares.
    # # Relationship 10: (:Company)-[exhausts:cubicmetres]->(:Water)
    # # Relationship 10 explanation: A Company exhausted Water which is measured in cubicmetres.
    # # Relationship 11: (:Company)-[indirectlyEmits:tonsCO2Eq]->(:Scope2)
    # # Relationship 11 explanation: A Company emitted Scope2 which is measured in tonsCO2Eq.
    # # Relationship 12: (:Company)-[indirectlyEmits:tonsCO2Eq]->(:Scope3)
    # # Relationship 12 explanation: A Company emitted Scope3 which is measured in tonsCO2Eq.
    # # Relationship 13: (:Company)-[owns:EUR]->(:Asset)
    # # Relationship 13 explanation: A Company owns an Asset which is measured in EUR.
    # # Relationship 14: (:Company)-[receives:EUR]->(:Revenue)
    # # Relationship 14 explanation: A Company receives a Revenue which is measured in EUR.
    # # Relationship 15: (:Company)-[spends:EUR]->(:Expenditure)
    # # Relationship 15 explanation: A Company spends Expenditure which is measured in EUR.
    # """

    # nodes_and_labels = """
    # Node "EnergyFromFossilSources": "TotalEnergyConsumptionFromFossilSources"
    # Node "EnergyFromNuclearSources": "TotalEnergyConsumptionFromNuclearSources"
    # Node "EnergyFromRenewableSources": "TotalEnergyConsumptionFromRenewableSources"
    # Node "Asset": "AssetsAtMaterialPhysicalRiskBeforeClimateChangeAdaptationActions", "AssetsAtMaterialTransitionRiskBeforeClimateMitigationActions"
    # Node "Expenditure": "FinancialResourcesAllocatedToActionPlanOpEx", "FinancialResourcesAllocatedToActionPlanCapEx"
    # Node "Revenue": "NetRevenueUsedToCalculateGHGIntensity", "NetRevenue"
    # Node "GHGEmission": "TotalGHGEmissions"
    # Node "GHGReduction": "AbsoluteValueOfTotalGHGEmissionsReduction"
    # Node "Scope1": "GrossScope1GHGEmissions"
    # Node "Scope2": "GrossLocationBasedScope2GHGEmissions", "GrossMarketBasedScope2GHGEmissions"
    # Node "Scope3": "GrossScope3GHGEmissions"
    # Node "Land": "TotalUseOfLandArea"
    # Node "Water": "TotalWaterConsumption"
    # Node "Substance": "TotalAmountOfSubstancesOfConcernGenerated"
    # Node "Waste": "EmissionsToAirByPollutant", "EmissionsToSoilByPollutant", "EmissionsToWaterByPollutant"
    # """

    examples = """
    # Example question 1: How much of GrossScope1GHGEmissions in tonsCO2Eq did the Company BASF emit in the period 2022?
    # Cypher statement to question 1:
    MATCH (source:Company {{label:"BASF"}})-[rel:emits]->(target:Scope1 {{label: "GrossScope1GHGEmissions", period:"2022"}}) 
    RETURN rel.tonsCO2Eq
    # Example question 2: How much of GrossLocationBasedScope2GHGEmissions in tonsCO2Eq did Adidas emit in the year 2023?
    # Cypher statement to question 2:
    MATCH (source:Company {{label:"Adidas"}})-[rel:indirectlyEmits]->(target:Scope2 {{label: "GrossLocationBasedScope2GHGEmissions", period:"2023"}}) 
    RETURN rel.tonsCO2Eq
    # Example question 3: How much did TotalUseOfLandArea for Adidas increase or decrease from 2022 to 2023?
    # Cypher statement to question 3:
    MATCH (source:Company {{label:"Adidas"}})-[rel1:exhausts]->(target:Land {{label: "TotalUseOfLandArea", period:"2022"}})
    MATCH (source:Company {{label:"Adidas"}})-[rel2:exhausts]->(target:Land {{label: "TotalUseOfLandArea", period:"2023"}})
    RETURN rel1.hectares - rel2.hectares AS landChange
    # Example question 4: How much did EmissionsToWaterByPolllutant for Adidas increase or decrease from the year 2022 to the year 2023?
    # Cypher statement to question 4:
    MATCH (source:Company {{label:"Adidas"}})-[rel1:disposes]->(target:Waste {{label: "EmissionsToWaterByPollutant", period:"2022"}})
    MATCH (source:Company {{label:"Adidas"}})-[rel2:disposes]->(target:Waste {{label: "EmissionsToWaterByPollutant", period:"2023"}})
    RETURN rel1.tons - rel2.tons AS waterChange
    # Example question 5: Which company had the highest AbsoluteValueOfTotalGHGEmissionsReduction in 2023?
    # Cypher statement to question 5:
    MATCH (source:Company)-[rel:contributesTo]->(target:GHGReduction {{label: "AbsoluteValueOfTotalGHGEmissionsReduction", period: "2023"}})
    WITH source, MAX(rel.tonsCO2Eq) AS Maximum
    RETURN source.label, Maximum
    ORDER by Maximum DESC
    LIMIT 1
    # Example question 6: What is the AbsoluteValueOfTotalGHGEmissionsReduction of Adidas in the year 2023?
    # Cypher statement to question 6:
    MATCH (source:Company {{label:"Adidas"}})-[rel:contributesTo]->(target:GHGReduction {{label: "AbsoluteValueOfTotalGHGEmissionsReduction", period: "2023" }})
    RETURN rel.tonsCO2Eq
    # Example question 7: What was the total AbsoluteValueOfTotalGHGEmissionsReduction of Adidas for all years?
    # Cypher statement to question 7:
    MATCH (source:Company {{label: "Adidas"}})-[rel:contributesTo]->(target:GHGReduction {{label: "AbsoluteValueOfTotalGHGEmissionsReduction"}})
    WITH SUM(rel.tonsCO2Eq) AS totalReduction
    RETURN totalReduction
    # Example question 8: In which year did Adidas have the highest AbsoluteValueOfTotalGHGEmissionsReduction and how much was it?
    # Cypher statement to question 8:
    MATCH (source:Company {{label: "Adidas"}})-[rel:contributesTo]->(target:GHGReduction {{label: "AbsoluteValueOfTotalGHGEmissionsReduction"}})
    WITH target, MAX(rel.tonsCO2Eq) AS Maximum
    RETURN target.period, Maximum
    ORDER by Maximum DESC
    LIMIT 1
    # Example question 9: What is the Median AbsoluteValueOfTotalGHGEmissionsReduction for Adidas for all years?
    # Cypher statement to question 9:
    MATCH (source:Company {{label: "Adidas"}})-[rel:contributesTo]->(target:GHGReduction {{label: "AbsoluteValueOfTotalGHGEmissionsReduction"}})
    RETURN apoc.agg.median(rel.tonsCO2Eq) as median
    # Example question 10: Which industry had the most AbsoluteValueOfTotalGHGEmissionsReduction in 2023?
    # Cypher statement to question 10:
    MATCH (source:Company) 
    UNWIND source.industries as inds 
    WITH (collect(DISTINCT inds)) as inds 
    UNWIND inds as ind
    MATCH (source:Company)-[rel:contributesTo]->(target:GHGReduction {{label: "AbsoluteValueOfTotalGHGEmissionsReduction", period: "2023"}}) 
    WHERE ind in source.industries 
    RETURN ind, sum(rel.tonsCO2Eq) as sum 
    ORDER by sum 
    DESC LIMIT 1
    # Example question 11: Which industry had the most NetRevenue in 2022?
    # Cypher statement to question 11:
    MATCH (source:Company) 
    UNWIND source.industries as inds 
    WITH (collect(DISTINCT inds)) as inds 
    UNWIND inds as ind
    MATCH (source:Company)-[rel:receives]->(target:Revenue {{label: "NetRevenue", period: "2022"}}) 
    WHERE ind in source.industries 
    RETURN ind, sum(rel.EUR) as sum 
    ORDER by sum 
    DESC LIMIT 1
    """

    def __init__(self):
        path_to_secrets: pathlib.Path = pathlib.Path(path_base, 'secrets.env')
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        neo4j_pw = os.getenv('NEO4J_PW')
        """ We need an OpenAI access key that is available for free (3 months) on: 
        website: https://platform.openai.com/docs/quickstart?context=python """
        openai_key = os.getenv("OPENAI_API_KEY")
        self.graph = Neo4jGraph(url=uri, username="neo4j", password=neo4j_pw)
        self.graph.refresh_schema()
        """ In order to use 'ChatOpenAI' as the LLM, we need to install OpenAI first: 'pip install openai' """
        self.chat_llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)

    def get_schema(self):
        return self.graph.schema

    def create_prompt(self):
        """ IMPORTANT: The PromptTemplate is optimized for graphs and only accepts TWO input_variables (schema, question).
        Additional variables need to be inserted via f-string variables, such as 'self.rels_explanation' and
        'self.examples' in this prompt.

        The following are all the relationships with their property being a quantity of the target Node:
        {self.rels_explanation}
        Do also take into consideration that Nodes can only have the following labels respectively:
        {self.nodes_and_labels}
        Other labels for Nodes are not allowed.
        Do take into account that quantities or values of target Nodes are often stored as the property values of the
        relationship. For instance, given the Relationship pattern "(:source Node)-[Relationship:property]->(:target Node):",
        the quantity or property value of the target Node is given as the property of the Relationship.

        """
        cypher_prompt = f"""
        Task: Generate Cypher statement to query a Neo4j graph database.
        Instructions:
        Use only the provided relationship types and properties in the schema.
        Do not use any other relationship types or properties that are not provided.
        Schema:
        {{schema}}
        Note: Do not include any explanations or apologies in your responses.
        Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
        Do not include any text except the generated Cypher statement.
        Examples: Here are a few examples of generated Cypher statements for particular questions:
        {self.examples}
        
        Now, the question is:
        {{question}}
        """
        CYPHER_GENERATION_PROMPT = PromptTemplate(
            input_variables=["schema", "question"], template=cypher_prompt
        )
        return CYPHER_GENERATION_PROMPT

    def create_chain(self, prompt: PromptTemplate):
        return GraphCypherQAChain.from_llm(llm=self.chat_llm,
                                           graph=self.graph,
                                           cypher_prompt=prompt,
                                           verbose=True,
                                           return_intermediate_steps=True
                                           )

    def ask_question(self, question: str):
        prompt = self.create_prompt()
        chain = self.create_chain(prompt=prompt)
        answer = chain.run(question)
        return answer


if __name__ == '__main__':
    qa = GraphBot()
    # question = "How much of TotalUseOfLandArea did Adidas have in the year 2022?"
    # question = "How much did EmissionsToSoilByPolllutant for Adidas increase or decrease from the year 2022 to the year 2023?"
    question = "Which industry had the most NetRevenue in 2023?"
    print('Question:\n', question)
    ans = qa.ask_question(question=question)
    print('Answer:\n', ans)
