"""Studio renders of a millimetre STL with Blender 4.3, without a GPU.

Usage:
  blender -b --python tools/render_model.py -- models/swift_hybrid_2026_60mm.stl \
      --output previews --save-blend previews/swift_hybrid_2026.blend

X is the longitudinal axis; front is -X, rear +X, and Z is up.
The STL is displayed exactly as supplied: this script does not alter its shape.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stl", type=Path)
    parser.add_argument("--output", type=Path, default=Path("previews"))
    parser.add_argument("--save-blend", type=Path)
    parser.add_argument("--size", type=int, default=1000)
    parser.add_argument("--samples", type=int, default=96)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--views", nargs="+", choices=["front_3q", "rear_3q", "front", "rear", "side", "top"],
                        default=["front_3q", "rear_3q", "side", "top"])
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(argv)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, target, power, size):
    lamp = bpy.data.lights.new(name, "AREA")
    lamp.energy = power
    lamp.shape = "DISK"
    lamp.size = size
    obj = bpy.data.objects.new(name, lamp)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


def material(name, rgba, roughness=0.7):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = rgba
    node.inputs["Roughness"].default_value = roughness
    return mat


def main():
    args = arguments()
    stl = args.stl.resolve()
    if not stl.is_file():
        raise FileNotFoundError(stl)
    source_sha256 = hashlib.sha256(stl.read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.wm.stl_import(filepath=str(stl), global_scale=0.001,
                          use_mesh_validate=True, forward_axis="Y", up_axis="Z")
    model = bpy.context.object
    model.name = "Suzuki Swift Hybrid 2026 — supplied printable mesh"
    bpy.context.view_layer.update()
    points = [model.matrix_world @ Vector(v) for v in model.bound_box]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    dims = hi - lo
    # Centred studio coordinates do not change dimensions or mesh geometry.
    model.location += Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    target = Vector((0.0, 0.0, dims.z * 0.48))
    model.data.materials.clear()
    model.data.materials.append(material("Solid light grey — relief inspection", (0.54, 0.58, 0.62, 1), 0.56))
    for polygon in model.data.polygons:
        polygon.use_smooth = False

    span = max(dims)
    bpy.ops.mesh.primitive_plane_add(size=span * 10, location=(0, 0, -span * 0.002))
    plane = bpy.context.object
    plane.name = "Studio floor"
    plane.data.materials.append(material("Warm neutral backdrop", (0.77, 0.78, 0.8, 1)))
    power_scale = (span / 0.0665) ** 2
    area_light("Large key", (-span * 1.4, -span * 1.5, span * 2.8), target, 0.25 * power_scale, span * 2.8)
    area_light("Soft fill", (span * 1.4, span * 1.6, span * 1.7), target, 0.13 * power_scale, span * 3.0)
    area_light("Roof rim", (span * 1.4, -span * 0.4, span * 3.0), target, 0.18 * power_scale, span * 2.0)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "Orthographic inspection camera"
    camera.data.type = "ORTHO"
    camera.data.lens = 55
    camera.data.clip_start = span / 1000
    camera.data.clip_end = span * 100
    scene = bpy.context.scene
    scene.camera = camera
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    # The cloud Blender build has Cycles CPU, but no OpenImageDenoise.
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.threads_mode = "FIXED"
    scene.render.threads = args.threads
    scene.render.resolution_x = args.size
    scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    world_nodes = scene.world.node_tree.nodes
    world_links = scene.world.node_tree.links
    world_bg = world_nodes.get("Background")
    world_bg.inputs["Color"].default_value = (0.72, 0.76, 0.82, 1)
    world_bg.inputs["Strength"].default_value = 0.25
    # A light camera backdrop keeps exact side/front views as readable as the
    # elevated views, while preserving the same ambient studio illumination.
    camera_bg = world_nodes.new("ShaderNodeBackground")
    camera_bg.inputs["Color"].default_value = (0.77, 0.78, 0.8, 1)
    camera_bg.inputs["Strength"].default_value = 0.8
    light_path = world_nodes.new("ShaderNodeLightPath")
    world_mix = world_nodes.new("ShaderNodeMixShader")
    world_links.new(light_path.outputs["Is Camera Ray"], world_mix.inputs[0])
    world_links.new(world_bg.outputs["Background"], world_mix.inputs[1])
    world_links.new(camera_bg.outputs["Background"], world_mix.inputs[2])
    world_links.new(world_mix.outputs[0], world_nodes.get("World Output").inputs["Surface"])

    directions = {
        "front_3q": Vector((-1.45, -1.65, 0.95)),
        "rear_3q": Vector((1.45, 1.65, 0.95)),
        "front": Vector((-3, 0, 0)),
        "rear": Vector((3, 0, 0)),
        "side": Vector((0, -2.5, 0.0)),
        "top": Vector((0, -0.001, 3)),
    }
    def set_view(view):
        direction = directions[view].normalized()
        camera.location = target + direction * span * 4
        aim(camera, target)
        # Orthographic fit for each camera includes the entire attachment.
        inverse_rotation = camera.rotation_euler.to_matrix().transposed()
        local_points = [inverse_rotation @ (p - Vector(((lo.x + hi.x) / 2,
                            (lo.y + hi.y) / 2, lo.z)) - target) for p in points]
        view_width = max(p.x for p in local_points) - min(p.x for p in local_points)
        view_height = max(p.y for p in local_points) - min(p.y for p in local_points)
        camera.data.ortho_scale = max(view_width, view_height) * 1.28

    outputs = []
    for view in args.views:
        set_view(view)
        output = args.output / f"{view}.png"
        scene.render.filepath = str(output.resolve())
        bpy.ops.render.render(write_still=True)
        outputs.append(str(output.resolve()))
    if args.save_blend:
        set_view("front_3q")
        args.save_blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend.resolve()))
    report = {"source": str(stl), "source_sha256": source_sha256,
              "dimensions_mm": [round(v * 1000, 5) for v in dims],
              "renderer": "Blender Cycles CPU", "pixels": args.size, "images": outputs,
              "mesh_altered": False}
    report["source_changed_during_render"] = hashlib.sha256(stl.read_bytes()).hexdigest() != source_sha256
    (args.output / "render_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["source_changed_during_render"]:
        raise RuntimeError("The source STL changed during rendering; rerun after the final export completes")


if __name__ == "__main__":
    main()
