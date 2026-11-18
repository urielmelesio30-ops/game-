# -*- coding: utf-8 -*-
"""«¿ES GOL O NO?» en 3D limpio (Blender Workbench): reglas de fútbol que casi nadie conoce.
Vídeo 1: saque de banda directo a portería.
Regla (IFAB, Regla 15): no se puede marcar gol directamente de un saque de banda. Si entra directo en la portería
rival → saque de puerta; si entra directo en la propia → córner para el rival. Si lo toca cualquier otro jugador
antes de entrar, el gol vale.
Uso: python futbol3d.py [--muestra]"""
import json, math, os, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import audio
import plano as PL
import bpy

RAIZ = os.path.dirname(AQUI)
SLUG = "37-es-gol-saque-de-banda"
SALIDA = os.path.join(RAIZ, "salida", SLUG)
FUENTES = os.path.join(RAIZ, "fuentes")
FPS = 30
W, H = 1080, 1920

BEATS = [
    dict(say="Sacas de banda… y la metes directa en la portería."),
    dict(say="¿Es gol?", etiqueta=("¿ES GOL?", "amarillo")),
    dict(say="Pues no.", etiqueta=("NO ES GOL", "rojo"), x=True, silbato=0.05),
    dict(say="Un saque de banda nunca puede ser gol directo."),
    dict(say="Si entra en la portería rival, es saque de puerta para ellos.", etiqueta=("SAQUE DE PUERTA", "amarillo")),
    dict(say="Y si la metes en tu propia portería… es córner para el rival.", etiqueta=("CÓRNER PARA EL RIVAL", "rojo")),
    dict(say="Eso sí: si otro jugador la toca antes de entrar… gol válido.", etiqueta=("¡GOL VÁLIDO!", "verde"), gol=0.75),
    dict(say="¿Lo sabías? Comenta sí o no, y sígueme para más reglas.", etiqueta=("¿LO SABÍAS?", "amarillo")),
]


# ------------------------------------------------------------- tiempos (voz primero)
def tiempos():
    t = 0.05
    out = []
    for b in BEATS:
        a = audio.voz(b["say"])
        d = len(a) / audio.VOZ_SR
        out.append(dict(b, t0=t, dur=d + 0.25, audio=a, palabras=PL.tiempos_palabras(b["say"], t, d)))
        t += d + 0.25
    return out, t + 0.6


# ------------------------------------------------------------- Blender
def col(r, g, b):
    return (r / 255, g / 255, b / 255, 1)


MATS = {}


def mat(nombre, rgb):
    if nombre not in MATS:
        m = bpy.data.materials.new(nombre)
        m.diffuse_color = col(*rgb)
        MATS[nombre] = m
    return MATS[nombre]


def objeto(o, m, padre=None, suave=True):
    o.data.materials.append(m)
    if suave and o.type == "MESH":
        for p in o.data.polygons:
            p.use_smooth = True
    if padre:
        o.parent = padre
    return o


def caja(loc, esc, m, padre=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = esc
    return objeto(o, m, padre, suave=False)


def cil(loc, r, h, m, padre=None, rot=(0, 0, 0), lados=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=lados)
    return objeto(bpy.context.object, m, padre)


def esfera(loc, r, m, padre=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12)
    return objeto(bpy.context.object, m, padre)


def vacio(loc, padre=None):
    bpy.ops.object.empty_add(location=loc)
    o = bpy.context.object
    if padre:
        o.parent = padre
    return o


def jugador(pos, ang, camiseta, pantalon, piel=(236, 196, 160), pelo=(40, 30, 26), gorra=None):
    """Muñeco sencillo con brazos y piernas articulados. Mira hacia +Y local."""
    root = vacio(pos)
    root.rotation_euler = (0, 0, ang)
    mc, mp, mpi, mpe = mat("c" + str(camiseta), camiseta), mat("p" + str(pantalon), pantalon), mat("piel", piel), mat("pelo" + str(pelo), pelo)
    cil((0, 0, 1.25), 0.24, 0.62, mc, root)                      # torso
    cil((0, 0, 0.9), 0.23, 0.22, mp, root)                       # cadera
    esfera((0, 0, 1.78), 0.17, mpi, root)                        # cabeza
    gor = esfera((0, -0.02, 1.84), 0.172, mpe, root); gor.scale = (1, 1, 0.75)
    cil((0, 0, 1.6), 0.07, 0.1, mpi, root)                       # cuello
    partes = {}
    for lado, sx in (("izq", -1), ("der", 1)):
        hombro = vacio((sx * 0.31, 0, 1.5), root)
        cil((0, 0, -0.3), 0.07, 0.6, mc if False else mpi, hombro)
        cil((0, 0, -0.1), 0.085, 0.22, mc, hombro)                # manga
        esfera((0, 0, -0.62), 0.075, mpi, hombro)
        partes["brazo_" + lado] = hombro
        cadera = vacio((sx * 0.12, 0, 0.85), root)
        cil((0, 0, -0.2), 0.1, 0.4, mp, cadera)
        cil((0, 0, -0.55), 0.075, 0.45, mpi, cadera)
        bota = caja((0, 0.06, -0.82), (0.07, 0.14, 0.05), mat("bota", (30, 30, 36)), cadera)
        partes["pierna_" + lado] = cadera
    partes["root"] = root
    return partes


def clave(o, prop, valor, f):
    setattr(o, prop, valor)
    o.keyframe_insert(data_path=prop, frame=f)


def construir(T, total):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, int(total * FPS)
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_shadows = True
    sh.shadow_intensity = 0.45
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    sh.show_specular_highlight = False
    sc.display.light_direction = (0.35, -0.45, 0.82)
    sc.display.render_aa = "11"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("mundo"); sc.world = w
    w.color = (0.03, 0.06, 0.14)

    # --- campo: franjas de césped
    for k in range(-12, 6):
        caja((0, k * 3 + 1.5, -0.05), (40, 1.5, 0.05), mat("cesped" + str(k % 2), (52, 150, 72) if k % 2 else (62, 168, 82)))
    blanco = mat("linea", (245, 248, 250))
    L = lambda x0, y0, x1, y1: caja(((x0 + x1) / 2, (y0 + y1) / 2, 0.005), (max(0.06, abs(x1 - x0) / 2), max(0.06, abs(y1 - y0) / 2), 0.006), blanco)
    L(-15, 0, 15, 0)                    # línea de fondo
    L(-15, -40, -15, 0)                 # banda
    L(-8.0, -5.5, 8.0, -5.5); L(-8.0, -5.5, -8.0, 0); L(8.0, -5.5, 8.0, 0)          # área chica (proporción reducida)
    L(-13, -14, 13, -14); L(-13, -14, -13, 0); L(13, -14, 13, 0)                  # área grande
    caja((0, -10, 0.006), (0.12, 0.12, 0.006), blanco)                              # punto de penalti
    # gradas sencillas al fondo
    for k in range(5):
        caja((0, 9 + k * 1.6, 0.5 + k * 1.0), (40, 0.8, 0.5 + k * 0.05), mat("grada" + str(k % 2), (24, 40, 90) if k % 2 else (30, 52, 110)))
    caja((-26, -15, 3), (8, 40, 3), mat("grada0", (24, 40, 90)))
    # público (puntos de colores)
    rng = np.random.default_rng(3)
    for k in range(160):
        c = [(240, 90, 90), (250, 220, 90), (90, 160, 250), (250, 250, 250), (250, 140, 60)][k % 5]
        esfera((rng.uniform(-30, 30), 9.2 + (k % 5) * 1.6, 1.25 + (k % 5) * 1.0), 0.22, mat("pub" + str(k % 5), c))
    # --- portería
    poste = mat("poste", (250, 250, 250))
    for sx in (-1, 1):
        cil((sx * 3.66, 0, 1.22), 0.07, 2.44, poste)
        cil((sx * 3.66, 1.6, 0.6), 0.03, 1.2, poste)
    cil((0, 0, 2.44), 0.07, 7.32 + 0.14, poste, rot=(0, math.pi / 2, 0))
    red = mat("red", (215, 225, 235))
    for (loc, esc, rot) in (((0, 0.8, 2.44), (3.66, 0.8, 1), (0, 0, 0)), ((0, 1.6, 1.22), (3.66, 1.22, 1), (math.pi / 2, 0, 0)),
                            ((-3.66, 0.8, 1.22), (0.8, 1.22, 1), (0, math.pi / 2, 0)), ((3.66, 0.8, 1.22), (0.8, 1.22, 1), (0, math.pi / 2, 0))):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=28, y_subdivisions=14, size=2, location=loc, rotation=rot)
        o = bpy.context.object
        o.scale = esc
        o.modifiers.new("w", "WIREFRAME").thickness = 0.025
        o.data.materials.append(red)
    # banderín de córner
    cil((-15, 0, 0.9), 0.06, 1.8, poste)
    bpy.ops.mesh.primitive_plane_add(size=0.9, location=(-15, 0.45, 1.4), rotation=(math.pi / 2, 0, math.pi / 2))
    bpy.context.object.data.materials.append(mat("banderin", (250, 210, 50)))

    # --- jugadores
    TU, TU_P = (245, 245, 245), (30, 40, 90)
    RIV, RIV_P = (250, 140, 40), (25, 25, 35)
    sacador = jugador((-15.6, -9, 0), math.radians(-60), TU, TU_P)
    portero = jugador((0, -0.9, 0), math.radians(180), (40, 200, 120), (30, 30, 30))
    companero = jugador((-3.2, -6.5, 0), math.radians(-150), TU, TU_P)
    rivales = [jugador(p, math.radians(a), RIV, RIV_P) for p, a in (((2.6, -3.6, 0), 200), ((2.5, -7.5, 0), 160), ((-6.5, -8.5, 0), 230))]

    balon = esfera((-15.6, -9, 2.3), 0.2, mat("balon", (255, 255, 255)))

    # --- cámara con objetivo
    bpy.ops.object.camera_add(location=(-22, -20, 9))
    cam = bpy.context.object; sc.camera = cam
    cam.data.lens = 26
    obj = vacio((-4, -4, 1))
    tc = cam.constraints.new("TRACK_TO"); tc.target = obj; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    return dict(sacador=sacador, portero=portero, companero=companero, rivales=rivales, balon=balon, cam=cam, obj=obj)


def F(t):
    return int(round(t * FPS))


def animar(E, T, total):
    s, b, cam, obj, por, comp = E["sacador"], E["balon"], E["cam"], E["obj"], E["portero"], E["companero"]

    def saque(t0, destino, t_lanz=0.45, t_vuelo=1.1, desvio=None):
        """Animación de un saque de banda: brazos atrás, lanza, el balón vuela a destino (con desvío opcional)."""
        for lado in ("izq", "der"):
            br = s["brazo_" + lado]
            clave(br, "rotation_euler", (0, 0, 0), F(t0 - 0.05))
            clave(br, "rotation_euler", (math.radians(200), 0, 0), F(t0 + t_lanz))
            clave(br, "rotation_euler", (math.radians(110), 0, 0), F(t0 + t_lanz + 0.18))
            clave(br, "rotation_euler", (math.radians(20), 0, 0), F(t0 + t_lanz + 0.9))
        p0 = np.array((-15.6, -9, 2.3))
        mano = np.array((-15.45, -9.15, 2.45))
        tramos = [(mano, np.array(desvio), 2.2), (np.array(desvio), np.array(destino), 0.6)] if desvio else [(mano, np.array(destino), 3.2)]
        f = F(t0 - 0.05)
        clave(b, "location", tuple(p0), f)
        clave(b, "location", tuple(mano), F(t0 + t_lanz))
        t = t0 + t_lanz
        for i, (a, z, alto) in enumerate(tramos):
            dur = t_vuelo * (0.75 if desvio and i == 0 else (0.35 if desvio else 1.0))
            n = max(2, F(dur))
            for k in range(1, n + 1):
                u = k / n
                p = a + (z - a) * u
                p[2] += alto * 4 * u * (1 - u)
                clave(b, "location", tuple(p), F(t) + k)
            t += dur
        # el balón cae dentro de la red
        fin = np.array(destino)
        clave(b, "location", tuple(fin + (0, 0.6, -0.4)), F(t + 0.25))
        clave(b, "location", (fin[0], fin[1] + 0.7, 0.13), F(t + 0.6))
        return t

    def camara(t, pos, mira, lens=None):
        clave(cam, "location", pos, F(t))
        clave(obj, "location", mira, F(t))
        if lens:
            cam.data.lens = lens
            cam.data.keyframe_insert("lens", frame=F(t))

    g = {i: b_ for i, b_ in enumerate(T)}
    # 0: saque directo a portería (cámara detrás del sacador)
    t_fin = saque(g[0]["t0"] + 0.4, (-1.2, 0.6, 1.4))
    # el portero salta tarde
    clave(por["root"], "location", (0, -0.9, 0), F(t_fin - 0.4))
    clave(por["root"], "location", (-0.9, -0.9, 0.5), F(t_fin))
    clave(por["root"], "location", (-0.9, -0.9, 0), F(t_fin + 0.35))
    for lado in ("izq", "der"):
        clave(por["brazo_" + lado], "rotation_euler", (0, 0, 0), F(t_fin - 0.4))
        clave(por["brazo_" + lado], "rotation_euler", (math.radians(150), 0, math.radians(30 if lado == "izq" else -30)), F(t_fin))
    # 1-2: plano de la portería (balón en la red)
    # 3: vista cenital de la jugada
    # 4: saque de puerta: el portero pone el balón en el área chica
    t4 = g[4]["t0"]
    clave(b, "location", (-1.2, 1.3, 0.13), F(t4))
    clave(b, "location", (-2, -4.5, 0.13), F(t4 + 1.4))
    clave(por["root"], "location", (-0.9, -0.9, 0), F(t4))
    clave(por["root"], "location", (-2.2, -3.8, 0), F(t4 + 1.4))
    # 5: córner (cámara al banderín)
    t5 = g[5]["t0"]
    clave(b, "location", (-2, -4.5, 0.13), F(t5))
    clave(b, "location", (-14.6, -0.6, 0.13), F(t5 + 0.1))
    # 6: repetición con toque del compañero → gol válido
    t6 = g[6]["t0"]
    clave(b, "location", (-15.6, -9, 2.3), F(t6))
    cabeza = (-3.2, -6.5, 2.0)
    t_gol = saque(t6 + 0.3, (1.6, 0.6, 1.0), desvio=cabeza, t_vuelo=1.4)
    E["t_fin"], E["t_gol"], E["t_cabeza"] = t_fin, t_gol, t6 + 0.3 + 0.45 + 1.4 * 0.75
    clave(comp["root"], "location", (-3.2, -6.5, 0), F(t6 + 1.1))
    clave(comp["root"], "location", (-3.2, -6.5, 0.45), F(t6 + 1.75))
    clave(comp["root"], "location", (-3.2, -6.5, 0), F(t6 + 2.1))
    # 7: plano general girando
    t7 = g[7]["t0"]
    PLANOS = {
        0: (((-19.6, -12.6, 3.3), (-9, -4, 1.4), 24), ((-10, -10.5, 4.2), (-1, 0, 1.2), 26)),
        1: (((2.8, -6.8, 1.9), (-1.2, 0.8, 0.9), 30), ((2.4, -6.0, 1.7), (-1.2, 0.8, 0.8), 33)),
        2: (((2.0, -5.0, 1.5), (-1.2, 0.8, 0.7), 34), ((1.8, -4.5, 1.4), (-1.2, 0.8, 0.6), 37)),
        3: (((-7.5, -11, 24), (-7, -5, 0), 22), ((-6.5, -10.5, 22), (-6, -5, 0), 22)),
        4: (((5, -13, 6), (-1, -3, 0.5), 26), ((4, -12, 5), (-1.5, -3.5, 0.5), 28)),
        5: (((-9.5, -7.5, 3.0), (-14.6, -0.4, 0.8), 28), ((-10.5, -6.0, 2.5), (-14.6, -0.3, 0.8), 32)),
        6: (((-19.6, -12.6, 3.3), (-9, -4, 1.4), 24), ((-9, -12, 4), (0, 0, 1.2), 26)),
        7: (((-16, -16, 9), (-3, -4, 0.5), 22), ((4, -19, 9), (-3, -4, 0.5), 22)),
    }
    # trayectoria punteada (solo en la vista cenital)
    p0, p1 = np.array((-15.45, -9.15, 2.45)), np.array((-1.2, 0.6, 1.4))
    for k in range(1, 22):
        u = k / 22
        p = p0 + (p1 - p0) * u; p[2] += 3.2 * 4 * u * (1 - u)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=tuple(p), segments=12, ring_count=6)
        o = bpy.context.object; o.data.materials.append(mat("traza", (255, 230, 60)))
        for fr_, v in ((0, True), (F(g[3]["t0"]) - 1, True), (F(g[3]["t0"]), False), (F(g[3]["t0"] + g[3]["dur"]), False), (F(g[3]["t0"] + g[3]["dur"]) + 1, True)):
            o.hide_render = v; o.keyframe_insert("hide_render", frame=fr_)
    for i_, (a_, z_) in PLANOS.items():
        b_ = g[i_]
        camara(b_["t0"], *a_)
        camara(b_["t0"] + b_["dur"] - 0.22, *z_)


# ------------------------------------------------------------- movimiento de los jugadores (carrera, respiración, porterías, celebración)
def ruta(pts):
    def f(t):
        if t <= pts[0][0]:
            return pts[0][1]
        for (ta, pa), (tb, pb) in zip(pts, pts[1:]):
            if t <= tb:
                u = (t - ta) / max(1e-6, tb - ta)
                u = u * u * (3 - 2 * u)
                return (pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u)
        return pts[-1][1]
    return f


def limpiar_anim(partes, conservar=()):
    for k, o in partes.items():
        if k in conservar:
            continue
        o.animation_data_clear()


def animar_jugadores(E, T, total):
    g = {i: b for i, b in enumerate(T)}
    t0 = lambda i: g[i]["t0"]
    t1 = lambda i: g[i]["t0"] + g[i]["dur"]
    t_fin, t_gol, t_cab = E["t_fin"], E["t_gol"], E["t_cabeza"]
    r0, r1, r2 = E["rivales"]
    J = []
    # rivales: corren hacia la portería mientras vuela el balón; se recolocan en la repetición
    for partes, ini, dest, extra in ((r0, (2.6, -3.6), (1.0, -1.8), (4.0, -9.0)), (r1, (2.5, -7.5), (0.6, -4.6), (1.0, -12.0)), (r2, (-6.5, -8.5), (-3.4, -5.2), (-11.0, -3.0))):
        J.append(dict(p=partes, ruta=ruta([(0, ini), (t0(0) + 1.0, ini), (t1(0), dest), (t0(4), dest), (t1(4) - 0.5, extra), (t0(6) - 0.01, extra), (t0(6), ini),
                                             (t0(6) + 1.2, ini), (t_gol + 0.3, dest), (t1(7), dest)]), foco=(-1, -2)))
    # compañero: se desmarca, salta a cabecear y celebra
    comp = E["companero"]
    J.append(dict(p=comp, ruta=ruta([(0, (-4.5, -9.0)), (t0(0) + 0.6, (-4.5, -9.0)), (t1(0), (-5.6, -2.8)), (t0(6) - 0.01, (-5.6, -2.8)), (t0(6), (-5.0, -9.5)),
                                     (t_cab, (-3.2, -6.5)), (t_gol + 0.4, (-3.2, -6.5)), (t1(6) + 0.8, (-10.5, -3.0)), (t1(7), (-10.5, -3.0))]),
                  foco=(-1, -2), salto=[(t_cab - 0.25, t_cab + 0.25, 0.55)], celebra=(t_gol + 0.3, total)))
    # sacador: entra al campo tras el saque
    sac = E["sacador"]
    J.append(dict(p=sac, ruta=ruta([(0, (-15.6, -9)), (t0(0) + 1.4, (-15.6, -9)), (t1(0), (-12.0, -7.6)), (t0(6) - 0.01, (-12.0, -7.6)), (t0(6), (-15.6, -9)),
                                    (t0(6) + 1.5, (-15.6, -9)), (t1(6) + 0.8, (-11.0, -3.6)), (t1(7), (-11.0, -3.6))]),
                  foco=(-1, -2), sin_brazos=(0, t0(6) + 1.6), celebra=(t_gol + 0.8, total)))
    # portero: sigue el balón y se estira
    por = E["portero"]
    J.append(dict(p=por, ruta=ruta([(0, (0, -0.9)), (t0(0) + 0.5, (0, -0.9)), (t_fin - 0.5, (-0.4, -0.9)), (t_fin, (-1.5, -0.9)), (t0(4), (-1.5, -0.9)),
                                    (t0(4) + 1.4, (-2.2, -3.8)), (t1(5), (-0.5, -1.2)), (t0(6), (0, -0.9)), (t_gol - 0.4, (-0.3, -0.9)), (t_gol, (1.2, -0.9)), (total, (1.2, -0.9))]),
                  foco=(-6, -8), estirada=[(t_fin - 0.35, 1, t0(3)), (t_gol - 0.3, -1, t1(6))]))
    for j in J:
        limpiar_anim(j["p"], conservar=("brazo_izq", "brazo_der") if j["p"] is sac else ())
    n = int(total * FPS) + 1
    for j in J:
        P = j["p"]
        fase, ang_prev = 0.0, None
        prev = j["ruta"](0)
        for f in range(n):
            t = f / FPS
            x, y = j["ruta"](t)
            vx, vy = (x - prev[0]) * FPS, (y - prev[1]) * FPS
            v = math.hypot(vx, vy)
            prev = (x, y)
            if v > 12:          # salto de posición (corte de cámara): no animar la carrera
                v = 0
            fase += v / FPS * 4.4
            amp = min(1.0, v / 3.0)
            if v > 0.6:
                ang = math.atan2(vy, vx) - math.pi / 2
            else:
                ang = math.atan2(j["foco"][1] - y, j["foco"][0] - x) - math.pi / 2
            if ang_prev is not None:
                d = (ang - ang_prev + math.pi) % (2 * math.pi) - math.pi
                ang = ang_prev + d * 0.25
            ang_prev = ang
            z = 0.02 * math.sin(t * 2 * math.pi * 0.6 + hash(id(P)) % 7) + abs(math.sin(fase)) * 0.06 * amp
            tilt = 0.0
            celebra = "celebra" in j and j["celebra"][0] <= t <= j["celebra"][1]
            if celebra:
                z += 0.35 * abs(math.sin((t - j["celebra"][0]) * 2 * math.pi * 1.4))
            for a, b_, h in j.get("salto", []):
                if a <= t <= b_:
                    u = (t - a) / (b_ - a); z += h * 4 * u * (1 - u)
            for (te, lado, tfin) in j.get("estirada", []):
                if te <= t <= tfin:
                    u = min(1, (t - te) / 0.3)
                    tilt = lado * math.radians(75) * u
                    z += 0.45 * 4 * min(u, 0.5) * (1 - min(u, 0.5)) if u < 1 else 0.2
            P["root"].location = (x, y, z); P["root"].keyframe_insert("location", frame=f)
            P["root"].rotation_euler = (0, tilt, ang); P["root"].keyframe_insert("rotation_euler", frame=f)
            pierna = math.radians(38) * amp * math.sin(fase)
            P["pierna_izq"].rotation_euler = (pierna, 0, 0); P["pierna_izq"].keyframe_insert("rotation_euler", frame=f)
            P["pierna_der"].rotation_euler = (-pierna, 0, 0); P["pierna_der"].keyframe_insert("rotation_euler", frame=f)
            sb = j.get("sin_brazos")
            if sb and sb[0] <= t <= sb[1] and not celebra:
                continue
            if celebra:
                br = math.radians(165) + 0.2 * math.sin(t * 9)
                bi, bd = (br, 0, math.radians(15)), (br, 0, math.radians(-15))
            elif tilt:
                bi, bd = (math.radians(160), 0, 0), (math.radians(160), 0, 0)
            else:
                brazo = math.radians(32) * amp * math.sin(fase) + math.radians(4) * math.sin(t * 3.8)
                bi, bd = (-brazo, 0, math.radians(6)), (brazo, 0, math.radians(-6))
            P["brazo_izq"].rotation_euler = bi; P["brazo_izq"].keyframe_insert("rotation_euler", frame=f)
            P["brazo_der"].rotation_euler = bd; P["brazo_der"].keyframe_insert("rotation_euler", frame=f)


# ------------------------------------------------------------- montaje 2D (texto, marcador, etiquetas)
from PIL import Image, ImageDraw, ImageFont

_f = {}


def fuente(tam):
    if tam not in _f:
        _f[tam] = ImageFont.truetype(os.path.join(FUENTES, "Anton-Regular.ttf"), tam)
    return _f[tam]


def cursiva(im, k=0.18):
    w, h = im.size
    return im.transform((w + int(h * k), h), Image.AFFINE, (1, k, -h * k, 0, 1, 0), Image.BICUBIC)


COLS = dict(amarillo=((232, 250, 60), (14, 14, 20)), rojo=((240, 60, 70), (255, 255, 255)), verde=((70, 220, 120), (10, 20, 14)))


def etiqueta(txt, estilo, tam=110):
    fondo, letra = COLS[estilo]
    f = fuente(tam)
    l, t, r, b = f.getbbox(txt)
    im = Image.new("RGBA", (r - l + 70, b - t + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width - 1, im.height - 1), fill=fondo + (255,))
    d.text((35 - l, 25 - t), txt, font=f, fill=letra)
    return cursiva(im)


def texto_arriba(palabras, k):
    """Frase de la voz arriba: palabras ya dichas en gris azulado, la actual en blanco (como en el formato de referencia)."""
    f = fuente(96)
    piezas = []
    for i, p in enumerate(palabras):
        colr = (255, 255, 255) if i == k else (170, 186, 214)
        l, t, r, b = f.getbbox(p.upper())
        im = Image.new("RGBA", (r - l + 14, 140), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((4 - l + 4, 10 - t + 5), p.upper(), font=f, fill=(0, 0, 0, 120))
        d.text((4 - l, 10 - t), p.upper(), font=f, fill=colr)
        piezas.append(im)
    lineas, act, ancho = [], [], 0
    for p in piezas:
        if act and ancho + p.width > W - 120:
            lineas.append(act); act, ancho = [], 0
        act.append(p); ancho += p.width + 10
    lineas.append(act)
    out = Image.new("RGBA", (W, 150 * len(lineas)), (0, 0, 0, 0))
    for j, l_ in enumerate(lineas):
        x = (W - sum(p.width + 10 for p in l_)) // 2
        for p in l_:
            out.alpha_composite(p, (x, j * 140)); x += p.width + 10
    return cursiva(out, 0.12)


def marcador(tu, rival, resalta=None):
    f, f2 = fuente(64), fuente(72)
    im = Image.new("RGBA", (470, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 290, 99), fill=(14, 18, 40, 235))
    d.text((24, 10), "TÚ · RIVAL", font=f, fill=(255, 255, 255))
    d.rectangle((290, 0, 380, 99), fill=(232, 250, 60) if resalta == "tu" else (24, 30, 60, 235))
    d.rectangle((380, 0, 469, 99), fill=(24, 30, 60, 235))
    d.text((318, 6), str(tu), font=f2, fill=(14, 14, 20) if resalta == "tu" else (255, 255, 255))
    d.text((408, 6), str(rival), font=f2, fill=(255, 255, 255))
    return cursiva(im, 0.1)


def montar(T, total, frames_dir, muestra=False):
    xmark = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    dx = ImageDraw.Draw(xmark)
    dx.line((40, 40, 380, 380), fill=(240, 60, 70, 220), width=60); dx.line((380, 40, 40, 380), fill=(240, 60, 70, 220), width=60)
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    n = int(total * FPS)
    cuadros = range(n) if not muestra else [F(b["t0"] + b["dur"] * 0.7) for b in T]
    for fi in cuadros:
        tg = fi / FPS
        kb = max([i for i, b in enumerate(T) if b["t0"] <= tg], default=0)
        b = T[kb]; tl = tg - b["t0"]
        fr = Image.open(os.path.join(frames_dir, f"f_{fi:04d}.png")).convert("RGBA")
        # degradado oscuro arriba para que se lea el texto
        if "GRAD" not in _f:
            g = np.zeros((H, W, 4), np.uint8)
            a = np.clip(1 - np.arange(H) / 520, 0, 1) * 170
            g[..., 3] = a[:, None].astype(np.uint8)
            _f["GRAD"] = Image.fromarray(g, "RGBA")
        fr.alpha_composite(_f["GRAD"])
        pts = b["palabras"]
        k = max([i for i, (t0, _) in enumerate(pts) if tg >= t0], default=0)
        g0 = (k // 4) * 4
        fr.alpha_composite(texto_arriba([p for _, p in pts[g0:g0 + 4]], k - g0), (0, 170))
        # etiqueta grande en escena
        if "etiqueta" in b and tl > 0.15:
            u = min(1, (tl - 0.15) / 0.18)
            et = etiqueta(*b["etiqueta"])
            s = 0.6 + 0.4 * u + 0.06 * math.sin(min(1, u) * math.pi)
            et = et.resize((int(et.width * s), int(et.height * s)), Image.BICUBIC)
            fr.alpha_composite(et, (int(W / 2 - et.width / 2), int(600 - et.height / 2)))
        if b.get("x") and tl > 0.1:
            u = min(1, (tl - 0.1) / 0.2)
            xm = xmark.resize((int(420 * (0.5 + 0.5 * u)),) * 2)
            fr.alpha_composite(xm, (int(W / 2 - xm.width / 2), int(1080 - xm.height / 2)))
        gol_tu = 1 if (kb == 6 and tl > b["dur"] * b.get("gol", 1)) or kb == 7 else 0
        fr.alpha_composite(marcador(gol_tu, 0, "tu" if gol_tu else None), (40, 1330))
        arr = np.asarray(fr.convert("RGB"))
        if muestra:
            Image.fromarray(arr).resize((360, 640)).save(os.path.join(SALIDA, f"muestra_{kb:02d}.png"))
        else:
            ff.stdin.write(arr.tobytes())
    if muestra:
        return
    ff.stdin.close(); ff.wait()
    # audio: voz + ambiente de estadio + silbato + música suave
    sr = audio.MUS_SR
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for b in T:
        i = int(b["t0"] * audio.VOZ_SR); voz[i:i + len(b["audio"])] += b["audio"]
    wav_voz = os.path.join(SALIDA, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    n = int((total + 1) * sr)
    rng = np.random.default_rng(1)
    ruido = np.cumsum(rng.standard_normal(n)).astype(np.float32)
    ruido = audio._hp(ruido, 200); ruido = audio._lp(ruido, 1200)
    ruido = ruido / (np.abs(ruido).max() + 1e-6) * 0.25
    lento = 0.7 + 0.3 * np.sin(np.arange(n) / sr * 0.7)
    amb = ruido * lento
    mus = audio.musica(total + 1, semilla=4, bpm=110, tono="D")
    if mus.ndim == 2:
        mus = mus.mean(axis=1)
    mus = mus[:n] * 0.5
    mezcla = amb + mus[:len(amb)] if len(mus) >= len(amb) else amb
    for b in T:
        if "silbato" in b:
            t0 = b["t0"] + b["silbato"]
            m = int(0.45 * sr); tt = np.arange(m) / sr
            s = 0.5 * np.sin(2 * np.pi * (3000 + 120 * np.sin(2 * np.pi * 40 * tt)) * tt) * np.minimum(1, (0.45 - tt) * 20)
            i = int(t0 * sr); mezcla[i:i + m] += s.astype(np.float32)
        if "gol" in b:
            t0 = b["t0"] + b["dur"] * b["gol"]
            m = int(2.5 * sr); i = int(t0 * sr)
            env = np.minimum(1, np.arange(m) / (0.15 * sr)) * np.exp(-np.arange(m) / (1.2 * sr))
            mezcla[i:i + m] += (ruido[i:i + m] * 3.0 * env).astype(np.float32)
            e = audio.efecto("logro"); e = e.mean(axis=1) if e.ndim == 2 else e; mezcla[i:i + len(e)] += e[:len(mezcla) - i] * 1.2
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


def portada():
    """Portada con el título en la zona 3:4 de la cuadrícula, sobre un fotograma del vídeo."""
    fr = Image.open(os.path.join(SALIDA, "frames", f"f_{F(T_[1]['t0'] + 0.5):04d}.png")).convert("RGBA")
    osc = Image.new("RGBA", fr.size, (6, 10, 30, 120)); fr.alpha_composite(osc)
    t1 = etiqueta("¿ES GOL", "amarillo", 190); t2 = etiqueta("O NO?", "amarillo", 190)
    fr.alpha_composite(t1, ((W - t1.width) // 2, 560)); fr.alpha_composite(t2, ((W - t2.width) // 2, 820))
    sub = etiqueta("SAQUE DE BANDA DIRECTO", "rojo", 70)
    fr.alpha_composite(sub, ((W - sub.width) // 2, 1100))
    fr.convert("RGB").save(os.path.join(SALIDA, "portada.png"))


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    T_, total = tiempos()
    print(f"[{SLUG}] {total:.1f}s", flush=True)
    E = construir(T_, total)
    animar(E, T_, total)
    animar_jugadores(E, T_, total)
    frames = os.path.join(SALIDA, "frames"); os.makedirs(frames, exist_ok=True)
    sc = bpy.context.scene
    muestra = "--muestra" in sys.argv
    lista = [F(b["t0"] + b["dur"] * 0.7) for b in T_] if muestra else range(sc.frame_start, sc.frame_end + 1)
    for fi in lista:
        p = os.path.join(frames, f"f_{fi:04d}.png")
        if os.path.exists(p) and not muestra:
            continue
        sc.frame_set(fi)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        if fi % 60 == 0:
            print(f"  fotograma {fi}/{sc.frame_end}", flush=True)
    montar(T_, total, frames, muestra)
    if not muestra:
        portada()
