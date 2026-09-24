# Phase 4 - Market analysis and market sizing (TAM / SAM)
# Question: how much charging energy do electric cars in each city need,
# and how much of it is realistically bought at PUBLIC chargers?
# Every input is in data/raw/market_inputs.csv with its label and source.

import pandas as pd
import matplotlib.pyplot as plt

inputs = pd.read_csv("data/raw/market_inputs.csv").set_index("input")
delhi = inputs["delhi"]
hyd = inputs["hyderabad"]


# ---------------------------------------------------------------
# STEP 1 - How many electric cars are on the road (Aug 2026)?
# ---------------------------------------------------------------

# Hyderabad: start from the RTA count (Aug 2025), then add cars sold since.
# Telangana sales Jan-Aug 2025 are backed out from the 100% growth figure:
# Jan-Aug 2026 = 2 x Jan-Aug 2025.
tg_jan_aug_2025 = hyd["ecar_sales_jan_aug_2026"] / (1 + hyd["ecar_growth_yoy_jan_aug_2026_pct"] / 100)
tg_sep_dec_2025 = hyd["telangana_ecar_sales_cy2025"] - tg_jan_aug_2025
tg_sold_since_aug_2025 = tg_sep_dec_2025 + hyd["ecar_sales_jan_aug_2026"]

# Only part of Telangana's new cars are in Hyderabad (68% assumption)
hyd_share = hyd["hyderabad_share_of_telangana_evs_pct"] / 100
hyd_stock = hyd["hyderabad_ecar_stock_aug_2025"] + tg_sold_since_aug_2025 * hyd_share

# Delhi: no published cumulative count, so we build it from sales.
# (a) cars sold before FY26: Delhi's FY26 share of national sales, applied to national FY24 + FY25
#     (cars sold before FY24 are ignored - a deliberately cautious choice)
# (b) cars sold in FY26
# (c) cars sold Apr-Aug 2026: Jan-Aug 2026 sales pro-rated to 5 of 8 months
delhi_national_share = delhi["ecar_sales_fy26"] / delhi["national_ecar_sales_fy26"]
delhi_before_fy26 = delhi_national_share * (delhi["national_ecar_sales_fy24"] + delhi["national_ecar_sales_fy25"])
delhi_apr_aug_2026 = delhi["ecar_sales_jan_aug_2026"] * 5 / 8
delhi_stock = delhi_before_fy26 + delhi["ecar_sales_fy26"] + delhi_apr_aug_2026

print("STEP 1 - Estimated electric cars on the road, Aug 2026")
print(f"  Delhi:     {delhi_stock:,.0f}  (Delhi share of national sales = {delhi_national_share:.1%})")
print(f"  Hyderabad: {hyd_stock:,.0f}  (Telangana cars sold since Aug 2025 = {tg_sold_since_aug_2025:,.0f})")


# ---------------------------------------------------------------
# STEP 2 - Split cars into cabs and private cars, then work out energy
# ---------------------------------------------------------------
# Energy per year (kWh) = cars x km per year x kWh per km

results = []
for city, row, stock in [("Delhi", delhi, delhi_stock), ("Hyderabad", hyd, hyd_stock)]:
    cab_cars = stock * row["cab_share_of_ecar_stock_pct"] / 100
    private_cars = stock - cab_cars

    cab_km_per_year = row["cab_km_per_day"] * row["cab_operating_days"]

    private_energy_kwh = private_cars * row["private_km_per_year"] * row["kwh_per_km"]
    cab_energy_kwh = cab_cars * cab_km_per_year * row["kwh_per_km"]

    # TAM = ALL charging energy these cars need, wherever they charge
    tam_mwh = (private_energy_kwh + cab_energy_kwh) / 1000

    # SAM = the part bought at PUBLIC chargers (most charging happens at home or depots)
    sam_private_mwh = private_energy_kwh * row["private_public_share_pct"] / 100 / 1000
    sam_cab_mwh = cab_energy_kwh * row["cab_public_share_pct"] / 100 / 1000

    results.append({
        "city": city,
        "ecar_stock": stock,
        "cab_cars": cab_cars,
        "private_cars": private_cars,
        "tam_mwh_per_year": tam_mwh,
        "sam_private_mwh": sam_private_mwh,
        "sam_cab_mwh": sam_cab_mwh,
        "sam_mwh_per_year": sam_private_mwh + sam_cab_mwh,
    })

market = pd.DataFrame(results).set_index("city")
market["sam_share_of_tam_pct"] = market["sam_mwh_per_year"] / market["tam_mwh_per_year"] * 100
market["cab_share_of_sam_pct"] = market["sam_cab_mwh"] / market["sam_mwh_per_year"] * 100

print("\nSTEP 2 - Market size (energy per year)")
print(market.round(0).to_string())


# ---------------------------------------------------------------
# STEP 3 - Sanity check against real charger usage
# ---------------------------------------------------------------
# If ALL public demand went to the existing fast-charging stations,
# how much energy would each station sell per day?
# Benchmark: an average Indian public DC charger is in use 8.36% of the time.
# A 50 kW charger at 8.36% sells about 50 x 24 x 0.0836 = ~100 kWh a day.
benchmark_kwh_per_charger_day = 50 * 24 * 0.0836

delhi_stations = delhi["fast_charging_stations"]
hyd_stations = hyd["fast_charging_stations"] * hyd_share   # Telangana count, scaled to Hyderabad

market["fast_stations"] = [delhi_stations, hyd_stations]
market["sam_kwh_per_station_per_day"] = market["sam_mwh_per_year"] * 1000 / 365 / market["fast_stations"]

print("\nSTEP 3 - Sanity check")
print(f"  Benchmark: one 50 kW charger at 8.36% use = {benchmark_kwh_per_charger_day:.0f} kWh/day")
print(market[["fast_stations", "sam_kwh_per_station_per_day"]].round(0).to_string())

market.round(1).to_csv("outputs/tables/market_sizing.csv")


# ---------------------------------------------------------------
# CHART - Who buys public charging? (answers: are cabs worth targeting?)
# ---------------------------------------------------------------
blue, orange = "#2a78d6", "#eb6834"      # validated categorical slots 1 and 2
ink, muted = "#0b0b0b", "#52514e"

fig, ax = plt.subplots(figsize=(8, 3.6))
fig.patch.set_facecolor("#fcfcfb")
ax.set_facecolor("#fcfcfb")

cities = market.index.tolist()
private = market["sam_private_mwh"] / 1000     # GWh
cab = market["sam_cab_mwh"] / 1000

ax.barh(cities, private, color=blue, height=0.5, label="Private cars", edgecolor="#fcfcfb", linewidth=2)
ax.barh(cities, cab, left=private, color=orange, height=0.5, label="Cabs", edgecolor="#fcfcfb", linewidth=2)

# Label only the totals (not every segment)
for i, city in enumerate(cities):
    total = private.iloc[i] + cab.iloc[i]
    ax.text(total + 0.05, i, f"{total:.1f} GWh / yr", va="center", color=ink, fontsize=10)

ax.set_title("Public charging demand per year (SAM), by customer type", loc="left", color=ink, fontsize=12)
ax.set_xlabel("GWh per year", color=muted)
ax.tick_params(colors=muted)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
ax.spines["left"].set_color("#d0cfca")
ax.spines["bottom"].set_color("#d0cfca")
ax.set_xlim(0, (private + cab).max() * 1.3)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, labelcolor=muted)
plt.tight_layout()
plt.savefig("outputs/charts/phase4_sam_by_segment.png", dpi=150)
print("\nChart saved: outputs/charts/phase4_sam_by_segment.png")
