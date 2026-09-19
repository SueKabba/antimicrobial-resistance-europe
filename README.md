# Antimicrobial resistance trends across Europe

A pipeline analyzing 24 years of ECDC surveillance data on antibiotic
resistance across 30 European countries, covering three pathogens: MRSA
(Staphylococcus aureus), E. coli, and Klebsiella pneumoniae.

## Project goal

This project analyzes the three pathogens most relevant to European
antimicrobial resistance surveillance and shows, through a real SQL-based
pipeline, how resistance rates have shifted across countries and time.
The aim is to surface which country-pathogen combinations are worsening
fastest, since that's the kind of finding that informs healthcare
decisions: knowing where resistance is emerging lets health systems
prioritize surveillance, stewardship programs, and research funding
where they matter most. This project stands on its own, driven by that
question, not by any single job application.

## Why this matters

Antimicrobial resistance is what happens when bacteria stop responding to
the drugs used to treat them. It turns routine infections into harder,
slower, more expensive problems to treat, and it's one of the areas where
surveillance data and forecasting directly inform public health response,
not just reporting. The pattern in this data is stark: carbapenem-resistant
Klebsiella pneumoniae has gone from near zero in most countries in 2005 to
over 60% of isolates in Greece and rising sharply in Bulgaria and Romania.

## Files

| File | What it does |
|---|---|
| `pipeline.py` | Loads the three raw Atlas exports from `data/raw/`, cleans and reshapes them with a SQL query, writes `data/cleaned_resistance_data.csv` |
| `analysis.py` | Plots resistance trends per pathogen, fits a forecasting model per country/pathogen, writes `outputs/forecast_summary.csv` |
| `outputs/trend_*.png` | One chart per pathogen |
| `outputs/forecast_summary.csv` | Predicted next-year resistance rate for every country/pathogen combination with enough history, ranked by trend |

## Running it

```
python3 pipeline.py
python3 analysis.py
```

Software Used: Python 3 with `pandas`, `numpy`, `scikit-learn`,
`matplotlib` (`pip install pandas numpy scikit-learn matplotlib`). SQLite
needs no separate install, it's part of Python's standard library.


**"Why SQL instead of just pandas?"**
Both would work at this data size. SQL is the more honest answer for
what actually happens with data at scale: it's the standard interface
for querying data warehouses, and doing the aggregation as a `GROUP BY`
query rather than a pandas groupby is closer to how that work looks in
a real pipeline.

**"Why a simple linear regression instead of a more advanced model?"**
Because it's fully explainable. A linear trend per country/pathogen
tells you exactly what it's doing: fitting the straight line that best
matches recent years, then extending it one year forward. That's a
defensible baseline you can describe completely, which matters more for
a first version than a more accurate model you can't fully explain. The
model requires at least 5 years of data before it fits a trend at all,
since several countries have gaps.

**"What did I find?"**
Carbapenem-resistant K. pneumoniae is the clearest and most concerning
trend: Bulgaria's rate hit 67.6% in 2024, up from near zero in 2005, and
Greece has held above 60% since 2020. The scale of that trend is worth
stating directly: Klebsiella's fastest-rising countries are climbing by
more than 3 percentage points a year, while MRSA's fastest-rising
country is climbing by less than half a point a year. MRSA overall has
actually been declining across Europe since a 2004 peak. Same dataset,
same method, two pathogens moving in opposite directions.

**"What would I do next?"**
Two things: swap the linear regression for something that handles
non-linear jumps better, like ARIMA, since several of these trends
accelerate rather than move in a straight line. And extend the
dashboard's forecasting view the same way the trend and bar charts
already work, filterable by pathogen rather than fixed to one view.

## Dashboard

Live on Tableau Public: [Antimicrobial Resistance in Europe (2000-2024)](https://public.tableau.com/app/profile/sue.kabba/viz/AntimicrobialResistanceinEurope2000-2024/Dashboard1)

Three connected views, all built on the same six country-pathogen pairs
(the top 2 fastest-rising per pathogen) with matching colors across
every chart, so a country's line, bar, and map color always mean the
same thing:

- A map of resistance rate by country, with a pathogen dropdown to
  switch between MRSA, E. coli, and Klebsiella pneumoniae
- A trend line showing those six pairs' resistance rates over the full
  24-year period
- A bar chart ranking the same six pairs by how fast they're rising

