# -*- coding: utf-8 -*-
"""Blackjack (21) y el equipo del MIT que contaba cartas, en 3D limpio (Blender Workbench), con el formato del vídeo
de fútbol: texto de la voz arriba, marcador «TÚ · CRUPIER», etiquetas en escena y portada.
Datos: reglas básicas del blackjack (acercarse a 21 sin pasarse; figuras = 10; as = 1 u 11; se juega contra el crupier;
as + carta de 10 de entrada = blackjack). Equipo del MIT: empezó en 1979 a partir de un curso sobre juegos de azar del
periodo IAP del MIT; contaban cartas (sistema Hi-Lo: 2-6 = +1, 7-9 = 0, 10-as = -1) en equipo: «observadores» que apostaban
poco y avisaban con señales a un «gran apostador». Ganaron millones durante años; los casinos los identificaron y les
prohibieron la entrada. Contar cartas no es ilegal, pero los casinos pueden echarte. Su historia inspiró el libro
«Bringing Down the House» (2002) y la película «21» (2008).
Uso: python blackjack3d.py [--muestra]"""
import math, os, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import audio
import plano as PL
import futbol3d as FB
from futbol3d import mat, caja, cil, esfera, vacio, jugador, clave, ruta, F, fuente, cursiva, etiqueta, texto_arriba
import bpy
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(AQUI)
SLUG = "38-blackjack-y-el-equipo-del-mit"
SALIDA = os.path.join(RAIZ, "salida", SLUG)
FPS = 30
W, H = 1080, 1920
RW, RH = 720, 1280            # render 3D (se escala al montar)
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

audio.PRONUNCIA[:0] = [("MIT", "eme i te"), ("Hi-Lo", "Jai Lou"), ("blackjack", "blákyak"), ("Blackjack", "Blákyak"), ("Las Vegas", "Las Végas")]

BEATS = [
    dict(say="Unos estudiantes del MIT ganaron millones al blackjack… y sin hacer trampa.", etiqueta=("¿SIN TRAMPA?", "amarillo")),
    dict(say="Primero, cómo se juega: tienes que acercarte a veintiuno sin pasarte.", hud=(17, None)),
    dict(say="Las figuras valen diez, y el as vale uno u once: lo que más te convenga.", hud=(17, None)),
    dict(say="Y no juegas contra los demás: juegas contra el crupier.", hud=(17, 9)),
    dict(say="Pides carta o te plantas. Pero si te pasas de veintiuno, pierdes.", hud=(23, 9), etiqueta=("TE PASAS", "rojo"), golpe=0.55),
    dict(say="Y si de entrada sacas un as y una figura… ¡blackjack!", hud=(21, None), etiqueta=("¡BLACKJACK!", "verde"), golpe=0.7),
    dict(say="Ahora viene lo bueno.", etiqueta=("LO BUENO", "amarillo")),
    dict(say="En 1979, unos alumnos del MIT aprendieron a contar cartas.", etiqueta=("MIT · 1979", "amarillo")),
    dict(say="Las cartas bajas suman uno. Las altas restan uno.", cuenta_fija=True),
    dict(say="Si la cuenta sube, quedan muchas cartas altas en la baraja… y la ventaja pasa a ti.", cuenta=(0, 8)),
    dict(say="Unos contaban apostando poco… y con una señal llamaban al que apostaba fuerte.", etiqueta=("LA SEÑAL", "amarillo")),
    dict(say="Así ganaron millones en Las Vegas durante años.", etiqueta=("MILLONES", "verde"), golpe=0.4),
    dict(say="Y ojo: contar cartas no es ilegal… pero los casinos te pueden echar.", etiqueta=("NO ES ILEGAL", "verde"), etiqueta2=("PERO TE PUEDEN ECHAR", "rojo")),
    dict(say="Al final los descubrieron, y su historia inspiró la película veintiuno.", etiqueta=("LA PELÍCULA «21»", "amarillo")),
    dict(say="¿Te atreverías a contar cartas? Comenta, y sígueme para más.", etiqueta=("¿TE ATREVERÍAS?", "amarillo")),
]


def tiempos():
    t = 0.05
    out = []
    for b in BEATS:
        a = audio.voz(b["say"])
        d = len(a) / audio.VOZ_SR
        out.append(dict(b, t0=t, dur=d + 0.2, audio=a, palabras=PL.tiempos_palabras(b["say"], t, d)))
        t += d + 0.2
    return out, t + 0.6


# ------------------------------------------------------------- escena
FONT = {}


def texto3d(txt, loc, tam, color, rot=(0, 0, 0)):
    if "dv" not in FONT:
        FONT["dv"] = bpy.data.fonts.load(DEJAVU)
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.data.body = txt
    o.data.font = FONT["dv"]
    o.data.size = tam
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"
    o.data.extrude = 0.0008
    o.data.materials.append(mat("t" + str(color), color))
    return o


CW, CH = 0.2, 0.28   # tamaño de carta (exagerado para que se lea)
ZM = 0.93            # altura de la mesa


def carta(rango, palo):
    root = vacio((0, -20, ZM))
    base = caja((0, 0, 0.002), (CW / 2, CH / 2, 0.002), mat("carta", (250, 250, 246)), root)
    dors = caja((0, 0, -0.0005), (CW / 2 - 0.004, CH / 2 - 0.004, 0.0004), mat("dorso", (170, 30, 50)), root)
    rojo = palo in "♥♦"
    c = (210, 30, 40) if rojo else (20, 20, 26)
    t1 = texto3d(rango, (0, 0.03, 0.0045), 0.13, c); t1.parent = root
    t2 = texto3d(palo, (0, -0.075, 0.0045), 0.09, c); t2.parent = root
    return root


def ocultar(obj, desde, hasta=None):
    """Oculta en render un objeto y sus hijos fuera de [desde, hasta)."""
    for o in [obj] + list(obj.children_recursive):
        for fr_, v in ((0, True), (desde - 1, True), (desde, False)) + (((hasta - 1, False), (hasta, True)) if hasta else ()):
            o.hide_render = v
            o.keyframe_insert("hide_render", frame=max(0, fr_))


ZAPATO = (0.95, 0.72, ZM + 0.08)


def repartir(c, t, dest, cara=True, dur=0.35, quitar=None):
    f0 = F(t)
    ocultar(c, f0, F(quitar) if quitar else None)
    clave(c, "location", ZAPATO, f0)
    clave(c, "rotation_euler", (0, math.pi, 0.4), f0)
    clave(c, "location", (dest[0], dest[1], ZM + 0.012 + dest[2] if len(dest) > 2 else ZM + 0.012), F(t + dur))
    clave(c, "rotation_euler", (0, 0 if cara else math.pi, 0), F(t + dur))
    if quitar:
        clave(c, "location", (dest[0], dest[1], ZM + 0.012), F(quitar - 0.3))
        clave(c, "location", (1.3, 0.9, ZM + 0.05), F(quitar))


def ficha_pila(loc, n, color, padre=None):
    root = vacio(loc)
    for k in range(n):
        cil((0, 0, k * 0.014 + 0.007), 0.05, 0.012, mat("ficha" + str(color), color), root)
        if k % 2 == 0:
            cil((0, 0, k * 0.014 + 0.0071), 0.051, 0.006, mat("fichab", (245, 245, 245)), root)
    return root


def construir(T, total):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, int(total * FPS)
    sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "MATERIAL"
    sh.show_shadows = True; sh.shadow_intensity = 0.4
    sh.show_cavity = True; sh.cavity_type = "WORLD"
    sh.show_specular_highlight = False
    sc.display.light_direction = (0.2, -0.5, 0.85)
    sc.display.render_aa = "8"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("mundo"); sc.world = w; w.color = (0.02, 0.015, 0.05)
    # sala: moqueta, paredes, tragaperras y luces
    for i in range(-6, 7):
        for j in range(-6, 7):
            caja((i * 1.2, j * 1.2, -0.01), (0.6, 0.6, 0.01), mat("moq" + str((i + j) % 2), (120, 20, 40) if (i + j) % 2 else (95, 14, 34)))
    caja((0, 6, 2.5), (8, 0.2, 2.5), mat("pared", (40, 22, 70)))
    for x in range(-6, 7, 2):
        caja((x, 5.5, 0.9), (0.4, 0.35, 0.9), mat("traga", (60, 60, 80)))
        caja((x, 5.14, 1.25), (0.3, 0.02, 0.25), mat("pant" + str(x % 3), [(255, 210, 60), (90, 220, 255), (255, 90, 180)][x % 3]))
    rng = np.random.default_rng(2)
    for k in range(40):
        esfera((rng.uniform(-7, 7), 5.75, rng.uniform(2.2, 4.6)), 0.09, mat("luz" + str(k % 4), [(255, 220, 120), (255, 90, 160), (110, 220, 255), (255, 255, 255)][k % 4]))
    # mesa de blackjack
    cil((0, 0.55, ZM - 0.06), 1.62, 0.1, mat("madera", (110, 60, 30)), lados=64)
    cil((0, 0.55, ZM - 0.02), 1.52, 0.06, mat("tapete", (24, 110, 70)), lados=64)
    caja((0, 1.75, ZM - 0.02), (1.7, 0.6, 0.08), mat("fondo_mesa", (24, 22, 30)))
    cil((0, 0.55, ZM / 2 - 0.1), 0.25, ZM - 0.2, mat("pata", (40, 30, 30)))
    texto3d("BLACKJACK PAGA 3 A 2", (0, 0.05, ZM + 0.014), 0.09, (200, 190, 120))
    texto3d("EL CRUPIER SE PLANTA EN 17", (0, -0.08, ZM + 0.014), 0.06, (170, 200, 170))
    caja(ZAPATO, (0.12, 0.18, 0.06), mat("zapato", (60, 20, 30)))
    for i, c in enumerate(((220, 40, 50), (40, 80, 200), (30, 30, 30), (40, 160, 80))):
        ficha_pila((-0.6 + i * 0.13, 0.95, ZM), 12, c)
    fichas_tu = ficha_pila((0.55, -0.55, ZM), 6, (220, 40, 50))
    # personajes
    crupier = jugador((0, 1.35, 0), math.pi, (150, 30, 40), (20, 20, 26))
    tu = jugador((12, -30, 0), 0, (245, 245, 245), (30, 40, 90))
    alumnos = [jugador((-12, -6 - k, 0), 0, c, (40, 40, 60)) for k, c in enumerate(((200, 40, 60), (80, 140, 230), (240, 200, 60)))]
    grande = jugador((-12, -10, 0), 0, (40, 40, 50), (30, 30, 36))
    seguridad = jugador((12, -6, 0), 0, (20, 20, 24), (20, 20, 24))
    # cámara
    bpy.ops.object.camera_add(location=(0, -3, 2.2))
    cam = bpy.context.object; sc.camera = cam
    obj = vacio((0, 0.2, ZM))
    tc = cam.constraints.new("TRACK_TO"); tc.target = obj; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    return dict(crupier=crupier, tu=tu, alumnos=alumnos, grande=grande, seguridad=seguridad, cam=cam, obj=obj, fichas_tu=fichas_tu)


def animar(E, T, total):
    g = {i: b for i, b in enumerate(T)}
    t0 = lambda i: g[i]["t0"]
    t1 = lambda i: g[i]["t0"] + g[i]["dur"]
    cr = E["crupier"]
    repartos = []

    def dar(rango, palo, t, dest, cara=True, quitar=None):
        c = carta(rango, palo)
        repartir(c, t, dest, cara, quitar=quitar)
        repartos.append(t)
        return c

    # 0: gancho, mano ganadora ya en la mesa
    dar("A", "♠", 0.0, (-0.12, -0.25), quitar=t1(0))
    dar("K", "♥", 0.15, (0.08, -0.25), quitar=t1(0))
    # 1: tu mano 10 + 7
    dar("10", "♠", t0(1) + 0.2, (-0.12, -0.25), quitar=t1(4))
    dar("7", "♥", t0(1) + 0.6, (0.08, -0.25), quitar=t1(4))
    # 2: valores de las figuras y el as
    vals = [("J", "♦", "10"), ("Q", "♣", "10"), ("K", "♥", "10"), ("A", "♠", "1 / 11")]
    for i, (r, p, v) in enumerate(vals):
        x = -0.48 + i * 0.32
        dar(r, p, t0(2) + 0.1 + i * 0.25, (x, 0.32), quitar=t1(2))
        tx = texto3d(v, (x, 0.52, ZM + 0.016), 0.08, (255, 220, 60))
        ocultar(tx, F(t0(2) + 0.4 + i * 0.25), F(t1(2)))
    # 3: el crupier: 9 y una tapada
    dar("9", "♣", t0(3) + 0.2, (-0.12, 0.45), quitar=t1(4))
    dar("?", " ", t0(3) + 0.5, (0.08, 0.45), cara=False, quitar=t1(4))
    # 4: pides y te pasas (10 + 7 + 6)
    dar("6", "♦", t0(4) + 0.3, (0.28, -0.25), quitar=t1(4))
    # 5: blackjack
    dar("A", "♥", t0(5) + 0.15, (-0.12, -0.25), quitar=t1(5))
    dar("K", "♠", t0(5) + 0.5, (0.08, -0.25), quitar=t1(5))
    # 8: valores de la cuenta Hi-Lo
    cuenta = [("3", "♠", "+1", (60, 220, 110)), ("5", "♥", "+1", (60, 220, 110)), ("8", "♣", "0", (220, 220, 220)), ("K", "♦", "-1", (240, 70, 80)), ("A", "♣", "-1", (240, 70, 80))]
    for i, (r, p, v, c) in enumerate(cuenta):
        x = -0.48 + i * 0.24
        dar(r, p, t0(8) + 0.1 + i * 0.22, (x, 0.3), quitar=t1(8))
        tx = texto3d(v, (x, 0.52, ZM + 0.016), 0.1, c)
        ocultar(tx, F(t0(8) + 0.4 + i * 0.22), F(t1(8)))
    # 9: salen muchas cartas bajas → la cuenta sube
    bajas = [("2", "♠"), ("4", "♥"), ("6", "♣"), ("3", "♦"), ("5", "♠"), ("2", "♥"), ("6", "♦"), ("4", "♣")]
    for i, (r, p) in enumerate(bajas):
        dest = (-0.6 + (i % 4) * 0.4, -0.25 if i < 4 else 0.4)
        dar(r, p, t0(9) + 0.1 + i * (g[9]["dur"] * 0.6 / 8), dest, quitar=t1(9))
    # el crupier mueve el brazo al repartir
    br = cr["brazo_der"]; cd = cr["codo_der"]
    for t in sorted(repartos):
        clave(br, "rotation_euler", (math.radians(35), 0, 0), F(t))
        clave(br, "rotation_euler", (math.radians(70), 0, math.radians(-25)), F(t + 0.18))
        clave(br, "rotation_euler", (math.radians(35), 0, 0), F(t + 0.4))
        clave(cd, "rotation_euler", (math.radians(60), 0, 0), F(t))
        clave(cd, "rotation_euler", (math.radians(20), 0, 0), F(t + 0.18))
        clave(cd, "rotation_euler", (math.radians(60), 0, 0), F(t + 0.4))
    # fichas que crecen («millones»)
    rng = np.random.default_rng(5)
    for k in range(16):
        a = k / 16 * 2 * math.pi
        p = ficha_pila((math.cos(a) * 0.55, 0.45 + math.sin(a) * 0.35, ZM), 30, [(220, 40, 50), (40, 80, 200), (30, 30, 30), (40, 160, 80), (240, 200, 60)][k % 5])
        clave(p, "scale", (1, 1, 0.01), F(t0(10) + g[10]["dur"] * 0.7))
        clave(p, "scale", (1, 1, 0.01), F(t0(11) + 0.05 * k))
        clave(p, "scale", (1, 1, 1.0), F(t0(11) + 0.6 + 0.05 * k))
        clave(p, "scale", (1, 1, 1.0), F(t1(12)))
        clave(p, "scale", (1, 1, 0.01), F(t1(12) + 0.3))
    return dict(t0=t0, t1=t1)


# ------------------------------------------------------------- personas
def mover_personas(E, T, total, tt):
    t0, t1 = tt["t0"], tt["t1"]
    al = E["alumnos"]
    P = []
    lejos = (-12, -8)
    sitios = [(-1.25, -0.55), (1.25, -0.55), (-1.6, 0.35)]
    for k, a in enumerate(al):
        P.append(dict(p=a, ruta=ruta([(0, (lejos[0], lejos[1] - k)), (t0(7) - 0.01, (lejos[0], lejos[1] - k)), (t0(7), (-4.2, 1.2 + k * 0.7)),
                                      (t0(7) + 1.6, sitios[k]), (t0(13) + 0.3, sitios[k]), (t1(13), (-5.5, 2.5 + k * 0.6)), (total, (-5.5, 2.5 + k * 0.6))]),
                      foco=(0, 0.5), senal=(t0(10) + 0.4, t0(10) + 1.6) if k == 0 else None))
    P.append(dict(p=E["grande"], ruta=ruta([(0, (-12, -10)), (t0(10) + 1.2, (-12, -10)), (t0(10) + 1.21, (-4.2, 0.6)), (t1(10), (0.0, -1.1)),
                                            (t0(13) + 0.3, (0.0, -1.1)), (t1(13), (-5.0, 1.8)), (total, (-5.0, 1.8))]), foco=(0, 0.5)))
    P.append(dict(p=E["seguridad"], ruta=ruta([(0, (12, -6)), (t0(12) - 0.01, (12, -6)), (t0(12), (4.2, 0.8)), (t1(12), (0.7, -1.5)),
                                              (t1(13), (-3.8, 1.2)), (total, (-3.8, 1.2))]), foco=(0, -1.1)))
    # «tú» desaparece cuando llegan los alumnos (cede el sitio al gran apostador)
    P.append(dict(p=E["tu"], ruta=ruta([(0, (12, -30)), (total, (12, -30))]), foco=(0, 0.5)))
    n = int(total * FPS) + 1
    for j in P:
        Pp = j["p"]
        fase, ang_prev = 0.0, None
        prev = j["ruta"](0)
        for f in range(n):
            t = f / FPS
            x, y = j["ruta"](t)
            vx, vy = (x - prev[0]) * FPS, (y - prev[1]) * FPS
            v = math.hypot(vx, vy); prev = (x, y)
            if v > 12:
                v = 0
            fase += v / FPS * 5.0
            amp = min(1.0, v / 1.6)
            ang = math.atan2(vy, vx) - math.pi / 2 if v > 0.4 else math.atan2(j["foco"][1] - y, j["foco"][0] - x) - math.pi / 2
            if ang_prev is not None:
                d = (ang - ang_prev + math.pi) % (2 * math.pi) - math.pi
                ang = ang_prev + d * 0.25
            ang_prev = ang
            z = 0.015 * math.sin(t * 3.8 + hash(id(Pp)) % 5) + abs(math.sin(fase)) * 0.04 * amp
            clave(Pp["root"], "location", (x, y, z), f)
            clave(Pp["root"], "rotation_euler", (0, 0, ang), f)
            pierna = math.radians(30) * amp * math.sin(fase)
            clave(Pp["pierna_izq"], "rotation_euler", (pierna, 0, 0), f)
            clave(Pp["pierna_der"], "rotation_euler", (-pierna, 0, 0), f)
            clave(Pp["rodilla_izq"], "rotation_euler", (-math.radians(6 + 50 * amp * max(0.0, math.cos(fase))), 0, 0), f)
            clave(Pp["rodilla_der"], "rotation_euler", (-math.radians(6 + 50 * amp * max(0.0, -math.cos(fase))), 0, 0), f)
            brazo = math.radians(22) * amp * math.sin(fase) + math.radians(3) * math.sin(t * 3)
            bi, bd = (-brazo, 0, math.radians(6)), (brazo, 0, math.radians(-6))
            ci = cdr = math.radians(15 + 30 * amp)
            s_ = j.get("senal")
            if s_ and s_[0] <= t <= s_[1]:       # la señal: se toca la oreja
                bd, cdr = (math.radians(150), 0, math.radians(-20)), math.radians(125)
            clave(Pp["brazo_izq"], "rotation_euler", bi, f); clave(Pp["brazo_der"], "rotation_euler", bd, f)
            clave(Pp["codo_izq"], "rotation_euler", (ci, 0, 0), f); clave(Pp["codo_der"], "rotation_euler", (cdr, 0, 0), f)


def camaras(E, T, total, tt):
    t0, t1 = tt["t0"], tt["t1"]
    cam, obj = E["cam"], E["obj"]
    PL_ = {
        0: (((0.0, -2.0, 2.2), (0, -0.1, ZM), 30), ((0.3, -1.7, 1.8), (0, -0.2, ZM), 36)),
        1: (((-0.6, -2.4, 2.0), (0, 0.0, ZM), 30), ((-0.3, -1.9, 1.8), (0, -0.1, ZM), 34)),
        2: (((0.0, -1.6, 2.1), (0, 0.25, ZM), 32), ((0.0, -1.4, 1.9), (0, 0.25, ZM), 34)),
        3: (((0.9, -1.9, 1.9), (0, 0.9, 1.3), 28), ((0.6, -1.6, 1.8), (0, 0.9, 1.3), 30)),
        4: (((0.0, -1.7, 2.0), (0.05, 0.0, ZM), 32), ((0.0, -1.4, 1.8), (0.05, -0.1, ZM), 36)),
        5: (((0.4, -1.6, 1.8), (0, -0.2, ZM), 34), ((0.2, -1.4, 1.6), (0, -0.25, ZM), 38)),
        6: (((3.5, -4.5, 3.0), (0, 0.5, 1.0), 24), ((2.5, -4.0, 2.6), (0, 0.5, 1.0), 26)),
        7: (((-1.5, -4.2, 3.2), (-1.8, 0.2, 1.0), 24), ((-1.0, -3.8, 3.0), (-1.2, 0.0, 1.0), 26)),
        8: (((0.0, -1.5, 2.1), (0, 0.22, ZM), 32), ((0.0, -1.35, 1.95), (0, 0.22, ZM), 34)),
        9: (((0.0, -2.2, 2.4), (0, 0.1, ZM), 28), ((0.0, -1.9, 2.2), (0, 0.1, ZM), 30)),
        10: (((-0.5, -3.8, 3.2), (-0.9, -0.3, 1.1), 24), ((0.0, -3.6, 3.0), (-0.4, -0.5, 1.1), 26)),
        11: (((2.2, -2.2, 2.4), (0, 0.4, ZM), 26), ((-2.2, -2.2, 2.4), (0, 0.4, ZM), 26)),
        12: (((3.0, -3.4, 3.2), (0.6, -0.8, 1.1), 24), ((2.4, -3.2, 3.0), (0.4, -1.0, 1.1), 26)),
        13: (((0.5, -4.4, 3.2), (-1.5, 0.3, 1.0), 24), ((0.3, -4.2, 3.0), (-2.5, 1.0, 1.0), 26)),
        14: (((2.8, -3.6, 2.6), (0, 0.4, 1.0), 24), ((-2.8, -3.6, 2.6), (0, 0.4, 1.0), 24)),
    }
    for i, (a, z) in PL_.items():
        for t, (pos, mira, lens) in ((t0(i), a), (t1(i) - 0.2, z)):
            clave(cam, "location", pos, F(t)); clave(obj, "location", mira, F(t))
            cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=F(t))


# ------------------------------------------------------------- montaje
def panel(tu, crup, total_rojo=False):
    f, f2 = fuente(60), fuente(70)
    im = Image.new("RGBA", (560, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 559, 99), fill=(14, 18, 40, 235))
    d.text((22, 12), "TÚ", font=f, fill=(255, 255, 255))
    d.rectangle((110, 0, 220, 99), fill=(240, 60, 70) if total_rojo else ((232, 250, 60) if tu == 21 else (30, 40, 80)))
    d.text((128, 6), str(tu), font=f2, fill=(255, 255, 255) if total_rojo or tu != 21 else (14, 14, 20))
    d.text((240, 12), "CRUPIER", font=f, fill=(255, 255, 255))
    d.rectangle((450, 0, 559, 99), fill=(30, 40, 80))
    d.text((470, 6), str(crup) if crup is not None else "–", font=f2, fill=(255, 255, 255))
    return cursiva(im, 0.1)


def panel_cuenta(n):
    f = fuente(70)
    im = Image.new("RGBA", (420, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 419, 109), fill=(14, 18, 40, 235))
    d.text((24, 12), "CUENTA", font=f, fill=(255, 255, 255))
    d.rectangle((270, 0, 419, 109), fill=(60, 220, 110) if n > 0 else (30, 40, 80))
    d.text((290, 10), f"{n:+d}" if n else "0", font=f, fill=(14, 14, 20) if n > 0 else (255, 255, 255))
    return cursiva(im, 0.1)


def montar(T, total, frames_dir, muestra=False):
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    grad = np.zeros((H, W, 4), np.uint8); grad[..., 3] = (np.clip(1 - np.arange(H) / 520, 0, 1) * 170)[:, None].astype(np.uint8)
    grad = Image.fromarray(grad, "RGBA")
    n = int(total * FPS)
    cuadros = range(n) if not muestra else [F(b["t0"] + b["dur"] * 0.7) for b in T]
    for fi in cuadros:
        tg = fi / FPS
        kb = max([i for i, b in enumerate(T) if b["t0"] <= tg], default=0)
        b = T[kb]; tl = tg - b["t0"]
        fr = Image.open(os.path.join(frames_dir, f"f_{fi:04d}.png")).convert("RGBA").resize((W, H), Image.LANCZOS)
        if kb == 6:   # «ahora viene lo bueno»: se oscurece la escena
            fr.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
        fr.alpha_composite(grad)
        pts = b["palabras"]
        k = max([i for i, (t0_, _) in enumerate(pts) if tg >= t0_], default=0)
        g0 = (k // 4) * 4
        fr.alpha_composite(texto_arriba([p for _, p in pts[g0:g0 + 4]], k - g0), (0, 170))
        t_et = b["dur"] * b.get("golpe", 0) if "golpe" in b else 0.15
        if "etiqueta" in b and tl > t_et:
            u = min(1, (tl - t_et) / 0.18)
            et = etiqueta(*b["etiqueta"])
            s = 0.6 + 0.4 * u + 0.06 * math.sin(u * math.pi)
            et = et.resize((int(et.width * s), int(et.height * s)), Image.BICUBIC)
            fr.alpha_composite(et, (int(W / 2 - et.width / 2), int(600 - et.height / 2)))
        if "etiqueta2" in b and tl > b["dur"] * 0.5:
            u = min(1, (tl - b["dur"] * 0.5) / 0.18)
            et = etiqueta(*b["etiqueta2"], tam=90)
            et = et.resize((int(et.width * (0.6 + 0.4 * u)), int(et.height * (0.6 + 0.4 * u))), Image.BICUBIC)
            fr.alpha_composite(et, (int(W / 2 - et.width / 2), int(760 - et.height / 2)))
        if "hud" in b:
            tu, cr = b["hud"]
            if kb == 4 and tl < b["dur"] * 0.45:
                tu = 17
            fr.alpha_composite(panel(tu, cr, total_rojo=tu > 21), (40, 1330))
        if b.get("cuenta_fija") or "cuenta" in b:
            a_, z_ = b.get("cuenta", (0, 0))
            nval = int(round(a_ + (z_ - a_) * min(1, tl / (b["dur"] * 0.7))))
            fr.alpha_composite(panel_cuenta(nval), (40, 1330))
        arr = np.asarray(fr.convert("RGB"))
        if muestra:
            Image.fromarray(arr).resize((360, 640)).save(os.path.join(SALIDA, f"muestra_{kb:02d}.png"))
        else:
            ff.stdin.write(arr.tobytes())
    if muestra:
        return
    ff.stdin.close(); ff.wait()
    sr = audio.MUS_SR
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for b in T:
        i = int(b["t0"] * audio.VOZ_SR); voz[i:i + len(b["audio"])] += b["audio"]
    wav_voz = os.path.join(SALIDA, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    n_ = int((total + 1) * sr)
    mus = audio.musica(total + 1, semilla=9, bpm=96, tono="A")
    mus = (mus.mean(axis=1) if mus.ndim == 2 else mus)[:n_] * 0.6
    rng = np.random.default_rng(3)
    amb = audio._lp(rng.standard_normal(n_).astype(np.float32), 900) * 0.05   # murmullo del casino
    mezcla = mus + amb[:len(mus)]
    # «clic» de carta y fichas en cada reparto aproximado + efectos en momentos clave
    for b in T:
        if "golpe" in b or "etiqueta" in b:
            t_e = b["t0"] + (b["dur"] * b.get("golpe", 0) if "golpe" in b else 0.15)
            e = audio.efecto("golpe" if b.get("etiqueta", ("", ""))[1] == "rojo" else "logro")
            e = e.mean(axis=1) if e.ndim == 2 else e
            i = int(t_e * sr); j = min(len(mezcla), i + len(e)); mezcla[i:j] += e[:j - i] * 0.8
    wav_mus = os.path.join(SALIDA, "musica.wav"); audio.sf.write(wav_mus, mezcla, sr)
    final = os.path.join(SALIDA, f"{SLUG}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.35[m];[m][v1]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=300[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final], check=True)
    for f_ in (mp4, wav_voz, wav_mus):
        os.remove(f_)
    print("OK →", final, f"({total:.1f}s)")


def portada(T):
    fr = Image.open(os.path.join(SALIDA, "frames", f"f_{F(T[5]['t0'] + T[5]['dur'] * 0.8):04d}.png")).convert("RGBA").resize((W, H), Image.LANCZOS)
    fr.alpha_composite(Image.new("RGBA", (W, H), (6, 4, 20, 110)))
    for txt, y, est, tam in (("GANARON MILLONES", 520, "amarillo", 130), ("AL BLACKJACK", 720, "amarillo", 150), ("SIN HACER TRAMPA", 960, "rojo", 90)):
        e = etiqueta(txt, est, tam); fr.alpha_composite(e, ((W - e.width) // 2, y))
    fr.convert("RGB").save(os.path.join(SALIDA, "portada.png"))


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    T, total = tiempos()
    print(f"[{SLUG}] {total:.1f}s", flush=True)
    E = construir(T, total)
    tt = animar(E, T, total)
    mover_personas(E, T, total, tt)
    camaras(E, T, total, tt)
    frames = os.path.join(SALIDA, "frames"); os.makedirs(frames, exist_ok=True)
    sc = bpy.context.scene
    muestra = "--muestra" in sys.argv
    lista = [F(b["t0"] + b["dur"] * 0.7) for b in T] if muestra else range(sc.frame_start, sc.frame_end + 1)
    for fi in lista:
        p = os.path.join(frames, f"f_{fi:04d}.png")
        if os.path.exists(p) and not muestra:
            continue
        sc.frame_set(fi); sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        if fi % 90 == 0:
            print(f"  fotograma {fi}/{sc.frame_end}", flush=True)
    montar(T, total, frames, muestra)
    if not muestra:
        portada(T)
