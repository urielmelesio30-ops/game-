# -*- coding: utf-8 -*-
"""Vídeo 3D: la teoría más comentada de Vengadores: Doomsday (y otras dos).

Reutiliza el pasillo 3D de video3d_doomsday.py con estaciones nuevas. Solo se
usan la mascota del canal (normal y disfrazada de villana) y piezas genéricas.
Todo se presenta como teoría de fans, no como dato confirmado.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import video3d_doomsday as V
import tres_d as T
import bpy

audio.PRONUNCIA[:0] = [("Franklin Richards", "Fránklin Ríchards"), ("Tony Stark", "Tóni Estárk"), ("Sue", "Su"), ("Stark", "Estárk")]

V.SLUG = "14-doomsday-teorias-3d"
V.SALIDA = os.path.join(T.RAIZ, "salida", V.SLUG)
V.NUMEROS = False
V.BEATS = [
    dict(e="pregunta", say="¿Y si Doom… en realidad no fuera Víctor von Doom?"),
    dict(e="variante", say="La teoría más comentada: que Robert Downey Jr. interprete a un Tony Stark de otro universo."),
    dict(e="cara", say="Sería una forma de explicar por qué el villano tiene la misma cara que Iron Man."),
    dict(e="caido", say="Algunos fans van más allá: un héroe caído que culpa a los Vengadores de todo."),
    dict(e="franklin", say="Otra teoría: Doom quiere el poder de Franklin Richards, el hijo de Reed y Sue."),
    dict(e="incursion", say="Y hay quien cree que todo empieza con choques entre universos: las incursiones."),
    dict(e="aviso", say="Ojo: nada de esto está confirmado. Son teorías de fans."),
    dict(e="cta", say="¿Tú qué crees: Stark o Doom? Te leo en comentarios. Y sígueme para más."),
]
V.EFECTOS = {"pregunta": "golpe", "variante": "subida", "caido": "golpe", "franklin": "logro", "incursion": "boom", "aviso": "golpe"}

CIAN = (0.3, 0.85, 1.0)
VERDE = (0.2, 1.0, 0.4)


def texto(t, y, z, tam, color, em=2.0, extr=0.12):
    return T.texto3d(t, (0, y, z), tam, T.mat("t_" + t, color, emision=em), extr=extr)


# ------------------------------------------------------------- estaciones
def c_pregunta(y, anim, ctx):
    q = texto("?", y + 1.6, 0.8, 3.2, VERDE, em=4, extr=0.3)
    anim.setdefault("giran", []).append(q); anim["q"] = q
    T.mascota_villana((-1.9, y + 1.2, 0.0), capa=False, corona=False, ojos_color=CIAN)


def a_pregunta(c):
    q = c["anim"]["q"]
    T.clave(q, "rotation_euler", (math.radians(90), 0, math.radians(-30)), c["F"](c["t0"]))
    T.clave(q, "rotation_euler", (math.radians(90), 0, math.radians(30)), c["F"](c["fin"]))


def c_variante(y, anim, ctx):
    T.mascota_villana((-2.2, y + 1.6, 0.0), capa=False, corona=False, ojos_color=CIAN)
    T.mascota_villana((2.2, y + 1.6, 0.0))
    bpy.ops.mesh.primitive_torus_add(location=(0, y + 1.6, 1.5), rotation=(0, math.radians(90), 0),
                                     major_radius=1.1, minor_radius=0.07, major_segments=28, minor_segments=4)
    aro = bpy.context.object; aro.data.materials.append(T.mat("portal_v", (0.6, 0.3, 1.0), emision=8))
    anim["aro_v"] = aro
    texto("VARIANTE", y + 0.6, 3.3, 0.7, (1.0, 0.85, 0.3), em=2.5)


def a_variante(c):
    aro = c["anim"]["aro_v"]
    T.clave(aro, "scale", (0.01, 0.01, 0.01), c["F"](c["t0"] + 0.2))
    T.clave(aro, "scale", (1, 1, 1), c["F"](c["t0"] + 0.7))


def c_cara(y, anim, ctx):
    marco = ctx["oro"]
    espejo = T.mat("espejo", (0.9, 0.95, 1.0), rugoso=0.02, metal=1.0)
    T.caja("espejo", (1.2, y + 2.4, 1.9), (1.0, 0.05, 1.5), espejo)
    for (dx, dz, sx, sz) in ((0, 1.55, 1.1, 0.08), (0, -1.55, 1.1, 0.08), (1.05, 0, 0.08, 1.6), (-1.05, 0, 0.08, 1.6)):
        T.caja("marco", (1.2 + dx, y + 2.38, 1.9 + dz), (sx, 0.08, sz), marco)
    T.mascota_villana((-1.0, y + 0.6, 0.0), capa=False, corona=False, ojos_color=CIAN)
    texto("MISMA CARA", y + 0.2, 3.9, 0.6, (1.0, 0.85, 0.3))


def c_caido(y, anim, ctx):
    T.caja("ped_roto", (0, y + 1.8, 0.4), (0.9, 0.9, 0.4), ctx["piedra"])
    T.mascota_villana((0, y + 1.8, 0.8))
    trozos = []
    for k in range(10):
        o = T.caja(f"trozo{k}", (0, y + 1.8, 9), (0.18, 0.18, 0.18), T.mat(f"tz{k}", (0.8, 0.15, 0.15), emision=1.5))
        trozos.append(o)
    anim["trozos"] = trozos
    texto("UN HÉROE CAÍDO", y + 0.4, 3.9, 0.55, (1.0, 0.3, 0.3))


def a_caido(c):
    import numpy as np
    rng = np.random.default_rng(4)
    for k, o in enumerate(c["anim"]["trozos"]):
        x = rng.uniform(-2.5, 2.5); yy = c["y"] + 1.8 + rng.uniform(-1, 1)
        T.clave(o, "location", (x, yy, 9), c["F"](c["t0"] + k * 0.08))
        T.clave(o, "location", (x, yy, 0.2), c["F"](c["t0"] + 0.7 + k * 0.08))
        T.clave(o, "rotation_euler", (0, 0, 0), c["F"](c["t0"] + k * 0.08))
        T.clave(o, "rotation_euler", (rng.uniform(0, 3), rng.uniform(0, 3), 0), c["F"](c["t0"] + 0.7 + k * 0.08))


def c_franklin(y, anim, ctx):
    T.caja("ped_f", (0, y + 1.8, 0.5), (0.6, 0.6, 0.5), ctx["piedra"])
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.55, location=(0, y + 1.8, 2.1))
    orbe = bpy.context.object; orbe.data.materials.append(T.mat("orbe", (0.7, 0.85, 1.0), emision=9))
    anim["orbe"] = orbe
    for k, r in enumerate((1.0, 1.35)):
        bpy.ops.mesh.primitive_torus_add(location=(0, y + 1.8, 2.1), major_radius=r, minor_radius=0.03, major_segments=28, minor_segments=4)
        o = bpy.context.object; o.data.materials.append(T.mat(f"orb_r{k}", (0.4, 0.7, 1.0), emision=5))
        anim.setdefault("giran", []).append(o); anim.setdefault("anillos_f", []).append(o)
    texto("EL PODER", y + 0.9, 3.6, 0.6, (0.6, 0.85, 1.0))
    texto("DE FRANKLIN", y + 0.9, 3.0, 0.5, (0.95, 0.95, 0.9), em=1)


def a_franklin(c):
    o = c["anim"]["orbe"]; F = c["F"]
    for k in range(0, int(c["d"] * 4) + 2):
        T.clave(o, "location", (0, c["y"] + 1.8, 2.1 + 0.15 * math.sin(k)), F(c["t0"] + k / 4))
    for i, a in enumerate(c["anim"]["anillos_f"]):
        T.clave(a, "rotation_euler", (0.3 * (i + 1), 0, 0), F(c["t0"]))
        T.clave(a, "rotation_euler", (0.3 * (i + 1) + 2, 0.6, 6.3 * (1 if i else -1)), F(c["fin"]))


def c_incursion(y, anim, ctx):
    plan = []
    for k, (x, col) in enumerate(((-2.6, (0.25, 0.5, 0.95)), (2.6, (0.85, 0.35, 0.2)))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(x, y + 2.5, 2.2))
        p = bpy.context.object; p.data.materials.append(T.mat(f"planeta{k}", col, emision=0.6)); plan.append(p)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, y + 2.5, 2.2))
    flash = bpy.context.object; flash.data.materials.append(T.mat("flash", (1, 0.95, 0.8), emision=25)); flash.scale = (0.01, 0.01, 0.01)
    anim["planetas"] = plan; anim["flash"] = flash
    texto("INCURSIONES", y + 1.0, 4.2, 0.6, (1.0, 0.6, 0.3))


def a_incursion(c):
    F = c["F"]; t0, fin, y = c["t0"], c["fin"], c["y"]
    choque = t0 + c["d"] * 0.6
    for k, p in enumerate(c["anim"]["planetas"]):
        x = -2.6 if k == 0 else 2.6
        T.clave(p, "location", (x, y + 2.5, 2.2), F(t0))
        T.clave(p, "location", (x * 0.35, y + 2.5, 2.2), F(choque))
        T.clave(p, "scale", (1, 1, 1), F(choque))
        T.clave(p, "scale", (0.01, 0.01, 0.01), F(choque + 0.15))
    fl = c["anim"]["flash"]
    T.clave(fl, "scale", (0.01, 0.01, 0.01), F(choque - 0.02))
    T.clave(fl, "scale", (2.6, 2.6, 2.6), F(choque + 0.25))
    T.clave(fl, "scale", (0.01, 0.01, 0.01), F(fin))


def c_aviso(y, anim, ctx):
    T.caja("cartel", (0, y + 2.0, 2.0), (2.3, 0.1, 1.1), T.mat("cartel", (0.08, 0.08, 0.1)))
    for (dx, dz, sx, sz) in ((0, 1.15, 2.4, 0.06), (0, -1.15, 2.4, 0.06), (2.35, 0, 0.06, 1.2), (-2.35, 0, 0.06, 1.2)):
        T.caja("borde", (dx, y + 1.95, 2.0 + dz), (sx, 0.08, sz), T.mat("borde_r", (1.0, 0.15, 0.2), emision=5))
    texto("SIN CONFIRMAR", y + 1.85, 2.0, 0.65, (1.0, 0.25, 0.3), em=4, extr=0.05)
    texto("TEORÍAS DE FANS", y + 1.85, 1.25, 0.4, (0.95, 0.95, 0.9), em=1.5, extr=0.05)


V.EXTRA = {
    "pregunta": dict(construir=c_pregunta, animar=a_pregunta),
    "variante": dict(construir=c_variante, animar=a_variante),
    "cara": dict(construir=c_cara),
    "caido": dict(construir=c_caido, animar=a_caido),
    "franklin": dict(construir=c_franklin, animar=a_franklin),
    "incursion": dict(construir=c_incursion, animar=a_incursion),
    "aviso": dict(construir=c_aviso),
}

if __name__ == "__main__":
    V.main()
