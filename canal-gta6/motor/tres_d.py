# -*- coding: utf-8 -*-
"""Estilo 3D low-poly con Blender (módulo bpy) + Cycles.

Sala del trono oscura con focos y haces de luz, vitrinas, cómics que caen,
castillo en una montaña y la mascota del canal (la tele) como villana.
Cámara que recorre la escena; subtítulos arriba palabra a palabra.
Todo el contenido 3D es original y se construye por código.

Uso:  python3 tres_d.py      → salida/demo-3d/demo-3d.mp4
"""
import json, math, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import doomsday  # noqa: F401  (pronunciación de nombres)
import bpy

audio.VELOCIDAD = 1.1
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FUENTES = os.path.join(RAIZ, "fuentes")
SALIDA = os.path.join(RAIZ, "salida", "demo-3d")
FPS = 30
RW, RH = 540, 960            # render 3D; se escala x2 al montar
MUESTRAS = int(os.environ.get("MUESTRAS", "12"))

BEATS = [
    dict(say="Robert Downey Jr. vuelve a Marvel… ¡como el villano!"),
    dict(say="Fue Iron Man durante once años… y ahora se cambia de bando."),
    dict(say="Se llama Víctor von Doom."),
    dict(say="Nació en los cómics en 1962,"),
    dict(say="y es el rey de su propio país: Latveria."),
]


# ------------------------------------------------------------- utilidades de Blender
def mat(nombre, color, emision=0.0, rugoso=0.6, metal=0.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rugoso
    b.inputs["Metallic"].default_value = metal
    if emision:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emision
    return m


def mat_haz(nombre, color):
    """Haz de luz falso: emisión mezclada con transparencia (barato en Cycles)."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = 0.0
    mix.inputs["Fac"].default_value = 0.07
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m, em.inputs["Strength"]


def caja(nombre, loc, esc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = nombre
    o.scale = esc
    o.data.materials.append(m)
    return o


def cilindro(loc, r, h, m, lados=6, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=lados, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.data.materials.append(m)
    return o


def cono(loc, r1, r2, h, m, lados=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=lados, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.data.materials.append(m)
    return o


def texto3d(txt, loc, tam, m, rot=(math.radians(90), 0, 0), extr=0.08):
    cu = bpy.data.curves.new("t_" + txt, type="FONT")
    cu.body = txt
    cu.font = bpy.data.fonts.load(os.path.join(FUENTES, "Anton-Regular.ttf"), check_existing=True)
    cu.size = tam
    cu.extrude = extr
    cu.align_x = "CENTER"
    o = bpy.data.objects.new("t_" + txt, cu)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(m)
    return o


def clave(obj, prop, valor, frame, idx=None):
    setattr(obj, prop, valor)
    obj.keyframe_insert(data_path=prop, frame=frame)


def clave_valor(sock, valor, frame):
    sock.default_value = valor
    sock.keyframe_insert("default_value", frame=frame)


# ------------------------------------------------------------- escena
def mascota_villana(base, capa=True, corona=True, ojos_color=(0.2, 1.0, 0.4)):
    """La tele del canal en 3D, con capa, corona y ojos verdes (personaje original)."""
    x, y, z = base
    crema = mat("crema", (0.85, 0.78, 0.62), rugoso=0.5)
    pantalla = mat("pantalla", (0.02, 0.03, 0.04), rugoso=0.2)
    negro = mat("negro", (0.01, 0.01, 0.01))
    oro = mat("oro", (0.9, 0.62, 0.15), rugoso=0.3, metal=0.9)
    ojos = mat("ojos", ojos_color, emision=6.0)
    gris = mat("gris_ant", (0.5, 0.5, 0.55), metal=0.6, rugoso=0.4)
    if capa:
        caja("capa", (x, y + 0.45, z + 0.9), (0.95, 0.05, 1.0), mat("capa", (0.25, 0.08, 0.4), rugoso=0.8), rot=(math.radians(-8), 0, 0))
    caja("cuerpo", (x, y, z + 1.25), (0.8, 0.45, 0.65), crema)
    caja("pantalla", (x - 0.12, y - 0.46, z + 1.25), (0.55, 0.02, 0.5), pantalla)
    o_iz = caja("ojo_i", (x - 0.35, y - 0.49, z + 1.35), (0.13, 0.02, 0.045), ojos)
    o_de = caja("ojo_d", (x + 0.11, y - 0.49, z + 1.35), (0.13, 0.02, 0.045), ojos)
    if corona:
        caja("ceja_i", (x - 0.35, y - 0.5, z + 1.47), (0.15, 0.02, 0.03), negro, rot=(0, math.radians(-15), 0))
    if corona:
        caja("ceja_d", (x + 0.11, y - 0.5, z + 1.47), (0.15, 0.02, 0.03), negro, rot=(0, math.radians(15), 0))
    caja("sonrisa", (x - 0.12, y - 0.49, z + 1.08), (0.18, 0.02, 0.03), ojos)
    for bx, c in ((0.62, (0.95, 0.75, 0.2)), (0.62, (0.3, 0.75, 0.95))):
        pass
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.08, location=(x + 0.62, y - 0.46, z + 1.45))
    bpy.context.object.data.materials.append(mat("boton1", (0.95, 0.75, 0.2)))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.08, location=(x + 0.62, y - 0.46, z + 1.2))
    bpy.context.object.data.materials.append(mat("boton2", (0.3, 0.75, 0.95)))
    for sx in (-1, 1):
        cilindro((x + sx * 0.3, y, z + 2.15), 0.03, 0.6, gris, rot=(0, math.radians(sx * 25), 0))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.08, location=(x + sx * 0.43, y, z + 2.43))
        bpy.context.object.data.materials.append(mat("punta", (0.95, 0.4, 0.6) if sx > 0 else (0.95, 0.8, 0.3), emision=2))
    if corona:
        cilindro((x, y, z + 1.98), 0.35, 0.16, oro, lados=10)
        for k in range(5):
            a = k * 2 * math.pi / 5
            cono((x + math.cos(a) * 0.3, y + math.sin(a) * 0.3, z + 2.15), 0.09, 0.0, 0.25, oro, lados=4)
    # patas
    for sx in (-0.4, 0.4):
        caja("pata", (x + sx, y, z + 0.3), (0.08, 0.08, 0.3), negro)
    return ojos


def construir(tiempos):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = MUESTRAS
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    w = bpy.data.worlds.new("mundo"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.015, 0.03, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

    suelo = mat("suelo", (0.06, 0.07, 0.09), rugoso=0.35)
    pared = mat("pared", (0.09, 0.1, 0.14), rugoso=0.9)
    piedra = mat("piedra", (0.16, 0.17, 0.2))
    alfombra = mat("alfombra", (0.45, 0.04, 0.06))
    oro = mat("oro2", (0.9, 0.62, 0.15), rugoso=0.3, metal=0.9)
    morado = mat("morado", (0.2, 0.06, 0.32))
    # sala
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); bpy.context.object.data.materials.append(suelo)
    caja("fondo", (0, 7, 5), (14, 0.3, 5), pared)
    for sx in (-1, 1):
        caja("lado", (sx * 9, 0, 5), (0.3, 14, 5), pared)
        for k in range(4):
            cilindro((sx * 5.5, -6 + k * 4, 3), 0.45, 6, piedra, lados=6)
    caja("alfombra", (0, -3, 0.01), (1.2, 8, 0.01), alfombra)
    # trono
    caja("trono_base", (0, 3.4, 0.25), (1.6, 1.2, 0.25), piedra)
    caja("trono_asiento", (0, 3.6, 0.75), (1.2, 0.8, 0.25), morado)
    caja("trono_resp", (0, 4.3, 2.0), (1.2, 0.2, 1.8), morado)
    for sx in (-1, 1):
        cono((sx * 1.1, 4.3, 4.0), 0.25, 0.0, 0.6, oro, lados=4)
    ojos = mascota_villana((0, 3.4, 0.75))
    # focos con haz visible
    def foco(pos, objetivo, color, energia):
        bpy.ops.object.light_add(type="SPOT", location=pos)
        L = bpy.context.object
        L.data.color = color
        L.data.spot_size = math.radians(32)
        L.data.spot_blend = 0.4
        dx, dy, dz = (objetivo[0] - pos[0], objetivo[1] - pos[1], objetivo[2] - pos[2])
        L.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) + math.pi / 2)
        L.data.energy = 0
        mh, st = mat_haz(f"haz{len(bpy.data.materials)}", color)
        largo = math.sqrt(dx * dx + dy * dy + dz * dz)
        c = cono(((pos[0] + objetivo[0]) / 2, (pos[1] + objetivo[1]) / 2, (pos[2] + objetivo[2]) / 2),
                 math.tan(math.radians(14)) * largo, 0.05, largo, mh, lados=16)
        c.rotation_euler = L.rotation_euler
        return L, st, energia
    f_trono = foco((0, 0.5, 8.5), (0, 3.4, 0.8), (1.0, 0.95, 0.85), 2500)
    for pos, color, en_ in (((0, 5.5, 3.5), (0.6, 0.2, 1.0), 400), ((5, -2, 2.5), (0.2, 1.0, 0.4), 250),
                            ((-5, -2, 2.5), (0.3, 0.5, 1.0), 250), ((0, -4, 4), (1.0, 0.6, 0.3), 150)):
        bpy.ops.object.light_add(type="POINT", location=pos)
        bpy.context.object.data.color = color; bpy.context.object.data.energy = en_
        bpy.context.object.data.shadow_soft_size = 1.5
    # vitrinas: héroe (azul) y villano (verde)
    vidrio = bpy.data.materials.new("vidrio"); vidrio.use_nodes = True
    vb = vidrio.node_tree.nodes["Principled BSDF"]
    vb.inputs["Transmission Weight"].default_value = 1.0
    vb.inputs["Roughness"].default_value = 0.05
    vitrinas = {}
    for nombre, x, col, icono in (("HÉROE", -4.0, (0.3, 0.55, 1.0), "estrella"), ("VILLANO", 4.0, (0.25, 1.0, 0.45), "corona")):
        caja("pedestal", (x, -1, 0.6), (0.6, 0.6, 0.6), piedra)
        caja("vitrina", (x, -1, 1.75), (0.55, 0.55, 0.55), vidrio)
        mi = mat("icono" + nombre, col, emision=3.0)
        if icono == "estrella":
            cono((x, -1, 1.75), 0.35, 0.0, 0.15, mi, lados=5, rot=(math.radians(90), 0, 0))
        else:
            cilindro((x, -1, 1.6), 0.25, 0.12, mi, lados=8)
            for k in range(4):
                a = k * math.pi / 2 + 0.4
                cono((x + math.cos(a) * 0.2, -1 + math.sin(a) * 0.2, 1.8), 0.07, 0, 0.22, mi, lados=4)
        texto3d(nombre, (x, -1.62, 0.55), 0.38, mat("txt" + nombre, (0.95, 0.95, 0.9), emision=0.6))
        vitrinas[nombre] = foco((x, -2.2, 7.5), (x, -1, 1.7), col, 1800)
    # cómics que caerán y el 1962
    comics = []
    for k in range(7):
        mc = mat(f"comic{k}", [(0.95, 0.8, 0.3), (0.9, 0.3, 0.25), (0.3, 0.6, 0.95)][k % 3], rugoso=0.7)
        o = caja(f"comic{k}", (0, 0, 30), (0.32, 0.02, 0.46), mc)
        caja(f"banda{k}", (0, 0, 30), (0.3, 0.025, 0.07), mat(f"banda{k}", (0.95, 0.95, 0.9)))
        comics.append((o, bpy.context.object))
    t1962 = texto3d("1962", (0, -6.5, -3), 1.2, mat("oro1962", (1.0, 0.75, 0.2), emision=2.5, metal=0.8), extr=0.2)
    # Latveria: montaña y castillo al fondo, fuera de la sala
    roca = mat("roca", (0.18, 0.24, 0.2))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=9, location=(0, 40, -3))
    mont = bpy.context.object; mont.scale = (1.6, 1.2, 0.9); mont.data.materials.append(roca)
    cast = mat("castillo", (0.3, 0.32, 0.38))
    tejado = mat("tejado", (0.12, 0.4, 0.22))
    caja("muralla", (0, 38, 6.2), (2.2, 1.2, 0.9), cast)
    for sx in (-2.2, 2.2):
        cilindro((sx, 38, 7.0), 0.6, 3.0, cast, lados=8)
        cono((sx, 38, 9.0), 0.8, 0.0, 1.3, tejado, lados=8)
    cilindro((0, 38.5, 7.9), 0.7, 2.6, cast, lados=8); cono((0, 38.5, 9.8), 0.95, 0, 1.6, tejado, lados=8)
    bandera = caja("bandera", (0.55, 38.5, 11.3), (0.5, 0.02, 0.3), mat("bandera", (0.2, 0.95, 0.4), emision=1.5))
    cilindro((0, 38.5, 11.0), 0.03, 1.4, mat("mastil", (0.7, 0.7, 0.7)))
    bpy.ops.object.light_add(type="SUN", location=(0, 30, 20)); sol = bpy.context.object
    sol.data.energy = 0; sol.rotation_euler = (math.radians(50), 0, math.radians(20)); sol.data.color = (0.6, 1.0, 0.7)
    # cámara con objetivo
    bpy.ops.object.empty_add(location=(0, 3.4, 1.5)); mira = bpy.context.object
    bpy.ops.object.camera_add(location=(0, -16, 3)); cam = bpy.context.object
    cam.data.lens = 24
    sc.camera = cam
    tc = cam.constraints.new("TRACK_TO"); tc.target = mira; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

    # --------------------------------------------------------- animación por beats
    F = lambda t: int(round(t * FPS)) + 1
    (t0, d0), (t1, d1), (t2, d2), (t3, d3), (t4, d4) = tiempos
    L, st, en = f_trono
    # beat 1: se enciende el foco del trono y la cámara avanza
    for (fr, e_, s_) in ((F(0), 0, 0), (F(0.35), en, 1.6), (F(t2 - 0.05), en, 1.6), (F(t2), en, 0.0)):
        clave(L.data, "energy", e_, fr); clave_valor(st, s_, fr)
    clave(cam, "location", (0, -16, 3.0), F(0)); clave(mira, "location", (0, 3.4, 1.6), F(0))
    clave(cam, "location", (0, -5.5, 2.2), F(t1 - 0.2)); clave(mira, "location", (0, 3.4, 1.6), F(t1 - 0.2))
    # beat 2: paneo de la vitrina del héroe (se apaga) a la del villano (se enciende)
    Lh, sth, enh = vitrinas["HÉROE"]; Lv, stv, env = vitrinas["VILLANO"]
    clave(Lh.data, "energy", 0, F(t1 - 0.01)); clave_valor(sth, 0, F(t1 - 0.01))
    clave(Lh.data, "energy", enh, F(t1 + 0.1)); clave_valor(sth, 1.4, F(t1 + 0.1))
    mitad = t1 + d1 * 0.5
    clave(Lh.data, "energy", enh, F(mitad - 0.2)); clave_valor(sth, 1.4, F(mitad - 0.2))
    clave(Lh.data, "energy", 0, F(mitad)); clave_valor(sth, 0, F(mitad))
    clave(Lv.data, "energy", 0, F(mitad)); clave_valor(stv, 0, F(mitad))
    clave(Lv.data, "energy", env, F(mitad + 0.15)); clave_valor(stv, 1.4, F(mitad + 0.15))
    clave(cam, "location", (-3.2, -5.0, 2.2), F(t1)); clave(mira, "location", (-4.0, -1, 1.5), F(t1))
    clave(cam, "location", (-1.5, -5.4, 2.4), F(mitad - 0.2)); clave(mira, "location", (-4.0, -1, 1.6), F(mitad - 0.3))
    clave(cam, "location", (3.2, -5.0, 2.2), F(t2 - 0.1)); clave(mira, "location", (4.0, -1, 1.6), F(t2 - 0.2))
    # beat 3: primer plano de la cara, los ojos se encienden a tope
    bo = ojos.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    clave_valor(bo, 6, F(t2)); clave_valor(bo, 25, F(t2 + 0.5)); clave_valor(bo, 10, F(t3))
    clave(cam, "location", (0.0, -0.4, 2.1), F(t2)); clave(mira, "location", (-0.1, 3.4, 2.0), F(t2))
    clave(cam, "location", (-0.1, 1.2, 2.05), F(t3 - 0.05)); clave(mira, "location", (-0.1, 3.4, 2.0), F(t3 - 0.05))
    # beat 4: los cómics caen alrededor del 1962
    clave(t1962, "location", (0, -6.5, -3), F(t3)); clave(t1962, "location", (0, -6.5, 1.2), F(t3 + 0.5))
    clave(cam, "location", (0, -11.5, 1.9), F(t3)); clave(mira, "location", (0, -6.5, 1.6), F(t3))
    clave(cam, "location", (0, -10.5, 2.1), F(t4)); clave(mira, "location", (0, -6.5, 1.6), F(t4))
    rng = np.random.default_rng(3)
    for k, (o, banda) in enumerate(comics):
        x = rng.uniform(-2.2, 2.2); yy = -6.0 + rng.uniform(-0.5, 1.5)
        ini = t3 + k * 0.12
        for ob, dz in ((o, 0), (banda, 0.3)):
            clave(ob, "location", (x, yy - 0.03 * (ob is banda), 9 + dz), F(ini))
            clave(ob, "rotation_euler", (0, 0, 0), F(ini))
            clave(ob, "location", (x, yy - 0.03 * (ob is banda), 0.5 + rng.uniform(0, 2.5) + dz), F(ini + 0.9))
            clave(ob, "rotation_euler", (rng.uniform(-0.6, 0.6), rng.uniform(-0.8, 0.8), rng.uniform(-1, 1)), F(ini + 0.9))
    # beat 5: la cámara sale volando hacia el castillo de Latveria
    clave(sol.data, "energy", 0, F(t4)); clave(sol.data, "energy", 4, F(t4 + 0.4))
    clave(cam, "location", (0, 20, 14), F(t4 + 0.6)); clave(mira, "location", (0, 38, 8), F(t4 + 0.4))
    clave(cam, "location", (6, 28, 10), F(t4 + d4 + 0.5))
    for k in range(int((t4 + d4 + 1) * 4)):
        clave(bandera, "rotation_euler", (0, 0, math.sin(k) * 0.25), F(k / 4))
    # la cámara atraviesa la pared del fondo en el beat 5: la ocultamos entonces
    fondo = bpy.data.objects["fondo"]
    fondo.hide_render = False; fondo.keyframe_insert("hide_render", frame=F(t4))
    fondo.hide_render = True; fondo.keyframe_insert("hide_render", frame=F(t4) + 1)
    return sc


# ------------------------------------------------------------- montaje
def main():
    os.makedirs(SALIDA, exist_ok=True)
    frames_dir = os.path.join(SALIDA, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    t, tiempos, clips, subt = 0.05, [], [], []
    for b in BEATS:
        a = audio.voz(b["say"])
        d = len(a) / audio.VOZ_SR
        tiempos.append((t, d)); clips.append((t, a)); subt.append((t, d, b["say"]))
        t += d + 0.15
    total = t + 0.6
    nfr = int(total * FPS)
    print(f"[3d] {total:.1f}s → {nfr} fotogramas", flush=True)
    sc = construir(tiempos)
    sc.frame_start, sc.frame_end = 1, nfr
    sc.render.filepath = os.path.join(frames_dir, "f_")
    sc.render.image_settings.file_format = "PNG"
    if "--solo" in sys.argv:   # prueba: unos fotogramas sueltos
        for fr in [int(x) for x in sys.argv[sys.argv.index("--solo") + 1].split(",")]:
            sc.frame_set(fr); sc.render.filepath = os.path.join(frames_dir, f"prueba_{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    bpy.ops.render.render(animation=True)
    json.dump(dict(total=total, tiempos=tiempos, subt=subt), open(os.path.join(SALIDA, "tiempos.json"), "w"))
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    audio.sf.write(os.path.join(SALIDA, "voz.wav"), voz, audio.VOZ_SR)
    mus = audio.musica(total + 1, semilla=5, bpm=88, tono="D")
    (t0, d0), (t1, d1), (t2, d2), (t3, d3), (t4, d4) = tiempos
    for te, s in ((0.35, audio.efecto("golpe")), (t1 + d1 * 0.5, audio.efecto("golpe")), (t2 + 0.1, audio.efecto("subida")),
                  (t3 + 0.1, audio.whoosh(2)), (t4 + 0.1, audio.whoosh(3))):
        i = int(te * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * 1.6
    audio.sf.write(os.path.join(SALIDA, "musica.wav"), mus, audio.MUS_SR)
    print("[3d] render terminado; montando…", flush=True)
    montar(total, subt)


def montar(total, subt):
    from PIL import Image, ImageDraw, ImageFont
    W, H = RW * 2, RH * 2
    f_b = ImageFont.truetype(os.path.join(FUENTES, "Anton-Regular.ttf"), 92)
    palabras = []
    for t0, d, frase in subt:
        ws = frase.split()
        pesos = [len(w) + 2 for w in ws]
        tt = t0
        for w, p in zip(ws, pesos):
            palabras.append((tt, w, t0))
            tt += d * p / sum(pesos)
    final = os.path.join(SALIDA, "demo-3d.mp4")
    frames_dir = os.path.join(SALIDA, "frames")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", os.path.join(SALIDA, "voz.wav"), "-i", os.path.join(SALIDA, "musica.wav"),
                           "-filter_complex",
                           f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
                           "[2:a]volume=0.35[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[md];"
                           "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for fi in range(n):
        tg = fi / FPS
        ruta = os.path.join(frames_dir, f"f_{fi + 1:04d}.png")
        im = Image.open(ruta).convert("RGB").resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        # palabras de la frase actual ya dichas (máx. 3 en pantalla, como en la referencia)
        act = [i for i, (t0, w, ini) in enumerate(palabras) if t0 <= tg]
        if act:
            k = act[-1]
            ini = palabras[k][2]
            grupo = [i for i in range(max(0, k - 2), k + 1) if palabras[i][2] == ini]
            txt = [palabras[i][1] for i in grupo]
            ancho = sum(d.textlength(w + " ", font=f_b) for w in txt)
            x = (W - ancho) / 2
            for j, w in enumerate(txt):
                actual = j == len(txt) - 1
                col = (255, 255, 255) if actual else (150, 150, 160)
                d.text((x + 3, 214 + 4), w, font=f_b, fill=(0, 0, 0))
                d.text((x, 214), w, font=f_b, fill=col)
                x += d.textlength(w + " ", font=f_b)
        if tg < 3:
            f_a = ImageFont.truetype(os.path.join(FUENTES, "Jersey10-Regular.ttf"), 40)
            txt = "Canal de fans. Sin relación con Marvel ni Disney."
            d.text(((W - d.textlength(txt, font=f_a)) / 2, 1700), txt, font=f_a, fill=(210, 210, 215))
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()
    print(f"[3d] OK → {final}", flush=True)


if __name__ == "__main__":
    main()
