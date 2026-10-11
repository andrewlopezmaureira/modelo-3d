"""Sujeción paramétrica para integrar en el modelo del auto, en milímetros.

Este módulo define únicamente la sujeción; la carrocería está en build_swift.py.
La muestra exportada por este módulo es una probeta de la unión y el orificio.
"""

from pathlib import Path
import json
import os

os.environ.setdefault("XDG_CACHE_HOME", "/tmp/modelo-3d-cache")

import cadquery as cq


def make_mount(rear_x=60.0, base_z=3.0, hole_diameter=4.0,
               outer_diameter=9.0, thickness=3.2):
    """Crea un anillo horizontal que solapa 2,5 mm con la zaga del auto."""
    if hole_diameter <= 0 or outer_diameter - hole_diameter < 4.0:
        raise ValueError("El orificio necesita al menos 2 mm de pared radial.")
    if thickness < 3.0:
        raise ValueError("El soporte FDM necesita al menos 3 mm de espesor.")
    return (cq.Workplane("XY", origin=(rear_x + 2.0, 0, base_z))
            .circle(outer_diameter / 2)
            .circle(hole_diameter / 2)
            .extrude(thickness))


def validate_sample(sample, mount):
    """Comprueba un sólido fusionado, un agujero libre y una unión efectiva."""
    assert len(sample.solids().vals()) == 1, "La sujeción debe estar fusionada."
    assert sample.val().isValid(), "El sólido CAD no es válido."
    bore_probe = (cq.Workplane("XY", origin=(62.0, 0, 2.5))
                  .circle(1.99).extrude(4.2))
    interference = sample.intersect(bore_probe).val().Volume()
    assert interference < 1e-6, "El orificio de la argolla está obstruido."
    joining_probe = cq.Workplane("XY").box(3, 6, 3).translate((59, 0, 4.6))
    overlap_volume = mount.intersect(joining_probe).val().Volume()
    assert overlap_volume > 1.0, "No existe solape útil para unir al auto."
    bounds = sample.val().BoundingBox()
    assert abs(bounds.xmax - 66.5) < 1e-6
    return {
        "cad_valid": True,
        "solids": 1,
        "hole_clear_mm": 4.0,
        "radial_wall_mm": 2.5,
        "attachment_thickness_mm": 3.2,
        "rear_extent_mm": bounds.xmax,
        "joining_probe_overlap_mm3": round(overlap_volume, 4),
        "physical_load_test": "not_performed",
        "complete_vehicle_model": False
    }


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "models" / "attachment_sample"
    output.mkdir(parents=True, exist_ok=True)
    mount = make_mount()
    # Bloque de comprobación: representa únicamente la zona de unión.
    test_block = cq.Workplane("XY").box(6, 12, 3.2).translate((57, 0, 4.6))
    sample = test_block.union(mount).clean()
    report = validate_sample(sample, mount)
    cq.exporters.export(sample, str(output / "attachment_sample.step"))
    cq.exporters.export(sample, str(output / "attachment_sample.stl"),
                        tolerance=0.02, angularTolerance=0.08)
    restored = cq.importers.importStep(str(output / "attachment_sample.step"))
    assert restored.val().isValid() and len(restored.solids().vals()) == 1
    assert abs(restored.val().Volume() - sample.val().Volume()) < 1e-5
    report["step_round_trip"] = "passed"
    (output / "validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
