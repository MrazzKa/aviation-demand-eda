# US Air Travel 2019–2023: the recovery wasn't what everyone thinks

A data story built on **3,000,000 real US flights** (BTS on-time records, 2019–2023)
about how air-travel demand collapsed, who came back, and where the system still
breaks. SQL heavy-lifting in **DuckDB**, stats and charts in **Python**.

> **Data:** U.S. DOT Bureau of Transportation Statistics, "Reporting Carrier
> On-Time Performance" — a 3M-row public sample (2019-01 → 2023-08). Real flights
> actually operated by US carriers. Includes delay-cause breakdown and cancellations.
> *(The CSV is ~600 MB and not committed here — grab it from BTS/Kaggle and drop it
> in `av_data/`.)*

---

## Four findings

### 1. Business travel never came back — leisure overshot

![Recovery](charts/02_business_vs_leisure_recovery.png)

Both segments crashed together in spring 2020 (down ~70%). But the recovery split
in two: by 2023, **leisure/sun routes ran 7% above their 2019 level**, while
**business-hub routes plateaued at 87% and stopped climbing**. "Air travel
recovered" is only half true — *leisure* recovered; business trips were structurally
replaced (video calls) and never returned. For demand intelligence this is the whole
ballgame: capacity and pricing should follow the segment that's actually growing.

### 2. The COVID demand cliff

![COVID curve](charts/01_covid_demand_curve.png)

The monthly series puts a number on it: demand bottomed in April–May 2020 at roughly
**30% of normal**, then clawed back over three years in the asymmetric way above.

### 3. The Southwest meltdown, visible in raw data

![Southwest](charts/03_southwest_meltdown.png)

A winter storm hit every airline around Dec 22–23, 2022 — but only one *collapsed*.
Southwest's cancellation rate climbed day over day to **77% on Dec 26**, while every
other carrier was back under 10%. The data shows it wasn't the weather (that passed);
it was one airline's operations. A single `WHERE carrier='WN'` tells the story.

### 4. Why your evening flight is cursed — delays cascade

![Delay cascade](charts/04_delay_cascade.png)

Average departure delay grows from **~3.6 min at 6am to ~16.6 min by 8pm**. The
cause column proves the mechanism: "late-aircraft" (the previous flight ran late) is
**23% of delay minutes in the morning but 45% in the evening**. Delay isn't random —
it accumulates through the day as aircraft fall behind. Book early flights.

---

## Method

- **DuckDB** runs SQL straight over the 600 MB CSV — aggregation, `CASE`-based
  segmentation, date math, cancellation rates — no need to load it all into pandas.
- Recovery is indexed to each segment's own **2019 monthly baseline**, so seasonality
  isn't mistaken for recovery.
- Delay causes use the BTS minute-allocation fields (carrier / weather / NAS /
  security / late-aircraft).

## How this maps to demand intelligence (Aviastats-style)

This is a sandbox version of the questions a market-intelligence team answers on
real ticketing data: *which segments are growing, where demand shifted, and which
operational risks concentrate in one carrier or time-of-day.* The dataset has no
fares, so this is a demand-and-reliability study, not pricing — adding fare data
(DOT DB1B) extends it to elasticity and revenue management.

## Reproduce

```bash
pip install -r requirements.txt
# place flights_sample_3m.csv in av_data/
python analysis.py     # writes charts/
```

## Honest limitations

US carriers only; a 3M-row sample (proportional, so rates are reliable, absolute
counts are sample-scaled); business/leisure is a destination proxy, not surveyed
trip purpose; data ends Aug 2023.

*Tools: DuckDB · SQL (CTEs, window functions, CASE aggregation) · Python (pandas, numpy, matplotlib). Data: U.S. BTS.*
