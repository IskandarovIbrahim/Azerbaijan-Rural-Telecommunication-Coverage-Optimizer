---
name: evaluate-coverage-experiments
description: Design repeatable comparisons and report coverage optimizer results. Use for benchmark scenarios, sensitivity experiments, engineering reports, maps and reproducibility checks.
---

1. Use the [game plan](../../../docs/game-plan.md) and [data source decisions](../../../docs/data-sources.md) to identify scenario config, source manifest, code revision, clocked stages and intended comparisons. Keep input-independent checks runnable offline.
2. Compare solvers on exactly the same matrix, cost and demand. Compare FSPL-only and terrain-aware results with the same radio and site settings. Change one parameter per sensitivity experiment unless a documented combined scenario is the purpose.
3. Time matrix generation and optimization separately. Record repeats, hardware and dependency versions. Report cost, coverage denominators including unreachable demand, selected sites and solver status. Track how selections change with assumptions.
4. Tie maps and tables to run artifacts and cite source terms. Distinguish simulated results, synthetic fixtures and public coverage context in labels. Document what evidence would be needed to test real-world performance.
