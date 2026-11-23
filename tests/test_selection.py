"""Small synthetic cases with independently enumerable optima."""

from itertools import combinations
import unittest

from coverage_optimizer.selection import compare_selection


def fixture(rows, costs, columns):
    return {
        "scenario_id": "synthetic",
        "site_ids": [f"synthetic-site-{i}" for i in range(len(rows))],
        "site_cost_units": costs,
        "settlement_ids": [f"synthetic-settlement-{i}" for i in range(columns)],
        "variants": {"terrain_los": rows},
    }


def enumerate_minimum(rows, costs):
    reachable = {column for row in rows for column, value in enumerate(row) if value}
    return min(
        sum(costs[i] for i in chosen)
        for size in range(len(rows) + 1)
        for chosen in combinations(range(len(rows)), size)
        if {col for i in chosen for col, value in enumerate(rows[i]) if value} == reachable
    )


class SiteSelectionTests(unittest.TestCase):
    def test_greedy_can_need_an_extra_tower(self):
        rows = [[1, 1, 1, 1, 0, 0], [1, 1, 0, 0, 1, 0], [0, 0, 1, 1, 0, 1]]
        costs = [1, 1, 1]
        result = compare_selection(fixture(rows, costs, 6), "terrain_los")
        self.assertEqual(result["full_cover_status"], "feasible")
        self.assertEqual(result["methods"]["greedy"]["selected_site_count"], 3)
        self.assertEqual(result["methods"]["exact"]["total_cost_units"], enumerate_minimum(rows, costs))
        self.assertEqual(result["methods"]["exact"]["selected_site_count"], 2)

    def test_exact_weighted_cover_and_unreachable_demand(self):
        rows = [[1, 1, 0], [1, 0, 0], [0, 1, 0]]
        costs = [3, 1, 1.5]
        result = compare_selection(fixture(rows, costs, 3), "terrain_los")
        self.assertEqual(result["full_cover_status"], "infeasible")
        self.assertEqual(result["unreachable_settlement_ids"], ["synthetic-settlement-2"])
        exact = result["methods"]["exact"]
        self.assertEqual(exact["total_cost_units"], enumerate_minimum(rows, costs))
        self.assertEqual(exact["covered_settlement_count"], 2)

    def test_no_reachable_demand_needs_no_sites(self):
        result = compare_selection(fixture([[0, 0]], [1], 2), "terrain_los")
        self.assertEqual(result["full_cover_status"], "infeasible")
        self.assertEqual(result["methods"]["exact"]["selected_sites"], [])
        self.assertEqual(result["methods"]["greedy"]["total_cost_units"], 0)
        self.assertIsNone(result["greedy_relative_cost_gap"])

    def test_tied_greedy_scores_use_site_id(self):
        data = fixture([[1], [1]], [1, 1], 1)
        data["site_ids"] = ["synthetic-site-z", "synthetic-site-a"]
        result = compare_selection(data, "terrain_los")
        self.assertEqual(result["methods"]["greedy"]["selected_sites"][0]["site_id"],
                         "synthetic-site-a")

    def test_invalid_link_and_cost_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "binary"):
            compare_selection(fixture([[2]], [1], 1), "terrain_los")
        with self.assertRaisesRegex(ValueError, "positive"):
            compare_selection(fixture([[1]], [0], 1), "terrain_los")
