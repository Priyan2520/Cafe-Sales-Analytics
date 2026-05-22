"""
feature_engineering_pipeline.py
────────────────────────────────
Cafe Sales Analytics · Step 2 of 3
Extend the clean dataset with financial metrics and time-series dimensions
needed for Power BI, SQL analytics, and downstream modelling.

Engineered Columns
------------------
Financial:   Revenue, Cost, Profit, Profit_Margin_Pct
Time:        Day, DayOfWeek, IsWeekend, Week, Month_Num, Month,
             Month_Start, Quarter, Quarter_Label, Year

Usage
-----
    python scripts/feature_engineering_pipeline.py
    python scripts/feature_engineering_pipeline.py --input path/to/clean.csv
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Configuration ─────────────────────────────────────────────────────────────

INPUT_PATH  = Path("data/processed/cleaned_cafe_sales.csv")
OUTPUT_PATH = Path("data/processed/engineered_cafe_sales.csv")
LOG_PATH    = Path("reports/feature_engineering.log")

# Cost of goods assumption: 60% COGS → 40% gross margin
# Replace with actual cost table if SKU-level cost data becomes available.
COGS_RATE = 0.60


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
    return logging.getLogger("feature_engineering")


log = configure_logging()


# ── Engineering steps ─────────────────────────────────────────────────────────

def load_clean(path: Path) -> pd.DataFrame:
    log.info("[1/4] Loading clean dataset: %s", path)
    if not path.exists():
        raise FileNotFoundError(
            f"Clean dataset not found at '{path}'.\n"
            "Run data_cleaning_pipeline.py first."
        )
    df = pd.read_csv(path, parse_dates=["Transaction Date"])
    log.info("  Loaded: %d rows × %d columns", *df.shape)
    return df


def add_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive Revenue, Cost, Profit, and Profit Margin from transaction fields.

    Note: Revenue is re-derived from Quantity × Price Per Unit (not Total Spent)
    to ensure consistency post-cleaning. The cleaning pipeline already reconciled
    these fields, so values should be identical.
    """
    log.info("[2/4] Engineering financial features")

    df["Revenue"]          = (df["Quantity"] * df["Price Per Unit"]).round(2)
    df["Cost"]             = (df["Revenue"] * COGS_RATE).round(2)
    df["Profit"]           = (df["Revenue"] - df["Cost"]).round(2)
    df["Profit_Margin_Pct"] = ((df["Profit"] / df["Revenue"]) * 100).round(2)

    actual_margin = df["Profit"].sum() / df["Revenue"].sum() * 100
    log.info("  Total Revenue  : ₹%12,.2f", df["Revenue"].sum())
    log.info("  Total Cost     : ₹%12,.2f", df["Cost"].sum())
    log.info("  Total Profit   : ₹%12,.2f", df["Profit"].sum())
    log.info("  Gross Margin   :   %6.2f%%  (expected %.1f%%)", actual_margin, (1 - COGS_RATE) * 100)

    if abs(actual_margin - (1 - COGS_RATE) * 100) > 0.05:
        log.warning("  Margin deviation detected — review COGS_RATE assumption.")

    return df


def add_time_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """Extract structured time dimensions from Transaction Date.

    IsWeekend and DayOfWeek are useful for identifying traffic patterns
    (e.g., whether cafe performance differs on weekends vs weekdays).
    """
    log.info("[3/4] Engineering time dimensions")

    dt = df["Transaction Date"]

    df["Day"]          = dt.dt.day
    df["DayOfWeek"]    = dt.dt.day_name()
    df["IsWeekend"]    = dt.dt.dayofweek.isin([5, 6]).astype(int)   # 1 = Sat/Sun
    df["Week"]         = dt.dt.isocalendar().week.astype(int)
    df["Month_Num"]    = dt.dt.month                                 # for sort order
    df["Month"]        = dt.dt.strftime("%B")                        # "January"
    df["Month_Short"]  = dt.dt.strftime("%b")                        # "Jan"
    df["Month_Start"]  = dt.dt.to_period("M").dt.to_timestamp()
    df["Quarter"]      = dt.dt.to_period("Q").astype(str)            # "2023Q1"
    df["Quarter_Label"] = "Q" + dt.dt.quarter.astype(str)
    df["Year"]         = dt.dt.year
    df["Year_Month"]   = dt.dt.strftime("%Y-%m")                     # for time series joins

    new_cols = [
        "Day", "DayOfWeek", "IsWeekend", "Week", "Month_Num", "Month",
        "Month_Short", "Month_Start", "Quarter", "Quarter_Label", "Year", "Year_Month",
    ]
    log.info("  Added time columns: %s", ", ".join(new_cols))
    return df


def validate_and_save(df: pd.DataFrame, path: Path) -> None:
    """Assert all engineered columns are present, non-null, and mathematically correct."""
    log.info("[4/4] Validating engineered dataset")

    required_financial = ["Revenue", "Cost", "Profit", "Profit_Margin_Pct"]
    required_temporal  = ["Day", "DayOfWeek", "Month", "Quarter", "Year", "Month_Start"]

    for col in required_financial + required_temporal:
        assert col in df.columns, f"Missing engineered column: '{col}'"
        assert df[col].isna().sum() == 0, f"Nulls found in engineered column: '{col}'"

    # Financial consistency
    rev_check = (df["Revenue"] - df["Quantity"] * df["Price Per Unit"]).abs()
    assert (rev_check <= 0.01).all(), "Revenue ≠ Qty × Price Per Unit"

    cost_check = (df["Cost"] - (df["Revenue"] * COGS_RATE)).abs()
    assert (cost_check <= 0.01).all(), "Cost ≠ Revenue × COGS_RATE"

    profit_check = (df["Profit"] - (df["Revenue"] - df["Cost"])).abs()
    assert (profit_check <= 0.01).all(), "Profit ≠ Revenue − Cost"

    log.info("  ✓ All financial columns validated")
    log.info("  ✓ All time dimension columns validated")

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("Saved engineered dataset → %s  (%d rows × %d cols)", path, *df.shape)


# ── Preview ────────────────────────────────────────────────────────────────────

def print_preview(df: pd.DataFrame) -> None:
    preview_cols = [
        "Transaction Date", "Item", "Quantity", "Price Per Unit",
        "Revenue", "Cost", "Profit", "Profit_Margin_Pct",
        "DayOfWeek", "Month", "Quarter_Label", "Year",
    ]
    log.info("\nColumn preview (first 5 rows):")
    print(df[preview_cols].head().to_string(index=False))

    log.info("\nColumn dtypes:")
    print(df[preview_cols].dtypes.to_string())


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_pipeline(input_path: Path, output_path: Path) -> pd.DataFrame:
    log.info("=" * 60)
    log.info("  CAFE SALES — FEATURE ENGINEERING PIPELINE")
    log.info("=" * 60)

    df = load_clean(input_path)
    df = add_financial_features(df)
    df = add_time_dimensions(df)
    validate_and_save(df, output_path)
    print_preview(df)

    log.info("=" * 60)
    return df


# ── Entry point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cafe Sales — Feature Engineering Pipeline")
    parser.add_argument("--input",  type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_pipeline(args.input, args.output)
    except (FileNotFoundError, AssertionError) as e:
        log.error("Pipeline aborted: %s", e)
        sys.exit(1)
