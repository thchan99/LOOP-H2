import numpy as np
import pandas as pd
from scipy.optimize import linprog
from config.constants import DAYS_PER_YEAR, TRANSPORT_COST_PER_KG_KM_DEFAULT
from model.economics import get_capex_weight_series, get_transport_scale, summarize_solution_economics

pmax_col = "Max H2 Production Capacity (kg/day)"
demand_col = "Demand (kg/day)"
supply_lat = "Latitude"
supply_lon = "Longitude"
demand_lat = "Latitude"
demand_lon = "Longitude"
capex_col = "Capital Cost Per H2"
opex_col = "Operating Cost Per H2"
transport_cost_per_kg_km = TRANSPORT_COST_PER_KG_KM_DEFAULT

def optimize_transport_lp(df_prod, df_demand, params, h2_price, graphene_price, graphene_percent, require_full_demand = True, verbose = False):
    transport_weight = params["transport_weight"]
    water_weight = params["water_weight"]
    graphene_fraction = float(graphene_percent) / 100.0

    oversize_index = params.get("oversize_index", 0)
    if oversize_index is None:
        oversize_index = 0
    margin = 1.0 + float(oversize_index / 100.0)

    df_prod = df_prod.reset_index(drop=True).copy()
    df_demand = df_demand.reset_index(drop=True).copy()

    S = len(df_prod)
    D = len(df_demand)
    # Extract vectors
    dem = df_demand[demand_col].to_numpy(float)          # (D,)
    pmax = df_prod[pmax_col].to_numpy(float)         # (S,)
    capex = df_prod[capex_col].to_numpy(float)       # (S,)
    opex = df_prod[opex_col].to_numpy(float)         # (S,)
    # graphene proportion per kg H2 produced (assumed column present)
    graph_prop = df_prod.get("Graphene Prop", pd.Series(0.0, index=df_prod.index)).to_numpy(float)  # (S,)

    # Feasibility check
    target_capacity = dem.sum() * margin
    if require_full_demand and pmax.sum() + 1e-9 < target_capacity:
        raise ValueError(
            f"Infeasible: total state supply cap {pmax.sum():.0f} kg/day is less than the required oversized capacity of {target_capacity:.0f} kg/day."
        )

    # Compute cost matrix (S x D): distance km * cost_per_kg_km
    s_lat = df_prod[supply_lat].to_numpy(float)[:, None]
    s_lon = df_prod[supply_lon].to_numpy(float)[:, None]
    d_lat = df_demand[demand_lat].to_numpy(float)[None, :]
    d_lon = df_demand[demand_lon].to_numpy(float)[None, :]

    dist_km = haversine_km(s_lat, s_lon, d_lat, d_lon)  # broadcasts -> (S,D)
    c_tr = DAYS_PER_YEAR * transport_cost_per_kg_km * dist_km                # (S,D) Yearly cost per kg shipped

    # Variables: [x (S*D), p (S)]
    n_x = S * D
    n_p = S
    nvar = n_x + n_p
    # Objective vector: we minimize (cost - revenue) which is equivalent to
    # maximizing profit = revenue - cost.
    # Revenue per kg shipped from plant i = h2_price + graphene_percent * graphene_price * graph_prop[i]
    rev_per_kg = DAYS_PER_YEAR * h2_price * np.ones(S) + DAYS_PER_YEAR * graphene_fraction * graphene_price * graph_prop  # shape (S,)

    # Determine capex weight: hydrofleet sites penalized by water_weight
    capex_weight = get_capex_weight_series(df_prod["Type"], water_weight).to_numpy(float)

    c = np.zeros(nvar)
    # piecewise linear scaling:
    # w in [-1,0] -> scale = w + 1  (linear decrease to 0)
    # w in [0,1]  -> scale = 1 + TRANSPORT_BOOST * w  (linear increase to 1+T)
    scale = get_transport_scale(transport_weight)
    # cost minus revenue for x variables
    # (opex_i + scaled transport) - rev_per_kg_i
    # broadcast revenue along demands
    c_x = (opex[:, None] + scale * c_tr) - rev_per_kg[:, None]
    c[:n_x] = c_x.reshape(-1)
    # p variables: only cost side, apply capex weight
    c[n_x:] = capex * capex_weight  # cost on p_i

    # Bounds: x_ij >= 0, 0 <= p_i <= pmax_i
    bounds = [(0, None)] * n_x + [(0, pmax[i]) for i in range(S)]

    # Constraints
    A_ub = []
    b_ub = []

    # (2) sum_j x_ij <= p_i  => sum_j x_ij - p_i <= 0
    for i in range(S):
        row = np.zeros(nvar)
        row[i*D:(i+1)*D] = 1.0
        row[n_x + i] = -1.0
        A_ub.append(row)
        b_ub.append(0.0)
    
    row_oversize = np.zeros(nvar)
    row_oversize[n_x:] = -1.0  # Apply -1 to all built capacity (p_i) variables
    A_ub.append(row_oversize)
    b_ub.append(-target_capacity)

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)

    # (3) demand: sum_i x_ij == d_j
    A_eq = np.zeros((D, nvar))
    for j in range(D):
        A_eq[j, j:n_x:D] = 1.0  # x_0j, x_1j, ... spaced by D
    b_eq = dem.copy()

    if require_full_demand:
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    else:
        # If you allow unmet demand, switch equality to <= by putting it in A_ub.
        A_ub2 = np.vstack([A_ub, A_eq])
        b_ub2 = np.concatenate([b_ub, b_eq])
        res = linprog(c, A_ub=A_ub2, b_ub=b_ub2, bounds=bounds, method="highs")

    if not res.success:
        raise RuntimeError(f"Optimization failed: {res.message}")

    sol = res.x
    X = sol[:n_x].reshape(S, D)
    P = sol[n_x:]

    # Package result as a long table (supply->demand shipments)
    shipments = []
    for i in range(S):
        for j in range(D):
            if X[i, j] > 1e-9:
                shipments.append({
                    "supply_idx": i,
                    "demand_idx": j,
                    "ship_kg_day": float(X[i, j]),
                    "dist_km": float(dist_km[i, j]),
                    "transport_cost": float(X[i, j] * c_tr[i, j])
                })

    df_ship = pd.DataFrame(shipments)

    # Useful Summaries
    shipped_sum = df_ship.groupby("supply_idx")["ship_kg_day"].sum() if not df_ship.empty else pd.Series(dtype=float)
    df_prod_summary = df_prod.copy()
    df_prod_summary["H2 Production Capacity (kg/day)"] = pd.Series(P, index=df_prod_summary.index).fillna(0.0)
    df_prod_summary["Total H2 Shipped (kg/day)"] = df_prod_summary.index.to_series().map(shipped_sum).fillna(0.0)

    economics = summarize_solution_economics(
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
    total_h2_supplied = float(X.sum())
    total_graphene_supplied = float((X * graph_prop[:, None]).sum())

    if verbose:
        print("Solver Status:", res.message)

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
        "solver_status": res.message,
    }

    return X, P, df_ship, summary


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371.0
    lat1 = np.radians(lat1); lon1 = np.radians(lon1)
    lat2 = np.radians(lat2); lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))