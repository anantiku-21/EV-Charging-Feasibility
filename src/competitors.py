# Phase 5 - Competitor analysis
# Question: what do nearby competitors charge for DC fast charging,
# and how much room is left between that price and our electricity cost?
# Data: data/raw/competitors.csv (every row labelled OBSERVED or REPORTED, with URL and date)

import pandas as pd
import matplotlib.pyplot as plt

comp = pd.read_csv("data/raw/competitors.csv")

# Some prices are ranges like "21.99-22.99" or "13.00 + GST".
# For comparison we take the mid-point of a range and drop the text.
def price_midpoint(text):
    if pd.isna(text):
        return None
    text = str(text).replace("+ GST", "").strip()
    parts = [float(p) for p in text.split("-")]
    return sum(parts) / len(parts)

comp["dc_price_mid"] = comp["dc_price_rs_kwh"].apply(price_midpoint)

# Keep only stations we actually saw a price for (OBSERVED), plus the govt network
priced = comp.dropna(subset=["dc_price_mid"])
print(priced[["city", "station", "area", "dc_power_kw", "dc_price_mid", "label"]].to_string(index=False))


# Private operators vs government-linked (Rs 13) stations are very different, so summarise separately
govt_linked = priced["dc_price_mid"] <= 13
private_observed = priced[~govt_linked & priced["label"].str.startswith("OBSERVED")]

summary = private_observed.groupby("city")["dc_price_mid"].agg(["count", "min", "median", "max"])
print("\nPrivate DC prices actually observed (Rs/kWh):")
print(summary.round(2).to_string())


# How much is left per unit after paying for electricity?
# Electricity cost from Phase 3: Hyderabad Rs 6.00 (LT-IX), Delhi Rs 4.50 base, ~Rs 5.50 with surcharges (to verify).
# GST: we do NOT yet know if listed prices include 18% GST, so show both cases.
electricity_cost = {"Delhi": 5.50, "Hyderabad": 6.00}

rows = []
for city in ["Delhi", "Hyderabad"]:
    median_price = summary.loc[city, "median"]
    for price_name, price in [("private median", median_price), ("govt Rs 13", 13.0)]:
        if city == "Delhi" and price_name == "govt Rs 13":
            continue   # no Rs 13 government network found in Delhi
        rows.append({
            "city": city,
            "price_point": price_name,
            "price": price,
            "margin_if_price_excl_gst": price - electricity_cost[city],
            "margin_if_price_incl_gst": price / 1.18 - electricity_cost[city],
        })

margins = pd.DataFrame(rows)
print("\nRs left per kWh after electricity (before rent, staff, maintenance):")
print(margins.round(2).to_string(index=False))

priced.to_csv("outputs/tables/competitor_matrix.csv", index=False)
margins.round(2).to_csv("outputs/tables/competitor_margins.csv", index=False)


# CHART - What do competitors charge? One dot per station, per city.
blue, ink, muted, grid = "#2a78d6", "#0b0b0b", "#52514e", "#d0cfca"

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharex=True)
fig.patch.set_facecolor("#fcfcfb")

for ax, city in zip(axes, ["Delhi", "Hyderabad"]):
    ax.set_facecolor("#fcfcfb")
    data = priced[priced["city"] == city].sort_values("dc_price_mid")
    y = range(len(data))
    # Filled dot = price we saw on a station listing; hollow dot = reported in press/operator site
    is_observed = data["label"].str.startswith("OBSERVED").tolist()
    for yi, price, seen in zip(y, data["dc_price_mid"], is_observed):
        if seen:
            ax.scatter(price, yi, s=70, color=blue, edgecolor="#fcfcfb", linewidth=2, zorder=3)
        else:
            ax.scatter(price, yi, s=70, facecolor="#fcfcfb", edgecolor=blue, linewidth=2, zorder=3)
    ax.set_yticks(list(y))
    ax.set_yticklabels(data["station"], fontsize=8, color=muted)
    for yi, price in zip(y, data["dc_price_mid"]):
        ax.text(price + 0.4, yi, f"Rs {price:.2f}", va="center", fontsize=8, color=ink)

    # Reference line: our own electricity cost per kWh
    ax.axvline(electricity_cost[city], color=muted, linestyle="--", linewidth=1)
    ax.text(electricity_cost[city] + 0.3, -0.45, "our electricity cost", fontsize=8, color=muted, va="center")
    ax.set_ylim(-0.8, len(data) - 0.5)

    ax.set_title(city, loc="left", color=ink, fontsize=11)
    ax.set_xlim(0, 30)
    ax.set_xlabel("DC price, Rs per kWh", color=muted)
    ax.tick_params(colors=muted)
    ax.grid(axis="x", color=grid, linewidth=0.5)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(grid)

fig.suptitle("Competitor DC fast-charging prices, Sep 2026  (filled = seen on listing, hollow = reported)",
             x=0.02, ha="left", color=ink, fontsize=11)
plt.tight_layout()
plt.savefig("outputs/charts/phase5_competitor_prices.png", dpi=150)
print("\nChart saved: outputs/charts/phase5_competitor_prices.png")
