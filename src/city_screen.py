# Phase 2 - City screen
# Question: which candidate city has the best balance of EV car demand vs existing fast chargers?
# All inputs come from data/raw/city_screen_inputs.csv (sources in the source register).

import pandas as pd

cities = pd.read_csv("data/raw/city_screen_inputs.csv")

# Telangana sales cover only 11 months (Apr 2025 - Feb 2026).
# Scale to 12 months so all cities are compared on the same annual basis.
# This is a simple pro-rata ASSUMPTION (ignores the March sales peak), so it slightly understates Telangana.
cities["e4w_sales_annual"] = cities["e4w_sales_fy26"] / cities["e4w_months_covered"] * 12

# Main screening metric: new electric cars per year for every public fast-charging station.
# Higher = more new demand per competing fast charger = less crowded market.
# Caveat: compares one year of sales (flow) with 5 years of installed stations (stock) - indicative only.
cities["new_e4w_per_fast_station"] = cities["e4w_sales_annual"] / cities["pcs_fast"]

# Share of stations that are fast chargers - fast DC is the product a car-focused station would sell.
cities["fast_share_pct"] = cities["pcs_fast"] / cities["pcs_total"] * 100

result = cities[["city", "e4w_sales_annual", "e4w_penetration_pct", "pcs_fast",
                 "new_e4w_per_fast_station", "fast_share_pct", "ev_energy_charge_rs_kwh"]]
result = result.sort_values("new_e4w_per_fast_station", ascending=False)

print(result.round(1).to_string(index=False))

# Ranchi: FY26 sales are not published, so we check it against the cumulative stock instead.
# Even the ENTIRE e-4W stock to Aug 2024 is compared here - a generous test.
ranchi_e4w_stock = 1475
ranchi_fast = cities.loc[cities["city"] == "Ranchi", "pcs_fast"].iloc[0]
print(f"\nRanchi check: cumulative e-4W stock per fast station = {ranchi_e4w_stock / ranchi_fast:.1f}")
