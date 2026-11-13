# Inspection of the saved 70% / 50-station network

**Inspection only:** the selected network, geographic optimization, eligibility and completeness methodology are unchanged. No replacement is proposed. Every day in 1976–2025 is weighted equally; no recent/historical weighting or missing-day fill is applied.

## Definitions and source availability

- Review numbers follow ascending full-precision historical completeness, then station ID; these are the numbers on the map. Original optimization selection order is retained in the CSV.
- Primary nearby counts/highest completeness use the **3,992 candidates eligible at 70%** from the frozen 1976–2025 analysis, excluding the station itself. Other selected stations would count if within range; the network’s minimum separation is about 916 km, so none are within 250 km. Secondary columns also report the full 5,243 pre-threshold candidate pool.
- Distances are inclusive great-circle radii on the same 6,371.0088-km sphere as the geographic analysis. Nearby station IDs are not merged even if coordinates coincide. No political borders restrict the search.
- A complete day requires recorded TMAX and TMIN, neither missing (`-9999`), each with blank QFLAG. Missing months/elements count as incomplete. Longest-gap dates are inclusive and restricted to 1976-01-01 through 2025-12-31. If equal-length maxima occur, the main table displays the earliest; every tied maximum is in longest-gaps.csv.
- Observed first/last years below are derived from any nonmissing element values in the entire cached `.dly` file, including outside 1976–2025 and values carrying QC flags. The CSV separately preserves original inventory endpoint years and QC-valid first/last years. Endpoints do not prove continuity.
- All **50/50** canonical cached source files were available and matched their original source-provenance hashes; no fresh downloads were made. Unknown elevations: **0**. Inventory-versus-file endpoint mismatches: **0** stations (details in endpoint-checks.csv). A blank nearby maximum means no other candidate in that radius, not 0% completeness.
- No substitution is applied in this inspection. The provisional rule is the arithmetic mean of the ten most recent valid same-month/day observations from the same station in preceding years; see the [decision log](../../../../docs/decisions.md#provisional-same-calendar-date-substitution). Preceding calendar days, substituted values and future years are not used. Station moves, source equivalence, climatic representativeness and replacement coverage effects are not evaluated.

## Complete station table

Nearby entries are **other-candidate count / highest historical completeness**. All percentages describe paired-valid days over the same 18,263-day window. Elevation is metres; coordinates are degrees.

| No. | ID / station | Country | Latitude, longitude | Elevation | Complete | Incomplete days | Longest gap: days; start → end | TMAX observed years | TMIN observed years | Within 50 km | Within 100 km | Within 250 km |
|---:|---|---|---|---:|---:|---:|---|---|---|---:|---:|---:|
| 1 | AYM00089611 / CASEY | Antarctica | -66.2830, 110.5170 | 41.0 | 70.37% | 5412 | 352; 2015-03-11 → 2016-02-25 | 1969–2026 | 1969–2026 | 0 / — | 0 / — | 0 / — |
| 2 | IN001020700 / PBO ANANTAPUR | India | 14.5830, 77.6330 | 364.0 | 71.17% | 5265 | 32; 1976-11-18 → 1976-12-19 | 1961–2026 | 1961–2026 | 0 / — | 0 / — | 1 / 71.84% |
| 3 | UV000065516 / BOROMO | Burkina Faso | 11.7500, -2.9330 | 271.0 | 72.19% | 5079 | 158; 2019-02-08 → 2019-07-15 | 1973–2026 | 1973–2026 | 0 / — | 0 / — | 0 / — |
| 4 | AYM00088963 / BASE ESPERANZA | Antarctica | -63.4000, -56.9830 | 24.0 | 72.67% | 4991 | 365; 2005-01-01 → 2005-12-31 | 1961–2026 | 1961–2026 | 0 / — | 1 / 70.14% | 1 / 70.14% |
| 5 | MXM00076773 / HUAJUAPAN DE LEON (DGE) | Mexico | 17.8000, -97.7667 | 1583.7 | 72.73% | 4980 | 1514; 2005-06-02 → 2009-07-24 | 1976–2026 | 1976–2026 | 0 / — | 0 / — | 1 / 87.37% |
| 6 | NG000001075 / BIRNI N'KONNI | Niger | 13.8000, 5.2500 | 272.0 | 72.79% | 4969 | 646; 1997-07-24 → 1999-04-30 | 1938–2026 | 1938–2026 | 0 / — | 0 / — | 0 / — |
| 7 | SF000068296 / SKUKUZA | South Africa | -24.9830, 31.6000 | 271.0 | 72.88% | 4953 | 1187; 2005-09-16 → 2008-12-15 | 1960–2026 | 1960–2026 | 0 / — | 0 / — | 0 / — |
| 8 | MO000060195 / MIDELT | Morocco | 32.6800, -4.7300 | 1508.0 | 73.60% | 4822 | 152; 1979-09-21 → 1980-02-19 | 1965–2026 | 1965–2026 | 0 / — | 0 / — | 0 / — |
| 9 | ITW00033126 / SIGONELLA | Italy | 37.4000, 14.9167 | 31.1 | 73.70% | 4803 | 669; 1985-05-01 → 1987-02-28 | 1960–2026 | 1960–2026 | 0 / — | 0 / — | 0 / — |
| 10 | AYM00089564 / MAWSON | Antarctica | -67.6000, 62.8670 | 16.0 | 74.39% | 4678 | 328; 2015-03-12 → 2016-02-02 | 1954–2026 | 1954–2026 | 0 / — | 0 / — | 0 / — |
| 11 | MG000044259 / CHOIBALSAN | Mongolia | 48.0830, 114.5500 | 747.0 | 74.51% | 4655 | 164; 2022-11-13 → 2023-04-25 | 1956–2026 | 1956–2026 | 0 / — | 0 / — | 0 / — |
| 12 | CHM00055578 / XIGAZE | China | 29.2500, 88.8830 | 3837.0 | 80.00% | 3653 | 374; 2016-11-15 → 2017-11-23 | 1955–2026 | 1955–2026 | 0 / — | 0 / — | 0 / — |
| 13 | MG000044212 / ULAAN-GOM | Mongolia | 49.8000, 92.0800 | 936.0 | 81.35% | 3406 | 31; 1978-01-01 → 1978-01-31 | 1957–2026 | 1957–2026 | 0 / — | 0 / — | 1 / 82.19% |
| 14 | NZ000093417 / PARAPARAUMU AWS | New Zealand | -40.9000, 174.9830 | 7.0 | 82.54% | 3189 | 11; 2007-11-05 → 2007-11-15 | 1972–2026 | 1972–2026 | 0 / — | 0 / — | 0 / — |
| 15 | SF000068712 / CAPE COLUMBINE | South Africa | -32.8330, 17.8500 | 67.0 | 82.58% | 3181 | 714; 2005-10-26 → 2007-10-09 | 1959–2026 | 1959–2026 | 0 / — | 0 / — | 0 / — |
| 16 | CAN02303685 / SHEPHERD BAY A | Canada | 68.8167, -93.4333 | 42.7 | 82.77% | 3146 | 1003; 2023-04-04 → 2025-12-31 | 1957–2026 | 1957–2026 | 0 / — | 0 / — | 0 / — |
| 17 | TH000048462 / ARANYAPRATHET | Thailand | 13.7000, 102.5830 | 49.0 | 84.35% | 2859 | 57; 2013-12-20 → 2014-02-14 | 1951–2026 | 1951–2026 | 0 / — | 0 / — | 0 / — |
| 18 | TX000038750 / ESENGYLY | Turkmenistan | 37.4667, 53.6331 | -22.0 | 85.21% | 2702 | 6; 1999-06-24 → 1999-06-29 | 1926–2026 | 1926–2026 | 0 / — | 0 / — | 0 / — |
| 19 | MP000061974 / AGALEGA | Mauritius | -10.4330, 56.7500 | 3.0 | 85.37% | 2671 | 197; 2021-01-26 → 2021-08-10 | 1951–2026 | 1951–2026 | 0 / — | 0 / — | 0 / — |
| 20 | CAN01093474 / HIXON | Canada | 53.5314, -122.6994 | 551.0 | 86.04% | 2549 | 1000; 2020-12-20 → 2023-09-15 | 1970–2026 | 1970–2026 | 0 / — | 1 / 82.28% | 2 / 82.28% |
| 21 | BOM00033038 / VASILEVICI | Belarus | 52.2500, 29.8331 | 142.0 | 86.71% | 2428 | 134; 2011-06-10 → 2011-10-21 | 1914–2026 | 1891–2026 | 0 / — | 0 / — | 0 / — |
| 22 | VQW00011624 / HENRY E ROHLSEN AP | Virgin Islands [United States] | 17.6997, -64.8125 | 14.0 | 87.73% | 2240 | 505; 1990-07-11 → 1991-11-27 | 1951–2026 | 1951–2026 | 0 / — | 1 / 91.26% | 13 / 99.98% |
| 23 | CHM00050788 / FUJIN | China | 47.2330, 131.9830 | 65.0 | 87.95% | 2201 | 726; 2015-12-01 → 2017-11-25 | 1952–2026 | 1952–2026 | 0 / — | 0 / — | 0 / — |
| 24 | CHM00057799 / JIAN | China | 27.1170, 114.9670 | 78.0 | 88.27% | 2143 | 374; 2016-11-15 → 2017-11-23 | 1951–2026 | 1951–2026 | 0 / — | 0 / — | 1 / 93.95% |
| 25 | CHM00056951 / LINCANG | China | 23.9500, 100.2170 | 1503.0 | 88.57% | 2088 | 459; 2016-11-15 → 2018-02-16 | 1953–2026 | 1953–2026 | 0 / — | 0 / — | 1 / 88.56% |
| 26 | ASN00014401 / WARRUWI | Australia | -11.6502, 133.3796 | 19.2 | 88.63% | 2077 | 82; 1983-11-26 → 1984-02-15 | 1966–2026 | 1966–2026 | 0 / — | 0 / — | 1 / 83.58% |
| 27 | RSM00020982 / VOLOCHANKA | Russia | 70.9700, 94.5000 | 37.0 | 88.90% | 2027 | 696; 2019-07-01 → 2021-05-26 | 1936–2026 | 1936–2026 | 0 / — | 0 / — | 0 / — |
| 28 | TI000038954 / KHOROG | Tajikistan | 37.5000, 71.5000 | 2077.0 | 89.02% | 2006 | 61; 1976-11-01 → 1976-12-31 | 1910–2026 | 1910–2026 | 0 / — | 0 / — | 1 / 83.93% |
| 29 | KZ000035406 / TAIPAK | Kazakhstan | 49.0500, 51.8667 | 2.0 | 89.03% | 2003 | 17; 2008-10-13 → 2008-10-29 | 1927–2026 | 1925–2026 | 0 / — | 0 / — | 1 / 89.30% |
| 30 | KZ000035796 / BALHASH | Kazakhstan | 46.8000, 75.0831 | 350.0 | 89.40% | 1936 | 33; 2020-06-29 → 2020-07-31 | 1936–2026 | 1936–2026 | 0 / — | 0 / — | 0 / — |
| 31 | CAN05050920 / FLIN FLON | Canada | 54.7667, -101.8833 | 320.0 | 91.27% | 1595 | 689; 2021-08-23 → 2023-07-12 | 1927–2026 | 1927–2026 | 0 / — | 0 / — | 0 / — |
| 32 | GL000004320 / DANMARKSHAVN | Greenland [Denmark] | 76.7700, -18.6700 | 12.0 | 91.51% | 1550 | 129; 1981-06-24 → 1981-10-30 | 1958–2026 | 1958–2026 | 0 / — | 0 / — | 0 / — |
| 33 | RSM00021931 / JUBILEJNAJA | Russia | 70.7700, 136.2200 | 23.0 | 92.15% | 1433 | 81; 1997-03-16 → 1997-06-04 | 1936–2026 | 1936–2026 | 0 / — | 0 / — | 0 / — |
| 34 | RSM00032389 / KLJUCHI | Russia | 56.3167, 160.8331 | 28.0 | 92.34% | 1399 | 180; 2020-05-12 → 2020-11-07 | 1914–2026 | 1914–2026 | 0 / — | 0 / — | 0 / — |
| 35 | ASN00015602 / JERVOIS | Australia | -22.9494, 136.1442 | 328.0 | 92.81% | 1313 | 107; 1979-12-16 → 1980-03-31 | 1967–2026 | 1967–2026 | 0 / — | 0 / — | 1 / 99.82% |
| 36 | GL000004360 / TASIILAQ | Greenland [Denmark] | 65.5997, -37.6331 | 50.0 | 93.01% | 1276 | 144; 2024-11-01 → 2025-03-24 | 1897–2026 | 1894–2026 | 0 / — | 0 / — | 0 / — |
| 37 | RSM00024738 / SUNTAR | Russia | 62.1500, 117.6500 | 131.0 | 93.04% | 1271 | 11; 2021-08-08 → 2021-08-18 | 1936–2026 | 1936–2026 | 0 / — | 0 / — | 0 / — |
| 38 | USC00260438 / ARTHUR 4NW | United States | 40.7808, -115.1853 | 1908.0 | 93.04% | 1271 | 93; 1976-06-01 → 1976-09-01 | 1925–2026 | 1963–2026 | 0 / — | 3 / 100.00% | 22 / 100.00% |
| 39 | USC00406619 / NORRIS | United States | 36.2131, -84.0603 | 338.3 | 93.66% | 1157 | 106; 1981-04-01 → 1981-07-15 | 1935–2026 | 1935–2026 | 1 / 99.99% | 13 / 99.99% | 93 / 100.00% |
| 40 | RSM00028275 / TOBOLSK | Russia | 58.1500, 68.2500 | 49.0 | 93.80% | 1133 | 31; 2008-03-01 → 2008-03-31 | 1900–2026 | 1887–2026 | 0 / — | 0 / — | 0 / — |
| 41 | RSM00022602 / REBOLY | Russia | 63.8200, 30.8200 | 180.0 | 94.35% | 1031 | 53; 1996-12-20 → 1997-02-10 | 1910–2026 | 1910–2026 | 0 / — | 2 / 99.87% | 13 / 99.98% |
| 42 | CHM00052787 / WUSHAOLING | China | 37.2000, 102.8670 | 3044.0 | 95.15% | 885 | 10; 2024-11-13 → 2024-11-22 | 1951–2026 | 1951–2026 | 0 / — | 0 / — | 1 / 88.82% |
| 43 | ISE00105694 / BET DAGAN | Israel | 32.0000, 34.7994 | 30.0 | 96.75% | 594 | 14; 1993-07-08 → 1993-07-21 | 1962–2026 | 1962–2026 | 0 / — | 0 / — | 1 / 94.76% |
| 44 | USC00416104 / MT LOCKE | United States | 30.6711, -104.0231 | 2069.6 | 97.27% | 498 | 50; 1981-01-20 → 1981-03-10 | 1935–2026 | 1935–2026 | 1 / 84.80% | 1 / 84.80% | 13 / 100.00% |
| 45 | USW00026529 / TANANA AP | United States | 65.1730, -152.1067 | 68.6 | 98.02% | 362 | 61; 2025-11-01 → 2025-12-31 | 1902–2026 | 1901–2026 | 0 / — | 0 / — | 7 / 100.00% |
| 46 | USC00219170 / WORTHINGTON 2 NNE | United States | 43.6453, -95.5803 | 477.9 | 98.05% | 356 | 92; 2009-05-01 → 2009-07-31 | 1971–2026 | 1971–2026 | 5 / 97.85% | 22 / 100.00% | 99 / 100.00% |
| 47 | ASN00007045 / MEEKATHARRA AIRPORT | Australia | -26.6136, 118.5372 | 517.0 | 99.04% | 175 | 7; 1984-12-31 → 1985-01-06 | 1948–2026 | 1948–2026 | 0 / — | 0 / — | 0 / — |
| 48 | GMM00010704 / BERUS | Germany | 49.2653, 6.6878 | 363.0 | 99.38% | 114 | 12; 2001-05-05 → 2001-05-16 | 1951–2026 | 1951–2026 | 5 / 100.00% | 16 / 100.00% | 82 / 100.00% |
| 49 | CAN07060400 / BAGOTVILLE A | Canada | 48.3333, -71.0000 | 159.1 | 99.63% | 68 | 2; 1992-12-09 → 1992-12-10 | 1942–2026 | 1942–2026 | 0 / — | 0 / — | 1 / 96.39% |
| 50 | ASN00048027 / COBAR MO | Australia | -31.4840, 145.8294 | 260.0 | 99.71% | 53 | 12; 2019-03-01 → 2019-03-12 | 1962–2026 | 1962–2026 | 0 / — | 0 / — | 4 / 97.37% |

[Full CSV with separate fields, inventory/QC-valid endpoints and both neighbor pools](station-review.csv). [Numbered map](numbered-network-map.png). [Completeness histogram](completeness-histogram.png).

## Longest incomplete gaps

Historical completeness ranges from **70.37%** to **99.71%**, median **88.60%**. **15** stations have a longest gap of at least 365 days; **4** have one of at least 730 days. These are absent/invalid paired days, not necessarily total station outages.

| No. | Station | Longest gap | Inclusive start | Inclusive end |
|---:|---|---:|---|---|
| 5 | MXM00076773 / HUAJUAPAN DE LEON (DGE) | 1514 days | 2005-06-02 | 2009-07-24 |
| 7 | SF000068296 / SKUKUZA | 1187 days | 2005-09-16 | 2008-12-15 |
| 16 | CAN02303685 / SHEPHERD BAY A | 1003 days | 2023-04-04 | 2025-12-31 |
| 20 | CAN01093474 / HIXON | 1000 days | 2020-12-20 | 2023-09-15 |
| 23 | CHM00050788 / FUJIN | 726 days | 2015-12-01 | 2017-11-25 |
| 15 | SF000068712 / CAPE COLUMBINE | 714 days | 2005-10-26 | 2007-10-09 |
| 27 | RSM00020982 / VOLOCHANKA | 696 days | 2019-07-01 | 2021-05-26 |
| 31 | CAN05050920 / FLIN FLON | 689 days | 2021-08-23 | 2023-07-12 |
| 9 | ITW00033126 / SIGONELLA | 669 days | 1985-05-01 | 1987-02-28 |
| 6 | NG000001075 / BIRNI N'KONNI | 646 days | 1997-07-24 | 1999-04-30 |
| 22 | VQW00011624 / HENRY E ROHLSEN AP | 505 days | 1990-07-11 | 1991-11-27 |
| 25 | CHM00056951 / LINCANG | 459 days | 2016-11-15 | 2018-02-16 |
| 12 | CHM00055578 / XIGAZE | 374 days | 2016-11-15 | 2017-11-23 |
| 24 | CHM00057799 / JIAN | 374 days | 2016-11-15 | 2017-11-23 |
| 4 | AYM00088963 / BASE ESPERANZA | 365 days | 2005-01-01 | 2005-12-31 |

[All longest gaps, including ties](longest-gaps.csv); [every incomplete run](incomplete-runs.csv).

## Nearby substantially more complete observations

**Inspection flag:** another 70%-eligible candidate within 100 km has at least **5 percentage points** higher historical paired completeness. This is a descriptive flag, not a new eligibility rule or a proposed replacement. Completeness gains use exact day counts before display rounding. Every flagged candidate is listed in the companion CSV. No geographic optimization, replacement coverage calculation, climate equivalence test or site-history assessment has been performed.

| No. | Selected station | Selected completeness | Highest-completeness nearby candidate | Distance | Nearby completeness | Gain | Number meeting flag |
|---:|---|---:|---|---:|---:|---:|---:|
| 38 | USC00260438 / ARTHUR 4NW | 93.04% | USW00024121 / ELKO RGNL AP | 50.8 km | 100.00% | 6.96 pp | 1 |
| 39 | USC00406619 / NORRIS | 93.66% | USW00013891 / KNOXVILLE AP | 44.4 km | 99.99% | 6.33 pp | 4 |
| 41 | RSM00022602 / REBOLY | 94.35% | FIE00145452 / VALTIMO KK | 99.2 km | 99.87% | 5.52 pp | 2 |

**3 of 50 selected stations** meet the inspection flag. [Flagged stations](stations-with-nearby-higher-completeness.csv); [all qualifying nearby differences](substantially-more-complete-neighbors-within-100km.csv); [all candidate neighbors within 250 km](nearby-candidates.csv).

## Existing geographic coverage, for reference

Copied from the committed facility-location comparison row; no new geographic selection or optimization was run. Land statistics use all 3,588,564 equal-area locations, including Antarctica. NN is the distance to each selected station’s nearest other selected station.

| Metric | Distance |
|---|---:|
| Mean land-to-nearest station | 1,219.78 km |
| Median land distance | 851.84 km |
| Land distance p90 | 2,638.70 km |
| Land distance p95 | 3,508.71 km |
| Minimum selected-station NN distance | 916.11 km |
| Median selected-station NN distance | 1,400.83 km |
| Selected-station NN distance p90 | 2,033.88 km |

[Original geographic statistics row](geographic-reference.csv). The original trial is exploratory, not a final adopted network.

## Validation and reproducibility

The selected input and frozen candidate CSVs are hash-checked, all daily files are checked against the original per-station provenance, and daily paired counts/longest lengths reconcile exactly with the saved metrics and the existing daily-analysis function. Neighbor counts reconcile across radii and candidate pools; maxima exclude self and the 5-pp flags are checked with integer day counts. Map numbers correspond to exactly 50 unique rows. No missing values are silently filled. Validation and source/output hashes are saved with this report.

Read-only inspection code and tests: `analysis/network_review/`. Original input network: `data/processed/geography/facility-location/networks/network-70pct-50.csv`. Source metadata are frozen as of the saved November 2026 run; dates and coordinates are not a history of station moves.
