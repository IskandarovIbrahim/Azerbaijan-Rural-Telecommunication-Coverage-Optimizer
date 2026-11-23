"""Compare greedy and minimum-cost site selection on a shared link matrix."""

import json
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp

from .inputs import sha256


def read_ids(data: dict, key: str) -> list[str]:
    ids = data[key]
    if (not isinstance(ids, list) or any(not isinstance(item, str) or not item for item in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError(f"{key} must be a list of unique nonempty identifiers")
    return ids


def greedy_cover(matrix: np.ndarray, costs: np.ndarray, site_ids: list[str]) -> list[int]:
    uncovered = np.ones(matrix.shape[1], dtype=bool)
    order = sorted(range(len(site_ids)), key=site_ids.__getitem__)
    selected = []
    while uncovered.any():
        gains = matrix[:, uncovered].sum(axis=1)
        index = max(order, key=lambda i: gains[i] / costs[i])
        if not gains[index]:
            raise RuntimeError("greedy selection cannot cover the target settlements")
        selected.append(index)
        uncovered &= ~matrix[index]
    return selected


def exact_cover(matrix: np.ndarray, costs: np.ndarray) -> tuple[list[int], dict]:
    if not matrix.shape[1]:
        return [], {"status": "optimal", "lower_bound_cost_units": 0.0, "relative_gap": 0.0}

    size = len(costs)
    result = milp(
        costs,
        integrality=np.ones(size, dtype=int),
        bounds=Bounds(np.zeros(size), np.ones(size)),
        constraints=LinearConstraint(matrix.T, 1, np.inf),
        options={"mip_rel_gap": 0.0},
    )
    if result.status != 0:
        raise RuntimeError(f"solver did not establish optimality (status {result.status}): {result.message}")
    selected = np.flatnonzero(result.x > 0.5).tolist()
    if not isclose(float(costs[selected].sum()), result.fun, rel_tol=1e-8, abs_tol=1e-10):
        raise RuntimeError("solver objective does not match the selected sites")
    return selected, {
        "status": "optimal",
        "solver": "SciPy MILP / HiGHS",
        "scipy_version": scipy.__version__,
        "lower_bound_cost_units": result.mip_dual_bound,
        "relative_gap": result.mip_gap,
    }


def compare_selection(data: dict, variant: str) -> dict:
    site_ids = read_ids(data, "site_ids")
    settlement_ids = read_ids(data, "settlement_ids")
    raw_costs = data["site_cost_units"]
    if (not isinstance(raw_costs, list) or len(raw_costs) != len(site_ids)
            or any(type(cost) not in (int, float) for cost in raw_costs)):
        raise ValueError("site_cost_units must contain one number per site")
    costs = np.asarray(raw_costs, dtype=float)
    if not np.isfinite(costs).all() or (costs <= 0).any():
        raise ValueError("site costs must be finite and positive")

    rows = data["variants"][variant]
    if (not isinstance(rows, list) or len(rows) != len(site_ids)
            or any(not isinstance(row, list) or len(row) != len(settlement_ids) for row in rows)
            or any(type(value) is not int or value not in (0, 1) for row in rows for value in row)):
        raise ValueError("matrix must contain one binary row per site and one column per settlement")

    matrix = np.asarray(rows, dtype=bool).reshape(len(site_ids), len(settlement_ids))
    reachable = matrix.any(axis=0)
    target = matrix[:, reachable]
    greedy_indices = greedy_cover(target, costs, site_ids)
    exact_indices, solver = exact_cover(target, costs)

    def describe(selected: list[int]) -> dict:
        covered = matrix[selected].any(axis=0)
        if not np.array_equal(covered, reachable) or len(set(selected)) != len(selected):
            raise RuntimeError("selection does not cover the target set exactly as reported")
        return {
            "selected_site_count": len(selected),
            "total_cost_units": float(costs[selected].sum()),
            "covered_settlement_count": int(covered.sum()),
            "selected_sites": [
                {
                    "site_id": site_ids[index],
                    "cost_units": float(costs[index]),
                    "reachable_settlement_ids": [
                        settlement_ids[col] for col in np.flatnonzero(matrix[index])
                    ],
                }
                for index in selected
            ],
        }

    greedy = describe(greedy_indices)
    exact = {**describe(exact_indices), **solver}
    unreachable_ids = [settlement_ids[col] for col in np.flatnonzero(~reachable)]
    optimum = exact["total_cost_units"]
    cost_gap = (greedy["total_cost_units"] / optimum - 1) if optimum else None
    return {
        "scenario_id": data["scenario_id"],
        "model_variant": variant,
        "candidate_site_count": len(site_ids),
        "total_settlement_count": len(settlement_ids),
        "target": "reachable_settlements",
        "target_settlement_count": int(reachable.sum()),
        "full_cover_status": "infeasible" if unreachable_ids else "feasible",
        "unreachable_settlement_ids": unreachable_ids,
        "greedy_relative_cost_gap": cost_gap,
        "methods": {"greedy": greedy, "exact": exact},
    }


def select_sites(matrix_path: Path, variant: str, output_path: Path) -> dict:
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    result = compare_selection(data, variant)
    result["matrix_sha256"] = sha256(matrix_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output_path.parent) as temp:
        draft = Path(temp) / output_path.name
        draft.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        draft.replace(output_path)
    return result
