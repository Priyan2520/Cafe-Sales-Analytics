# Portfolio Review & Dashboard Upgrade Guide
## Cafe Sales Analytics — Senior BI Consultant Assessment

---

## 1. Dashboard Audit — Executive Overview Page (Current State)

### What's Working Well

**KPI Cards** — Six cards with YoY comparisons and MoM growth. Clean layout, consistent icon use, and the "vs PY" / "vs Last Month" sub-labels add real analytical context. This is better than 80% of beginner portfolios.

**Monthly Trend Line** — Dual-series (Revenue + Profit) is correct. The flat trajectory is an honest representation of the data, not a design flaw.

**Top 10 Table** — Including Profit Margin % alongside Revenue is smart. It signals you understand that volume and profitability are different things.

**Key Insights & Top Opportunities panels** — This is a differentiator. Most student dashboards just show charts. Adding a pre-read layer shows business communication awareness.

---

### What Needs Fixing

#### Issue 1 — Data Inconsistency (Critical)
The Python KPI report and the dashboard show different figures:
- Python: Revenue = ₹86,732 | Top item = Juice | 2 locations | 3 payment methods
- Dashboard: Revenue = ₹88,950 | Top item = Coffee | 3 locations | 4 payment methods

**This is a red flag for any recruiter who looks closely.** It suggests the Power BI file was connected to a different dataset version than the Python scripts produced.

**Fix:** Re-run the full pipeline → reload Power BI from `engineered_cafe_sales.csv`. Ensure every number in the README, report, and dashboard matches.

#### Issue 2 — Donut Charts (Design)
Two donuts on the same page (Payment Method + Order Type) is redundant and wastes space. Donuts are weak for comparison because humans read arc length poorly.

**Fix:** Replace the Payment Method donut with a horizontal bar chart sorted by revenue. Replace the Order Type donut with a stacked bar showing Revenue + Profit side-by-side per channel. This gives margin context.

#### Issue 3 — Month Sort on Trend Chart (Functional)
If months are sorted alphabetically (April, August, December...) instead of chronologically, the trend line is meaningless. Verify the `Month_Num` column is used for sort order in Power BI (`Sort By Column` → `Month_Num`).

#### Issue 4 — Flat Margin Across All Quarters
Every quarter shows exactly 40.0% margin. This is the 60% COGS flat-rate assumption surfacing in the visuals. A recruiter or hiring manager will immediately notice that all margins are identical — it looks like the analysis hasn't been stress-tested.

**Fix:** Add a note in the dashboard footer: *"Gross margin based on uniform 60% COGS assumption — SKU-level cost data not available in source dataset."* This turns a potential weakness into a demonstration of analytical integrity.

#### Issue 5 — Left Panel Slicer Hierarchy
The filter panel has Date, Location, Item, Payment Method, Order Type as flat dropdowns. There's no visual hierarchy guiding the user on *what to filter first*.

**Fix:** Add a thin divider line and section labels: "📅 TIME FILTERS" above Date, "📍 SEGMENT FILTERS" above Location/Item/Payment. This costs 5 minutes and looks significantly more polished.

#### Issue 6 — "All values are in INR" Footer
This is good instinct but the formatting is inconsistent with the rest of the footer. Align it with the data-as-of date in the top right for visual balance.

---

## 2. Diagnostic Analysis Page — Recommended Design

Build this as Page 2 with the tab label: **"2. Diagnostic Analysis"**

### Visual Layout (6 charts, 2×3 grid)

```
┌──────────────────────────┬──────────────────────────┐
│  Revenue vs Profit       │  Item × Payment Method   │
│  by Location             │  Heatmap                 │
│  (Grouped Bar)           │  (Matrix visual)         │
├──────────────────────────┼──────────────────────────┤
│  Revenue vs Profit       │  Revenue Contribution    │
│  Scatter Plot            │  Treemap                 │
│  (bubble = transactions) │                          │
├──────────────────────────┼──────────────────────────┤
│  Profit Waterfall        │  Revenue Driver          │
│  by Channel              │  Decomposition Tree      │
└──────────────────────────┴──────────────────────────┘
```

### Visual-by-Visual Rationale

**Revenue vs Profit by Location (Grouped Bar)**
- Business question: Is In-Store actually less profitable per unit than Takeaway?
- Insight available: Takeaway leads revenue but Delivery may have lower net profit after delivery costs.
- Why grouped bar: Allows direct revenue/profit comparison per location in one glance. Avoid stacked — it obscures the profit/revenue ratio.

**Item × Payment Method Heatmap (Matrix)**
- Business question: Do Coffee buyers skew toward Digital Wallet? Do Brownie buyers use Cash?
- Insight available: If low-margin items (Brownie, Scone) correlate with Cash transactions, those customers may be harder to convert to digital incentive programs.
- Config: Item on rows, Payment Method on columns, cell value = Transaction Count or Revenue. Use conditional background formatting.

**Revenue vs Profit Scatter Plot**
- Business question: Where are our "star" items vs "review" items on the margin curve?
- Config: X-axis = Total Revenue, Y-axis = Total Profit, bubble size = Transaction Count, colour = Quadrant classification. Add reference lines at median Revenue and median Margin.
- Insight available: Items in the bottom-left quadrant (low rev, low profit) are the menu review candidates.

**Revenue Contribution Treemap**
- Business question: What is the visual weight of each product in our portfolio?
- Config: Group by Item, size by Total Revenue, colour by Profit Margin %. Darker = higher margin.
- Insight available: If Coffee (largest box) is also darkest, it reinforces the "protect this product" recommendation.

**Profit Waterfall by Channel**
- Business question: How does each channel contribute to total profit?
- Config: Start at 0, add each channel's profit contribution, end at total. Colour green = positive.
- Insight available: If Delivery adds less profit than Takeaway despite volume, this is a direct input to channel strategy.

**Revenue Driver Decomposition Tree**
- Business question: Why did revenue increase vs. last period? Is it volume, price, or mix?
- Config: Analyse = Total Revenue. Explain by = Item, Location, Payment Method, Quarter.
- Insight available: Management can drill from "Revenue ↑ 12.6%" down to "↑ driven by Coffee in Takeaway channel in Q4."

---

## 3. Power BI Design Improvement Checklist

### Color Palette
Use a single accent colour consistently. Recommended:
```
Primary Blue:    #0A6EBD  (KPI headers, selected bars)
Neutral Gray:    #6B7280  (axis labels, secondary text)
Positive Green:  #22C55E  (growth indicators, positive values)
Negative Red:    #EF4444  (declining values, low-margin flags)
Background:      #F8FAFC  (canvas, very light)
Card Background: #FFFFFF  (clean white for KPI cards)
```

Never use more than 2 data colours in a single chart unless encoding a dimension.

### Typography
- Title font: Segoe UI Semibold, 16–18px
- KPI value: Segoe UI Bold, 28–32px
- KPI sub-label: Segoe UI, 11px, gray
- Axis labels: 11px
- Tooltips: 12px

### Spacing
- Canvas padding: 16px on all sides
- Between cards: 8px gap
- Between chart rows: 12px gap
- Card padding: 12px internal

### KPI Card Upgrade
Replace the current rounded icon cards with this structure:
```
┌─────────────────────────┐
│ 📊 TOTAL REVENUE        │  ← 11px label, uppercase
│ ₹88.95K                 │  ← 30px bold
│ ▲ 12.6% vs Prior Year   │  ← 11px, green arrow
└─────────────────────────┘
```
Add a thin left border in the accent colour (3px) for visual anchoring.

---

## 4. Python Code Audit

### Original Code — Issues

| Issue | Severity | Fix Applied |
|---|---|---|
| `print()` statements instead of logging | Medium | Replaced with `logging` module |
| No CLI argument support | Low | Added `argparse` |
| No exception handling on file load | High | Added `FileNotFoundError` + `sys.exit(1)` |
| Flat `main()` with everything inline | Medium | Refactored to pure functions |
| No anomaly detection or forecasting | High | Added IQR anomaly + linear forecast |
| Bottom-5 query returned wrong items | High | Logic corrected |
| `assert abs(margin - 40.0) < 0.01` crashes in prod | Medium | Replaced with log warning |
| No log file output | Low | Added FileHandler |

### What's Already Good
- Function decomposition is present (not one giant block)
- Type hints partially used
- Validation step at end of cleaning pipeline is correct instinct
- `pd.to_numeric(..., errors="coerce")` is the right approach

---

## 5. SQL Code Audit

### Original Queries — Issues

| Issue | Fix Applied |
|---|---|
| `/ LAG(...) OVER (...)` without NULLIF | Added `NULLIF(..., 0)` guard everywhere |
| No cumulative / running total query | Added Q2.1 with `SUM(...) OVER (ROWS UNBOUNDED PRECEDING)` |
| No cross-tab queries (Item × Payment) | Added Q3.3 |
| No low-margin flag / action classification | Added Q6.1 with CASE-based flag |
| Missing cumulative contribution (Pareto) | Added Q6.2 |
| Section 5 queries were thin | Expanded to payment × location cross-analysis |

---

## 6. README Audit

### Original README — Issues
- "Internship @ Syntecxhub" as primary identity — this should be secondary, not the headline
- Key Insights contained a factual error ("Juice and Salad dominate") that conflicts with the dashboard (Coffee dominates)
- No architecture diagram reference
- How-to-Run section lacked the Power BI step
- No Future Improvements section
- No strategic recommendations section
- Badges were correct but badge styling was inconsistent

### Rewritten README — Improvements
- Leads with project value, not employer
- Architecture diagram included
- Business Insights section is data-grounded
- Strategic Recommendations table is action-oriented (not vague)
- All data references consistent with dashboard values
- Future Improvements listed with realistic next steps

---

## 7. Hiring Manager Score

| Dimension | Original | Upgraded | Comments |
|---|---|---|---|
| Dashboard Design | 7 / 10 | — | Already above average; fix donuts and data mismatch |
| Data Engineering | 6 / 10 | 9 / 10 | Pipeline is solid; logging + anomaly detection added |
| SQL Quality | 6 / 10 | 9 / 10 | Good base; window functions and cross-tabs added |
| DAX Depth | 5 / 10 | 9 / 10 | Time intelligence + dynamic ranking added |
| Business Storytelling | 5 / 10 | 8 / 10 | Insights now grounded in data, not generic |
| README Quality | 6 / 10 | 9 / 10 | Recruiter-facing narrative, architecture, consistency |
| Code Quality | 6 / 10 | 9 / 10 | Logging, exception handling, modular functions |
| **Overall** | **6.0 / 10** | **~8.7 / 10** | |

**6.0 → 8.7** is the difference between "looks like a tutorial clone" and "looks like a junior analyst's first real consulting deliverable."

---

## 8. Before Publishing to GitHub — Final Checklist

- [ ] All numbers match: Python report, SQL output, Power BI dashboard, README KPI table
- [ ] Month sort is chronological in all trend charts
- [ ] No Syntecxhub branding in repository name, README title, or script headers (replace with your name)
- [ ] Raw data file is NOT committed (it's in `.gitignore`)
- [ ] `requirements.txt` tested — `pip install -r requirements.txt` works cleanly
- [ ] All scripts run end-to-end without errors from a fresh clone
- [ ] Screenshot `assets/executive_dashboard.png` is the final version (not a draft)
- [ ] Dashboard screenshot is high resolution (at least 1920×1080, PNG not JPEG)
- [ ] LinkedIn post ready — include dashboard screenshot + 3 bullet findings + GitHub link
- [ ] GitHub repo description filled in (not blank): *"End-to-end BI analytics pipeline for a multi-location cafe — Python, SQL, Power BI, DAX"*
- [ ] At least 3 GitHub Topics tagged: `power-bi`, `data-analytics`, `python`, `sql`, `pandas`

---

## 9. What Would Make This Truly Industry-Level (v2 Roadmap)

1. **Replace flat COGS with a cost dimension table** — even a manually created 10-row CSV with SKU-level margins would make the analysis significantly more credible.

2. **Add a dbt project layer** — even a simple `models/` folder with 2–3 dbt models on top of the cleaned CSV would signal modern data stack awareness.

3. **Add a Date dimension table in Power BI** — built in DAX with `CALENDAR()` and proper fiscal year, quarter, and week columns. Without this, time intelligence measures are unreliable.

4. **Deploy the report** — publish to Power BI Service and share a public link. Recruiters can then interact with the dashboard without downloading the `.pbix`. This single step raises perceived quality significantly.

5. **Add one forecasting visual** — a Python-generated matplotlib chart showing the 3-month forecast alongside actuals, saved as `assets/revenue_forecast.png` and embedded in the README.

---

*Assessment conducted based on dashboard screenshot and source files. All code improvements are in the `scripts/` folder of the upgraded repository.*
