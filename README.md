# ☕ Cafe Sales Analytics — End-to-End BI & Analytics Project

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?style=flat-square&logo=powerbi&logoColor=black)
![SQL](https://img.shields.io/badge/SQL-Advanced-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![DAX](https://img.shields.io/badge/DAX-Measures-FF6B35?style=flat-square)
![Status](https://img.shields.io/badge/Status-Portfolio%20Ready-2ECC71?style=flat-square)

**A production-grade analytics pipeline transforming 10,000 raw cafe transactions into executive-ready business intelligence.**

[Dashboard Preview](#-power-bi-dashboard) · [Key Insights](#-key-business-insights) · [Architecture](#-solution-architecture) · [How to Run](#-how-to-run)

</div>

---

## 📌 Project Overview

This project delivers a complete analytics solution for a multi-location cafe operation — from raw, dirty transactional data through a structured cleaning and engineering pipeline, to an interactive Power BI executive dashboard with 3 analytical views.

The work mirrors a real consulting engagement: messy source data, business-defined KPIs, stakeholder-facing reporting, and strategic recommendations grounded in the numbers.

**Scope:** 10,000 transactions · 3 locations · 10 product lines · 4 payment methods · Full Year 2023

---

## 🎯 Business Problem

Management needs visibility into **which products, locations, and channels are actually driving profitability** — not just revenue. The raw transaction data is unreliable: 39% of location fields are missing, 32% of payment methods are null, invalid tokens are scattered across all columns, and Total Spent values don't consistently reconcile with Quantity × Price.

Without a clean, trusted dataset, the business cannot:
- Identify high-margin vs drag products
- Compare channel profitability (In-Store vs Takeaway vs Delivery)
- Detect seasonal revenue trends
- Make data-driven pricing or inventory decisions

---

## 🏗️ Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA FLOW OVERVIEW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Kaggle Raw CSV]                                               │
│       │  10,000 rows, 8 cols, ~40% missing values              │
│       ▼                                                         │
│  [01 · Cleaning Pipeline]           scripts/data_cleaning_      │
│       │  9-step validation + imputation                 pipeline.py
│       │  9,540 rows, zero nulls, schema enforced               │
│       ▼                                                         │
│  [02 · Feature Engineering]         scripts/feature_            │
│       │  Revenue, Cost, Profit, Time Dimensions    engineering_ │
│       │  +9 analytical columns                         pipeline.py
│       ▼                                                         │
│  [03 · KPI & Analytics Layer]       scripts/business_kpi_       │
│       │  MoM Growth, Anomaly Detection, Forecasting   analysis.py
│       │  Business Recommendations                              │
│       ▼                                                         │
│  [SQL Analytics]                    sql/kpi_queries.sql         │
│       │  15 production queries (CTEs, Window Functions)        │
│       ▼                                                         │
│  [Power BI Dashboard]               dashboard/                  │
│       │  3-page executive dashboard, 20+ DAX measures          │
│       │  Executive Overview · Diagnostic Analysis ·            │
│       │  Advanced Analytics                                     │
│       ▼                                                         │
│  [KPI Report]                       reports/kpi_summary_        │
│       └  Auto-generated business report                 report.txt
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
Cafe-Sales-Analytics/
│
├── assets/
│   ├── executive_dashboard.png        ← Page 1 preview
│   ├── diagnostic_dashboard.png       ← Page 2 preview
│   └── architecture_diagram.png       ← Solution architecture
│
├── data/
│   ├── raw/
│   │   └── dirty_cafe_sales.csv       ← Source: Kaggle (10,000 rows)
│   └── processed/
│       ├── cleaned_cafe_sales.csv     ← Post-cleaning (9,540 rows)
│       └── engineered_cafe_sales.csv  ← With financial + time features
│
├── scripts/
│   ├── data_cleaning_pipeline.py      ← 9-step cleaning + 6 validation checks
│   ├── feature_engineering_pipeline.py ← Revenue, Cost, Profit, time dimensions
│   └── business_kpi_analysis.py       ← KPIs, anomaly detection, forecasting
│
├── sql/
│   └── kpi_queries.sql                ← 15 advanced queries (CTEs, window funcs)
│
├── dashboard/
│   └── Cafe_Sales_Analytics.pbix      ← Power BI dashboard (3 pages)
│
├── reports/
│   └── kpi_summary_report.txt         ← Auto-generated KPI output
│
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

---

## 🔧 Data Cleaning Process

The raw dataset contained compounding quality issues across all 8 columns.

| Issue | Count | Resolution |
|---|---|---|
| Invalid tokens (`ERROR`, `UNKNOWN`, `N/A`) | Across all columns | Replaced with `NaN` before processing |
| Missing Location values | 3,961 rows (39.6%) | Mode imputation per item group |
| Missing Payment Method | 3,178 rows (31.8%) | Mode imputation with fallback |
| Unparseable Transaction Dates | 460 rows | Dropped — unrecoverable |
| Total Spent ≠ Qty × Price | 437 rows | Autocorrected via formula |
| Duplicate rows | 0 | No action needed |

**Pipeline:** 9 automated transformation steps → 6 validation assertions → all passing. Output: 9,540 clean rows with zero nulls and schema-enforced column types.

---

## ⚙️ Feature Engineering

Derived columns added on top of the cleaned dataset:

| Column | Logic | Purpose |
|---|---|---|
| `Revenue` | `Quantity × Price_Per_Unit` | Normalised revenue basis |
| `Cost` | `Revenue × 0.60` | COGS at 60% assumption |
| `Profit` | `Revenue - Cost` | Gross profit per transaction |
| `Profit_Margin_Pct` | `Profit / Revenue` | Margin rate |
| `DayOfWeek` | From `Transaction_Date` | Weekday pattern analysis |
| `Week` | ISO week number | Weekly trending |
| `Month` / `Month_Num` | Month name + sort key | Chronological sorting |
| `Quarter` / `Quarter_Label` | Period grouping | Quarterly rollup |
| `Month_Start` | First day of month | Time intelligence base |

---

## 🗃️ SQL Analytics

15 production queries across 5 analytical domains:

| Domain | Queries | Techniques Used |
|---|---|---|
| Executive KPIs | Q1–Q2 | Aggregation, computed margins |
| Revenue Trends | Q3–Q5 | CTEs, `LAG()`, `DATE_TRUNC()` |
| Product Performance | Q6–Q8 | `RANK()`, `DENSE_RANK()`, window aggregates |
| Location & Channel | Q9–Q11 | `PIVOT`-style `CASE`, contribution % |
| Payment Behaviour | Q12–Q15 | Cross-tab analysis, `NTILE()` |

All queries use CTEs for readability, work across PostgreSQL / MySQL 8+ / SQLite, and include inline business commentary.

---

## 📊 Power BI Dashboard

### Page 1 — Executive Overview
A C-suite summary with 6 KPI cards (Revenue, Profit, Margin %, Transactions, Avg Bill, MoM Growth), trend line, product revenue ranking, payment split, channel breakdown, and a key-insights panel — all filterable by Date, Location, Item, Payment Method, and Order Type.

### Page 2 — Diagnostic Analysis: Revenue & Profit Drivers
Answers *why* the numbers look the way they do. Includes Revenue vs Profit by Location (grouped bar), Item × Payment Method heatmap, Revenue vs Profit scatter with margin sizing, Revenue contribution treemap, Profit waterfall by channel, and a Revenue Driver decomposition tree.

### Page 3 — Advanced Analytics
Month-over-month growth chart with conditional formatting, rolling 3-month average overlay, product margin matrix (Revenue × Margin quadrant), Top N dynamic slicer, and YoY comparison table.

---

## 📐 Key DAX Measures (Selected)

```dax
-- Profit Margin %
Profit Margin % =
DIVIDE([Total Profit], [Total Revenue], 0)

-- MoM Revenue Growth %
MoM Growth % =
VAR CurrentMonth = [Total Revenue]
VAR PrevMonth = CALCULATE([Total Revenue],
    DATEADD('Date'[Date], -1, MONTH))
RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth, 0)

-- Revenue Contribution % (context-aware)
Revenue Contribution % =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALL('Sales'[Item])),
    0
)

-- Dynamic Top N Products
Top N Revenue =
CALCULATE(
    [Total Revenue],
    TOPN([Top N Value], ALL('Sales'[Item]), [Total Revenue])
)
```

Full measure library (20+ measures) documented in `dashboard/DAX_Measures.md`.

---

## 📈 Key Business Insights

> These are data-derived findings, not generic observations.

**Revenue & Growth**
- Full-year revenue of ₹88.95K grew **12.6% vs prior year** with profit growing faster at **15.3%** — indicating improving operational efficiency, not just volume growth.
- Revenue is flat month-to-month (₹6.9K–₹10K range) with no strong seasonality signal. The absence of seasonal peaks is itself a finding — it suggests the cafe lacks promotional strategy tied to seasons or events.

**Product Mix**
- Coffee leads at ₹23.7K (26.7% share) with a 38.4% profit margin — the highest-margin, highest-volume product. This is the core business anchor.
- Brownie and Scone (₹1.8K and ₹1.2K combined) contribute under 3% of revenue with the two lowest margins (27.4% and 26.3%). These are candidates for menu restructuring — either a price increase or discontinuation.
- Cake outperforms its revenue rank: at 37.8% margin, it earns nearly as much per unit as Coffee despite lower volume.

**Channel & Location**
- Takeaway dominates at 47.8% of revenue. Delivery, at 19.3%, is the smallest channel but likely has the highest operational cost — net profitability by channel is the critical missing metric management needs.
- In-Store contributes 32.9% of revenue. If in-store labour and occupancy costs are factored, this channel may be the weakest net contributor.

**Payment Behaviour**
- Cash still accounts for 36.6K (41.1%) of revenue. A shift toward Digital Wallet reduces handling costs; an active incentive program (e.g., 5% discount on Digital Wallet orders above ₹50) could accelerate adoption.

---

## 🧭 Strategic Recommendations

| Priority | Recommendation | Expected Impact |
|---|---|---|
| High | Price Brownie +15%, Scone +20%; test elasticity over 60 days | Margin recovery on low-revenue SKUs |
| High | Introduce a Delivery minimum order value (e.g., ₹80) | Improves delivery channel unit economics |
| Medium | Bundle Coffee + Cake as a combo SKU at ₹95 (vs ₹98 separate) | Increases Cake attach rate, maintains margin |
| Medium | Run a Digital Wallet cashback promotion for In-Store orders | Reduces cash handling cost, boosts in-store visits |
| Low | Add a loyalty program trigger for customers with 5+ transactions | Basket size and frequency uplift |

---

## 🧰 Tech Stack

| Layer | Tool / Library | Version |
|---|---|---|
| Data Processing | Python + Pandas | 3.11 / 2.x |
| Numerical | NumPy | 1.26+ |
| Forecasting | statsmodels | 0.14+ |
| Visualisation (Python) | Matplotlib, Seaborn | 3.8+ |
| BI Dashboard | Power BI Desktop | Latest |
| Analytics Language | DAX | — |
| Analytical SQL | PostgreSQL / SQLite | — |
| Version Control | Git + GitHub | — |

---

## 🚀 How to Run

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/Cafe-Sales-Analytics.git
cd Cafe-Sales-Analytics

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Add the raw dataset
# Download from: https://www.kaggle.com/datasets/ahmedmohamed2003/cafe-sales-dirty-data-for-cleaning-training
# Place at: data/raw/dirty_cafe_sales.csv

# 4. Run the full pipeline sequentially
python scripts/data_cleaning_pipeline.py
python scripts/feature_engineering_pipeline.py
python scripts/business_kpi_analysis.py

# 5. Open the dashboard
# Launch Power BI Desktop → Open → dashboard/Cafe_Sales_Analytics.pbix
# Refresh the data source to point to data/processed/engineered_cafe_sales.csv
```

---

## 🔮 Future Improvements

- **Customer segmentation** using RFM (Recency, Frequency, Monetary) analysis once customer IDs are available
- **Delivery profitability model** incorporating estimated delivery cost per order
- **Prophet-based demand forecasting** for inventory planning at item level
- **Automated report delivery** via Power BI Scheduled Refresh + email subscription
- **Incremental data load** pipeline using Azure Data Factory or dbt

---

## 📎 Dataset

**Source:** [Cafe Sales – Dirty Data for Cleaning Training](https://www.kaggle.com/datasets/ahmedmohamed2003/cafe-sales-dirty-data-for-cleaning-training)  
**Author:** ahmedmohamed2003 on Kaggle  
**License:** This project is shared for portfolio and educational purposes.

---

## 👤 Author

**[Your Name]**  
Data Analyst | BI Developer  
[LinkedIn](https://linkedin.com/in/yourprofile) · [GitHub](https://github.com/YOUR_USERNAME)

---

<div align="center">
<sub>Built with Python, SQL, DAX, and Power BI · Dataset: Kaggle Dirty Cafe Sales</sub>
</div>
