import pathlib

# PATHS

path_base = pathlib.Path("D:/A_STUDIUM/PYTHON/UASFRA-MS-PROJDIGI/")
path_data = pathlib.Path(path_base, "src/data/")
path_pdfs = pathlib.Path(path_data, "pdfs/")

# PDFs
reports = [
            {"name": "covestro-ar22-entire.pdf", "company": "Covestro", "pages": [11, 12, 16, 17]},
            {"name": "annual-report-adidasag.com-ar22.pdf", "company": "Adidas", "pages": [x for x in range(79, 92)]},
            {"name": "Airbus_Annual_Report_2022.pdf", "company": "Airbus", "pages": [x for x in range(60, 93)]},
            {"name": "basf-ar22.pdf", "company": "BASF", "pages": [x for x in range(135, 151)]},
            {"name": "entire-vw-ar22.pdf", "company": "VW", "pages": [x for x in range(169, 175)]}
           ]
