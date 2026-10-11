"""Empaqueta modelos, fuente y vistas tras comprobar sus informes y hashes."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
STEM = "swift_hybrid_2026_60mm"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    reviewed = json.loads((ROOT / "models/independent-review.json").read_text())
    assert reviewed["overall_geometry_validation"] == "passed"
    assert not reviewed["failed_checks"]
    for extension in ["stl", "3mf", "step"]:
        model = ROOT / "models" / f"{STEM}.{extension}"
        assert digest(model) == reviewed["files"][extension]["sha256"], extension
    stl_hash = digest(ROOT / "models" / f"{STEM}.stl")
    renders = json.loads((ROOT / "previews/render_report.json").read_text())
    ring = json.loads((ROOT / "models/keyring_validation.json").read_text())
    assert renders["source_sha256"] == stl_hash
    assert ring["source_sha256"] == stl_hash and ring["sampled_clear_sections"]

    files = [ROOT / x for x in ["README.md", "design.json", "requirements.txt", ".gitignore"]]
    files += sorted((ROOT / "tools").glob("*.py"))
    files += [ROOT / "models" / f"{STEM}.{x}" for x in ["stl", "3mf", "step"]]
    files += [ROOT / "models" / x for x in ["validation.json", "independent-review.json",
                                           "keyring_validation.json"]]
    files += [ROOT / "models/attachment_sample" / x for x in
              ["attachment_sample.stl", "attachment_sample.step", "validation.json"]]
    for view in ["front_3q", "rear_3q", "side", "top", "front", "rear"]:
        path = ROOT / "previews" / f"{view}.png"
        assert path.is_file() and path.stat().st_size > 10_000, view
        files.append(path)
    files += [ROOT / "previews" / x for x in ["render_report.json", "swift_hybrid_2026.blend"]]
    files += [ROOT / "references" / x for x in ["vehicle-research.md", "existing-models.md",
                                                "research-status.md"]]
    assert all(p.is_file() for p in files)
    checksums = "".join(f"{digest(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
    (ROOT / "SHA256SUMS").write_text(checksums, encoding="utf-8")
    files.append(ROOT / "SHA256SUMS")
    directory = ROOT / "deliverables"
    directory.mkdir(exist_ok=True)
    archive = directory / "suzuki_swift_hybrid_2026_llavero.zip"
    prefix = "suzuki_swift_hybrid_2026_llavero"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as package:
        for path in files:
            package.write(path, f"{prefix}/{path.relative_to(ROOT).as_posix()}")
    with ZipFile(archive) as package:
        assert package.testzip() is None, "Un archivo del ZIP no supera CRC."
        assert len(package.namelist()) == len(files)
    print(json.dumps({"archive":str(archive), "files":len(files),
                      "bytes":archive.stat().st_size,"sha256":digest(archive)}, indent=2))


if __name__ == "__main__":
    main()
