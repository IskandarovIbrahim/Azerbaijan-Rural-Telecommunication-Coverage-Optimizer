---
name: model-wireless-links
description: Compute and verify free-space and terrain-aware fixed-wireless links. Use for line-of-sight profiles, link budgets, Fresnel clearance or coverage-matrix generation.
---

1. Read the radio design in the [game plan](../../../docs/game-plan.md). Keep input and output units explicit. Use positive distances and frequencies in FSPL. Store one-way link-budget assumptions in the scenario config and report received power and margin.
2. Sample the full profile in a suitable metric CRS. Derive endpoint heights from the same surface reference plus the configured antenna heights. Apply the same sample and endpoint policy for comparable runs. If Earth curvature or Fresnel clearance is modeled, expose the parameters and document the geometry. A profile with missing elevations yields an unknown terrain decision.
3. Keep FSPL-only and terrain-aware decisions independently reproducible. Emit stable site and settlement IDs, distance, loss, margin, LOS state and outcome reason. Only links that satisfy the modeled constraints enter the binary matrix as successes.
4. Test against reference FSPL values, a clear path, a ridge and missing terrain. Retain raw diagnostics for disambiguating threshold failures and obstructions. Label outputs as simulated candidate-to-receiver links conditioned on the upstream backhaul assumption.
