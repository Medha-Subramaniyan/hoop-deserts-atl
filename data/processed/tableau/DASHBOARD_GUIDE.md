# Tableau Dashboard Build Guide

### "The Court Was Never the Constraint" — Full Stack Culture

A step-by-step build for the interactive companion to the article. Every sheet
here earns its place by answering one question the article raises. Nothing is
included because Tableau makes it easy.

---

## 0. Before you start

### The one thing that matters most

The dashboard has to survive a hostile reader. Someone will look at this and say
*"you just didn't count the courts in poor neighborhoods."* Every design choice
below is chosen so that objection can be checked, not just asserted against.

That means: tooltips carry raw counts, not just rates. The court layer is
browsable. The data-coverage sheet is not hidden in an appendix — it's a tab.

### Data files

All in `data/processed/tableau/`.


| File                 | Rows  | Grain                | Use                    |
| -------------------- | ----- | -------------------- | ---------------------- |
| `all_tracts.csv`     | 1,311 | one census tract     | every non-map sheet    |
| `all_courts.csv`     | 578   | one basketball court | court layer + coverage |
| `atlanta_tracts.shp` | 530   | one tract polygon    | Atlanta choropleth     |
| `chicago_tracts.shp` | 781   | one tract polygon    | Chicago choropleth     |


**CSVs cannot draw polygons.** They carry `lat`/`lon` centroids, which give you
dots. For the filled choropleth you must connect to the `.shp` files. A shapefile
is really 5+ sibling files (`.shp`, `.dbf`, `.shx`, `.prj`, `.cpg`) — keep them
together in one folder or the connection fails.

### Scope note — read this before you build

**Chicago is city limits (781 tracts), not Cook County (1,332).**

The Overpass export only ever covered the city. 97.5% of mapped courts fall
inside it. Including the 551 unqueried suburban tracts would have rendered them
as court-free on the map — a visual claim that is simply false.

Income quartiles are recomputed *within* each city's frame, so "Q1" means
"poorest quarter of this city," not "poorest quarter of a pooled two-city
distribution." That is what makes the two panels comparable.

Say this in the dashboard footer. It is the kind of methods note that earns
trust rather than spending it.

### Fields you'll use constantly


| Field                      | Meaning                      | Watch out for                        |
| -------------------------- | ---------------------------- | ------------------------------------ |
| `courts_per_10k`           | courts ÷ (pop/10,000)        | NULL where pop < 100                 |
| `court_count`              | raw courts in tract          | true zero, never null                |
| `income_q`                 | Q1 (lowest) … Q4 (highest)   | contains literal `"nan"` — filter it |
| `LPA`                      | % adults physically inactive | the article's outcome variable       |
| `pct_white/black/hispanic` | race & ethnicity shares      | **do not sum to 100**                |
| `hoops_status`             | Full / Half / Not recorded   | 75% "Not recorded"                   |
| `lit_status`               | Lit / Not lit / Not recorded | 94% "Not recorded"                   |


**On the race fields:** ACS race (table B02001) and Hispanic origin (B03003) are
separate universes. A Hispanic resident is also counted in a race category. Three
independent shares — never stack them, never present them as a breakdown of 100%.

**On** `median_household_income`**:** 27 tracts are NULL (Census suppresses estimates
where the sample is too small). Tableau silently drops them from income views.
That is correct behavior, but you should know it's happening.

---



## 1. Connect the data

1. **Open Tableau → Connect → Text file →** `all_tracts.csv`
2. In the data source tab, **Add** a second connection: `all_courts.csv`
3. Do **not** join them. Use them as separate logical tables.

> **Why no join:** they're different grains. One row per tract vs. one row per
> court. Joining duplicates tract rows once per court and quietly inflates every
> average you compute afterward. Keep them separate; the dashboard links them
> with filter actions instead.

1. Add two more connections for the shapefiles: **Connect → Spatial file →**
  `atlanta_tracts.shp`, then again for `chicago_tracts.shp`.



### Immediately set field defaults

Right-click each field → **Default Properties**:

- `courts_per_10k` → Number (Custom, 2 decimals)
- `LPA`, `OBESITY`, `MHLTH`, `pct_*`, `poverty_rate` → Number, 1 decimal, suffix `%`
- `median_household_income` → Currency (Custom, 0 decimals)
- `income_q` → Sort → Manual → drag into Q1 → Q2 → Q3 → Q4 order

> Doing this once at the data-source level saves re-formatting on every sheet.

---



## 2. Calculated fields

Create these first. **Analysis → Create Calculated Field.**

### 2.1 `Courts per 10k (aggregate)`

```
SUM([Court Count]) / (SUM([Total Population]) / 10000)
```

> **This is the single most important calculation in the dashboard.**
>
> `AVG([Courts Per 10k])` gives a *different and worse* answer. 77% of Atlanta
> tracts and 69% of Chicago tracts have zero courts, and a handful have tiny
> populations — averaging tract-level rates lets a 200-person tract with one
> court swing the result as hard as a 6,000-person tract.
>
> This version pools the numerator and denominator across whatever group you
> drop it on, which is the honest population-weighted rate. Use it everywhere.



### 2.2 `% tracts with no court`

```
SUM(IF [Court Count] = 0 THEN 1 ELSE 0 END) / COUNT([GEOID])
```

Format as Percentage, 0 decimals.

> This is the robust companion to the rate. With this much zero-inflation, "what
> share of neighborhoods have nothing at all" is a claim that doesn't move if one
> outlier tract changes.



### 2.3 `Has court (label)`

```
IF [Court Count] = 0 THEN "No court" ELSE "Has court" END
```



### 2.4 `Income quartile (clean)`

```
IF [Income Q] = "nan" THEN NULL ELSE [Income Q] END
```

> The CSV stores missing income as the literal string `"nan"`. Without this it
> renders as a fifth quartile, which is wrong and looks broken.



### 2.5 `Inactivity band` (for the scatter)

```
IF [LPA] >= 35 THEN "35%+ inactive"
ELSEIF [LPA] >= 25 THEN "25–35%"
ELSE "Under 25%" END
```



### 2.6 `Court attribute recorded?` (on the courts source)

```
IF ISNULL([Lit]) THEN "Not recorded" ELSE "Recorded" END
```

---



## 3. The color system

Set this once and never deviate. Consistency is what makes six sheets read as one
dashboard.

### Cities — categorical (identity)


| City    | Hex       |
| ------- | --------- |
| Atlanta | `#e8833a` |
| Chicago | `#2a6fb5` |


> Chosen far apart in **both hue and lightness**, so they survive protanopia,
> deuteranopia, and greyscale printing. Tableau's default 10-color palette is not
> colorblind-safe — do not use it.
>
> Set via: right-click `City` on Color → Edit Colors → assign manually.



### Inactivity — sequential (magnitude)

Single hue, light → dark: **Blue** (Tableau's sequential "Blue" palette).

> Sequential means *one hue, varying lightness*. Lightness is what encodes "how
> much" and it's the channel that survives colour-vision deficiency. Never use a
> rainbow / spectral ramp for magnitude, and never red-green.



### Race — three fixed categories


| Group    | Hex       |
| -------- | --------- |
| White    | `#8c8c8c` |
| Black    | `#4a3aa7` |
| Hispanic | `#1baf7a` |




### Neutrals

- Text: `#1a1a1a`
- Secondary text: `#6b6b6b`
- Gridlines: `#e5e5e3`
- Court dots on maps: `#d64545`

---



## 4. Sheet 1 — "The Reversal" (bar chart)

**Article section: 3 & 4. This is the dashboard's headline.**

### Build

1. **Columns:** `Income quartile (clean)`
2. **Rows:** `Courts per 10k (aggregate)`
3. **Columns** (before quartile): `City` → creates side-by-side panels
4. **Color:** `City` → apply the two hex codes
5. **Label:** drag `Courts per 10k (aggregate)` → Label shelf. Alignment: top-center, bold
6. **Filter:** `Income quartile (clean)` → exclude Null
7. Right-click y-axis → **Edit Axis** → uncheck "Include zero"? **No — keep zero.**
  Bar length must encode value from a zero baseline or it lies.



### Expected result


| Quartile     | Atlanta  | Chicago  |
| ------------ | -------- | -------- |
| Q1 (lowest)  | 1.08     | **2.11** |
| Q2           | 0.68     | 1.55     |
| Q3           | 0.73     | 1.21     |
| Q4 (highest) | **1.55** | 1.08     |


Chicago descends monotonically. Atlanta is U-shaped — highest at *both* ends.

### Title

> **Chicago built courts where income is lowest. Atlanta built them at both ends.**
> Basketball courts per 10,000 residents, by census-tract income quartile



### Tooltip

```
<Income quartile (clean)> — <City>

<AGG(Courts per 10k (aggregate))> courts per 10,000 residents
<SUM(Court Count)> courts across <COUNT(GEOID)> tracts
<% tracts with no court> of tracts have no court at all
Median household income: <MEDIAN(Median Household Income)>
```

> The raw count belongs in the tooltip because a rate alone invites "you
> normalized it to get the answer you wanted." Showing 45 courts vs 70 courts
> underneath the rate closes that door.



### The honest caveat to build in

Atlanta's Q4 number is inflated by private half-courts in wealthy subdivisions —
see Sheet 5. Add a caption: *"Atlanta Q4 includes private residential courts;
Chicago's are overwhelmingly Park District."*

---



## 5. Sheet 2 — "What Actually Sorts" (slope chart)

**Article section: 7. The counterweight to Sheet 1.**

### Build

1. **Columns:** `Income quartile (clean)`
2. **Rows:** `MEDIAN(LPA)`
3. **Color:** `City`
4. **Marks:** Line. Add a second mark type via dual axis, or simply set Path and
  enable "Show markers" (Format → Lines → Markers: automatic)
5. **Label:** `MEDIAN(LPA)`, but set **Label → Marks to Label → Line Ends only**

> Labeling only the endpoints is the whole trick. Four labels per line is noise;
> two is a statement — you read the drop, not the individual points.



### Expected result


|         | Q1    | Q2    | Q3    | Q4    |
| ------- | ----- | ----- | ----- | ----- |
| Atlanta | 31.1% | 24.5% | 16.6% | 13.8% |
| Chicago | 37.0% | 30.3% | 23.1% | 13.4% |


Near-parallel steep declines. **Both cities.** Regardless of where courts went.

### Title

> **The gap that is real, in both cities**
> Median share of adults reporting no physical activity outside work



### Why this sheet is the argument

Place it directly beneath Sheet 1 in the dashboard. The visual rhyme does the
work: two cities that distributed courts on opposite logics produced the *same*
inactivity gradient. If courts drove activity, these two charts could not both be
true.

---



## 6. Sheet 3 — Dual maps

**Article section: 4 & hero visual.**

### 6a. Court locations (dot map)

1. Go to the `all_courts.csv` source
2. Double-click `Latitude` then `Longitude` → Tableau builds a map
3. Set both to **Dimension** (right-click → Dimension) so every court is its own mark
4. **Detail:** `id` — forces one mark per court
5. **Color:** solid `#d64545`, opacity 80%, size small
6. **Filter:** `City`
7. Map → Background Maps → **Light** (or None for print)



### 6b. Inactivity (choropleth)

1. Switch to the `chicago_tracts.shp` source
2. Double-click `Geometry` → polygons render
3. **Color:** `LPA` → Blue sequential palette
4. Edit Colors → **5 steps** (stepped, not continuous)

> Stepped color is a deliberate choice. Continuous ramps imply a precision that
> modeled small-area estimates don't have. Five bins say "these are bands,"
> which is what PLACES data actually supports.

1. **Border:** white, thin
2. Repeat with `atlanta_tracts.shp`



### Tooltip (choropleth)

```
<NAMELSAD>
<Neighborhood>

Physically inactive: <LPA>
Obesity: <OBESITY>
Median household income: <Median Household Income>
Basketball courts: <Court Count>
Population: <Total Population>
```

> `Neighborhood` is NULL for 361 Atlanta tracts (outside city limits) and 0
> Chicago tracts. Tableau shows a blank line; acceptable, or wrap in
> `IFNULL([Neighborhood], "Unincorporated")`.



### The point of putting them side by side

Left map: dots scattered across the whole city. Right map: a sharp north/south
(Atlanta) or north/south-and-west (Chicago) gradient. **Scattered vs. sorted.**
That contrast is the article's thesis in one image.

---



## 7. Sheet 4 — "Who 'Underserved' Means" (grouped bars)

**Article section: 5. The most original finding, and the least obvious.**

### Build

1. Create a **parameter** or use Measure Names/Values:
  - Drag `Measure Names` to Columns
  - Drag `Measure Values` to Rows
  - In Measure Values, keep only `MEDIAN(pct_white)`, `MEDIAN(pct_black)`,
  `MEDIAN(pct_hispanic)`
2. **Columns:** `Income quartile (clean)` (outer), `Measure Names` (inner)
3. **Color:** `Measure Names` → assign the three race hex codes
4. **Rows:** `City` → two stacked panels



### Critical: do NOT stack these bars

Grouped side-by-side only. Stacking would draw a 100% whole that does not exist,
because ACS race and Hispanic origin are separate measures.

### Add a caption directly on the sheet

> *ACS race (B02001) and Hispanic origin (B03003) are separate measures. A
> Hispanic resident is also counted in a race category, so these shares do not
> sum to 100%.*



### What it reveals

Chicago's **Q2 is the Hispanic quartile** — the highest Hispanic share of any
quartile — and court density there has already fallen from 2.11 to 1.55.

Meanwhile court density correlates **+0.21 with % Black** but **−0.07 with %
Hispanic**.

> **The insight:** Chicago's Park District investment tracked *Black*
> neighborhoods, not low-income neighborhoods generally. Little Village, New
> City, and Gage Park — Mexican-American neighborhoods with among the worst
> inactivity in the city — sit outside the pattern entirely.
>
> A `pct_black`-only analysis would have rendered them as unexplained noise. This
> sheet is why the three-way breakdown was worth doing.



### Title

> **"Low income" is not one population — and the courts followed only one of them**

---



## 8. Sheet 5 — "A Court Is Not a Court" (stacked bars)

**Article section: 6. Where the article stops being about counts.**

Use the `all_courts.csv` source.

### Build

1. **Columns:** `Income Q`
2. **Rows:** `COUNT(id)`
3. **Color:** `hoops_status`
4. **Rows** (outer): `City`
5. Right-click COUNT(id) → Quick Table Calculation → **Percent of Total**
6. Compute Using → `hoops_status`



### Expected result


| City    | Full court (2+) | Half court (1) | Not recorded |
| ------- | --------------- | -------------- | ------------ |
| Atlanta | 28              | 19             | 144          |
| Chicago | 85              | 13             | 289          |


Among **recorded** courts: Atlanta is 60% full-court, Chicago is **87%**.

### The finding

Every income quartile in both cities averages 1.3–1.9 courts per tract *where
courts exist.* By count, courts look identical everywhere. They are not.

Atlanta's wealthy-tract "advantage" partly counts private half-courts as
equivalent to a Park District full court. Chicago applies a municipal standard.

### State the sample size on the sheet

Only 47 Atlanta and 98 Chicago courts have `hoops` recorded. **Label this
directional, not conclusive.** Put it in the caption, not the footnotes.

---



## 9. Sheet 6 — "What Nobody Records" (coverage bars)

**Article section: 6 & the thesis. Do not bury this.**

### Build

1. Source: `all_courts.csv`
2. Create calcs for each attribute, e.g.:
  ```
   SUM(IF NOT ISNULL([Lit]) THEN 1 ELSE 0 END) / COUNT([id])
  ```
   Repeat for `Surface`, `Access`, `Hoops`.
3. **Rows:** Measure Names (the four coverage calcs)
4. **Columns:** Measure Values
5. **Color:** `City`
6. Horizontal bars — the category labels are words, so vertical would force
  rotated text



### Expected result


| Attribute       | Atlanta | Chicago |
| --------------- | ------- | ------- |
| Lighting        | 9%      | **4%**  |
| Surface         | 12%     | 9%      |
| Public/private  | 17%     | 15%     |
| Number of hoops | 25%     | 25%     |




### Why this is the thesis, not a caveat

Lighting determines whether a court is usable after work in winter. It is
recorded on **18 of 191** Atlanta courts and **14 of 387** in Chicago.

The variable most likely to explain who actually plays is almost entirely absent
from the public record of public space.

> **The business implication** — and this is where your column lands: every brand
> campaign, every parks bond, every "courts built" metric optimizes for what's
> easy to count. Presence is legible. Hours, lighting, maintenance, programming
> and perceived safety are not — so they don't get funded, and they don't get
> measured.



### Title

> **The thing most likely to explain who plays is the thing nobody records**

---



## 10. Sheet 7 — Neighborhood detail table

**Article section: 7. The receipts.**

### Build

1. Source: `all_tracts.csv`
2. **Rows:** `Neighborhood`, `City`
3. **Text/Columns:** `MEDIAN(LPA)`, `MEDIAN(OBESITY)`, `SUM(Court Count)`,
  `MEDIAN(Median Household Income)`, `SUM(Total Population)`
4. **Filter:** `Neighborhood` → exclude Null; `SUM(Court Count)` → at least 1
5. **Sort:** `MEDIAN(LPA)` descending
6. Add a **highlight**: `MEDIAN(LPA)` on Color, sequential Blue



### What surfaces

The neighborhoods with courts *and* the worst inactivity:

- **Fuller Park, Chicago** — 3 courts across 2 tracts (~2,100 people), 48.2% inactive, 50.4% obesity
- **Riverdale, Chicago** — 6 courts, 7,500 residents, 51.3% obesity
- **Thomasville Heights, Atlanta** — 2 courts, 49.2% inactive, 49.4% obesity
- **Mechanicsville, Vine City, West End, Englewood, Garfield Park**

> **This table is the article's proof paragraph.** Riverdale has one of the
> highest court-per-capita concentrations in the city and half its adults are
> obese. If access drove participation, that row could not exist.

---



## 11. Assembling the dashboard



### Layout — a scrolling narrative, not a control panel

Size: **1200 × 2400**, Fixed size. Long-form, article-companion, scrolls like the
piece it accompanies.

```
┌──────────────────────────────────────────────────┐
│  TITLE: The Court Was Never the Constraint       │
│  Standfirst + [City filter] [Income filter]      │
├──────────────────────────────────────────────────┤
│  SHEET 1 — The Reversal            (h ≈ 380px)   │
│  caption: the two cities' opposite logics        │
├──────────────────────────────────────────────────┤
│  SHEET 2 — What Actually Sorts     (h ≈ 340px)   │
│  caption: same gradient, both cities             │
├──────────────────────────────────────────────────┤
│  SHEET 3 — Dual maps (2×2)         (h ≈ 620px)   │
│  courts left · inactivity right                  │
├──────────────────────────────────────────────────┤
│  SHEET 4 — Who "underserved" means (h ≈ 360px)   │
├──────────────────────────────────────────────────┤
│  SHEET 5 — A court is not a court  (h ≈ 320px)   │
│  SHEET 6 — What nobody records     (h ≈ 320px)   │
├──────────────────────────────────────────────────┤
│  SHEET 7 — Neighborhood table      (h ≈ 400px)   │
├──────────────────────────────────────────────────┤
│  METHODS + SOURCES FOOTER                        │
└──────────────────────────────────────────────────┘
```

> **Sheets 1 and 2 must be adjacent and in that order.** The argument is the
> juxtaposition: opposite court distributions, identical health gradients. Split
> them across tabs and the dashboard stops making a point.



### Filters

Add exactly two, in a single row at the top:

1. **City** — Single Value (dropdown), "All" enabled. Apply to *all sheets using
  this data source*.
2. **Income quartile** — Multiple Values (dropdown). Apply to Sheets 1, 4, 5, 7.

> **Resist adding more.** Every additional filter is a request that the reader do
> your analytical work. A narrative dashboard should have a default view that
> already makes the point; filters are for verifying it, not discovering it.



### Filter action — make the maps interrogable

Dashboard → Actions → Add Action → **Filter**:

- Source: Sheet 3 (choropleth)
- Target: Sheet 7 (neighborhood table)
- Run on: **Select**
- Clearing the selection: Show all values

Now clicking a tract on the map filters the detail table to it. This is what lets
a skeptical reader check any specific place you name.

---



## 12. Titles and captions — write these deliberately

The dashboard title should state the finding, not the topic.

**Title:**

> The Court Was Never the Constraint

**Standfirst:**

> Atlanta and Chicago built basketball courts on opposite theories of who
> deserves public space. Neither theory changed who plays.

**Caption under Sheets 1+2 (the pivot of the whole thing):**

> Chicago's poorest neighborhoods have roughly twice the court density of its
> wealthiest. Atlanta's have slightly fewer. Yet physical inactivity falls just
> as steeply with income in both cities — 37% to 13% in Chicago, 31% to 14% in
> Atlanta. Two opposite distribution strategies, one identical outcome.

**Footer — methods (do not skip this):**

> **Method.** Court locations from OpenStreetMap via Overpass API. Health
> estimates from CDC PLACES 2025 (model-based small-area estimates, not direct
> measurement). Income, poverty and race from ACS 2023 5-year estimates. Tracts
> from Census TIGER 2025.
>
> Chicago is restricted to city limits (781 tracts); the court export covers the
> city, and 97.5% of mapped courts fall inside it. Atlanta covers Fulton and
> DeKalb counties (530 tracts). Income quartiles are computed within each city.
>
> Correlations reported are Spearman's ρ. With 69–77% of tracts having no court,
> Pearson's r is distorted by outliers — in Atlanta it reported +0.157 (p<0.001)
> against poverty where Spearman found −0.001 (p=0.98).
>
> **Limitations.** OpenStreetMap depends on volunteer mapping and likely
> undercounts courts, plausibly more so in lower-income areas — which would make
> the reported pattern conservative, not overstated. Court attributes are sparsely
> recorded (see "What nobody records"). Two cities is a comparison, not a national
> claim.

---



## 13. Formatting pass

Do this last, all at once:

- **Font:** one family throughout. Titles 14–16pt bold, body 10–11pt, captions 9pt italic
- **Gridlines:** `#e5e5e3`, thin. Remove all vertical gridlines on bar charts
- **Borders:** remove sheet borders and shading; use whitespace to separate
- **Zero lines:** keep on bar charts, remove elsewhere
- **Axis titles:** delete any that repeat the sheet title
- **Tooltips:** remove Tableau's default "Sheet 1" header from every one
- **Null handling:** Map → Edit Location → unknown values → hide the indicator

---



## 14. Pre-publication checklist

- [ ] Every rate uses `Courts per 10k (aggregate)`, never `AVG([Courts Per 10k])`
- [ ] `income_q = "nan"` excluded on every sheet
- [ ] Race bars grouped, never stacked, with the ACS caption visible
- [ ] Sheet 5 and 6 state their sample sizes on the sheet
- [ ] Chicago labeled "city limits" everywhere it appears
- [ ] Methods footer present and readable without scrolling past it
- [ ] Tooltips show raw counts alongside every rate
- [ ] Colors match the article's static figures exactly
- [ ] Tested at 100% zoom and on a phone-width viewport
- [ ] Every number cross-checked against `notebooks/visualizations.ipynb`

---



## 15. Headline numbers — cross-check against these


| Metric                         | Atlanta       | Chicago       |
| ------------------------------ | ------------- | ------------- |
| Tracts                         | 530           | 781           |
| Courts                         | 191           | 387           |
| Tracts with no court           | 77%           | 69%           |
| Q1 courts per 10k              | 1.08          | **2.11**      |
| Q4 courts per 10k              | **1.55**      | 1.08          |
| Q1/Q4 ratio                    | 0.69          | 1.96          |
| Spearman ρ (density vs income) | +0.10 (ns)    | −0.15         |
| Inactivity Q1 → Q4             | 31.1% → 13.8% | 37.0% → 13.4% |
| Lighting recorded              | 9%            | 4%            |


If a sheet disagrees with this table, the sheet is wrong. Regenerate the source
data from `notebooks/visualizations.ipynb`, which prints these values in its final
cell.