import pandas as pd

from config.constants import DAYS_PER_YEAR, TRANSPORT_BOOST, WATER_BOOST


def get_transport_scale(transport_weight):
    weight = float(transport_weight)
    if weight <= 0:
        return weight + 1.0
    return 1.0 + TRANSPORT_BOOST * weight


def get_capex_weight_series(prod_types, water_weight):
    hydrofleet_mask = prod_types.astype(str).str.lower() == "hydrofleet"
    return hydrofleet_mask.map(
        lambda is_hydrofleet: 1.0 + float(water_weight) * WATER_BOOST if is_hydrofleet else 1.0
    ).astype(float)


def summarize_solution_economics(
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

    if "H2 Production Capacity (kg/day)" not in df_prod.columns:
        df_prod["H2 Production Capacity (kg/day)"] = 0.0
    if "Total H2 Shipped (kg/day)" not in df_prod.columns:
        df_prod["Total H2 Shipped (kg/day)"] = 0.0
    if "Graphene Prop" not in df_prod.columns:
        df_prod["Graphene Prop"] = 0.0

    if not df_ship.empty and "demand_idx" in df_ship.columns:
        shipped_by_demand = (
            df_ship.groupby("demand_idx")["ship_kg_day"]
            .sum()
            .reindex(df_demand.index, fill_value=0.0)
        )
        demand_series = DAYS_PER_YEAR * h2_price * shipped_by_demand.groupby(df_demand["Type"]).sum()
    else:
        demand_series = pd.Series(dtype=float)

    revenue_dict = demand_series.to_dict()

    graphene_kg_day = df_prod["Total H2 Shipped (kg/day)"] * df_prod["Graphene Prop"]
    graphene_series = DAYS_PER_YEAR * graphene_price * graphene_fraction * graphene_kg_day.groupby(df_prod["Type"]).sum()
    revenue_dict["graphene"] = graphene_series.to_dict()

    capital_series = (
        df_prod["Capital Cost Per H2"] * df_prod["H2 Production Capacity (kg/day)"]
    ).groupby(df_prod["Type"]).sum()
    capital_dict = capital_series.to_dict()

    opex_series = (
        df_prod["Operating Cost Per H2"] * df_prod["Total H2 Shipped (kg/day)"]
    ).groupby(df_prod["Type"]).sum()
    operating_dict = opex_series.to_dict()

    transport_cost = float(df_ship["transport_cost"].sum()) if "transport_cost" in df_ship.columns else 0.0
    operating_dict["transport"] = transport_cost

    total_revenue = float(demand_series.sum() + graphene_series.sum())
    total_capex = float(capital_series.sum())
    total_opex = float(opex_series.sum())
    total_profit = total_revenue - (total_capex + total_opex + transport_cost)

    capex_weights = get_capex_weight_series(df_prod["Type"], water_weight)
    weighted_capex_series = (
        df_prod["Capital Cost Per H2"] * df_prod["H2 Production Capacity (kg/day)"] * capex_weights
    )
    weighted_capex = float(weighted_capex_series.sum())
    transport_scale = get_transport_scale(transport_weight)
    weighted_transport = transport_scale * transport_cost
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