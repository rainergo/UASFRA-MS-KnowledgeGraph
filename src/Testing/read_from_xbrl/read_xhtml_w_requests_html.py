#%%
from requests_html import HTML

#%%
# load xhtml
xhtml_file = "/data/XBRLs/cache/reports/adidasag-2022-12-31-de.xhtml"
with open(file=xhtml_file, mode="r", encoding="utf-8") as f:
    data = f.read()

html = HTML(html=data)

#%%
elements = html.find('body')
for ele in elements:
    print(ele.links)


