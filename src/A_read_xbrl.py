import pathlib
from enum import StrEnum

from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance

from settings import path_data


class XHTMLName(StrEnum):
    """ Insert name of xhtml-files located in folder '/src/data/XBRLs/raw/reports/'. See: README-data.md """
    Adidas = "adidasag-2022-12-31-de.xhtml"
    Philips = "H1FJE8H61JGM1JSGM897-2022-12-31.xhtml"
    BASF = "basf-gruppe-2022-12-31-de.xhtml"


class XBRL:

    def __init__(self):
        self.source_path: str = pathlib.Path(path_data, 'XBRLs', 'raw').as_posix()
        self.reports_path: str = pathlib.Path(self.source_path, 'reports').as_posix()
        self.target_path: str = pathlib.Path(path_data, 'XBRLs', 'xbrl_to_json').as_posix()

    def read_xbrl_to_json(self, xhtml_name: XHTMLName):
        print(f'XBRL-File for {xhtml_name.name} will be parsed. This might take a few seconds. Please be patient!')
        cache: HttpCache = HttpCache(cache_dir=self.source_path, verify_https=True)
        parser: XbrlParser = XbrlParser(cache=cache)
        xhtml_path: str = pathlib.Path(self.reports_path, xhtml_name).as_posix()
        instance: XbrlInstance = parser.parse_instance(uri=xhtml_path, encoding="utf-8")
        json_path: str = pathlib.Path(self.target_path, f'{xhtml_name.name}.json').as_posix()
        instance.json(file_path=json_path)
        print(f'XBRL-File for {xhtml_name.name} was parsed and the json-file was saved to: {json_path}')


if __name__ == '__main__':
    xbrl = XBRL()
    """ XHTMLName is a StrEnum. Just choose between the Enum.name such as XHTMLName.Adidas or XHTMLName.BASF, etc. """
    xbrl.read_xbrl_to_json(xhtml_name=XHTMLName.Adidas)
