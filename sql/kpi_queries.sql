-- ================================================================
--  Cafe Sales Analytics — Production SQL Query Library
--  Compatibility: PostgreSQL 13+ · MySQL 8+ · SQLite 3.25+
--  Table:         cafe_sales  (from engineered_cafe_sales.csv)
--
--  Column Reference
--  ─────────────────
--  Transaction_ID, Item, Quantity, Price_Per_Unit, Total_Spent,
--  Payment_Method, Location, Transaction_Date,
--  Revenue, Cost, Profit, Profit_Margin_Pct,
--  Day, DayOfWeek, IsWeekend, Week, Month_Num, Month, Month_Short,
--  Month_Start, Quarter, Quarter_Label, Year, Year_Month
-- ================================================================


-- ════════════════════════════════════════════════════════════════
-- SECTION 1 · EXECUTIVE KPI OVERVIEW
-- Business question: What is the full-year financial performance?
-- ════════════════════════════════════════════════════════════════

-- Q1.1  Full-year executive summary
--       This is the source of truth for the dashboard KPI cards.
SELECT
    ROUND(SUM(Revenue),  2)                              AS Total_Revenue,
    ROUND(SUM(Cost),     2)                              AS Total_Cost,
    ROUND(SUM(Profit),   2)                              AS Total_Profit,
    ROUND(SUM(Profit) / NULLIF(SUM(Revenue), 0) * 100, 2) AS Gross_Margin_Pct,
    COUNT(*)                                             AS Total_Transactions,
    ROUND(AVG(Total_Spent), 2)                           AS Avg_Transaction_Value,
    ROUND(AVG(Quantity),    2)                           AS Avg_Items_Per_Txn
FROM cafe_sales;


-- Q1.2  Year-over-year performance (requires 2+ years of data)
--       Produces the YoY Growth % shown on KPI cards.
WITH yearly AS (
    SELECT
        Year,
        ROUND(SUM(Revenue), 2) AS Annual_Revenue,
        ROUND(SUM(Profit),  2) AS Annual_Profit,
        COUNT(*)               AS Transactions
    FROM cafe_sales
    GROUP BY Year
)
SELECT
    Year,
    Annual_Revenue,
    Annual_Profit,
    Transactions,
    LAG(Annual_Revenue) OVER (ORDER BY Year)             AS Prev_Year_Revenue,
    ROUND(
        (Annual_Revenue - LAG(Annual_Revenue) OVER (ORDER BY Year))
        / NULLIF(LAG(Annual_Revenue) OVER (ORDER BY Year), 0) * 100,
    2)                                                   AS YoY_Revenue_Growth_Pct
FROM yearly
ORDER BY Year;


-- ════════════════════════════════════════════════════════════════
-- SECTION 2 · REVENUE TRENDS (MoM · QoQ · Running Total)
-- Business question: Is revenue trending up, flat, or declining?
-- ════════════════════════════════════════════════════════════════

-- Q2.1  Monthly revenue with MoM growth and running total
--       Powers the "Monthly Revenue vs Profit Trend" line chart.
WITH monthly AS (
    SELECT
        Year_Month,
        Month_Short,
        Year,
        ROUND(SUM(Revenue), 2)  AS Monthly_Revenue,
        ROUND(SUM(Profit),  2)  AS Monthly_Profit,
        COUNT(*)                AS Transactions
    FROM cafe_sales
    GROUP BY Year_Month, Month_Short, Year
)
SELECT
    Year_Month,
    Month_Short,
    Monthly_Revenue,
    Monthly_Profit,
    ROUND(Monthly_Profit / NULLIF(Monthly_Revenue, 0) * 100, 2) AS Margin_Pct,
    Transactions,
    LAG(Monthly_Revenue) OVER (ORDER BY Year_Month)       AS Prev_Month_Revenue,
    ROUND(
        (Monthly_Revenue - LAG(Monthly_Revenue) OVER (ORDER BY Year_Month))
        / NULLIF(LAG(Monthly_Revenue) OVER (ORDER BY Year_Month), 0) * 100,
    2)                                                    AS MoM_Growth_Pct,
    ROUND(SUM(Monthly_Revenue) OVER (
        ORDER BY Year_Month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2)                                                 AS Running_Total
FROM monthly
ORDER BY Year_Month;


-- Q2.2  Quarterly rollup with QoQ growth
--       Powers the quarterly trend visual and quarter slicer.
WITH quarterly AS (
    SELECT
        Quarter_Label,
        ROUND(SUM(Revenue), 2) AS Quarterly_Revenue,
        ROUND(SUM(Profit),  2) AS Quarterly_Profit,
        COUNT(*)               AS Transactions
    FROM cafe_sales
    GROUP BY Quarter_Label
)
SELECT
    Quarter_Label,
    Quarterly_Revenue,
    Quarterly_Profit,
    ROUND(Quarterly_Profit / NULLIF(Quarterly_Revenue, 0) * 100, 2) AS Margin_Pct,
    Transactions,
    ROUND(
        (Quarterly_Revenue - LAG(Quarterly_Revenue) OVER (ORDER BY Quarter_Label))
        / NULLIF(LAG(Quarterly_Revenue) OVER (ORDER BY Quarter_Label), 0) * 100,
    2)                                                   AS QoQ_Growth_Pct
FROM quarterly
ORDER BY Quarter_Label;


-- Q2.3  3-Month rolling average revenue
--       Smooths monthly volatility. Used in the Advanced Analytics page.
WITH monthly AS (
    SELECT
        Year_Month,
        ROUND(SUM(Revenue), 2) AS Monthly_Revenue
    FROM cafe_sales
    GROUP BY Year_Month
)
SELECT
    Year_Month,
    Monthly_Revenue,
    ROUND(AVG(Monthly_Revenue) OVER (
        ORDER BY Year_Month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                                AS Rolling_3M_Avg
FROM monthly
ORDER BY Year_Month;


-- ════════════════════════════════════════════════════════════════
-- SECTION 3 · PRODUCT PERFORMANCE
-- Business question: Which items drive revenue vs. margin?
-- ════════════════════════════════════════════════════════════════

-- Q3.1  Full product performance matrix with ranking
--       Source for the "Revenue by Item" bar chart and the Top 10 table.
SELECT
    Item,
    ROUND(SUM(Revenue), 2)                               AS Total_Revenue,
    ROUND(SUM(Profit),  2)                               AS Total_Profit,
    ROUND(SUM(Profit) / NULLIF(SUM(Revenue), 0) * 100, 2) AS Profit_Margin_Pct,
    COUNT(*)                                             AS Transactions,
    ROUND(AVG(Price_Per_Unit), 2)                        AS Avg_Price,
    ROUND(SUM(Revenue) / SUM(SUM(Revenue)) OVER () * 100, 2) AS Revenue_Share_Pct,
    RANK()       OVER (ORDER BY SUM(Revenue) DESC)       AS Revenue_Rank,
    RANK()       OVER (ORDER BY SUM(Profit)  DESC)       AS Profit_Rank,
    DENSE_RANK() OVER (ORDER BY
        SUM(Profit) / NULLIF(SUM(Revenue), 0) DESC)      AS Margin_Rank
FROM cafe_sales
GROUP BY Item
ORDER BY Revenue_Rank;


-- Q3.2  Product performance by location
--       Answers: does Coffee sell better In-Store or Takeaway?
--       Feeds the Item × Location cross-tab in Diagnostic Analysis.
SELECT
    Item,
    Location,
    ROUND(SUM(Revenue), 2)   AS Revenue,
    ROUND(SUM(Profit),  2)   AS Profit,
    COUNT(*)                 AS Transactions,
    ROUND(SUM(Revenue) / SUM(SUM(Revenue)) OVER (PARTITION BY Item) * 100, 2)
                             AS Pct_Of_Item_Revenue
FROM cafe_sales
GROUP BY Item, Location
ORDER BY Item, Revenue DESC;


-- Q3.3  Item × Payment Method cross-tab (for the heatmap)
--       Identifies whether Digital Wallet users buy different items than Cash users.
SELECT
    Item,
    Payment_Method,
    COUNT(*)                 AS Transactions,
    ROUND(SUM(Revenue), 2)   AS Revenue,
    ROUND(AVG(Total_Spent), 2) AS Avg_Bill
FROM cafe_sales
GROUP BY Item, Payment_Method
ORDER BY Item, Revenue DESC;


-- ════════════════════════════════════════════════════════════════
-- SECTION 4 · LOCATION & CHANNEL ANALYSIS
-- Business question: Which channel and location is most profitable?
-- ════════════════════════════════════════════════════════════════

-- Q4.1  Revenue and profitability by location
--       Core metric for location investment decisions.
SELECT
    Location,
    ROUND(SUM(Revenue),  2)                               AS Total_Revenue,
    ROUND(SUM(Profit),   2)                               AS Total_Profit,
    ROUND(SUM(Profit) / NULLIF(SUM(Revenue), 0) * 100, 2) AS Profit_Margin_Pct,
    COUNT(*)                                              AS Transactions,
    ROUND(AVG(Total_Spent), 2)                            AS Avg_Bill,
    ROUND(SUM(Revenue) / SUM(SUM(Revenue)) OVER () * 100, 2) AS Revenue_Share_Pct
FROM cafe_sales
GROUP BY Location
ORDER BY Total_Revenue DESC;


-- Q4.2  Monthly revenue trend by location
--       Identifies whether location performance diverges over time.
SELECT
    Year_Month,
    Location,
    ROUND(SUM(Revenue), 2)  AS Monthly_Revenue,
    COUNT(*)                AS Transactions
FROM cafe_sales
GROUP BY Year_Month, Location
ORDER BY Year_Month, Location;


-- Q4.3  Location × Day-of-week heatmap
--       Used in scheduling and staffing optimisation decisions.
SELECT
    Location,
    DayOfWeek,
    COUNT(*)               AS Transactions,
    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(AVG(Total_Spent), 2) AS Avg_Bill
FROM cafe_sales
GROUP BY Location, DayOfWeek
ORDER BY Location,
    CASE DayOfWeek
        WHEN 'Monday'    THEN 1 WHEN 'Tuesday'   THEN 2
        WHEN 'Wednesday' THEN 3 WHEN 'Thursday'  THEN 4
        WHEN 'Friday'    THEN 5 WHEN 'Saturday'  THEN 6
        WHEN 'Sunday'    THEN 7
    END;


-- ════════════════════════════════════════════════════════════════
-- SECTION 5 · PAYMENT BEHAVIOUR ANALYSIS
-- Business question: Which payment method is most valuable per transaction?
-- ════════════════════════════════════════════════════════════════

-- Q5.1  Payment method summary
--       Basis for Digital Wallet adoption strategy.
SELECT
    Payment_Method,
    COUNT(*)                                              AS Transactions,
    ROUND(SUM(Revenue), 2)                                AS Total_Revenue,
    ROUND(AVG(Total_Spent), 2)                            AS Avg_Bill,
    ROUND(MAX(Total_Spent), 2)                            AS Max_Bill,
    ROUND(SUM(Revenue) / SUM(SUM(Revenue)) OVER () * 100, 2) AS Revenue_Share_Pct,
    NTILE(4) OVER (ORDER BY SUM(Revenue) DESC)            AS Revenue_Quartile
FROM cafe_sales
GROUP BY Payment_Method
ORDER BY Total_Revenue DESC;


-- Q5.2  Payment method vs. location cross-analysis
--       Answers: do delivery customers prefer Digital Wallet over In-Store Cash?
SELECT
    Location,
    Payment_Method,
    COUNT(*)               AS Transactions,
    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(AVG(Total_Spent), 2) AS Avg_Bill,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY Location), 2)
                           AS Pct_Of_Location_Txns
FROM cafe_sales
GROUP BY Location, Payment_Method
ORDER BY Location, Revenue DESC;


-- ════════════════════════════════════════════════════════════════
-- SECTION 6 · LOW-MARGIN & HIGH-RISK ITEM ANALYSIS
-- Business question: Which items are dragging overall profitability?
-- ════════════════════════════════════════════════════════════════

-- Q6.1  Items below average margin — candidates for price review
--       A key input to the menu rationalisation recommendation.
WITH item_margins AS (
    SELECT
        Item,
        ROUND(SUM(Revenue), 2)                               AS Total_Revenue,
        ROUND(SUM(Profit) / NULLIF(SUM(Revenue), 0) * 100, 2) AS Profit_Margin_Pct,
        ROUND(SUM(Revenue) / SUM(SUM(Revenue)) OVER () * 100, 2) AS Revenue_Share_Pct
    FROM cafe_sales
    GROUP BY Item
),
avg_margin AS (
    SELECT AVG(Profit_Margin_Pct) AS Avg_Margin FROM item_margins
)
SELECT
    im.Item,
    im.Total_Revenue,
    im.Profit_Margin_Pct,
    im.Revenue_Share_Pct,
    am.Avg_Margin,
    ROUND(im.Profit_Margin_Pct - am.Avg_Margin, 2) AS Margin_vs_Avg,
    CASE
        WHEN im.Profit_Margin_Pct < am.Avg_Margin AND im.Revenue_Share_Pct < 10
            THEN 'Priority Review — Low Margin, Low Volume'
        WHEN im.Profit_Margin_Pct < am.Avg_Margin
            THEN 'Margin Review — Volume Offset'
        ELSE 'Acceptable'
    END                                             AS Action_Flag
FROM item_margins im
CROSS JOIN avg_margin am
ORDER BY im.Profit_Margin_Pct ASC;


-- Q6.2  Revenue contribution waterfall data
--       Shows how each item adds to the cumulative revenue total.
--       Powers the waterfall chart in Diagnostic Analysis page.
WITH item_rev AS (
    SELECT
        Item,
        ROUND(SUM(Revenue), 2)  AS Revenue,
        RANK() OVER (ORDER BY SUM(Revenue) DESC) AS Rev_Rank
    FROM cafe_sales
    GROUP BY Item
)
SELECT
    Item,
    Revenue,
    Rev_Rank,
    ROUND(SUM(Revenue) OVER (ORDER BY Rev_Rank
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS Cumulative_Revenue,
    ROUND(Revenue / SUM(Revenue) OVER () * 100, 2) AS Revenue_Pct,
    ROUND(SUM(Revenue) OVER (ORDER BY Rev_Rank
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / SUM(Revenue) OVER () * 100, 2)           AS Cumulative_Pct
FROM item_rev
ORDER BY Rev_Rank;
