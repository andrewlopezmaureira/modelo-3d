"""Verificación de un STL binario: cierre, orientación, componentes y medidas."""

from collections import defaultdict, deque
from pathlib import Path
import argparse
import json
import struct

import numpy as np


def verify(path):
    data = Path(path).read_bytes()
    if len(data) < 84:
        raise ValueError("STL binario incompleto.")
    count = struct.unpack_from("<I", data, 80)[0]
    if count == 0 or len(data) != 84 + 50 * count:
        raise ValueError("STL sin triángulos o de longitud incorrecta.")
    vertices = []
    triangles = []
    vertex_map = {}
    edges = defaultdict(list)
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * index)
        points = np.array(values[3:12]).reshape(3, 3)
        if not np.isfinite(points).all():
            raise ValueError("Coordenadas no finitas.")
        if np.linalg.norm(np.cross(points[1] - points[0], points[2] - points[0])) < 1e-10:
            raise ValueError("Triángulo degenerado.")
        ids = []
        for point in points:
            key = tuple(np.round(point, 5))
            if key not in vertex_map:
                vertex_map[key] = len(vertices)
                vertices.append(point)
            ids.append(vertex_map[key])
        triangles.append(points)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edges[tuple(sorted((a, b)))].append((index, a, b))
    adjacency = defaultdict(set)
    for uses in edges.values():
        if len(uses) != 2:
            raise ValueError("Malla abierta o arista no manifold.")
        first, second = uses
        if first[1:] != second[1:][::-1]:
            raise ValueError("Orientación incoherente en una arista.")
        adjacency[first[0]].add(second[0])
        adjacency[second[0]].add(first[0])
    pending = set(range(count))
    components = 0
    while pending:
        components += 1
        queue = deque([pending.pop()])
        while queue:
            for neighbor in adjacency[queue.popleft()]:
                if neighbor in pending:
                    pending.remove(neighbor)
                    queue.append(neighbor)
    if components != 1:
        raise ValueError(f"Se esperaba una sola pieza; hay {components} componentes.")
    tri = np.array(triangles)
    volume = np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
    if volume <= 0:
        raise ValueError("El volumen orientado debe ser positivo.")
    points = np.array(vertices)
    return {
        "file": str(path), "triangles": count, "watertight": True,
        "consistent_winding": True, "components": components,
        "dimensions_mm": np.round(np.ptp(points, axis=0), 5).tolist(),
        "volume_mm3": round(float(volume), 5)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.stl), indent=2))
