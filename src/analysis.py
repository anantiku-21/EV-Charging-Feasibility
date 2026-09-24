# EV Charging Station Feasibility - financial model (Phases 6 to 16)
#
# One station, rented site, 10 years, two cities (Delhi, Hyderabad),
# three charger configurations (A lean, B balanced, C fleet hub),
# three scenarios (conservative, base, aggressive).
#
# All business assumptions live in data/processed/*.csv - nothing important is hard-coded here.
# The chain is:  demand -> configuration -> CAPEX + OPEX -> revenue -> EBITDA -> cash flow
#                -> NPV / IRR / payback -> break-even -> scenarios / sensitivity

import pandas as pd

assumptions = pd.read_csv("data/processed/assumptions.csv")
configs = pd.read_csv("data/processed/configurations.csv").set_index("config")
unit_costs = pd.read_csv("data/processed/unit_costs.csv").set_index("item")["cost_rs"]

CITIES = ["Delhi", "Hyderabad"]
SCENARIOS = ["conservative", "base", "aggressive"]


def get(parameter, city, scenario):
    """Look up one assumption. City-specific rows win over 'All' rows."""
    rows = assumptions[assumptions["parameter"] == parameter]
    city_row = rows[rows["city"] == city]
    if len(city_row) == 0:
        city_row = rows[rows["city"] == "All"]
    return float(city_row[scenario].iloc[0])


def npv(rate, cash_flows):
    # cash_flows[0] is today (Year 0), then Year 1, Year 2, ...
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))


def irr(cash_flows):
    # Find the rate where NPV = 0 by repeatedly halving the search range (bisection).
    # If the project never even gets its money back (undiscounted), a negative IRR is not meaningful: report None.
    if sum(cash_flows) < 0:
        return None
    low, high = -0.99, 1.0
    if npv(low, cash_flows) * npv(high, cash_flows) > 0:
        return None          # no IRR in a sensible range (e.g. cash never turns positive)
    for _ in range(200):
        mid = (low + high) / 2
        if npv(low, cash_flows) * npv(mid, cash_flows) <= 0:
            high = mid
        else:
            low = mid
    return mid


def payback_years(cash_flows):
    # Years until cumulative cash turns positive (linear within the year). None = never within horizon.
    cumulative = cash_flows[0]
    for year in range(1, len(cash_flows)):
        if cumulative + cash_flows[year] >= 0:
            return year - 1 + (-cumulative / cash_flows[year])
        cumulative += cash_flows[year]
    return None


def run_model(city, scenario, config, overrides=None):
    """Build the 10-year cash flow for one city / scenario / configuration.
    'overrides' lets sensitivity and break-even tests change one input at a time."""
    o = overrides or {}
    cfg = configs.loc[config]
    years = int(get("horizon_years", city, scenario))

    # ---------- Station hardware ----------
    n_dc60, n_dc120, n_ac = int(cfg["dc_60kw_units"]), int(cfg["dc_120kw_units"]), int(cfg["ac_7kw_units"])
    n_chargers = n_dc60 + n_dc120 + n_ac
    total_kw = n_dc60 * 60 + n_dc120 * 120 + n_ac * 7.4

    # ---------- CAPEX (Phase 8) ----------
    capex_mult = get("capex_multiplier", city, scenario) * o.get("capex_factor", 1.0)
    charger_capex = (n_dc60 * unit_costs["dc_60kw_charger"] + n_dc120 * unit_costs["dc_120kw_charger"]
                     + n_ac * unit_costs["ac_7kw_charger"]) * capex_mult
    # upstream_factor = 0 tests a host site that already has spare grid capacity (no new transformer/feeder)
    upstream_capex = cfg["upstream_cost_lakh"] * 100000 * capex_mult * o.get("upstream_factor", 1.0)
    civil_capex = ((n_dc60 + n_dc120) * unit_costs["civil_per_dc_bay"] + n_ac * unit_costs["civil_per_ac_bay"]) * capex_mult
    other_capex = unit_costs["signage"] + unit_costs["software_setup"] + unit_costs["permits_misc"]
    subtotal = charger_capex + upstream_capex + civil_capex + other_capex
    contingency = subtotal * get("contingency", city, scenario)
    total_capex = subtotal + contingency

    # ---------- Capacity (what the station can physically sell) ----------
    delivery = get("power_delivery_factor", city, scenario)
    capacity_kwh_day = (total_kw * delivery * 24 * get("max_practical_utilisation", city, scenario)
                        * get("uptime", city, scenario))
    full_time_kwh_day = total_kw * delivery * 24          # used to express utilisation as % of hours

    # ---------- Demand (Phase 6) ----------
    fair_share = get("public_demand_kwh_per_day", city, scenario) / get("fast_stations", city, scenario)
    steady_y1 = fair_share * get("capture_multiple", city, scenario) * o.get("demand_factor", 1.0)
    growth = get("demand_growth_per_station", city, scenario)
    ramp = get("year1_ramp", city, scenario)

    # ---------- Prices and costs ----------
    price = get("price_net_of_gst", city, scenario) * o.get("price_factor", 1.0)
    price_esc = get("price_escalation", city, scenario)
    tariff = get("electricity_rs_per_kwh", city, scenario) * o.get("electricity_factor", 1.0)
    tariff_esc = get("tariff_escalation", city, scenario)
    losses = get("grid_losses", city, scenario)
    fixed_elec_month = get("electricity_fixed_rs_per_month", city, scenario)
    if city == "Hyderabad" and total_kw > 150:
        # Above 150 kW the station must take an HT-IX connection: demand charge + higher customer charge
        kva = total_kw / 0.95
        fixed_elec_month = kva * unit_costs["hyd_ht_demand_charge"] + unit_costs["hyd_ht_customer_charge"]

    host_share = o.get("host_share", get("host_revenue_share", city, scenario))
    staff_fte = o.get("staff_fte", get("staff_fte", city, scenario))
    inflation = get("fixed_cost_inflation", city, scenario)
    tax_rate = get("tax_rate", city, scenario)
    discount_rate = o.get("discount_rate", get("risk_free_rate", city, scenario)
                          + get("beta", city, scenario) * get("equity_risk_premium", city, scenario))
    depreciation = total_capex / get("depreciation_years", city, scenario)

    rows = []
    tax_losses_brought_forward = 0.0
    for year in range(1, years + 1):
        # Demand this year: flat override (break-even test) or ramp + growth
        if "flat_demand_kwh_day" in o:
            demand_day = o["flat_demand_kwh_day"]
        else:
            demand_day = steady_y1 * (1 + growth) ** (year - 1)
            if year == 1:
                demand_day *= ramp
        sold_day = min(demand_day, capacity_kwh_day)   # can't sell more than the chargers can deliver
        kwh_year = sold_day * 365

        infl = (1 + inflation) ** (year - 1)
        revenue = kwh_year * price * (1 + price_esc) ** (year - 1)
        electricity = (kwh_year / (1 - losses) * tariff + fixed_elec_month * 12) * (1 + tariff_esc) ** (year - 1)
        gross_profit = revenue - electricity

        host_rent = revenue * host_share
        staff = staff_fte * get("staff_cost_rs_per_month", city, scenario) * 12 * infl
        maintenance = charger_capex * get("maintenance_pct_of_charger_capex", city, scenario) * infl
        software = n_chargers * get("cms_rs_per_charger_month", city, scenario) * 12 * infl
        payment_fees = revenue * get("payment_fee_share", city, scenario)
        insurance = total_capex * get("insurance_pct_of_capex", city, scenario) * infl
        misc = get("misc_rs_per_month", city, scenario) * 12 * infl
        other_opex = host_rent + staff + maintenance + software + payment_fees + insurance + misc
        ebitda = gross_profit - other_opex

        # Tax on profit after depreciation; early losses are carried forward and used later
        ebit = ebitda - depreciation
        if ebit < 0:
            tax = 0.0
            tax_losses_brought_forward += -ebit
        else:
            losses_used = min(tax_losses_brought_forward, ebit)
            tax_losses_brought_forward -= losses_used
            tax = (ebit - losses_used) * tax_rate
        free_cash_flow = ebitda - tax

        rows.append({
            "year": year, "kwh_per_day": sold_day, "sessions_per_day": sold_day / get("kwh_per_session", city, scenario),
            "utilisation": sold_day / full_time_kwh_day, "revenue": revenue, "electricity": electricity,
            "gross_profit": gross_profit, "host_rent": host_rent, "staff": staff, "maintenance": maintenance,
            "software": software, "payment_fees": payment_fees, "insurance": insurance, "misc": misc,
            "opex_excl_electricity": other_opex, "ebitda": ebitda, "depreciation": depreciation,
            "tax": tax, "free_cash_flow": free_cash_flow,
        })

    table = pd.DataFrame(rows)

    # Working capital: one month of year-1 running costs, paid upfront and recovered at the end
    working_capital = (table.loc[0, "electricity"] + table.loc[0, "opex_excl_electricity"]) / 12
    cash_flows = [-(total_capex + working_capital)] + table["free_cash_flow"].tolist()
    cash_flows[-1] += working_capital
    table["net_cash_flow"] = cash_flows[1:]
    table["cumulative_cash_flow"] = pd.Series(cash_flows).cumsum().iloc[1:].values

    return {
        "table": table,
        "capex": {"chargers": charger_capex, "upstream_grid": upstream_capex, "civil": civil_capex,
                  "other": other_capex, "contingency": contingency, "total": total_capex},
        "working_capital": working_capital,
        "cash_flows": cash_flows,
        "discount_rate": discount_rate,
        "npv": npv(discount_rate, cash_flows),
        "irr": irr(cash_flows),
        "payback": payback_years(cash_flows),
        "total_kw": total_kw,
        "capacity_kwh_day": capacity_kwh_day,
        "full_time_kwh_day": full_time_kwh_day,
        "kwh_per_session": get("kwh_per_session", city, scenario),
    }


def break_even_kwh_per_day(city, scenario, config, target="npv"):
    """Flat daily energy (same every year) at which NPV = 0 (or year-1 EBITDA = 0).
    Found by bisection on the model itself, so it uses the project's real cost structure."""
    low, high = 0.0, run_model(city, scenario, config)["capacity_kwh_day"]

    def value(kwh):
        result = run_model(city, scenario, config, {"flat_demand_kwh_day": kwh})
        return result["npv"] if target == "npv" else result["table"].loc[0, "ebitda"]

    if value(high) < 0:
        return None          # not viable even when the station is full
    for _ in range(60):
        mid = (low + high) / 2
        if value(mid) < 0:
            low = mid
        else:
            high = mid
    return high


if __name__ == "__main__":
    import os
    os.makedirs("outputs/tables", exist_ok=True)

    lakh = 100000
    # ---- Phase 7: compare configurations (base case) ----
    config_rows = []
    for city in CITIES:
        for config in configs.index:
            r = run_model(city, "base", config)
            config_rows.append({"city": city, "config": config, "capex_lakh": r["capex"]["total"] / lakh,
                                "yr1_utilisation_pct": r["table"].loc[0, "utilisation"] * 100,
                                "yr10_utilisation_pct": r["table"].loc[9, "utilisation"] * 100,
                                "npv_lakh": r["npv"] / lakh, "irr_pct": None if r["irr"] is None else r["irr"] * 100})
    config_table = pd.DataFrame(config_rows)
    print("Configuration comparison (base case):")
    print(config_table.round(1).to_string(index=False))
    config_table.round(2).to_csv("outputs/tables/config_comparison.csv", index=False)
