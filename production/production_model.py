import pandas as pd
# import numpy as np
import os
from production.landfill import get_landfillDB
from production.existing_infrastructure import getExistingProdDB
from production.hydrofleet import getHydrofleetDB

# determine output directory relative to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output_files")

if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)


class ProductionModel:
    def __init__(self, landfill_file_path, demand_db, verbose=False):
        self.landfill_file_path = landfill_file_path
        self.demand_db = demand_db
        self.verbose = verbose
        self.landfill_DB = get_landfillDB(self.landfill_file_path, self.verbose)
        self.existing_DB = getExistingProdDB(self.verbose)
        self.hydrofleet_DB = getHydrofleetDB(self.demand_db, self.verbose)
    
    def get_productionDB(self):
        prod_DB = pd.concat(
            [self.landfill_DB, self.existing_DB, self.hydrofleet_DB],
            ignore_index=True,
            sort=False
        )

        if self.verbose:
            prod_DB.to_excel(os.path.join(OUTPUT_DIR, "production_sites.xlsx"), index=False)
        return prod_DB
    
    def updateHydrofleetDB(self, demand_db):
        self.demand_db = demand_db
        self.hydrofleet_DB = getHydrofleetDB(self.demand_db, self.verbose)