"""
business_kpi_analysis.py
─────────────────────────
Cafe Sales Analytics · Step 3 of 3
Compute all business KPIs, detect revenue anomalies, generate a 3-month
forecast, and produce a structured business report.

Sections
--------
1. Executive KPI Overview
2. Revenue Trends (MoM, QoQ)
3. Product Performance Matrix
4. Channel & Location Analysis
5. Payment Method Behaviour
6. Anomaly Detection (IQR method)
7. Revenue Forecast (Linear Trend)
8. Business Recommendations
9. Report Export

Usage
-----
    python scripts/business_kpi_analysis.py
    python scripts/business_kpi_analysis.py --input path/to/engineered.csv
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_PATH  = Path("data/processed/engineered_cafe_sales.csv")
REPORT_PATH = Path("reports/kpi_summary_report.txt")
LOG_PATH    = Path("reports/kpi_analysis.log")

DIVIDER  = "=" * 64
DIVIDER2 = "-" * 64
N_TOP    = 5      # Top/bottom N for product rankings
FORECAST_MONTHS = 3


# ── Logging ───────────────────────────────────────────────────────────────────

def configure_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_PATH, mode="w"),
        ],
    )
    return logging.getLogger("kpi_analysis")


log = configure_logging()


# ── Data loading ──────────────────────────────────────────────────────────────

def load_engineered(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Engineered dataset not found at '{path}'.\n"
            "Run feature_engineering_pipeline.py first."
        )
    df = pd.read_csv(path, parse_dates=["Transaction Date", "Month_Start"])
    log.info("Loaded engineered dataset: %d rows × %d columns", *df.shape)
    return df


# ── Section 1: Executive KPI Overview ────────────────────────────────────────

def compute_executive_kpis(df: pd.DataFrame) -> dict:
    """Top-level business metrics. These are the numbers on the executive dashboard."""
    revenue     = df["Revenue"].sum()
    profit      = df["Profit"].sum()
    transactions = len(df)

    kpis = {
        "Total Revenue (₹)":           revenue,
        "Total Cost (₹)":              df["Cost"].sum(),
        "Total Profit (₹)":            profit,
        "Gross Margin (%)":             profit / revenue * 100,
        "Total Transactions":          transactions,
        "Avg Transaction Value (₹)":   df["Total Spent"].mean(),
        "Avg Revenue per Transaction": revenue / transactions,
        "Avg Quantity per Transaction": df["Quantity"].mean(),
    }
    return kpis


# ── Section 2: Revenue Trends ─────────────────────────────────────────────────

def compute_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly Revenue, Profit, MoM Growth %, and running total."""
    monthly = (
        df.groupby("Month_Start")
        .agg(
            Revenue    = ("Revenue", "sum"),
            Profit     = ("Profit",  "sum"),
            Transactions = ("Revenue", "count"),
        )
        .sort_index()
        .reset_index()
    )
    monthly["Margin_Pct"]      = (monthly["Profit"] / monthly["Revenue"] * 100).round(2)
    monthly["Prev_Revenue"]    = monthly["Revenue"].shift(1)
    monthly["MoM_Growth_Pct"]  = (
        (monthly["Revenue"] - monthly["Prev_Revenue"])
        / monthly["Prev_Revenue"] * 100
    ).round(2)
    monthly["Running_Total"]   = monthly["Revenue"].cumsum().round(2)
    monthly["Month_Label"]     = monthly["Month_Start"].dt.strftime("%b %Y")
    return monthly[["Month_Label", "Revenue", "Profit", "Margin_Pct",
                     "Transactions", "MoM_Growth_Pct", "Running_Total"]]


def compute_quarterly_trends(df: pd.DataFrame) -> pd.DataFrame:
    q = (
        df.groupby("Quarter_Label")
        .agg(
            Revenue      = ("Revenue", "sum"),
            Profit       = ("Profit",  "sum"),
            Transactions = ("Revenue", "count"),
        )
        .reset_index()
        .sort_values("Quarter_Label")
    )
    q["Margin_Pct"]     = (q["Profit"] / q["Revenue"] * 100).round(1)
    q["QoQ_Growth_Pct"] = (
        (q["Revenue"] - q["Revenue"].shift(1)) / q["Revenue"].shift(1) * 100
    ).round(2)
    return q


# ── Section 3: Product Performance Matrix ────────────────────────────────────

def compute_product_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Per-item aggregation with revenue rank, margin, and revenue share.

    The quadrant logic (high/low revenue × high/low margin) is used to
    classify each product for the Power BI scatter matrix.
    """
    product = (
        df.groupby("Item")
        .agg(
            Total_Revenue  = ("Revenue",        "sum"),
            Total_Profit   = ("Profit",         "sum"),
            Transactions   = ("Revenue",        "count"),
            Avg_Price      = ("Price Per Unit", "mean"),
            Avg_Qty        = ("Quantity",       "mean"),
        )
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )

    total_rev = product["Total_Revenue"].sum()
    product["Revenue_Share_Pct"] = (product["Total_Revenue"] / total_rev * 100).round(2)
    product["Profit_Margin_Pct"] = (product["Total_Profit"] / product["Total_Revenue"] * 100).round(2)
    product["Revenue_Rank"]      = product["Total_Revenue"].rank(ascending=False, method="min").astype(int)

    # Quadrant classification for scatter analysis
    rev_median = product["Total_Revenue"].median()
    mgn_median = product["Profit_Margin_Pct"].median()
    product["Quadrant"] = np.where(
        (product["Total_Revenue"] >= rev_median) & (product["Profit_Margin_Pct"] >= mgn_median),
        "Star — High Revenue, High Margin",
        np.where(
            (product["Total_Revenue"] >= rev_median) & (product["Profit_Margin_Pct"] < mgn_median),
            "Volume Driver — High Revenue, Low Margin",
            np.where(
                (product["Total_Revenue"] < rev_median) & (product["Profit_Margin_Pct"] >= mgn_median),
                "Niche — Low Revenue, High Margin",
                "Review — Low Revenue, Low Margin",
            ),
        ),
    )
    return product


# ── Section 4: Channel & Location Analysis ───────────────────────────────────

def compute_channel_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue and profit by order channel (Location + Order Type if available)."""
    channel_col = "Order Type" if "Order Type" in df.columns else "Location"
    channel = (
        df.groupby(channel_col)
        .agg(
            Total_Revenue  = ("Revenue",    "sum"),
            Total_Profit   = ("Profit",     "sum"),
            Transactions   = ("Revenue",    "count"),
            Avg_Bill       = ("Total Spent", "mean"),
        )
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )
    total_rev = channel["Total_Revenue"].sum()
    channel["Revenue_Share_Pct"] = (channel["Total_Revenue"] / total_rev * 100).round(2)
    channel["Profit_Margin_Pct"] = (channel["Total_Profit"] / channel["Total_Revenue"] * 100).round(2)
    return channel


# ── Section 5: Payment Method Behaviour ──────────────────────────────────────

def compute_payment_analysis(df: pd.DataFrame) -> pd.DataFrame:
    pay = (
        df.groupby("Payment Method")
        .agg(
            Total_Revenue  = ("Revenue",    "sum"),
            Transactions   = ("Revenue",    "count"),
            Avg_Bill       = ("Total Spent", "mean"),
        )
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )
    total_rev = pay["Total_Revenue"].sum()
    pay["Revenue_Share_Pct"] = (pay["Total_Revenue"] / total_rev * 100).round(2)
    return pay


# ── Section 6: Anomaly Detection ─────────────────────────────────────────────

def detect_revenue_anomalies(monthly_trends: pd.DataFrame, iqr_multiplier: float = 1.5) -> pd.DataFrame:
    """Flag monthly revenue values that fall outside the IQR fence.

    IQR method: lower fence = Q1 - 1.5×IQR, upper fence = Q3 + 1.5×IQR.
    Anomalous months may indicate data quality issues, unusual promotions,
    operational disruptions, or genuine seasonal demand shifts.
    """
    rev = monthly_trends["Revenue"]
    q1, q3 = rev.quantile(0.25), rev.quantile(0.75)
    iqr = q3 - q1
    lower_fence = q1 - iqr_multiplier * iqr
    upper_fence = q3 + iqr_multiplier * iqr

    anomalies = monthly_trends[
        (monthly_trends["Revenue"] < lower_fence) |
        (monthly_trends["Revenue"] > upper_fence)
    ].copy()
    anomalies["Fence_Lower"] = lower_fence
    anomalies["Fence_Upper"] = upper_fence

    log.info(
        "Anomaly detection: IQR fences [₹%.0f, ₹%.0f] → %d anomalous month(s) found",
        lower_fence, upper_fence, len(anomalies),
    )
    return anomalies


# ── Section 7: Revenue Forecast ───────────────────────────────────────────────

def forecast_revenue(monthly_trends: pd.DataFrame, n_months: int = FORECAST_MONTHS) -> pd.DataFrame:
    """Linear trend extrapolation for short-term revenue forecasting.

    Uses ordinary least squares on a month index. For production use, replace
    with Prophet or SARIMA once sufficient history is available (≥24 months).
    """
    data = monthly_trends[["Month_Label", "Revenue"]].copy()
    data["t"] = np.arange(len(data))

    # Fit linear trend: Revenue = b0 + b1 * t
    coeffs = np.polyfit(data["t"], data["Revenue"], deg=1)
    slope, intercept = coeffs

    # Forecast
    last_t = data["t"].max()
    forecast_rows = []
    for i in range(1, n_months + 1):
        t = last_t + i
        forecast_rev = intercept + slope * t
        forecast_rows.append({
            "Month_Label":    f"Forecast +{i}",
            "Forecast_Revenue": round(forecast_rev, 2),
            "Type": "Forecast",
        })

    forecast_df = pd.DataFrame(forecast_rows)
    log.info(
        "Forecast (linear trend, slope=%.1f/month): %s",
        slope,
        ", ".join(f"₹{r['Forecast_Revenue']:,.0f}" for _, r in forecast_df.iterrows()),
    )
    return forecast_df


# ── Section 8: Business Recommendations ──────────────────────────────────────

def generate_recommendations(
    product_matrix:  pd.DataFrame,
    channel_analysis: pd.DataFrame,
    payment_analysis: pd.DataFrame,
) -> list[str]:
    """Data-driven recommendations derived from the analysis outputs."""
    recs = []

    # Product recommendations
    review_items = product_matrix[product_matrix["Quadrant"] == "Review — Low Revenue, Low Margin"]
    if not review_items.empty:
        items_str = ", ".join(review_items["Item"].tolist())
        recs.append(
            f"PRODUCT | Menu rationalisation: [{items_str}] are low-revenue AND "
            f"low-margin. Consider a price increase (test +15–20%) or removal. "
            f"Monitor basket attach rate before discontinuing."
        )

    star_items = product_matrix[product_matrix["Quadrant"] == "Star — High Revenue, High Margin"]
    if not star_items.empty:
        items_str = ", ".join(star_items["Item"].tolist())
        recs.append(
            f"PRODUCT | Protect star SKUs: [{items_str}] drive both volume and margin. "
            f"Prioritise stock availability, feature in upsell prompts, and anchor combo deals."
        )

    # Channel recommendations
    if len(channel_analysis) > 1:
        weakest = channel_analysis.iloc[-1]
        recs.append(
            f"CHANNEL | '{weakest.iloc[0]}' channel contributes {weakest['Revenue_Share_Pct']:.1f}% "
            f"of revenue. Evaluate net profitability after channel-specific costs (e.g., delivery "
            f"commissions, packaging). A minimum order threshold may improve unit economics."
        )

    # Payment recommendations
    cash_row = payment_analysis[payment_analysis["Payment Method"] == "Cash"]
    if not cash_row.empty and cash_row["Revenue_Share_Pct"].values[0] > 30:
        recs.append(
            f"PAYMENT | Cash represents {cash_row['Revenue_Share_Pct'].values[0]:.1f}% of revenue. "
            f"Cash handling costs 2–4% of transaction value. A targeted Digital Wallet incentive "
            f"(e.g., 5% discount above ₹80) could shift 10–15% of cash volume within 60 days."
        )

    return recs


# ── Report writer ─────────────────────────────────────────────────────────────

def write_report(
    kpis:             dict,
    monthly:          pd.DataFrame,
    quarterly:        pd.DataFrame,
    products:         pd.DataFrame,
    channels:         pd.DataFrame,
    payments:         pd.DataFrame,
    anomalies:        pd.DataFrame,
    forecast:         pd.DataFrame,
    recommendations:  list[str],
    path:             Path,
) -> None:
    lines = []

    def section(title: str) -> None:
        lines.extend(["", DIVIDER, f"  {title}", DIVIDER])

    section("CAFE SALES — BUSINESS KPI REPORT")

    section("SECTION 1 — EXECUTIVE KPI OVERVIEW")
    for k, v in kpis.items():
        if "%" in k:
            lines.append(f"  {k:<40}: {v:>8.2f}%")
        elif "Transaction" in k and "Value" not in k:
            lines.append(f"  {k:<40}: {v:>8,.0f}")
        else:
            lines.append(f"  {k:<40}: ₹{v:>11,.2f}")

    section("SECTION 2 — MONTHLY REVENUE TRENDS")
    lines.append(f"  {'Month':<12} {'Revenue':>10} {'Profit':>10} {'Margin%':>8} {'MoM%':>8} {'Txns':>6}")
    lines.append("  " + DIVIDER2)
    for _, row in monthly.iterrows():
        mom = f"{row['MoM_Growth_Pct']:+.2f}%" if pd.notna(row["MoM_Growth_Pct"]) else "    —"
        lines.append(
            f"  {row['Month_Label']:<12} ₹{row['Revenue']:>9,.2f} ₹{row['Profit']:>9,.2f} "
            f"{row['Margin_Pct']:>7.1f}% {mom:>8} {row['Transactions']:>6}"
        )

    section("SECTION 3 — QUARTERLY PERFORMANCE")
    lines.append(f"  {'Quarter':<10} {'Revenue':>10} {'Profit':>10} {'Margin%':>8} {'QoQ%':>8} {'Txns':>6}")
    lines.append("  " + DIVIDER2)
    for _, row in quarterly.iterrows():
        qoq = f"{row['QoQ_Growth_Pct']:+.2f}%" if pd.notna(row["QoQ_Growth_Pct"]) else "    —"
        lines.append(
            f"  {row['Quarter_Label']:<10} ₹{row['Revenue']:>9,.2f} ₹{row['Profit']:>9,.2f} "
            f"{row['Margin_Pct']:>7.1f}% {qoq:>8} {row['Transactions']:>6}"
        )

    section("SECTION 4 — PRODUCT PERFORMANCE MATRIX")
    cols = ["Item", "Revenue_Rank", "Total_Revenue", "Revenue_Share_Pct", "Profit_Margin_Pct", "Quadrant"]
    lines.append(f"  {'Item':<12} {'Rank':>4} {'Revenue':>10} {'Rev%':>6} {'Margin%':>8}  Quadrant")
    lines.append("  " + DIVIDER2)
    for _, row in products.iterrows():
        lines.append(
            f"  {row['Item']:<12} {row['Revenue_Rank']:>4} ₹{row['Total_Revenue']:>9,.2f} "
            f"{row['Revenue_Share_Pct']:>5.1f}% {row['Profit_Margin_Pct']:>7.1f}%  {row['Quadrant']}"
        )

    section("SECTION 5 — CHANNEL ANALYSIS")
    ch_col = channels.columns[0]
    for _, row in channels.iterrows():
        lines.append(
            f"  {row[ch_col]:<12}  Revenue: ₹{row['Total_Revenue']:>9,.2f}  "
            f"Share: {row['Revenue_Share_Pct']:.1f}%  Margin: {row['Profit_Margin_Pct']:.1f}%  "
            f"Avg Bill: ₹{row['Avg_Bill']:.2f}"
        )

    section("SECTION 6 — PAYMENT METHOD ANALYSIS")
    for _, row in payments.iterrows():
        lines.append(
            f"  {row['Payment Method']:<16}  Revenue: ₹{row['Total_Revenue']:>9,.2f}  "
            f"Share: {row['Revenue_Share_Pct']:.1f}%  Avg Bill: ₹{row['Avg_Bill']:.2f}  "
            f"Txns: {row['Transactions']:,}"
        )

    section("SECTION 7 — ANOMALY DETECTION")
    if anomalies.empty:
        lines.append("  No monthly revenue anomalies detected (IQR method, 1.5× fence).")
    else:
        lines.append("  Anomalous months (outside IQR 1.5× fences):")
        for _, row in anomalies.iterrows():
            lines.append(
                f"  ⚠  {row['Month_Label']}  Revenue: ₹{row['Revenue']:,.2f}  "
                f"[Fence: ₹{row['Fence_Lower']:,.0f} – ₹{row['Fence_Upper']:,.0f}]"
            )

    section("SECTION 8 — REVENUE FORECAST (3-Month Linear Trend)")
    for _, row in forecast.iterrows():
        lines.append(f"  {row['Month_Label']:<16}  Forecast: ₹{row['Forecast_Revenue']:>10,.2f}")
    lines.append("  Note: Linear extrapolation. For accuracy, use Prophet with ≥24 months of data.")

    section("SECTION 9 — BUSINESS RECOMMENDATIONS")
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"\n  [{i}] {rec}")

    lines.extend(["", DIVIDER, "  END OF REPORT", DIVIDER])

    path.parent.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(lines)
    path.write_text(report_text, encoding="utf-8")
    log.info("Report saved → %s", path)
    print(report_text)


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_analysis(input_path: Path, report_path: Path) -> None:
    log.info(DIVIDER)
    log.info("  CAFE SALES — BUSINESS KPI ANALYSIS")
    log.info(DIVIDER)

    df = load_engineered(input_path)

    kpis             = compute_executive_kpis(df)
    monthly          = compute_monthly_trends(df)
    quarterly        = compute_quarterly_trends(df)
    products         = compute_product_matrix(df)
    channels         = compute_channel_analysis(df)
    payments         = compute_payment_analysis(df)
    anomalies        = detect_revenue_anomalies(monthly)
    forecast         = forecast_revenue(monthly, n_months=FORECAST_MONTHS)
    recommendations  = generate_recommendations(products, channels, payments)

    write_report(
        kpis, monthly, quarterly, products,
        channels, payments, anomalies, forecast,
        recommendations, report_path,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cafe Sales — Business KPI Analysis")
    parser.add_argument("--input",  type=Path, default=INPUT_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_analysis(args.input, args.report)
    except (FileNotFoundError, AssertionError) as e:
        log.error("Analysis aborted: %s", e)
        sys.exit(1)
