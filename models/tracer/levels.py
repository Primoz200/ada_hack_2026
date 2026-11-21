"""Tracer level geometry, loaded from shared/tracer_levels.json (shared with the frontend)."""
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

LEVELS_FILE = Path(__file__).resolve().parents[2] / "shared" / "tracer_levels.json"


class Level:
    """A level path resampled densely by arc length, with tangents, normals and curvature."""

    def __init__(self, spec: dict, step: float = 2.0):
        self.id = spec["level_id"]
        self.version = spec["version"]
        self.channel_width = float(spec["channel_width"])
        self.time_limit_s = float(spec["time_limit_s"])

        pts = np.asarray(spec["path"], dtype=float)
        seglen = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0.0], np.cumsum(seglen)])
        self.length = float(cum[-1])

        s = np.append(np.arange(0.0, self.length, step), self.length)
        self.s = s
        self.xy = np.column_stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])])

        # Heading from the raw polyline (piecewise constant), so sharp corners stay sharp,
        # then smoothed to get a physically plausible turning profile.
        seg_idx = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(seglen) - 1)
        seg_dir = np.diff(pts, axis=0) / seglen[:, None]
        heading = np.unwrap(np.arctan2(seg_dir[seg_idx, 1], seg_dir[seg_idx, 0]))
        heading = gaussian_filter1d(heading, sigma=10.0 / step, mode="nearest")  # ~10 units
        self.tangent = np.column_stack([np.cos(heading), np.sin(heading)])
        self.normal = np.column_stack([-self.tangent[:, 1], self.tangent[:, 0]])
        # Signed curvature (rad / unit). Positive = turning towards +normal.
        self.curvature = np.gradient(heading, s)

        self._tree = cKDTree(self.xy)

    def point_at(self, s_query):
        """Path point and normal at arc length(s)."""
        s_query = np.clip(s_query, 0.0, self.length)
        x = np.interp(s_query, self.s, self.xy[:, 0])
        y = np.interp(s_query, self.s, self.xy[:, 1])
        nx = np.interp(s_query, self.s, self.normal[:, 0])
        ny = np.interp(s_query, self.s, self.normal[:, 1])
        return np.column_stack([x, y]), np.column_stack([nx, ny])

    def curvature_at(self, s_query):
        return np.interp(np.clip(s_query, 0.0, self.length), self.s, self.curvature)

    def distance_to_path(self, xy):
        """Distance of each point to the path (accurate to ~step/2) and the arc position of the nearest point."""
        d, idx = self._tree.query(np.asarray(xy, dtype=float))
        return d, self.s[idx]


def load_levels(path: Path = LEVELS_FILE) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {spec["level_id"]: Level(spec) for spec in data["levels"]}
