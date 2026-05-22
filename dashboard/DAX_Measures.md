# DAX Measure Library — Cafe Sales Analytics

All measures follow the naming convention: `[Measure Name]` with consistent formatting.
Table references: `'Sales'` (fact table), `'Date'` (date dimension).

---

## 1. Core Financial Measures

### Total Revenue
```dax
Total Revenue =
SUMX('Sales', 'Sales'[Quantity] * 'Sales'[Price Per Unit])
```
> Uses SUMX rather than SUM([Revenue]) to remain correct when the column is filtered
> or the table is recalculated. Always the anchor measure — all ratios derive from this.

---

### Total Cost
```dax
Total Cost =
[Total Revenue] * 0.60
```
> 60% COGS assumption. Replace with a `Costs` dimension table once SKU-level cost
> data is available — this will make margins realistic rather than uniform.

---

### Total Profit
```dax
Total Profit =
[Total Revenue] - [Total Cost]
```

---

### Profit Margin %
```dax
Profit Margin % =
DIVIDE([Total Profit], [Total Revenue], 0)
```
> DIVIDE handles zero-revenue scenarios cleanly; never use `/` directly in DAX
> without a NULLIF-equivalent guard. Format this measure as Percentage (2 decimals).

---

### Average Transaction Value
```dax
Avg Transaction Value =
DIVIDE([Total Revenue], [Total Transactions], 0)
```

---

### Total Transactions
```dax
Total Transactions =
COUNTROWS('Sales')
```

---

## 2. Time Intelligence Measures

> All time intelligence measures require a proper **Date dimension table** connected
> to `'Sales'[Transaction Date]` with `Mark as Date Table` enabled.

---

### MoM Revenue Growth %
```dax
MoM Growth % =
VAR CurrentPeriod   = [Total Revenue]
VAR PreviousPeriod  = CALCULATE(
    [Total Revenue],
    DATEADD('Date'[Date], -1, MONTH)
)
RETURN
    DIVIDE(CurrentPeriod - PreviousPeriod, PreviousPeriod, BLANK())
```
> Returns BLANK() when there is no prior month — avoids misleading 0% in visuals.
> Format as Percentage (1 decimal). Use in KPI card with conditional arrow icon.

---

### YoY Revenue Growth %
```dax
YoY Growth % =
VAR CurrentYear  = [Total Revenue]
VAR PreviousYear = CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR('Date'[Date])
)
RETURN
    DIVIDE(CurrentYear - PreviousYear, PreviousYear, BLANK())
```

---

### Revenue — Prior Year (for comparison visuals)
```dax
Revenue PY =
CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR('Date'[Date])
)
```

---

### Running Total Revenue (Year-to-Date)
```dax
Revenue YTD =
CALCULATE(
    [Total Revenue],
    DATESYTD('Date'[Date])
)
```

---

### Rolling 3-Month Average
```dax
Revenue 3M Rolling Avg =
CALCULATE(
    [Total Revenue],
    DATESINPERIOD('Date'[Date], LASTDATE('Date'[Date]), -3, MONTH)
) / 3
```
> Useful in the trend line chart to smooth monthly variance. Add as a secondary
> line on the Monthly Revenue visual.

---

## 3. Context-Aware Contribution Measures

### Revenue Contribution % (relative to visible total)
```dax
Revenue Contribution % =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALL('Sales'[Item])),
    0
)
```
> The ALL() removes the Item filter context, giving each item's share of the
> **total** revenue regardless of how the visual is filtered. Use in the treemap
> and the Top 10 table.

---

### Profit Contribution %
```dax
Profit Contribution % =
DIVIDE(
    [Total Profit],
    CALCULATE([Total Profit], ALL('Sales'[Item])),
    0
)
```

---

## 4. Dynamic Ranking Measures

### Product Revenue Rank (dense)
```dax
Product Revenue Rank =
IF(
    HASONEVALUE('Sales'[Item]),
    RANKX(
        ALL('Sales'[Item]),
        [Total Revenue],
        ,
        DESC,
        Dense
    )
)
```
> The HASONEVALUE guard prevents incorrect rank values when the measure is
> evaluated at total level. Use in tables and conditional formatting rules.

---

### Top N Filter — Dynamic (connects to a "Top N" slicer parameter)
```dax
Top N Revenue =
CALCULATE(
    [Total Revenue],
    TOPN(
        [Top N Value],          -- from a What-If Parameter slicer
        ALL('Sales'[Item]),
        [Total Revenue],
        DESC
    )
)
```

### Is Top N Item (helper — for conditional formatting)
```dax
Is Top N Item =
[Product Revenue Rank] <= [Top N Value]
```

---

## 5. Dynamic Titles

### Page Title — Date Range Context
```dax
Title Date Range =
"Revenue Analysis · " &
FORMAT(MIN('Date'[Date]), "DD MMM YYYY") &
" – " &
FORMAT(MAX('Date'[Date]), "DD MMM YYYY")
```

### KPI Card Title — Revenue with Period
```dax
Title Revenue KPI =
"Total Revenue" & " (" & FORMAT(MAX('Date'[Date]), "MMM YYYY") & ")"
```

### Dynamic MoM Arrow Label
```dax
MoM Arrow Label =
VAR Growth = [MoM Growth %]
RETURN
    IF(ISBLANK(Growth), "—",
        IF(Growth >= 0,
            "▲ " & FORMAT(Growth, "0.0%") & " vs LM",
            "▼ " & FORMAT(ABS(Growth), "0.0%") & " vs LM"
        )
    )
```
> Use this as the KPI card subtitle to give the MoM direction at a glance without
> relying on Power BI's built-in (limited) KPI visual.

---

## 6. Decomposition & Diagnostic Measures

### Margin Classification (for scatter plot colour coding)
```dax
Margin Classification =
SWITCH(
    TRUE(),
    [Profit Margin %] >= 0.38, "High Margin (≥38%)",
    [Profit Margin %] >= 0.32, "Mid Margin (32–38%)",
    "Low Margin (<32%)"
)
```

### Revenue vs Profit Scatter — Bubble Size
```dax
Scatter Bubble Size =
[Total Transactions]
```

---

## Setup Notes

1. **Date Table:** Create a dedicated `'Date'` table using `CALENDAR()` or `CALENDARAUTO()`. Mark it as a Date Table. Without this, time intelligence functions will not work.
2. **Measure Table:** Store all measures in a dedicated `_Measures` table (empty table, measures only) to keep the field pane clean.
3. **Naming:** Use spaces, not underscores, in measure names for readability in the field pane and tooltip labels.
4. **Format Strings:** Set format strings directly on measures, not in the visual — this ensures consistency across all report pages.
