# UASFRA-MS-PROJDIGI
### I. Overview
UASFRA-MS-PROJDIGI is a project and part of the requirements for the Master program (M.Sc.) in Computer Science at the [Frankfurt University of Applied Sciences](https://www.frankfurt-university.de/en/studies/master-programs/general-computer-science-msc/for-prospective-students/).

The project's goal is to create a [NEO4J Knowledge Graph](https://neo4j.com/) ("KG") populated with [ESG](https://de.wikipedia.org/wiki/Environmental,_Social_and_Governance) data required to be reported by companies due to the [European Sustainability Reporting Standards (ESRS)](https://www.efrag.org/lab6?AspxAutoDetectCookieSupport=1) legislation. 

The programs presented here are able to create and query such a NEO4J Knowledge Graph with Python functions.
***
### II. Project structure
All programs can be executed from the "main.py"-script in the root folder of this project. The "main.py"-script uses the following modules in the "src"-folder:

main.py
> src
>> - A_read_xbrl.py: <em><span style="color: yellow;">Convert company's XBRL-files into JSON-files to later import the data into the KG</span></em>
>> - B_rdf_graph.py 
>> - C_read_data.py
>> - D_graph_construction
>> - E_embeddings.py
>> - F_graph_bot.py
>> - G_graph_queries.py
 

***
### III. Installation
#### In order to run the functions in "main.py", NEO4J and related software needs to be installed first.
##### A. NEO4J database
###### There are different options to install the NEO4J database on your system. We recommend to choose the 
[Graph Database Self-Managed / NEO4J Server](https://neo4j.com/deployment-center/#gdb-tab) (Community or Enterprise)  
###### version. Please follow the installation instructions here:
- Check the system requirements to install NEO4J: [NEO4J system requirements](https://neo4j.com/docs/operations-manual/current/installation/requirements/)
- Linux installation instructions: [NEO4J Linux installation](https://neo4j.com/docs/operations-manual/current/installation/linux/)
- Windows installation instructions: [NEO4J Windows installation](https://neo4j.com/docs/operations-manual/current/installation/windows/)

##### B. NEO4J plugins
###### Please make sure to also install the following NEO4J plugins:
- [NEO4J neosemantics (or "n10s")](https://github.com/neo4j-labs/neosemantics/releases)
- [NEO4J apoc](https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/4.1.0.11)
- [NEO4J graph-data-science](https://neo4j.com/deployment-center/#gds-tab)

###### Under Windows, the respective jar-files need to be downloaded and put into the "$NEO4J_HOME/plugins" sub-folder of the "$NEO4J_HOME"-folder on your system. Some "$NEO4J_HOME/conf"-files need to be adjusted. Please refer to the installation instructions here:
- [neosemantics installation instructions](https://neo4j.com/labs/neosemantics/installation/#_standalone_instance)
- [apoc installation instructions](https://neo4j.com/labs/apoc/4.1/installation/#neo4j-server)
- [graph-data-science installation instructions](https://neo4j.com/docs/graph-data-science/current/installation/neo4j-server/)

##### C. NEO4J settings
###### In order to check the NEO4J installation and to run the "main.py"-script correctly:

   1. Make sure you have adjusted the "$NEO4J_HOME/conf"-files as described in the NEO4J plugins installation instructions.
   2. Open http://localhost:7474 in your web browser.
   3. Connect using the username "neo4j" with the default password "neo4j". You might be prompted to change your password. 
   4. Go to the file "secrets_template.env" in the root folder of this project. Change the name of this file from "secrets_template.env" to "secrets.env". Set the NEO4J username and password from the web browser as your "NEO4J_USER" and "NEO4J_PW" there. You might also want to insert your "OPENAI_API_KEY" there if you want to use the graph bot later.
   5. Go to your browser http://localhost:7474 again and run the following Cypher query: 
      
        >SHOW functions;

   6. You should now see a long list of functions, some of them <b><u>must</u></b> start with:
      
      - n10s.* (for neosemantics functions)
      - apoc.* (for apoc functions)
      - gds.* (for graph-data-science functions)

   7. If any of these three prefixes is missing, please go back and check/redo the installation.

##### D. Project settings
###### In the root folder of this project, there is a "settings.py"-file with:
    # PATHS
    path_base = pathlib.Path("C:/your/path/to/the/root-folder/")
    path_data = pathlib.Path(path_base, "src/data/")
    path_models = pathlib.Path(path_base, "src/models/")
    path_ontos = pathlib.Path(path_models, "Ontologies")

Only adjust the "<u>path_base</u>"-value to the path where this project (root folder) is located on your system. Leave all other paths untouched unless you want to change the location of these folders. 

***

### IV. Usage