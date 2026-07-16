# Power BI Implementation Guide — HCP Intelligence Page

**Role:** Senior BI Engineer  
**Target Audience:** Student Analyst  
**Dashboard Page:** Page 3 — HCP Intelligence  
**Estimated Build Time:** 1.0 – 1.5 hours

---

## 1. Business Story

> **The Central Question this page answers:**  
> *"Which Healthcare Providers are our most valuable prescribers — and how should we engage each group differently to protect revenue and unlock growth?"*

The HCP Intelligence page is the **prescriber strategy hub** of the platform. Rather than treating all 500 HCPs equally, the commercial team needs to know *where* prescribing value is concentrated, *which* providers are drifting away, and *who* is still untapped.

This page translates the K-Means segmentation model's raw cluster output into a decision-ready view across five actionable segments:

| Segment | Strategic Intent |
|---|---|
| 🏆 **Champions** (6 HCPs) | Protect & deepen — these 6 providers generate 12.05% of all revenue |
| 💙 **Loyal HCPs** (44 HCPs) | Sustain & reward — consistent high-frequency prescribers (avg 75.6 Rx/yr) |
| 🚀 **High Potential** (162 HCPs) | Invest & activate — largest group (32.4%) with strong recent engagement |
| ⚠️ **At Risk** (205 HCPs) | Rescue & re-engage — the biggest churn risk; 41% of the HCP base |
| 🔻 **Low Value** (83 HCPs) | Efficient maintenance — low frequency, deprioritize field visits |

**Commercial insights unlocked by this page:**
- **The Pareto Reality:** Just 50 HCPs (Champions + Loyal) account for **36.46%** of total prescribing revenue.
- **The Churn Risk:** 205 "At Risk" HCPs represent nearly half the base — high-priority for field rep intervention.
- **The Growth Pool:** 162 "High Potential" HCPs (37.66% revenue share) are the primary target for promotional campaigns.

---

## 2. Connected Tables

The HCP Intelligence page is powered by **two tables** — one from the ML pipeline output, one from the PostgreSQL warehouse.

### Table A — `hcp_segments` *(Primary Table — ML Output CSV)*

**Source:** `data/output/hcp_segments.csv`  
**Grain:** One row per HCP (500 rows total)  
**How it's generated:** Output of `src/models/hcp_segmenter.py` — K-Means clustering (K=5) on RFM features built from the `prescriptions` table.

| Column | Type | Business Meaning |
|---|---|---|
| `hcp_id` | VARCHAR | Primary key — unique HCP identifier (e.g. HCP-0001) |
| `recency` | INT | Days since last prescription (lower = more recently active) |
| `frequency` | INT | Total number of prescriptions written |
| `monetary` | FLOAT | Total lifetime prescribing value (USD) — the **M** in RFM |
| `avg_rx_value` | FLOAT | Average value per prescription event |
| `unique_drugs` | INT | Number of distinct drug SKUs prescribed |
| `total_quantity` | INT | Total units prescribed across all drugs |
| `prescription_span` | INT | Days between first and last prescription (engagement lifespan) |
| `specialty` | VARCHAR | Clinical specialty (e.g. Cardiology, Gastroenterology) |
| `tier` | VARCHAR | HCP tier classification (Tier 1 / Tier 2 / Tier 3) |
| `years_experience` | INT | Years in practice |
| `territory_id` | VARCHAR | FK → `territories[territory_id]` |
| `cluster` | INT | Raw K-Means cluster index (0–4) — internal use only, **hide this field** |
| `segment` | VARCHAR | **Business segment label** — the key analytical dimension |

> **⚠️ Important:** The `cluster` column is the raw numeric K-Means output and has no business meaning on its own. Always use the `segment` column in your visuals and DAX measures. Right-click → Hide `cluster` in the field list after loading.

---

### Table B — `prescriptions` *(Supporting Table — PostgreSQL Warehouse)*

**Source:** PostgreSQL `pharma_analytics.prescriptions`  
**Grain:** One row per individual prescription transaction  
**Role on this page:** Provides transactional Rx data to cross-validate and enrich the aggregated HCP-level segment view — enables drug-level and therapeutic class drilldowns within each segment.

| Column | Type | Business Meaning |
|---|---|---|
| `prescription_id` | VARCHAR | Primary key |
| `hcp_id` | VARCHAR | FK → `hcp_segments[hcp_id]` |
| `drug_name` | VARCHAR | Drug prescribed |
| `therapeutic_class` | VARCHAR | Drug class (e.g. Cardiovascular, Oncology) |
| `prescription_date` | DATE | Date of prescription event |
| `quantity` | INT | Units prescribed |
| `unit_price` | NUMERIC | Price per unit |
| `total_value` | NUMERIC | Total transaction value (quantity × unit_price) |

> **Note:** `prescriptions` allows you to break down segment-level revenue by drug or therapeutic class — answering "Which segment drives Cardiology Rx?" or "Which drug is most reliant on Champion prescribers?"

---

### Supporting Dimension Tables *(Optional — for cross-page filter context)*

These tables are already loaded in the model and support slicer cross-filtering when needed:

| Table | FK Relationship | Role |
|---|---|---|
| `hcp_master` | `hcp_master[hcp_id]` → `prescriptions[hcp_id]` | Provides `city`, `state`, `hospital_affiliation` for geographic drilldowns |
| `territories` | `territories[territory_id]` → `hcp_segments[territory_id]` | Allows segment distribution to be sliced by region |

---

## 3. Data Model Relationships

```
hcp_segments [hcp_id] (1)  ──────►  prescriptions [hcp_id] (*)
```

**Relationship details:**

| Property | Value |
|---|---|
| From Table | `hcp_segments` |
| To Table | `prescriptions` |
| Join Key | `hcp_id` |
| Cardinality | One-to-Many |
| Cross-filter Direction | Single (hcp_segments → prescriptions) |
| Active | Yes |

> **⚠️ Warning:** Do **not** create a direct relationship between `hcp_segments` and `hcp_master`. Both tables reference the same HCPs but were built from different pipelines with different grain logic. Use `prescriptions` as the bridge if `hcp_master` attributes are needed on this page.

---

## 4. DAX Measures

All measures below should be created in a dedicated measure table named `_HCP Intelligence` for organization.

### 4.1 Core Segment Measures

```dax
-- Count of distinct HCPs in the current segment filter context
HCP Count by Segment =
DISTINCTCOUNT(hcp_segments[hcp_id])
```

```dax
-- Share of total monetary value attributed to the filtered segment(s)
Revenue Contribution % =
DIVIDE(
    SUM(hcp_segments[monetary]),
    CALCULATE(SUM(hcp_segments[monetary]), ALL(hcp_segments)),
    0
)
```

```dax
-- Average days since last prescription (lower = more recently active)
Avg Recency =
AVERAGE(hcp_segments[recency])
```

```dax
-- Average number of prescriptions written per HCP
Avg Frequency =
AVERAGE(hcp_segments[frequency])
```

```dax
-- Average lifetime prescribing value per HCP
Avg Monetary =
AVERAGE(hcp_segments[monetary])
```

### 4.2 Segment-Specific Spotlight Measures

```dax
-- Absolute count of Champion HCPs (for headline KPI card)
Champions Count =
CALCULATE(
    DISTINCTCOUNT(hcp_segments[hcp_id]),
    hcp_segments[segment] = "Champions"
)
```

```dax
-- Champions' share of total revenue (Pareto insight)
Champion Revenue % =
DIVIDE(
    CALCULATE(SUM(hcp_segments[monetary]), hcp_segments[segment] = "Champions"),
    CALCULATE(SUM(hcp_segments[monetary]), ALL(hcp_segments)),
    0
)
```

```dax
-- Count of At Risk HCPs (churn risk headline KPI)
At Risk Count =
CALCULATE(
    DISTINCTCOUNT(hcp_segments[hcp_id]),
    hcp_segments[segment] = "At Risk"
)
```

```dax
-- Share of HCP base that is At Risk (churn exposure %)
At Risk HCP % =
DIVIDE(
    [At Risk Count],
    DISTINCTCOUNT(hcp_segments[hcp_id]),
    0
)
```

### 4.3 Prescription-Linked Measures

```dax
-- Total Rx transaction value (from prescriptions table, filtered by segment context)
Total Rx Value =
SUM(prescriptions[total_value])
```

```dax
-- Average Rx value per transaction for the selected HCP/segment context
Avg Rx per Transaction =
AVERAGE(prescriptions[total_value])
```

---

## 5. Visual Build Order

### Step 1 — Top KPI Cards (Row of 4 across the top)

| Card | Measure | Format |
|---|---|---|
| Total HCPs | `HCP Count by Segment` | Integer |
| Champions | `Champions Count` | Integer |
| At Risk HCPs | `At Risk Count` | Integer — apply red conditional format |
| Avg Monetary | `Avg Monetary` | Currency ($M, 2 decimal) |

> Build these first — they anchor the narrative and let you validate data load before building complex visuals.

---

### Step 2 — Segment Distribution Donut Chart

- **Visual type:** Donut Chart  
- **Legend:** `hcp_segments[segment]`  
- **Values:** `HCP Count by Segment`  
- **Tooltip:** Add `Revenue Contribution %` and `Avg Frequency`  
- **Colors (match Python `hcp_segmentation_charts.png` palette):**

| Segment | Hex Color |
|---|---|
| Champions | `#4CAF50` (Green) |
| Loyal HCPs | `#2196F3` (Blue) |
| High Potential | `#FF9800` (Orange) |
| At Risk | `#F44336` (Red) |
| Low Value | `#9E9E9E` (Grey) |

---

### Step 3 — Revenue by Segment Horizontal Bar Chart

- **Visual type:** Clustered Bar Chart (horizontal)  
- **Y-axis:** `hcp_segments[segment]`  
- **X-axis:** `SUM(hcp_segments[monetary])`  
- **Sort:** Descending by revenue  
- **Data labels:** On — show `Revenue Contribution %`  
- **Conditional formatting:** Match the same 5-color palette as Step 2

> **Expected story:** Champions bar is visually small in *count* but disproportionately tall in *revenue* — this visual alone communicates the Pareto principle.

---

### Step 4 — HCP Value Matrix Scatter Plot (RFM Plot)

- **Visual type:** Scatter Chart  
- **X-axis:** `Avg Frequency`  
- **Y-axis:** `Avg Monetary`  
- **Legend:** `hcp_segments[segment]`  
- **Size:** `HCP Count by Segment`  
- **Tooltip:** `Avg Recency`, `Avg Frequency`, `Avg Monetary`, `Revenue Contribution %`

> **Tip:** This is the most analytically powerful visual on the page. The upper-right quadrant (high frequency + high monetary) visually confirms Champions and Loyal HCPs. At Risk HCPs cluster in the lower-left, spatially illustrating the churn problem.

---

### Step 5 — HCP Profile Detail Table

- **Visual type:** Matrix or Table  
- **Rows:** `hcp_segments[hcp_id]`, `hcp_segments[specialty]`, `hcp_segments[tier]`, `hcp_segments[territory_id]`, `hcp_segments[segment]`  
- **Values:** `hcp_segments[monetary]`, `hcp_segments[frequency]`, `hcp_segments[recency]`  
- **Conditional formatting:**
  - `monetary` → Green gradient (higher = greener)
  - `recency` → Red gradient (higher recency = worse engagement = redder)
- **Sort default:** Descending by `monetary`

---

### Step 6 — Slicers (Filter Panel)

| Slicer | Field | Type |
|---|---|---|
| Segment | `hcp_segments[segment]` | List (multi-select) |
| Specialty | `hcp_segments[specialty]` | Dropdown |
| Tier | `hcp_segments[tier]` | List |
| Territory | `hcp_segments[territory_id]` | Dropdown |

---

## 6. Page Layout Blueprint

```
┌──────────────────────────────────────────────────────────────────┐
│  PAGE TITLE: HCP Intelligence — Prescriber Segmentation         │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│  KPI:       │  KPI:       │  KPI:       │  KPI:                 │
│  Total HCPs │  Champions  │  At Risk    │  Avg Monetary/HCP     │
├─────────────┴──────┬──────┴─────────────┴───────────────────────┤
│                    │                                             │
│  Segment Donut     │  Revenue by Segment (Horizontal Bar)        │
│  (left half)       │  (right half)                               │
│                    │                                             │
├────────────────────┴─────────────────────────────────────────────┤
│                                                                  │
│        HCP Value Matrix Scatter Plot (full width)                │
│             Frequency (X) vs. Monetary (Y) by Segment            │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  [Slicers: Segment | Specialty | Tier | Territory]               │
│  HCP Profile Detail Table (filterable matrix)                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Common Implementation Mistakes

| # | Mistake | Correct Approach |
|---|---|---|
| 1 | Rebuilding K-Means clustering in DAX | Import the pre-built `hcp_segments.csv` — segmentation is a Python ML output, not a DAX calculation |
| 2 | Using `cluster` column (0–4) in visuals | Always use `segment` (the labelled version). Hide `cluster` in the field list |
| 3 | Using `AVERAGE(monetary)` to get "total revenue" across segments | Use `SUM(hcp_segments[monetary])` with `ALL()` for the grand total denominator |
| 4 | Treating `hcp_segments[monetary]` and `prescriptions[total_value]` as the same metric | `monetary` is the RFM aggregate from the ML pipeline. `total_value` is per-transaction from the warehouse. Complementary, not interchangeable |
| 5 | Creating a direct relationship from `hcp_segments` → `hcp_master` | No direct relationship needed; `prescriptions[hcp_id]` is the correct bridge |
| 6 | Scatter plot showing flat dots with no size variation | Ensure the **Size** field well is populated with `HCP Count by Segment` — without it, the bubble chart loses its analytical depth |

---

## 8. Validation Checks

After building the page, verify these rules before publishing:

| Check | Expected Result |
|---|---|
| Total HCP count | **500** |
| Distinct segment count | **5** |
| Segment names (exact match) | Champions, Loyal HCPs, High Potential, At Risk, Low Value |
| Champions count | **6** |
| At Risk count | **205** |
| Revenue Contribution % (all segments) | Sums to **100%** |
| At Risk share of HCP base | **41.0%** |
| High Potential share of HCP base | **32.4%** |

---

## 9. Segment Reference Card

Use as a quick reference during build and for tooltip/annotation copy:

| Segment | HCP Count | HCP % | Avg Recency (days) | Avg Frequency (Rx) | Avg Monetary | Revenue % |
|---|---|---|---|---|---|---|
| 🏆 Champions | 6 | 1.2% | 5.8 | 79.3 | $50,066,757 | 12.05% |
| 💙 Loyal HCPs | 44 | 8.8% | 4.2 | 75.6 | $13,824,288 | 24.41% |
| 🚀 High Potential | 162 | 32.4% | 8.3 | 39.4 | $5,792,559 | 37.66% |
| ⚠️ At Risk | 205 | 41.0% | 11.8 | 17.0 | $2,188,040 | 18.00% |
| 🔻 Low Value | 83 | 16.6% | 46.3 | 16.1 | $2,366,639 | 7.88% |

---

## 10. Data Lineage Summary

```
PostgreSQL: prescriptions
    (hcp_id, drug_name, prescription_date, total_value)
            │
            ▼
src/processing/ → hcp_rfm_features.csv
    (hcp_id, recency, frequency, monetary, avg_rx_value, ...)
            │
            ▼
src/models/hcp_segmenter.py  (K-Means, K=5)
            │
            ▼
data/output/hcp_segments.csv   ◄── PRIMARY TABLE ON THIS PAGE
    (hcp_id, recency, frequency, monetary, segment, ...)
            │
            │  joined by hcp_id
            ▼
PostgreSQL: prescriptions      ◄── SUPPORTING TABLE (transaction grain)
            │
            ▼
    Power BI: HCP Intelligence Page
```

---

*Document generated for: Pharma Sales Forecasting & HCP Intelligence Platform*  
*Last updated: 2026-07-04*
