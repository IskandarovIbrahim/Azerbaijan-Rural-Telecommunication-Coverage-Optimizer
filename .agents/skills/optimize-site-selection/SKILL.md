---
name: optimize-site-selection
description: Implement and compare greedy and exact radio site selection on a shared coverage matrix. Use for weighted set cover, budgeted maximum coverage, infeasibility reporting and solver verification.
---

1. Read the optimization section in the [game plan](../../../docs/game-plan.md). Treat the link matrix as an input indexed by stable site and settlement IDs. Use finite positive costs and explicitly state the target demand set.
2. For full cover, implement greedy marginal coverage per cost with stable tie-breaking and a binary MILP minimizing cost. Detect uncovered columns and expose them in results, even when also running an explicitly reachable-only variant.
3. If optimizing coverage under a budget, count each settlement's weight once and link each covered flag to at least one selected covering site. Keep costs, demand weights, reachability, budget and matrix identical across comparison runs.
4. Recompute coverage and cost from each returned selection. Report solver status and bound or gap when available. Describe a result as exact only when optimality is established. Compare against enumeration on small fixtures and report infeasible, zero-demand and tied outcomes without inventing an improvement.
