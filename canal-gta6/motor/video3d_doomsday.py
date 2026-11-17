# -*- coding: utf-8 -*-
"""Vídeo 3D low-poly: "6 cosas que tienes que saber antes de Vengadores: Doomsday".

Un pasillo-museo oscuro con una "estación" por dato; la cámara viaja de una a
otra. Todo el contenido 3D es original (piezas simples y la mascota del canal);
no se modela ningún personaje ni logo de Marvel.
Render rápido: Cycles con pocas muestras + eliminación de ruido, 24 fps.

Uso:  python3 video3d_doomsday.py [--solo 10,50,...]
"""
import json, math, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import doomsday  # noqa: F401  (pronunciación)
import bpy
import tres_d as T

audio.PRONUNCIA[:0] = [("Endgame", "Éndgueim"), ("Russo", "Rúso")]
audio.VELOCIDAD = 1.1
FPS = 24
RW, RH = 432, 768
SLUG = "13-doomsday-6-cosas-3d"
SALIDA = os.path.join(T.RAIZ, "salida", SLUG)
PASO = 16  # distancia entre estaciones
NUMEROS = True   # números 1..6 en las estaciones
EXTRA = {}       # estaciones nuevas: {"nombre": {"construir": f(y, anim, ctx), "animar": f(ctx)}}
EFECTOS = {"intro": "golpe", "villano": "golpe", "doom": "subida", "russo": "golpe", "portal": "boom"}

BEATS = [
    dict(e="intro", say="Seis cosas que tienes que saber antes de ver Vengadores: Doomsday."),
    dict(e="fecha", say="Uno: se estrena el 18 de diciembre de 2026. En algunos países, un día antes."),
    dict(e="villano", say="Dos: Robert Downey Jr. vuelve a Marvel… pero como el villano, Víctor von Doom."),
    dict(e="doom", say="Tres: Doom es el gran enemigo de Los 4 Fantásticos. Un genio que además domina la magia."),
    dict(e="xmen", say="Cuatro: vuelven los X-Men de las películas de siempre, con Patrick Stewart e Ian McKellen."),
    dict(e="steve", say="Cinco: Chris Evans vuelve como Steve Rogers. Se confirmó en los primeros avances."),
    dict(e="russo", say="Seis: la dirigen los hermanos Russo, los mismos de Vengadores: Endgame."),
    dict(e="portal", say="Y todo prepara Vengadores: Secret Wars, prevista para diciembre de 2027."),
    dict(e="cta", say="¿Cuál te ha sorprendido más? Te leo en comentarios. Y sígueme para más."),
]


def emision(m):
    return m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]


def construir(tiempos):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = int(os.environ.get("MUESTRAS", "6"))
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 1
    sc.cycles.transmission_bounces = 0
    sc.cycles.transparent_max_bounces = 24
    sc.cycles.use_adaptive_sampling = True
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    w = bpy.data.worlds.new("mundo"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.025, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.5

    suelo = T.mat("suelo", (0.05, 0.06, 0.08), rugoso=0.3)
    pared = T.mat("pared", (0.08, 0.09, 0.13), rugoso=0.9)
    piedra = T.mat("piedra", (0.15, 0.16, 0.19))
    alfombra = T.mat("alfombra", (0.4, 0.04, 0.06))
    oro = T.mat("oro", (1.0, 0.7, 0.2), emision=1.5, rugoso=0.3, metal=0.8)
    blanco = T.mat("blanco_txt", (0.95, 0.95, 0.9), emision=0.8)
    n_est = len(BEATS)
    largo = PASO * n_est
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, largo / 2 - 8, 0))
    bpy.context.object.scale = (24, largo + 30, 1); bpy.context.object.data.materials.append(suelo)
    T.caja("alfombra", (0, largo / 2 - 8, 0.01), (1.1, largo / 2 + 10, 0.01), alfombra)
    for sx in (-1, 1):
        T.caja("pared", (sx * 8, largo / 2 - 8, 5), (0.3, largo / 2 + 14, 5), pared)
        for k in range(n_est * 2):
            T.cilindro((sx * 5.5, -6 + k * PASO / 2, 3), 0.4, 6, piedra, lados=6)

    focos = {}

    def foco(nombre, pos, objetivo, color, energia, haz=True):
        bpy.ops.object.light_add(type="SPOT", location=pos)
        L = bpy.context.object
        L.data.color = color; L.data.spot_size = math.radians(26); L.data.spot_blend = 0.4; L.data.energy = 0
        dx, dy, dz = (objetivo[0] - pos[0], objetivo[1] - pos[1], objetivo[2] - pos[2])
        import mathutils
        L.rotation_euler = mathutils.Vector((dx, dy, dz)).to_track_quat("-Z", "Y").to_euler()
        st = None
        if haz:
            mh, st = T.mat_haz("haz_" + nombre, color)
            lg = math.sqrt(dx * dx + dy * dy + dz * dz)
            c = T.cono(((pos[0] + objetivo[0]) / 2, (pos[1] + objetivo[1]) / 2, (pos[2] + objetivo[2]) / 2),
                       math.tan(math.radians(11)) * lg, 0.05, lg, mh, lados=12)
            c.rotation_euler = L.rotation_euler
        focos[nombre] = (L, st, energia)
        return L

    def punto(pos, color, energia):
        bpy.ops.object.light_add(type="POINT", location=pos)
        o = bpy.context.object; o.data.color = color; o.data.energy = energia; o.data.shadow_soft_size = 1.5

    anim = {}  # objetos que se animan después
    for i, b in enumerate(BEATS):
        y = i * PASO
        e = b["e"]
        foco(e, (0, y - 2.5, 8.5), (0, y + 1.5, 0.8), (1.0, 0.95, 0.85), 2200)
        punto((0, y + 3.5, 3), [(0.6, 0.2, 1.0), (0.2, 1.0, 0.4), (0.3, 0.5, 1.0)][i % 3], 300)
        if e in EXTRA:
            EXTRA[e]["construir"](y, anim, dict(oro=oro, blanco=blanco, piedra=piedra, foco=foco, punto=punto))
            continue
        if NUMEROS and 1 <= i <= 6:
            num = T.texto3d(str(i), (-2.6, y + 1.0, 3.2), 1.3, oro, extr=0.15)
            anim.setdefault("numeros", []).append(num)
        if e == "intro":
            seis = T.texto3d("6", (1.2, y + 1.5, 1.0), 2.6, oro, extr=0.3)
            anim["seis"] = seis
            T.mascota_villana((-1.6, y + 1.6, 0.0))
            T.texto3d("COSAS", (1.2, y + 1.5, 0.35), 0.6, blanco)
        elif e == "fecha":
            crema = T.mat("papel", (0.92, 0.88, 0.78))
            rojo = T.mat("rojo_cal", (0.8, 0.08, 0.1))
            T.caja("cal", (0, y + 1.6, 1.9), (1.3, 0.12, 1.6), crema)
            T.caja("cal_top", (0, y + 1.5, 3.2), (1.3, 0.14, 0.35), rojo)
            T.texto3d("DIC", (0, y + 1.33, 3.0), 0.45, blanco)
            T.texto3d("18", (0, y + 1.42, 1.0), 1.5, T.mat("negro_cal", (0.02, 0.02, 0.02)), extr=0.05)
            hoja = T.caja("hoja", (0, y + 1.35, 1.9), (1.25, 0.02, 1.25), crema)
            anim["hoja"] = hoja
        elif e == "villano":
            for nombre, x, col in (("HÉROE", -2.2, (0.3, 0.55, 1.0)), ("VILLANO", 2.2, (0.25, 1.0, 0.45))):
                T.caja("ped", (x, y + 1.5, 0.6), (0.6, 0.6, 0.6), piedra)
                mi = T.mat("ic" + nombre, col, emision=3.0)
                if nombre == "HÉROE":
                    ico = T.cono((x, y + 1.5, 1.7), 0.4, 0.0, 0.15, mi, lados=5, rot=(math.radians(90), 0, 0))
                else:
                    ico = T.cilindro((x, y + 1.5, 1.55), 0.3, 0.12, mi, lados=8)
                    for k in range(4):
                        a = k * math.pi / 2 + 0.4
                        T.cono((x + math.cos(a) * 0.24, y + 1.5 + math.sin(a) * 0.24, 1.78), 0.08, 0, 0.26, mi, lados=4)
                anim["ico_" + nombre] = (ico, mi)
                T.texto3d(nombre, (x, y + 0.88, 0.55), 0.36, blanco)
                foco("v_" + nombre, (x, y - 1.0, 7.0), (x, y + 1.5, 1.6), col, 1600)
        elif e == "doom":
            morado = T.mat("trono", (0.2, 0.06, 0.32))
            T.caja("tr_b", (0, y + 2.3, 0.25), (1.6, 1.2, 0.25), piedra)
            T.caja("tr_a", (0, y + 2.5, 0.75), (1.2, 0.8, 0.25), morado)
            T.caja("tr_r", (0, y + 3.2, 2.0), (1.2, 0.2, 1.8), morado)
            T.mascota_villana((0, y + 2.3, 0.75))
            bpy.ops.mesh.primitive_torus_add(location=(0, y + 2.3, 1.9), major_radius=1.5, minor_radius=0.04,
                                             major_segments=24, minor_segments=4)
            aro = bpy.context.object; aro.data.materials.append(T.mat("magia", (0.2, 1.0, 0.45), emision=6))
            anim["aro"] = aro
            T.texto3d("GENIO + MAGIA", (0, y + 0.6, 3.6), 0.5, blanco)
        elif e == "xmen":
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.8, depth=0.3, location=(0, y + 1.8, 0.15))
            plat = bpy.context.object; plat.data.materials.append(piedra)
            t = T.texto3d("X-MEN", (0, y + 1.8, 0.4), 1.2, T.mat("xmen", (1.0, 0.85, 0.2), emision=2, metal=0.6), extr=0.2)
            anim["xmen"] = t
            for k in range(6):
                a = math.pi * (0.15 + 0.7 * k / 5)
                px, py = math.cos(a) * 3.2, y + 1.8 + math.sin(a) * 1.4
                T.caja("silla", (px, py, 0.5), (0.3, 0.3, 0.5), piedra)
                T.caja("resp", (px, py + 0.3, 1.2), (0.3, 0.05, 0.4), T.mat(f"s{k}", (0.15, 0.2, 0.5)))
        elif e == "steve":
            T.caja("ped2", (0, y + 1.6, 0.4), (1.0, 1.0, 0.4), piedra)
            T.texto3d("VUELVE", (0, y + 1.2, 2.4), 0.7, T.mat("vuelve", (1.0, 0.85, 0.3), emision=2.5), extr=0.12)
            T.texto3d("STEVE ROGERS", (0, y + 1.2, 1.3), 0.5, blanco)
            estrellas = []
            for k in range(8):
                a = k * math.pi / 4
                s = T.cono((math.cos(a) * 2.2, y + 1.6 + math.sin(a) * 0.3, 1.8 + math.sin(a) * 1.0), 0.15, 0, 0.05,
                           T.mat(f"est{k}", (1, 0.9, 0.5), emision=5), lados=5, rot=(math.radians(90), 0, 0))
                estrellas.append(s)
            anim["estrellas"] = estrellas
        elif e == "russo":
            negro = T.mat("claq_n", (0.03, 0.03, 0.03), rugoso=0.4)
            T.caja("claq", (0, y + 1.6, 1.5), (1.4, 0.1, 0.9), negro)
            bpy.ops.object.empty_add(location=(-1.4, y + 1.6, 2.45)); bisagra = bpy.context.object
            brazo = T.caja("brazo", (0, 0, 0), (1.4, 0.1, 0.12), negro)
            brazo.parent = bisagra; brazo.location = (1.4, 0, 0.12)
            for k in range(5):
                rayita = T.caja("raya", (0, 0, 0), (0.12, 0.11, 0.1), blanco)
                rayita.parent = bisagra; rayita.location = (0.35 + k * 0.55, 0, 0.12); rayita.rotation_euler = (0, math.radians(30), 0)
            T.texto3d("RUSSO", (0, y + 1.45, 1.2), 0.7, blanco, extr=0.04)
            anim["bisagra"] = bisagra
        elif e == "portal":
            aros = []
            for k, (r, col) in enumerate(((2.6, (0.2, 1.0, 0.45)), (2.0, (0.6, 0.2, 1.0)), (1.4, (0.3, 0.8, 1.0)))):
                bpy.ops.mesh.primitive_torus_add(location=(0, y + 2.5, 2.8), rotation=(math.radians(90), 0, 0),
                                                 major_radius=r, minor_radius=0.08, major_segments=32, minor_segments=4)
                o = bpy.context.object; o.data.materials.append(T.mat(f"portal{k}", col, emision=8)); aros.append(o)
            anim["aros"] = aros
            T.texto3d("SECRET WARS", (0, y + 1.2, 0.9), 0.6, blanco)
            T.texto3d("2027", (0, y + 1.2, 0.2), 0.55, oro)
        elif e == "cta":
            T.mascota_villana((0, y + 1.6, 0.0))
            T.texto3d("SÍGUEME", (0, y + 0.8, 3.3), 0.8, T.mat("sigue", (1.0, 0.25, 0.4), emision=3), extr=0.15)

    # cámara
    bpy.ops.object.empty_add(location=(0, 1.5, 1.6)); mira = bpy.context.object
    bpy.ops.object.camera_add(location=(0, -10, 2.4)); cam = bpy.context.object
    cam.data.lens = 24; sc.camera = cam
    tc = cam.constraints.new("TRACK_TO"); tc.target = mira; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

    F = lambda t: int(round(t * FPS)) + 1
    for i, (b, (t0, d)) in enumerate(zip(BEATS, tiempos)):
        y = i * PASO
        e = b["e"]
        fin = t0 + d + 0.15
        # foco principal: se enciende al llegar
        L, st, en = focos[e]
        T.clave(L.data, "energy", 0, F(max(0, t0 - 0.1))); T.clave_valor(st, 0, F(max(0, t0 - 0.1)))
        T.clave(L.data, "energy", en, F(t0 + 0.25)); T.clave_valor(st, 0.45, F(t0 + 0.25))
        # cámara: llega rápido a la estación y luego se acerca despacio (con un ligero giro)
        lado = 1.4 if i % 2 else -1.4
        T.clave(cam, "location", (lado * 2, y - 9.5, 3.2), F(t0))
        T.clave(mira, "location", (0, y + 1.5, 1.7), F(t0))
        T.clave(cam, "location", (lado * 0.6, y - 6.0, 2.3), F(t0 + 0.6))
        T.clave(cam, "location", (-lado * 0.4, y - 4.6, 2.1), F(fin - 0.05))
        T.clave(mira, "location", (0, y + 1.5, 1.8), F(fin - 0.05))
        if i + 1 < len(BEATS):   # transición: la cámara sube por encima de las piezas (no las atraviesa)
            T.clave(cam, "location", (0, y + 4.0, 7.5), F(fin + 0.03))
            T.clave(mira, "location", (0, y + PASO + 1.5, 1.7), F(fin + 0.03))
        if e in EXTRA and "animar" in EXTRA[e]:
            EXTRA[e]["animar"](dict(anim=anim, t0=t0, d=d, fin=fin, y=y, F=F, cam=cam, mira=mira, focos=focos))
        if e == "intro":
            s6 = anim["seis"]
            for k in range(0, int(fin * FPS) + 2, 6):
                T.clave(s6, "rotation_euler", (math.radians(90), 0, math.radians(-25 + 15 * math.sin(k / 10))), k + 1)
        if e == "fecha":
            h = anim["hoja"]
            T.clave(h, "location", tuple(h.location), F(t0 + 0.5))
            T.clave(h, "rotation_euler", (0, 0, 0), F(t0 + 0.5))
            T.clave(h, "location", (0.6, y - 1.5, -0.5), F(t0 + 1.4))
            T.clave(h, "rotation_euler", (math.radians(-80), math.radians(30), 0.3), F(t0 + 1.4))
        if e == "villano":
            Lh, sth, enh = focos["v_HÉROE"]; Lv, stv, env = focos["v_VILLANO"]
            mitad = t0 + d * 0.45
            T.clave(Lh.data, "energy", 0, F(t0)); T.clave_valor(sth, 0, F(t0))
            T.clave(Lh.data, "energy", enh, F(t0 + 0.2)); T.clave_valor(sth, 0.5, F(t0 + 0.2))
            T.clave(Lh.data, "energy", enh, F(mitad - 0.15)); T.clave_valor(sth, 0.5, F(mitad - 0.15))
            T.clave(Lh.data, "energy", 0, F(mitad)); T.clave_valor(sth, 0, F(mitad))
            T.clave(Lv.data, "energy", 0, F(mitad)); T.clave_valor(stv, 0, F(mitad))
            T.clave(Lv.data, "energy", env, F(mitad + 0.15)); T.clave_valor(stv, 0.5, F(mitad + 0.15))
            ih, mh = anim["ico_HÉROE"]
            T.clave_valor(emision(mh), 3, F(mitad - 0.15)); T.clave_valor(emision(mh), 0, F(mitad))
        if e == "doom":
            aro = anim["aro"]
            T.clave(aro, "rotation_euler", (0.2, 0, 0), F(t0)); T.clave(aro, "rotation_euler", (0.5, 0.3, 6.3), F(fin))
        if e == "xmen":
            t = anim["xmen"]
            T.clave(t, "rotation_euler", (math.radians(90), 0, math.radians(-40)), F(t0))
            T.clave(t, "rotation_euler", (math.radians(90), 0, math.radians(40)), F(fin))
        if e == "steve":
            for k, s in enumerate(anim["estrellas"]):
                T.clave(s, "scale", (0, 0, 0), F(t0 + 0.2 + k * 0.08)); T.clave(s, "scale", (1.4, 1.4, 1.4), F(t0 + 0.45 + k * 0.08))
        if e == "russo":
            bis = anim["bisagra"]
            T.clave(bis, "rotation_euler", (0, math.radians(-35), 0), F(t0 + 0.4))
            T.clave(bis, "rotation_euler", (0, 0, 0), F(t0 + 0.7))
        if e == "portal":
            for k, o in enumerate(anim["aros"]):
                T.clave(o, "rotation_euler", (math.radians(90), 0, 0), F(t0))
                T.clave(o, "rotation_euler", (math.radians(90), (1 if k % 2 else -1) * 6.3, 0), F(fin))
            T.clave(cam, "location", (0, y - 1.0, 2.8), F(fin - 0.05))  # la cámara entra en el portal
            T.clave(mira, "location", (0, y + 2.5, 2.8), F(fin - 0.05))
    # interpolación lineal en la rotación del aro y los portales (giro continuo)
    for o in [anim[k] for k in ("aro",) if k in anim] + anim.get("aros", []) + anim.get("giran", []):
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return sc


def main():
    os.makedirs(os.path.join(SALIDA, "frames"), exist_ok=True)
    t, tiempos, clips, subt = 0.05, [], [], []
    for b in BEATS:
        a = audio.voz(b["say"])
        d = len(a) / audio.VOZ_SR
        tiempos.append((t, d)); clips.append((t, a)); subt.append((t, d, b["say"]))
        t += d + 0.25
    total = t + 0.5
    nfr = int(total * FPS)
    print(f"[3d] {total:.1f}s → {nfr} fotogramas a {FPS} fps", flush=True)
    sc = construir(tiempos)
    sc.frame_start, sc.frame_end = 1, nfr
    sc.render.image_settings.file_format = "PNG"
    if "--solo" in sys.argv:
        for fr in [int(x) for x in sys.argv[sys.argv.index("--solo") + 1].split(",")]:
            sc.frame_set(fr); sc.render.filepath = os.path.join(SALIDA, "frames", f"prueba_{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    sc.render.filepath = os.path.join(SALIDA, "frames", "f_")
    bpy.ops.render.render(animation=True)
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    audio.sf.write(os.path.join(SALIDA, "voz.wav"), voz, audio.VOZ_SR)
    mus = audio.musica(total + 1, semilla=5, bpm=92, tono="D")
    for b, (t0, d) in zip(BEATS, tiempos):
        ef = EFECTOS.get(b["e"])
        s = audio.efecto(ef) if ef else audio.whoosh(len(b["e"]))
        te = t0 + (0.7 if b["e"] == "russo" else 0.2)
        i = int(te * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * (1.6 if ef else 0.8)
    audio.sf.write(os.path.join(SALIDA, "musica.wav"), mus, audio.MUS_SR)
    # montaje con los subtítulos arriba (mismo sistema que la demo 3D)
    T.SALIDA, T.FPS, T.RW, T.RH = SALIDA, FPS, RW, RH
    montar(total, subt)


def montar(total, subt):
    """Reutiliza T.montar pero escalando a 1080x1920 exactos."""
    T.RW, T.RH = 540, 960   # T.montar escala x2 → 1080x1920
    from PIL import Image
    fr = os.path.join(SALIDA, "frames")
    for f in sorted(os.listdir(fr)):
        if f.startswith("f_"):
            p = os.path.join(fr, f)
            Image.open(p).convert("RGB").resize((540, 960), Image.LANCZOS).save(p)
    T.montar(total, subt)
    os.replace(os.path.join(SALIDA, "demo-3d.mp4"), os.path.join(SALIDA, SLUG + ".mp4"))
    print(f"[3d] OK → {os.path.join(SALIDA, SLUG + '.mp4')}", flush=True)


if __name__ == "__main__":
    main()
