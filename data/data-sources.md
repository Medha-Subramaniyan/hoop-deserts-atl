# Data Sources

This project merges four datasets to analyze the relationship between basketball
court access, socioeconomic conditions, and public health outcomes in Atlanta
(Fulton & DeKalb counties, GA).

### 1. Basketball Court Locations

- **File:** `overpassturbo_export.geojson`
- **Source:** [OpenStreetMap](https://www.openstreetmap.org) via the [Overpass API](https://overpass-api.de/)
- **How obtained:** Queried via [Overpass Turbo](https://overpass-turbo.eu/) for all
nodes/ways/relations tagged `sport=basketball` within the administrative
boundary of Atlanta, GA. Exported as GeoJSON.
- **Fields of interest:** `leisure`, `sport`, `surface`, `lit` (lighting),
point geometry (or centroid for way/relation features)
- **Known limitations:** OSM coverage depends on volunteer mapping and may
undercount informal or unmapped courts, particularly in lower-income areas —
a limitation worth flagging directly in the analysis rather than treating
the court count as ground truth.



### 2. Income, Poverty & Race (ACS 5-Year Estimates)

- **File:** `censusgov.json`
- **Source:** [U.S. Census Bureau, American Community Survey (ACS) 5-Year
Estimates, 2023](https://www.census.gov/programs-surveys/acs), via the
[Census API](https://www.census.gov/data/developers/data-sets/acs-5year.html)
- **How obtained:** Pulled programmatically using a Census API key, filtered
to all tracts in Fulton County (FIPS 121) and DeKalb County (FIPS 089), GA
(state FIPS 13).
- **Variables:**

  | Code                                          | Description                                                          |
  | --------------------------------------------- | -------------------------------------------------------------------- |
  | `B19013_001E`                                 | Median household income                                              |
  | `B17001_002E` / `B17001_001E`                 | Population below poverty line / total (used to compute poverty rate) |
  | `B01003_001E`                                 | Total population                                                     |
  | `B02001_001E` / `B02001_002E` / `B02001_003E` | Total / White alone / Black or African American alone                |
  | `B03003_003E`                                 | Hispanic or Latino population                                        |

- **Join key:** 11-digit tract GEOID (state + county + tract, zero-padded)



### 3. Community Health Outcomes

- **File:** `PLACES__Local_Data_for_Better_Health__Census_Tract_Data__2025_release_20260811.csv`
- **Source:** [CDC PLACES: Local Data for Better Health](https://www.cdc.gov/places/),
2025 release, Census Tract level
- **How obtained:** Downloaded directly from the CDC PLACES data portal,
pre-filtered to GA tracts within Fulton and DeKalb counties.
- **Format:** Long format — one row per (tract, measure) pair. Pivoted on
`MeasureId` to get one row per tract with each health measure as a column.
- **Key measures used:**

  | MeasureId | Description                    |
  | --------- | ------------------------------ |
  | `LPA`     | Physical inactivity prevalence |
  | `OBESITY` | Obesity prevalence             |
  | `MHLTH`   | Frequent mental distress       |

- **Join key:** `LocationID` (matches Census tract GEOID)
- **Note:** These are model-based small-area estimates, not direct
measurements — per CDC guidance, not intended for evaluating specific local
interventions, only for identifying broad patterns.



### 4. Census Tract Boundaries

- **Files:** `tl_2025_13_tract.shp` (+ `.dbf`, `.shx`, `.prj`, `.cpg`)
- **Source:** U.S. Census Bureau, [TIGER/Line Shapefiles, 2025](https://www2.census.gov/geo/tiger/TIGER2025/TRACT/)
- **How obtained:** Downloaded `tl_2025_13_tract.zip` (Georgia, state FIPS
  1. and filtered to `COUNTYFP` in `['121', '089']` for Fulton and DeKalb.
- **Purpose:** Enables spatial point-in-polygon joins between court locations
and tracts, and provides polygon geometry for choropleth mapping.
- **Join key:** `GEOID`
- **Note:** Boundary vintage (2025) is one year ahead of the ACS estimate
vintage (2023 5-year); GEOIDs were spot-checked for mismatches from tract
boundary changes before joining.

