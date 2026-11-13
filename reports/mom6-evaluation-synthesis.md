# How West Coast colleagues have used and evaluated MOM6-NEP10k so far

*Synthesis for issue [#4](https://github.com/nmfs-opensci/om-fish-2027/issues/4). Draft for review, 2026-11-12.*

## Summary

Five people are working with the CEFI MOM6-NEP10k hindcast for the California Current, in four GitHub repositories and in work that so far exists only in slides: Brooke Hawkins, Megan Feddern, Isaac Schroeder, Owen Liu and Darren Pilcher. All of the work uses the **monthly hindcast** (1993 to mid-2025); none of it uses the seasonal forecast yet. The comparisons fall into four groups:

- **Sea surface temperature against OISST** (Brooke, and Isaac in the slides). This is the clearest "it works" result: R = 0.97, bias +0.14 °C and RMSE 0.70 °C over 1993–2025 for the CCIEA box.
- **Indices built from MOM6 against the same indices built from another model.** These are the habitat compression index (HCI) against UCSC ROMS (Isaac and Owen, separately) and groundfish life-stage indices against ROMS (hake) and GLORYS (yellowtail; Megan and Brooke, and a tech memo).
- **Subsurface heat content against an observational reanalysis** (Owen, CORA). This is run as a parallel analysis; no agreement statistic is reported yet.
- **Biogeochemistry against ship and glider observations** (Darren, slides only).

Where the authors themselves describe agreement, the pattern is consistent. **Temperature-based quantities agree well**: SST, the HCI and the yellowtail spawning-season temperature. **Mixed layer depth and sea surface height agree moderately** with ROMS (r ≈ 0.7–0.87). **Velocity, transport and eddy kinetic energy agree weakly or not at all** (r from −0.27 to 0.69). **Subsurface oxygen and aragonite saturation are biased high**, which the author ties to a known low-productivity bias in this release.

The same steps are coded separately in each repository and language, in different ways. Examples are pulling MOM6 from Earthmover, distance-from-coast masks, layer-thickness reconstruction, the HCI and area weighting. Two people have each built a MOM6 HCI with different settings. [Appendix C](#appendix-c-common-tasks-and-the-tutorials-they-suggest) turns these shared tasks into a list of candidate tutorials.

### At a glance: who is comparing what

| Who | What they built from MOM6 | Compared against | Code reviewed? |
|---|---|---|---|
| Brooke Hawkins | SST maps, time series and seasonal anomaly maps (CCIEA box) | NOAA OISST v2.1 | Yes, `mom6-based-esr-indices` |
| Isaac Schroeder | HCI (4 regions) | OISST and UCSC ROMS | **No.** The MOM6 HCI is in the slides only; the repo holds the operational ROMS/OISST pipeline |
| Owen Liu | Ocean heat content (6 depth layers) and heatwave area; MOM6 HCI (3 regions) | CORA reanalysis (OHC); IEA HCI from ROMS (HCI) | Yes, `subsurface_heatwaves` |
| Megan Feddern (with Brooke) | Hake and yellowtail life-stage indices: MLD, SSH, temperature, velocity/transport, EKE | ROMS (hake), GLORYS (yellowtail), an earlier MOM6 workflow | Yes, `mom6-based-groundfish-indices` |
| Diandre' Richie, Megan Feddern, Brooke Hawkins | Yellowtail indices, 1998–2021 | GLORYS | **No.** Tech memo, cited in the slides |
| Darren Pilcher | O₂, Ω_arag and temperature at Newport Line stations; surface NO₃ | Newport Hydrographic Line; WCOA cruises | **No.** Slides only |

### Data access: everyone with code uses the Earthmover Icechunk store

All three repositories with MOM6 code read the same Earthmover repository, **`NOAA-PMEL/cefi-nep-hindcast-monthly`**, the cloud-native (Icechunk/Zarr) copy of the monthly hindcast. None of them downloads files from the CEFI THREDDS portal for the model fields. They reach the store in three ways:

- **Brooke** opens it natively in Python (`arraylake` client → read-only Icechunk session → `xr.open_zarr`). She reads both the `raw` native grid and the `regrid` groups (`esr@4aa6ceb:sst_anomaly/mom6/sst-anomaly.ipynb`, cell 4). The slides offer this notebook as a pattern that "could be adopted to other variables and model releases and forecast" (Slides, p. 7).
- **Megan** uses the same native access from R, calling Python through reticulate (`groundfish@e279952:PacificHake/Hake_Variables.qmd`).
- **Owen** uses Earthmover's **OPeNDAP (DAP2) endpoint** for the same store from R `ncdf4`, which needs no Python and no login (`heatwaves@bc80f0a:code/download_monthly_thetao.R`).

How Isaac and Darren reached MOM6 is not known. All three read the store's `main` branch rather than a fixed snapshot or tag, so the data they get changes when a new release is published (see (b) and question 5).

**The Earthmover store is a draft, not yet the production version.** The current store was built from release r20250912 (the release Brooke records); the newest CEFI release is r20260701. The draft data has some idiosyncrasies and errors, and the repository owners have each worked around them:

- **Duplicated months.** Jan–Jun 2025 appear twice in some groups. Brooke drops the duplicates before comparing (`sst-comparison.ipynb`, cell 5).
- **Static fields.** Bathymetry and similar grid information are not taken from the store. Megan downloads them separately from THREDDS (`STATIC/README.md`).
- **Slow subsurface reads.** Reading 3-D fields is slow. Owen downloads one year at a time to local files and names data access as his main bottleneck.
- **Conventions handled by hand:** 0–360 longitude, mid-month time stamps shifted to the first of the month, and dimension renaming to fit existing scripts.

Results computed from the draft store will be worth re-checking once the production version is available, especially anything that depends on the 2025 months or on the release.

[Appendix B](#appendix-b-minimal-access-patterns) gives a minimal snippet for each route, with how each was tested.

Sources: the four repositories at the commits listed in the [appendix](#appendix-a-what-was-reviewed), and the deck *MOM6 / ESR Progress Update*, CC ESR Seaside Chat, 2026-10-30 (cited below as **"Slides, p. N"**). 

---

## (a) What each group did

Citations use `repo@commit:path`. The repository short names are defined in the appendix.

### a1. SST comparison and ESR anomaly maps: Brooke Hawkins (`esr`)

**Purpose.** The repository checks whether MOM6 can stand in for OISST in an existing CCIEA ESR product: Isaac's seasonal SST anomaly maps for the 2025 mini-ESR (`esr@4aa6ceb:sst_anomaly/mom6/sst-anomaly.ipynb`, cell 0). The slides say the purpose is to "build some confidence" and show MOM6 can slot into existing data workflows, "not suggesting replacing observational data with model product data" (Slides, p. 7).

**MOM6 product.**
- Hindcast release **r20250912**, monthly, from the Earthmover repository `NOAA-PMEL/cefi-nep-hindcast-monthly`, branch `main`.
- Variable `tos` (SST), both **raw** (native curvilinear grid, group `raw/aux1`) and **regrid** (rectilinear).
- Domain 32–48 °N, 128–116.8 °W; period Jan 1993 – Jun 2025 (`sst-anomaly.ipynb`, cells 0, 3, 4).

**Data access.**
- Python: `arraylake` client, then `xr.open_zarr` on a read-only Icechunk session.
- The raw grid is subset by masking `geolat`/`geolon`, the regrid by `.sel` on lat/lon.
- The subset is written to a local netCDF of about 0.03 GB, which is committed through Git LFS (`.gitattributes`).
- Timestamps are shifted to the first of the month and dimensions renamed so that Isaac's OISST plotting script runs unchanged (cell 6).
- The notebook notes that it was developed "with syntax formatting and debugging assistance using Google Gemini and GitHub Copilot" (cell 0).

**Comparison data.** NOAA OISST v2.1 (0.25°), taken from the netCDF that Isaac's pipeline builds from ERDDAP (`oisst/TS_monthly.nc`; source script `oc_cciea:code_gha/SSTspatial/sst_oi_daily_v21_update.py`).

**Methods** (`esr@4aa6ceb:sst_anomaly/sst-comparison.ipynb`):
- Both MOM6 versions are regridded bilinearly onto the OISST grid with xESMF.
- Statistics are cos(latitude) area-weighted: mean, bias, Pearson correlation and RMSE, each computed globally, as a time series and as a map.
- The MOM6 files contained duplicated Jan–Jun 2025 time steps, which are dropped (cell 5).
- The anomaly maps reuse Isaac's script with the climatology set to 1993–2025 for **both** OISST and MOM6, to match the hindcast period. Isaac's operational version uses 1982–present (`sst_anomaly/oisst/contour_noaaoisst_clim_anoms_season.py`, line 89; commit `2c51a3e`).

**Stated findings** (cells 29, 31, 33):
- MOM6 is "slightly warmer (0.14 °C)", "highly correlated (R = 0.97)" and "generally falls within 1 degree" (RMSE = 0.70 °C). Raw and regrid give nearly the same numbers: bias 0.125/0.132, R 0.971/0.972, RMSE 0.708/0.701.
- MOM6 "captures seasonal variability" and is "slightly more variable (higher highs, and lower lows)".
- Spatial pattern: warm bias of about 0.5 °C near Monterey Bay and south of the Channel Islands, cool bias of about −0.3 °C nearshore Washington and around the Channel Islands.
- In contrast to the whole-domain evaluation in Drenkard et al. (2025), which found bias −0.16 °C, R = 1.00 and RMSE 0.28, the CCIEA subdomain "runs warmer rather than cooler".
- The author suggests regridding all products to a common coarser grid in future, and documenting this for new users (cell 33).

**Timeline.**
- Created 2026-06-11.
- July 2026: SST extracted and Isaac's anomaly code adapted.
- Aug–Sep 2026: correlation, then RMSE/bias and area weighting, then written interpretation.
- Sep–Oct 2026: raw vs. regrid comparison.
- Last commit 2026-10-21 (31 commits).
- An unmerged branch `copilot/update-sst-comparison-regridding-method` (`6d08488`, 2026-10-21) adds conservative regridding.

### a2. Groundfish indices: Megan Feddern, with Brooke Hawkins (`groundfish`)

**Purpose.** The repository produces life-stage-specific oceanographic indices for groundfish stock assessments and risk tables: Pacific hake (the indices used in the 2025 hake ecosystem summary) and northern yellowtail rockfish (`groundfish@e279952:PacificHake/README.md`). The slides list as next steps comparisons "between MOM6, ROMS, GLORYS" and an "onramp" for hake, petrale sole, sablefish and yellowtail (Slides, p. 17).

**MOM6 product.**
- Monthly hindcast, **regrid** groups `regrid/main` and `regrid/aux1` on Earthmover `NOAA-PMEL/cefi-nep-hindcast-monthly`, branch `main`. The release is not pinned in the code.
- Variables: `MLD_003`, `ssh`, `thetao`, `uo_rotate`, `vo_rotate` (`PacificHake/Hake_Variables.qmd`).
- Static files come from THREDDS release **r20260701** (`STATIC/README.md`): bathymetry `deptho`, distance-to-coast on the native and regrid grids, and coast angle.
- Each index is defined by a lookup table of months × latitude band × depth range × isobath or distance-from-shore band. Hake, for example, has spawning temperature at 130–500 m, Jan–Mar, 31–36 °N, and the poleward undercurrent at 33.5–34.5 °N, 75–275 m. The slides count **30 variables** from MOM6 (p. 17).
- Output is annual values per index, 1993–2025.

**Data access.**
- An R package (`DESCRIPTION`, `R/*.R`) calls Python through **reticulate** (`arraylake`, `icechunk`, `xarray`, `zarr`), all lazily.
- Masks are aligned to the data with `interp_like(method="nearest")`.
- 3-D means reconstruct layer thicknesses from `z_l` midpoints (`R/annual_mean_3d.R`, lines 20–28). `annual_mean_3d` keeps the thickness weighting commented out (line 150); `annual_mean_3d_depthweighted` applies it.
- Transport and coast angle follow "Mike's MATLAB" code, ported to radians (`R/transport_3D.R`, line 77).
- Climate indices (PDO, NPGO) come from the CCIEA ERDDAP (`R/fetch_erddap_metric.R`).
- An archived note reads "token issue? go to terminal arraylake auth login" (`ARCHIVE/MOM6_variables.qmd`, line 41).

**Comparison data.**
- **Hake:** ROMS annual indices for 1980–2010 and 2011–2021, from CSVs in the repo (`PacificHake/Data_ROMS.for.hake.analysis.mean.*.csv`). Which ROMS configuration produced them is not documented.
- **Yellowtail:** GLORYS indices from CSVs (`Yellowtail/yellowtail_GLORYs.csv`, `Yellowtail/2024Env-annual-yellowtail_GLORYS_UNSTANDARDIZED.csv`), plus "MOM6v2", an earlier Python MOM6 workflow by "Brooke and Roland" (`Yellowtail/yellowtail_MOM6.csv`). That earlier code is not in this repo.

**Methods.** Pearson correlation of z-scored annual series, with figures showing standardized and unstandardized series.
- Hake vs. ROMS is computed on the 1994–2010 overlap (`Hake_Variables.qmd`).
- Yellowtail vs. GLORYS and vs. MOM6v2 is computed on roughly 1993/94–2022/23 (`Yellowtail/Yellowtail.qmd`).

**Stated findings, yellowtail** (`Yellowtail/Yellowtail.qmd`, rendered `Yellowtail/Yellowtail.pdf`, both `86654f1`, 2026-11-06):
- **The new R workflow reproduces the earlier Python MOM6 workflow** (r = 0.986–0.997). The small differences are attributed to different hindcast versions.
- **After a depth-filter bug was fixed** ("depth bins were used to filter the longitudinal extent rather than the depths"), the new and old workflows still correlate at r = 0.70–0.99 once standardized.
- **MOM6 vs. GLORYS:** "all variables are moderately to highly correlated. Although it is surprising Tcop does not have a higher correlation." Only the Tcop value (**0.612**) is printed in the rendered figure.
- **Depth-weighting** changes the temperature indices very little (r = 0.999).
- **Velocity, MOM6 vs. GLORYS:** r = **0.33** (CSTlarv), **0.41** (CSTpjuv), **0.60** (LSTpjuv), "although there is a bias". The author suspects that "some of the poor performing aspects of transport" are related to "moderately different calculations… how distance is projected, or the depth integration".

**Stated findings, hake vs. ROMS** (figures only, no prose):
- `PacificHake/Output/standardized2d.png` (`ac93537`, 2026-11-04):
  - MLD: **0.77** (egg), **0.68** (larv), **0.79** (latelarv), **0.78** (yolk).
  - SSH: **0.87** (Jan–Apr, central), **0.73** (Jan–Apr, south), **0.70** (May–Sep, central), **0.71** (May–Sep, south).
- `PacificHake/standardized3d.png` (`86654f1`, 2026-11-06), EKE:
  - Jan–Apr: **0.69** (central), **0.17** (south).
  - May–Sep: **−0.02** (central), **−0.18** (south).

**Timeline.**
- Created 2026-06-11. Megan's first commits 2026-08-13/14 (README, static files, a "testing code base from Eli" commit).
- Sep 2026: Earthmover/arraylake processing and ERDDAP climate indices.
- Oct 2026: 3-D variables, conversion to a local R package, coast angle, transport, depth weighting, EKE.
- Early Nov 2026: yellowtail comparison and velocity variants. Last commit 2026-11-06 (42 commits).

### a3. CCIEA ocean-conditions pipeline: Isaac Schroeder (`oc_cciea`)

**Purpose.** This is the operational code behind the CCIEA ocean-conditions indicators. It runs on GitHub Actions and covers the HCI, SST spatial anomalies, marine heatwaves, the basin-scale indices, BEUTI/CUTI, dissolved oxygen, the CalCOFI products and the mini-ESR figures (`code_gha/*`, `.github/workflows/*`, 30 workflow files).

**MOM6 in this repository.** A search of `main` and `gh-pages` (file contents and commit messages, for `mom6`, `nep10k` and `cefi`) found **no MOM6 code**. The repository is relevant because:
- it is the **observational and ROMS baseline** that the MOM6 work is compared against. The OISST SST anomaly script `code_gha/miniESR/contour_noaaoisst_clim_anoms_season.py` (`288fe7d`, 2026-06-22) is the one Brooke adapted for MOM6. The ROMS-based HCI comes from `code_gha/HCI_ROMS/`: near-real-time UCSC ROMS 2 m temperature via CeNCOOS OPeNDAP (`nrt_roms_daily_update.py`, line 58); 4 latitude regions, 43.5–48, 40–43.5, 35.5–40 and 30–35.5 °N; thresholds from a 1980–2010 climatology within 75 km of shore (`calc_thresholds_roms_area.py`, lines 10–19).
- Isaac's **MOM6 HCI comparison**, shown in the slides, appears to have been done outside this repository.

**MOM6 HCI comparison, slides only** (Slides, p. 8).
- HCI computed from OISST, UCSC ROMS (2 m) and MOM6 SST for HCI Regions 1–4, 1993–2025.
- Stated: "Generally the comparison between UCSC ROMS and MOM6 is better as you go north" and "the comparison is better for winter and spring". No statistics are given.
- The MOM6 product version, threshold baseline and code are not available for review.

**Timeline.** The repository history starts 2025-11-09; 545 of 729 commits fall in Nov 2025 – Jan 2026, which suggests a migration or rebuild of an existing pipeline (inferred). Activity continues through 2026-10-16. The ROMS HCI pipeline was added in June 2026 ("Using Cencoos opendap instead of UCSC", 2026-06-26).

### a4. Subsurface heatwaves and a MOM6 HCI: Owen Liu (`heatwaves`)

**Purpose.** "Try to use MOM6 data to calculate subsurface heatwaves in the California Current, taking advantage of the new earthmover setup for data access" (`heatwaves@bc80f0a:code/explore_ohc.qmd`). A second notebook builds a MOM6 version of the HCI (`code/make hci.qmd`).

**MOM6 product.**
- Monthly hindcast, **regrid**, from Earthmover `NOAA-PMEL/cefi-nep-hindcast-monthly/main/regrid/main`. The release is not pinned.
- Variables: `thetao` over depth indices 1–36 (0–1000 m), `rhopot0` (for isopycnals), `uo_rotate`, `vo_rotate`.
- Domain 32–48.5 °N, 230–244 °E, cropped to the US EEZ; period 1993–2025.
- Ocean heat content uses ρ = 1026 and cp = 3990 (`code/calculate_ohc.R`, line 74), in 6 layers: 0–5, 0–50, 50–100, 100–250, 250–500 and 500–1000 m.
- An earlier approach tracked temperature on the 1025.5 and 1026.5 kg/m³ isopycnals (`code/explore_subsurface_heatwaves.qmd`, `42a8ab5`).

**Data access.**
- R `ncdf4` against Earthmover's **OPeNDAP (DAP2) endpoint**, with index-based subsetting. Each year is written to a local netCDF via `terra` (`code/download_monthly_thetao.R`; same pattern for `rho` and `u_v`).
- Local data and outputs (`/data`, `*.nc`, `*.tif`) are git-ignored, so the analysis notebooks cannot run from the repository alone.
- The author notes: "The primary bottleneck in the processing is the accessing and downloading of the original data" (`explore_subsurface_heatwaves.qmd`).
- Distance-from-coast masks (75 and 150 km) are computed in R from a coastline polygon (`make hci.qmd`, `check_shear.R`).

**Comparison data.**
- **CORA** (Coriolis Ocean Dataset for Reanalysis) temperature, downloaded 2026-10-01 (`code/process_cora.R`).
- **IEA HCI** downloaded from the CCIEA ERDDAP (`data/hci/cciea_OC_HCI_*.csv`, read in `make hci.qmd`).
- **CUGN** Spray glider Line 90 anomalies (`code/process_cugn.R`) and **Trinidad Head CTD** from ERDDAP (`code/process_TH_temperature.R`) are processed and plotted. No comparison of them with MOM6 was found in the code.

**Methods.**
- OHC z-score anomalies against a monthly climatology, with and without a linear trend.
- Means by latitude bin and HCI region; Hovmöller plots; correlation among regions and depths.
- Heatwave area (cells more than 1 SD above climatology); hotspot frequency.
- Breakpoint models: piecewise-continuous, discontinuous and mean-shift.
- CORA receives "parallel analyses" in `code/explore_cora.qmd`. The MOM6 HCI is compared with the IEA HCI by time series, scatter plot against 1:1 and correlation (`make hci.qmd`, lines 403–404). The correlation values are not saved in the repo.

**Stated findings.**
- **MOM6 HCI vs. IEA HCI** (`make hci.qmd`, `3905844`): "very highly correlated in general, especially the cumulative HCI". The MOM6 HCI "is somewhat lower… at higher HCI values", especially July–November. In cool, good-habitat conditions it "indicates a little less cool habitat". The author offers two possible causes: the different baseline (MOM6 1993–2010 vs. ROMS 1980–2010) or different thresholds. Region 4 is excluded because "the domain of the downloaded MOM6 data do not extend as far south".
- **OHC (MOM6 only)** (Slides, pp. 9–12):
  - A breakpoint around Feb 2014 marks the shift into the "MHW era" for near-surface layers; for 50–250 m the breakpoint comes later in 2014; 250–1000 m shows an increasing trend since at least 2002.
  - The series are more correlated across regions within a depth (~0.85) than across depths within a region (~0.35).
  - The largest regional differences are at 100–250 m.
- **MOM6 vs. CORA:** no agreement result is stated in the code or the slides.

**Timeline.**
- Created 2026-09-03.
- 2026-09-28: OHC and isopycnal heatwaves.
- 2026-10-28: HCI regions, breakpoints, CORA and the MOM6 HCI.
- 2026-11-11: velocity shear, OHC gradients.
- 4 commits in total, so the history shows little of how the work developed.

### a5. Work shown without code in these repositories

**Biogeochemical indices: Darren Pilcher** (Slides, pp. 13–16). MOM6 is compared with the **Newport Hydrographic Line** at NH05 (50 m) and NH25 (150 m), 2005–2025, for dissolved O₂, Ω_aragonite and temperature, as time series and monthly climatologies. Surface NO₃ is compared with **WCOA** cruise data.
- "Model subsurface oxygen is generally biased high and not fully capturing seasonal drawdown"; Ω_arag is "similar… biased high and not fully capturing drawdown".
- "Bias in oxygen and Ω_arag more prominent at deeper depths."
- Surface NO₃: **R = 0.51, RMSE = 8.6, bias = 5.9 µmol/kg**, with "excess surface NO₃ due to iron limitation".
- All of this is "consistent with basin-scale analysis and lower productivity bias". "GFDL updated model with several improvements. Currently waiting on new output."
- No statement is made about temperature agreement at NH05/NH25. Code location and access method are not known.

**Yellowtail indices tech memo: Richie, Feddern, Hawkins** (Slides, p. 18). MOM6-NEP10k vs. GLORYS for yellowtail indices, 1998–2021: "Temperature good, others less so", with "differences from season and model product definitions (e.g. MLD)". The memo itself was not reviewed. The `groundfish` repo's yellowtail comparison (a2) appears to be a re-implementation of the same indices.

---

## (b) Across the work: what is shared and what differs

### Steps each group implements separately

| Step | `esr` (Brooke) | `groundfish` (Megan) | `heatwaves` (Owen) | `oc_cciea` / slides (Isaac) |
|---|---|---|---|---|
| Get MOM6 | Python `arraylake` → Icechunk → local netCDF | R → reticulate → Python `arraylake`, lazy | R `ncdf4` → Earthmover OPeNDAP → local yearly netCDF | not in repo |
| Grid | raw **and** regrid | regrid | regrid | unknown |
| Spatial subset | lat/lon box (raw: mask on `geolat`/`geolon`) | lookup table: months × lat × depth × isobath or distance | bounding box → US EEZ polygon | 4 HCI lat regions, 75/150 km bands (ROMS/OISST) |
| Distance-from-shore / isobath | — | precomputed `dist2coast`, `deptho` from THREDDS r20260701 | computed in R from a coastline polygon | `create_xdis_area_bath_mask_area.py` (for ROMS/OISST) |
| Layer thickness | — | rebuilt from `z_l` midpoints | `diff(c(0, depth_bottom))` | — |
| Area weighting | cos(lat) | cos(lat) for EKE; unweighted horizontal mean for 2-D/3-D indices | cell areas (terra) | cell areas |
| Regridding to compare | xESMF bilinear onto OISST 0.25° | none (index-level comparison) | none (CORA is analysed separately; HCI at index level) | unknown |
| Climatology baseline | 1993–2025 (both products) | z-scored over the overlap | 1993–2010 (HCI); full period (OHC) | 1980–2010 (ROMS HCI) |

**HCI from MOM6 has been built twice**, by Isaac (slides) and by Owen (`make hci.qmd`), apparently independently (inferred: neither references the other). Owen's version uses 3 regions (Region 4 excluded) and a 1993–2010 baseline. Isaac's slide figure shows all 4 regions; his settings are not available.

**SST anomaly maps:** Brooke ported Isaac's OISST script and changed its baseline to 1993–2025. The operational OISST product uses 1982–present.

### Differences that could matter when comparing results

- **Hindcast release is not pinned, and the store is a draft.** All three repos read the Earthmover `main` branch of the draft store, which is not yet the production version. Only Brooke records the release (r20250912), and Megan's static files come from r20260701. Megan attributes small workflow differences to "differences in the hindcast version" (`Yellowtail.qmd`). Darren reports that a new GFDL release is pending.
- **Raw vs. regrid.** Brooke found only small differences for SST (bias 0.125 vs. 0.132 °C). Everyone else uses regrid. The effect on nearshore, transport or vertical quantities has not been examined.
- **Baselines differ:** 1993–2010, 1993–2025 and 1980–2010. Owen names this as a possible reason why the MOM6 HCI sits lower than the IEA HCI.
- **Depth averaging:** thickness-weighted (Owen; Megan's `_depthweighted` variant) vs. unweighted over layers (Megan's `annual_mean_3d`). Megan found the difference negligible for yellowtail temperature (r = 0.999).
- **Comparison target:** observations (OISST, Newport Line, WCOA), reanalysis (GLORYS, CORA) or another model (UCSC ROMS). "Agreement" therefore means different things in different rows of the table in (c).
- **Statistic:** correlation of z-scored annual indices (groundfish) removes bias by construction. Brooke's monthly gridded statistics include bias and RMSE.

### Practical friction visible in the code

- **Data access is the stated bottleneck** for Owen's 3-D work, which downloads 0–1000 m year by year (`explore_subsurface_heatwaves.qmd`).
- **Mixed-language setups:** Megan runs Python from R through reticulate and pins `icechunk>=2.0.0` and `arraylake>=1.0.0` at runtime. The archive notes an `arraylake auth login` token issue.
- **Data products have problems**: duplicated Jan–Jun 2025 time steps in the MOM6 monthly series (`sst-comparison.ipynb`, cell 5), and 0–360 longitude conventions handled by hand in every repo. The duplicates were still present on 2026-11-12: the `regrid/aux1` group (where `tos`, `MLD_003` and `ssh` live) has 396 time steps, against 390 in `regrid/main`, checked over OPeNDAP for this report.
- **Bugs found and fixed while working:** Megan's depth filter was applied to longitude, then fixed and documented (`Yellowtail.qmd`). Owen's and Megan's repos have no equivalent check for their depth and distance logic (inferred from the absence of tests or validation notebooks).
- **Local state needed to reproduce:** Owen's `/data` and outputs are git-ignored. Brooke's netCDFs live in Git LFS. Megan's static files are committed, about 16 MB.
- **Code from other people's tools, ported:** coast angle and transport from "Mike's MATLAB" (Megan); the HCI method from Schroeder et al. 2022 (Owen); Isaac's plotting scripts (Brooke).
- **Transport and velocity disagree, and the cause is still open.** Megan says differences in "how distance is projected, or the depth integration" remain to be checked.

---

## (c) Model–data correspondence reported so far

The rating column uses the authors' own words where they give them. Where only a number is given, the rating follows this rule of thumb: **high** r ≥ 0.8, **moderate** 0.5–0.8, **low** < 0.5. "Not assessed" means the comparison was set up but no result is stated.

| MOM6 variable | Region / depth / season | Compared against | Metric | Reported correspondence | Source |
|---|---|---|---|---|---|
| SST (`tos`) | CCIEA box 32–48 °N, monthly 1993–2025 | OISST v2.1 | area-weighted R, bias, RMSE | **High**: R 0.97, bias +0.14 °C, RMSE 0.70 °C; warm ~0.5 °C Monterey Bay and S. of Channel Is.; cool ~−0.3 °C nearshore WA | `esr@4aa6ceb:sst_anomaly/sst-comparison.ipynb` |
| SST seasonal anomaly | same, Winter/Spring 2025 | OISST | visual | Shown side by side; no statistic | `esr@4aa6ceb:sst_anomaly/mom6/sst-anomaly.ipynb`; Slides p. 7 |
| HCI (from SST) | Regions 1–4, 1993–2025 | UCSC ROMS 2 m; OISST | visual | **Mixed**: "better as you go north", "better for winter and spring" | Slides p. 8 (no code) |
| HCI (from `thetao` surface) | Regions 1–3, monthly and cumulative | IEA HCI (UCSC ROMS) | correlation, 1:1 scatter | **High** ("very highly correlated", esp. cumulative); MOM6 lower at high HCI, esp. Jul–Nov | `heatwaves@bc80f0a:code/make hci.qmd` |
| MLD (`MLD_003`) | hake egg/yolk/larv/latelarv, shelf break 31–37 °N | ROMS | r of z-scored annual, 1994–2010 | **Moderate**: 0.68–0.79 | `groundfish@e279952:PacificHake/Output/standardized2d.png` |
| MLD | yellowtail part/larv/pjuv | GLORYS | r of z-scored annual | **Moderate to high** (author's words; values not printed); tech memo: "less so" than temperature | `groundfish@e279952:Yellowtail/Yellowtail.qmd`; Slides p. 18 |
| SSH | hake, 0–30 km offshore, Jan–Apr and May–Sep, central and south | ROMS | r of z-scored annual, 1994–2010 | **Moderate to high**: 0.70–0.87 (highest Jan–Apr central) | `groundfish@e279952:PacificHake/Output/standardized2d.png` |
| Temperature (`thetao`) | yellowtail Tcop (copulation) | GLORYS | r of z-scored annual | **Moderate**: 0.61 ("surprising Tcop does not have a higher correlation") | `groundfish@e279952:Yellowtail/Yellowtail.pdf` |
| Temperature | yellowtail, 1998–2021 | GLORYS | not stated | **High**: "Temperature good" | Slides p. 18 (tech memo, not reviewed) |
| Temperature | hake spawning, 130–500 m | ROMS | — | Not assessed (index computed; no comparison figure found) | `groundfish@e279952:PacificHake/Hake_Variables.qmd` |
| Cross-shelf velocity | yellowtail larv, pjuv | GLORYS | r, annual | **Low**: 0.33, 0.41; "there is a bias" | `groundfish@e279952:Yellowtail/Yellowtail.pdf` |
| Alongshore velocity | yellowtail pjuv | GLORYS | r, annual | **Moderate**: 0.60 | same |
| Transport (along- and cross-shore) | hake, various stages | ROMS | — | Not assessed (computed; no comparison shown); author flags transport as "poor performing" overall | `groundfish@e279952:PacificHake/Hake_Variables.qmd`, `Yellowtail/Yellowtail.qmd` |
| EKE (surface) | hake, 0–30 km, Jan–Apr / May–Sep, central and south | ROMS | r of z-scored annual, 1994–2010 | **Moderate** Jan–Apr central (0.69); **low / none** elsewhere (0.17, −0.02, −0.18) | `groundfish@e279952:PacificHake/standardized3d.png` |
| OHC, 6 layers 0–1000 m | US EEZ, by latitude bin | CORA | parallel anomaly and heatwave-area analyses | Not assessed (no comparison stated) | `heatwaves@bc80f0a:code/explore_cora.qmd` |
| Temperature profiles | CalCOFI Line 90; Trinidad Head | CUGN glider; TH CTD | — | Not assessed (observations processed only) | `heatwaves@bc80f0a:code/process_cugn.R`, `process_TH_temperature.R` |
| Dissolved O₂ | NH05 50 m, NH25 150 m, 2005–2025 | Newport Hydrographic Line | time series, monthly climatology | **Low**: biased high, misses seasonal drawdown; worse at depth | Slides pp. 13, 15 (no code) |
| Ω_aragonite | NH05 50 m, NH25 150 m | Newport Hydrographic Line | time series, monthly climatology | **Low**: biased high, misses drawdown; worse at depth | Slides pp. 14–15 (no code) |
| Temperature | NH05 50 m, NH25 150 m, monthly climatology | Newport Hydrographic Line | climatology plot | Shown; no statement of agreement | Slides p. 15 (no code) |
| NO₃ | surface, WCOA cruises | WCOA | R, RMSE, bias | **Moderate to low**: R 0.51, RMSE 8.6, bias +5.9 µmol/kg (model high) | Slides p. 16 (no code) |
| CUTI / BEUTI | — | — | — | Not assessed (listed as planned "processed output" in Slides p. 17; not found in code) | Slides p. 17 |
| Any variable, **seasonal forecast** | — | — | — | Not assessed (no forecast use found) | — |

**Read across the table:** SST and SST-derived indices agree best. Temperature, MLD and SSH indices agree moderately with other models. Velocity, transport and EKE agree weakly. Subsurface biogeochemistry carries a known bias, and the author expects a new model release to reduce it.

---

## (d) Open questions for the authors

1. **Isaac:** Where does the MOM6 HCI code live, and which MOM6 release, baseline period and thresholds did it use? Could it be reconciled with Owen's `make hci.qmd`, which has 3 regions and a 1993–2010 baseline?
2. **Owen:** What were the MOM6–IEA HCI correlation values? Is there a summary of how MOM6 OHC and heatwave timing compare with CORA? Are CUGN and Trinidad Head meant to be compared with MOM6?
3. **Darren:** Where is the biogeochemistry comparison code, and which MOM6 release was it run on? Are the "improvements" in the pending GFDL output expected to fix the O₂/Ω_arag bias?
4. **Megan / Brooke:**
   - Which ROMS produced the hake comparison CSVs, and over which domain?
   - In `Hake_Variables.qmd`, line 390, `MLDlarv` is computed with the `'yolk'` stage settings. Is that intended? In the comparison figure the MOM6 MLDlarv and MLDyolk series appear identical.
   - Is the "MOM6v2" Python workflow (Brooke and Roland) archived anywhere?
   - Is the yellowtail tech memo available to cite?
5. **All:** Should analyses pin a hindcast release (e.g. an Icechunk snapshot or tag) rather than read `main`? At least two releases (r20250912, r20260701) are in use at once. When the production version of the Earthmover store is published, which results should be re-run first?
6. **All:** Does anyone plan to evaluate the **seasonal forecast** (Jacox et al. 2026 preprint) against these same indices?
7. **Brooke:** Is the unmerged conservative-regridding branch (`6d08488`) intended to replace the bilinear comparison?
8. **All:** For the transport, velocity and EKE indices, is the disagreement with ROMS and GLORYS thought to come mostly from model physics or from differences in how each workflow computes the index?

---

## Appendix A: what was reviewed

All repositories were cloned read-only on 2026-11-12. Nothing was run, and no large model output was downloaded. Statistics are quoted from committed notebook outputs, rendered PDFs or figures, or from the slides.

| Short name | Repository | Commit reviewed | Commits / span |
|---|---|---|---|
| `esr` | [brooke-l-hawkins-noaa/mom6-based-esr-indices](https://github.com/brooke-l-hawkins-noaa/mom6-based-esr-indices/tree/4aa6ceb6a57b7a12c1dc40ee9632e1b1aa6cfb53) | `4aa6ceb6a57b7a12c1dc40ee9632e1b1aa6cfb53` (pinned in issue) | 31 / 2026-06-11 – 2026-10-21 |
| `groundfish` | [brooke-l-hawkins-noaa/mom6-based-groundfish-indices](https://github.com/brooke-l-hawkins-noaa/mom6-based-groundfish-indices/tree/e279952c188ace69bac4df2d7887dba9f7455792) | `e279952c188ace69bac4df2d7887dba9f7455792` (HEAD of `main`) | 42 / 2026-06-11 – 2026-11-06 |
| `oc_cciea` | [id-sch/oc_cciea.github.io](https://github.com/id-sch/oc_cciea.github.io/tree/5ce77aae3d91b74c4fd7cd8ce3e79540717f3ac1) | `5ce77aae3d91b74c4fd7cd8ce3e79540717f3ac1` (HEAD of `main`) | 729 / 2025-11-09 – 2026-10-16 |
| `heatwaves` | [owenrliu/subsurface_heatwaves](https://github.com/owenrliu/subsurface_heatwaves/tree/bc80f0a9e5dda7cc05c882d17095e3426fac0591) | `bc80f0a9e5dda7cc05c882d17095e3426fac0591` (HEAD of `main`) | 4 / 2026-09-03 – 2026-11-11 |
| Slides | *MOM6 / ESR Progress Update*, CC ESR Seaside Chat, 2026-10-30 (Hawkins, Schroeder, Liu, Pilcher, Feddern), 19 pp. | — | not in repo |

Other branches checked: `esr` `copilot/update-sst-comparison-regridding-method` (`6d08488`); `oc_cciea` `gh-pages`.

**Files read**

- `esr`: `README.md`; `sst_anomaly/sst-comparison.ipynb`; `sst_anomaly/mom6/sst-anomaly.ipynb`; `sst_anomaly/mom6/contour_noaamom6hindcast_clim_anoms_season.py`; `sst_anomaly/oisst/contour_noaaoisst_clim_anoms_season.py`; `.gitattributes`.
- `groundfish`: `README.md`; `DESCRIPTION`; `PacificHake/README.md`; `PacificHake/Hake_Variables.qmd`; `PacificHake/Output/standardized2d.png`, `standardized3d.png`; `PacificHake/standardized3d.png`; `Yellowtail/Yellowtail.qmd`, `Yellowtail.pdf`, `Yellowtail_Variables.qmd`; `R/*.R`; `STATIC/README.md`; `ARCHIVE/MOM6_variables.qmd` (searched); CSV headers.
- `oc_cciea`: repository-wide search for MOM6 terms; `code_gha/HCI_ROMS/nrt_roms_daily_update.py`, `calc_thresholds_roms_area.py`; `code_gha/HCI/*` (searched); `code_gha/miniESR/*`; `code_gha/SSTspatial/*` (searched); `.github/workflows/code1_hciroms_gha.yml`; git log.
- `heatwaves`: `README.md`; `code/download_monthly_thetao.R`; `code/calculate_ohc.R`; `code/explore earthmover.R`; `code/explore_subsurface_heatwaves.qmd`; `code/explore_ohc.qmd`; `code/explore_cora.qmd`; `code/make hci.qmd`; `code/process_cora.R`, `process_cugn.R`, `process_TH_temperature.R`; `code/shear.R`, `check_shear.R`; `.gitignore`; list of `plots/`.

## Appendix B: minimal access patterns

These snippets show the general pattern the authors use, reduced to the essentials. Each one opens the monthly hindcast lazily and pulls a small subset: SST, or temperature in the top 250 m, for the CCIEA box 32–48 °N, 128–116.8 °W. They are adapted from the cited files, not copied, and none of the authors wrote them in this form.

Notes that apply to all three:

- **Longitude is 0–360** in every group, so add 360 to negative longitudes.
- **Groups:** `regrid/main` holds the 3-D fields (`thetao`, `uo_rotate`, `vo_rotate`, `rhopot0`, …). `regrid/aux1` holds the 2-D and derived fields (`tos`, `MLD_003`, `ssh`, …). The `raw/...` groups hold the same fields on the native curvilinear grid, with 2-D `geolat`/`geolon` coordinates on `jh`/`ih` dimensions.
- **Duplicated months:** as of 2026-11-12, `regrid/aux1` has 396 time steps against 390 in `regrid/main`; Jan–Jun 2025 appear twice. Drop the duplicates before computing anything.
- **Release:** `main` always points at the newest build. The current store is a **draft built from r20250912**, not yet the production version. Record the date you read it, and use a snapshot or tag if the store offers one.

### B1. Python, native Icechunk (Brooke's pattern)

Adapted from `esr@4aa6ceb:sst_anomaly/mom6/sst-anomaly.ipynb`, cells 4 and 6. This route needs a free Earthmover account: run `arraylake auth login` once per machine.

```python
# pip install arraylake icechunk zarr xarray dask
import xarray as xr
from arraylake import Client

client = Client()  # uses the token saved by `arraylake auth login`
repo = client.get_repo("NOAA-PMEL/cefi-nep-hindcast-monthly")
session = repo.readonly_session(branch="main")

# regridded (rectilinear) 2-D fields
aux = xr.open_zarr(session.store, zarr_format=3, group="regrid/aux1")
sst = (
    aux["tos"]
    .drop_duplicates("time", keep="first")
    .sel(lat=slice(32, 48), lon=slice(-128 + 360, -116.8 + 360))
)
sst.to_netcdf("mom6_sst_ccs.nc")  # only now is data transferred (~12 MB)

# native curvilinear grid: subset with a mask on 2-D geolat/geolon
raw = xr.open_zarr(session.store, zarr_format=3, group="raw/aux1")
box = (
    (raw.geolat >= 32) & (raw.geolat <= 48)
    & (raw.geolon >= -128 + 360) & (raw.geolon <= -116.8 + 360)
)
sst_raw = raw["tos"].where(box).dropna("ih", how="all").dropna("jh", how="all")
```

### B2. R, native Icechunk through reticulate (Megan's pattern)

Adapted from `groundfish@e279952:PacificHake/Hake_Variables.qmd`. It is the same as B1, driven from R, and needs the same Earthmover login.

```r
library(reticulate)
py_require(c("icechunk>=2.0.0", "arraylake>=1.0.0", "zarr", "xarray", "dask"))
arraylake <- import("arraylake")
xr        <- import("xarray")

client  <- arraylake$Client()
repo    <- client$get_repo("NOAA-PMEL/cefi-nep-hindcast-monthly")
session <- repo$readonly_session(branch = "main")

main   <- xr$open_zarr(session$store, zarr_format = 3L, group = "regrid/main")
thetao <- main[["thetao"]]$sel(
  lat = py_eval("slice(32, 48)"),
  lon = py_eval("slice(232, 243.2)"),
  z_l = py_eval("slice(0, 250)")
)
# reduce lazily in xarray before bringing values into R
ts <- thetao$mean(dim = c("lat", "lon", "z_l"), skipna = TRUE)$values
```

### B3. R or Python over OPeNDAP, no login (Owen's pattern)

Adapted from `heatwaves@bc80f0a:code/download_monthly_thetao.R`. Earthmover serves each group of the store as a DAP2 endpoint: `https://compute.earthmover.io/v1/services/dap2/<org>/<repo>/<branch>/<group>/opendap`. Subsetting is by index, and only the requested slab is transferred.

```r
library(ncdf4)
url <- paste0("https://compute.earthmover.io/v1/services/dap2/",
              "NOAA-PMEL/cefi-nep-hindcast-monthly/main/regrid/main/opendap")
nc  <- nc_open(url)
lat <- ncvar_get(nc, "lat"); lon <- ncvar_get(nc, "lon")
z   <- ncvar_get(nc, "z_l"); tm  <- ncvar_get(nc, "time")  # days since 1993-01-01

ilat <- which(lat >= 32 & lat <= 48)
ilon <- which(lon >= 360 - 128 & lon <= 360 - 116.8)
iz   <- which(z <= 250)
it   <- length(tm)  # last month; dimension order is lon, lat, depth, time

thetao <- ncvar_get(nc, "thetao",
  start = c(min(ilon), min(ilat), min(iz), it),
  count = c(length(ilon), length(ilat), length(iz), 1))
nc_close(nc)
```

The same endpoint works from Python:

```python
import xarray as xr
url = ("https://compute.earthmover.io/v1/services/dap2/"
       "NOAA-PMEL/cefi-nep-hindcast-monthly/main/regrid/aux1/opendap")
ds = xr.open_dataset(url, engine="netcdf4")  # pip install netCDF4 xarray
sst = (ds["tos"].drop_duplicates("time", keep="first")
       .sel(lat=slice(32, 48), lon=slice(-128 + 360, -116.8 + 360)))
```

### How these were tested (2026-11-12)

| Snippet | Result |
|---|---|
| B3, R | **Ran.** Hub R with `ncdf4` 1.24 (hub image, not a clean install). Returned a 39 × 187 × 24 slab, mean 11.07 °C for 0–250 m, last month. |
| B3, Python | **Ran** in a clean venv (`xarray`, `netCDF4` only). `regrid/aux1` opened with 396 time steps (1993-01 to 2025-06, duplicates included); the SST subset was 187 × 39, mean 14.76 °C for the last month. |
| B1, Python | **Not yet run successfully.** The clean venv installed `arraylake` 1.8.0, `icechunk` 2.3.1, `zarr` 3.4.2 and `xarray` 2026.9.0, but the hub's saved Earthmover token had expired (`invalid_grant`). The code follows Brooke's notebook, whose committed output shows it ran on 2026-09-17. |
| B2, R | **Not run** (same login requirement). It follows Megan's committed qmd. |

## Appendix C: common tasks, and the tutorials they suggest

This appendix turns the shared steps in (b) into a list of candidate tutorials, ordered roughly as a workflow. "Who needed it" counts the people whose code or slides show the task; Darren and Isaac's MOM6 work count only where the slides make the task visible. "Start from" points to existing code that could seed a tutorial. Each tutorial would ideally come in both R and Python, since the work splits about evenly between them: Brooke and Isaac use Python, Megan and Owen use R.

### Getting the data

| # | Tutorial | Who needed it | What it should cover | Start from |
|---|---|---|---|---|
| 1 | **Open MOM6 from Earthmover and pull a subset** | Everyone with code (Brooke, Megan, Owen) | The three routes (native Icechunk in Python, the same from R via reticulate, OPeNDAP with no login); groups (`regrid/main`, `regrid/aux1`, `raw/...`); choosing variables; subsetting by box, depth and time before transferring; saving a local subset; estimating size first | Appendix B; `esr:sst_anomaly/mom6/sst-anomaly.ipynb`; `groundfish:PacificHake/Hake_Variables.qmd`; `heatwaves:code/download_monthly_thetao.R` |
| 2 | **Know the product: releases, grids and conventions** | Everyone | Hindcast vs. forecast; releases and why to record or pin one; that the Earthmover version is a draft; 0–360 longitude; mid-month time stamps; dropping the duplicated 2025 months; variable names and units (`tos`, `thetao`, `MLD_003`, `uo_rotate`, …) | `esr:sst_anomaly/sst-comparison.ipynb` (cells 5–15) |
| 3 | **Raw (native) vs. regrid grids** | Brooke (compared both); everyone else chose regrid | Curvilinear `geolat`/`geolon` on `jh`/`ih`; masking instead of slicing; when the choice matters (nearshore, velocities, transport); regrid's uneven spacing (≈0.086° × 0.288° in this box) | `esr:sst_anomaly/sst-comparison.ipynb` (cells 9–15) |
| 4 | **Static grid information** | Megan, Owen, Isaac (ROMS/OISST) | Where bathymetry, cell area, distance-to-coast and coast angle come from, and how to align them with the data grid | `groundfish:STATIC/README.md`, `R/annual_mean_2d.R` |

### Defining where and when

| # | Tutorial | Who needed it | What it should cover | Start from |
|---|---|---|---|---|
| 5 | **Coastal and regional masks** | Megan, Owen, Isaac | Distance-from-shore bands (e.g. 0–30, 75, 150 km), isobath bands, the US EEZ, the HCI latitude regions; building them once and reusing them | `groundfish:STATIC/*`; `heatwaves:code/make hci.qmd`, `check_shear.R`; `oc_cciea:code_gha/HCI_ROMS/create_xdis_area_bath_mask_area.py` |
| 6 | **Working with depth** | Megan, Owen; Darren (fixed depths at stations) | Selecting depth ranges on `z_l`; layer thickness from `z_i` or `z_l`; thickness-weighted means; depth-integrated quantities such as heat content; pulling values at a station and depth; isopycnals from `rhopot0` | `groundfish:R/annual_mean_3d_depthweighted.R`; `heatwaves:code/calculate_ohc.R`, `explore_subsurface_heatwaves.qmd` |
| 7 | **Seasonal and life-stage windows** | Megan (≈30 life-stage indices), Brooke (seasonal anomalies), Owen (HCI months) | Month windows, including ones that wrap the year; carrying a window over from the previous year ("preconditioning"); a lookup-table approach so each index is defined once | `groundfish:PacificHake/Hake_Variables.qmd` (`lifestage_dict`) |

### Making indices

| # | Tutorial | Who needed it | What it should cover | Start from |
|---|---|---|---|---|
| 8 | **From a gridded field to a time series** | Everyone | Area-weighted spatial means (cos(latitude) or cell area); handling land and NaNs; monthly to seasonal to annual aggregation | `esr:sst_anomaly/sst-comparison.ipynb` (cells 16–20); `groundfish:R/eke_surface.R` |
| 9 | **Climatologies, anomalies and baselines** | Brooke, Owen, Isaac | Monthly climatology; anomalies and z-scores; detrending; choosing a baseline when MOM6 starts in 1993 and existing products use 1980–2010 or 1982–present | `heatwaves:code/explore_ohc.qmd`; `esr:sst_anomaly/mom6/contour_noaamom6hindcast_clim_anoms_season.py` |
| 10 | **Velocity, transport and eddy kinetic energy** | Megan; Owen (shear) | Rotated velocities (`uo_rotate`/`vo_rotate`); along-shore and cross-shore components using coast angle; transport through a section; surface EKE; vertical shear. This is the area where reported agreement is weakest, so it would also cover how calculation choices change results. | `groundfish:R/transport_3D.R`, `R/eke_surface.R`; `heatwaves:code/shear.R` |
| 11 | **Recreating an existing CCIEA indicator from MOM6** | Brooke (SST anomaly maps); Isaac and Owen (HCI, separately) | Worked examples: the HCI from MOM6, and the ESR SST anomaly map. One shared HCI implementation would settle the two current versions. | `heatwaves:code/make hci.qmd`; `esr:sst_anomaly/mom6/`; `oc_cciea:code_gha/HCI_ROMS/` |
| 12 | **Event and extreme metrics** | Owen | Marine heatwave area and frequency above a threshold; hotspots; breakpoint and regime-shift tests on index time series | `heatwaves:code/explore_ohc.qmd` |

### Comparing with other data

| # | Tutorial | Who needed it | What it should cover | Start from |
|---|---|---|---|---|
| 13 | **Getting comparison datasets** | Everyone | OISST, CCIEA indices (HCI, PDO, NPGO) and Trinidad Head CTD from ERDDAP; GLORYS; UCSC ROMS via CeNCOOS OPeNDAP; CORA; CUGN gliders; the Newport Hydrographic Line | `oc_cciea:code_gha/SSTspatial/sst_oi_daily_v21_update.py`, `code_gha/HCI_ROMS/nrt_roms_daily_update.py`; `groundfish:R/fetch_erddap_metric.R`; `heatwaves:code/process_cora.R`, `process_cugn.R`, `process_TH_temperature.R` |
| 14 | **Putting model and observations on the same grid** | Brooke | Bilinear vs. conservative regridding with xESMF; regridding both products to a common coarser grid (Brooke's own suggestion); model-to-point extraction for stations and gliders | `esr:sst_anomaly/sst-comparison.ipynb`; `esr` branch `copilot/update-sst-comparison-regridding-method` |
| 15 | **Skill metrics and how to report them** | Everyone | Bias, RMSE, correlation (gridded, time series, maps); correlation of standardized annual indices, and what it hides (bias); monthly-climatology comparisons; seasonal and regional breakdowns; a common way to state "agreement" so results can be pooled into one table like (c) | `esr:sst_anomaly/sst-comparison.ipynb` (cells 18–33); `groundfish:Yellowtail/Yellowtail.qmd` |

### Not yet done by anyone, but implied

| # | Tutorial | Why | Notes |
|---|---|---|---|
| 16 | **Using the seasonal forecast** | No one has used it yet; the slides list "develop new indices with new variables and forecast" (Slides, p. 19) | Leads and ensemble members, forecast anomalies, skill against the hindcast and observations |
| 17 | **Daily data** | Everyone used monthly data | When daily is needed (heatwave duration, upwelling events) and what is available on Earthmover |
| 18 | **Reproducible MOM6 workflows** | Several repos depend on local files, Git LFS or an unpinned release | Recording or pinning the release, environment files (including R and Python together), keeping derived files small and documented |

**A possible core sequence.** Tutorials 1, 2, 5, 6, 8, 9, 13 and 15 cover what nearly everyone had to do: access, conventions, masks, depth, spatial means, anomalies, comparison data and skill metrics. The others are specialist add-ons.
