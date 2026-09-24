# EV Charging Station Feasibility & Financial Analysis — Delhi vs Hyderabad

> **Verdict:** Don't build the station as designed in either city. **Delhi works only as a conditional pilot:** a single 60 kW charger at a host site with spare grid capacity, run unmanned, with a host revenue share of 10% or less (NPV **+₹5.3 lakh**, IRR **20.9%**, payback **4.7 years**). It still fails the conservative scenario. **Hyderabad is financially unattractive now** (NPV **−₹2.2 lakh** even with every lever pulled), because a ₹13/kWh government charging network is capping prices.

*A portfolio feasibility study for a hypothetical charge-point operator (CPO). There is no real client. Every external number is sourced and labelled in [`docs/source_register.md`](docs/source_register.md).*

---

## 1. Executive summary

| | Delhi | Hyderabad |
|---|---|---|
| Public charging demand (SAM) | 15.2 GWh/yr | 14.0 GWh/yr |
| Best configuration | A: 1 × 60 kW DC + 2 × 7.4 kW AC | A (same) |
| Setup cost (CAPEX) | ₹31.2 lakh | ₹31.2 lakh |
| Utilisation, year 1 → year 5 (base) | 7.3% → 13.6% | 7.2% → 13.4% |
| Year-1 EBITDA (base) | −₹0.9 lakh | −₹1.8 lakh |
| **NPV @ 14.1% (base)** | **−₹25.4 lakh** | **−₹34.8 lakh** |
| IRR / payback (base) | never recovers its cost | never recovers its cost |
| **Break-even utilisation (NPV = 0)** | **25.5%** (16 cars/day) | **35.8%** (22.5 cars/day) |
| National average public DC utilisation | 8.4% | 8.4% |
| NPV with all three levers | **+₹5.3 lakh** (IRR 20.9%) | −₹2.2 lakh (IRR 11.0% < 14.1%) |

**The core insight:** each unit sold earns ₹7–10 after electricity, but fixed costs of about ₹4 lakh a year and a ₹31 lakh setup need **3–4× the utilisation Indian public chargers actually achieve**. The problem is volume, not price or financing.

## 2. Business problem and decision

Should a CPO invest in one public EV charging station (rented site, 10-year horizon) in Delhi, in Hyderabad, in both or in neither, and under what conditions does the investment clear its cost of capital?

**Success tests, agreed before any results:** NPV > 0; IRR > cost of capital; payback before chargers wear out; break-even utilisation below what Indian chargers actually achieve; survives the conservative scenario.

**Scope decisions:**
- **Rented site only.** CPOs rarely buy land, and land would swamp the result.
- **Customers:** cab fleets first, private cars second.
- **Subsidies excluded.** PM E-DRIVE charging funds go to government entities, not private CPOs.

## 3. Selected market and why

Five cities were screened on **new e-cars per year per existing fast-charging station**:

| City | Score | Result |
|---|---|---|
| Delhi | 42.6 | Studied in full |
| Hyderabad | 39.4 | Studied in full |
| Bengaluru | 32.2 | Crowded (state-level data) |
| Pune | 28.3 | Crowded (state-level data) |
| Ranchi | ~11 | Dropped: too few e-cars (~11 cars *in total* per fast station) |

Delhi and Hyderabad were too close to call, so **both were studied in full**.

## 4. Data sources

The primary sources are:
- PIB / Ministry of Heavy Industries Lok Sabha replies (charging stations)
- Vahan data via EVreporter and Autocar Professional (EV sales)
- TGERC and DERC tariff schedules (electricity)
- MHI PM E-DRIVE operational guidelines (benchmark charger and grid costs)
- Damodaran (equity risk premium) and the 10-year G-sec yield (risk-free rate)
- Statiq public station listings (competitor prices, observed 23 Sep 2026)

All 40 numbers are in the source register with URL, date, and a FACT / ESTIMATE / ASSUMPTION / DERIVED label.

## 5. Market analysis and sizing

| | Delhi | Hyderabad |
|---|---|---|
| E-cars on the road (Aug 2026, estimate) | ~45,400 | ~42,000 |
| E-car sales growth, Jan–Aug 2026 | +120% | +100% |
| TAM: all charging energy e-cars need | 80 GWh/yr | 74 GWh/yr |
| SAM: the part bought at public chargers | 15.2 GWh/yr | 14.0 GWh/yr |
| Cabs' share of SAM | ~70% | ~70% |

- **TAM** = cars × km/yr × kWh/km.
- **SAM** = TAM × public-charging share (private cars 10%, cabs 30%).
- **SOM** = SAM ÷ existing fast stations × capture multiple (1.25× in the base case).

**Validation:** spreading SAM across existing fast stations gives about 104 kWh per station per day. An independent national utilisation study implies about 100 kWh/day. The two methods agree.

## 6. Competitor analysis

- **Delhi:** private DC prices are ₹19.99–22.99.
- **Hyderabad:** private DC prices are ₹21.99–24.99. But the government is putting **200 stations at a fixed ₹13 + GST for 10 years** out to tender, and one Gachibowli site already charges ₹13.
- **Reliability gap:** many listed rival chargers showed faulted connectors. Reliability is the only evidence-backed edge a new station has.

## 7. Demand methodology

Year-1 demand (kWh/day) = public demand ÷ existing fast stations × capture multiple × ramp-up.

- Demand then grows each year at a per-station rate: 0% / 7% / 12% for conservative / base / aggressive. The rate is modest because charger supply is growing as fast as cars.
- Demand is capped by what the chargers can physically deliver (40% maximum practical utilisation, 95% uptime).

## 8. Station configuration

| Option | CAPEX | NPV Delhi | NPV Hyderabad |
|---|---|---|---|
| **A: 1 × 60 kW DC + 2 AC** | ₹31.2 L | **−₹25.4 L** | **−₹34.8 L** |
| B: 2 × 60 kW DC + 2 AC | ₹47.0 L | −₹45.3 L | −₹54.8 L |
| C: 2 × 120 kW DC + 2 AC | ₹64.1 L | −₹66.4 L | −₹95.9 L |

At today's demand, extra chargers are idle capital, so the lean option A is used throughout.

## 9. CAPEX, OPEX, revenue, EBITDA, cash flow (option A, base case)

- **CAPEX, ₹31.2 lakh total:**
  - chargers ₹9.3 L
  - grid connection ₹14.8 L (MHI benchmark)
  - civil ₹3.0 L
  - other ₹1.25 L
  - contingency ₹2.8 L
- **OPEX:**
  - electricity: Delhi ₹5.50/kWh, Hyderabad ₹6.00/kWh
  - host share 15% of revenue
  - 1 attendant at ₹20k/month
  - maintenance 5% of charger cost
  - software ₹1,500 per charger per month
  - payment fees 1.5%
  - insurance and miscellaneous
- **Revenue:** kWh sold × price net of GST (Delhi ₹18.64, Hyderabad ₹16.00), rising 2% a year.
- **EBITDA:**
  - year 1: −₹0.9 L (Delhi), −₹1.8 L (Hyderabad)
  - year 5: +₹1.5 L (12% margin, Delhi), −₹0.4 L (Hyderabad)
- **Cash flow:** the cumulative position after 10 years is still −₹15 lakh in Delhi.

Full year-by-year tables are in `outputs/tables/cashflow_*_base.csv`.

## 10. NPV, IRR, payback

- **Discount rate** = 7.02% risk-free + 1.0 × 7.08% India equity risk premium = **14.1%**.
- **Base case:** both cities have negative NPV and never recover their cost within 10 years. IRR is reported as n/a because the project never gets its money back.
- **Discount rate barely matters:** at 12% to 16%, Delhi's NPV only moves between −₹24.5 L and −₹26.1 L.

## 11. Break-even

Break-even was found by solving the full 10-year model for NPV = 0, not by using a generic formula.

| | Utilisation needed | Cars/day needed | For comparison |
|---|---|---|---|
| Delhi | **25.5%** | **16** | EBITDA-only break-even in year 1: 9.2% |
| Hyderabad | **35.8%** | **22.5** | EBITDA-only break-even in year 1: 12.7% |

The national average utilisation is **8.4%**.

## 12. Scenarios

| NPV (₹ lakh) | Conservative | Base | Aggressive |
|---|---|---|---|
| Delhi | −70.8 | −25.4 | +22.6 (IRR 27.2%, payback 4.2 yrs) |
| Hyderabad | −76.1 | −34.8 | +14.9 (IRR 23.1%, payback 4.8 yrs) |

Hyderabad's base case forced down to the ₹13 government price gives an NPV of −₹43.1 lakh.

## 13. Sensitivity

The biggest NPV swings on the base case (Delhi) come from:

| Input changed | NPV range |
|---|---|
| Staff (2 people → none) | −₹40 L to −₹12 L |
| Demand (−30% / +30%) | −₹35 L to −₹16 L |
| Grid connection (new → host's spare capacity) | −₹25 L to −₹9 L |
| CAPEX (±20%) | −₹32 L to −₹19 L |
| Price (±10%) | −₹31 L to −₹20 L |

**Levers stacked on the Delhi base case:**

| Step | NPV |
|---|---|
| Base case | −₹25.4 L |
| + host site with spare grid capacity | −₹8.8 L |
| + unmanned (remote-monitored) | +₹2.9 L |
| + host share cut to 10% | **+₹5.3 L** |

With all three levers, break-even utilisation falls to **10.4%** in Delhi and **14.3%** in Hyderabad.

## 14. Key findings

1. Both cities have about 15 GWh/yr of public charging demand, and about 70% of it comes from cabs.
2. The lean single-charger station beats bigger hubs.
3. The base case fails in both cities: break-even needs 3–4× the national average utilisation.
4. Fixed costs (staff, grid connection) matter more than price or the discount rate.
5. Delhi turns positive only with three negotiated levers, and remains fragile.
6. Hyderabad's ₹13 government network makes private entry unattractive for now.

## 15. Final recommendation

Under base-case assumptions the station reaches 7% utilisation in year 1 and 13–14% by year 5. Year-1 EBITDA is negative, and the ₹31 lakh investment is never recovered in either city. The project becomes unattractive below roughly 25% utilisation in Delhi and 36% in Hyderabad.

- **Delhi: viable only after specific modifications.** Pilot one 60 kW charger at a host site with spare grid capacity, run unmanned, with a host share of 10% or less. Commit capital only after three things are in hand:
  - a host term sheet
  - a cab-fleet offtake letter
  - DISCOM confirmation of the surcharges on the EV tariff
- **Hyderabad: financially unattractive under the modelled assumptions.** Do not invest now. Revisit once the ₹13 TGREDCO network is operating and the road-tax waiver decision (due Dec 2026) is known.

## 16. Risks

The full risk register (likelihood, impact, mitigation) is in the notebook, Section 20. The top risks are:
- cab fleets charging at their own depots (the post-BluSmart model)
- charger supply outpacing cars (Delhi is targeting 16,000+ points)
- a price war with the ₹13 government network in Hyderabad

## 17. Limitations

- Delhi's e-car stock is estimated from sales data.
- The cab share of cars (15%) and the cabs' public-charging share (30%) are assumptions.
- Only 3 private competitor prices per city were collected, on one date, and they are assumed to include GST.
- Delhi's EV tariff surcharges are unverified.
- The cost of 60/120 kW chargers is interpolated from MHI benchmarks.
- Maintenance, software and staff costs are assumptions.

## 18. Repository structure

```
EV-Charging-Feasibility/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/          city_screen_inputs.csv, market_inputs.csv, competitors.csv
│   └── processed/    assumptions.csv (central assumption table), unit_costs.csv, configurations.csv
├── notebooks/        ev_charging_feasibility.ipynb (23 sections + model audit), build_notebook.py
├── src/
│   ├── analysis.py        the financial model (demand → CAPEX/OPEX → cash flow → NPV/IRR → break-even)
│   ├── run_results.py     scenarios, sensitivity, levers, charts
│   ├── city_screen.py     Phase 2 city screen
│   ├── market_sizing.py   Phase 4 TAM/SAM
│   └── competitors.py     Phase 5 competitor matrix
├── excel/            ev_charging_financial_model.xlsx (formula-driven; Checks sheet = TRUE), build_excel.py
├── presentation/     ev_charging_strategy_deck.pptx / .pdf, build_deck.js
├── outputs/          charts/, tables/, run_log.txt
└── docs/             source_register.md, phase1_problem_statement.md, interview_prep.md
```

## 19. How to reproduce

```bash
pip install -r requirements.txt
python src/city_screen.py
python src/market_sizing.py
python src/competitors.py
python src/run_results.py          # model results, tables and charts
python excel/build_excel.py        # rebuild the Excel model (open in Excel to recalculate)
node presentation/build_deck.js    # needs: npm install pptxgenjs
```

Run all commands from the repository root. To test your own assumptions, change `data/processed/assumptions.csv` and rerun, or use the blue input cells on the Excel **Inputs** sheet.
