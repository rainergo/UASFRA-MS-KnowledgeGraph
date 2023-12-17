from pprint import pprint
import requests

node = "Company"
prop = "LEI"
prop_wiki_id = "P1278"
new_prop = "industry"
new_prop_wiki_id = "P452"
use_new_prop_label: bool = True
new_prop_is_list: bool = True

query = rf"""
MATCH (node:{node})
WITH 
    "SELECT ?{prop} ?{new_prop}{"Label" if use_new_prop_label else ""}
        WHERE {{
            FILTER contains(?{prop}, \"" + node.{prop} + "\")
            ?company wdt:{prop_wiki_id}     ?{prop} ;
                     wdt:{new_prop_wiki_id} ?{new_prop} .
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
      }}"     
AS sparql
CALL apoc.load.jsonParams(
    "https://query.wikidata.org/sparql?query=" + 
      apoc.text.urlencode(sparql),
    {{ Accept: "application/sparql-results+json"}}, null)
YIELD value
UNWIND value['results']['bindings'] as row
WITH row['{prop}']['value'] as prop_val, 
     {'collect(' if new_prop_is_list else ''}row['{new_prop}{"Label" if use_new_prop_label else ""}']['value']{')' if new_prop_is_list else ''} as new_prop_val
MERGE (n:{node} {{ {prop}: prop_val }})
SET n.{new_prop} = new_prop_val;
"""

if __name__ == '__main__':
    print(query)
