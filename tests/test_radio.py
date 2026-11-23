"""Synthetic radio-model checks with simple, known surfaces."""

import unittest

import numpy as np

from coverage_optimizer.links import link_records
from coverage_optimizer.radio import RadioScenario, free_space_path_loss_db, terrain_clearance_m


class RadioModelTests(unittest.TestCase):
    def setUp(self):
        self.scenario = RadioScenario(
            frequency_mhz=900, transmit_power_dbm=23, transmit_antenna_gain_dbi=8,
            receive_antenna_gain_dbi=3, system_loss_db=2, transmit_antenna_height_m=20,
            receive_antenna_height_m=4, receiver_threshold_dbm=-100, fade_margin_db=15,
            effective_earth_radius_factor=4 / 3,
        )
        self.site = {"site_id": "synthetic-site", "x": 0, "y": 0, "pixel": (0.5, 1.5)}
        self.settlement = {"settlement_id": "synthetic-settlement", "name": "Synthetic",
                           "x": 400, "y": 0, "pixel": (4.5, 1.5)}

    def records(self, surface):
        return link_records(self.site, self.settlement, surface, self.scenario, "synthetic")

    def test_fspl_reference_and_units(self):
        self.assertAlmostEqual(free_space_path_loss_db(1_000, 1_000), 92.44, places=8)
        self.assertAlmostEqual(free_space_path_loss_db(2_000, 1_000), 98.4606, places=4)
        for distance, frequency in ((0, 1_000), (1_000, 0)):
            with self.assertRaises(ValueError):
                free_space_path_loss_db(distance, frequency)

    def test_flat_and_ridge_profiles_have_identical_link_budgets(self):
        surface = np.zeros((3, 5))
        baseline, flat = self.records(surface)
        self.assertEqual((flat["los_state"], flat["decision"]), ("clear", "usable"))
        surface[1, 2] = 30
        _, ridge = self.records(surface)
        self.assertEqual((ridge["los_state"], ridge["reason"]), ("blocked", "terrain_obstruction"))
        self.assertEqual(baseline["margin_db"], ridge["margin_db"])
        self.assertLess(ridge["min_clearance_m"], 0)

    def test_missing_terrain_is_unknown_when_the_budget_passes(self):
        surface = np.zeros((3, 5))
        surface[1, 2] = np.nan
        baseline, terrain = self.records(surface)
        self.assertEqual(baseline["decision"], "usable")
        self.assertEqual((terrain["decision"], terrain["reason"]), ("unknown", "incomplete_terrain"))

    def test_low_margin_is_unusable_even_with_clear_los(self):
        self.settlement["x"] = 20_000
        flat = np.zeros((3, 5))
        # Elevate both antennas enough that the curvature term does not cause blockage.
        scenario = RadioScenario.from_config({**vars(self.scenario), "receive_antenna_height_m": 30})
        baseline, terrain = link_records(self.site, self.settlement, flat, scenario, "synthetic")
        self.assertEqual(baseline["reason"], "insufficient_margin")
        self.assertEqual((terrain["los_state"], terrain["decision"]), ("clear", "unusable"))

    def test_curvature_can_block_flat_terrain(self):
        clearance = terrain_clearance_m(np.zeros((3, 5)), (0.5, 1.5), (4.5, 1.5),
                                        34_000, self.scenario)
        self.assertLess(clearance, 0)

    def test_coincident_endpoints_are_unknown(self):
        self.settlement["x"] = 0
        for row in self.records(np.zeros((3, 5))):
            self.assertEqual(row["reason"], "coincident_endpoints")
            self.assertIsNone(row["margin_db"])
