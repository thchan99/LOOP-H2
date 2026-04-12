"""
Global constants for LOOP-H2 project.

This module centralizes all universally constant values used across the project.
Units are indicated in comments for each constant group.

Unit conventions:
- Distances/lengths: feet
- Volumes of landfill gas (LFG): cubic feet (ft^3); "mmscfd" = million standard cubic feet/day
- Mass: tons (short tons) for waste, kilograms (kg) for hydrogen
- Time: years for durations, days for production rates
- Energy: kilowatt-hours (kWh)
- Costs: US dollars ($)
"""

# Demand Sheet Param
DEMAND_SHEET_NUM = 0
DEMAND_DIST_CENTER_SHEET_NUM = 2

# Physical conversion constants
SCF_TO_NM3 = 0.0283168      # standard cubic feet to normal cubic meters (Nm3/scf)
H2_KG_PER_NM3 = 0.08988     # kg H2 per normal cubic meter at STP (kg/Nm3)
H2_TO_DIESEL_MASS_RATIO = 5.0

# Economic defaults
GA_DAILY_DIESEL_CONSUMPTION_KG = 11495307.0  # Based on EIA 2024 Transportation Distillate Fuel Oil Consumption for GA
PRICE_ELECTRICITY_PER_KWH_DEFAULT = 0.1     # $ per kWh
CAPACITY_FACTOR_DEFAULT = 0.9               # fraction (0-1)
DAYS_PER_YEAR = 365.25                       # days/year
TRANSPORT_COST_PER_KG_KM_DEFAULT = 0.02  # $ per kg
TRANSPORT_BOOST = 75.0                      # unitless objective scaling factor (calibrated from baseline objective magnitudes)
WATER_BOOST = 10.0                          # unitless objective scaling factor


# LFG generation model constants
CURR_YEAR = 2025                # reference year for calculations
DATA_COLLECTED_YEAR = 2022      # data cutoff year used in generation model
DECAY_CONST_K = 0.017329        # decay constant (1/year) from calibration
L0_CONSTANT = 3855.406          # empirical constant used in LFG model (ft^3 per ton-year?)
DEFAULT_METHANE_PERCENT = 50    # default methane content in LFG if not specified (1-100)

# BCS and well cost defaults
AVG_WASTE_DEPTH_FT = 65                     # feet
NUM_WELLS_PER_MMSCFD = 47.913               # wells per MMscf/day of LFG
DRILL_CAPEX_PER_FT = 85                     # $ per ft of productive depth
GATHERING_CAPEX_PER_WELL = 17000            # $ per well
SURVEYING_CAPEX_PER_WELL = 700              # $ per well
DRILLING_COST_TOTAL_DEFAULT = 20000         # $ total fixed drilling cost

# Flare and operating defaults
FLARE_CAPEX_CONST = 13700                   # $ fixed flare capital cost
FLARE_CAPEX_PROP_PER_KG_DAY = 112           # $ per (kg/day of H2) proportional
OPEX_COST_CONST_DEFAULT = 5100              # $ per year fixed O&M (BCS)
OPEX_COST_PER_WELL_PER_YEAR = 2600          # $ per well per year
BCS_ELECTRICITY_RATE_KWH_PER_FT3 = 0.002    # kWh per ft^3 of LFG

# Levidian / conversion empirical defaults
INPUT_FLOW_M3_PER_HR = 10.0     # m3/hr (feedstock input for Levidian empirical data)
OUTPUT_FLOW_KG_PER_HR = 2.0     # kg/hr H2 (empirical output)
GRAPHENE_PROP_DEFAULT = 1.0     # Graphene (kh/hr) produced per kg/hr H2.
LEV_H2_PROD_RATE_PER_HR_DEFAULT = 2             # kg/hr H2 per Levidian unit (default)
LEV_ELECTRICITY_RATE_KWH_PER_HR_DEFAULT = 90    # kWh/hr per unit (default)
LEVIDIAN_PURCHASE_COST = 5000000                # $ per machine (purchase+installation)
LEVIDIAN_LEASE_COST_PER_MONTH = 10000           # $ per month per machine

# Hydrofleet equipment & cost defaults
HYDROFLEET_H2_PROD_CAPACITY_KG_DAY = 120000  # kg/day (max production capacity per unit)
HYDROFLEET_CAPITAL_COST_PROP = 27500        # $ per (kg/day) proportional capital cost
HYDROFLEET_CAPITAL_COST_CONST = 275000000   # $ fixed capital cost
HYDROFLEET_OPEX_COST_PROP = 0.0             # $ per (kg/day) proportional operating cost
HYDROFLEET_OPEX_COST_CONST = 0.0            # $ fixed operating cost per year

# Existing production sites (coordinates, capacity, and costs)
# Units: latitude/longitude (decimal degrees), capacity (kg/day), costs ($)
EXIST_PROD_PLUG_LAT = 30.841815335225338
EXIST_PROD_PLUG_LON = -81.67894597617449
EXIST_PROD_PLUG_CAPACITY_KG_DAY = 15000    # kg/day
EXIST_PROD_PLUG_CAPITAL_COST_CONST = 0.0   # $ fixed capital cost
EXIST_PROD_PLUG_OPEX_COST_CONST = 0.0      # $ operating cost (per kg H2)
EXIST_PROD_PLUG_CAPITAL_COST_PROP = 0.0    # $ per (kg/day)
EXIST_PROD_PLUG_OPEX_COST_PROP = 15.0      # $ per kg (proportional operating)

EXIST_PROD_SAVANNAH_LAT = 32.113363951846694
EXIST_PROD_SAVANNAH_LON = -81.27713504232894
EXIST_PROD_SAVANNAH_CAPACITY_KG_DAY = 4200      # kg/day
EXIST_PROD_SAVANNAH_CAPITAL_COST_CONST = 0.0    # $ fixed capital cost
EXIST_PROD_SAVANNAH_OPEX_COST_CONST = 15.0      # $ operating cost (per kg H2)
EXIST_PROD_SAVANNAH_CAPITAL_COST_PROP = 0.0     # $ per (kg/day)
EXIST_PROD_SAVANNAH_OPEX_COST_PROP = 15.0       # $ per kg (proportional operating)