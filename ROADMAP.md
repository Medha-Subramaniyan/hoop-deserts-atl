# Project Roadmap — Hoop Deserts ATL

Learning-oriented checklist: concept → attempt it yourself → checkpoint → narrow ask for
help if stuck. Grounded in the actual bugs and columns present in this repo's data as of
2026-08-11.

## Where things stand

`tracts` is loaded and filtered to Fulton + DeKalb. `courts`, `census`, and `health` are
also loaded but not yet cleaned or joined. Known bugs to fix in Phase 1:

- `census` numeric columns are still `object` dtype (need casting)
- `census.median_household_income` contains Census null sentinel `-666666666`
- `census` has no `GEOID` column yet (needs building from `state`+`county`+`tract`)
- `courts` has at least one point outside Georgia (longitude ~ -92, central Missouri)
- `courts` vs `tracts` CRS not yet verified to match
- `health` is long-format (one row per tract+measure) and needs pivoting on `MeasureId`

---



## Phase 1 (finish it) — Clean each layer independently

**Concepts to learn:** dtype casting, sentinel/null values, string manipulation
(`.str.zfill()`), CRS basics

- [x] `census`: cast income/poverty/population/race columns from `object` to numeric
  ```
  (`pd.to_numeric`)
  ```
- [ ] `census`: replace `-666666666` with `NaN` — look up why Census uses this value
  ```
  before just patching it
  ```
- [x] `census`: build `GEOID` from `state` + `county` + `tract`, zero-padded to correct
  ```
  widths — verify on one row by hand first
  ```
- [ ] `courts`: find and inspect the row(s) with coordinates outside Georgia; decide
  ```
  keep/drop/investigate and note why
  ```
- [ ] `courts` vs `tracts`: print `.crs` on both — same or different? Understand what
  ```
  breaks on mismatch before fixing it
  ```
- [ ] `health`: pivot long → wide on `MeasureId` (one row per tract) — try it on a 3-row
  ```
  slice first, then run on the full table
  ```

**Checkpoint:** each of the 4 dataframes should `.head()` / `.info()` with dtypes and
null counts you can explain out loud without looking anything up.

**Ask for help with:** why Census uses `-666666666` instead of `NaN`; walking through
`pivot_table` with a toy example; what actually breaks with mismatched CRS.

---



## Phase 2 — Joins

**Concepts to learn:** spatial join vs. tabular merge, inner/left join semantics, why
row counts change

- [ ] Predict the output shape of `gpd.sjoin(courts, tracts, predicate='within')` before
  ```
  running it (~78 rows, each tagged with a tract GEOID)
  ```
- [ ] Run it — does the row count match your prediction? If not, debug why before moving on
- [ ] Merge `census` onto `tracts` via `GEOID` — choose join type deliberately (left off
  ```
  `tracts` to avoid silently losing tracts) and be able to justify it
  ```
- [ ] Merge pivoted `health` onto the result via matching keys (`GEOID` / `LocationID`)
- [ ] Spot-check: pick a tract you can identify by name (e.g. a Buckhead or West End
  ```
  tract) and confirm its income/health numbers look plausible
  ```

**Checkpoint:** one GeoDataFrame, ~530 rows, with geometry + income + poverty + race +
LPA/OBESITY/MHLTH + court count — and you can explain the join type used at each step.

**Ask for help with:** debugging unexpected merge row counts; the difference between how
`sjoin` and `merge` decide what counts as a match.

---



## Phase 3 — Build the core metric

**Concepts to learn:** `.groupby()`, vectorized math, divide-by-zero handling, `.fillna()`

- [ ] `courts_per_tract = sjoin_result.groupby('GEOID').size()` — explain in your own
  ```
  words what `.size()` counts
  ```
- [ ] Merge the count back onto the Phase 2 GeoDataFrame — decide deliberately how to
  ```
  handle tracts with no match (missing vs. true zero)
  ```
- [ ] Compute `density = courts / (total_population / 10_000)` — predict what happens
  ```
  for near-zero-population tracts before checking
  ```
- [ ] Plot a histogram of `density` — describe its shape (skewed? outlier-dominated?)

**Checkpoint:** you can explain, unprompted, why most tracts have density = 0 and why
that's expected here, not a bug.

**Ask for help with:** sanity-checking divide-by-zero handling; what the histogram shape
implies for choosing a correlation method later.

---



## Phase 4 — Analysis

**Concepts to learn:** Pearson vs. Spearman, reading scatterplots for skew/outliers,
quantile thresholding, boolean masking

- [ ] Scatter `density` vs. `median_household_income` before computing any correlation
  ```
  number
  ```
- [ ] Run Pearson and Spearman `.corr()` and compare — explain why they differ given the
  ```
  skewed distribution
  ```
- [ ] Repeat for `density` vs. `OBESITY`, `LPA`, `MHLTH`
- [ ] Define "hoop desert" via `.quantile(0.25)` / `.quantile(0.75)` cutoffs on density +
  ```
  income + inactivity — build the boolean mask one condition at a time, checking row
  count after each `&`
  ```
- [ ] Pull the actual tract `NAME`s meeting the definition — these become the named
  ```
  neighborhoods in the article
  ```
- [ ] Decide which article angle the data actually supports (pure density map / court
  ```
  quality via `surface`+`lit` / income+race breakdown) and commit to it
  ```

**Checkpoint:** state the core finding as one sentence with a real number, and explain
why Spearman or Pearson was the right choice.

**Ask for help with:** interpreting correlation strength; sanity-checking quantile-mask
logic; judging which angle the data supports best.

---



## Phase 5 — Visualization

**Concepts to learn:** `geopandas.plot()` layering, colormaps, legends, colorblind-safe
sequential palettes

- [ ] Static exploratory plots first: bar chart of top/bottom 10 tracts by density,
  ```
  scatter of income vs. density with a trendline
  ```
- [ ] Build the hero map: `tracts.plot(column=..., cmap=..., legend=True)`, overlay
  ```
  courts as points on the same `ax`
  ```
- [ ] Try 2-3 sequential colormaps, pick the most legible and colorblind-safe (avoid
  ```
  red-green)
  ```
- [ ] Highlight/outline the named hoop-desert tracts
- [ ] Label 3-5 specific neighborhoods by name on the map

**Checkpoint:** someone who's never seen the data should understand the core finding
from the map alone.

**Ask for help with:** layering two plots on one matplotlib axis; a legibility critique
of the color scale.

---



## Phase 6 — Writing

Mostly solo work by design — this is where over-relying on AI would defeat the point.

- [ ] Write findings in plain, data-only sentences first — no narrative, one sentence
  ```
  per major number
  ```
- [ ] Fact-check every sentence against actual dataframe output, not memory
- [ ] Draft the full piece: hook → thesis → visual proof → socio-economic breakdown →
  ```
  health connection (caveated) → limitations → conclusion
  ```
- [ ] Read it once cold, as a reader who's never seen the data — does the map + one
  ```
  paragraph carry the whole story?
  ```

**Ask for help with:** narrow checks only — "does this paragraph overclaim given sample
size," "critique this transition" — not full-section drafting.