# %%
import pandas as pd
from PyPDF2 import PdfReader
import pathlib

from src.settings import path_data, path_pdfs, reports

# %%
data_dict = {"report_name": list(), "report_page": list(), "company": list(), "text": list()}

for list_item in reports:
    reader = PdfReader(pathlib.Path(path_pdfs, list_item["name"]))
    print(f'Processing {list_item["name"]}. This may take a while, please wait ... !')
    for page in list_item["pages"]:
        try:
            data_dict["report_name"].append(list_item["name"])
            data_dict["report_page"].append(page)
            data_dict["company"].append(list_item["company"])
            text = reader.pages[page].extract_text()
            data_dict["text"].append(text)
        except:
            print(f'Error while processing {list_item["name"]}. PDF is skipped, proceed to next PDF.')
print("Extraction finished!")


df = pd.DataFrame(data_dict)
print(df.head(n=10).to_markdown())

#%%
# Clean text:
from src.Testing.pdf_to_text.text_cleaning import clean
cleaner = clean.CleanText()
df["clean_text"] = df["text"].map(cleaner.clean)
print(df.to_markdown())

#%%
for list_item in reports:
    df_grouped = df.groupby(['company']).get_group(list_item['company'])
    text = df_grouped.clean_text.str.cat(sep=' ')
    with open(file=pathlib.Path(path_pdfs, "pdf_texts_with_entities", f"{list_item['company']}_text_with_ents.txt"), mode='w', encoding="UTF-8") as f:
        f.write(text)

#%%
name_of_file = 'text_annual_reports'
path_of_file = pathlib.Path(path_data, name_of_file)
df.to_feather(path=path_of_file)
print(f'File "{name_of_file}" was saved to: {path_of_file}!')

