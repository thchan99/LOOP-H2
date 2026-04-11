import os

import pandas as pd
from config.constants import (
    HYDROFLEET_H2_PROD_CAPACITY_KG_DAY,
    HYDROFLEET_CAPITAL_COST_PROP,
    HYDROFLEET_CAPITAL_COST_CONST,
    HYDROFLEET_OPEX_COST_PROP,
    HYDROFLEET_OPEX_COST_CONST
)

# compute output directory relative to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output_files")
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

PROD_FINAL_COLS = ["Latitude", "Longitude", "Max H2 Production Capacity (kg/day)", "Proportional Capital Cost", "Proportional Operating Cost", "Constant Capital Cost", "Constant Operating Cost", "Capital Cost Per H2", "Operating Cost Per H2", "Graphene Prop", "Type"]

def getHydrofleetDB(df_demand, verbose = False):
    df_hydrofleet =  df_demand[["Latitude", "Longitude"]].copy()
    df_hydrofleet["Type"] = "hydrofleet"
    df_hydrofleet["Max H2 Production Capacity (kg/day)"] = HYDROFLEET_H2_PROD_CAPACITY_KG_DAY
    df_hydrofleet["Proportional Capital Cost"] = HYDROFLEET_CAPITAL_COST_PROP
    df_hydrofleet["Proportional Operating Cost"] = HYDROFLEET_OPEX_COST_PROP
    df_hydrofleet["Constant Capital Cost"] = HYDROFLEET_CAPITAL_COST_CONST
    df_hydrofleet["Constant Operating Cost"] = HYDROFLEET_OPEX_COST_CONST

    # Keep both fixed and proportional components explicit for MILP;
    # this per-H2 view is retained for compatibility with the existing LP path.
    capacity = df_hydrofleet["Max H2 Production Capacity (kg/day)"]
    df_hydrofleet["Capital Cost Per H2"] = df_hydrofleet["Proportional Capital Cost"] + (
        df_hydrofleet["Constant Capital Cost"] / capacity.where(capacity > 0, 1.0)
    )
    df_hydrofleet["Operating Cost Per H2"] = df_hydrofleet["Proportional Operating Cost"] + (
        df_hydrofleet["Constant Operating Cost"] / capacity.where(capacity > 0, 1.0)
    )

    df_hydrofleet["Graphene Prop"] = 0.0  # Assuming no graphene production for hydrofleet sites
    df_hydrofleet = df_hydrofleet[PROD_FINAL_COLS]
    if verbose:
        df_hydrofleet.to_excel(os.path.join(OUTPUT_DIR, "hydrofleet_production_sites.xlsx"), index=False)
    return df_hydrofleet



# def get_hydrofleet_costs(verbose = False):
    