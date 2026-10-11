"""Remove only exactly zero-area facets introduced by CAD tessellation.

The helpers preserve every surviving vertex coordinate, normal, face index,
component transform, and package entry. They do not weld vertices, repair
holes, change winding, or remove a small but nonzero triangle. Bounds and
signed volume are checked before replacing the export atomically.
"""

from pathlib import Path
import argparse
import io
import json
import os
import struct
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np


def _measure(triangles):
    if not len(triangles) or not np.isfinite(triangles).all():
        raise ValueError("An export must contain finite triangles.")
    points = triangles.reshape(-1, 3)
    return {
        "bounds": np.stack((points.min(axis=0), points.max(axis=0))),
        "volume": float(np.einsum(
            "ij,ij->i", triangles[:, 0],
            np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6.0),
    }


def _keep_and_report(triangles):
    cross = np.cross(triangles[:, 1] - triangles[:, 0],
                     triangles[:, 2] - triangles[:, 0])
    # Comparing components directly avoids underflow when squaring an area.
    keep = np.any(cross != 0.0, axis=1)
    before, after = _measure(triangles), _measure(triangles[keep])
    if not np.array_equal(before["bounds"], after["bounds"]):
        raise ValueError("Removing zero-area facets would change the bounds.")
    difference = abs(before["volume"] - after["volume"])
    volume_tolerance = max(1e-8, abs(before["volume"]) * 1e-12)
    if difference > volume_tolerance:
        raise ValueError("Removing zero-area facets would change the volume.")
    return keep, {
        "before": len(triangles),
        "removed": int(np.count_nonzero(~keep)),
        "remaining": int(np.count_nonzero(keep)),
        "bounds_preserved": True,
        "bounds": before["bounds"].tolist(),
        "signed_volume_before": before["volume"],
        "signed_volume_after": after["volume"],
        "signed_volume_difference": difference,
        "criterion": "exactly zero cross product; no area threshold",
    }


def _atomic_replace(path, contents):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(contents)
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def clean_stl(path):
    """Sanitize a binary STL in place and return measurable removal counts."""
    path = Path(path)
    contents = path.read_bytes()
    if len(contents) < 84:
        raise ValueError("Incomplete binary STL.")
    count = struct.unpack_from("<I", contents, 80)[0]
    if len(contents) != 84 + 50 * count:
        raise ValueError("Binary STL facet count does not match its length.")
    record_type = np.dtype([
        ("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)),
        ("attribute", "<u2"),
    ])
    records = np.frombuffer(contents, dtype=record_type, count=count, offset=84)
    keep, report = _keep_and_report(records["vertices"].astype(np.float64))
    if report["removed"]:
        cleaned = (contents[:80] + struct.pack("<I", report["remaining"])
                   + records[keep].tobytes())
        _atomic_replace(path, cleaned)
    return {"file": str(path), **report}


def clean_3mf(path):
    """Sanitize each 3MF mesh while retaining resources and build transforms."""
    path = Path(path)
    original = path.read_bytes()
    reports = []
    replacements = {}
    with ZipFile(io.BytesIO(original)) as package:
        for name in package.namelist():
            if not name.lower().endswith(".model"):
                continue
            root = ET.fromstring(package.read(name))
            namespace = root.tag.split("}", 1)[0].lstrip("{")
            ns = {"m": namespace}
            for obj in root.findall("m:resources/m:object", ns):
                mesh = obj.find("m:mesh", ns)
                if mesh is None:
                    continue
                vertex_elements = mesh.findall("m:vertices/m:vertex", ns)
                parent = mesh.find("m:triangles", ns)
                if parent is None:
                    raise ValueError("A 3MF mesh has no triangle collection.")
                triangle_elements = parent.findall("m:triangle", ns)
                vertices = np.array([
                    [float(element.attrib[axis]) for axis in ("x", "y", "z")]
                    for element in vertex_elements], dtype=np.float64)
                indices = np.array([
                    [int(element.attrib[key]) for key in ("v1", "v2", "v3")]
                    for element in triangle_elements], dtype=np.int64)
                if not len(indices) or np.any(indices < 0) or np.any(indices >= len(vertices)):
                    raise ValueError("Invalid vertex references in 3MF mesh.")
                keep, report = _keep_and_report(vertices[indices])
                for element, preserve in zip(triangle_elements, keep):
                    if not preserve:
                        parent.remove(element)
                reports.append({"package_entry": name,
                                "object_id": obj.attrib.get("id"), **report})
            if any(report["removed"] for report in reports
                   if report["package_entry"] == name):
                ET.register_namespace("", namespace)
                replacements[name] = ET.tostring(
                    root, encoding="utf-8", xml_declaration=True)
        if not reports:
            raise ValueError("No meshes found in the 3MF package.")
        if replacements:
            cleaned = io.BytesIO()
            with ZipFile(cleaned, "w") as destination:
                destination.comment = package.comment
                for entry in package.infolist():
                    destination.writestr(
                        entry, replacements.get(entry.filename,
                                                package.read(entry.filename)))
            _atomic_replace(path, cleaned.getvalue())
    return {"file": str(path), "removed": sum(r["removed"] for r in reports),
            "remaining": sum(r["remaining"] for r in reports),
            "bounds_preserved": True, "objects": reports}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    arguments = parser.parse_args()
    cleaner = {".stl": clean_stl, ".3mf": clean_3mf}.get(
        arguments.export.suffix.lower())
    if cleaner is None:
        parser.error("Expected a binary .stl or a .3mf file.")
    print(json.dumps(cleaner(arguments.export), indent=2))
