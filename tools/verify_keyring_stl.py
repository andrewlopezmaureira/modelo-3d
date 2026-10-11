"""Independent sampled cross-section check of the 4 mm key-ring opening.

Coordinates and diameters are millimetres. This checks the exported STL rather
than calling the CAD generator. It complements (does not replace) solid and
watertight-mesh validation, and does not test physical strength.
"""

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


def check(path, center=(62.0, 0.0), diameter=4.0, z_min=3.05, z_max=6.15):
    data = Path(path).read_bytes()
    if len(data) < 84:
        raise ValueError("Incomplete binary STL")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise ValueError("Expected a binary STL")
    dtype = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)),
                      ("attribute", "<u2")])
    tri = np.frombuffer(data, dtype=dtype, count=count, offset=84)["vertices"].astype(float)
    origin = np.array(center)
    results = []
    for z in np.linspace(z_min, z_max, 7):
        faces = tri[(tri[:, :, 2].min(1) < z) & (tri[:, :, 2].max(1) > z)]
        segments = []
        for face in faces:
            points = []
            for i, j in [(0, 1), (1, 2), (2, 0)]:
                if (face[i, 2] - z) * (face[j, 2] - z) < 0:
                    point = face[i] + (z - face[i, 2]) / (face[j, 2] - face[i, 2]) * (face[j] - face[i])
                    points.append(point[:2])
            if len(points) == 2:
                segments.append(points)
        if not segments:
            raise ValueError(f"No closed cross-section at Z={z} mm")
        seg = np.array(segments)
        start = seg[:, 0] - origin
        edge = seg[:, 1] - seg[:, 0]
        first_hits, parity = [], []
        for theta in np.linspace(0, 2 * np.pi, 180, endpoint=False) + 0.000173:
            ray = np.array([np.cos(theta), np.sin(theta)])
            denominator = ray[0] * edge[:, 1] - ray[1] * edge[:, 0]
            stable = np.abs(denominator) > 1e-10
            distance = np.divide(start[:, 0] * edge[:, 1] - start[:, 1] * edge[:, 0],
                                 denominator, out=np.full(len(edge), np.nan), where=stable)
            fraction = np.divide(start[:, 0] * ray[1] - start[:, 1] * ray[0],
                                 denominator, out=np.full(len(edge), np.nan), where=stable)
            hits = np.sort(distance[stable & (distance > 0) & (fraction >= 0) & (fraction <= 1)])
            if not len(hits):
                raise ValueError("A ray did not intersect the key-ring wall")
            hits = hits[np.r_[True, np.diff(hits) > 1e-4]]
            first_hits.append(float(hits[0]))
            parity.append(len(hits) % 2)
        results.append({
            "z_mm": round(float(z), 6),
            "minimum_clear_radius_mm": round(min(first_hits), 6),
            "maximum_clear_radius_mm": round(max(first_hits), 6),
            "center_in_material_by_ray_parity": any(parity),
        })
    valid = all(abs(result["minimum_clear_radius_mm"] - diameter / 2) < 0.03
                and abs(result["maximum_clear_radius_mm"] - diameter / 2) < 0.03
                and not result["center_in_material_by_ray_parity"] for result in results)
    return {"source": str(path), "source_sha256": hashlib.sha256(data).hexdigest(),
            "probe_center_xy_mm": list(center),
            "nominal_hole_diameter_mm": diameter, "rays_per_section": 180,
            "sections": results, "sampled_clear_sections": valid,
            "physical_load_test": "not_performed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = check(args.stl)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    if not report["sampled_clear_sections"]:
        raise SystemExit("The sampled key-ring opening does not match its 4 mm specification")
