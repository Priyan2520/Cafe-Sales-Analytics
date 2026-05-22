"""
=============================================================
 Syntecxhub Cafe Sales — Step 2: Feature Engineering
 Author : [Your Name] | Intern @ Syntecxhub
 Input  : data/processed/cleaned_cafe_sales.csv
 Output : data/processed/engineered_cafe_sales.csv
=============================================================
"""

import pandas as pd
import numpy as np
import os

INPUT_PATH  = "data/processed/cleaned_cafe_sales.csv"
OUTPUT_PATH = "data/processed/engineered_cafe_sales.csv"

COST_RATE   = 0.60          # 60% cost assumption
MARGIN_RATE = 1 - COST_RATE # 40% gross margin


def load_clean(path: str) -> pd.DataFrame:
    print(f"[1/4] Loading clean file: {path}")
    df = pd.read_csv(path, parse_dates=["Transaction Date"])
    print(f"      Shape: {df.shape}")
    return df


def add_financial_columns(df: pd.DataFrame) -> pd.DataFrame:
    print("[2/4] Adding financial columns: Revenue, Cost, Profit")

    df["Revenue"] = (df["Quantity"] * df["Price Per Unit"]).round(2)
    df["Cost"]    = (df["Revenue"] * COST_RATE).round(2)
    df["Profit"]  = (df["Revenue"] - df["Cost"]).round(2)

    # Sanity check
    actual_margin = df["Profit"].sum() / df["Revenue"].sum() * 100
    print(f"      Total Revenue : ₹{df['Revenue'].sum():>12,.2f}")
    print(f"      Total Cost    : ₹{df['Cost'].sum():>12,.2f}")
    print(f"      Total Profit  : ₹{df['Profit'].sum():>12,.2f}")
    print(f"      Gross Margin  : {actual_margin:.1f}%  (should be 40.0%)")
    assert abs(actual_margin - 40.0) < 0.01, "Margin check failed!"
    return df


def add_time_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    print("[3/4] Extracting time dimensions from Transaction Date")

    dt = df["Transaction Date"]

    df["Day"]         = dt.dt.day
    df["DayOfWeek"]   = dt.dt.day_name()                            # "Monday"…
    df["Week"]        = dt.dt.isocalendar().week.astype(int)        # ISO week number
    df["Month_Num"]   = dt.dt.month                                 # 1–12 (for sorting)
    df["Month"]       = dt.dt.strftime("%B")                        # "January"…
    df["Month_Start"] = dt.dt.to_period("M").dt.to_timestamp()      # 2023-01-01
    df["Quarter"]     = dt.dt.to_period("Q").astype(str)            # "2023Q1"
    df["Year"]        = dt.dt.year

    # Quarter label used in charts: Q1, Q2, Q3, Q4
    df["Quarter_Label"] = "Q" + dt.dt.quarter.astype(str)

    print("      Columns added: Day, DayOfWeek, Week, Month_Num, Month,")
    print("                     Month_Start, Quarter, Year, Quarter_Label")
    return df


def validate_and_save(df: pd.DataFrame, path: str) -> None:
    print("[4/4] Validating and saving engineered dataset")

    required_cols = ["Revenue","Cost","Profit","Day","Month","Quarter","Year"]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
        assert df[col].isna().sum() == 0, f"Nulls in {col}"

    assert (df["Revenue"] == df["Quantity"] * df["Price Per Unit"]).all()
    assert (df["Cost"]    == (df["Revenue"] * COST_RATE).round(2)).all()
    assert (df["Profit"]  == (df["Revenue"] - df["Cost"]).round(2)).all()

    print("  ✅ All engineered columns verified — no nulls, math checks out")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  💾 Saved → {path}")
    print(f"  Final shape: {df.shape}")


def main():
    print("=" * 62)
    print("  SYNTECXHUB — FEATURE ENGINEERING PIPELINE")
    print("=" * 62)
    df = load_clean(INPUT_PATH)
    df = add_financial_columns(df)
    df = add_time_dimensions(df)
    validate_and_save(df, OUTPUT_PATH)
    print("=" * 62)

    # Preview
    print("\nColumn summary:")
    print(df[["Transaction Date","Item","Revenue","Cost","Profit",
              "Month","Quarter","Year"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
