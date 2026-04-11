import os
import pandas as pd
import numpy as np
from production.production_model import ProductionModel
from demand.demand_model import get_demandDB
from optimization.optimization import optimize_transport_lp
from optimization.mixed_optimization import optimize_transport_milp

def _check_supply_feasibility(df_prod, total_demand, max_hydrofleet_sites=None, oversize_index=0):
    """Raise ValueError before calling any solver if supply cannot cover demand.

    For MILP: hydrofleet contribution is capped at max_hydrofleet_sites × unit_capacity.
    For LP (no site cap): all hydrofleet capacity is counted.
    """
    margin = 1.0 + float(oversize_index or 0) / 100.0
    target = total_demand * margin

    hydrofleet_mask = df_prod["Type"].astype(str).str.lower().eq("hydrofleet")
    non_hydrofleet_cap = float(df_prod.loc[~hydrofleet_mask, "Max H2 Production Capacity (kg/day)"].sum())

    if max_hydrofleet_sites is not None:
        # All hydrofleet units share the same per-unit capacity; use the max of the column.
        unit_cap = df_prod.loc[hydrofleet_mask, "Max H2 Production Capacity (kg/day)"].max()
        unit_cap = 0.0 if (unit_cap is None or pd.isna(unit_cap)) else float(unit_cap)
        hydrofleet_cap = int(max_hydrofleet_sites) * unit_cap
        site_note = f", limited to {max_hydrofleet_sites} hydrofleet site(s) × {unit_cap:,.0f} kg/day each"
    else:
        hydrofleet_cap = float(df_prod.loc[hydrofleet_mask, "Max H2 Production Capacity (kg/day)"].sum())
        site_note = ""

    total_cap = non_hydrofleet_cap + hydrofleet_cap
    if total_cap + 1e-9 < target:
        raise ValueError(
            f"Infeasible: maximum available supply {total_cap:,.0f} kg/day"
            f"{site_note} cannot meet the required demand of {target:,.0f} kg/day. "
            "Try increasing the hydrofleet site limit, enabling more production types, or reducing demand."
        )


class Model:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))   # directory of this .py file
        self.verbose = False
        self.use_mixed_optimization = True
        self.milp_time_limit = 30.0   # seconds — increase for better quality, lower for speed
        self.milp_mip_rel_gap = 0.05  # 5 % gap tolerance — solver stops when within 5 % of optimal
        self.folder_path = os.path.abspath(os.path.join(base_dir, "..", "data"))
        self.landfill_file_name = "landfill_dataGA.xlsx"
        self.demand_file_name = "supply_demand_final.xlsx"

        self.landfill_file_path = os.path.join(self.folder_path, self.landfill_file_name)
        self.demand_file_path = os.path.join(self.folder_path, self.demand_file_name)


        self.demand_database = get_demandDB(self.demand_file_path, verbose=self.verbose)
        self.prodModel = ProductionModel(self.landfill_file_path, self.demand_database, verbose=self.verbose)
        self.prod_database = self.prodModel.get_productionDB()

    def get_optimal_soln(self, user_params):

        # Filter Demand Centers
        demand_sheet_num = user_params.get("demand_sheet_num")
        if demand_sheet_num is None:
            df_demand = self.demand_database.copy()
        else:
            df_demand = get_demandDB(self.demand_file_path, sheet_num=demand_sheet_num, verbose=self.verbose).copy()

        selected_routes = user_params["routes"]
        demand_types = df_demand["Type"].astype(str).str.strip().str.lower()
        truck_mask = demand_types == "truck"

        # Keep all non-truck demand; keep only truck demand that matches selected routes
        df_demand = df_demand[(~truck_mask) | (df_demand["Route"].isin(selected_routes))].copy()

        # Apply the dashboard percentage to each demand type
        demand_type_scales = {
            "truck": user_params.get("fleetconv", 100) / 100.0,
            "amazon": user_params.get("distcenter_az", 100) / 100.0,
            "walmart": user_params.get("distcenter_wm", 100) / 100.0,
            "warehouse": user_params.get("distcenter_hd", 100) / 100.0,
        }
        df_demand["Type"] = df_demand["Type"].astype(str).str.strip().str.lower()
        for demand_type, scale in demand_type_scales.items():
            df_demand.loc[df_demand["Type"] == demand_type, "Demand (kg/day)"] *= scale

        df_demand = df_demand.reset_index(drop=True)

        # Extract optimizer weights
        oversize_index = user_params.get("oversize_index", 0)
        # n_hydrofleet from the dashboard slider acts as an upper bound on active hydrofleet sites,
        # but only when hydrofleet infrastructure is enabled in production options.
        selected_prod_options = user_params.get("prodoptions", [])
        hydrofleet_selected = any(str(opt).strip().lower() == "hydrofleet" for opt in selected_prod_options)
        max_hydrofleet_sites = user_params.get("n_hydrofleet") if hydrofleet_selected and user_params.get("n_hydrofleet") is not None else None
        solver_params = {
            'transport_weight': user_params.get("k_transport", 5),
            'water_weight': user_params.get("k_water", 5),
            'oversize_index': oversize_index,
            # MILP solver controls: cap wall-clock time and accept near-optimal solutions
            'time_limit': user_params.get("milp_time_limit", user_params.get("time_limit", self.milp_time_limit)),
            'mip_rel_gap': user_params.get("milp_mip_rel_gap", user_params.get("mip_rel_gap", self.milp_mip_rel_gap)),
            # Hydrofleet site-count limit (MILP uses it as a hard constraint)
            'max_hydrofleet_sites': max_hydrofleet_sites,
        }

        #  Filter production sites according to prod options
        self.prodModel.updateHydrofleetDB(df_demand)  # Update hydrofleet production sites based on new demand
        self.prod_database = self.prodModel.get_productionDB()  # Refresh production database with updated hydrofleet sites
        df_prod = self.prod_database.copy()
        options = selected_prod_options
        df_prod = df_prod[df_prod["Type"].isin(options)]
        df_prod.reset_index(drop=True, inplace=True)

        # --- FEASIBILITY CHECK 1: Did the user uncheck everything? ---
        if df_prod.empty:
            raise ValueError("No production options selected. Please select at least one facility type.")

        # --- FEASIBILITY CHECK 2: Can the selected sites (respecting hydrofleet cap) meet demand? ---
        total_demand = float((df_demand["Demand (kg/day)"] * (1.0 + oversize_index / 100.0)).sum())
        use_mixed_optimization = bool(user_params.get("use_mixed_optimization", self.use_mixed_optimization))
        # For LP there is no structural site limit, so we check without the cap.
        # For MILP we enforce the cap and check feasibility against it.
        feasibility_cap = max_hydrofleet_sites if use_mixed_optimization else None
        _check_supply_feasibility(df_prod, df_demand["Demand (kg/day)"].sum(), feasibility_cap, oversize_index)

        h2_price = user_params.get("h2_sale", 8)
        graphene_price = user_params.get("graphene_sale", 1000)
        graphene_percent = user_params.get("graphene_percent", 0.0)
        # Run the selected optimizer safely (LP or MILP)
        try:
            if use_mixed_optimization:
                try:
                    X, P, Z, df_ship, summary = optimize_transport_milp(
                        df_prod,
                        df_demand,
                        solver_params,
                        h2_price,
                        graphene_price,
                        graphene_percent,
                        verbose=self.verbose,
                    )
                    summary["optimization_mode"] = "mixed_milp"
                except RuntimeError as milp_error:
                    milp_error_msg = str(milp_error)
                    # If MILP reaches a time limit without an incumbent solution,
                    # fall back to LP so the dashboard can still return a plan.
                    if "time limit" in milp_error_msg.lower():
                        X, P, df_ship, summary = optimize_transport_lp(
                            df_prod,
                            df_demand,
                            solver_params,
                            h2_price,
                            graphene_price,
                            graphene_percent,
                            verbose=self.verbose,
                        )
                        Z = None
                        summary["optimization_mode"] = "lp_fallback_after_milp_timeout"
                        summary["fallback_reason"] = milp_error_msg
                    else:
                        raise
            else:
                X, P, df_ship, summary = optimize_transport_lp(
                    df_prod,
                    df_demand,
                    solver_params,
                    h2_price,
                    graphene_price,
                    graphene_percent,
                    verbose=self.verbose,
                )
                Z = None
                summary["optimization_mode"] = "lp"
        except Exception as e:
            # Catches catastrophic solver errors
            raise RuntimeError(f"Optimizer failed to run: {str(e)}")

        # --- FEASIBILITY CHECK 3: Is the model mathematically impossible? ---
        # (e.g., Demand is 10,000 kg but max supply is only 500 kg)
        if P is None or df_ship is None or df_ship.empty:
            raise ValueError("The optimization is infeasible. Demand likely exceeds available supply capacity.")

        # Update Values for Production Sites
        df_prod["H2 Production Capacity (kg/day)"] = pd.Series(P, index=df_prod.index).fillna(0.0)
        if Z is not None:
            df_prod["Site Active"] = (pd.Series(Z, index=df_prod.index) > 0.5).astype(int)

        df_ship2 = (
            df_ship.assign(
                supply_lat  = df_ship["supply_idx"].map(df_prod["Latitude"]),
                supply_lon  = df_ship["supply_idx"].map(df_prod["Longitude"]),
                demand_lat  = df_ship["demand_idx"].map(df_demand["Latitude"]),
                demand_lon  = df_ship["demand_idx"].map(df_demand["Longitude"]),
            )
        )
        
        if not df_ship2.empty:
            shipped_sum = df_ship2.groupby("supply_idx")["ship_kg_day"].sum()
            df_prod["Total H2 Shipped (kg/day)"] = df_prod.index.to_series().map(shipped_sum).fillna(0.0)
        else:
            df_prod["Total H2 Shipped (kg/day)"] = 0.0
        return [df_prod, df_demand, df_ship2, summary]


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))
