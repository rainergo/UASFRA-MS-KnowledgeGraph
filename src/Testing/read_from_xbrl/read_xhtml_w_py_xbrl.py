#%%
import logging
import pathlib
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance
# just to see which research are downloaded
logging.basicConfig(level=logging.INFO)

from src.settings import path_data

#%%
name = 'Adidas'

#%%
folder_path = pathlib.Path(path_data, 'XBRLs', 'cache').as_posix()
company_htms = {"Adidas": "adidasag-2022-12-31-de.xhtml",
                 "Philips": "H1FJE8H61JGM1JSGM897-2022-12-31.xhtml",
                "BASF": "basf-gruppe-2022-12-31-de.xhtml"}

htm_path = pathlib.Path(folder_path, 'reports', company_htms[name]).as_posix()

#%%
cache: HttpCache = HttpCache(cache_dir=folder_path, verify_https=True)
parser = XbrlParser(cache)

inst: XbrlInstance = parser.parse_instance(uri=htm_path, encoding="utf-8")
print('Parsing done.')
#%%
# print json to console
print(inst.json(override_fact_ids=True))

# save to file
json_path = pathlib.Path(folder_path, f'{name}.json').as_posix()
inst.json(file_path=json_path)