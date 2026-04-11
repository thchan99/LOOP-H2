import pandas as pd

from config.constants import DAYS_PER_YEAR
from model.economics import get_capex_weight_series, get_transport_scale


PROD_CAPACITY_COL = "H2 Production Capacity (kg/day)"
PROD_SHIPPED_COL = "Total H2 Shipped (kg/day)"
SITE_ACTIVE_COL = "Site Active"
GRAPHENE_PROP_COL = "Graphene Prop"

PROP_CAPEX_COL = "Proportional Capital Cost"
PROP_OPEX_COL = "Proportional Operating Cost"
CONST_CAPEX_COL = "Constant Capital Cost"
CONST_OPEX_COL = "Constant Operating Cost"


def _get_site_activity(df_prod):
    if SITE_ACTIVE_COL in df_prod.columns:
        return pd.to_numeric(df_prod[SITE_ACTIVE_COL], errors="coerce").fillna(0.0).clip(lower=0.0, upper=1.0)
    if PROD_CAPACITY_COL in df_prod.columns:
        return (pd.to_numeric(df_prod[PROD_CAPACITY_COL], errors="coerce").fillna(0.0) > 1e-9).astype(float)
    return pd.Series(0.0, index=df_prod.index, dtype=float)


def summarize_mixed_solution_economics(
    df_prod,
    df_demand,
    df_ship,
    h2_price,
    graphene_price,
    graphene_fraction,
    transport_weight=0.0,
    water_weight=0.0,
):
    df_prod = df_prod.copy()
    df_demand = df_demand.copy()
    df_ship = df_ship.copy() if df_ship is not None else pd.DataFrame()

    if PROD_CAPACITY_COL not in df_prod.columns:
        df_prod[PROD_CAPACITY_COL] = 0.0
    if PROD_SHIPPED_COL not in df_prod.columns:
        df_prod[PROD_SHIPPED_COL] = 0.0
    if GRAPHENE_PROP_COL not in df_prod.columns:
        df_prod[GRAPHENE_PROP_COL] = 0.0

    for cost_col in [PROP_CAPEX_COL, PROP_OPEX_COL, CONST_CAPEX_COL, CONST_OPEX_COL]:
        if cost_col not in df_prod.columns:
            df_prod[cost_col] = 0.0

    if not df_ship.empty and "demand_idx" in df_ship.columns:
        shipped_by_demand = (
            df_ship.groupby("demand_idx")["ship_kg_day"]
            .sum()
            .reindex(df_demand.index, fill_value=0.0)
        )
        demand_series = DAYS_PER_YEAR * float(h2_price) * shipped_by_demand.groupby(df_demand["Type"]).sum()
    else:
        demand_series = pd.Series(dtype=float)

    revenue_dict = demand_series.to_dict()

    graphene_kg_day = df_prod[PROD_SHIPPED_COL] * df_prod[GRAPHENE_PROP_COL]
    graphene_series = DAYS_PER_YEAR * float(graphene_price) * float(graphene_fraction) * graphene_kg_day.groupby(df_prod["Type"]).sum()
    revenue_dict["graphene"] = graphene_series.to_dict()

    site_active = _get_site_activity(df_prod)

    prop_capex_series = (df_prod[PROP_CAPEX_COL] * df_prod[PROD_CAPACITY_COL]).groupby(df_prod["Type"]).sum()
    fixed_capex_series = (df_prod[CONST_CAPEX_COL] * site_active).groupby(df_prod["Type"]).sum()
    capital_series = prop_capex_series.add(fixed_capex_series, fill_value=0.0)
    capital_dict = capital_series.to_dict()

    prop_opex_series = (df_prod[PROP_OPEX_COL] * df_prod[PROD_SHIPPED_COL]).groupby(df_prod["Type"]).sum()
    fixed_opex_series = (df_prod[CONST_OPEX_COL] * site_active).groupby(df_prod["Type"]).sum()
    operating_series = prop_opex_series.add(fixed_opex_series, fill_value=0.0)
    operating_dict = operating_series.to_dict()

    transport_cost = float(df_ship["transport_cost"].sum()) if "transport_cost" in df_ship.columns else 0.0
    operating_dict["transport"] = transport_cost

    total_revenue = float(demand_series.sum() + graphene_series.sum())
    total_capex = float(capital_series.sum())
    total_opex = float(operating_series.sum())
    total_profit = total_revenue - (total_capex + total_opex + transport_cost)

    capex_weights = get_capex_weight_series(df_prod["Type"], water_weight)
    weighted_prop_capex = float((df_prod[PROP_CAPEX_COL] * df_prod[PROD_CAPACITY_COL] * capex_weights).sum())
    weighted_fixed_capex = float((df_prod[CONST_CAPEX_COL] * site_active * capex_weights).sum())
    weighted_capex = weighted_prop_capex + weighted_fixed_capex

    transport_scale = get_transport_scale(transport_weight)
    weighted_transport = float(transport_scale * transport_cost)
    objective_profit = total_revenue - (weighted_capex + total_opex + weighted_transport)

    return {
        "revenue": revenue_dict,
        "capital_cost": capital_dict,
        "operating_cost": operating_dict,
        "totals": {
            "revenue": total_revenue,
            "capex": total_capex,
            "opex": total_opex,
            "transport": transport_cost,
            "profit": total_profit,
        },
        "objective_totals": {
            "capex": weighted_capex,
            "opex": total_opex,
            "transport": weighted_transport,
            "profit": objective_profit,
        },
    }