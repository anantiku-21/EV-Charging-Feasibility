# Runs every analysis the report needs, using the one model in analysis.py.
# Outputs: outputs/tables/*.csv and outputs/charts/*.png

import os
import pandas as pd
import matplotlib.pyplot as plt
from analysis import run_model, break_even_kwh_per_day, configs, CITIES, SCENARIOS

os.makedirs("outputs/tables", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)
LAKH = 100000
BENCHMARK_UTILISATION = 0.0836    # national average public DC charger, ExperiencesWithEVs Jul 2025

def pct(x):
    return None if x is None else round(x * 100, 1)


# ============ Phase 7: which configuration? ============
config_rows = []
for city in CITIES:
    for config in configs.index:
        r = run_model(city, "base", config)
        config_rows.append({"city": city, "config": config, "description": configs.loc[config, "description"],
                            "capex_lakh": r["capex"]["total"] / LAKH,
                            "yr1_utilisation_pct": r["table"].loc[0, "utilisation"] * 100,
                            "npv_lakh": r["npv"] / LAKH, "irr_pct": pct(r["irr"])})
config_table = pd.DataFrame(config_rows)
config_table.round(2).to_csv("outputs/tables/config_comparison.csv", index=False)
print("=== Configuration comparison (base case) ===")
print(config_table.round(1).to_string(index=False))

# Pick the configuration with the highest base-case NPV in each city
best_config = config_table.loc[config_table.groupby("city")["npv_lakh"].idxmax()].set_index("city")["config"].to_dict()
print("\nBest configuration by NPV:", best_config)


# ============ Phases 8-13: base-case detail for the chosen configuration ============
for city in CITIES:
    r = run_model(city, "base", best_config[city])
    t = r["table"].copy()
    money_cols = [c for c in t.columns if c not in ["year", "kwh_per_day", "sessions_per_day", "utilisation"]]
    t[money_cols] = t[money_cols] / LAKH
    t["utilisation"] = t["utilisation"] * 100
    t.round(2).to_csv(f"outputs/tables/cashflow_{city.lower()}_base.csv", index=False)

    capex = pd.Series(r["capex"]) / LAKH
    capex.round(2).to_csv(f"outputs/tables/capex_{city.lower()}.csv", header=["rs_lakh"])

    print(f"\n=== {city} | config {best_config[city]} | base case (Rs lakh) ===")
    print("CAPEX:", capex.round(2).to_dict(), "| working capital:", round(r["working_capital"] / LAKH, 2))
    print(t[["year", "kwh_per_day", "sessions_per_day", "utilisation", "revenue", "electricity", "gross_profit",
             "opex_excl_electricity", "ebitda", "tax", "net_cash_flow", "cumulative_cash_flow"]].round(1).to_string(index=False))
    print(f"Discount rate {r['discount_rate']:.2%} | NPV Rs {r['npv']/LAKH:.1f} lakh | IRR {pct(r['irr'])}% | payback {r['payback']}")


# ============ Phase 11: unit economics (year 1 and year 5, base) ============
unit_rows = []
for city in CITIES:
    r = run_model(city, "base", best_config[city])
    for idx in [0, 4]:
        row = r["table"].loc[idx]
        kwh = row["kwh_per_day"] * 365
        unit_rows.append({
            "city": city, "year": int(row["year"]),
            "revenue_per_kwh": row["revenue"] / kwh,
            "electricity_per_kwh": row["electricity"] / kwh,
            "contribution_per_kwh": (row["revenue"] - row["electricity"] - row["host_rent"] - row["payment_fees"]) / kwh,
            "other_opex_per_kwh": (row["opex_excl_electricity"] - row["host_rent"] - row["payment_fees"]) / kwh,
            "ebitda_per_kwh": row["ebitda"] / kwh,
            "revenue_per_session": row["revenue"] / kwh * r["kwh_per_session"],
            "contribution_per_session": (row["revenue"] - row["electricity"] - row["host_rent"] - row["payment_fees"]) / kwh * r["kwh_per_session"],
        })
unit_table = pd.DataFrame(unit_rows)
unit_table.round(2).to_csv("outputs/tables/unit_economics.csv", index=False)
print("\n=== Unit economics (Rs) ===")
print(unit_table.round(2).to_string(index=False))


# ============ Phase 14 + 15: scenarios and break-even ============
scenario_rows = []
for city in CITIES:
    config = best_config[city]
    for scenario in SCENARIOS:
        r = run_model(city, scenario, config)
        t = r["table"]
        be_npv = break_even_kwh_per_day(city, scenario, config, "npv")
        be_ebitda = break_even_kwh_per_day(city, scenario, config, "ebitda")
        full = r["full_time_kwh_day"]
        scenario_rows.append({
            "city": city, "config": config, "scenario": scenario,
            "yr1_kwh_day": t.loc[0, "kwh_per_day"], "yr1_sessions_day": t.loc[0, "sessions_per_day"],
            "yr1_utilisation_pct": t.loc[0, "utilisation"] * 100, "yr5_utilisation_pct": t.loc[4, "utilisation"] * 100,
            "yr1_revenue_lakh": t.loc[0, "revenue"] / LAKH, "yr1_ebitda_lakh": t.loc[0, "ebitda"] / LAKH,
            "yr5_revenue_lakh": t.loc[4, "revenue"] / LAKH, "yr5_ebitda_lakh": t.loc[4, "ebitda"] / LAKH,
            "yr5_ebitda_margin_pct": t.loc[4, "ebitda"] / t.loc[4, "revenue"] * 100,
            "capex_lakh": r["capex"]["total"] / LAKH, "npv_lakh": r["npv"] / LAKH, "irr_pct": pct(r["irr"]),
            "payback_years": None if r["payback"] is None else round(r["payback"], 1),
            "breakeven_npv_kwh_day": be_npv,
            "breakeven_npv_sessions_day": None if be_npv is None else be_npv / r["kwh_per_session"],
            "breakeven_npv_utilisation_pct": None if be_npv is None else be_npv / full * 100,
            "breakeven_npv_revenue_lakh_yr1": None if be_npv is None else run_model(city, scenario, config, {"flat_demand_kwh_day": be_npv})["table"].loc[0, "revenue"] / LAKH,
            "breakeven_ebitda_utilisation_pct": None if be_ebitda is None else be_ebitda / full * 100,
            "breakeven_ebitda_sessions_day": None if be_ebitda is None else be_ebitda / r["kwh_per_session"],
        })
scenario_table = pd.DataFrame(scenario_rows)
scenario_table.round(2).to_csv("outputs/tables/scenarios.csv", index=False)
print("\n=== Scenarios ===")
print(scenario_table.round(1).T.to_string())


# ============ Phase 16: sensitivity (one input at a time, base case) ============
tests = [
    ("Demand (capture) -30% / +30%", {"demand_factor": 0.7}, {"demand_factor": 1.3}),
    ("Charging price -10% / +10%", {"price_factor": 0.9}, {"price_factor": 1.1}),
    ("Electricity cost +20% / -20%", {"electricity_factor": 1.2}, {"electricity_factor": 0.8}),
    ("CAPEX +20% / -20%", {"capex_factor": 1.2}, {"capex_factor": 0.8}),
    ("Host revenue share 20% / 10%", {"host_share": 0.20}, {"host_share": 0.10}),
    ("Staff 2 FTE / 0 FTE", {"staff_fte": 2.0}, {"staff_fte": 0.0}),
    ("Discount rate 16% / 12%", {"discount_rate": 0.16}, {"discount_rate": 0.12}),
    ("Grid work: new connection / host's spare capacity", {"upstream_factor": 1.0}, {"upstream_factor": 0.0}),
]
sens_rows = []
for city in CITIES:
    base_npv = run_model(city, "base", best_config[city])["npv"]
    for name, bad, good in tests:
        low = run_model(city, "base", best_config[city], bad)["npv"]
        high = run_model(city, "base", best_config[city], good)["npv"]
        sens_rows.append({"city": city, "input": name, "base_npv_lakh": base_npv / LAKH,
                          "npv_bad_lakh": low / LAKH, "npv_good_lakh": high / LAKH,
                          "swing_lakh": (high - low) / LAKH})
sens_table = pd.DataFrame(sens_rows).sort_values(["city", "swing_lakh"], ascending=[True, False])
sens_table.round(2).to_csv("outputs/tables/sensitivity_tornado.csv", index=False)
print("\n=== Sensitivity (NPV, Rs lakh) ===")
print(sens_table.round(1).to_string(index=False))

# ============ What would it take? Stack the controllable levers on the base case ============
# Levers management can actually negotiate: a host site with spare grid capacity,
# an unmanned (remote-monitored) station, and a lower host revenue share.
lever_steps = [
    ("Base case", {}),
    ("+ host site with spare grid capacity", {"upstream_factor": 0.0}),
    ("+ unmanned (remote-monitored)", {"upstream_factor": 0.0, "staff_fte": 0.0}),
    ("+ host share cut to 10%", {"upstream_factor": 0.0, "staff_fte": 0.0, "host_share": 0.10}),
]
lever_rows = []
for city in CITIES:
    for name, ov in lever_steps:
        r = run_model(city, "base", best_config[city], ov)
        lever_rows.append({"city": city, "step": name, "capex_lakh": r["capex"]["total"] / LAKH,
                           "npv_lakh": r["npv"] / LAKH, "irr_pct": pct(r["irr"]),
                           "payback_years": None if r["payback"] is None else round(r["payback"], 1)})
    # Break-even utilisation once all levers are pulled
    full = run_model(city, "base", best_config[city])["full_time_kwh_day"]
    all_levers = lever_steps[-1][1]
    low, high = 0.0, run_model(city, "base", best_config[city])["capacity_kwh_day"]
    for _ in range(60):
        mid = (low + high) / 2
        if run_model(city, "base", best_config[city], {**all_levers, "flat_demand_kwh_day": mid})["npv"] < 0:
            low = mid
        else:
            high = mid
    lever_rows.append({"city": city, "step": "Break-even utilisation with all levers (%)",
                       "capex_lakh": None, "npv_lakh": high / full * 100, "irr_pct": None, "payback_years": None})
lever_table = pd.DataFrame(lever_rows)
lever_table.round(2).to_csv("outputs/tables/levers.csv", index=False)
print("\n=== What would it take? (base case + controllable levers) ===")
print(lever_table.round(1).to_string(index=False))

# Robustness: does the "all levers" station survive the other scenarios? (success test 5)
robust_rows = []
for city in CITIES:
    for scenario in SCENARIOS:
        r = run_model(city, scenario, best_config[city], lever_steps[-1][1])
        robust_rows.append({"city": city, "scenario": scenario, "npv_lakh": r["npv"] / LAKH, "irr_pct": pct(r["irr"]),
                            "payback_years": None if r["payback"] is None else round(r["payback"], 1)})
robust_table = pd.DataFrame(robust_rows)
robust_table.round(2).to_csv("outputs/tables/levers_by_scenario.csv", index=False)
print("\n=== All-levers station across scenarios ===")
print(robust_table.round(1).to_string(index=False))

# Hyderabad price shock: base case, but forced to match the Rs 13 government price
r13 = run_model("Hyderabad", "base", best_config["Hyderabad"], {"price_factor": 13.0 / 16.0})
print(f"\nHyderabad base case at Rs 13 price: NPV Rs {r13['npv']/LAKH:.1f} lakh")
pd.DataFrame([{"case": "Hyderabad base at Rs 13", "npv_lakh": r13["npv"] / LAKH}]).round(2).to_csv(
    "outputs/tables/hyderabad_rs13_case.csv", index=False)

# Discount-rate table and NPV-vs-demand curve (used for charts and the deck)
rate_rows, curve_rows = [], []
for city in CITIES:
    for rate in [0.12, 0.14, 0.1410, 0.16]:
        rate_rows.append({"city": city, "discount_rate_pct": rate * 100,
                          "npv_lakh": run_model(city, "base", best_config[city], {"discount_rate": rate})["npv"] / LAKH})
    full = run_model(city, "base", best_config[city])["full_time_kwh_day"]
    for util in [x / 100 for x in range(4, 41, 2)]:
        r = run_model(city, "base", best_config[city], {"flat_demand_kwh_day": util * full})
        curve_rows.append({"city": city, "utilisation_pct": util * 100, "npv_lakh": r["npv"] / LAKH})
pd.DataFrame(rate_rows).round(2).to_csv("outputs/tables/discount_rate_sensitivity.csv", index=False)
curve = pd.DataFrame(curve_rows)
curve.round(2).to_csv("outputs/tables/npv_vs_utilisation.csv", index=False)

# Two-way table: NPV by utilisation and price (base case, Delhi & Hyderabad)
grid_rows = []
for city in CITIES:
    full = run_model(city, "base", best_config[city])["full_time_kwh_day"]
    for util in [0.08, 0.12, 0.16, 0.20, 0.25, 0.30]:
        for price_factor in [0.8, 0.9, 1.0, 1.1]:
            r = run_model(city, "base", best_config[city], {"flat_demand_kwh_day": util * full, "price_factor": price_factor})
            grid_rows.append({"city": city, "utilisation_pct": util * 100, "price_factor": price_factor, "npv_lakh": r["npv"] / LAKH})
pd.DataFrame(grid_rows).round(2).to_csv("outputs/tables/npv_grid_utilisation_price.csv", index=False)


# ============ Charts ============
blue, orange, ink, muted, grid_c, bg = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#d0cfca", "#fcfcfb"

def style(ax):
    ax.set_facecolor(bg)
    ax.tick_params(colors=muted)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(grid_c)
    ax.spines["bottom"].set_color(grid_c)

# Chart 1: how busy must the station be? NPV vs utilisation, with the national benchmark
fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor(bg)
style(ax)
for city, colour in [("Delhi", blue), ("Hyderabad", orange)]:
    c = curve[curve["city"] == city]
    ax.plot(c["utilisation_pct"], c["npv_lakh"], color=colour, linewidth=2, label=city)
ax.axhline(0, color=muted, linewidth=1)
ax.axvline(BENCHMARK_UTILISATION * 100, color=muted, linestyle="--", linewidth=1)
ax.text(BENCHMARK_UTILISATION * 100 + 0.5, ax.get_ylim()[1] * 0.85, "India average\npublic DC charger (8.4%)", fontsize=8, color=muted)
for city, colour in [("Delhi", blue), ("Hyderabad", orange)]:
    be = scenario_table[(scenario_table["city"] == city) & (scenario_table["scenario"] == "base")]["breakeven_npv_utilisation_pct"].iloc[0]
    if be is not None:
        ax.scatter([be], [0], color=colour, s=60, zorder=3, edgecolor=bg, linewidth=2)
        ax.text(be, -6 if city == "Delhi" else 6, f"{city} break-even {be:.0f}%", fontsize=8, color=ink, ha="left")
ax.set_xlabel("Average utilisation over 10 years (% of hours a charger is in use)", color=muted)
ax.set_ylabel("NPV, Rs lakh", color=muted)
ax.set_title(f"How busy must the station be? NPV vs utilisation (config {best_config['Delhi']}, base case)", loc="left", color=ink, fontsize=11)
ax.legend(frameon=False, labelcolor=muted)
plt.tight_layout()
plt.savefig("outputs/charts/npv_vs_utilisation.png", dpi=150)
plt.close()

# Chart 2: tornado for each city
fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
fig.patch.set_facecolor(bg)
for ax, city in zip(axes, CITIES):
    style(ax)
    s = sens_table[sens_table["city"] == city].sort_values("swing_lakh")
    base = s["base_npv_lakh"].iloc[0]
    y = range(len(s))
    ax.barh(list(y), s["npv_bad_lakh"] - base, left=base, color=orange, height=0.55, edgecolor=bg, linewidth=2, label="Worse case")
    ax.barh(list(y), s["npv_good_lakh"] - base, left=base, color=blue, height=0.55, edgecolor=bg, linewidth=2, label="Better case")
    ax.axvline(base, color=ink, linewidth=1)
    ax.axvline(0, color=muted, linestyle="--", linewidth=1)
    ax.set_yticks(list(y))
    ax.set_yticklabels(s["input"], fontsize=8, color=muted)
    ax.set_title(f"{city} (base NPV Rs {base:.0f} lakh)", loc="left", color=ink, fontsize=10)
    ax.set_xlabel("NPV, Rs lakh (dashed = zero)", color=muted)
axes[0].legend(frameon=False, labelcolor=muted, fontsize=8, loc="lower right")
fig.suptitle("Which assumption moves NPV most? (one input changed at a time)", x=0.02, ha="left", color=ink, fontsize=12)
plt.tight_layout()
plt.savefig("outputs/charts/tornado.png", dpi=150)
plt.close()

# Chart 3: scenario NPVs
fig, ax = plt.subplots(figsize=(8, 3.8))
fig.patch.set_facecolor(bg)
style(ax)
x_labels = [s.capitalize() for s in SCENARIOS]
width = 0.35
for i, (city, colour) in enumerate([("Delhi", blue), ("Hyderabad", orange)]):
    vals = scenario_table[scenario_table["city"] == city].set_index("scenario").loc[SCENARIOS, "npv_lakh"]
    xs = [j + (i - 0.5) * width for j in range(3)]
    ax.bar(xs, vals, width=width, color=colour, edgecolor=bg, linewidth=2, label=city)
    for xx, v in zip(xs, vals):
        ax.text(xx, v + (2 if v >= 0 else -5), f"{v:.0f}", ha="center", fontsize=8, color=ink)
ax.axhline(0, color=muted, linewidth=1)
ax.set_xticks(range(3))
ax.set_xticklabels(x_labels, color=muted)
ax.set_ylabel("NPV, Rs lakh", color=muted)
ax.set_title("NPV by scenario (best configuration per city)", loc="left", color=ink, fontsize=11)
ax.legend(frameon=False, labelcolor=muted)
plt.tight_layout()
plt.savefig("outputs/charts/scenario_npv.png", dpi=150)
plt.close()

# Chart 4: configuration comparison
fig, ax = plt.subplots(figsize=(8, 3.6))
fig.patch.set_facecolor(bg)
style(ax)
for i, (city, colour) in enumerate([("Delhi", blue), ("Hyderabad", orange)]):
    vals = config_table[config_table["city"] == city].set_index("config")["npv_lakh"]
    xs = [j + (i - 0.5) * width for j in range(len(vals))]
    ax.bar(xs, vals, width=width, color=colour, edgecolor=bg, linewidth=2, label=city)
    for xx, v in zip(xs, vals):
        ax.text(xx, v - 5, f"{v:.0f}", ha="center", fontsize=8, color=ink)
ax.axhline(0, color=muted, linewidth=1)
ax.set_xticks(range(3))
ax.set_xticklabels(["A: 1x60 kW DC", "B: 2x60 kW DC", "C: 2x120 kW DC"], color=muted)
ax.set_ylabel("NPV, Rs lakh (base case)", color=muted)
ax.set_title("More chargers = more idle capital at today's demand", loc="left", color=ink, fontsize=11)
ax.legend(frameon=False, labelcolor=muted)
plt.tight_layout()
plt.savefig("outputs/charts/config_npv.png", dpi=150)
plt.close()

print("\nCharts saved in outputs/charts/")
