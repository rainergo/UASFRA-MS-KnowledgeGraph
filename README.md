# UASFRA-MS-KnowledgeGraph
### I. Overview
UASFRA-MS-KnowledgeGraph is a data science project and part of the requirements for the Master program (M.Sc.) in Computer Science at the [Frankfurt University of Applied Sciences](https://www.frankfurt-university.de/en/studies/master-programs/general-computer-science-msc/for-prospective-students/).

The project's goal is to create a [NEO4J Knowledge Graph](https://neo4j.com/) ("KG") populated with [ESG](https://de.wikipedia.org/wiki/Environmental,_Social_and_Governance) data required to be reported by companies due to the [European Sustainability Reporting Standards (ESRS)](https://www.efrag.org/lab6?AspxAutoDetectCookieSupport=1) legislation. 

The reported ESG data is extracted from XBRL-files as part of this project.

The programs presented in here are able to create and query such a NEO4J Knowledge Graph using Python.

The Knowledge Graph can be queried with Python functions or a OpenAI-attached chat bot.

The documentation and presentation to this project are avaialable [here](./project/documentation/UASFRA-MS-KnowledgeGraph-Documentation.pdf) and [here](./project/UASFRA-MS-KnowledgeGraph-ProjectPresentation.pdf).

There are additional READ.md-files concerning the respective sections:
> - [Research](./research/README-research.md)
> - [Data](./src/data/README-data.md)
> - [Model](./src/models/README-models.md)

***
### II. Project structure
###### All programs can be executed from the "main.py"-script in the root folder of this project. The "main.py"-script makes use of the following modules in the "src"-folder:

main.py
> src
>> - A_read_xbrl.py: <em><span style="color: yellow; font-size: 9px">Converts company's XBRL-files into JSON-files to later import the data into the KG</span></em>
>> - B_rdf_graph.py: <em><span style="color: yellow; font-size: 9px">Creates cypher queries based on the provided ontology.ttl-file and constructs the KG schema</span></em> 
>> - C_read_data.py: <em><span style="color: yellow; font-size: 9px">Creates templates for importing the data from the JSON-files created earlier</span></em>
>> - D_graph_construction: <em><span style="color: yellow; font-size: 9px">Imports data from the JSON-files into the KG and loads addional data from wikidata and dbpedia</span></em>
>> - E_embeddings.py: <em><span style="color: yellow; font-size: 9px">Converts text of some Node's text properties into LLM embeddings to later do similarity search</span></em>
>> - F_graph_bot.py: <em><span style="color: yellow; font-size: 9px">Formulates questions in relation to data in the KG in human-readable form for a KB bot to answer them</span></em>
>> - G_graph_queries.py: <em><span style="color: yellow; font-size: 9px">Formulates questions in relation to data in the KG and gets results from Python functions </span></em>
 

***
### III. Settings and Installation
###### In order to run the functions in "main.py", some settings must be adjusted and NEO4J and related software needs to be installed first.
##### A. Project settings
###### In the root folder of this project, there is a "settings.py"-file with:
    # PATHS
    path_base = pathlib.Path("C:/your/path/to/the/root-folder/")
    path_data = pathlib.Path(path_base, "src/data/")
    path_models = pathlib.Path(path_base, "src/models/")
    path_ontos = pathlib.Path(path_models, "Ontologies")

###### Only adjust the "<u>path_base</u>"-value to the path where this project (root folder) is located on your system. Leave all other paths untouched unless you want to change the location of these folders. 

##### B. NEO4J database
###### There are different options to install the NEO4J database on your system. We recommend to choose the 
[Graph Database Self-Managed / NEO4J Server](https://neo4j.com/deployment-center/#gdb-tab) (Community or Enterprise)  
###### version. Please follow the installation instructions here:
- Check the system requirements to install NEO4J: [NEO4J system requirements](https://neo4j.com/docs/operations-manual/current/installation/requirements/)
- Linux installation instructions: [NEO4J Linux installation](https://neo4j.com/docs/operations-manual/current/installation/linux/)
- Windows installation instructions: [NEO4J Windows installation](https://neo4j.com/docs/operations-manual/current/installation/windows/)

##### C. NEO4J plugins
###### Please make sure to also install the following NEO4J plugins:
- [NEO4J neosemantics (or "n10s")](https://github.com/neo4j-labs/neosemantics/releases)
- [NEO4J apoc](https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/4.1.0.11)
- [NEO4J graph-data-science (or "gds")](https://neo4j.com/deployment-center/#gds-tab)

###### Under Windows, the respective jar-files need to be downloaded and put into the "$NEO4J_HOME/plugins" sub-folder of the "$NEO4J_HOME"-folder on your system. Some "$NEO4J_HOME/conf"-files need to be adjusted. Please refer to the installation instructions here:
- [NEO4J neosemantics installation instructions](https://neo4j.com/labs/neosemantics/installation/#_standalone_instance)
- [NEO4J apoc installation instructions](https://neo4j.com/labs/apoc/4.1/installation/#neo4j-server)
- [NEO4J graph-data-science installation instructions](https://neo4j.com/docs/graph-data-science/current/installation/neo4j-server/)

##### D. Python libraries
###### In order to use the programs, some Python libraries need to be installed first. Please install (i.e. with: **pip install ...**) all the libraries listed under [packages] in the Pipfile of the root folder:

Pipfile:
>[packages]
> - neo4j
> - pandas
> - python-dotenv
> - etc.

##### E. Check installation and settings
###### In order to check if the NEO4J installation succeeded and if Python NEO4J scripts can be executed:

   1. Make sure you have adjusted the "$NEO4J_HOME/conf"-files as described in the NEO4J plugins installation instructions.
   2. Open http://localhost:7474 in your web browser.
   3. Connect using the username "neo4j" with the default password "neo4j". You might be prompted to change your password. 
   4. Go to the file "secrets_template.env" in the root folder of this project. Change the name of this file from "secrets_template.env" to "secrets.env". Set the NEO4J username and password from the web browser as your "NEO4J_USER" and "NEO4J_PW" there. You might also want to insert your "OPENAI_API_KEY" there if you want to use the graph bot later.
   5. To see if NEO4J and its plugins were installed correctly and can be used in "main.py", please run the following "test_installation.py"-script in the root folder: 

test_installation.py:
```python
""" This script's purpose is to check if the installation of NEO4J and the import of Python libraries succeeded.""" 

from src.G_graph_queries import GraphQueries

gq = GraphQueries()
df = gq._query_df(query="SHOW functions")

apoc = df.name.str.startswith('apoc').any()
n10s = df.name.str.startswith('n10s').any()
gds = df.name.str.startswith('gds').any()

if __name__ == '__main__':
    print(f"""INSTALLATIONS:
    apoc: {apoc}
    n10s: {n10s}
    graph-data-science: {gds}""")
```

   6. You <b><u>should</u></b> now see "True" printed for all three prefixes:
      
      - n10s.* (for neosemantics functions)
      - apoc.* (for apoc functions)
      - gds.* (for graph-data-science functions)

   7. If you get an error or any of these three prefixes is missing ("False" in the printout), please go back and check/redo the settings and the installation.

***

### IV. Usage
###### Make sure to have satisfied all requirements and adjusted all the settings as laid out above. 

##### A. Functions
###### From the "main.py"-file in the root folder, you can now run the following functions by <u>uncommenting</u> the <u><b># CODE BLOCK</b></u> below the desired function description:
main.py

    0. Read XBRL-file into JSON-file. Please see: README-data.md-file.
        # CODE BLOCK
    1. Load ontology and show schema of knowledge graph in browser. Please see: README-models.md-file.
        # CODE BLOCK
    2. Load JSON-files/Company data into the NEO4J Knowledge-Graph. Please see: README-data.md-file.
        # CODE BLOCK
    3. Enrich NEO4J Knowledge-Graph with external data from wikidata.
        # CODE BLOCK
    4. Enrich NEO4J Knowledge-Graph with external data from dbpedia.
        # CODE BLOCK
    5. Create text embedding for one of the text properties.
        # CODE BLOCK
    6. GraphBot: RAG (Retrieval Augmented Generation) with NEO4J Graph.
        # CODE BLOCK
    7. GraphQueries: Query NEO4J Graph with Python functions.
        # CODE BLOCK

###### Please note, that for functions 1. - 5. above, you also need to uncomment the following line:
     onto_file_path_or_url: str = path_ontos.as_posix() + "/onto4/Ontology4.ttl"

##### B. Parameters
###### Most of the parameters to be passed to these functions are Python "Enums". For instance, for the function ...
*execute_graph_queries()*

    """ 7. GraphQueries: Query NEO4J Graph with Python functions. """

    execute_graph_queries(esrs_1=ESRS.EmissionsToAirByPollutant, 
                          company=Company.Adidas, 
                          periods=['2023', '2022'],
                          return_df=True, 
                          stat=Stats.SUM, 
                          esrs_2=ESRS.NetRevenue, 
                          comp_prop=CompProp.Industries,
                          print_queries=False)

###### ... the parameters are the Enums "ESRS", "Company", "Stats" and "CompProp". 

###### These Enums allow you to easily select a value from the possible values such as "Adidas" after typing "Company." as your IDE should now show you all the possible values.
These Enum values are:

ESRS:

###### The ESRS-values refer to the 21 exemplary ESRS data points that you populated the KG with if you have (at least) run the functions 1. through 5. from "main.py". Please refer to the README-data.md-file in "/src/data/" for further details:
    
        AbsoluteValueOfTotalGHGEmissionsReduction 
        AssetsAtMaterialPhysicalRiskBeforeClimateChangeAdaptationActions
        AssetsAtMaterialTransitionRiskBeforeClimateMitigationActions
        EmissionsToAirByPollutant
        EmissionsToSoilByPollutant
        EmissionsToWaterByPolllutant
        FinancialResourcesAllocatedToActionPlanCapEx
        FinancialResourcesAllocatedToActionPlanOpEx
        GrossLocationBasedScope2GHGEmissions
        GrossMarketBasedScope2GHGEmissions
        GrossScope1GHGEmissions
        GrossScope3GHGEmissions
        NetRevenue
        NetRevenueUsedToCalculateGHGIntensity
        TotalAmountOfSubstancesOfConcernGenerated
        TotalEnergyConsumptionFromFossilSources
        TotalEnergyConsumptionFromNuclearSources
        TotalEnergyConsumptionFromRenewableSources
        TotalGHGEmissions
        TotalUseOfLandArea
        TotalWaterConsumption

Company:

###### The Company-values refer to the 3 exemplary companies "Adidas", "BASF" and "Puma" that you populated the KG with. Please refer to the README-data.md-file in "/src/data/" for further details:
    
        Adidas
        BASF
        Puma

Stats:

###### The Stats-values refer to 4 statistical functions that can be used to calculate aggregates:
    
        MIN
        MAX
        AVG
        SUM

CompProp:

###### The two CompProp-values refer to Node properties of the "Company" Node which come from external sources such as wikidata or dbpedia. Aggregates and single data points can be calculated according to these values. Please refer to the functions in "G_graph_queries.py"":
    
        Country
        Industries

###### Please note that the sample JSON-files loaded into the KG only contains data for the periods 2022 and 2023.

The next section is: [Research](./research/README-research.md)
