import pandas as pd
import numpy as np
from config.constants import (
    EXIST_PROD_PLUG_LAT, EXIST_PROD_PLUG_LON, EXIST_PROD_PLUG_CAPACITY_KG_DAY,
    EXIST_PROD_PLUG_CAPITAL_COST_CONST, EXIST_PROD_PLUG_OPEX_COST_CONST,
    EXIST_PROD_PLUG_CAPITAL_COST_PROP, EXIST_PROD_PLUG_OPEX_COST_PROP,
    EXIST_PROD_SAVANNAH_LAT, EXIST_PROD_SAVANNAH_LON, EXIST_PROD_SAVANNAH_CAPACITY_KG_DAY,
    EXIST_PROD_SAVANNAH_CAPITAL_COST_CONST, EXIST_PROD_SAVANNAH_OPEX_COST_CONST,
    EXIST_PROD_SAVANNAH_CAPITAL_COST_PROP, EXIST_PROD_SAVANNAH_OPEX_COST_PROP
)

PROD_FINAL_COLS = ["Latitude", "Longitude", "Max H2 Production Capacity (kg/day)", "Proportional Capital Cost", "Proportional Operating Cost", "Constant Capital Cost", "Constant Operating Cost", "Capital Cost Per H2", "Operating Cost Per H2", "Graphene Prop", "Type"]

def getExistingProdDB(verbose = False):
    plug = {
        "Latitude": EXIST_PROD_PLUG_LAT,
        "Longitude": EXIST_PROD_PLUG_LON,
        "Max H2 Production Capacity (kg/day)": EXIST_PROD_PLUG_CAPACITY_KG_DAY,
        "Proportional Capital Cost": EXIST_PROD_PLUG_CAPITAL_COST_PROP,
        "Proportional Operating Cost": EXIST_PROD_PLUG_OPEX_COST_PROP * 365,
        "Constant Capital Cost": EXIST_PROD_PLUG_CAPITAL_COST_CONST,
        "Constant Operating Cost": EXIST_PROD_PLUG_OPEX_COST_CONST * 365,
        "Type": "plug"
    }
    savannah = {
        "Latitude": EXIST_PROD_SAVANNAH_LAT,
        "Longitude": EXIST_PROD_SAVANNAH_LON,
        "Max H2 Production Capacity (kg/day)": EXIST_PROD_SAVANNAH_CAPACITY_KG_DAY,
        "Proportional Capital Cost": EXIST_PROD_SAVANNAH_CAPITAL_COST_PROP,
        "Proportional Operating Cost": EXIST_PROD_SAVANNAH_OPEX_COST_PROP * 365,
        "Constant Capital Cost": EXIST_PROD_SAVANNAH_CAPITAL_COST_CONST,
        "Constant Operating Cost": EXIST_PROD_SAVANNAH_OPEX_COST_CONST * 365,
        "Type": "savannah"
    }
    df = pd.DataFrame([plug, savannah])

    # Compute per-H2 costs (proportional + constant/component per capacity)
    df["Capital Cost Per H2"] = df.apply(lambda r: r["Proportional Capital Cost"] + (r["Constant Capital Cost"] / r["Max H2 Production Capacity (kg/day)"] if r["Max H2 Production Capacity (kg/day)"] > 0 else 0), axis=1)
    df["Operating Cost Per H2"] = df.apply(lambda r: r["Proportional Operating Cost"] + (r["Constant Operating Cost"] / r["Max H2 Production Capacity (kg/day)"] if r["Max H2 Production Capacity (kg/day)"] > 0 else 0), axis=1)
    df["Graphene Prop"] = 0.0  # Assuming no graphene production for existing sites
    df = df[PROD_FINAL_COLS]
    return df
