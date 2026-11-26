# -*- coding: utf-8 -*-
"""¿Cómo cuenta células un equipo de hematología? Vídeo vertical estilo plastilina / stop motion (Blender Workbench a
10 imágenes por segundo, con temblor de cámara y parpadeo de luz al montar), con el formato de los vídeos 3D del canal.
Datos: principio Coulter (impedancia): la célula, suspendida en un diluyente conductor, cruza un orificio entre dos
electrodos y aumenta la resistencia; cada paso es un pulso y su altura es proporcional al volumen de la célula.
Método óptico: la célula cruza un haz de luz (láser) y la luz dispersada (frontal ≈ tamaño, lateral ≈ complejidad
interna) permite diferenciar leucocitos. El equipo aspira y diluye la muestra y la divide en canales: GR/PLQ (dilución
alta) y GB/HB, donde un reactivo lisante rompe los hematíes y la hemoglobina se mide por fotometría. Hay unos
setecientos hematíes por cada leucocito. Con lo medido calcula HCT, VCM, HCM y CHCM. Control de calidad diario en tres
niveles (bajo, normal, alto); ante alarmas («flags») se revisa un frotis al microscopio.
Uso: python hematologia3d.py [--muestra]"""
import math, os, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import audio
import plano as PL
from futbol3d import mat, vacio, clave, F, fuente, etiqueta, texto_arriba
import bpy
from mathutils import Vector
from PIL import Image, ImageEnhance

RAIZ = os.path.dirname(AQUI)
SLUG = "39-como-cuenta-celulas-un-equipo-de-hematologia"
SALIDA = os.path.join(RAIZ, "salida", SLUG)
FUENTES = os.path.join(RAIZ, "fuentes")
FPS = 30
PASO = 3                      # stop motion: una imagen nueva cada 3 fotogramas (10 por segundo)
W, H = 1080, 1920
RW, RH = 720, 1280
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

audio.PRONUNCIA[:0] = [("Coulter", "Cúlter")]

BEATS = [
    dict(say="¿Cómo cuenta tus células un equipo de hematología? Un pulso… es una célula.", etiqueta=("1 PULSO = 1 CÉLULA", "amarillo")),
    dict(say="Método uno, impedancia o Coulter: la célula pasa por un agujerito y frena la corriente.", etiqueta=("IMPEDANCIA · COULTER", "amarillo")),
    dict(say="Cuanto más grande es la célula, más alto es el pulso.", etiqueta=("MÁS GRANDE = MÁS ALTO", "verde"), golpe=0.55),
    dict(say="Método dos, óptico: la célula cruza un haz de luz, y la luz que desvía dice qué célula es.", etiqueta=("ÓPTICO · LUZ", "amarillo")),
    dict(say="Pero antes, el equipo aspira la muestra del tubo… y la mezcla.", etiqueta=("ASPIRA Y MEZCLA", "amarillo")),
    dict(say="Luego la divide en dos cámaras: rojos y plaquetas por un lado… y blancos por otro.", etiqueta=("ROJOS + PLAQUETAS", "rojo"), etiqueta2=("BLANCOS", "verde")),
    dict(say="Cada cámara lleva su dilución, porque hay unos setecientos rojos por cada blanco.", etiqueta=("700 ROJOS : 1 BLANCO", "amarillo")),
    dict(say="En la de blancos, un reactivo rompe los rojos… y así se mide la hemoglobina.", etiqueta=("HEMOGLOBINA", "verde"), golpe=0.6),
    dict(say="Con todo eso calcula el resto: hematocrito, volumen medio y más.", etiqueta=("PARÁMETROS", "amarillo")),
    dict(say="Cada día se pasan controles: bajo, normal y alto.", etiqueta=("CONTROL DE CALIDAD", "verde")),
    dict(say="Y si aparece una célula rara… ¡salta la alarma!", etiqueta=("¡ALARMA!", "rojo"), golpe=0.62),
    dict(say="Entonces se hace un frotis… y se mira al microscopio.", etiqueta=("FROTIS + MICROSCOPIO", "amarillo")),
    dict(say="Automatización rápida… pero la validación es tuya. Sígueme para más.", etiqueta=("MÁQUINA + CRITERIO", "verde")),
]

XO, XA, XC, XR, XW, XE, XF, XG, XM = 0.0, 3.0, 6.0, 7.25, 7.85, 9.6, 12.0, 14.5, 16.6
PULSOS = []                   # instantes de cada pulso (para el «bip»)


def tiempos():
    t = 0.05
    out = []
    for b in BEATS:
        a = audio.voz(b["say"])
        d = len(a) / audio.VOZ_SR
        out.append(dict(b, t0=t, dur=d + 0.25, audio=a, palabras=PL.tiempos_palabras(b["say"], t, d)))
        t += d + 0.25
    return out, t + 0.6


# ------------------------------------------------------------- plastilina
def M(rgb):
    return mat("c%d_%d_%d" % tuple(rgb), rgb)


TEX = {}


def grumos(o, s):
    if "t" not in TEX:
        t = bpy.data.textures.new("arcilla", "CLOUDS"); t.noise_scale = 0.35; TEX["t"] = t
    m = o.modifiers.new("g", "DISPLACE"); m.texture = TEX["t"]; m.strength = s; m.texture_coords = "LOCAL"
    return o


def _fin(o, rgb, padre, suave=True):
    o.data.materials.append(M(rgb))
    if suave:
        for p in o.data.polygons:
            p.use_smooth = True
    if padre:
        o.parent = padre
    return o


def _angulo():
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except Exception:
        pass


def bloque(loc, half, rgb, padre=None, bev=0.018, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.scale = half
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _angulo()
    if bev:
        b = o.modifiers.new("b", "BEVEL"); b.width = min(bev, min(half) * 0.8); b.segments = 3; b.harden_normals = True
    return _fin(o, rgb, padre, suave=False)


def cilindro(loc, r, h, rgb, padre=None, rot=(0, 0, 0), lados=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=lados)
    o = bpy.context.object
    _angulo()
    b = o.modifiers.new("b", "BEVEL"); b.width = min(0.012, r * 0.3, h * 0.3); b.segments = 3; b.harden_normals = True
    return _fin(o, rgb, padre, suave=False)


def bola(loc, r, rgb, padre=None, esc=(1, 1, 1), lumps=True):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    o = bpy.context.object; o.scale = esc
    _fin(o, rgb, padre)
    if lumps:
        grumos(o, r * 0.08)
    return o


def barra(a, b, r, rgb, padre=None, lados=16):
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return cilindro(tuple((a + b) / 2), r, d.length, rgb, padre, rot=tuple(rot), lados=lados)


FONTS = {}


def texto(txt, loc, tam, rgb, padre=None, rot=(math.pi / 2, 0, 0), dejavu=False, grosor=0.006):
    k = "dv" if dejavu else "an"
    if k not in FONTS:
        FONTS[k] = bpy.data.fonts.load(DEJAVU if dejavu else os.path.join(FUENTES, "Anton-Regular.ttf"))
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.data.body = txt; o.data.font = FONTS[k]; o.data.size = tam
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"
    o.data.extrude = grosor; o.data.bevel_depth = grosor * 0.5; o.data.bevel_resolution = 2
    o.data.materials.append(M(rgb))
    if padre:
        o.parent = padre
    return o


def ocultar(obj, desde, hasta=None):
    """Visible en render solo en [desde, hasta)."""
    for o in [obj] + list(obj.children_recursive):
        for fr_, v in ((0, True), (desde - 1, True), (desde, False)) + (((hasta - 1, False), (hasta, True)) if hasta else ()):
            o.hide_render = v
            o.keyframe_insert("hide_render", frame=max(0, fr_))


def pasos(ta, tb):
    f0 = max(0, F(ta)); f0 -= f0 % PASO
    return range(f0, F(tb) + PASO, PASO)


# ------------------------------------------------------------- células con ojos
def ojos(padre, R, yf, z, sep, enfado=False):
    r = max(0.012, R * 0.2)
    for s in (-1, 1):
        bola((s * sep, yf, z), r, (255, 255, 255), padre, lumps=False)
        bola((s * sep, yf - r * 0.7, z - r * 0.15), r * 0.5, (22, 20, 28), padre, lumps=False)
        if enfado:
            barra((s * sep * 1.8, yf - r * 0.6, z + r * 1.6), (s * sep * 0.3, yf - r * 0.6, z + r * 1.0), r * 0.25, (40, 20, 50), padre)


def celula(tipo):
    root = vacio((0, -50, 0))
    if tipo == "rojo":
        R = 0.085
        bpy.ops.mesh.primitive_torus_add(major_radius=0.056, minor_radius=0.03, major_segments=40, minor_segments=14, rotation=(math.pi / 2, 0, 0))
        o = bpy.context.object; _fin(o, (214, 48, 54), root); grumos(o, 0.004)
        cilindro((0, 0, 0), 0.05, 0.026, (184, 36, 44), root, rot=(math.pi / 2, 0, 0))
        ojos(root, 0.07, -0.016, 0.012, 0.022)
    elif tipo == "plaqueta":
        R = 0.035
        bola((0, 0, 0), 0.035, (196, 150, 222), root, esc=(1.2, 0.7, 0.8))
    elif tipo == "rara":
        R = 0.12
        bola((0, 0, 0), 0.12, (128, 70, 170), root)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            barra((math.cos(a) * 0.1, 0.02, math.sin(a) * 0.1), (math.cos(a) * 0.17, 0.02, math.sin(a) * 0.17), 0.016, (100, 50, 140), root, lados=8)
        bola((0.0, -0.06, -0.04), 0.06, (70, 30, 100), root, esc=(1, 0.6, 0.8))
        ojos(root, 0.12, -0.1, 0.04, 0.04, enfado=True)
    else:                                  # leucocitos: blanco / neutro / linfo / mono
        R = 0.1
        bola((0, 0, 0), 0.1, (242, 236, 246), root)
        nucleo = (128, 72, 176)
        if tipo == "linfo":
            bola((0, -0.045, -0.02), 0.07, nucleo, root, esc=(1, 0.8, 0.9))
        elif tipo == "mono":
            bola((-0.02, -0.06, -0.035), 0.055, nucleo, root, esc=(1.4, 0.6, 0.7))
        else:
            for p in ((-0.045, -0.07, -0.035), (0.0, -0.08, -0.05), (0.045, -0.07, -0.03)):
                bola(p, 0.03, nucleo, root)
        if tipo == "neutro":
            rng = np.random.default_rng(4)
            for k in range(10):
                a, b = rng.uniform(0, 2 * math.pi), rng.uniform(-0.6, 0.6)
                bola((math.cos(a) * 0.092 * math.cos(b), -abs(math.sin(a)) * 0.092, math.sin(b) * 0.092), 0.008, (236, 160, 190), root, lumps=False)
        ojos(root, 0.1, -0.088, 0.035, 0.034)
    return root, R


def desfile(lista, xc, y, z, vel=0.55, span=0.95, apoyadas=True):
    """Células que cruzan x = xc en el instante tc. Devuelve [(root, R, tc, vel)]."""
    out = []
    for tipo, tc in lista:
        root, R = celula(tipo)
        ta, tb = tc - span / vel, tc + span / vel
        zc = z + R if apoyadas else z
        for f in pasos(ta, tb):
            t = f / FPS
            x = xc + (t - tc) * vel
            clave(root, "location", (x, y, zc + abs(math.sin(t * 9)) * 0.016), f)
            clave(root, "rotation_euler", (0, math.sin(t * 9) * 0.14, 0), f)
        ocultar(root, max(0, F(ta)), F(tb))
        out.append((root, R, tc, vel, tipo))
    return out


# ------------------------------------------------------------- gráfica de pulsos
def tarjeta(xc, y=0.42, z0=0.34, z1=0.76):
    bloque((xc, y, (z0 + z1) / 2), (0.62, 0.015, (z1 - z0) / 2), (250, 247, 236), bev=0.012)
    for s in (-1, 1):
        bloque((xc + s * 0.55, y + 0.03, z0 / 2), (0.022, 0.022, z0 / 2), (150, 110, 70))
    barra((xc - 0.56, y - 0.022, z0 + 0.05), (xc + 0.56, y - 0.022, z0 + 0.05), 0.007, (60, 60, 76))
    texto("PULSOS", (xc - 0.46, y - 0.02, z1 - 0.05), 0.05, (150, 150, 170))
    return dict(x=xc, y=y - 0.022, base=z0 + 0.05, n=0)


def pico(card, h, rgb, t_on, t_off):
    x = card["x"] - 0.48 + card["n"] * 0.085
    card["n"] += 1
    e = vacio((x, card["y"], card["base"]))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.04, depth=1, location=(0, 0, 0.5), rotation=(0, 0, math.pi / 4))
    c = bpy.context.object; c.scale = (1, 0.3, 1); _fin(c, rgb, e, suave=False)
    clave(e, "scale", (1, 1, 0.001), max(0, F(t_on) - 1))
    clave(e, "scale", (1, 1, h), F(t_on))
    ocultar(e, F(t_on), F(t_off))
    PULSOS.append(t_on)


ALTURA = dict(rojo=0.15, plaqueta=0.06, blanco=0.3, neutro=0.27, linfo=0.18, mono=0.32, rara=0.34)
COLOR_PICO = dict(rojo=(214, 48, 54), plaqueta=(196, 150, 222), rara=(128, 70, 170))


# ------------------------------------------------------------- escena
def construir(total):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, int(total * FPS)
    sh = sc.display.shading
    luz = os.environ.get("LUZ", "paint.sl")
    if luz.endswith(".exr"):
        sh.light = "MATCAP"; sh.studio_light = luz
    else:
        sh.light = "STUDIO"; sh.studio_light = luz
    sh.color_type = "MATERIAL"
    sh.show_shadows = True; sh.shadow_intensity = 0.45
    sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.cavity_ridge_factor = 1.2; sh.cavity_valley_factor = 1.0
    sh.curvature_ridge_factor = 0.6; sh.curvature_valley_factor = 0.8
    sh.show_specular_highlight = True
    sc.display.light_direction = (0.35, -0.45, 0.82)
    sc.display.render_aa = "8"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("mundo"); sc.world = w; w.color = (0.9, 0.75, 0.62)
    # mesa de papel kraft, fondo y «alfombrillas» de cartulina por estación
    bloque((8, 0, -0.05), (14, 6, 0.05), (214, 176, 128), bev=0)
    bloque((8, 2.4, 1.6), (14, 0.05, 1.7), (246, 214, 186), bev=0)
    for x, c in ((XO, (176, 214, 236)), (XA, (206, 190, 236)), (XC, (184, 226, 200)), ((XR + XW) / 2, (184, 226, 200)),
                 (XE, (250, 226, 150)), (XF, (246, 196, 206)), (XG, (176, 214, 236)), (XM, (206, 190, 236))):
        bloque((x, 0.05, 0.004), (0.78, 0.62, 0.004), c, bev=0)
    E = {}
    # --- óptico (y alarma): canal, lámpara y haz
    for xc, nombre in ((XO, "O"), (XG, "G")):
        bloque((xc, 0, 0.04), (0.82, 0.09, 0.03), (120, 176, 232), bev=0.012)
        for s in (-1, 1):
            bloque((xc, s * 0.095, 0.075), (0.82, 0.012, 0.015), (96, 150, 214), bev=0.008)
        barra((xc + 0.82, 0, 0.0), (xc + 0.82, 0, 0.9), 0.025, (110, 110, 124))
        barra((xc + 0.82, 0, 0.88), (xc, 0, 0.88), 0.022, (110, 110, 124))
        cilindro((xc, 0, 0.8), 0.06, 0.12, (90, 92, 104))
        cilindro((xc, 0, 0.735), 0.045, 0.012, (255, 236, 120))
        haz = cilindro((xc, 0, 0.42), 0.02, 0.62, (255, 238, 130) if nombre == "O" else (255, 120, 120), lados=16)
        det = cilindro((xc, 0, 0.073), 0.035, 0.008, (40, 90, 60))
        det_on = cilindro((xc, 0, 0.076), 0.036, 0.008, (120, 255, 150))
        E["haz" + nombre] = haz; E["det" + nombre] = det_on
    E["cardO"] = tarjeta(XO)
    # --- impedancia: baño, tabique con agujero y electrodos
    bloque((XA, 0, 0.03), (0.8, 0.3, 0.03), (90, 156, 230), bev=0.015)
    bloque((XA, 0.31, 0.06), (0.82, 0.02, 0.06), (240, 240, 246), bev=0.01)
    for s in (-1, 1):
        bloque((XA + s * 0.81, 0, 0.06), (0.02, 0.32, 0.06), (240, 240, 246), bev=0.01)
    col_t = (200, 186, 160)
    bloque((XA, 0, 0.065), (0.025, 0.3, 0.005), col_t, bev=0.004)
    bloque((XA, 0, 0.35), (0.025, 0.3, 0.03), col_t)
    for s in (-1, 1):
        bloque((XA, s * 0.215, 0.2), (0.025, 0.085, 0.15), col_t)
    for x_, rgb, sig in ((XA - 0.6, (220, 50, 56), "+"), (XA + 0.6, (50, 50, 60), "−")):
        barra((x_, 0.12, 0.06), (x_, 0.12, 0.46), 0.03, rgb)
        bola((x_, 0.12, 0.47), 0.045, rgb)
        texto(sig, (x_, 0.1, 0.6), 0.16, rgb, dejavu=True, grosor=0.02)
    E["cardA"] = tarjeta(XA, y=0.45, z0=0.42, z1=0.82)
    # --- analizador y tubo
    caja = bloque((XC + 0.05, 0.1, 0.3), (0.35, 0.25, 0.3), (196, 156, 104), bev=0.03)
    texto("ANALIZADOR", (XC + 0.05, -0.155, 0.1), 0.075, (90, 60, 40))
    bloque((XC + 0.2, -0.152, 0.33), (0.14, 0.006, 0.08), (40, 70, 60), bev=0.006)
    E["pantalla"] = texto("MEZCLANDO", (XC + 0.2, -0.162, 0.33), 0.045, (140, 255, 170))
    bloque((XC - 0.2, -0.2, 0.52), (0.04, 0.06, 0.02), (150, 150, 160))
    barra((XC - 0.2, -0.24, 0.52), (XC - 0.2, -0.24, 0.33), 0.009, (200, 200, 210))
    tubo = vacio((XC - 0.65, -0.5, 0))
    cilindro((0, 0, 0.15), 0.052, 0.3, (226, 236, 242), tubo)
    sangre = vacio((0, 0, 0.012), tubo)
    cilindro((0, 0, 0.1), 0.054, 0.2, (176, 30, 40), sangre)
    cilindro((0, 0, 0.32), 0.058, 0.06, (156, 96, 206), tubo)
    E["tubo"], E["sangre"] = tubo, sangre
    mezclador = vacio((XC + 0.25, 0.15, 0.61))
    barra((0, 0, 0), (0, 0, 0.08), 0.012, (120, 120, 130), mezclador)
    for a in (0, math.pi / 2):
        barra((math.cos(a) * -0.08, math.sin(a) * -0.08, 0.08), (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.08), 0.014, (240, 120, 90), mezclador)
    E["mezclador"] = mezclador
    # rieles hacia los frascos
    E["rielR"] = ((XC + 0.4, -0.05, 0.36), (XR - 0.12, -0.02, 0.36))
    E["rielW"] = ((XC + 0.4, 0.2, 0.46), (XW - 0.1, 0.06, 0.36))
    for a, b in (E["rielR"], E["rielW"]):
        barra(a, b, 0.012, (150, 200, 236))
        barra((a[0], a[1], a[2] - 0.03), (b[0], b[1], b[2] - 0.03), 0.012, (150, 200, 236))
    # frascos
    for x_, et, nombre in ((XR, "ROJOS + PLQ", "R"), (XW, "BLANCOS", "W")):
        cilindro((x_, 0, 0.16), 0.2, 0.32, (214, 232, 240))
        liq = cilindro((x_, 0, 0.3), 0.18, 0.02, (246, 214, 214) if nombre == "R" else (236, 230, 244))
        E["liq" + nombre] = liq
        texto(et, (x_, -0.205, 0.13), 0.055 if nombre == "R" else 0.065, (70, 70, 90))
        cuenta = vacio((x_ + 0.05, 0, 0.8))
        cilindro((0, 0, 0), 0.03, 0.14, (240, 240, 246), cuenta)
        bola((0, 0, 0.1), 0.045, (110, 170, 236), cuenta)
        barra((0, 0, -0.07), (0, 0, -0.14), 0.01, (220, 230, 240), cuenta)
    liq_rojo = cilindro((XW, 0, 0.301), 0.181, 0.02, (196, 50, 62))
    E["liq_rojo"] = liq_rojo
    # fotómetro de hemoglobina
    bloque((XW + 0.5, 0, 0.2), (0.07, 0.06, 0.06), (90, 92, 104))
    bloque((XR + 0.3, 0, 0.2), (0.03, 0.05, 0.05), (40, 90, 60))
    E["hazHB"] = barra((XW + 0.43, 0, 0.2), (XR + 0.33, 0, 0.2), 0.018, (255, 238, 130))
    # --- tablero de resultados
    bloque((XE, 0.22, 0.6), (0.46, 0.02, 0.56), (196, 156, 104), bev=0.02)
    for s in (-1, 1):
        bloque((XE + s * 0.36, 0.3, 0.3), (0.025, 0.06, 0.3), (160, 120, 80))
    for i in range(8):
        cx, cz = XE + (-0.21 if i % 2 == 0 else 0.21), 0.98 - (i // 2) * 0.24
        bloque((cx, 0.195, cz), (0.19, 0.008, 0.1), (170, 130, 84), bev=0.006)
    # --- control de calidad
    E["botes"] = []
    for i, (et, liq, tapa) in enumerate((("BAJO", (244, 160, 160), (120, 200, 240)), ("NORMAL", (214, 70, 82), (120, 220, 140)),
                                         ("ALTO", (140, 22, 42), (250, 170, 90)))):
        b = vacio((XF + (i - 1) * 0.4, 0, 0))
        cilindro((0, 0, 0.13), 0.09, 0.26, (226, 236, 242), b)
        cilindro((0, -0.004, 0.1), 0.088, 0.17, liq, b)
        cilindro((0, 0, 0.28), 0.095, 0.05, tapa, b)
        texto(et, (0, -0.1, 0.07), 0.05, (255, 255, 255) if i else (60, 40, 50), b)
        ok = texto("✓", (XF + (i - 1) * 0.4, 0, 0.48), 0.2, (60, 200, 100), dejavu=True, grosor=0.02)
        E["botes"].append((b, ok))
    # --- alarma
    cartel = vacio((XG + 0.1, 0.3, 0.25))
    barra((0, 0, -0.25), (0, 0, 0.2), 0.018, (120, 100, 80), cartel)
    bloque((0, 0, 0.32), (0.34, 0.02, 0.12), (232, 52, 60), cartel, bev=0.02)
    texto("¡ALARMA!", (0, -0.025, 0.32), 0.13, (255, 255, 255), cartel)
    E["cartel"] = cartel
    bloque((XG - 0.55, -0.25, 0.04), (0.06, 0.06, 0.04), (60, 60, 70))
    E["sirena"] = bola((XG - 0.55, -0.25, 0.13), 0.06, (255, 60, 60), lumps=False)
    bola((XG - 0.55, -0.25, 0.13), 0.058, (120, 30, 36), lumps=False)
    # --- microscopio y frotis
    bloque((XM, 0.08, 0.03), (0.2, 0.2, 0.03), (240, 240, 246))
    bloque((XM, 0.25, 0.38), (0.05, 0.05, 0.35), (240, 240, 246))
    bloque((XM, 0.04, 0.25), (0.2, 0.16, 0.015), (50, 50, 60), bev=0.008)
    E["luzM"] = cilindro((XM, 0.04, 0.268), 0.04, 0.006, (255, 240, 140))
    barra((XM, 0.04, 0.36), (XM, 0.14, 0.8), 0.05, (240, 240, 246))
    barra((XM, 0.14, 0.8), (XM, 0.16, 0.9), 0.035, (50, 50, 60))
    barra((XM, 0.04, 0.36), (XM, 0.04, 0.3), 0.025, (140, 140, 150))
    for s in (-1, 1):
        cilindro((XM + s * 0.07, 0.25, 0.3), 0.04, 0.03, (50, 50, 60), rot=(0, math.pi / 2, 0))
    porta = vacio((XM - 0.6, -0.3, 0.008))
    bloque((0, 0, 0), (0.16, 0.05, 0.005), (206, 234, 242), porta, bev=0.003)
    frotis = bola((0.0, 0, 0.006), 0.045, (226, 120, 146), porta, esc=(2.2, 0.8, 0.12), lumps=False)
    E["porta"], E["frotis"] = porta, frotis
    E["gota"] = bola((XM - 0.5, -0.3, 0.03), 0.025, (190, 30, 44), lumps=False)
    extensor = vacio((XM - 0.42, -0.3, 0.05))
    bloque((0, 0, 0), (0.005, 0.06, 0.05), (206, 234, 242), extensor, rot=(0, -0.6, 0), bev=0.002)
    E["extensor"] = extensor
    # cámara
    bpy.ops.object.camera_add(location=(0, -2, 1))
    cam = bpy.context.object; sc.camera = cam
    obj = vacio((0, 0, 0.3))
    tc = cam.constraints.new("TRACK_TO"); tc.target = obj; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    E["cam"], E["obj"] = cam, obj
    return E


def destello(xc, z, t, n, t_off):
    """Rayos de luz que salen de la célula al cruzar el haz (luz dispersada)."""
    e = vacio((xc, -0.02, z))
    for k in range(n):
        a = math.pi * (0.15 + 0.7 * k / max(1, n - 1)) + math.pi
        barra((math.cos(a) * 0.12, 0, math.sin(a) * 0.12), (math.cos(a) * 0.3, 0, math.sin(a) * 0.3), 0.01, (255, 238, 130), e, lados=8)
        barra((-math.cos(a) * 0.12, 0, -math.sin(a) * 0.12), (-math.cos(a) * 0.3, 0, -math.sin(a) * 0.3), 0.01, (255, 238, 130), e, lados=8)
    ocultar(e, F(t), F(min(t + 0.35, t_off)))


def animar(E, T, total):
    t0 = lambda i: T[i]["t0"]
    t1 = lambda i: T[i]["t0"] + T[i]["dur"]
    d = lambda i: T[i]["dur"]

    # 0 y 3: óptico
    def optico(lista, card, beat, rayos):
        for root, R, tc, vel, tipo in desfile(lista, XO, 0, 0.08):
            pico(card, ALTURA[tipo], COLOR_PICO.get(tipo, (128, 72, 176)), max(0, tc), t1(beat))
            VENT.append((max(0, tc) - 0.05, tc + 0.3))
            destello(XO, 0.08 + R, max(0, tc), rayos.get(tipo, 2), t1(beat))
    VENT = []
    optico([("rojo", 0.0), ("rojo", d(0) * 0.4), ("blanco", d(0) * 0.75)], E["cardO"], 0, dict(rojo=2, blanco=3))
    E["cardO"]["n"] = 0
    optico([("neutro", t0(3) + d(3) * 0.18), ("linfo", t0(3) + d(3) * 0.42), ("mono", t0(3) + d(3) * 0.66), ("rojo", t0(3) + d(3) * 0.86)],
           E["cardO"], 3, dict(neutro=5, linfo=2, mono=3, rojo=1))
    det = E["detO"]
    det.hide_render = True; det.keyframe_insert("hide_render", frame=0)
    for a_, b_ in VENT:
        det.hide_render = False; det.keyframe_insert("hide_render", frame=F(max(0, a_)))
        det.hide_render = True; det.keyframe_insert("hide_render", frame=F(b_))
    # 1 y 2: impedancia
    lista = [("rojo", t0(1) + d(1) * 0.3), ("rojo", t0(1) + d(1) * 0.55), ("plaqueta", t0(1) + d(1) * 0.8),
             ("plaqueta", t0(2) + d(2) * 0.15), ("rojo", t0(2) + d(2) * 0.32), ("blanco", t0(2) + d(2) * 0.55)]
    cel = desfile(lista, XA, 0, 0.2, vel=0.5, span=0.75, apoyadas=False)
    for root, R, tc, vel, tipo in cel:
        pico(E["cardA"], ALTURA[tipo], COLOR_PICO.get(tipo, (128, 72, 176)), tc, t1(2))
    # la corriente: bolitas amarillas de + a −; se paran cuando una célula tapa el agujero
    puntos = [bola((XA, 0.1, 0.27), 0.018, (255, 214, 60), lumps=False) for _ in range(9)]
    s = 0.0
    fs = list(pasos(t0(1) - 0.4, t1(2) + 0.3))
    for f in fs:
        t = f / FPS
        tapado = any(abs((XA + (t - tc) * vel) - XA) < R + 0.04 for _, R, tc, vel, _ in cel)
        if not tapado:
            s += 0.45 * PASO / FPS
        for k, p in enumerate(puntos):
            x = XA - 0.58 + ((s + k * 1.16 / 9) % 1.16)
            clave(p, "location", (x, 0.1, 0.27), f)
    # 4: tubo al analizador
    tubo, sangre = E["tubo"], E["sangre"]
    a, b = (XC - 0.65, -0.5, 0), (XC - 0.2, -0.24, 0)
    for t, loc in ((t0(4), a), (t0(4) + d(4) * 0.22, b), (t0(4) + d(4) * 0.36, (b[0], b[1], 0.1)),
                   (t0(4) + d(4) * 0.72, (b[0], b[1], 0.1)), (t0(4) + d(4) * 0.86, b), (t1(4), a)):
        clave(tubo, "location", loc, F(t))
    clave(sangre, "scale", (1, 1, 1), F(t0(4) + d(4) * 0.4)); clave(sangre, "scale", (1, 1, 0.75), F(t0(4) + d(4) * 0.7))
    ocultar(E["pantalla"], F(t0(4) + d(4) * 0.72), F(t1(5)))
    mz = E["mezclador"]
    for f in pasos(t0(4) + d(4) * 0.7, t1(5)):
        clave(mz, "rotation_euler", (0, 0, f / FPS * 9), f)
    # 5: reparto por los rieles
    def viajar(tipo_rgb, r, riel, salida, dur=0.9, destino=None, aparece=None):
        (ax, ay, az), (bx, by, bz) = riel
        o = bola((0, -50, 0), r, tipo_rgb)
        for f in pasos(salida, salida + dur):
            u = min(1, (f / FPS - salida) / dur)
            clave(o, "location", (ax + (bx - ax) * u, ay + (by - ay) * u, az + (bz - az) * u + r + abs(math.sin(u * 12)) * 0.02), f)
        ocultar(o, F(salida), F(salida + dur))
        if destino is not None:
            ocultar(destino, F(salida + dur), aparece)
    rng = np.random.default_rng(7)
    def montones(xc, n, rgb, r, hasta=None):
        out = []
        for k in range(n):
            a, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(0, 1)) * 0.14
            out.append(bola((xc + math.cos(a) * rr, math.sin(a) * rr, 0.32 + r * 0.6), r, rgb, esc=(1, 1, 0.7)))
        return out
    rojos_R = montones(XR, 22, (214, 48, 54), 0.028)
    plq_R = montones(XR, 6, (196, 150, 222), 0.016)
    blancos_W = montones(XW, 3, (242, 236, 246), 0.04)
    rojos_W = montones(XW, 9, (214, 48, 54), 0.028)
    s5 = t0(5) + 0.1
    for k, o in enumerate(rojos_R + plq_R):
        viajar((214, 48, 54) if k < 22 else (196, 150, 222), 0.028 if k < 22 else 0.016, E["rielR"], s5 + (k % 14) * d(5) * 0.05, destino=o)
    for k, o in enumerate(rojos_W):
        viajar((214, 48, 54), 0.028, E["rielW"], s5 + d(5) * 0.45 + k * d(5) * 0.04, destino=o, aparece=F(t0(7) + d(7) * 0.42))
    for k, o in enumerate(blancos_W):
        viajar((242, 236, 246), 0.04, E["rielW"], s5 + d(5) * 0.5 + k * d(5) * 0.12, destino=o)
    # los rojos del frasco de blancos revientan (lisis)
    for k, o in enumerate(rojos_W):
        tp = t0(7) + d(7) * (0.25 + 0.02 * k)
        clave(o, "scale", (1, 1, 0.7), F(tp) - 3); clave(o, "scale", (1.5, 1.5, 1.0), F(tp)); clave(o, "scale", (0.01, 0.01, 0.01), F(tp) + 3)
    ocultar(E["liq_rojo"], F(t0(7) + d(7) * 0.42))
    ocultar(E["hazHB"], F(t0(7) + d(7) * 0.55), F(t1(7)))
    # 6: gotas de diluyente (muchas al de rojos, una al de blancos) y 7: gota de reactivo
    def gota(x_, t, rgb):
        o = bola((0, -50, 0), 0.03, rgb, esc=(1, 1, 1.3), lumps=False)
        for f in pasos(t, t + 0.3):
            u = min(1, (f / FPS - t) / 0.3)
            clave(o, "location", (x_ + 0.05, 0, 0.66 - u * u * 0.32), f)
        ocultar(o, F(t), F(t + 0.3))
    for k in range(5):
        gota(XR, t0(6) + 0.2 + k * d(6) * 0.15, (110, 170, 236))
    gota(XW, t0(6) + d(6) * 0.5, (110, 170, 236))
    gota(XW, t0(7) + d(7) * 0.08, (110, 210, 130))
    # 8: resultados
    fichas = [("GR 4,8", 0), ("GB 7,2", 0), ("PLQ 250", 0), ("HB 14", 0), ("HCT 42%", 1), ("VCM 88", 1), ("HCM 29", 1), ("CHCM 33", 1)]
    for i, (txt, calc) in enumerate(fichas):
        cx, cz = XE + (-0.21 if i % 2 == 0 else 0.21), 0.98 - (i // 2) * 0.24
        e = vacio((cx, 0.17, cz + 0.8))
        bloque((0, 0, 0), (0.17, 0.02, 0.085), (250, 220, 110) if calc else (150, 200, 240), e, bev=0.015)
        texto(txt, (0, -0.025, 0), 0.1, (60, 44, 30), e)
        tl = t0(8) + (0.05 + i * 0.05 if not calc else 0.3 + (i - 4) * 0.13) * d(8)
        for dt, z in ((0, cz + 0.8), (0.2, cz - 0.03), (0.3, cz + 0.02), (0.4, cz)):
            clave(e, "location", (cx, 0.17, z), F(tl + dt))
        ocultar(e, F(tl))
    # 9: control de calidad
    for i, (bote, ok) in enumerate(E["botes"]):
        tj = t0(9) + d(9) * (0.22 + 0.2 * i)
        x_ = XF + (i - 1) * 0.4
        for dt, z in ((-0.01, 0), (0.15, 0.14), (0.3, 0)):
            clave(bote, "location", (x_, 0, z), F(tj + dt))
        ocultar(ok, F(tj + 0.3))
    # 10: alarma
    tg = t0(10) + d(10) * 0.62
    desfile([("rojo", t0(10) + d(10) * 0.1), ("blanco", t0(10) + d(10) * 0.32), ("rara", tg - 0.05)], XG, 0, 0.08)
    c = E["cartel"]
    for t, s_ in ((0, 0.01), (tg - 0.01, 0.01), (tg + 0.1, 1.25), (tg + 0.2, 0.95), (tg + 0.3, 1.0)):
        clave(c, "scale", (s_, s_, s_), F(t))
    sir = E["sirena"]
    sir.hide_render = True; sir.keyframe_insert("hide_render", frame=0)
    for k in range(int((total - tg) / 0.2) + 1):
        sir.hide_render = k % 2 == 1; sir.keyframe_insert("hide_render", frame=F(tg + k * 0.2))
    # 11: frotis y microscopio
    porta, ext, gotaM = E["porta"], E["extensor"], E["gota"]
    ocultar(gotaM, F(t0(11) + d(11) * 0.05), F(t0(11) + d(11) * 0.25))
    for t, x_ in ((t0(11), XM - 0.42), (t0(11) + d(11) * 0.18, XM - 0.5), (t0(11) + d(11) * 0.42, XM - 0.72), (t0(11) + d(11) * 0.5, XM - 0.9)):
        clave(ext, "location", (x_, -0.3, 0.05), F(t))
    fr = E["frotis"]
    for t, sx, x_ in ((t0(11) + d(11) * 0.18, 0.1, 0.1), (t0(11) + d(11) * 0.42, 1.0, 0.0)):
        clave(fr, "scale", (2.2 * sx, 0.8, 0.12), F(t)); clave(fr, "location", (x_, 0, 0.006), F(t))
    ocultar(fr, F(t0(11) + d(11) * 0.2))
    for t, loc in ((t0(11) + d(11) * 0.5, (XM - 0.6, -0.3, 0.008)), (t0(11) + d(11) * 0.62, (XM - 0.35, -0.15, 0.4)),
                   (t0(11) + d(11) * 0.74, (XM, 0.02, 0.27))):
        clave(porta, "location", loc, F(t))
    ocultar(E["luzM"], F(t0(11) + d(11) * 0.78))
    return t0, t1


def camaras(E, T):
    t0 = lambda i: T[i]["t0"]
    t1 = lambda i: T[i]["t0"] + T[i]["dur"]
    cam, obj = E["cam"], E["obj"]
    PL_ = {
        0: (((0.25, -2.0, 1.05), (0, 0.1, 0.38)), ((0.1, -1.75, 0.95), (0, 0.1, 0.38))),
        1: (((XA + 0.3, -2.1, 1.15), (XA, 0.1, 0.4)), ((XA + 0.15, -1.85, 1.05), (XA, 0.1, 0.4))),
        2: (((XA + 0.35, -1.45, 0.8), (XA, 0.15, 0.38)), ((XA + 0.2, -1.3, 0.75), (XA, 0.15, 0.38))),
        3: (((-0.3, -1.9, 1.0), (0, 0.1, 0.38)), ((-0.15, -1.65, 0.9), (0, 0.1, 0.38))),
        4: (((XC - 0.4, -1.9, 1.1), (XC - 0.05, 0, 0.3)), ((XC - 0.25, -1.6, 1.0), (XC - 0.05, 0, 0.3))),
        5: (((6.9, -3.0, 1.9), (6.9, 0, 0.3)), ((6.95, -2.7, 1.75), (6.95, 0, 0.3))),
        6: (((7.55, -1.8, 1.45), (7.55, 0, 0.3)), ((7.55, -1.6, 1.35), (7.55, 0, 0.3))),
        7: (((XW + 0.05, -1.55, 1.25), (XW - 0.05, 0, 0.28)), ((XW, -1.35, 1.15), (XW - 0.05, 0, 0.28))),
        8: (((XE, -2.1, 0.8), (XE, 0.2, 0.55)), ((XE, -1.85, 0.75), (XE, 0.2, 0.55))),
        9: (((XF, -1.9, 0.95), (XF, 0, 0.25)), ((XF, -1.65, 0.85), (XF, 0, 0.25))),
        10: (((XG - 0.2, -2.0, 1.0), (XG, 0.1, 0.38)), ((XG - 0.05, -1.7, 0.9), (XG, 0.1, 0.38))),
        11: (((XM - 0.5, -1.8, 1.05), (XM - 0.25, 0, 0.3)), ((XM - 0.15, -1.6, 0.95), (XM - 0.05, 0, 0.35))),
        12: (((15.4, -3.0, 1.5), (15.6, 0, 0.4)), ((15.6, -3.6, 1.9), (15.6, 0, 0.45))),
    }
    cam.data.lens = 30
    for i, (a, z) in PL_.items():
        for t, (pos, mira) in ((t0(i), a), (t1(i) - 0.2, z)):
            # más cerca y con el tema más abajo en el cuadro (arriba van los textos)
            k = {9: 1.05, 12: 0.9}.get(i, 0.8)
            pos = tuple(m + (p_ - m) * k for p_, m in zip(pos, mira))
            mira = (mira[0], mira[1], mira[2] + 0.22)
            clave(cam, "location", pos, F(t)); clave(obj, "location", mira, F(t))


# ------------------------------------------------------------- montaje
def montar(T, total, frames_dir, muestra=False):
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    grad = np.zeros((H, W, 4), np.uint8); grad[..., 3] = (np.clip(1 - np.arange(H) / 560, 0, 1) * 150)[:, None].astype(np.uint8)
    grad = Image.fromarray(grad, "RGBA")
    yy, xx = np.mgrid[0:H, 0:W]
    vig = np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2, 0, 1)
    vig = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (vig * 55).astype(np.uint8)]), "RGBA")
    rng = np.random.default_rng(11)
    grano = [rng.normal(0, 4, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1) for _ in range(4)]
    golpes = [b["t0"] + b["dur"] * b["golpe"] for b in T if "golpe" in b]
    n = int(total * FPS)
    cuadros = range(n) if not muestra else [F(b["t0"] + b["dur"] * 0.7) - F(b["t0"] + b["dur"] * 0.7) % PASO for b in T]
    if muestra and os.environ.get("BEATS"):
        cuadros = [cuadros[int(i)] for i in os.environ["BEATS"].split(",")]
    cache = {}
    for fi in cuadros:
        tg = fi / FPS
        kb = max([i for i, b in enumerate(T) if b["t0"] <= tg], default=0)
        b = T[kb]; tl = tg - b["t0"]
        src = fi - fi % PASO
        if src not in cache:
            cache.clear()
            r = np.random.default_rng(src)
            im = Image.open(os.path.join(frames_dir, f"f_{src:04d}.png")).convert("RGB").resize((int(W * 1.012), int(H * 1.012)), Image.LANCZOS)
            dx, dy = r.integers(0, int(W * 0.012) + 1), r.integers(0, int(H * 0.012) + 1)
            im = im.crop((dx, dy, dx + W, dy + H))
            im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.4)).enhance(1.08)
            arr = np.asarray(im).astype(np.float32) * r.uniform(1.06, 1.12)
            arr = np.clip(arr + grano[(src // PASO) % 4], 0, 255).astype(np.uint8)
            cache[src] = arr
        fr = Image.fromarray(cache[src]).convert("RGBA")
        sacude = [g for g in golpes if 0 <= tg - g < 0.3]
        if sacude:
            r = np.random.default_rng(fi)
            fr = fr.transform(fr.size, Image.AFFINE, (1, 0, int(r.integers(-16, 17)), 0, 1, int(r.integers(-16, 17))))
        fr.alpha_composite(vig)
        fr.alpha_composite(grad)
        pts = b["palabras"]
        k = max([i for i, (t0_, _) in enumerate(pts) if tg >= t0_], default=0)
        g0 = (k // 4) * 4
        fr.alpha_composite(texto_arriba([p for _, p in pts[g0:g0 + 4]], k - g0), (0, 170))
        t_et = 0.0 if kb == 0 else (b["dur"] * b["golpe"] if "golpe" in b else 0.15)
        if "etiqueta" in b and tl >= t_et:
            u = 1.0 if kb == 0 else min(1, (tl - t_et) / 0.18)
            et = etiqueta(*b["etiqueta"], tam=100)
            s = 0.6 + 0.4 * u + 0.06 * math.sin(u * math.pi)
            et = et.resize((int(et.width * s), int(et.height * s)), Image.BICUBIC)
            fr.alpha_composite(et, (int(W / 2 - et.width / 2), int(610 - et.height / 2)))
        if "etiqueta2" in b and tl > b["dur"] * 0.55:
            u = min(1, (tl - b["dur"] * 0.55) / 0.18)
            et = etiqueta(*b["etiqueta2"], tam=90)
            et = et.resize((int(et.width * (0.6 + 0.4 * u)), int(et.height * (0.6 + 0.4 * u))), Image.BICUBIC)
            fr.alpha_composite(et, (int(W / 2 - et.width / 2), int(760 - et.height / 2)))
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
    mus = audio.musica(total + 1, semilla=12, bpm=100, tono="C")
    mezcla = (mus.mean(axis=1) if mus.ndim == 2 else mus)[:n_].astype(np.float32) * 0.6
    # «bip» en cada pulso
    m = int(0.07 * sr); tt = np.arange(m) / sr
    bip = (0.35 * np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt * 45)).astype(np.float32)
    for tp in PULSOS:
        i = int(tp * sr); j = min(len(mezcla), i + m); mezcla[i:j] += bip[:j - i]
    for b in T:
        if "etiqueta" in b:
            t_e = b["t0"] + (b["dur"] * b["golpe"] if "golpe" in b else 0.15)
            e = audio.efecto("golpe" if b["etiqueta"][1] == "rojo" else "logro")
            e = e.mean(axis=1) if e.ndim == 2 else e
            i = int(t_e * sr); j = min(len(mezcla), i + len(e)); mezcla[i:j] += e[:j - i] * 0.6
    # sirena de la alarma
    tg = T[10]["t0"] + T[10]["dur"] * T[10]["golpe"]
    m = int(1.6 * sr); tt = np.arange(m) / sr
    fq = np.where((tt // 0.2) % 2 == 0, 880, 660)
    sir = (0.18 * np.sign(np.sin(2 * np.pi * np.cumsum(fq) / sr)) * np.exp(-tt * 1.2)).astype(np.float32)
    sir = audio._lp(sir, 3000)
    i = int(tg * sr); mezcla[i:i + m] += sir[:len(mezcla) - i]
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
    f = F(T[0]["dur"] * 0.75); f -= f % PASO
    fr = Image.open(os.path.join(SALIDA, "frames", f"f_{f:04d}.png")).convert("RGBA").resize((W, H), Image.LANCZOS)
    fr.alpha_composite(Image.new("RGBA", (W, H), (20, 10, 30, 90)))
    for txt, y, est, tam in (("¿CÓMO CUENTA", 420, "amarillo", 140), ("TUS CÉLULAS?", 620, "amarillo", 140), ("1 PULSO = 1 CÉLULA", 1380, "rojo", 90)):
        e = etiqueta(txt, est, tam); fr.alpha_composite(e, ((W - e.width) // 2, y))
    fr.convert("RGB").save(os.path.join(SALIDA, "portada.png"))


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    T, total = tiempos()
    print(f"[{SLUG}] {total:.1f}s", flush=True)
    E = construir(total)
    animar(E, T, total)
    camaras(E, T)
    frames = os.path.join(SALIDA, "frames"); os.makedirs(frames, exist_ok=True)
    sc = bpy.context.scene
    muestra = "--muestra" in sys.argv
    if muestra:
        lista = [F(b["t0"] + b["dur"] * 0.7) - F(b["t0"] + b["dur"] * 0.7) % PASO for b in T]
        if os.environ.get("BEATS"):
            lista = [lista[int(i)] for i in os.environ["BEATS"].split(",")]
    else:
        lista = range(sc.frame_start, sc.frame_end + 1, PASO)
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
