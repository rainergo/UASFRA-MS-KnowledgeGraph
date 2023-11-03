import re
import spacy
import pathlib
from pprint import pprint

from src.settings import path_data, reports

#%%
company = "Adidas"
companies = [list_item['company'] for list_item in reports]
assert company in companies
with open(file=pathlib.Path(path_data, f"{company}_text_with_ents_clean.txt"), mode='r', encoding="UTF-8") as f:
    text = f.read()

#%%
# Replacements
replacements = {"Adidas":
                    {" us ": " " + company + " ",
                    " Us ": " " + company + " ",
                    "we are": company + " is",
                    "We are": company + " is",
                    " we ": " " + company + " ",
                    " We ": " " + company + " ",
                    " our ": " " + company + "'s ",
                    " Our ": " " + company + "'s "
                    },
                "Airbus":
                    {"The Company": company,
                    "the Company": company,
                     " Company ": " " + company + " "
                    },
                }

for old, new in replacements[company].items():
    text = text.replace(old, new)

pprint(text)
print('---------------------------')

#%%
nlp = spacy.load("en_core_web_lg")
nlp.add_pipe('coreferee')
# nlp.add_pipe("xx_coref", config={"chunk_size": 2500, "chunk_overlap": 2, "device": 0})
# doc_coref = nlp(text=text)
# text = doc_coref._.resolved_text
doc = nlp(text=text)

#%%
doc._.coref_chains.print()

#%%
sents_with_ents = list()
sents_with_multiple_ents = list()
ents_to_consider = ["PERSON", "ORG", "GPE"]
doc = nlp(text=text)
for sent in doc.sents:
    entity_list = [(ent.label_, ent.text) for ent in sent.ents]
    entity_to_consider_list = [(ent.label_, ent.text) for ent in sent.ents if ent.label_ in ents_to_consider]
    if len(entity_to_consider_list) > 0:
        print(f'ent_types: {entity_to_consider_list}\n'
            f'sent:\n'
              f'{sent.text}')
        print('-----------------------------------------------------------')
    if 0 < len(entity_list) < 2:
        sents_with_ents.append(sent.text)
    if 2 <= len(entity_list):
        sents_with_multiple_ents.append(sent.text)

#%%
# Switch here:
which_sents = sents_with_multiple_ents
entity_sents = " ".join(which_sents)
doc_ents = nlp(text=entity_sents)

#%%
styles = ["ent", "dep"]
style = styles[1]
from spacy import displacy
displacy_output = displacy.serve(doc_ents, style=style, host="localhost", auto_select_port=True)