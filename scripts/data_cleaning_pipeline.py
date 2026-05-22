"""
data_cleaning_pipeline.py
─────────────────────────
Cafe Sales Analytics · Step 1 of 3
Transform the raw Kaggle dirty-cafe CSV into a validated, schema-enforced
clean dataset ready for feature engineering.

Pipeline Steps
--------------
1. Load raw CSV
2. Normalise invalid tokens  → NaN
3. Cast numeric columns      → float64
4. Parse & validate dates    → datetime64, drop unparseable
5. Standardise categoricals  → enforce domain vocabularies
6. Autocorrect Total Spent   → Qty × Price reconciliation
7. Impute remaining nulls    → group-mode / group-mean strategies
8. Remove duplicate rows
9. Final validation          → 6 assertion-based checks

Usage
-----
    python scripts/data_cleaning_pipeline.py
    python scripts/data_cleaning_pipeline.py --raw path/to/custom.csv
"""

import os
import sys
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────

RAW_PATH    = Path("data/raw/dirty_cafe_sales.csv")
OUTPUT_PATH = Path("data/processed/cleaned_cafe_sales.csv")
LOG_PATH    = Path("reports/cleaning_pipeline.log")

VALID_ITEMS    = {"Coffee", "Tea", "Cake", "Cookie", "Salad",
                  "Sandwich", "Smoothie", "Juice", "Muffin", "Brownie", "Scone"}
VALID_PAYMENTS = {"Cash", "Credit Card", "Digital Wallet", "Debit Card"}
VALID_LOCS     = {"In-Store", "Takeaway", "Delivery"}
INVALID_TOKENS = {"ERROR", "UNKNOWN", "N/A", "NA", "null", "none", "NaN", ""}


# ── Logging setup ─────────────────────────────────────────────────────────────

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
    return logging.getLogger("cleaning_pipeline")


log = configure_logging()


# ── Pipeline steps ────────────────────────────────────────────────────────────

def load_raw(path: Path) -> pd.DataFrame:
    """Load raw CSV, keeping all columns as strings for safe initial inspection."""
    log.info("[1/9] Loading raw file: %s", path)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found at '{path}'.\n"
            "Download from: https://www.kaggle.com/datasets/ahmedmohamed2003/"
            "cafe-sales-dirty-data-for-cleaning-training\n"
            "Place the file at: data/raw/dirty_cafe_sales.csv"
        )
    df = pd.read_csv(path, dtype=str)
    log.info("  Loaded: %d rows × %d columns", *df.shape)
    return df


def replace_invalid_tokens(df: pd.DataFrame) -> pd.DataFrame:
    """Replace all known garbage tokens and blank strings with NaN."""
    log.info("[2/9] Normalising invalid tokens → NaN")
    df.replace(list(INVALID_TOKENS), np.nan, inplace=True)
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].str.strip()
    df.replace("", np.nan, inplace=True)
    total_nulls = df.isnull().sum().sum()
    log.info("  Total nulls after normalisation: %d", total_nulls)
    return df


def cast_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Quantity, Price Per Unit, Total Spent to float64."""
    log.info("[3/9] Casting numeric columns → float64")
    numeric_cols = ["Quantity", "Price Per Unit", "Total Spent"]
    for col in numeric_cols:
        before_nulls = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_nulls  = df[col].isna().sum()
        coerced = after_nulls - before_nulls
        if coerced:
            log.warning("  '%s': %d values coerced to NaN (non-numeric)", col, coerced)
    return df


def parse_and_filter_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse Transaction Date; drop rows where date is irrecoverable."""
    log.info("[4/9] Parsing Transaction Date → datetime64; dropping bad rows")
    n_before = len(df)
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    n_bad = df["Transaction Date"].isna().sum()
    df = df.dropna(subset=["Transaction Date"]).reset_index(drop=True)
    log.info("  Dropped %d unparseable date rows → %d remaining", n_bad, len(df))
    assert len(df) == n_before - n_bad
    return df


def standardise_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce domain vocabularies for Item, Payment Method, and Location."""
    log.info("[5/9] Standardising categorical columns")

    alias_map_loc = {
        "In-store": "In-Store", "In Store": "In-Store",
        "Instore": "In-Store",  "INSTORE": "In-Store",
        "Take Away": "Takeaway", "Take-Away": "Takeaway",
    }

    for col, valids, alias in [
        ("Item",           VALID_ITEMS,    {}),
        ("Payment Method", VALID_PAYMENTS, {}),
        ("Location",       VALID_LOCS,     alias_map_loc),
    ]:
        df[col] = df[col].str.strip().str.title()
        if alias:
            df[col] = df[col].replace(alias)
        invalid_mask = ~df[col].isin(valids) & df[col].notna()
        if invalid_mask.sum():
            log.warning("  '%s': %d unrecognised values → NaN", col, invalid_mask.sum())
        df.loc[invalid_mask, col] = np.nan
        log.info("  '%s': %d nulls", col, df[col].isna().sum())

    return df


def reconcile_total_spent(df: pd.DataFrame) -> pd.DataFrame:
    """Overwrite Total Spent with Qty × Price Per Unit wherever both are known.

    This eliminates data entry errors where the three fields are inconsistent.
    Rows where Quantity or Price are missing are left as-is for imputation later.
    """
    log.info("[6/9] Reconciling Total Spent = Quantity × Price Per Unit")
    has_both = df["Quantity"].notna() & df["Price Per Unit"].notna()
    expected = (df.loc[has_both, "Quantity"] * df.loc[has_both, "Price Per Unit"]).round(2)
    mismatch = has_both & (abs(df["Total Spent"].fillna(-9999) - expected) > 0.01)
    log.info("  Corrected %d mismatched rows", mismatch.sum())
    df.loc[has_both, "Total Spent"] = expected
    return df


def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute nulls using group-aware strategies to preserve distributional integrity.

    Strategy:
    - Quantity:       mode per Item → global median fallback
    - Price Per Unit: mean per Item → global median fallback
    - Total Spent:    recomputed from reconciled Qty × Price
    - Categoricals:   mode of the column
    """
    log.info("[7/9] Imputing remaining nulls")

    # Quantity
    item_qty_mode = (
        df.groupby("Item")["Quantity"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan)
    )
    mask_q = df["Quantity"].isna()
    df.loc[mask_q, "Quantity"] = df.loc[mask_q, "Item"].map(item_qty_mode)
    df["Quantity"] = df["Quantity"].fillna(df["Quantity"].median())
    log.info("  Quantity: %d values imputed", mask_q.sum())

    # Price Per Unit
    mask_p = df["Price Per Unit"].isna()
    df["Price Per Unit"] = df["Price Per Unit"].fillna(
        df.groupby("Item")["Price Per Unit"].transform("mean")
    ).fillna(df["Price Per Unit"].median())
    log.info("  Price Per Unit: %d values imputed", mask_p.sum())

    # Recompute Total Spent now that Qty and Price are complete
    df["Total Spent"] = (df["Quantity"] * df["Price Per Unit"]).round(2)

    # Categoricals — simple mode imputation
    for col in ("Item", "Payment Method", "Location"):
        mode_val = df[col].mode()[0]
        n_filled = df[col].isna().sum()
        df[col] = df[col].fillna(mode_val)
        log.info("  '%s': %d nulls filled with mode='%s'", col, n_filled, mode_val)

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows."""
    log.info("[8/9] Removing duplicate rows")
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = n_before - len(df)
    if removed:
        log.warning("  Removed %d duplicate rows", removed)
    else:
        log.info("  No duplicates found")
    return df


def validate_output(df: pd.DataFrame) -> None:
    """Six deterministic checks; raise AssertionError on first failure."""
    log.info("[9/9] Running validation suite")
    errors = []

    # Check 1: Zero nulls
    total_nulls = df.isnull().sum().sum()
    if total_nulls:
        errors.append(f"CHECK 1 FAILED — {total_nulls} null values remain")

    # Check 2: No invalid tokens remain
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        bad = df[col].isin(INVALID_TOKENS - {""})
        if bad.sum():
            errors.append(f"CHECK 2 FAILED — '{col}' has {bad.sum()} invalid tokens")

    # Check 3: Numeric columns are float64
    for col in ("Quantity", "Price Per Unit", "Total Spent"):
        if not pd.api.types.is_float_dtype(df[col]):
            errors.append(f"CHECK 3 FAILED — '{col}' dtype is {df[col].dtype}, expected float64")

    # Check 4: Transaction Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Transaction Date"]):
        errors.append("CHECK 4 FAILED — 'Transaction Date' is not datetime64")

    # Check 5: Total Spent reconciles with Qty × Price
    discrepancy = (df["Total Spent"] - df["Quantity"] * df["Price Per Unit"]).abs()
    bad_rows = (discrepancy > 0.01).sum()
    if bad_rows:
        errors.append(f"CHECK 5 FAILED — {bad_rows} rows: Total Spent ≠ Qty × Price Per Unit")

    # Check 6: Categoricals contain only valid domain values
    for col, valids in (
        ("Location",       VALID_LOCS),
        ("Payment Method", VALID_PAYMENTS),
        ("Item",           VALID_ITEMS),
    ):
        unknown = ~df[col].isin(valids)
        if unknown.sum():
            errors.append(f"CHECK 6 FAILED — '{col}' has {unknown.sum()} out-of-domain values")

    if errors:
        for e in errors:
            log.error("  ✗ %s", e)
        raise AssertionError("Validation failed — see log for details.")

    for i, msg in enumerate([
        "Zero null values",
        "No invalid tokens",
        "Numeric columns are float64",
        "Transaction Date is datetime64",
        "Total Spent = Quantity × Price Per Unit",
        "All categoricals within valid domain",
    ], 1):
        log.info("  ✓ CHECK %d: %s", i, msg)

    log.info("  All validation checks passed.")


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_pipeline(raw_path: Path, output_path: Path) -> pd.DataFrame:
    log.info("=" * 60)
    log.info("  CAFE SALES — DATA CLEANING PIPELINE")
    log.info("=" * 60)

    df = load_raw(raw_path)
    df = replace_invalid_tokens(df)
    df = cast_numeric_columns(df)
    df = parse_and_filter_dates(df)
    df = standardise_categoricals(df)
    df = reconcile_total_spent(df)
    df = impute_missing_values(df)
    df = remove_duplicates(df)
    validate_output(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Saved clean dataset → %s  (%d rows × %d cols)", output_path, *df.shape)
    log.info("=" * 60)

    return df


# ── Entry point ───────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cafe Sales — Data Cleaning Pipeline")
    parser.add_argument("--raw",    type=Path, default=RAW_PATH,    help="Path to raw CSV")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Path for clean CSV output")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_pipeline(args.raw, args.output)
    except (FileNotFoundError, AssertionError) as e:
        log.error("Pipeline aborted: %s", e)
        sys.exit(1)
