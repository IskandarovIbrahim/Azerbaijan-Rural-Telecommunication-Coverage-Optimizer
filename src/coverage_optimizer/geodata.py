"""Read mapped demand, road geometry and elevation for the Quba pilot."""

from math import hypot
from pathlib import Path

import numpy as np
import osmium
from pyproj import Transformer
import rasterio
from rasterio.warp import Resampling, reproject

RURAL_PLACES = {"village", "hamlet"}
ROAD_CLASSES = {"primary", "secondary", "tertiary", "unclassified", "residential", "service", "track"}


class PilotOSM(osmium.SimpleHandler):
    def __init__(self, to_metric: Transformer, center: tuple[float, float], radius: float):
        super().__init__()
        self.to_metric = to_metric
        self.center = center
        self.radius = radius
        self.settlements: list[dict] = []
        self.segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
        # The pinned pilot lies near Xinaliq. The window includes roads outside the AOI.
        inverse = Transformer.from_crs(to_metric.target_crs, 4326, always_xy=True)
        x, y = center
        search = radius + 10_000
        self.road_bounds = inverse.transform_bounds(x - search, y - search, x + search, y + search)

    def node(self, node):
        if node.tags.get("place") not in RURAL_PLACES or not node.location.valid():
            return
        name = node.tags.get("name:az") or node.tags.get("name")
        if not name:
            return
        x, y = self.to_metric.transform(node.lon, node.lat)
        distance = hypot(x - self.center[0], y - self.center[1])
        if distance <= self.radius:
            source_id = f"osm:node:{node.id}"
            self.settlements.append({
                "settlement_id": source_id,
                "source_id": source_id,
                "name": name,
                "place": node.tags["place"],
                "demand_weight": 1,
                "distance_from_center_m": round(distance, 2),
                "point": (node.lon, node.lat),
                "metric_point": (x, y),
            })

    def way(self, way):
        if way.tags.get("highway") not in ROAD_CLASSES:
            return
        if any(way.tags.get(tag) in {"private", "no"} for tag in ("access", "motor_vehicle")):
            return
        left, bottom, right, top = self.road_bounds
        previous = None
        for node in way.nodes:
            if not node.location.valid():
                previous = None
                continue
            point = (node.lon, node.lat)
            if previous is not None and previous != point:
                lon, lat = point
                old_lon, old_lat = previous
                if (min(lon, old_lon) <= right and max(lon, old_lon) >= left
                        and min(lat, old_lat) <= top and max(lat, old_lat) >= bottom):
                    self.segments.append((self.to_metric.transform(*previous), self.to_metric.transform(*point)))
            previous = point


def load_boundary_check(path: Path):
    """Load a WGS84 GeoJSON boundary and return a point-in-boundary predicate."""
    from shapely import Point, from_geojson
    from shapely.prepared import prep

    geometry = from_geojson(path.read_text(encoding="utf-8"))
    if geometry.is_empty or geometry.area <= 0 or not geometry.is_valid:
        raise ValueError(f"invalid boundary geometry: {path.name}")
    boundary = prep(geometry)

    def covers_point(lon_lat: tuple[float, float]) -> bool:
        return boundary.covers(Point(lon_lat))

    return covers_point


def distance_to_roads(point: tuple[float, float], segments: np.ndarray) -> float | None:
    if not len(segments):
        return None
    starts = segments[:, 0]
    directions = segments[:, 1] - starts
    offsets = np.asarray(point) - starts
    fraction = np.clip(np.sum(offsets * directions, axis=1) / np.sum(directions**2, axis=1), 0, 1)
    nearest_offsets = offsets - fraction[:, None] * directions
    return float(np.min(np.linalg.norm(nearest_offsets, axis=1)))


def project_tiles(
    paths: list[Path], shape: tuple[int, int], transform, crs: str, *, mask: bool = False
) -> np.ndarray:
    destination = np.full(shape, np.nan, dtype=np.float32)
    for path in paths:
        with rasterio.open(path) as source:
            if source.crs is None:
                raise ValueError(f"source raster has no CRS: {path.name}")
            reproject(
                source=rasterio.band(source, 1),
                destination=destination,
                dst_transform=transform,
                dst_crs=crs,
                dst_nodata=np.nan,
                init_dest_nodata=False,
                resampling=Resampling.nearest if mask else Resampling.bilinear,
            )
    return destination
