# Game plan

## What the PDF proposes

Pages 3–4 of *Azerbaijan Engineering Project Ideas* propose a mountainous pilot, roughly 20 candidate sites and 15 settlements as an illustrative scale, SRTM elevation, free-space path loss plus terrain line of sight, and a weighted set-cover comparison between greedy selection and integer programming. The proposed reporting measures are infrastructure cost, coverage and runtime. Fresnel clearance and improved attenuation models are suggested extensions. The PDF's 2–4 weeks is an estimate for a focused prototype.

## Pilot and technical design

Start around Xınalıq, Quba District. Configure a provisional 15 km radius around a verified settlement point and clip demand to the chosen study area. Include a terrain buffer and retain only links whose full profiles are inside the available raster. Target 10–15 rural settlements and about 20 hypothetical sites. Choose the final extent after counting distinct settlements and checking terrain completeness. Document changes to the extent and screening rules. [Azerbaijan Tourism Board on Xınalıq](https://azerbaijan.travel/glean-a-gem-amid-mountains-in-incredible-khinalig)

- **Demand** — Start with one fixed outdoor receiver point per village and uniform weights. Preserve source identifiers and local names. Report percentages against all included settlements, including unreachable ones. Check receiver placement and population-based weights as separate scenarios.
- **Candidate sites** — Start with a deterministic, spaced grid, then filter missing terrain, water and excessively steep ground. Record slope and mapped road distance as screening attributes. A site on the shortlist is hypothetical. Start with equal site costs, then compare with a transparent access-cost index based on road distance or slope and show the effect of changing those weights. Use cost units, with actual currency reserved for sourced cost estimates.
- **Radio model** — Compare an FSPL-only baseline with FSPL plus sampled terrain line of sight. Use `FSPL_dB = 32.44 + 20 log10(distance_km) + 20 log10(frequency_MHz)`. Apply an assumed link budget and record frequency, transmit power, gains, losses, antenna heights, receiver threshold and margin. For example, a one-way modeled link passes when received power minus the fade margin meets the threshold and the terrain path is clear. Treat gaps in terrain profiles as unknown and report them separately. Use one configurable hypothetical fixed-wireless downlink scenario with assumed upstream backhaul and power at each candidate. Gateway reachability, return link, interference, clutter, capacity, permitting and site feasibility require separate modeling or field evidence. Add Fresnel clearance as a sensitivity test after the basic LOS model works. [ITU-R P.525](https://www.itu.int/rec/R-REC-P.525/) · [ITU-R P.526](https://www.itu.int/rec/R-REC-P.526/en)
- **Optimization** — Derive a binary site-by-settlement matrix from usable links. Minimize the sum of selected site costs subject to at least one selected site per settlement. Greedy chooses the greatest number of newly covered settlements per unit cost, with ties resolved by site ID. Run the exact binary model with SciPy MILP/HiGHS and compare both on identical inputs. Check returned selections independently and record solver status, bound or gap when available. A settlement with no eligible links makes full cover infeasible. Report it by name; offer a clearly labelled reachable-only comparison and a separate budgeted maximum-coverage scenario when useful. For the budgeted scenario, count each covered settlement once and use the same budget and weights across methods.
- **Engineering stack** — Python, NumPy, Rasterio, PyProj, SciPy MILP and pytest, with GeoPandas for spatial preprocessing if needed. Build a CLI and static outputs first. Keep DEM acquisition, RF calculations and optimization independently runnable.

## Deliverables and checks

Ship a repeatable command that produces a link table with pass/fail/unknown reasons, selected and unselected sites, settlement coverage summaries, a cost/coverage/runtime comparison, and a map of the pilot. Include a fully offline synthetic example alongside the real-data reproduction instructions.

Verify the distance/units math against reference values, clear and ridge-blocked paths on synthetic rasters, missing elevation handling, and exact solver results by enumeration on tiny matrices. Run both solvers on the same matrix and separately time link generation and optimization. Use repeated timings with hardware and software noted. Report selected site counts, cost, total and reachable coverage denominators, and the percentage cost gap only when an optimum is established and its cost is positive. Compare FSPL-only and terrain-aware matrices under identical settings, then vary antenna height, threshold/margin, and cost assumptions. Show changes in coverage, cost and selected sites. Equal costs or equal solutions are valid outcomes.

The output supports statements such as “under scenario A, the solver found a lower-cost set than greedy at equal modeled coverage,” if the run demonstrates that result. Map labels and the report should identify the output as a planning simulation. Field or operator measurements would be needed to assess real deployment performance.

## Work and commit sequence

Each row is a working checkpoint. Adjacent checkpoints can share a development session. Keep the corresponding code, tests and updated instructions together and commit only files for that checkpoint.

| Order | Commit subject | Evidence expected at the checkpoint |
| --- | --- | --- |
| 0 | `docs: plan the rural coverage optimizer` | Brief analysis, source decisions, skills, prompt and commit plan |
| 1 | `chore: scaffold the coverage optimizer` | Installable package, CLI help, pilot config, data contract and offline smoke test |
| 2 | `feat: prepare Quba pilot inputs` | Pinned source manifest, reproducible acquisition and transforms, AOI and inputs checked |
| 3 | `feat: model free-space and terrain-aware links` | Link table and tests for FSPL, ridge pass/fail and missing data |
| 4 | `feat: add greedy and exact site selection` | Tiny exact oracle, infeasibility tests and same-matrix comparison |
| 5 | `feat: run pilot scenarios and sensitivity analysis` | Reproducible metrics, timing and scenario metadata |
| 6 | `docs: publish the pilot results and reproduction guide` | Captioned map, compact results table and limitations supported by completed runs |

Inspect the staged diff and run the relevant checks before each commit. Commit configs, code, synthetic fixtures and small reports that can be redistributed. Keep large input files, tokens, environments and reproducible intermediate outputs out of Git. Record each commit hash and checks in the work handoff. Push completed checkpoints when authorized, with individual commits preserved so the GitHub history follows the engineering workflow.
