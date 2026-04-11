import pandas as pd
import numpy as np
import os
# from production.calibrate_landfill_model import calibrate_model
from config.constants import (
    DEFAULT_METHANE_PERCENT,
    GRAPHENE_PROP_DEFAULT,
    SCF_TO_NM3, H2_KG_PER_NM3,
    CURR_YEAR, DATA_COLLECTED_YEAR, DECAY_CONST_K, L0_CONSTANT,
    INPUT_FLOW_M3_PER_HR, OUTPUT_FLOW_KG_PER_HR,
    LEV_H2_PROD_RATE_PER_HR_DEFAULT, LEV_ELECTRICITY_RATE_KWH_PER_HR_DEFAULT,
    LEVIDIAN_PURCHASE_COST, LEVIDIAN_LEASE_COST_PER_MONTH,
    AVG_WASTE_DEPTH_FT, NUM_WELLS_PER_MMSCFD, DRILL_CAPEX_PER_FT,
    GATHERING_CAPEX_PER_WELL, SURVEYING_CAPEX_PER_WELL, DRILLING_COST_TOTAL_DEFAULT,
    FLARE_CAPEX_CONST, FLARE_CAPEX_PROP_PER_KG_DAY, OPEX_COST_CONST_DEFAULT,
    OPEX_COST_PER_WELL_PER_YEAR, BCS_ELECTRICITY_RATE_KWH_PER_FT3,
    PRICE_ELECTRICITY_PER_KWH_DEFAULT, CAPACITY_FACTOR_DEFAULT
)

# output directory relative to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output_files")
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Unit conventions used throughout this module:
# - Distances/lengths: feet
# - Volumes of landfill gas (LFG): cubic feet (ft^3); when expressed as
#   "mmscfd" this means million standard cubic feet per day.
# - Mass: tons (short tons) for waste, kilograms (kg) for hydrogen.
# - Time: years for durations, days for production rates.
# - Energy: kilowatt-hours (kWh) when used.
# - Costs: US dollars ($), per appropriate unit described in comments.
# -----------------------------------------------------------------------------


## These values come from the excel sheet.
LANDFILL_COL_NAMES = ["Landfill ID", "Landfill Name", "Latitude", "Longitude", "Year Landfill Opened", "Landfill Closure Year", "Waste in Place (tons)", 
             "Annual Waste Acceptance Rate (tons per year)", "LFG Generated (mmscfd)", "LFG Collection System In Place?", "LFG Collected (mmscfd)", "Methane Percent"]
LANDFILL_COL_INDICES = [0, 1, 2, 3, 4, 5, 12, 14, 19, 20, 21, 23] 
LANDFILL_DTYPE = {
    "Landfill ID": "Int64",                     # nullable integer
    "Landfill Name": "string",
    "Latitude": "float64",
    "Longitude": "float64",
    "Year Landfill Opened": "Int64",            # nullable integer
    "Landfill Closure Year": "Int64",           # nullable integer
    "Waste in Place (tons)": "float64",
    "Annual Waste Acceptance Rate (tons per year)": "float64",
    "LFG Generated (mmscfd)": "float64",
    "LFG Collection System In Place?": "string",
    "LFG Collected (mmscfd)": "float64",
    "Methane Percent": "float64",
}
PROD_FINAL_COLS = ["Latitude", "Longitude", "Max H2 Production Capacity (kg/day)", "Proportional Capital Cost", "Proportional Operating Cost", "Constant Capital Cost", "Constant Operating Cost", "Capital Cost Per H2", "Operating Cost Per H2", "Graphene Prop", "Type"]

def get_landfillDB(landfill_file_path, verbose = False):
    """Read and process the landfill Excel database.

    Parameters
    ----------
    landfill_file_path : str
        Path to the Excel file containing landfill data. Sheet columns are
        expected to include:
          - "Waste in Place (tons)" (tons of waste)
          - "Annual Waste Acceptance Rate (tons per year)"
          - "LFG Generated (mmscfd)" (million standard cubic feet per day)
          - "LFG Collected (mmscfd)" (same units)
          - "Methane Percent" (percent CH₄ in the gas, 0–100)
        Other columns (lat/long, years) are unitless or self‑explanatory.
    verbose : bool, optional
        If True, some intermediate files and print statements are produced.

    Returns
    -------
    pandas.DataFrame
        Combined dataframe containing both landfills with and without
        collection systems. Columns include production capacity and costs
    """
    df_prod = pd.read_excel(landfill_file_path, sheet_name=0, header=0, usecols=LANDFILL_COL_INDICES, names=LANDFILL_COL_NAMES, dtype=LANDFILL_DTYPE)
    df_prod_yes, df_prod_no = separate_landfills(df_prod, verbose)
    df_prod_yes = process_landfill_with_BCS(df_prod_yes, verbose)
    df_prod_no = process_landfill_without_BCS(df_prod_no, verbose)

    df_prod_combined = pd.concat([df_prod_yes, df_prod_no],ignore_index=True)
    # calibrate_model(df_prod, ch4_default = False, use_relative = False, use_annual = False, use_MAD = False)
    return df_prod_combined



def separate_landfills(df_prod, verbose = False):
    """Split dataframe into landfills with and without a collection system.

    Parameters
    ----------
    df_prod : pandas.DataFrame
        Input dataframe containing at least the following columns with units:
          - "LFG Collection System In Place?" (string yes/no)
          - "LFG Collected (mmscfd)" (mmscfd = million standard cubic feet/day)
    verbose : bool, optional

    Returns
    -------
    df_prod_yes : pandas.DataFrame
        Records where BCS is present and collected flow is provided.
    df_prod_no : pandas.DataFrame
        Records without a BCS or without a valid flow measurement.
    """
    col_sys = "LFG Collection System In Place?"
    col_collected = "LFG Collected (mmscfd)"
    # col_methane = "Methane Percent"
    sys_yes = (df_prod[col_sys].astype("string").str.strip().str.lower().isin(["yes", "y", "true", "1"]))
    mask_yes = sys_yes & df_prod[col_collected].notna()

    df_prod_yes = df_prod.loc[mask_yes].copy()
    df_prod_no = df_prod.loc[~mask_yes].copy()

    if verbose:
        print("Landfill filtering ...")
        print("Total Landfills:", len(df_prod))
        print("Landfills with BCS:", len(df_prod_yes))
        print("Landfills without BCS", len(df_prod_no))
        # print(df_prod_yes.isna().sum())
        # print(df_prod_no.isna().sum())
        print("-------------------------------------------------")

    ## Filter na values
    cols = ["Landfill ID", "Landfill Name",  "Latitude", "Longitude", "LFG Collected (mmscfd)", "Methane Percent"]
    df_prod_yes = df_prod_yes.dropna(subset=cols)
    cols = ["Landfill ID", "Landfill Name",  "Latitude", "Longitude",  "Year Landfill Opened", "Landfill Closure Year", "Waste in Place (tons)"]
    df_prod_no = df_prod_no.dropna(subset=cols)

    if verbose:
        print("Lanfills after filtering na items ...")
        print("Landfills with BCS:", len(df_prod_yes))
        print("Landfills without BCS", len(df_prod_no))
        print("-------------------------------------------------")

    return df_prod_yes, df_prod_no
    

def process_landfill_with_BCS(df_prod, verbose = False):
    """Process records for landfills that already have a collection system.

    The input dataframe is expected to contain
    "LFG Collected (mmscfd)" and "Methane Percent".  The latter is filled
    with a default of {} % if missing.

    The computed "Max H2 Production Capacity" column is returned in kilograms
    of H₂ per day (kg/day).
    """.format(DEFAULT_METHANE_PERCENT)
    df_prod["Type"] = "landfill with bcs"
    df_prod["Methane Percent"] = df_prod["Methane Percent"].fillna(DEFAULT_METHANE_PERCENT)
    df_prod["Max H2 Production Capacity (kg/day)"] = df_prod.apply(lambda row: h2_from_methane(row['LFG Collected (mmscfd)'], row['Methane Percent']), axis=1)
    def _compute_row(row):
        CH4_pct = row.get("Methane Percent", DEFAULT_METHANE_PERCENT)
        (bcs_cap_const, bcs_cap_prop, bcs_ope_const, bcs_ope_prop,
            lev_cap_const, lev_cap_prop, lev_ope_const, lev_ope_prop) = calculate_landfill_costs(CH4_pct, verbose=verbose)
        capacity = row.get("Max H2 Production Capacity (kg/day)")
        row["Proportional Capital Cost"] = lev_cap_prop
        row["Proportional Operating Cost"] = lev_ope_prop
        row["Constant Capital Cost"] = lev_cap_const
        row["Constant Operating Cost"] = lev_ope_const
        # Aggregate totals (units: $)
        row["Capital Cost Per H2"] = lev_cap_prop + lev_cap_const / capacity if capacity > 0 else 0
        row["Operating Cost Per H2"] = lev_ope_prop + lev_ope_const / capacity if capacity > 0 else 0
        return row
    df_prod = df_prod.apply(_compute_row, axis=1)
    df_prod["Graphene Prop"] = GRAPHENE_PROP_DEFAULT # Assuming a default graphene production proportional to H2 for landfills with BCS

    df_prod = df_prod[PROD_FINAL_COLS]
    if verbose:
        df_prod.to_excel(os.path.join(OUTPUT_DIR, "output_landfill_with_BCS.xlsx"), index=False)
    return df_prod



def process_landfill_without_BCS(df_prod, verbose = False):
    """Process landfills that do not yet have a collection system.

    Uses either the provided "LFG Generated (mmscfd)" or computes it based on
    waste in place, opening/closure years via :func:`calculate_LFG_Generation`.
    The resulting LFG flow is in mmscfd (million standard cubic feet/day).
    """
    df_prod["Type"] = "landfill without bcs"
    calc_mask = df_prod["LFG Generated (mmscfd)"].isna()
    df_prod.loc[calc_mask, "Calculated LFG (mmscfd)"] = df_prod.loc[calc_mask].apply(lambda row: calculate_LFG_Generation(row['Waste in Place (tons)'], row['Year Landfill Opened'], row['Landfill Closure Year']), axis=1)
    df_prod.loc[~calc_mask, "Calculated LFG (mmscfd)"] = df_prod.loc[~calc_mask, "LFG Generated (mmscfd)"]
    df_prod["Max H2 Production Capacity (kg/day)"] = df_prod.apply(lambda row: h2_from_methane(row['Calculated LFG (mmscfd)'],DEFAULT_METHANE_PERCENT), axis=1)
    def _compute_row(row):
        CH4_pct = row.get("Methane Percent", DEFAULT_METHANE_PERCENT)
        (bcs_cap_const, bcs_cap_prop, bcs_ope_const, bcs_ope_prop,
            lev_cap_const, lev_cap_prop, lev_ope_const, lev_ope_prop) = calculate_landfill_costs(CH4_pct, verbose=verbose)
        capacity = row.get("Max H2 Production Capacity (kg/day)")
        row["Proportional Capital Cost"] = lev_cap_prop + bcs_cap_prop
        row["Proportional Operating Cost"] = lev_ope_prop + bcs_ope_prop
        # Fixed costs
        row["Constant Capital Cost"] = lev_cap_const + bcs_cap_const
        row["Constant Operating Cost"] = lev_ope_const + bcs_ope_const
        # Aggregate totals (units: $)
        row["Capital Cost Per H2"] = lev_cap_prop + bcs_cap_prop +  lev_cap_const / capacity + bcs_cap_const / capacity if capacity > 0 else 0
        row["Operating Cost Per H2"] = lev_ope_prop + bcs_ope_prop + lev_ope_const / capacity + bcs_ope_const / capacity if capacity > 0 else 0
        return row
    df_prod = df_prod.apply(_compute_row, axis=1)
    df_prod["Graphene Prop"] = GRAPHENE_PROP_DEFAULT # Assuming a default graphene production proportional to H2 for landfills without BCS
    df_prod = df_prod[PROD_FINAL_COLS]
    if verbose:
        df_prod.to_excel(os.path.join(OUTPUT_DIR, "output_landfill_without_BCS.xlsx"), index=False)
    return df_prod


def calculate_LFG_Generation(total_waste, year_open, year_close, verbose = False):
    """Estimate landfill gas (LFG) generation from waste history.

    Parameters
    ----------
    total_waste : float
        Waste in place (tons).
    year_open : int
        Year the landfill opened (e.g. 1990).
    year_close : int
        Year the landfill closed, or current year if still open.
    verbose : bool, optional

    Returns
    -------
    float
        Estimated LFG generation in mmscfd (million standard cubic feet per day).
    """
    # Use module-level constants for years and decay
    # CURR_YEAR, DATA_COLLECTED_YEAR, DECAY_CONST_K, L0_CONSTANT are module constants
    # t_d: years of waste accumulation based on data collection cutoff
    t_d = min(DATA_COLLECTED_YEAR, year_close) - year_open # years
    R = total_waste/t_d  # average waste input rate (tons per year)
    # c: years from last data collection to current year, zero if landfill still open
    c = CURR_YEAR - min(CURR_YEAR, year_close)  # years
    t = CURR_YEAR - year_open  # years since opening
    L0 = L0_CONSTANT
    CH4_percent = DEFAULT_METHANE_PERCENT  # percent methane in LFG
    # Qt computed in ft^3 per year of CH4-equivalent gas. Note: L0 units need
    # verification (comment preserved) — assumed ft^3 per (ton*year) factor.
    Qt = (100.0/CH4_percent) * L0 * R * (np.exp(- DECAY_CONST_K * c) - np.exp(-DECAY_CONST_K * t)) # ft^3/year
    # convert cubic feet per year to million standard cubic feet per day
    Qt_mmscfd = Qt/(365 * 1e6)  # mmscfd
    return Qt_mmscfd


def h2_conversion_factor(CH4_pct):
    """Compute kilograms of hydrogen per day produced per unit of LFG flow.

    Parameters
    ----------
    CH4_pct : float
        Methane concentration in landfill gas expressed as a percentage (0-100).

    Returns
    -------
    float
        The conversion factor in kg H2 per (MMscf/day) of LFG.  Multiply this
        by a flow in mmscfd to obtain kg/day of H₂.
    """
    # Use module-level conversion constants: SCF_TO_NM3, H2_KG_PER_NM3,
    # INPUT_FLOW_M3_PER_HR, OUTPUT_FLOW_KG_PER_HR

    # Fraction of LFG that is CH4 (dimensionless)
    Q_ch4_fraction = (CH4_pct / 100.0)
    # convert methane flow to Nm3/day assuming 1 MMscf = 1e6 scf
    CH4_NM3_PER_DAY_PER_MMSCF = 1e6 * SCF_TO_NM3  # Nm3/day per MMscf/day
    CH4_Nm3_day = Q_ch4_fraction * CH4_NM3_PER_DAY_PER_MMSCF  # Nm3/day of CH4

    # Ideal hydrogen production (Nm3/day) from stoichiometry: 2 Nm3 H2 per Nm3 CH4
    H2_Nm3_day_theo = 2.0 * CH4_Nm3_day  # Nm3/day of H2 theoretical

    # Convert to kg/day using density constant
    H2_kg_day_theo = H2_Nm3_day_theo * H2_KG_PER_NM3  # kg/day theoretical

    # Empirical yield based on Levidian data (m3/hr -> kg/hr)
    yield_factor = OUTPUT_FLOW_KG_PER_HR / INPUT_FLOW_M3_PER_HR  # kg per m3
    # convert yield to kg/day per MMscf/day of LFG
    H2_kg_day_empirical = CH4_NM3_PER_DAY_PER_MMSCF * yield_factor  # kg/day per MMscf/day

    # Return empirical conversion factor (kg H2 per MMscf/day)
    return H2_kg_day_empirical

def h2_from_methane(Q_lfg_mmscfd, CH4_pct):
    """Convert a landfill gas flow to hydrogen production rate.

    Parameters
    ----------
    Q_lfg_mmscfd : float
        Landfill gas flow in million standard cubic feet per day (MMscf/day).
    CH4_pct : float
        Methane concentration in the gas (percent, 0–100).

    Returns
    -------
    float
        Hydrogen production rate in kilograms per day (kg/day).
    """

    # Multiply conversion factor (kg H2 per MMscf/day) by actual LFG flow.
    H2_kg_day = h2_conversion_factor(CH4_pct) * Q_lfg_mmscfd
    return H2_kg_day


def calculate_landfill_costs(CH4_pct, verbose = False):
    """Estimate capital and operating cost parameters for landfill hydrogen.

    Parameters
    ----------
    CH4_pct : float
        Methane concentration in the gas (percent, 0-100).
    verbose : bool, optional

    Returns
    -------
    tuple
        Eight floats corresponding to
        (bcs_cap_const, bcs_cap_prop, bcs_ope_const, bcs_ope_prop,
         lev_cap_const, lev_cap_prop, lev_ope_const, lev_ope_prop).
        Capital costs are in $ (either fixed or $ per kg/day of H2), operating
        costs are in $ (either per year or $ per kg of H2).
    """
    ##--------------------- variables of interest ------------------------
    # Use module-level constants directly
    p_e = PRICE_ELECTRICITY_PER_KWH_DEFAULT  # $ per kWh
    CF = CAPACITY_FACTOR_DEFAULT  # capacity factor (fraction)

    ## This is for Levidian Oldham. Update by changing module-level constants.
    Lev_H2_prod_rate = LEV_H2_PROD_RATE_PER_HR_DEFAULT  # kg H2 produced per hour by one Levidian unit
    Lev_electricity_rate = LEV_ELECTRICITY_RATE_KWH_PER_HR_DEFAULT  # kWh consumed per hour by one unit

    Levidian_purchase_cost = LEVIDIAN_PURCHASE_COST  # $ per machine (purchase + installation)
    Levidian_lease_cost_per_month = LEVIDIAN_LEASE_COST_PER_MONTH  # $ per month per machine


    ##---------------------Calculate Levidian Costs------------------------
    # H2 production from one Levidian unit per day
    H2_lev_day = Lev_H2_prod_rate * 24.0  # kg/day per machine
    # Number of machines required to supply 1 kg/day of H2 (inverse of output)
    N_Lev = 1.0/(CF * H2_lev_day)  # machines per (kg/day of H2)
    lev_cap_prop = Levidian_purchase_cost * N_Lev  # $ per (kg/day of H2) (Capital Cost)
    lev_cap_const = 0.0  # $ fixed capital cost
    # electricity intensity in kWh per kg H2
    e_intensity = Lev_electricity_rate / Lev_H2_prod_rate  # kWh per kg of H2
    # Operating cost proportional component: electricity plus lease cost
    lev_ope_prop = 365.0 * p_e * e_intensity  + Levidian_lease_cost_per_month  * 12.0 * N_Lev  # $ per kg of H2 (Operating Cost)
    lev_ope_const = 0.0  # $ fixed operating cost

    ##################################################################
    ##---------------------Calculate BCS Costs------------------------
    ##################################################################
    # BCS & well cost defaults are module-level constants; use them here
    AVG_WASTE_DEPTH = AVG_WASTE_DEPTH_FT
    num_wells_per_lfg_mmscfd = NUM_WELLS_PER_MMSCFD
    # Convert wells requirement to per kg/day of H2 using conversion factor (kg per MMscf/day)
    num_wells_per_kg_h2_day = num_wells_per_lfg_mmscfd / h2_conversion_factor(CH4_pct)  # wells per (kg/day H2)
    drill_capex_per_well = (AVG_WASTE_DEPTH - 10.0) * DRILL_CAPEX_PER_FT  # $ per well (assumes 10 ft non-productive layer)
    gathering_capex_per_well = GATHERING_CAPEX_PER_WELL
    suverying_capex_per_well = SURVEYING_CAPEX_PER_WELL

    DRILLING_COST_TOTAL = DRILLING_COST_TOTAL_DEFAULT

    ##### Flare cost is non-linear, has to linearize it.
    flare_capex_const = FLARE_CAPEX_CONST
    flare_capex_prop = FLARE_CAPEX_PROP_PER_KG_DAY

    bcs_cap_const = DRILLING_COST_TOTAL + flare_capex_const  # $ (Capital Cost Fixed).
    bcs_cap_prop = (drill_capex_per_well + gathering_capex_per_well + suverying_capex_per_well) * num_wells_per_kg_h2_day + flare_capex_prop  # $ per kg/day of H2 (Capital Cost)

    ##### Operating cost
    opex_cost_const = OPEX_COST_CONST_DEFAULT  # $ per year (fixed operating cost for BCS)
    opex_cost_per_well = OPEX_COST_PER_WELL_PER_YEAR
    # electricity consumption for BCS pumping system
    BCS_electricity_rate = BCS_ELECTRICITY_RATE_KWH_PER_FT3
    # convert to kWh per MMscf of LFG per year (1 MMscf = 1e6 ft^3, 365 days)
    BCS_electricity_rate_per_mmscfd = BCS_electricity_rate * 1e6 * 365.0  # kWh per (MMscf/day) per year
    # electricity cost per kg of H2 assuming CH4 concentration
    opex_cost_electricity_per_kg_h2 = BCS_electricity_rate / h2_conversion_factor(CH4_pct)  # kWh per kg of H2

    bcs_ope_const = opex_cost_const  # $ per year (Operating Cost Fixed)
    # $ per kg of H2 (Operating Cost proportional) including wells + electricity
    bcs_ope_prop = opex_cost_per_well * num_wells_per_kg_h2_day + opex_cost_electricity_per_kg_h2 * p_e  # $ per kg of H2 (Operating Cost)

    return bcs_cap_const, bcs_cap_prop, bcs_ope_const, bcs_ope_prop, lev_cap_const, lev_cap_prop, lev_ope_const, lev_ope_prop