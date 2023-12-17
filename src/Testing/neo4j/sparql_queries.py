from pprint import pprint
import requests

url_wikidata = 'https://query.wikidata.org/sparql'
url_dbpedia = 'https://dbpedia.org/sparql'

# query_wiki = '''
# select ?company ?companyLabel ?industry ?industryLabel ?countryLabel
# where {
#   ?company wdt:P1278  "549300JSX0Z4CW0V5023" .
#   ?company wdt:P452  ?industry .
#   ?company wdt:P17 ?country
#   SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
#   }
# limit 10
# '''

query_wiki = """
# PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT DISTINCT
    ?industry ?LEI
    # (group_concat(DISTINCT ?industry; separator = ", ") as ?inds)
    # (GROUP_CONCAT(?industryLabel; SEPARATOR = "; ") AS ?inds)
WHERE {
  ?company wdt:P1278 "549300JSX0Z4CW0V5023" ;
           wdt:P1278 ?LEI ;
           wdt:P452  ?industry .
  
  # BIND(concat(?industry + "_") AS ?indd)
  # UNION
  # { ?company wdt:P1278 "529900PM64WH8AF1E917" ;
  #            wdt:P452  ?industry . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  
  }
limit 10
"""

r_wikidata = requests.get(url_wikidata, params = {'format': 'json', 'query': query_wiki})
# r_dbpedia = requests.get(url_dbpedia, params={'format': 'json', 'query': query_dbpedia})
print(r_wikidata.status_code)

data = r_wikidata.json()
# data = r_dbpedia.json()
print('data:\n', data)
print('-----------------------------------')
res = data["results"]["bindings"]
print('res:\n', res)

if __name__ == '__main__':
    pass
