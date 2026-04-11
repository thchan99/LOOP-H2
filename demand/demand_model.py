import pandas as pd
import numpy as np
from config.constants import DEMAND_DIST_CENTER_SHEET_NUM, DEMAND_SHEET_NUM


DEMAND_COL_NAMES = ["Name", "Latitude", "Longitude", "Demand (kg/day)", "Route", "Type"]
DEMAND_COL_INDICES = [0, 1, 2, 3, 4, 5]

DEMAND_DTYPE = {
        "Name": str,
        "Latitude": float,
        "Longitude": float,
        "Demand (kg/day)": float,
        "Type": str,
        "Route": str
        }

def _read_demand_sheet(demand_file_path, sheet_num):
	df_demand = pd.read_excel(
		demand_file_path,
		sheet_name=sheet_num,
		dtype=DEMAND_DTYPE,
		header=0,
		usecols=DEMAND_COL_INDICES,
		names=DEMAND_COL_NAMES,
	)
	# Account for AADT 62kg/refill (from Hyundai)
	df_demand["Demand (kg/day)"] = df_demand["Demand (kg/day)"] * 62
	return df_demand


def get_demandDB(demand_file_path, sheet_num=None, verbose=False):
	selected_sheet = DEMAND_SHEET_NUM if sheet_num is None else int(sheet_num)

	demand_frames = [_read_demand_sheet(demand_file_path, selected_sheet)]
	if selected_sheet != DEMAND_DIST_CENTER_SHEET_NUM:
		demand_frames.append(_read_demand_sheet(demand_file_path, DEMAND_DIST_CENTER_SHEET_NUM))

	df_demand = pd.concat(demand_frames, ignore_index=True)
	df_demand = df_demand.reset_index(drop=True)
	return df_demand
