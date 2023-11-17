#%%
import logging
import pathlib
from xbrl.cache import HttpCache
from xbrl.taxonomy import TaxonomySchema, parse_taxonomy_url, parse_taxonomy
from xbrl.linkbase import PresentationArc
# just to see which research are downloaded
logging.basicConfig(level=logging.INFO)

from settings import path_data

#%%
folder_path = pathlib.Path(path_data, 'XBRLs', 'cache').as_posix()
xsd_ifrs: pathlib.Path = pathlib.Path(folder_path, "xbrl.ifrs.org/taxonomy/2021-03-24/full_ifrs_entry_point_2021-03-24.xsd")
xsd_esef: pathlib.Path = pathlib.Path(folder_path, "www.esma.europa.eu/taxonomy/2021-03-24/esef_cor.xsd")
uri_ifrs: str = "https://xbrl.ifrs.org/taxonomy/2021-03-24/full_ifrs_entry_point_2021-03-24.xsd"
uri_esef: str = "https://www.esma.europa.eu/taxonomy/2019-03-27/esef_all.xsd"

cache: HttpCache = HttpCache(cache_dir=folder_path, verify_https=True)

#%%

def print_presentation_arc(level: int, arc: PresentationArc):
    print(f"{'  ' * level}{arc.to_locator.concept_id}")
    for child_arc in arc.to_locator.children:
        print_presentation_arc(level + 1, child_arc)


# select taxonomy:
xsd_selected = uri_ifrs

if isinstance(xsd_selected, str):
    taxonomy: TaxonomySchema = parse_taxonomy_url(xsd_selected, cache)
else:
    taxonomy: TaxonomySchema = parse_taxonomy(xsd_selected, cache)

for pre_linkbase in taxonomy.pre_linkbases:
    for elr in pre_linkbase.extended_links:
        print(f"/n/n")
        print(elr.elr_id.split('#')[1])
        # if the elr is empty, skip it
        if len(elr.root_locators) == 0: continue
        # print abstract
        print(f"  {elr.root_locators[0].concept_id}")
        for root_locator in elr.root_locators:
            for pre_arc in root_locator.children:
                print_presentation_arc(2, pre_arc)

print('Done!')