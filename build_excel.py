# Builds excel/ev_charging_financial_model.xlsx - a formula-driven copy of src/analysis.py.
# Every number the model uses sits on the Inputs sheet (blue = input). Model sheets are pure formulas.

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

assump = pd.read_csv("data/processed/assumptions.csv")
unit_costs = pd.read_csv("data/processed/unit_costs.csv")
configs = pd.read_csv("data/processed/configurations.csv")
scen = pd.read_csv("outputs/tables/scenarios.csv")
sens = pd.read_csv("outputs/tables/sensitivity_tornado.csv")
levers = pd.read_csv("outputs/tables/levers.csv")

ARIAL = "Arial"
BLUE = Font(name=ARIAL, color="0000FF")
BLACK = Font(name=ARIAL, color="000000")
GREEN = Font(name=ARIAL, color="008000")
BOLD = Font(name=ARIAL, bold=True)
TITLE = Font(name=ARIAL, bold=True, size=14)
HEAD_FILL = PatternFill("solid", fgColor="DCE6F1")
KEY_FILL = PatternFill("solid", fgColor="FFFF00")
thin = Side(style="thin", color="BFBFBF")

RS = '#,##0;(#,##0);"-"'
RS1 = '#,##0.0;(#,##0.0);"-"'
RS2 = '#,##0.00;(#,##0.00);"-"'
PCT = '0.0%;(0.0%);"-"'

wb = Workbook()

# ------------------------------------------------------------------ Cover
cover = wb.active
cover.title = "Cover"

# ------------------------------------------------------------------ Inputs
inp = wb.create_sheet("Inputs")
inp["A1"] = "INPUTS - every assumption used by the model (blue = input you can change)"
inp["A1"].font = TITLE

# Controls
inp["A3"] = "CONTROLS"; inp["A3"].font = BOLD
controls = [
    ("Charger configuration (A / B / C)", "A", "config_choice", "A = lean, B = balanced, C = fleet hub; A has the highest NPV in both cities"),
    ("Demand factor", 1.0, "demand_factor", "Multiply demand (1 = as per scenario)"),
    ("Price factor", 1.0, "price_factor", "Multiply charging price (1 = as per scenario)"),
    ("Electricity cost factor", 1.0, "electricity_factor", "Multiply electricity tariff"),
    ("CAPEX factor", 1.0, "capex_factor", "Multiply equipment + civil + grid CAPEX"),
    ("Grid work factor (1 = new connection, 0 = host's spare capacity)", 1.0, "upstream_factor", "Lever: host site already has spare grid capacity"),
    ("Staff FTE override (blank = scenario value)", None, "staff_override", "Lever: 0 = unmanned remote-monitored"),
    ("Host revenue share override (blank = scenario value)", None, "host_override", "Lever: negotiated share"),
    ("Discount rate override (blank = CAPM)", None, "rate_override", "Tested 12%-16%"),
]
ref = {}
row = 4
for label, value, key, note in controls:
    inp.cell(row=row, column=1, value=label).font = BLACK
    c = inp.cell(row=row, column=3, value=value)
    c.font = BLUE
    c.fill = KEY_FILL
    inp.cell(row=row, column=11, value=note).font = Font(name=ARIAL, italic=True, color="595959")
    ref[key] = f"Inputs!$C${row}"
    row += 1

# Scenario assumptions table
row += 1
header_row = row
headers = ["Parameter", "Unit", "Delhi Cons", "Delhi Base", "Delhi Aggr", "Hyd Cons", "Hyd Base", "Hyd Aggr", "Label", "Source / rationale"]
for i, h in enumerate(headers, start=1):
    c = inp.cell(row=row, column=i, value=h)
    c.font = BOLD
    c.fill = HEAD_FILL
row += 1

col_for = {("Delhi", "conservative"): "C", ("Delhi", "base"): "D", ("Delhi", "aggressive"): "E",
           ("Hyderabad", "conservative"): "F", ("Hyderabad", "base"): "G", ("Hyderabad", "aggressive"): "H"}
param_row = {}
for parameter in assump["parameter"].unique():
    rows = assump[assump["parameter"] == parameter]
    first = rows.iloc[0]
    inp.cell(row=row, column=1, value=parameter).font = BLACK
    inp.cell(row=row, column=2, value=first["unit"]).font = BLACK
    for city in ["Delhi", "Hyderabad"]:
        city_rows = rows[rows["city"] == city]
        r = city_rows.iloc[0] if len(city_rows) else rows[rows["city"] == "All"].iloc[0]
        for scenario in ["conservative", "base", "aggressive"]:
            c = inp[f"{col_for[(city, scenario)]}{row}"]
            c.value = float(r[scenario])
            c.font = BLUE
            unit = str(first["unit"])
            if unit in ("share", "per year", "share of net revenue", "share of revenue", "share of capex", "share of hours", "share of rated kW") or "per year" in unit:
                c.number_format = '0.0%'
            elif float(r[scenario]) >= 1000:
                c.number_format = RS
            else:
                c.number_format = '0.00'
    labels = " / ".join(sorted(set(rows["label"])))
    inp.cell(row=row, column=9, value=labels).font = BLACK
    inp.cell(row=row, column=10, value=" | ".join(sorted(set(rows["source_or_rationale"])))).font = Font(name=ARIAL, size=9)
    param_row[parameter] = row
    row += 1

# Unit costs
row += 1
inp.cell(row=row, column=1, value="UNIT COSTS").font = BOLD
row += 1
for i, h in enumerate(["Item", "Unit", "Cost (Rs)", "", "", "", "", "", "Label", "Source / rationale"], start=1):
    c = inp.cell(row=row, column=i, value=h)
    c.font = BOLD
    c.fill = HEAD_FILL
row += 1
cost_row = {}
for _, r in unit_costs.iterrows():
    inp.cell(row=row, column=1, value=r["item"]).font = BLACK
    inp.cell(row=row, column=2, value=r["unit"]).font = BLACK
    c = inp.cell(row=row, column=3, value=float(r["cost_rs"]))
    c.font = BLUE
    c.number_format = RS
    inp.cell(row=row, column=9, value=r["label"]).font = BLACK
    inp.cell(row=row, column=10, value=r["source_or_rationale"]).font = Font(name=ARIAL, size=9)
    cost_row[r["item"]] = row
    row += 1

# Configurations
row += 1
inp.cell(row=row, column=1, value="CHARGER CONFIGURATIONS").font = BOLD
row += 1
for i, h in enumerate(["Config", "Description", "60 kW DC units", "120 kW DC units", "7.4 kW AC units", "Grid band", "Grid work (Rs lakh)", "", "Label", "Source"], start=1):
    c = inp.cell(row=row, column=i, value=h)
    c.font = BOLD
    c.fill = HEAD_FILL
row += 1
config_first = row
for _, r in configs.iterrows():
    vals = [r["config"], r["description"], int(r["dc_60kw_units"]), int(r["dc_120kw_units"]), int(r["ac_7kw_units"]),
            r["upstream_band"], float(r["upstream_cost_lakh"]), None, r["label"], r["source"]]
    for i, v in enumerate(vals, start=1):
        c = inp.cell(row=row, column=i, value=v)
        c.font = BLUE if i in (3, 4, 5, 7) else BLACK
    row += 1
config_last = row - 1
cfg_range = lambda col: f"Inputs!${col}${config_first}:${col}${config_last}"
cfg_keys = f"Inputs!$A${config_first}:$A${config_last}"

inp.column_dimensions["A"].width = 52
inp.column_dimensions["B"].width = 18
for col in "CDEFGH":
    inp.column_dimensions[col].width = 12
inp.column_dimensions["I"].width = 22
inp.column_dimensions["J"].width = 70
inp.column_dimensions["K"].width = 50
inp.freeze_panes = f"C{header_row + 1}"


# ------------------------------------------------------------------ Model sheets (one per city x scenario)
def build_model(city, scenario):
    name = f"{'DEL' if city == 'Delhi' else 'HYD'}_{scenario[:4].capitalize()}"
    ws = wb.create_sheet(name)
    col = col_for[(city, scenario)]
    P = lambda p: f"Inputs!${col}${param_row[p]}"          # scenario assumption
    U = lambda item: f"Inputs!$C${cost_row[item]}"          # unit cost

    ws["A1"] = f"{city} - {scenario} scenario - station model (all formulas)"
    ws["A1"].font = TITLE
    ws["A2"] = "Green = link to Inputs, black = calculation. Change inputs on the Inputs sheet only."
    ws["A2"].font = Font(name=ARIAL, italic=True, color="595959")

    lines = []   # (label, formula, format, key)
    def add(label, formula, fmt, key, link=False):
        lines.append((label, formula, fmt, key, link))

    add("Configuration", f"={ref['config_choice']}", None, "cfg", True)
    add("60 kW DC chargers", f"=INDEX({cfg_range('C')},MATCH(C4,{cfg_keys},0))", "0", "n60")
    add("120 kW DC chargers", f"=INDEX({cfg_range('D')},MATCH(C4,{cfg_keys},0))", "0", "n120")
    add("7.4 kW AC chargers", f"=INDEX({cfg_range('E')},MATCH(C4,{cfg_keys},0))", "0", "nac")
    add("Total chargers", "=C5+C6+C7", "0", "nch")
    add("Total connected kW", "=C5*60+C6*120+C7*7.4", "0.0", "kw")
    # CAPEX
    add("CAPEX multiplier (scenario x control)", f"={P('capex_multiplier')}*{ref['capex_factor']}", "0.00", "cm")
    add("Chargers (Rs)", f"=(C5*{U('dc_60kw_charger')}+C6*{U('dc_120kw_charger')}+C7*{U('ac_7kw_charger')})*C10", RS, "cap_ch")
    add("Grid connection work (Rs)", f"=INDEX({cfg_range('G')},MATCH(C4,{cfg_keys},0))*100000*C10*{ref['upstream_factor']}", RS, "cap_up")
    add("Civil & installation (Rs)", f"=((C5+C6)*{U('civil_per_dc_bay')}+C7*{U('civil_per_ac_bay')})*C10", RS, "cap_civ")
    add("Signage, software set-up, permits (Rs)", f"={U('signage')}+{U('software_setup')}+{U('permits_misc')}", RS, "cap_oth")
    add("Contingency (Rs)", f"=SUM(C11:C14)*{P('contingency')}", RS, "cap_cont")
    add("TOTAL CAPEX (Rs)", "=SUM(C11:C15)", RS, "capex")
    # Capacity and demand
    add("Capacity, kWh/day (at max practical utilisation)", f"=C9*{P('power_delivery_factor')}*24*{P('max_practical_utilisation')}*{P('uptime')}", RS1, "capacity")
    add("Energy if in use 24h, kWh/day (for utilisation %)", f"=C9*{P('power_delivery_factor')}*24", RS1, "fulltime")
    add("Fair share of public demand, kWh/day", f"={P('public_demand_kwh_per_day')}/{P('fast_stations')}", RS1, "fair")
    add("Steady demand year 1, kWh/day", f"=C19*{P('capture_multiple')}*{ref['demand_factor']}", RS1, "steady")
    # Prices / costs
    add("Price net of GST year 1 (Rs/kWh)", f"={P('price_net_of_gst')}*{ref['price_factor']}", RS2, "price")
    add("Electricity tariff year 1 (Rs/kWh)", f"={P('electricity_rs_per_kwh')}*{ref['electricity_factor']}", RS2, "tariff")
    ht = f"C9/0.95*{U('hyd_ht_demand_charge')}+{U('hyd_ht_customer_charge')}" if city == "Hyderabad" else "0"
    add("Fixed electricity charge (Rs/month)", f"=IF(AND({'TRUE' if city == 'Hyderabad' else 'FALSE'},C9>150),{ht},{P('electricity_fixed_rs_per_month')})", RS, "fixed_elec")
    add("Host revenue share", f"=IF({ref['host_override']}=\"\",{P('host_revenue_share')},{ref['host_override']})", PCT, "host")
    add("Staff FTE", f"=IF({ref['staff_override']}=\"\",{P('staff_fte')},{ref['staff_override']})", "0.0", "fte")
    add("Discount rate (CAPM: Rf + beta x ERP)", f"=IF({ref['rate_override']}=\"\",{P('risk_free_rate')}+{P('beta')}*{P('equity_risk_premium')},{ref['rate_override']})", PCT, "rate")
    add("Annual depreciation (Rs)", f"=C16/{P('depreciation_years')}", RS, "dep")

    r = 4
    key_row = {}
    for label, formula, fmt, key, link in lines:
        ws.cell(row=r, column=1, value=label).font = BLACK
        c = ws.cell(row=r, column=3, value=formula)
        c.font = GREEN if ("Inputs!" in formula and formula.count("Inputs!") == 1 and formula.startswith("=Inputs")) else BLACK
        if fmt:
            c.number_format = fmt
        key_row[key] = r
        r += 1
    ws["A16"].font = BOLD
    ws["C16"].font = BOLD

    # ---------------- Annual table ----------------
    top = r + 2
    ws.cell(row=top, column=1, value="ANNUAL PROJECTION (Rs unless stated)").font = BOLD
    yr_row = top + 1
    ws.cell(row=yr_row, column=1, value="Year").font = BOLD
    for y in range(0, 11):
        c = ws.cell(row=yr_row, column=3 + y, value=str(y))
        c.font = BOLD
        c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal="center")
    YC = lambda y: get_column_letter(3 + y)        # Year 0 in column C, Year 1 in D ... Year 10 in M

    items = ["Demand kWh/day", "kWh sold per day", "Sessions per day", "Utilisation (% of hours)", "kWh sold per year",
             "Revenue", "Electricity cost", "Gross profit", "Host revenue share", "Staff", "Maintenance", "Software / CMS",
             "Payment fees", "Insurance", "Misc (internet, cleaning, admin)", "Opex excl. electricity", "EBITDA",
             "EBITDA margin", "Depreciation", "EBIT", "Tax losses brought forward", "Tax losses used", "Tax",
             "Free cash flow (EBITDA - tax)", "CAPEX + working capital", "Net cash flow", "Cumulative cash flow", "Payback helper"]
    R = {}
    for i, it in enumerate(items):
        R[it] = yr_row + 1 + i
        ws.cell(row=R[it], column=1, value=it).font = BOLD if it in ("Revenue", "EBITDA", "Net cash flow") else BLACK

    for y in range(1, 11):
        L = YC(y)
        prev = YC(y - 1)
        g = f"(1+{P('demand_growth_per_station')})^({y}-1)"
        infl = f"(1+{P('fixed_cost_inflation')})^({y}-1)"
        ramp = f"*{P('year1_ramp')}" if y == 1 else ""
        f = {
            "Demand kWh/day": f"=$C${key_row['steady']}*{g}{ramp}",
            "kWh sold per day": f"=MIN({L}{R['Demand kWh/day']},$C${key_row['capacity']})",
            "Sessions per day": f"={L}{R['kWh sold per day']}/{P('kwh_per_session')}",
            "Utilisation (% of hours)": f"={L}{R['kWh sold per day']}/$C${key_row['fulltime']}",
            "kWh sold per year": f"={L}{R['kWh sold per day']}*365",
            "Revenue": f"={L}{R['kWh sold per year']}*$C${key_row['price']}*(1+{P('price_escalation')})^({y}-1)",
            "Electricity cost": f"=({L}{R['kWh sold per year']}/(1-{P('grid_losses')})*$C${key_row['tariff']}+$C${key_row['fixed_elec']}*12)*(1+{P('tariff_escalation')})^({y}-1)",
            "Gross profit": f"={L}{R['Revenue']}-{L}{R['Electricity cost']}",
            "Host revenue share": f"={L}{R['Revenue']}*$C${key_row['host']}",
            "Staff": f"=$C${key_row['fte']}*{P('staff_cost_rs_per_month')}*12*{infl}",
            "Maintenance": f"=$C${key_row['cap_ch']}*{P('maintenance_pct_of_charger_capex')}*{infl}",
            "Software / CMS": f"=$C${key_row['nch']}*{P('cms_rs_per_charger_month')}*12*{infl}",
            "Payment fees": f"={L}{R['Revenue']}*{P('payment_fee_share')}",
            "Insurance": f"=$C${key_row['capex']}*{P('insurance_pct_of_capex')}*{infl}",
            "Misc (internet, cleaning, admin)": f"={P('misc_rs_per_month')}*12*{infl}",
            "Opex excl. electricity": f"=SUM({L}{R['Host revenue share']}:{L}{R['Misc (internet, cleaning, admin)']})",
            "EBITDA": f"={L}{R['Gross profit']}-{L}{R['Opex excl. electricity']}",
            "EBITDA margin": f"=IFERROR({L}{R['EBITDA']}/{L}{R['Revenue']},0)",
            "Depreciation": f"=$C${key_row['dep']}",
            "EBIT": f"={L}{R['EBITDA']}-{L}{R['Depreciation']}",
            "Tax losses brought forward": "=0" if y == 1 else f"={prev}{R['Tax losses brought forward']}+MAX(0,-{prev}{R['EBIT']})-{prev}{R['Tax losses used']}",
            "Tax losses used": f"=MIN({L}{R['Tax losses brought forward']},MAX(0,{L}{R['EBIT']}))",
            "Tax": f"=MAX(0,{L}{R['EBIT']}-{L}{R['Tax losses used']})*{P('tax_rate')}",
            "Free cash flow (EBITDA - tax)": f"={L}{R['EBITDA']}-{L}{R['Tax']}",
            "CAPEX + working capital": "=$C$%d" % R["CAPEX + working capital"] + "*-1" if y == 10 else "=0",
            "Net cash flow": f"={L}{R['Free cash flow (EBITDA - tax)']}+{L}{R['CAPEX + working capital']}",
            "Cumulative cash flow": f"={prev}{R['Cumulative cash flow']}+{L}{R['Net cash flow']}",
            "Payback helper": f"=IF(AND({prev}{R['Cumulative cash flow']}<0,{L}{R['Cumulative cash flow']}>=0),{y}-1-{prev}{R['Cumulative cash flow']}/{L}{R['Net cash flow']},\"\")",
        }
        for it, formula in f.items():
            c = ws[f"{L}{R[it]}"]
            c.value = formula
            c.font = BLACK
            c.number_format = PCT if it in ("Utilisation (% of hours)", "EBITDA margin") else (RS1 if it in ("Demand kWh/day", "kWh sold per day", "Sessions per day") else RS)

    # Year 0: CAPEX and working capital (1 month of year-1 running costs, returned in year 10)
    wc = f"({YC(1)}{R['Electricity cost']}+{YC(1)}{R['Opex excl. electricity']})/12"
    ws[f"C{R['CAPEX + working capital']}"] = f"=-($C${key_row['capex']}+{wc})"
    ws[f"C{R['Net cash flow']}"] = f"=C{R['CAPEX + working capital']}"
    ws[f"C{R['Cumulative cash flow']}"] = f"=C{R['Net cash flow']}"
    # Year 10 returns working capital = -(year-0 amount minus capex)
    ws[f"M{R['CAPEX + working capital']}"] = f"=-C{R['CAPEX + working capital']}-$C${key_row['capex']}"
    for it in ("CAPEX + working capital", "Net cash flow", "Cumulative cash flow"):
        ws[f"C{R[it]}"].number_format = RS
        ws[f"M{R['CAPEX + working capital']}"].number_format = RS

    # ---------------- Outputs ----------------
    out = R["Payback helper"] + 2
    ws.cell(row=out, column=1, value="OUTPUTS").font = BOLD
    cf = f"D{R['Net cash flow']}:M{R['Net cash flow']}"
    outputs = [
        ("NPV (Rs)", f"=NPV($C${key_row['rate']},{cf})+C{R['Net cash flow']}", RS, "npv"),
        ("IRR", f"=IF(SUM(C{R['Net cash flow']}:M{R['Net cash flow']})<0,\"n/a (never recovers)\",IFERROR(IRR(C{R['Net cash flow']}:M{R['Net cash flow']},0.1),\"n/a\"))", PCT, "irr"),
        ("Payback (years)", f"=IF(COUNT(D{R['Payback helper']}:M{R['Payback helper']})=0,\"Not within 10 years\",MIN(D{R['Payback helper']}:M{R['Payback helper']}))", "0.0", "payback"),
        ("Year-1 utilisation", f"=D{R['Utilisation (% of hours)']}", PCT, "u1"),
        ("Year-5 utilisation", f"=H{R['Utilisation (% of hours)']}", PCT, "u5"),
        ("Year-1 revenue (Rs)", f"=D{R['Revenue']}", RS, "rev1"),
        ("Year-1 EBITDA (Rs)", f"=D{R['EBITDA']}", RS, "e1"),
        ("Year-5 EBITDA (Rs)", f"=H{R['EBITDA']}", RS, "e5"),
        ("Year-5 EBITDA margin", f"=H{R['EBITDA margin']}", PCT, "m5"),
        # Year-1 EBITDA break-even: fixed costs / contribution per kWh
        ("Contribution per kWh, year 1 (Rs)",
         f"=$C${key_row['price']}*(1-$C${key_row['host']}-{P('payment_fee_share')})-$C${key_row['tariff']}/(1-{P('grid_losses')})", RS2, "contrib"),
        ("Fixed costs, year 1 (Rs)",
         f"=D{R['Staff']}+D{R['Maintenance']}+D{R['Software / CMS']}+D{R['Insurance']}+D{R['Misc (internet, cleaning, admin)']}+$C${key_row['fixed_elec']}*12", RS, "fixedcost"),
        ("EBITDA break-even, kWh/day", f"=IF(C{{contrib}}>0,C{{fixedcost}}/C{{contrib}}/365,\"n/a\")", RS1, "be_kwh"),
        ("EBITDA break-even, sessions/day", f"=IFERROR(C{{be_kwh}}/{P('kwh_per_session')},\"n/a\")", RS1, "be_sess"),
        ("EBITDA break-even, utilisation", f"=IFERROR(C{{be_kwh}}/$C${key_row['fulltime']},\"n/a\")", PCT, "be_util"),
    ]
    out_row = {}
    r = out + 1
    for label, formula, fmt, key in outputs:
        out_row[key] = r
        r += 1
    r = out + 1
    for label, formula, fmt, key in outputs:
        formula = formula.replace("{contrib}", str(out_row["contrib"])).replace("{fixedcost}", str(out_row["fixedcost"])) \
                         .replace("{be_kwh}", str(out_row["be_kwh"]))
        ws.cell(row=r, column=1, value=label).font = BOLD if key in ("npv", "irr", "payback") else BLACK
        c = ws.cell(row=r, column=3, value=formula)
        c.font = BOLD if key in ("npv", "irr", "payback") else BLACK
        c.number_format = fmt
        if key == "npv":
            c.fill = KEY_FILL
        r += 1

    ws.column_dimensions["A"].width = 48
    ws.column_dimensions["B"].width = 4
    for y in range(0, 11):
        ws.column_dimensions[get_column_letter(3 + y)].width = 13
    ws.freeze_panes = "C4"
    return name, out_row, R


model_info = {}
for city in ["Delhi", "Hyderabad"]:
    for scenario in ["conservative", "base", "aggressive"]:
        model_info[(city, scenario)] = build_model(city, scenario)


# ------------------------------------------------------------------ Scenarios sheet (links to model sheets)
sc = wb.create_sheet("Scenarios", 2)
sc["A1"] = "SCENARIO COMPARISON - live links to the six model sheets"
sc["A1"].font = TITLE
metrics = [("Year-1 utilisation", "u1", PCT), ("Year-5 utilisation", "u5", PCT), ("Year-1 revenue (Rs)", "rev1", RS),
           ("Year-1 EBITDA (Rs)", "e1", RS), ("Year-5 EBITDA (Rs)", "e5", RS), ("Year-5 EBITDA margin", "m5", PCT),
           ("NPV (Rs)", "npv", RS), ("IRR", "irr", PCT), ("Payback (years)", "payback", "0.0"),
           ("EBITDA break-even utilisation (yr 1)", "be_util", PCT), ("EBITDA break-even sessions/day (yr 1)", "be_sess", RS1)]
hdr = ["Metric", "Delhi Cons", "Delhi Base", "Delhi Aggr", "Hyd Cons", "Hyd Base", "Hyd Aggr"]
for i, h in enumerate(hdr, start=1):
    c = sc.cell(row=3, column=i, value=h)
    c.font = BOLD
    c.fill = HEAD_FILL
order = [("Delhi", "conservative"), ("Delhi", "base"), ("Delhi", "aggressive"),
         ("Hyderabad", "conservative"), ("Hyderabad", "base"), ("Hyderabad", "aggressive")]
for j, (label, key, fmt) in enumerate(metrics):
    sc.cell(row=4 + j, column=1, value=label).font = BLACK
    for i, cs in enumerate(order):
        name, out_row, _ = model_info[cs]
        c = sc.cell(row=4 + j, column=2 + i, value=f"='{name}'!C{out_row[key]}")
        c.font = GREEN
        c.number_format = fmt
r = 4 + len(metrics) + 1
sc.cell(row=r, column=1, value="NPV break-even utilisation (from Python bisection; Excel has no goal-seek in a static file)").font = BOLD
r += 1
for i, cs in enumerate(order):
    rowv = scen[(scen["city"] == cs[0]) & (scen["scenario"] == cs[1])]["breakeven_npv_utilisation_pct"].iloc[0]
    c = sc.cell(row=r, column=2 + i, value=None if pd.isna(rowv) else float(rowv) / 100)
    c.font = BLUE
    c.number_format = PCT
sc.cell(row=r, column=1, value="NPV break-even utilisation (blank = not reachable within capacity)").font = BLACK
sc.column_dimensions["A"].width = 60
for col in "BCDEFG":
    sc.column_dimensions[col].width = 16


# ------------------------------------------------------------------ Sensitivity sheet (Python results + how to reproduce live)
se = wb.create_sheet("Sensitivity", 3)
se["A1"] = "SENSITIVITY - NPV (Rs lakh), base case, one input changed at a time"
se["A1"].font = TITLE
se["A2"] = ("Values come from src/run_results.py. To reproduce any row live: set the matching factor on the Inputs "
            "sheet (e.g. Demand factor = 0.7) and read NPV on DEL_Base / HYD_Base.")
se["A2"].font = Font(name=ARIAL, italic=True, color="595959")
for i, h in enumerate(["City", "Input tested", "Base NPV", "NPV worse", "NPV better", "Swing"], start=1):
    c = se.cell(row=4, column=i, value=h)
    c.font = BOLD
    c.fill = HEAD_FILL
for k, (_, r_) in enumerate(sens.iterrows()):
    vals = [r_["city"], r_["input"], r_["base_npv_lakh"], r_["npv_bad_lakh"], r_["npv_good_lakh"], r_["swing_lakh"]]
    for i, v in enumerate(vals, start=1):
        c = se.cell(row=5 + k, column=i, value=v)
        c.font = BLUE if i >= 3 else BLACK
        if i >= 3:
            c.number_format = RS1
r = 5 + len(sens) + 2
se.cell(row=r, column=1, value="WHAT WOULD IT TAKE? Controllable levers stacked on the base case (Rs lakh)").font = BOLD
r += 1
for i, h in enumerate(["City", "Step", "CAPEX", "NPV", "IRR %", "Payback yrs"], start=1):
    c = se.cell(row=r, column=i, value=h)
    c.font = BOLD
    c.fill = HEAD_FILL
for _, r_ in levers.iterrows():
    r += 1
    vals = [r_["city"], r_["step"], r_["capex_lakh"], r_["npv_lakh"], r_["irr_pct"], r_["payback_years"]]
    for i, v in enumerate(vals, start=1):
        c = se.cell(row=r, column=i, value=None if (isinstance(v, float) and pd.isna(v)) else v)
        c.font = BLUE if i >= 3 else BLACK
        if i >= 3:
            c.number_format = RS1
se.column_dimensions["A"].width = 12
se.column_dimensions["B"].width = 55
for col in "CDEF":
    se.column_dimensions[col].width = 14


# ------------------------------------------------------------------ Checks sheet
ch = wb.create_sheet("Checks", 4)
ch["A1"] = "MODEL CHECKS - every row must read TRUE"
ch["A1"].font = TITLE
checks = []
py_npv = {(r_["city"], r_["scenario"]): r_["npv_lakh"] * 100000 for _, r_ in scen.iterrows()}
row = 3
for cs, (name, out_row, R) in model_info.items():
    checks.append((f"{name}: sold kWh never exceeds capacity",
                   f"=MAX('{name}'!D{R['kWh sold per day']}:M{R['kWh sold per day']})<='{name}'!C17+0.001"))
    checks.append((f"{name}: revenue = kWh x price (year 1)",
                   f"=ABS('{name}'!D{R['Revenue']}-'{name}'!D{R['kWh sold per year']}*'{name}'!C21)<1"))
    checks.append((f"{name}: EBITDA = gross profit - opex (year 5)",
                   f"=ABS('{name}'!H{R['EBITDA']}-('{name}'!H{R['Gross profit']}-'{name}'!H{R['Opex excl. electricity']}))<1"))
    checks.append((f"{name}: cumulative cash = sum of net cash flows",
                   f"=ABS('{name}'!M{R['Cumulative cash flow']}-SUM('{name}'!C{R['Net cash flow']}:M{R['Net cash flow']}))<1"))
    checks.append((f"{name}: Excel NPV matches Python NPV (config A, all factors = 1) within Rs 1,000",
                   f"=OR(Inputs!$C$4<>\"A\",ABS('{name}'!C{out_row['npv']}-{py_npv[cs]:.2f})<1000)"))
for label, formula in checks:
    ch.cell(row=row, column=1, value=label).font = BLACK
    ch.cell(row=row, column=2, value=formula).font = BLACK
    row += 1
ch.cell(row=row + 1, column=1, value="ALL CHECKS PASS").font = BOLD
ch.cell(row=row + 1, column=2, value=f"=AND(B3:B{row - 1})").font = BOLD
ch.column_dimensions["A"].width = 85
ch.column_dimensions["B"].width = 18


# ------------------------------------------------------------------ Cover / executive summary (links to Scenarios)
cover["A1"] = "EV Charging Station Feasibility - Delhi vs Hyderabad"
cover["A1"].font = Font(name=ARIAL, bold=True, size=16)
cover["A2"] = "Portfolio feasibility study for a hypothetical charge-point operator. Not a real client engagement."
cover["A2"].font = Font(name=ARIAL, italic=True, color="595959")
cover["A4"] = "Decision question"
cover["A4"].font = BOLD
cover["A5"] = "Should a CPO invest in one public EV charging station (rented site, 10 years) in Delhi, Hyderabad, both or neither - and under what conditions?"
cover["A7"] = "Key outputs (base case, live links)"
cover["A7"].font = BOLD
kpis = [("Delhi NPV (Rs)", "C10", RS), ("Delhi IRR", "C11", PCT), ("Hyderabad NPV (Rs)", "F10", RS), ("Hyderabad IRR", "F11", PCT),
        ("Delhi year-1 utilisation", "C4", PCT), ("Hyderabad year-1 utilisation", "F4", PCT)]
for i, (label, cell, fmt) in enumerate(kpis):
    cover.cell(row=8 + i, column=1, value=label).font = BLACK
    c = cover.cell(row=8 + i, column=2, value=f"=Scenarios!{cell}")
    c.font = GREEN
    c.number_format = fmt
cover["A15"] = "How to use"
cover["A15"].font = BOLD
notes = ["Blue cells = inputs (change on the Inputs sheet only). Black = formulas. Green = links between sheets. Yellow = key levers.",
         "Six model sheets: DEL_/HYD_ x Cons/Base/Aggr. Each is the same formula layout reading its own scenario column.",
         "Levers on Inputs (grid work factor, staff override, host share override) reproduce the 'what would it take' case.",
         "Checks sheet must show ALL CHECKS PASS = TRUE.",
         "Sources for every number: docs/source_register.md in the repository."]
for i, n in enumerate(notes):
    cover.cell(row=16 + i, column=1, value=n).font = BLACK
cover.column_dimensions["A"].width = 60
cover.column_dimensions["B"].width = 20

for ws in wb.worksheets:
    for row_cells in ws.iter_rows():
        for c in row_cells:
            if c.font is None or c.font.name != ARIAL:
                c.font = Font(name=ARIAL, bold=c.font.bold if c.font else False, italic=c.font.italic if c.font else False,
                              color=c.font.color if c.font else None, size=c.font.size if c.font else 11)

wb.save("excel/ev_charging_financial_model.xlsx")
print("saved")
