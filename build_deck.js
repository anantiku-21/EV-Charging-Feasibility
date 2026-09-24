// Builds presentation/ev_charging_strategy_deck.pptx from the model's output tables.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
function readCsv(file) {
  const filePath = path.join(root, file);

  const lines = fs
    .readFileSync(filePath, "utf8")
    .replace(/^\uFEFF/, "")
    .trim()
    .split(/\r?\n/);

  const head = lines[0]
    .split(",")
    .map(h => h.trim());

  return lines.slice(1).map(line => {
    const cells = line.split(",");
    const o = {};

    head.forEach((h, i) => {
      const raw = (cells[i] ?? "").trim();

      if (raw === "") {
        o[h] = undefined;
      } else if (!isNaN(Number(raw))) {
        o[h] = Number(raw);
      } else {
        o[h] = raw;
      }
    });

    return o;
  });
}

const scen = readCsv("outputs/tables/scenarios.csv");
const cfg = readCsv("outputs/tables/config_comparison.csv");
const market = readCsv("outputs/tables/market_sizing.csv");
const curve = readCsv("outputs/tables/npv_vs_utilisation.csv");
const levers = readCsv("outputs/tables/levers.csv");
const robust = readCsv("outputs/tables/levers_by_scenario.csv");
const cashD = readCsv("outputs/tables/cashflow_delhi_base.csv");

const S = (city, sc) =>
  scen.find(r => r.city === city && r.scenario === sc);

const L = (city, step) =>
  levers.find(r => r.city === city && r.step === step);

const R = (city, sc) =>
  robust.find(r => r.city === city && r.scenario === sc);

const f0 = x =>
  x == null || x === "" ? "-" : Math.round(Number(x)).toString();

const f1 = x =>
  x == null || x === "" || isNaN(Number(x))
    ? "-"
    : Number(x).toFixed(1);

// Palette: deep teal (dominant), electric teal, amber warning accent
const DARK = "0E3B43", TEAL = "0F7C84", TEAL_L = "D7EEEE", AMBER = "E08A1E", INK = "1B1B1B", MUTED = "5A6468", BG = "FFFFFF", CARD = "F1F6F6";
const DELHI = "0F7C84", HYD = "E08A1E";
const HEAD = "Cambria", BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";   // 10 x 5.625 in
pres.title = "EV Charging Station Feasibility - Delhi vs Hyderabad";

function title(slide, text, sub) {
  slide.addText(text, { x: 0.5, y: 0.3, w: 9, h: 0.75, fontFace: HEAD, fontSize: 22, bold: true, color: DARK, margin: 0, isTextBox: true, valign: "top" });
  if (sub) slide.addText(sub, { x: 0.5, y: 1.02, w: 9, h: 0.3, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
}
function source(slide, text) {
  slide.addText(text, { x: 0.5, y: 5.22, w: 9, h: 0.25, fontFace: BODY, fontSize: 8, color: MUTED, margin: 0, isTextBox: true });
}
function stat(slide, x, y, w, big, label, colour) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.05, fill: { color: CARD }, line: { color: CARD }, rectRadius: 0.08 });
  slide.addText(big, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.55, fontFace: HEAD, fontSize: 24, bold: true, color: colour || DARK, margin: 0, isTextBox: true });
  slide.addText(label, { x: x + 0.15, y: y + 0.62, w: w - 0.3, h: 0.38, fontFace: BODY, fontSize: 10, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
}

// ---------------- Slide 1: Executive summary ----------------
{
  const s = pres.addSlide();
  s.background = { color: DARK };
  s.addText("EV CHARGING STATION FEASIBILITY  |  DELHI vs HYDERABAD", { x: 0.5, y: 0.3, w: 9, h: 0.3, fontFace: BODY, fontSize: 10, color: "9FD3D6", bold: true, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Don't build as designed. Delhi works only as a small, host-powered, unmanned site; Hyderabad does not work yet.",
    { x: 0.5, y: 0.65, w: 9, h: 1.1, fontFace: HEAD, fontSize: 22, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, valign: "top" });
  s.addText("Question: should a charge-point operator invest in one public station (rented site, 10 years) in Delhi, Hyderabad, both or neither, and under what conditions?",
    { x: 0.5, y: 1.8, w: 9, h: 0.5, fontFace: BODY, fontSize: 12, color: "CFE5E6", margin: 0, isTextBox: true });
  const d = S("Delhi", "base"), h = S("Hyderabad", "base"), dl = L("Delhi", "+ host share cut to 10%");
  const tiles = [
    [`Rs ${f0(d.npv_lakh)} / ${f0(h.npv_lakh)} lakh`, "Base-case NPV, Delhi / Hyderabad\n(Rs 31 lakh setup, 14.1% cost of capital)"],
    [`${f0(d.breakeven_npv_utilisation_pct)}% / ${f0(h.breakeven_npv_utilisation_pct)}%`, "Utilisation needed to break even\nvs 8.4% national average"],
    [`Rs +${f1(dl.npv_lakh)} lakh`, `Delhi NPV with all 3 levers\nIRR ${f1(dl.irr_pct)}%, payback ${f1(dl.payback_years)} yrs`],
  ];
  tiles.forEach((t, i) => {
    const x = 0.5 + i * 3.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.55, w: 2.85, h: 1.35, fill: { color: "175059" }, line: { color: "175059" }, rectRadius: 0.08 });
    s.addText(t[0], { x: x + 0.15, y: 2.65, w: 2.6, h: 0.55, fontFace: HEAD, fontSize: 22, bold: true, color: i === 2 ? "F5C27A" : "FFFFFF", margin: 0, isTextBox: true });
    s.addText(t[1], { x: x + 0.15, y: 3.22, w: 2.6, h: 0.62, fontFace: BODY, fontSize: 10, color: "CFE5E6", margin: 0, isTextBox: true, valign: "top" });
  });
  s.addText([
    { text: "Condition: ", options: { bold: true, color: "F5C27A" } },
    { text: `the Delhi case needs a host site with spare grid capacity, no on-site staff and a host share of 10% or less. It still fails the conservative scenario (NPV Rs ${f0(R("Delhi", "conservative").npv_lakh)} lakh), so pilot one site before committing more capital.`, options: { color: "FFFFFF" } },
  ], { x: 0.5, y: 4.15, w: 9, h: 0.75, fontFace: BODY, fontSize: 12, margin: 0, isTextBox: true, valign: "top" });
  source(s, "Portfolio feasibility study for a hypothetical operator. All figures from the project model (Python and Excel reconcile).");
  s.addNotes("Lead with the decision. Base case fails in both cities because utilisation is far below break-even. Delhi becomes positive only when three controllable levers are pulled together.");
}

// ---------------- Slide 2: Market ----------------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  title(s, "Both cities have ~15 GWh a year of public charging demand, and cabs are 70% of it",
        "Electric cars on the road (Aug 2026) and the share of their charging bought at public chargers (SAM)");
  const cities = market.map(m => m.city);
  s.addChart(pres.charts.BAR, [
    { name: "Private cars", labels: cities, values: market.map(m => m.sam_private_mwh / 1000) },
    { name: "Cabs", labels: cities, values: market.map(m => m.sam_cab_mwh / 1000) },
  ], { x: 0.5, y: 1.45, w: 5.4, h: 3.6, barDir: "bar", barGrouping: "stacked", chartColors: [TEAL, AMBER],
       showValue: true, dataLabelPosition: "ctr", dataLabelFormatCode: "0.0", dataLabelColor: "FFFFFF", dataLabelFontSize: 10,
       showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: MUTED,
       showTitle: true, title: "Public charging demand, GWh per year", titleFontSize: 11, titleColor: INK,
       catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valGridLine: { color: "E3E7E8", size: 0.5 }, catGridLine: { style: "none" } });
  stat(s, 6.2, 1.45, 3.3, `${(market[0].ecar_stock / 1000).toFixed(0)}k / ${(market[1].ecar_stock / 1000).toFixed(0)}k`, "Electric cars on the road, Delhi / Hyderabad (estimate)");
  stat(s, 6.2, 2.65, 3.3, "+120% / +100%", "E-car sales growth, Jan-Aug 2026 vs 2025");
  stat(s, 6.2, 3.85, 3.3, "~81%", "of charging happens at home or at fleet depots, so only ~19% is open to public stations", AMBER);
  source(s, "Sources: Autocar Professional (Sep 2026), EVreporter, Hyderabad RTA, Kazam-AEEE (2026), Goel et al. (2015). Cab share of cars (15%) and cab public-charging share (30%) are assumptions.");
}

// ---------------- Slide 3: Competition ----------------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  title(s, "Delhi rivals charge Rs 20-22 per unit; in Hyderabad a Rs 13 government network caps prices",
        "DC fast-charging prices seen on public station listings (23 Sep 2026) and reported network prices");
  const hdr = { bold: true, color: "FFFFFF", fill: { color: DARK }, fontFace: BODY, fontSize: 10 };
  const c = { fontFace: BODY, fontSize: 10, color: INK };
  const rows = [
    [{ text: "City", options: hdr }, { text: "Station / network", options: hdr }, { text: "Area", options: hdr }, { text: "Power", options: hdr }, { text: "Rs/kWh", options: hdr }],
    ["Delhi", "GMR Aerocity (Statiq)", "Aerocity", "60 kW", "19.99"],
    ["Delhi", "Statiq Mahipalpur Hub", "Airport corridor", "25-120 kW", "21.99-22.99"],
    ["Delhi", "Glida DLF Avenue", "Saket", "60 kW", "21.99"],
    ["Delhi", "Tata Power / Jio-bp (reported)", "Network", "30-60 kW", "15-22 / 18-20"],
    ["Hyderabad", "Divyasree Trinity (Statiq)", "HITEC City", "120 kW", "24.99"],
    ["Hyderabad", "Spider SLN / Solitaire (Statiq)", "Gachibowli", "120 kW", "21.99"],
    ["Hyderabad", "TSIIC IOCL Bunk", "Gachibowli", "60 kW", "13.00"],
    ["Hyderabad", "TGREDCO network, 200 stations", "City-wide", "-", "13 + GST, fixed 10 yrs"],
  ].map((r, i) => i === 0 ? r : r.map((v, j) => ({ text: v, options: { ...c, bold: j === 4, color: (i >= 7 && j === 4) ? AMBER : INK, fill: { color: i % 2 ? "FFFFFF" : CARD } } })));
  s.addTable(rows, { x: 0.5, y: 1.45, w: 5.9, colW: [0.85, 2.05, 1.1, 0.8, 1.1], rowH: 0.36, border: { type: "solid", color: "E3E7E8", pt: 0.5 } });
  s.addText("What it means", { x: 6.7, y: 1.45, w: 2.8, h: 0.3, fontFace: HEAD, fontSize: 14, bold: true, color: DARK, margin: 0, isTextBox: true });
  s.addText([
    { text: "Delhi: price of about Rs 22 (Rs 18.64 net of GST) is realistic; the risk is supply, with 16,000+ points planned by end-2026.", options: { bullet: true, breakLine: true } },
    { text: "Hyderabad: a cab driver saves ~Rs 9 a unit at the government stations, so our base price is set at Rs 16 net.", options: { bullet: true, breakLine: true } },
    { text: "Opening: many listed chargers were faulted or unavailable. Reliability, not price, is the only evidence-backed edge.", options: { bullet: true } },
  ], { x: 6.7, y: 1.85, w: 2.8, h: 3.2, fontFace: BODY, fontSize: 11, color: INK, margin: 0, paraSpaceAfter: 8, isTextBox: true, valign: "top" });
  source(s, "Sources: Statiq public station pages (observed 23 Sep 2026); That's My EV (Aug 2026); Jio-bp; NewsMeter (6 Sep 2026). Small sample: 3 private price points per city.");
}

// ---------------- Slide 4: Station economics ----------------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  title(s, "A single 60 kW charger beats bigger hubs, but it still loses money in its first year",
        "Base case, NPV by configuration (Rs lakh), plus the year-1 economics of the lean station");
  const labels = ["A: 1x60 kW", "B: 2x60 kW", "C: 2x120 kW"];
  s.addChart(pres.charts.BAR, [
    { name: "Delhi", labels, values: cfg.filter(r => r.city === "Delhi").map(r => r.npv_lakh) },
    { name: "Hyderabad", labels, values: cfg.filter(r => r.city === "Hyderabad").map(r => r.npv_lakh) },
  ], { x: 0.5, y: 1.45, w: 4.6, h: 3.6, barDir: "col", barGrouping: "clustered", chartColors: [DELHI, HYD],
       showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", dataLabelFontSize: 9, dataLabelColor: INK,
       showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: MUTED,
       showTitle: true, title: "NPV, Rs lakh (more chargers = more idle capital)", titleFontSize: 11, titleColor: INK,
       catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valGridLine: { color: "E3E7E8", size: 0.5 }, catGridLine: { style: "none" } });
  const d = S("Delhi", "base"), h = S("Hyderabad", "base");
  const hdr = { bold: true, color: "FFFFFF", fill: { color: DARK }, fontFace: BODY, fontSize: 10 };
  const c = (v, b) => ({ text: v, options: { fontFace: BODY, fontSize: 10, color: INK, bold: !!b } });
  s.addTable([
    [{ text: "Lean station (A), year 1", options: hdr }, { text: "Delhi", options: hdr }, { text: "Hyderabad", options: hdr }],
    [c("Setup cost (CAPEX)"), c(`Rs ${f1(d.capex_lakh)} L`), c(`Rs ${f1(h.capex_lakh)} L`)],
    [c("  of which grid connection"), c("Rs 14.8 L"), c("Rs 14.8 L")],
    [c("Utilisation, yr 1 -> yr 5"), c(`${f1(d.yr1_utilisation_pct)}% -> ${f1(d.yr5_utilisation_pct)}%`), c(`${f1(h.yr1_utilisation_pct)}% -> ${f1(h.yr5_utilisation_pct)}%`)],
    [c("Cars per day, yr 1"), c(f1(d.yr1_sessions_day)), c(f1(h.yr1_sessions_day))],
    [c("Revenue, yr 1"), c(`Rs ${f1(d.yr1_revenue_lakh)} L`), c(`Rs ${f1(h.yr1_revenue_lakh)} L`)],
    [c("EBITDA, yr 1", true), c(`Rs ${f1(d.yr1_ebitda_lakh)} L`, true), c(`Rs ${f1(h.yr1_ebitda_lakh)} L`, true)],
    [c("EBITDA, yr 5 (margin)"), c(`Rs ${f1(d.yr5_ebitda_lakh)} L (${f0(d.yr5_ebitda_margin_pct)}%)`), c(`Rs ${f1(h.yr5_ebitda_lakh)} L (${f0(h.yr5_ebitda_margin_pct)}%)`)],
    [c("Contribution per kWh, yr 1"), c("Rs 9.89"), c("Rs 7.13")],
  ], { x: 5.4, y: 1.45, w: 4.1, colW: [1.9, 1.1, 1.1], rowH: 0.32, border: { type: "solid", color: "E3E7E8", pt: 0.5 } });
  s.addText("Each unit earns ~Rs 7-10 after electricity and host share, but fixed costs (staff, maintenance, software) of ~Rs 4 lakh a year need 5-8 cars a day just to cover EBITDA.",
    { x: 5.4, y: 4.6, w: 4.1, h: 0.55, fontFace: BODY, fontSize: 9, color: MUTED, italic: true, margin: 0, isTextBox: true, valign: "top" });
  source(s, "CAPEX: MHI PM E-DRIVE benchmark costs (Sep 2025), Cars24 (Jun 2026), RIOD listing. L = lakh. 1 L = Rs 1,00,000.");
}

// ---------------- Slide 5: Break-even ----------------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  const d = S("Delhi", "base"), h = S("Hyderabad", "base");
  title(s, `To break even the station must be busy ${f0(d.breakeven_npv_utilisation_pct)}-${f0(h.breakeven_npv_utilisation_pct)}% of the time, 3-4x the Indian average`,
        "NPV (Rs lakh) against average utilisation over 10 years, lean station, base case");
  const pts = curve.filter(r => r.utilisation_pct <= 36);
  const xs = [...new Set(pts.map(r => r.utilisation_pct))].map(v => `${v}%`);
  s.addChart(pres.charts.LINE, [
    { name: "Delhi", labels: xs, values: pts.filter(r => r.city === "Delhi").map(r => r.npv_lakh) },
    { name: "Hyderabad", labels: xs, values: pts.filter(r => r.city === "Hyderabad").map(r => r.npv_lakh) },
  ], { x: 0.5, y: 1.45, w: 5.6, h: 3.6, chartColors: [DELHI, HYD], lineSize: 2, lineDataSymbol: "none",
       showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: MUTED,
       showTitle: true, title: "NPV (Rs lakh) vs utilisation; the national average is 8%", titleFontSize: 11, titleColor: INK,
       catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 8,
       valGridLine: { color: "E3E7E8", size: 0.5 }, catGridLine: { style: "none" } });
  stat(s, 6.4, 1.45, 3.1, `${f1(d.breakeven_npv_sessions_day)} / ${f1(h.breakeven_npv_sessions_day)}`, "Cars a day needed every year for NPV = 0, Delhi / Hyderabad (20 kWh each)");
  stat(s, 6.4, 2.65, 3.1, "8.4%", "Average utilisation of India's public DC chargers (14,008 chargers, Apr-Jul 2025)", AMBER);
  stat(s, 6.4, 3.85, 3.1, `${f1(d.yr1_sessions_day)} -> ${f1(cashD[4].sessions_per_day)}`, "Cars a day we expect in Delhi, year 1 -> year 5 (base case)");
  source(s, "Break-even found by solving the full 10-year model for NPV = 0 (flat demand). Utilisation = share of hours a charger is in use. Benchmark: ExperiencesWithEVs Charger Utilization Report, Jul 2025.");
}

// ---------------- Slide 6: Scenarios & sensitivity ----------------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  title(s, "Only the aggressive case beats the 14.1% cost of capital; staffing, demand and grid cost drive value",
        "Left: NPV by scenario (Rs lakh). Right: base-case NPV (Rs lakh) when one input moves");
  const scs = ["conservative", "base", "aggressive"];
  s.addChart(pres.charts.BAR, [
    { name: "Delhi", labels: ["Conservative", "Base", "Aggressive"], values: scs.map(x => S("Delhi", x).npv_lakh) },
    { name: "Hyderabad", labels: ["Conservative", "Base", "Aggressive"], values: scs.map(x => S("Hyderabad", x).npv_lakh) },
  ], { x: 0.5, y: 1.45, w: 4.0, h: 3.0, barDir: "col", barGrouping: "clustered", chartColors: [DELHI, HYD],
       showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", dataLabelFontSize: 9, dataLabelColor: INK,
       showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: MUTED,
       catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, valGridLine: { color: "E3E7E8", size: 0.5 }, catGridLine: { style: "none" } });
  const a = S("Delhi", "aggressive"), b = S("Hyderabad", "aggressive");
  s.addText(`Aggressive: Delhi IRR ${f1(a.irr_pct)}%, payback ${f1(a.payback_years)} yrs; Hyderabad IRR ${f1(b.irr_pct)}%, payback ${f1(b.payback_years)} yrs. Conservative and base never recover their cost.`,
    { x: 0.5, y: 4.5, w: 4.0, h: 0.65, fontFace: BODY, fontSize: 10, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
  const sens = readCsv("outputs/tables/sensitivity_tornado.csv");
  const top = ["Staff 2 FTE / 0 FTE", "Demand (capture) -30% / +30%", "Grid work: new connection / host's spare capacity", "CAPEX +20% / -20%", "Charging price -10% / +10%", "Discount rate 16% / 12%"];
  const nice = { "Staff 2 FTE / 0 FTE": "Staff: 2 people / none", "Demand (capture) -30% / +30%": "Demand -30% / +30%", "Grid work: new connection / host's spare capacity": "Grid: new / host's spare", "CAPEX +20% / -20%": "CAPEX +20% / -20%", "Charging price -10% / +10%": "Price -10% / +10%", "Discount rate 16% / 12%": "Discount rate 16% / 12%" };
  const hdr2 = { bold: true, color: "FFFFFF", fill: { color: DARK }, fontFace: BODY, fontSize: 9 };
  const cc = v => ({ text: v, options: { fontFace: BODY, fontSize: 9, color: INK } });
  const sw = (city, name) => { const r = sens.find(x => x.city === city && x.input === name); return `${f0(r.npv_bad_lakh)} to ${f0(r.npv_good_lakh)}`; };
  const trows = [[{ text: "Input (worse / better)", options: hdr2 }, { text: "Delhi NPV range", options: hdr2 }, { text: "Hyderabad NPV range", options: hdr2 }]];
  top.forEach(n => trows.push([cc(nice[n]), cc(sw("Delhi", n)), cc(sw("Hyderabad", n))]));
  s.addTable(trows, { x: 4.8, y: 1.45, w: 4.7, colW: [2.1, 1.3, 1.3], rowH: 0.27, border: { type: "solid", color: "E3E7E8", pt: 0.5 } });
  s.addText([
    { text: "Staff (0-2 people) is the biggest swing: a remote-monitored station is essential.", options: { bullet: true, breakLine: true } },
    { text: "A host with spare grid capacity removes Rs 14.8 lakh of CAPEX.", options: { bullet: true, breakLine: true } },
    { text: "Discount rate barely matters: the problem is volume, not financing.", options: { bullet: true } },
  ], { x: 4.8, y: 3.55, w: 4.7, h: 1.5, fontFace: BODY, fontSize: 11, color: INK, margin: 0, paraSpaceAfter: 6, isTextBox: true, valign: "top" });
  source(s, "Scenario inputs change demand capture, ramp-up, growth, price, electricity, host share, staff, maintenance and CAPEX together. Full table: outputs/tables/scenarios.csv.");
}

// ---------------- Slide 7: Recommendation ----------------
{
  const s = pres.addSlide();
  s.background = { color: DARK };
  s.addText("Recommendation: Delhi only as a conditional pilot; do not invest in Hyderabad now",
    { x: 0.5, y: 0.3, w: 9, h: 0.75, fontFace: HEAD, fontSize: 22, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, valign: "top" });
  const hdr = { bold: true, color: DARK, fill: { color: "9FD3D6" }, fontFace: BODY, fontSize: 10 };
  const c = (v, b) => ({ text: String(v), options: { fontFace: BODY, fontSize: 10, color: "FFFFFF", bold: !!b, fill: { color: "175059" } } });
  const steps = ["Base case", "+ host site with spare grid capacity", "+ unmanned (remote-monitored)", "+ host share cut to 10%"];
  const rows = [[{ text: "Lever (cumulative)", options: hdr }, { text: "Delhi NPV", options: hdr }, { text: "Hyderabad NPV", options: hdr }]];
  steps.forEach(st => rows.push([c(st), c(`Rs ${f1(L("Delhi", st).npv_lakh)} L`, st === steps[3]), c(`Rs ${f1(L("Hyderabad", st).npv_lakh)} L`, st === steps[3])]));
  s.addTable(rows, { x: 0.5, y: 1.2, w: 5.0, colW: [2.8, 1.1, 1.1], rowH: 0.34, border: { type: "solid", color: DARK, pt: 1 } });
  s.addText([
    { text: "Delhi: ", options: { bold: true, color: "F5C27A" } },
    { text: `proceed only with one 60 kW charger at a host site with spare grid capacity, unmanned, host share of 10% or less (NPV Rs ${f1(L("Delhi", steps[3]).npv_lakh)} L, IRR ${f1(L("Delhi", steps[3]).irr_pct)}%). It still fails the conservative case, so treat it as a pilot.`, options: { color: "FFFFFF", breakLine: true } },
    { text: "Hyderabad: ", options: { bold: true, color: "F5C27A" } },
    { text: `unattractive even with all levers (NPV Rs ${f1(L("Hyderabad", steps[3]).npv_lakh)} L). Revisit after the Rs 13 TGREDCO network opens and the road-tax waiver decision (Dec 2026).`, options: { color: "FFFFFF" } },
  ], { x: 0.5, y: 3.05, w: 5.0, h: 2.0, fontFace: BODY, fontSize: 11, margin: 0, paraSpaceAfter: 6, isTextBox: true, valign: "top" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.8, y: 1.2, w: 3.7, h: 3.85, fill: { color: "175059" }, line: { color: "175059" }, rectRadius: 0.08 });
  s.addText("Key risks", { x: 6.0, y: 1.3, w: 3.3, h: 0.3, fontFace: HEAD, fontSize: 13, bold: true, color: "F5C27A", margin: 0, isTextBox: true });
  s.addText([
    { text: "Fleets charge at their own depots (post-BluSmart)", options: { bullet: true, breakLine: true } },
    { text: "Charger supply outpaces cars (Delhi 16k points)", options: { bullet: true, breakLine: true } },
    { text: "Price war with Rs 13 government network", options: { bullet: true } },
  ], { x: 6.0, y: 1.65, w: 3.3, h: 1.2, fontFace: BODY, fontSize: 10, color: "FFFFFF", margin: 0, paraSpaceAfter: 3, isTextBox: true, valign: "top" });
  s.addText("Due diligence before any money", { x: 6.0, y: 2.95, w: 3.3, h: 0.3, fontFace: HEAD, fontSize: 13, bold: true, color: "F5C27A", margin: 0, isTextBox: true });
  s.addText([
    { text: "Host term sheet: grid capacity, share, tenure", options: { bullet: true, breakLine: true } },
    { text: "Cab-fleet offtake letter (sessions/day)", options: { bullet: true, breakLine: true } },
    { text: "DISCOM confirmation of surcharges on EV tariff", options: { bullet: true, breakLine: true } },
    { text: "Real utilisation data from 3-5 nearby chargers", options: { bullet: true } },
  ], { x: 6.0, y: 3.3, w: 3.3, h: 1.65, fontFace: BODY, fontSize: 10, color: "FFFFFF", margin: 0, paraSpaceAfter: 3, isTextBox: true, valign: "top" });
  source(s, "");
}

// ---------------- Appendix: assumptions ----------------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  title(s, "Appendix: key base-case assumptions and where they come from", null);
  const hdr = { bold: true, color: "FFFFFF", fill: { color: DARK }, fontFace: BODY, fontSize: 9 };
  const c = v => ({ text: v, options: { fontFace: BODY, fontSize: 9, color: INK } });
  const rows = [
    [{ text: "Assumption", options: hdr }, { text: "Delhi", options: hdr }, { text: "Hyderabad", options: hdr }, { text: "Label", options: hdr }, { text: "Source / rationale", options: hdr }],
    ["Public demand (SAM)", "41,641 kWh/day", "38,471 kWh/day", "Derived", "Phase 4 market sizing"],
    ["Existing fast stations", "399", "373", "Fact/derived", "PIB Lok Sabha reply, Dec 2025"],
    ["Capture vs fair share", "1.25x", "1.25x", "Assumption", "Reliable, well-sited station"],
    ["Price, net of GST", "Rs 18.64", "Rs 16.00", "Derived/assumption", "Rival listings; Rs 13 govt network"],
    ["Electricity", "Rs 5.50/kWh", "Rs 6.00/kWh", "Fact + est.", "DERC Rs 4.50 + surcharges; TGERC LT-IX"],
    ["Setup cost (lean)", "Rs 31.2 L", "Rs 31.2 L", "Fact/derived", "MHI PM E-DRIVE benchmarks"],
    ["Host revenue share", "15%", "15%", "Estimate", "Bolt.Earth: 10-20%"],
    ["Staff", "1 FTE @ Rs 20k/mo", "1 FTE @ Rs 20k/mo", "Assumption", "Above Delhi minimum wage"],
    ["Demand growth per station", "7%/yr", "7%/yr", "Assumption", "EVs double, but so do chargers"],
    ["Discount rate", "14.1%", "14.1%", "Fact + assump.", "7.02% G-sec + 1.0 x 7.08% ERP"],
    ["Tax", "25.17%", "25.17%", "Fact", "Sec 115BAA"],
  ].map((r, i) => i === 0 ? r : r.map(c));
  s.addTable(rows, { x: 0.5, y: 1.1, w: 9, colW: [2.0, 1.4, 1.4, 1.3, 2.9], rowH: 0.32, border: { type: "solid", color: "E3E7E8", pt: 0.5 } });
  source(s, "Full register of 40 sourced numbers: docs/source_register.md. All assumptions: data/processed/assumptions.csv.");
}

pres.writeFile({ fileName: path.join(root, "presentation/ev_charging_strategy_deck.pptx") }).then(() => console.log("deck saved"));
