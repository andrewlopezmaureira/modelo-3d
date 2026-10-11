"""Miniatura CAD original del Suzuki Swift Hybrid GLX Plus comercializado en 2026.

Interpretación de vistas oficiales, no CAD OEM. Unidades: mm. Frente: -X.
Ejecutar desde el checkout: python3 tools/build_swift.py
"""
from pathlib import Path
import json
import math
import os
import time
import numpy as np

os.environ.setdefault("XDG_CACHE_HOME", "/tmp/modelo-3d-cache")
import cadquery as cq
from keyring_mount import make_mount
from verify_stl import verify
from clean_exports import clean_stl, clean_3mf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "models"
LENGTH = 60.0
WIDTH = 1735 / 3860 * LENGTH
HEIGHT = 1485 / 3860 * LENGTH
WHEELBASE = 2450 / 3860 * LENGTH
WHEEL_R = (406.4 + 2 * 185 * .55) / 3860 * LENGTH / 2
WHEEL_Z = WHEEL_R - .12  # Base plana de ~2,1 mm tras recortar a Z=0.
FRONT_AXLE = 11.20
REAR_AXLE = FRONT_AXLE + WHEELBASE
HALF_WIDTH = WIDTH / 2


def log(message):
    print(message, flush=True)


def loft(sections):
    wires = [cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in points], close=True)
             for x, points in sections]
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])


def polygon_prism(points, vector):
    wire = cq.Wire.makePolygon([cq.Vector(*p) for p in points], close=True)
    return cq.Workplane("XY").newObject([
        cq.Solid.extrudeLinear(wire, [], cq.Vector(*vector))])


def cylinder(radius, height, origin, axis):
    return cq.Workplane("XY").newObject([
        cq.Solid.makeCylinder(radius, height, cq.Vector(*origin), cq.Vector(*axis))])


def stroke(points, radius):
    pieces = []
    for a, b in zip(points, points[1:]):
        v = cq.Vector(*b) - cq.Vector(*a)
        pieces.append(cq.Solid.makeCylinder(radius, v.Length, cq.Vector(*a), v.normalized()))
    for p in points:
        pieces.append(cq.Solid.makeSphere(radius, cq.Vector(*p)))
    shape = cq.Workplane("XY").newObject([pieces[0]])
    for part in pieces[1:]:
        shape = shape.union(part)
    return shape


def body_shape():
    specs = [
        (0, 9.7, 3.9, 11.8), (1.5, 11.9, 3.3, 12.6),
        (5.5, 13.15, 2.7, 13.65), (12, HALF_WIDTH, 2.7, 14.25),
        (20, 13.35, 2.7, 14.55), (31, 13.35, 2.7, 14.65),
        (43, HALF_WIDTH, 2.7, 14.75), (53, 13.25, 2.7, 14.15),
        (58.5, 12.25, 3.2, 13.35), (60, 10.5, 3.7, 12.7)]
    sections = []
    for x, w, bottom, top in specs:
        p = [(-.85*w,bottom),(-.98*w,bottom+.85),(-w,top-2.1),
             (-.95*w,top-.65),(-.67*w,top),(0,top+.12),
             (.67*w,top),(.95*w,top-.65),(w,top-2.1),
             (.98*w,bottom+.85),(.85*w,bottom),(0,bottom)]
        sections.append((x,p))
    return loft(sections)


def cabin_shape():
    specs = [(19,12.6,11.5,15.25),(23,12.8,11.3,18.5),
             (28.5,12.9,10.65,22.3),(34,12.85,10.55,HEIGHT),
             (44,12.9,10.65,HEIGHT),(49.5,12.7,10.65,22.7),
             (53,12.3,10.55,21.4),(56.5,11.9,10.6,18.65),
             (58.5,11.1,10.0,15.0)]
    sections=[]
    for x, wb, wt, top in specs:
        belt=min(14.65,top-1.3)
        p=[(-wb,12.65),(-wb,belt),(-wt-.4,top-.9),(-wt,top-.25),
           (-wt*.62,top),(wt*.62,top),(wt,top-.25),(wt+.4,top-.9),
           (wb,belt),(wb,12.65)]
        sections.append((x,p))
    return loft(sections)


def side_cavity(points, side):
    # Plane inclinado que sigue la inclinación de los cristales laterales.
    exterior=[(x,side*(15-.30*(z-14)),z) for x,z in points]
    return polygon_prism(exterior,(0,-side*2.7,0))


def windows(car):
    front=[(23.8,15.35),(29.3,21.6),(35.8,21.75),(35.8,15.45)]
    rear=[(37.05,15.45),(37.05,21.75),(46.8,21.5),(51.35,18.4),(52.25,15.6)]
    for side in [-1,1]:
        for polygon in [front,rear]:
            car=car.cut(side_cavity(polygon,side))
    # Parabrisas y luneta, con marcos gruesos para FDM.
    frontglass=[(20.2,-10.6,15.5),(20.2,10.6,15.5),
                (27.6,9.8,21.6),(27.6,-9.8,21.6)]
    car=car.cut(polygon_prism(frontglass,(-4.0,0,0)))
    rearglass=[(57.65,-9.6,15.5),(57.65,9.6,15.5),
               (52.6,9.3,21.2),(52.6,-9.3,21.2)]
    car=car.cut(polygon_prism(rearglass,(4.0,0,0)))
    return car


def wheels(car):
    for x in [FRONT_AXLE,REAR_AXLE]:
        for side in [-1,1]:
            arch=cylinder(WHEEL_R+.65,5.0,(x,side*10.35,WHEEL_Z),(0,side,0))
            car=car.cut(arch)
    for x in [FRONT_AXLE,REAR_AXLE]:
        for side in [-1,1]:
            tire=cylinder(WHEEL_R,3.95,(x,side*9.42,WHEEL_Z),(0,side,0))
            hubcut=cylinder(3.30,.72,(x,side*13.50,WHEEL_Z),(0,-side,0))
            tire=tire.cut(hubcut)
            # Cinco radios con cara plana y núcleo sólido; sin piezas móviles.
            center=cylinder(1.12,.65,(x,side*12.80,WHEEL_Z),(0,side,0))
            tire=tire.union(center)
            for i in range(5):
                angle=math.radians(i*72+15)
                def point(r,t):
                    return (x+r*math.cos(angle+t),side*12.80,WHEEL_Z+r*math.sin(angle+t))
                p=[point(.90,-.24),point(3.33,-.16),point(3.33,.16),point(.90,.24)]
                tire=tire.union(polygon_prism(p,(0,side*.60,0)))
            car=car.union(tire)
    return car


def face_features(car):
    # Parrilla de la nueva generación: ovalada, a diferencia de la anterior.
    grill=[(-6.9,5.7),(-8.3,6.8),(-8.6,8.8),(-7.6,10.4),
           (-5.8,11.0),(5.8,11.0),(7.6,10.4),(8.6,8.8),
           (8.3,6.8),(6.9,5.7)]
    grill=[(y*.90,z) for y,z in grill]
    cavity=polygon_prism([(-.5,y,z) for y,z in grill],(3.5,0,0))
    car=car.cut(cavity)
    # Retícula hexagonal en relieve, con pared mínima de 0,4 mm.
    grille_limit=polygon_prism([(-.5,y,z) for y,z in grill],(4.0,0,0))
    for row,z in enumerate([6.35,8.22,10.09]):
        for y in [-6.5,-4.34,-2.18,-.02,2.14,4.30,6.46]:
            y=y+(1.08 if row%2 else 0)
            def hexwire(radius):
                return cq.Wire.makePolygon([cq.Vector(2.65,
                    y+radius*math.cos(math.radians(30+i*60)),
                    z+radius*math.sin(math.radians(30+i*60))) for i in range(6)],close=True)
            ring=cq.Workplane("XY").newObject([cq.Solid.extrudeLinear(
                hexwire(1.25),[hexwire(.79)],cq.Vector(.55,0,0))])
            car=car.union(ring.intersect(grille_limit))
    # Placa delantera y emblema S, ambos en relieve.
    plate=cq.Workplane("XY").box(.75,7.8,1.9).translate((2.70,0,6.75))
    car=car.union(plate)
    logo=[(-.7,12.9),(.25,12.9),(.75,12.5),(-.3,12.05),
          (.45,11.75),(.8,12.05),(-.1,11.4),(-.8,11.9),(.2,12.4)]
    logo_points=[]
    for y,z in logo:
        z=12.15+(z-11.4)*.86
        logo_points.append((2.8*(z-12.15),y,z))
    car=car.union(polygon_prism(logo_points,(1.0,0,0)))
    for side in [-1,1]:
        head=[(7.8,10.55),(8.4,13.0),(11.8,13.0),(12.3,12.4),
              (11.9,10.2),(8.2,10.0)]
        def light_x(y,z):return 2.35+.70*(y-8)+.20*(z-10.5)
        car=car.cut(polygon_prism([(light_x(y,z),side*y,z) for y,z in head],(-4.5,0,0)))
        # Contorno DRL: tramo bajo y lateral exterior, engrosado a 0,55 mm.
        led=[(light_x(y,z)-.12,side*y,z) for y,z in [(8.3,10.4),(11.2,10.5),(11.85,12.0)]]
        car=car.union(stroke(led,.29))
    # Toma de aire baja y línea envolvente del capó.
    car=car.cut(cq.Workplane("XY").box(3.4,16.8,1.0).translate((.65,0,4.65)))
    bonnet=[(2.25,-9.5,13.1),(2.25,-5.0,13.0),(2.25,0,13.0),
            (2.25,5.0,13.0),(2.25,9.5,13.1)]
    car=car.cut(stroke(bonnet,.23))
    return car


def rear_features(car):
    # Faros traseros cuadrados con esquinas achaflanadas, en los hombros.
    for side in [-1,1]:
        p=[(7.8,11.7),(10.9,11.8),(12.0,14.0),(10.6,15.6),(8.15,15.35)]
        def light_x(y,z):return 59.3-.55*(y-8)-.45*(z-12)
        car=car.cut(polygon_prism([(light_x(y,z),side*y,z) for y,z in p],(4.0,0,0)))
        line=[(light_x(y,z)+.12,side*y,z) for y,z in
              [(8.5,14.6),(10.6,14.6),(11.1,12.6),(8.5,12.6)]]
        car=car.union(stroke(line,.28))
    # Hueco de placa en el parachoques trasero, no en la luneta.
    car=car.cut(cq.Workplane("XY").box(3,9.2,2.5).translate((59.9,0,6.15)))
    car=car.union(cq.Workplane("XY").box(.65,7.5,1.55).translate((58.45,0,6.15)))
    for side in [-1,1]:
        car=car.cut(cq.Workplane("XY").box(3.0,3.0,.65).translate((59.5,side*8.3,5.6)))
    # Contorno del portón y limpiaparabrisas integrado, sin elementos finos sueltos.
    hatch=[(58.5,-8.0,15.0),(59.3,-8.0,13.8),(59.55,-7.9,13.0),
           (59.92,-7.7,11.0),(59.92,-6.4,9.3),(59.92,6.4,9.3),
           (59.92,7.7,11.0),(59.55,7.9,13.0),(59.3,8.0,13.8),(58.5,8.0,15.0)]
    car=car.cut(stroke(hatch,.22))
    rear_logo=[(-.7,13.5),(.25,13.5),(.75,13.18),(-.3,12.82),
               (.45,12.58),(.8,12.82),(-.1,12.3),(-.8,12.70),(.2,13.10)]
    car=car.cut(polygon_prism([(59.4-(z-12.3),y,z) for y,z in rear_logo],(3,0,0)))
    # La luneta es un rebaje abierto: el limpiaparabrisas se apoya en su fondo.
    wiper_x=57.65+(52.6-57.65)*(.75/5.7)+.10
    car=car.union(stroke([(wiper_x,-3.4,16.25),(wiper_x,3.0,16.25)],.3))
    spoiler=cq.Workplane("XY").box(4.6,20.5,.95).translate((51.4,0,22.4))
    spoiler=spoiler.edges("|Z").fillet(.6)
    car=car.union(spoiler)
    return car


def side_features(car):
    for side in [-1,1]:
        def path(coords):return [(x,side*13.28,z) for x,z in coords]
        for p in [[(24.2,14.2),(23.7,10.8),(24.0,5.0),(35.8,4.55)],
                  [(36.6,14.25),(36.6,4.55),(44.0,4.55),(46.4,7.9),(51.6,14.2)]]:
            car=car.cut(stroke(path(p),.28))
        # Manillas convencionales visibles en ambas puertas de esta generación.
        for x in [32.2,46.1]:
            handle=cq.Workplane("XY").box(2.7,1.3,.72).translate((x,side*12.95,13.85))
            handle=handle.edges("|Y").fillet(.20)
            car=car.union(handle)
        # Faldón lateral GLX Plus, sencillo y unido al piso.
        sill=cq.Workplane("XY").box(25.4,1.4,.9).translate((30.25,side*12.55,3.5))
        car=car.union(sill)
        # Espejos engrosados y fusionados al pilar delantero.
        mirror=cq.Workplane("XY").box(3.2,3.7,1.65).translate((24.3,side*12.85,15.5))
        mirror=mirror.edges().fillet(.55)
        car=car.union(mirror)
    fuelring=(cylinder(1.27,2.7,(54.0,-14.8,12.35),(0,1,0))
              .cut(cylinder(.91,3.0,(54.0,-14.9,12.35),(0,1,0))))
    car=car.cut(fuelring)
    return car


def check_stage(car,name):
    if not car.val().isValid():
        raise RuntimeError(f"Geometría CAD inválida en {name}.")
    parts=car.solids().vals()
    if len(parts)!=1:
        raise RuntimeError(f"{name}: {len(parts)} sólidos, se necesita una pieza.")
    log(f"{name}: sólido válido, {car.val().Volume():.1f} mm³")


def main():
    started=time.monotonic()
    OUT.mkdir(exist_ok=True)
    log("Carrocería y cabina")
    car=body_shape().union(cabin_shape()).clean()
    # Recorta pequeñas sobreoscilaciones del loft a las dimensiones de referencia.
    clip=cq.Workplane("XY").box(LENGTH,WIDTH,HEIGHT).translate((LENGTH/2,0,HEIGHT/2))
    car=car.intersect(clip).clean()
    check_stage(car,"Base")
    for name,operation in [("Cristales",windows),("Ruedas",wheels),
                           ("Frente",face_features),("Trasera",rear_features),
                           ("Laterales",side_features)]:
        car=operation(car).clean()
        check_stage(car,name)
    # Plano pequeño en las ruedas para apoyar la impresión.
    above_ground=cq.Workplane("XY").box(80,40,HEIGHT).translate((32,0,HEIGHT/2))
    car=car.intersect(above_ground).clean()
    car_without_mount=car
    mount=make_mount(base_z=3.0)
    car=car.union(mount).clean()
    check_stage(car,"Sujeción integrada")
    bore=cylinder(1.99,5,(62,0,2.5),(0,0,1))
    assert car.intersect(bore).val().Volume()<1e-6,"El orificio debe quedar libre."
    body_bound=car_without_mount.val().BoundingBox()
    assert abs(body_bound.xlen-LENGTH)<.01
    cq.exporters.export(car,str(OUT/"swift_hybrid_2026_60mm.step"))
    cq.exporters.export(car,str(OUT/"swift_hybrid_2026_60mm.stl"),
                        tolerance=.025,angularTolerance=.07)
    cq.exporters.export(car,str(OUT/"swift_hybrid_2026_60mm.3mf"),
                        tolerance=.025,angularTolerance=.07)
    export_cleanup={"stl":clean_stl(OUT/"swift_hybrid_2026_60mm.stl"),
                    "3mf":clean_3mf(OUT/"swift_hybrid_2026_60mm.3mf")}
    restored=cq.importers.importStep(str(OUT/"swift_hybrid_2026_60mm.step"))
    assert restored.val().isValid() and len(restored.solids().vals())==1
    precise_volume=car.val().Volume(tol=1e-9)
    restored_volume=restored.val().Volume(tol=1e-9)
    # STEP vuelve a parametrizar superficies B-spline y sus curvas de recorte.
    # Contraste relativo de volumen más contraste de cada límite a 1 micrómetro.
    volume_relative_difference=abs(restored_volume-precise_volume)/precise_volume
    assert volume_relative_difference<1e-4, (precise_volume,restored_volume)
    original_box,restored_box=car.val().BoundingBox(),restored.val().BoundingBox()
    conservative_bbox_differences={key:abs(getattr(original_box,key)-getattr(restored_box,key))
        for key in ['xmin','xmax','ymin','ymax','zmin','zmax']}
    # BBox de B-splines sin teselar puede incluir el casco de sus puntos de
    # control. Compara los límites de superficies teseladas con el mismo ajuste.
    def surface_bounds(shape):
        vertices,_=shape.tessellate(.025,.07)
        xyz=np.array([v.toTuple() for v in vertices])
        return np.stack((xyz.min(axis=0),xyz.max(axis=0)))
    original_bounds=surface_bounds(car.val())
    restored_bounds=surface_bounds(restored.val())
    step_surface_bounds_difference=float(np.max(np.abs(original_bounds-restored_bounds)))
    assert step_surface_bounds_difference<.001, (original_bounds,restored_bounds)
    report=verify(OUT/"swift_hybrid_2026_60mm.stl")
    report.update({"cad_valid":True,"cad_solids":1,"step_round_trip":"passed",
                   "vehicle":"Swift Hybrid GLX Plus, exterior vendido en 2026",
                   "car_length_mm":round(body_bound.xlen,5),
                   "nominal_body_width_mm":round(WIDTH,5),
                   "height_mm":round(HEIGHT,5),"wheelbase_mm":round(WHEELBASE,5),
                   "ring_hole_mm":4.0,"hole_clear":True,
                   "cad_volume_mm3":round(precise_volume,5),
                   "step_volume_difference_mm3":abs(restored_volume-precise_volume),
                   "step_volume_relative_difference":volume_relative_difference,
                   "step_volume_relative_tolerance":1e-4,
                   "step_surface_bounds_difference_mm":step_surface_bounds_difference,
                   "conservative_cad_bbox_differences_mm":conservative_bbox_differences,
                   "export_cleanup":export_cleanup,
                   "physical_print_test":"not_performed",
                   "geometry_origin":"original CAD interpreted from official photographs",
                   "build_seconds":round(time.monotonic()-started,2)})
    (OUT/"validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    log(json.dumps(report,indent=2))


if __name__=="__main__":main()
