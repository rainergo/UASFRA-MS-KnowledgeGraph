## README.md for models
### This models-folder contains Ontology-files and accompanying data. Currently, there is only one ontology and thus only one ontology folder ("onto4"):
    - onto4
        - Ontology4.ttl
        - params
        - data_needed

### Ontology4.ttl
###### The name of the ontology ("Ontology4") has no special meaning and only reflects the latest version number. The ontology and file was created with the help of the free [Protégé](https://protege.stanford.edu/) tool provided by Stanford University. The file format is Turtle (".ttl"). The ontology can be visually represented:

<img src="./Ontologies/onto4/Ontology4.png" width="200" alt="">

###### The ontology subordinates and hosts all 21 sample ESG data points referred to earlier:
<img src="../../src/data/Knowledge-Graph-Sample-Data.png" width="1000" alt="">

###### The intent in the construction phase of the ontology was to use general concept class and node names. This would allow subordination of further data points under the existing nodes. 
###### For instance: For the category "Scope 1 Greenhouse Gas Emissions" there are roughly 30 data points to be reported (according to the [ESRS_Draft_10_2023.xlsx](../../research/ESRS/ESRS_Draft_10_2023.xlsx)) and loaded into the Knowledge-Graph later on and not just one as in our sample JSON-file. But this does not pose a problem, as these further data points can all be subordinated under the node "Scope1", just with different node labels. 
###### The provided node names try to generally cover the entire spectrum of environmental data ("E" in "ESG") to be reported under ESRS. The scope of our project was limited to environmental data and excludes social and governance aspects ("SG" in "ESG"). 