"""
=============================================================
 Syntecxhub Cafe Sales — Step 1: Data Cleaning Pipeline
 Author : [Your Name] | Intern @ Syntecxhub
 Dataset: Cafe Sales Dirty Data (Kaggle – ahmedmohamed2003)
 Rows   : 10,000 | Columns: 8 (raw) → 8 (cleaned)
=============================================================
"""
import pandas as pd
import numpy as np
import os, sys

RAW_PATH    = "data/raw/dirty_cafe_sales.csv"
OUTPUT_PATH = "data/processed/cleaned_cafe_sales.csv"

VALID_ITEMS    = ["Coffee","Tea","Cake","Cookie","Salad","Sandwich","Smoothie","Juice"]
VALID_PAYMENTS = ["Cash","Credit Card","Digital Wallet"]
VALID_LOCS     = ["In-Store","Takeaway"]
INVALID_TOKENS = ["ERROR","UNKNOWN","N/A","NA","null","none",""]
DIVIDER        = "=" * 62


def load_raw(path):
    print(f"[1/9] Loading raw file: {path}")
    df = pd.read_csv(path, dtype=str)
    print(f"      Shape: {df.shape}")
    return df


def replace_invalid_tokens(df):
    print("[2/9] Replacing invalid tokens (ERROR / UNKNOWN / blanks) → NaN")
    df = df.replace(INVALID_TOKENS, np.nan)
    str_cols = df.select_dtypes(include=["object","string"]).columns
    for col in str_cols:
        df[col] = df[col].str.strip()
    df = df.replace("", np.nan)
    print(f"      Null counts after replacement:\n{df.isnull().sum().to_string()}")
    return df


def convert_numeric_types(df):
    print("[3/9] Converting numeric columns to float64")
    for col in ["Quantity","Price Per Unit","Total Spent"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fix_dates(df):
    print("[4/9] Parsing Transaction Date; dropping unparseable rows")
    before = len(df)
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    bad = df["Transaction Date"].isna().sum()
    print(f"      Bad/missing dates: {bad}")
    df = df.dropna(subset=["Transaction Date"]).reset_index(drop=True)
    print(f"      Rows remaining: {len(df)} (dropped {before - len(df)})")
    return df


def standardise_categoricals(df):
    print("[5/9] Standardising categorical columns")

    # Item
    df["Item"] = df["Item"].str.strip().str.title()
    df.loc[~df["Item"].isin(VALID_ITEMS + [np.nan]), "Item"] = np.nan

    # Payment Method
    df["Payment Method"] = df["Payment Method"].str.strip().str.title()
    df.loc[~df["Payment Method"].isin(VALID_PAYMENTS + [np.nan]), "Payment Method"] = np.nan

    # Location — fix casing variations
    df["Location"] = df["Location"].str.strip().str.title()
    df["Location"] = df["Location"].replace({
        "In-store":"In-Store","In Store":"In-Store","Instore":"In-Store",
        "Takeaway":"Takeaway"
    })
    df.loc[~df["Location"].isin(VALID_LOCS + [np.nan]), "Location"] = np.nan

    print(f"      Item nulls    : {df['Item'].isna().sum()}")
    print(f"      Payment nulls : {df['Payment Method'].isna().sum()}")
    print(f"      Location nulls: {df['Location'].isna().sum()}")
    return df


def autocorrect_total_spent(df):
    print("[6/9] Autocorrecting Total Spent = Qty × Price Per Unit")
    has_both = df["Quantity"].notna() & df["Price Per Unit"].notna()
    expected = df.loc[has_both,"Quantity"] * df.loc[has_both,"Price Per Unit"]
    mismatch = has_both & (abs(df["Total Spent"].fillna(-999) - expected) > 0.01)
    print(f"      Rows corrected: {mismatch.sum()}")
    df.loc[has_both, "Total Spent"] = expected.round(2)
    return df


def impute_missing(df):
    print("[7/9] Imputing remaining missing values")

    # Quantity — mode per Item, fallback global median
    item_qty_mode = (df.groupby("Item")["Quantity"]
                       .agg(lambda x: x.mode().iloc[0] if len(x.mode()) else np.nan))
    mask_q = df["Quantity"].isna()
    df.loc[mask_q, "Quantity"] = df.loc[mask_q,"Item"].map(item_qty_mode)
    global_qty_med = df["Quantity"].median()
    df["Quantity"] = df["Quantity"].fillna(global_qty_med)

    # Price Per Unit — group mean per Item, fallback global median
    item_price_mean = df.groupby("Item")["Price Per Unit"].transform("mean")
    df["Price Per Unit"] = df["Price Per Unit"].fillna(item_price_mean)
    df["Price Per Unit"] = df["Price Per Unit"].fillna(df["Price Per Unit"].median())

    # Recompute Total Spent after filling numeric cols
    df["Total Spent"] = (df["Quantity"] * df["Price Per Unit"]).round(2)

    # Categoricals — mode imputation
    for col in ["Item","Payment Method","Location"]:
        mode_val = df[col].mode()[0]
        filled   = df[col].isna().sum()
        df[col]  = df[col].fillna(mode_val)
        print(f"      {col}: filled {filled} nulls with mode='{mode_val}'")

    return df


def remove_duplicates(df):
    print("[8/9] Removing duplicate rows")
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"      Duplicates removed: {before - len(df)}")
    return df


def validate(df):
    print("[9/9] Running validation checks...")
    errors = []

    null_total = df.isnull().sum().sum()
    if null_total != 0:
        errors.append(f"NULL values remain: {null_total}")

    str_cols = df.select_dtypes(include=["object","string"]).columns
    for col in str_cols:
        bad = df[col].isin(["ERROR","UNKNOWN","N/A",""])
        if bad.sum():
            errors.append(f"Invalid tokens in '{col}': {bad.sum()} rows")

    for col in ["Quantity","Price Per Unit","Total Spent"]:
        if not pd.api.types.is_float_dtype(df[col]):
            errors.append(f"'{col}' is not float64")

    if not pd.api.types.is_datetime64_any_dtype(df["Transaction Date"]):
        errors.append("'Transaction Date' is not datetime64")

    mismatch = abs(df["Total Spent"] - df["Quantity"]*df["Price Per Unit"]) > 0.01
    if mismatch.sum():
        errors.append(f"{mismatch.sum()} rows: Total Spent ≠ Qty × PPU")

    for col, valids in [("Location",VALID_LOCS),
                        ("Payment Method",VALID_PAYMENTS),
                        ("Item",VALID_ITEMS)]:
        bad = ~df[col].isin(valids)
        if bad.sum():
            errors.append(f"{bad.sum()} invalid values in '{col}'")

    if errors:
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)

    print("  ✅ CHECK 1 : Zero null values")
    print("  ✅ CHECK 2 : No invalid tokens")
    print("  ✅ CHECK 3 : Numeric columns are float64")
    print("  ✅ CHECK 4 : Transaction Date is datetime64")
    print("  ✅ CHECK 5 : Total Spent = Quantity × Price Per Unit")
    print("  ✅ CHECK 6 : Categoricals contain only valid values")
    print("\n  🏆 ALL CHECKS PASSED — Dataset is clean.")


def main():
    print(DIVIDER)
    print("  SYNTECXHUB — CAFE SALES DATA CLEANING PIPELINE")
    print(DIVIDER)
    df = load_raw(RAW_PATH)
    df = replace_invalid_tokens(df)
    df = convert_numeric_types(df)
    df = fix_dates(df)
    df = standardise_categoricals(df)
    df = autocorrect_total_spent(df)
    df = impute_missing(df)
    df = remove_duplicates(df)
    validate(df)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n  💾 Saved → {OUTPUT_PATH}")
    print(f"  Final shape: {df.shape}")
    print(DIVIDER)

if __name__ == "__main__":
    main()
