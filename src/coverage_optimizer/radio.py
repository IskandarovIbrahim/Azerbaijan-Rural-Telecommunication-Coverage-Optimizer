"""Free-space attenuation and geometric visibility over a raster surface."""

from dataclasses import dataclass, fields
from math import ceil, floor, isfinite, log10

import numpy as np

EARTH_RADIUS_M = 6_371_000


@dataclass(frozen=True)
class RadioScenario:
    frequency_mhz: float
    transmit_power_dbm: float
    transmit_antenna_gain_dbi: float
    receive_antenna_gain_dbi: float
    system_loss_db: float
    transmit_antenna_height_m: float
    receive_antenna_height_m: float
    receiver_threshold_dbm: float
    fade_margin_db: float
    effective_earth_radius_factor: float

    @classmethod
    def from_config(cls, scenario: dict) -> "RadioScenario":
        values = {}
        for field in fields(cls):
            value = scenario.get(field.name)
            if type(value) not in (int, float) or not isfinite(value):
                raise ValueError(f"scenario.{field.name} must be a finite number")
            values[field.name] = value
        if min(values[key] for key in (
            "frequency_mhz", "transmit_antenna_height_m", "receive_antenna_height_m",
            "effective_earth_radius_factor",
        )) <= 0:
            raise ValueError("frequency, antenna heights and Earth radius factor must be positive")
        if min(values["system_loss_db"], values["fade_margin_db"]) < 0:
            raise ValueError("system loss and fade margin must be nonnegative")
        return cls(**values)

    def budget(self, distance_m: float) -> tuple[float, float, float]:
        loss_db = free_space_path_loss_db(distance_m, self.frequency_mhz)
        power_dbm = (self.transmit_power_dbm + self.transmit_antenna_gain_dbi
                     + self.receive_antenna_gain_dbi - self.system_loss_db - loss_db)
        margin_db = power_dbm - self.receiver_threshold_dbm - self.fade_margin_db
        return loss_db, power_dbm, margin_db


def free_space_path_loss_db(distance_m: float, frequency_mhz: float) -> float:
    """Return ITU-R P.525 free-space loss with distance supplied in meters."""
    if not (0 < distance_m < float("inf") and 0 < frequency_mhz < float("inf")):
        raise ValueError("distance and frequency must be finite and positive")
    return 32.44 + 20 * (log10(distance_m) - 3) + 20 * log10(frequency_mhz)


def grid_crossings(start: float, end: float) -> np.ndarray:
    """Find where one pixel coordinate crosses an integer grid line."""
    if start == end:
        return np.empty(0)
    low, high = sorted((start, end))
    return (np.arange(floor(low) + 1, ceil(high)) - start) / (end - start)


def terrain_clearance_m(
    surface: np.ndarray,
    start_pixel: tuple[float, float],
    end_pixel: tuple[float, float],
    distance_m: float,
    scenario: RadioScenario,
) -> float | None:
    """Find minimum clearance along the direct ray, or None for incomplete terrain."""
    height, width = surface.shape
    x0, y0 = start_pixel
    x1, y1 = end_pixel
    if not (0 <= x0 < width and 0 <= x1 < width and 0 <= y0 < height and 0 <= y1 < height):
        return None
    tx = surface[floor(y0), floor(x0)] + scenario.transmit_antenna_height_m
    rx = surface[floor(y1), floor(x1)] + scenario.receive_antenna_height_m
    edges = np.unique(np.concatenate(([0.0, 1.0], grid_crossings(x0, x1), grid_crossings(y0, y1))))
    midpoints = (edges[:-1] + edges[1:]) / 2
    cols = np.floor(x0 + (x1 - x0) * midpoints).astype(int)
    rows = np.floor(y0 + (y1 - y0) * midpoints).astype(int)
    elevations = surface[rows, cols]
    if not (isfinite(tx) and isfinite(rx) and np.isfinite(elevations).all()):
        return None

    # In each constant-height cell, clearance is convex in path fraction t.
    # Clamp the quadratic minimum to the interval that lies in that cell.
    bulge_coefficient = distance_m**2 / (2 * EARTH_RADIUS_M * scenario.effective_earth_radius_factor)
    rise = rx - tx
    vertex = (1 - rise / bulge_coefficient) / 2
    t = np.clip(vertex, edges[:-1], edges[1:])
    clearance = tx + rise * t - bulge_coefficient * t * (1 - t) - elevations
    return float(clearance.min())
