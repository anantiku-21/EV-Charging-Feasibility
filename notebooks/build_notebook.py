# Builds notebooks/ev_charging_feasibility.ipynb (then run it with nbconvert --execute).
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
md = lambda t: cells.append(nbf.v4.new_markdown_cell(t))
code = lambda t: cells.append(nbf.v4.new_code_cell(t))

md("""# EV Charging Station Feasibility & Financial Analysis — Delhi vs Hyderabad

**Decision question:** Should a charge-point operator (CPO) invest in one public EV charging station (rented site, 10-year horizon) in Delhi, in Hyderabad, in both or in neither, and under what conditions?

*Portfolio feasibility study for a hypothetical CPO. Not a real client engagement. Every external number is in `docs/source_register.md`; every assumption is in `data/processed/assumptions.csv`.*

Each section answers: **What are we trying to answer? → What does the data show? → What business implication follows?**""")

code("""import os, sys
os.chdir("..") if os.path.basename(os.getcwd()) == "notebooks" else None
sys.path.insert(0, "src")
import pandas as pd
pd.set_option("display.float_format", "{:,.2f}".format)
from IPython.display import Image, display
from analysis import run_model, break_even_kwh_per_day, configs, CITIES, SCENARIOS
LAKH = 100000""")

md("""## 1. Business problem
**Question:** Is one public DC charging station a good investment, and where?

**Success tests (agreed before any results):** (1) NPV > 0 at the cost of capital, (2) IRR > cost of capital, (3) payback before chargers wear out, (4) break-even utilisation below what Indian public chargers actually achieve, (5) survives the conservative scenario.

**Scope:** rented site only (CPOs rarely buy land; land cost would swamp the result), customers = cab fleets first, private cars second; subsidies excluded (PM E-DRIVE charging funds go to government entities, not private CPOs).""")

md("""## 2. Data sources and research notes
All 40 sourced numbers, each labelled FACT / ESTIMATE / ASSUMPTION / DERIVED, are in the source register. The central assumptions table below drives both this notebook and the Excel model.""")
code("""assumptions = pd.read_csv("data/processed/assumptions.csv")
assumptions[["parameter", "city", "conservative", "base", "aggressive", "unit", "label"]]""")

md("""## 3. Market data and city selection
**Question:** Which cities have the most new electric cars per existing fast charger?

**Data:** PIB Lok Sabha reply (Dec 2025) for stations; EVreporter/Vahan for FY26 e-car sales.""")
code("""screen = pd.read_csv("data/raw/city_screen_inputs.csv")
screen["annual_sales"] = screen["e4w_sales_fy26"] / screen["e4w_months_covered"] * 12
screen["new_ecars_per_fast_station"] = screen["annual_sales"] / screen["pcs_fast"]
screen[["city", "annual_sales", "pcs_fast", "new_ecars_per_fast_station", "ev_energy_charge_rs_kwh"]].sort_values("new_ecars_per_fast_station", ascending=False)""")
md("""**Implication:** Delhi (42.6) and Hyderabad (39.4) lead and are close, so both were studied in full. Ranchi was dropped: Jharkhand had only ~1,475 e-cars in total (≈11 per fast station).""")

md("""## 4. Data cleaning
Main cleaning steps (all in code, nothing edited by hand):
- Telangana FY26 sales cover 11 months → pro-rated to 12.
- Telangana figures scaled to Hyderabad with the 68% share of state EVs registered in Hyderabad, Rangareddy and Medchal (ETV Bharat) — labelled ASSUMPTION when applied to cars.
- Competitor price ranges ("21.99-22.99") converted to mid-points; listed prices assumed to include 18% GST.""")

md("""## 5. Market analysis and sizing (TAM / SAM / SOM)
**Question:** How much charging energy do e-cars need, and how much is bought at public chargers?

- **TAM** = e-cars × km per year × kWh per km (all charging, anywhere)
- **SAM** = TAM × share charged in public (private cars 10%, cabs 30%)
- **SOM** = our station's share of SAM = SAM ÷ existing fast stations × capture multiple (Section 8)""")
code("""market = pd.read_csv("outputs/tables/market_sizing.csv")
market[["city", "ecar_stock", "tam_mwh_per_year", "sam_mwh_per_year", "cab_share_of_sam_pct", "sam_kwh_per_station_per_day"]]""")
code("""display(Image("outputs/charts/phase4_sam_by_segment.png"))""")
md("""**Validation:** if all public demand were spread over existing fast stations, each would sell ~104 kWh/day. An independent national study (8.36% utilisation of a 50 kW charger) gives ~100 kWh/day. The two methods agree.

**Implication:** both cities have ~15 GWh/yr of public demand; cabs are ~15% of cars but ~70% of public charging, so cab behaviour decides the business.""")

md("""## 6. Competitor analysis
**Question:** What do nearby rivals charge, and is there a gap?""")
code("""comp = pd.read_csv("outputs/tables/competitor_matrix.csv")
comp[["city", "station", "area", "dc_power_kw", "dc_price_mid", "status_seen", "label"]]""")
code("""display(Image("outputs/charts/phase5_competitor_prices.png"))""")
md("""**Implication:** Delhi private prices are ₹20–22; Hyderabad private prices are similar but a **₹13 government network (200 stations, fixed for 10 years)** is arriving. Many listed chargers were faulted, so reliability is the only evidence-backed edge. Limitation: 3 private price points per city, from one platform, on one date.""")

md("""## 7. Demand estimation
**Question:** How much will our one station sell?

Year-1 demand (kWh/day) = public demand ÷ existing fast stations × capture multiple × ramp-up. Then it grows each year by the per-station growth rate, capped by what the chargers can physically deliver.""")
code("""rows = []
for city in CITIES:
    for sc in SCENARIOS:
        t = run_model(city, sc, "A")["table"]
        rows.append({"city": city, "scenario": sc, "yr1_kwh_day": t.loc[0, "kwh_per_day"], "yr1_sessions": t.loc[0, "sessions_per_day"],
                     "yr5_kwh_day": t.loc[4, "kwh_per_day"], "yr10_kwh_day": t.loc[9, "kwh_per_day"]})
pd.DataFrame(rows)""")

md("""## 8. Station configuration
**Question:** One charger, two, or a fleet hub?""")
code("""pd.read_csv("outputs/tables/config_comparison.csv")""")
code("""display(Image("outputs/charts/config_npv.png"))""")
md("""**Implication:** at realistic demand the extra chargers sit idle, so the lean option **A (1 × 60 kW DC + 2 × 7.4 kW AC)** has the highest NPV in both cities. The rest of the analysis uses A.""")

md("""## 9. Financial assumptions
Discount rate = risk-free 7.02% (10-year G-sec) + beta 1.0 × India equity risk premium 7.08% (Damodaran) = **14.1%**. Tax 25.17% (Sec 115BAA). Straight-line depreciation over 10 years, no salvage. Working capital = one month of year-1 running costs, returned in year 10.""")

md("""## 10. CAPEX model""")
code("""r = run_model("Delhi", "base", "A")
pd.Series(r["capex"]).div(LAKH).rename("Rs lakh")""")
md("""The grid connection (₹14.8 lakh, MHI benchmark) is almost half the setup cost — a key lever later.""")

md("""## 11. OPEX, 12. Revenue, 13. P&L and 14. Cash flow (Delhi base case, Rs lakh)""")
code("""t = r["table"].copy()
cols = ["revenue", "electricity", "gross_profit", "host_rent", "staff", "maintenance", "software", "payment_fees",
        "insurance", "misc", "ebitda", "tax", "net_cash_flow", "cumulative_cash_flow"]
t[cols] = t[cols] / LAKH
t[["year", "kwh_per_day", "sessions_per_day", "utilisation"] + cols].round(2)""")
code("""pd.read_csv("outputs/tables/cashflow_hyderabad_base.csv")[["year", "kwh_per_day", "revenue", "electricity", "ebitda", "net_cash_flow", "cumulative_cash_flow"]]""")

md("""## 15. Unit economics
**Question:** Does each unit sold make money?""")
code("""pd.read_csv("outputs/tables/unit_economics.csv")""")
md("""**Implication:** each unit earns ₹7–10 after electricity, host share and payment fees, but fixed costs of ~₹4 lakh a year swamp this at 4–5 cars a day. Volume, not margin per unit, is the problem.""")

md("""## 16. Financial feasibility (NPV, IRR, payback)""")
code("""scen = pd.read_csv("outputs/tables/scenarios.csv")
scen[scen["scenario"] == "base"][["city", "capex_lakh", "npv_lakh", "irr_pct", "payback_years"]]""")
md("""IRR is reported as n/a when the project never gets its money back, because a negative IRR is not a meaningful return.""")

md("""## 17. Break-even analysis
**Question:** How busy must the station be?

Break-even is found by solving the full 10-year model for NPV = 0 (bisection), so it uses the project's real cost structure — not a generic formula.""")
code("""scen[["city", "scenario", "breakeven_npv_kwh_day", "breakeven_npv_sessions_day", "breakeven_npv_utilisation_pct",
      "breakeven_ebitda_utilisation_pct", "yr1_utilisation_pct", "yr5_utilisation_pct"]]""")
code("""display(Image("outputs/charts/npv_vs_utilisation.png"))""")
md("""**Implication:** base-case break-even needs **25.5% (Delhi) / 35.8% (Hyderabad)** utilisation every year — 3–4× the 8.4% national average.""")

md("""## 18. Scenario analysis""")
code("""scen[["city", "scenario", "yr1_revenue_lakh", "yr1_ebitda_lakh", "yr5_ebitda_margin_pct", "npv_lakh", "irr_pct", "payback_years", "breakeven_npv_utilisation_pct"]]""")
code("""display(Image("outputs/charts/scenario_npv.png"))""")

md("""## 19. Sensitivity analysis
**Question:** Which assumption matters most?""")
code("""pd.read_csv("outputs/tables/sensitivity_tornado.csv")""")
code("""display(Image("outputs/charts/tornado.png"))""")
md("""**Implication:** staffing (0–2 people), demand and the grid-connection cost move NPV most. The discount rate barely matters — the problem is volume, not financing.

**What would it take?** Stacking the three levers management can negotiate:""")
code("""pd.read_csv("outputs/tables/levers.csv")""")
code("""pd.read_csv("outputs/tables/levers_by_scenario.csv")""")

md("""## 20. Risk analysis

| Risk | Type | Likelihood (why) | Impact | Mitigation |
|---|---|---|---|---|
| Cab fleets charge at own depots | Modelled (cab public share 30%) | High — BluSmart's successors run private hubs | Cabs are ~70% of SAM; halving their share roughly halves demand | Sign a fleet offtake letter before building |
| Charger supply outpaces cars | Modelled (per-station growth 0–12%) | High — Delhi targets 16,000+ points by end-2026 | Utilisation stays near 8% | Choose a site with no rival within walking distance; stay lean |
| Price war with ₹13 government network (Hyderabad) | Modelled (₹13 case: NPV −₹43 lakh) | High — tender closed 22 Sep 2026 | Margin per unit halves | Do not enter Hyderabad now |
| Electricity surcharges higher than assumed (Delhi) | Assumption | Medium — PPAC applicability unverified | +20% tariff = −₹4 lakh NPV | Get DISCOM confirmation |
| Charger downtime | Modelled (95% uptime) | Medium — many rivals seen faulted | Lost sessions, reputation | AMC with uptime SLA |
| Telangana road-tax waiver lapses (Dec 2026) | Unknown | Uncertain — extension proposed, not approved | Slower e-car growth | Revisit Hyderabad after decision |
| Host terms / site access | Unknown, needs due diligence | — | Levers depend on it | Term sheet before capital |""")

md("""## 21. Key findings
1. Both cities have similar public demand (~15 GWh/yr), driven ~70% by cabs.
2. The lean one-charger station beats bigger hubs; extra chargers are idle capital.
3. Base case fails in both cities: NPV −₹25.4 lakh (Delhi), −₹34.8 lakh (Hyderabad).
4. Break-even needs 25.5% / 35.8% utilisation vs 8.4% national average.
5. Delhi turns positive (NPV +₹5.3 lakh, IRR 20.9%, payback 4.7 years) only with a host site that has spare grid capacity, an unmanned station and a ≤10% host share — and still fails the conservative case.
6. Hyderabad stays negative even with all levers (−₹2.2 lakh), mainly because of the ₹13 government price network.""")

md("""## 22. Recommendation
Under the base-case assumptions the lean station reaches only 7% utilisation in year 1 (13–14% by year 5), EBITDA is negative in year 1 and the project never recovers its ₹31 lakh cost in either city. The project becomes financially unattractive below roughly 25% utilisation in Delhi and 36% in Hyderabad.

- **Delhi — viable only after specific modifications:** proceed only as a pilot of one 60 kW charger at a host site with spare grid capacity, unmanned, host share ≤ 10% (NPV +₹5.3 lakh, IRR 20.9%). Because it fails the conservative scenario, commit capital only after a host term sheet, a cab-fleet offtake letter and DISCOM confirmation of surcharges.
- **Hyderabad — financially unattractive under the modelled assumptions:** do not invest now; revisit after the ₹13 TGREDCO network opens and the road-tax waiver decision (Dec 2026).""")

md("""## 23. Limitations
- Delhi e-car stock is estimated from sales (no published total); Hyderabad uses a 68% share of Telangana.
- Cab share of cars (15%) and cab public-charging share (30%) are assumptions with no published source.
- Competitor prices: 3 private price points per city from one platform on one date; GST inclusion assumed.
- Delhi surcharges on the EV tariff and Telangana duty are not yet verified.
- Charger cost for 60/120 kW is interpolated from MHI benchmarks; maintenance, software and staff costs are assumptions.
- Demand growth per station is a judgement balancing EV growth against charger roll-out.
- Utilisation includes AC chargers in the capacity base; the national benchmark covers DC chargers only.""")

md("""## Model audit""")
code("""# Reconciliation checks: the model's own arithmetic
checks = {}
for city in CITIES:
    r = run_model(city, "base", "A")
    t = r["table"]
    checks[f"{city}: revenue = kWh x price (yr 1)"] = abs(t.loc[0, "revenue"] - t.loc[0, "kwh_per_day"] * 365 * 18.64 * (1 if city == "Delhi" else 16 / 18.64)) < 1
    checks[f"{city}: sold kWh <= capacity (all years)"] = (t["kwh_per_day"] <= r["capacity_kwh_day"] + 1e-6).all()
    checks[f"{city}: EBITDA = gross profit - opex"] = ((t["gross_profit"] - t["opex_excl_electricity"] - t["ebitda"]).abs() < 1).all()
    checks[f"{city}: cumulative = sum of cash flows"] = abs(t["cumulative_cash_flow"].iloc[-1] - sum(r["cash_flows"])) < 1
    be = break_even_kwh_per_day(city, "base", "A")
    checks[f"{city}: NPV at break-even demand ~ 0"] = abs(run_model(city, "base", "A", {"flat_demand_kwh_day": be})["npv"]) < 100
checks["Excel NPV = Python NPV (see Excel 'Checks' sheet)"] = "checked in workbook"
pd.Series(checks, name="result")""")

nb["cells"] = cells
nbf.write(nb, "notebooks/ev_charging_feasibility.ipynb")
print("notebook written")
