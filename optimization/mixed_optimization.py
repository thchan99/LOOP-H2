import numpy as np
import pandas as pd

from config.constants import DAYS_PER_YEAR, TRANSPORT_COST_PER_KG_KM_DEFAULT
from model.economics import get_capex_weight_series, get_transport_scale
from model.economics_mixed import summarize_mixed_solution_economics

try:
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix
except ImportError as exc:
    Bounds = None
    LinearConstraint = None
    milp = None
    lil_matrix = None
    _MILP_IMPORT_ERROR = exc
else:
    _MILP_IMPORT_ERROR = None


PMAX_COL = "Max H2 Production Capacity (kg/day)"
DEMAND_COL = "Demand (kg/day)"
SUPPLY_LAT = "Latitude"
SUPPLY_LON = "Longitude"
DEMAND_LAT = "Latitude"
DEMAND_LON = "Longitude"

PROP_CAPEX_COL = "Proportional Capital Cost"
PROP_OPEX_COL = "Proportional Operating Cost"
CONST_CAPEX_COL = "Constant Capital Cost"
CONST_OPEX_COL = "Constant Operating Cost"

TRANSPORT_COST_PER_KG_KM = TRANSPORT_COST_PER_KG_KM_DEFAULT


def optimize_transport_milp(
    df_prod,
    df_demand,
    params,
    h2_price,
    graphene_price,
    graphene_percent,
    require_full_demand=True,
    verbose=False,
):
    """Solve production and transport with fixed-cost site activation via MILP.

    Decision variables:
    - x_ij: shipment from supply i to demand j (kg/day)
    - p_i: production at supply i (kg/day)
    - z_i: site open decision for supply i (binary)

    Optional siting controls in params:
    - exact_hydrofleet_sites: enforce exactly K hydrofleet sites open
    - max_hydrofleet_sites: enforce at most K hydrofleet sites open
    - min_hydrofleet_sites: enforce at least K hydrofleet sites open
    """
    if milp is None:
        raise ImportError(
            "scipy.optimize.milp is required for mixed optimization but is unavailable in the current environment."
        ) from _MILP_IMPORT_ERROR

    transport_weight = float(params.get("transport_weight", 0.0))
    water_weight = float(params.get("water_weight", 0.0))
    graphene_fraction = float(graphene_percent) / 100.0
    oversize_index = params.get("oversize_index", 0)
    if oversize_index is None:
        oversize_index = 0
    margin_mult = 1.0 + float(oversize_index / 100.0)

    df_prod = df_prod.reset_index(drop=True).copy()
    df_demand = df_demand.reset_index(drop=True).copy()

    S = len(df_prod)
    D = len(df_demand)

    if S == 0:
        raise ValueError("No production sites provided to MILP optimizer.")
    if D == 0:
        raise ValueError("No demand points provided to MILP optimizer.")

    dem = df_demand[DEMAND_COL].to_numpy(float)
    pmax = df_prod[PMAX_COL].to_numpy(float)

    prop_capex = df_prod.get(PROP_CAPEX_COL, pd.Series(0.0, index=df_prod.index)).to_numpy(float)
    prop_opex = df_prod.get(PROP_OPEX_COL, pd.Series(0.0, index=df_prod.index)).to_numpy(float)
    const_capex = df_prod.get(CONST_CAPEX_COL, pd.Series(0.0, index=df_prod.index)).to_numpy(float)
    const_opex = df_prod.get(CONST_OPEX_COL, pd.Series(0.0, index=df_prod.index)).to_numpy(float)

    graph_prop = df_prod.get("Graphene Prop", pd.Series(0.0, index=df_prod.index)).to_numpy(float)
    target_capacity = dem.sum() * margin_mult

    if require_full_demand and pmax.sum() + 1e-9 < target_capacity:
        raise ValueError(
            f"Infeasible: total state supply cap {pmax.sum():.0f} kg/day is less than the required oversized capacity of {target_capacity:.0f} kg/day."
        )

    s_lat = df_prod[SUPPLY_LAT].to_numpy(float)[:, None]
    s_lon = df_prod[SUPPLY_LON].to_numpy(float)[:, None]
    d_lat = df_demand[DEMAND_LAT].to_numpy(float)[None, :]
    d_lon = df_demand[DEMAND_LON].to_numpy(float)[None, :]

    dist_km = haversine_km(s_lat, s_lon, d_lat, d_lon)
    c_tr = DAYS_PER_YEAR * TRANSPORT_COST_PER_KG_KM * dist_km

    rev_per_kg = DAYS_PER_YEAR * (
        h2_price * np.ones(S) + graphene_fraction * graphene_price * graph_prop
    )

    capex_weight = get_capex_weight_series(df_prod["Type"], water_weight).to_numpy(float)
    transport_scale = get_transport_scale(transport_weight)

    # Only hydrofleet sites need binary open/close decisions.
    # All other site types (landfill, existing) are always available — their z is fixed to 1.
    hydrofleet_mask = df_prod["Type"].astype(str).str.lower().eq("hydrofleet").to_numpy()
    hydrofleet_idx = np.where(hydrofleet_mask)[0]

    n_x = S * D
    n_p = S
    n_z = S
    nvar = n_x + n_p + n_z

    idx_x_start = 0
    idx_p_start = n_x
    idx_z_start = n_x + n_p

    c = np.zeros(nvar)
    c_x = (prop_opex[:, None] + transport_scale * c_tr) - rev_per_kg[:, None]
    c[idx_x_start:idx_p_start] = c_x.reshape(-1)
    c[idx_p_start:idx_z_start] = prop_capex * capex_weight
    c[idx_z_start:] = const_capex * capex_weight + const_opex

    lb = np.zeros(nvar)
    ub = np.full(nvar, np.inf)
    ub[idx_p_start:idx_z_start] = pmax
    # Non-hydrofleet sites: z fixed at 1 (always open, no binary decision needed)
    ub[idx_z_start:] = 1.0
    lb[idx_z_start + np.where(~hydrofleet_mask)[0]] = 1.0

    # Binary only for hydrofleet z variables — dramatically reduces MIP tree size
    integrality = np.zeros(nvar, dtype=int)
    integrality[idx_z_start + hydrofleet_idx] = 1

    max_hydrofleet_sites = params.get("max_hydrofleet_sites")
    min_hydrofleet_sites = params.get("min_hydrofleet_sites")
    exact_hydrofleet_sites = params.get("exact_hydrofleet_sites")

    extra_rows = 0
    if exact_hydrofleet_sites is not None:
        extra_rows += 1
    else:
        if min_hydrofleet_sites is not None:
            extra_rows += 1
        if max_hydrofleet_sites is not None:
            extra_rows += 1

    n_rows = S + D + S + extra_rows
    A = lil_matrix((n_rows, nvar), dtype=float)
    b_l = np.full(n_rows, -np.inf, dtype=float)
    b_u = np.full(n_rows, np.inf, dtype=float)

    row = 0
    for i in range(S):
        A[row, i * D:(i + 1) * D] = margin_mult
        A[row, idx_p_start + i] = -1.0
        b_u[row] = 0.0
        row += 1

    for j in range(D):
        A[row, j:n_x:D] = 1.0
        if require_full_demand:
            b_l[row] = dem[j]
            b_u[row] = dem[j]
        else:
            b_u[row] = dem[j]
        row += 1

    for i in range(S):
        A[row, idx_p_start + i] = 1.0
        A[row, idx_z_start + i] = -pmax[i]
        b_u[row] = 0.0
        row += 1

    if extra_rows > 0:
        if hydrofleet_idx.size == 0:
            raise ValueError(
                "Hydrofleet site-count constraints were requested, but no hydrofleet candidates exist in df_prod."
            )

        if exact_hydrofleet_sites is not None:
            k_exact = int(exact_hydrofleet_sites)
            A[row, idx_z_start + hydrofleet_idx] = 1.0
            b_l[row] = float(k_exact)
            b_u[row] = float(k_exact)
            row += 1
        else:
            if min_hydrofleet_sites is not None:
                k_min = int(min_hydrofleet_sites)
                A[row, idx_z_start + hydrofleet_idx] = 1.0
                b_l[row] = float(k_min)
                row += 1
            if max_hydrofleet_sites is not None:
                k_max = int(max_hydrofleet_sites)
                A[row, idx_z_start + hydrofleet_idx] = 1.0
                b_u[row] = float(k_max)
                row += 1

    constraints = LinearConstraint(A.tocsr(), b_l, b_u)
    bounds = Bounds(lb, ub)

    solver_options = {
        "time_limit": float(params.get("time_limit", 60.0)),
        "mip_rel_gap": float(params.get("mip_rel_gap", 0.05)),
        "presolve": True,
    }

    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints, options=solver_options)
    # Accept both optimal and time-limit/gap-stopped solutions (status 0 and 3)
    if res.x is None:
        raise RuntimeError(f"MILP optimization failed: {res.message}")

    sol = res.x
    X = sol[idx_x_start:idx_p_start].reshape(S, D)
    P = sol[idx_p_start:idx_z_start]
    Z = sol[idx_z_start:]

    shipments = []
    for i in range(S):
        for j in range(D):
            if X[i, j] > 1e-9:
                shipments.append(
                    {
                        "supply_idx": i,
                        "demand_idx": j,
                        "ship_kg_day": float(X[i, j]),
                        "dist_km": float(dist_km[i, j]),
                        "transport_cost": float(X[i, j] * c_tr[i, j]),
                    }
                )

    df_ship = pd.DataFrame(shipments)

    shipped_by_supply = X.sum(axis=1)
    total_h2_supplied = float(X.sum())
    total_graphene_supplied = float((X * graph_prop[:, None]).sum())

    df_prod_summary = df_prod.copy()
    df_prod_summary["H2 Production Capacity (kg/day)"] = pd.Series(P, index=df_prod_summary.index).fillna(0.0)
    df_prod_summary["Total H2 Shipped (kg/day)"] = pd.Series(shipped_by_supply, index=df_prod_summary.index).fillna(0.0)
    df_prod_summary["Site Active"] = (pd.Series(Z, index=df_prod_summary.index) > 0.5).astype(int)

    economics = summarize_mixed_solution_economics(
        df_prod_summary,
        df_demand,
        df_ship,
        h2_price,
        graphene_price,
        graphene_fraction,
        transport_weight=transport_weight,
        water_weight=water_weight,
    )
    totals = economics["totals"]
    objective_totals = economics["objective_totals"]

    summary = {
        "capex_term": totals["capex"],
        "opex_term": totals["opex"],
        "transport_term": totals["transport"],
        "total_demand": float(dem.sum()),
        "total_shipped_kg_day": total_h2_supplied,
        "total_graphene_kg_day": total_graphene_supplied,
        "total_revenue": totals["revenue"],
        "total_profit": totals["profit"],
        "objective_capex_term": objective_totals["capex"],
        "objective_opex_term": objective_totals["opex"],
        "objective_transport_term": objective_totals["transport"],
        "objective_profit": objective_totals["profit"],
        "total_built_capacity": float(P.sum()),
        "total_supply": total_h2_supplied,
        "total_max_capacity_available_kg_day": float(pmax.sum()),
        "active_sites": int((Z > 0.5).sum()),
        "hydrofleet_active_sites": int(((Z > 0.5) & hydrofleet_mask).sum()),
        "solver_status": res.message,
    }

    if verbose:
        print("MILP Solver Status:", res.message)

    return X, P, Z, df_ship, summary


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    r_earth_km = 6371.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 2.0 * r_earth_km * np.arcsin(np.sqrt(a))
