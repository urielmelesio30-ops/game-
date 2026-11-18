# -*- coding: utf-8 -*-
"""Estilo anime 2D (original): personajes de busto con ojos grandes y brillos, sombreado plano (cel shading),
contornos gruesos, líneas de velocidad, fotogramas de impacto, rayos de luz, pétalos y fondos pintados.
No copia ningún personaje ni obra existente."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from historia import W, H, A

SS = 2
LIN = (24, 16, 28)                       # contorno
PIEL, PIEL_S = (255, 222, 196), (232, 176, 150)
PIEL_V, PIEL_VS = (236, 200, 170), (205, 160, 130)   # piel de persona mayor


# ------------------------------------------------------------- utilidades
def lienzo(w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def S(*v):
    return [x * SS for x in v]


def reducir(im):
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


def poli(d, pts, fill, w=6, outline=LIN):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill, outline=outline, width=w * SS if outline else 0)


def curva(p0, p1, p2, n=16):
    """Bézier cuadrática."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


# ------------------------------------------------------------- ojos y caras
def ojo(d, cx, cy, lado, expr, cerrado, iris=(70, 46, 30), iris2=(170, 110, 60), viejo=False):
    """lado=-1 ojo izquierdo (en pantalla), +1 derecho."""
    if cerrado:
        if expr in ("feliz", "sonrisa"):
            d.line([(x * SS, y * SS) for x, y in curva((cx - 40, cy + 6), (cx, cy - 26), (cx + 40, cy + 6))], fill=LIN, width=9 * SS)
        else:
            d.line([(x * SS, y * SS) for x, y in curva((cx - 42, cy + 4), (cx, cy + 14), (cx + 42, cy + 4))], fill=LIN, width=8 * SS)
        return
    sorpresa = expr == "sorpresa"
    # blanco
    d.ellipse(S(cx - 40, cy - 40, cx + 40, cy + 44), fill=(255, 255, 255))
    # iris con degradado (oscuro arriba, claro abajo)
    ri_w, ri_h = (22, 30) if sorpresa else (30, 42)
    d.ellipse(S(cx - ri_w, cy - ri_h + 4, cx + ri_w, cy + ri_h + 4), fill=iris2, outline=LIN, width=3 * SS)
    d.chord(S(cx - ri_w, cy - ri_h + 4, cx + ri_w, cy + ri_h + 4), 180, 360, fill=iris)
    d.ellipse(S(cx - ri_w * 0.45, cy - ri_h * 0.35 + 4, cx + ri_w * 0.45, cy + ri_h * 0.5 + 4), fill=(20, 12, 16))
    # brillos
    d.ellipse(S(cx - ri_w * 0.75, cy - ri_h * 0.7, cx - ri_w * 0.75 + 18, cy - ri_h * 0.7 + 22), fill=(255, 255, 255))
    d.ellipse(S(cx + ri_w * 0.3, cy + ri_h * 0.45, cx + ri_w * 0.3 + 9, cy + ri_h * 0.45 + 9), fill=(255, 255, 255))
    # párpado superior grueso con «ala» hacia fuera
    sup = curva((cx - 46, cy - 18), (cx - 6, cy - 54), (cx + 46, cy - 24))
    if lado < 0:
        sup = [(2 * cx - x, y) for x, y in sup][::-1]
    alto = 12
    pts = sup + [(x, y + alto * (0.3 + 0.7 * math.sin(math.pi * i / (len(sup) - 1)))) for i, (x, y) in enumerate(sup)][::-1]
    exterior = (cx + 54 * (1 if lado > 0 else -1), cy - 30)
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=LIN)
    d.polygon(S(*(sup[-1 if lado > 0 else 0]), *exterior, sup[-3 if lado > 0 else 2][0], sup[-3 if lado > 0 else 2][1] + 8), fill=LIN)
    # párpado según expresión (tapa la parte de arriba del ojo con piel)
    piel = PIEL_V if viejo else PIEL
    if expr in ("decidido", "enfado"):
        hacia = 1 if lado < 0 else -1   # baja hacia la nariz
        d.polygon(S(cx - 50, cy - 60, cx + 50, cy - 60, cx + 50, cy - 18 + 16 * hacia, cx - 50, cy - 18 - 16 * hacia), fill=piel)
        d.line(S(cx - 48, cy - 16 - 16 * hacia, cx + 48, cy - 16 + 16 * hacia), fill=LIN, width=9 * SS)
    elif expr == "triste":
        hacia = -1 if lado < 0 else 1
        d.polygon(S(cx - 50, cy - 60, cx + 50, cy - 60, cx + 50, cy - 26 + 12 * hacia, cx - 50, cy - 26 - 12 * hacia), fill=piel)
        d.line(S(cx - 48, cy - 24 - 12 * hacia, cx + 48, cy - 24 + 12 * hacia), fill=LIN, width=8 * SS)
    # pestaña inferior
    d.line([(x * SS, y * SS) for x, y in curva((cx - 30, cy + 44), (cx, cy + 50), (cx + 30, cy + 42), 8)], fill=LIN, width=4 * SS)
    if viejo:
        d.line(S(cx - 34, cy + 58, cx + 24, cy + 62), fill=PIEL_VS, width=4 * SS)


def ceja(d, cx, cy, lado, expr, col):
    ang = {"decidido": 18, "enfado": 24, "triste": -16, "sorpresa": -6, "feliz": -4, "sonrisa": -4}.get(expr, 4)
    a = math.radians(ang) * (1 if lado < 0 else -1)
    dy = -18 if expr == "sorpresa" else 0
    x0, x1 = cx - 46, cx + 46
    y0 = cy + dy - math.tan(a) * -46
    y1 = cy + dy - math.tan(a) * 46
    d.polygon(S(x0, y0 - 6, x1, y1 - 9, x1, y1 + 5, x0, y0 + 8), fill=col)


def boca(d, cx, cy, tipo, abierta):
    if abierta and tipo != "sonrisa_cerrada":
        if tipo in ("grito", "sorpresa"):
            d.ellipse(S(cx - 30, cy - 18, cx + 30, cy + 40), fill=(120, 30, 40), outline=LIN, width=5 * SS)
            d.chord(S(cx - 22, cy + 10, cx + 22, cy + 38), 0, 180, fill=(240, 120, 120))
        else:
            d.polygon(S(cx - 26, cy - 4, cx + 26, cy - 4, cx + 14, cy + 20, cx - 14, cy + 20), fill=(120, 30, 40), outline=LIN, width=4 * SS)
            d.chord(S(cx - 12, cy + 6, cx + 12, cy + 22), 0, 180, fill=(240, 120, 120))
    elif tipo in ("sonrisa", "feliz", "sonrisa_cerrada"):
        d.line([(x * SS, y * SS) for x, y in curva((cx - 30, cy - 6), (cx, cy + 16), (cx + 30, cy - 6), 10)], fill=LIN, width=5 * SS)
    elif tipo == "triste":
        d.line([(x * SS, y * SS) for x, y in curva((cx - 22, cy + 8), (cx, cy - 6), (cx + 22, cy + 8), 10)], fill=LIN, width=5 * SS)
    else:
        d.line(S(cx - 20, cy, cx + 20, cy + 2), fill=LIN, width=5 * SS)


# ------------------------------------------------------------- personajes de busto (600x800)
PERSONAJES = {
    "onoda": dict(pelo=(26, 24, 34), brillo=(70, 80, 120), ropa=(120, 116, 70), ropa_s=(90, 86, 50), gorra=(105, 100, 58), cuello=(200, 50, 50)),
    "onoda_selva": dict(pelo=(26, 24, 34), brillo=(70, 80, 120), ropa=(108, 100, 62), ropa_s=(78, 72, 44), gorra=(92, 86, 50), cuello=(160, 60, 50), sucio=True),
    "onoda_viejo": dict(pelo=(200, 200, 205), brillo=(240, 240, 245), ropa=(70, 80, 110), ropa_s=(50, 58, 84), viejo=True),
    "suzuki": dict(pelo=(60, 40, 30), brillo=(130, 90, 60), ropa=(60, 120, 200), ropa_s=(40, 86, 150), largo=True, mochila=True),
    "taniguchi": dict(pelo=(150, 150, 155), brillo=(210, 210, 215), ropa=(54, 56, 66), ropa_s=(36, 38, 46), gafas=True, viejo=True, corbata=True),
}


def busto(quien="onoda", expr="serio", boca_abierta=False, cerrado=False, lagrima=False, sudor=False):
    clave = ("BUSTO", quien, expr, boca_abierta, cerrado, lagrima, sudor)
    if clave in A:
        return A[clave]
    P = PERSONAJES[quien]
    viejo = P.get("viejo", False)
    piel, piel_s = (PIEL_V, PIEL_VS) if viejo else (PIEL, PIEL_S)
    im, d = lienzo(600, 820)
    cx = 300
    # ---- cuerpo
    poli(d, [(20, 820), (40, 690), (120, 630), (230, 600), (370, 600), (480, 630), (560, 690), (580, 820)], P["ropa"])
    poli(d, [(20, 820), (40, 690), (120, 630), (200, 612), (170, 820)], P["ropa_s"], 0, None)
    if P.get("mochila"):
        for x in (150, 450):
            d.line(S(x, 625, x + (30 if x < 300 else -30), 820), fill=(180, 60, 40), width=34 * SS)
    # cuello de la camisa
    poli(d, [(230, 600), (300, 690), (370, 600), (350, 585), (250, 585)], piel_s)
    if "cuello" in P:
        poli(d, [(200, 610), (240, 590), (300, 700), (250, 690)], P["ropa"])
        poli(d, [(400, 610), (360, 590), (300, 700), (350, 690)], P["ropa"])
        poli(d, [(215, 625), (245, 612), (262, 650), (230, 660)], P["cuello"], 3)
        poli(d, [(385, 625), (355, 612), (338, 650), (370, 660)], P["cuello"], 3)
    if P.get("corbata"):
        poli(d, [(270, 590), (330, 590), (300, 700)], (240, 240, 240), 3)
        poli(d, [(290, 610), (310, 610), (318, 700), (300, 730), (282, 700)], (150, 40, 50), 3)
    if P.get("sucio"):
        for x, y in ((140, 720), (420, 700), (480, 760), (210, 780)):
            poli(d, [(x, y), (x + 40, y + 6), (x + 32, y + 40), (x - 4, y + 34)], P["ropa_s"], 3)
    # ---- pelo de atrás (detrás de la cara)
    if "gorra" not in P:
        largo = P.get("largo")
        base = [(150, 380 if largo else 300), (140, 200), (185, 112), (260, 76), (340, 76), (415, 112), (460, 200), (450, 380 if largo else 300)]
        poli(d, base, P["pelo"], 6)
    # ---- cuello y cabeza
    d.rectangle(S(255, 470, 345, 600), fill=piel, outline=LIN, width=6 * SS)
    d.polygon(S(255, 500, 345, 470, 345, 560, 255, 580), fill=piel_s)
    for x in (172, 428):   # orejas
        d.ellipse(S(x - 26, 330, x + 26, 410), fill=piel, outline=LIN, width=6 * SS)
    cara = [(180, 230), (178, 330), (192, 400), (226, 458), (272, 500), (300, 510), (328, 500), (374, 458), (408, 400), (422, 330), (420, 230), (300, 150)]
    poli(d, cara, piel)
    # sombra plana en un lado
    poli(d, [(180, 230), (178, 330), (192, 400), (226, 458), (272, 500), (300, 510), (258, 440), (230, 360), (230, 250)], piel_s, 0, None)
    if viejo:
        for y in (300, 312):
            d.line(S(250, y, 350, y), fill=piel_s, width=3 * SS)
        d.arc(S(222, 420, 262, 470), 200, 300, fill=piel_s, width=4 * SS); d.arc(S(338, 420, 378, 470), 240, 340, fill=piel_s, width=4 * SS)
    # ---- ojos, cejas, nariz, boca
    ey = 360
    for lado, ex in ((-1, 245), (1, 355)):
        ojo(d, ex, ey, lado, expr, cerrado, viejo=viejo)
        ceja(d, ex, ey - 70, lado, expr, P["pelo"])
    if P.get("gafas"):
        for ex in (245, 355):
            d.rounded_rectangle(S(ex - 52, ey - 46, ex + 52, ey + 52), radius=20 * SS, outline=(60, 50, 50), width=6 * SS)
            d.line(S(ex - 30, ey - 30, ex - 10, ey - 40), fill=(255, 255, 255), width=5 * SS)
        d.line(S(297, ey - 10, 303, ey - 10), fill=(60, 50, 50), width=6 * SS)
    d.line(S(306, 410, 300, 432, 312, 434), fill=piel_s, width=5 * SS)
    tipo_boca = {"feliz": "sonrisa", "sonrisa": "sonrisa", "triste": "triste", "sorpresa": "sorpresa", "enfado": "grito", "decidido": "serio"}.get(expr, "serio")
    boca(d, 300, 466, tipo_boca, boca_abierta)
    if expr in ("feliz", "sonrisa", "sorpresa"):
        for x in (220, 380):
            for k in range(3):
                d.line(S(x - 20 + k * 14, 412, x - 28 + k * 14, 426), fill=(240, 120, 130), width=4 * SS)
    # ---- pelo
    pc, pb = P["pelo"], P["brillo"]
    if "gorra" in P:
        # patillas y flequillo bajo la visera
        for lado in (-1, 1):
            x0 = 300 + lado * 120
            poli(d, [(x0, 230), (x0 + lado * 2, 330), (x0 - lado * 14, 300), (x0 - lado * 26, 330), (x0 - lado * 30, 240)], pc, 5)
        flequillo = [(190, 250), (220, 300), (240, 262), (268, 312), (292, 264), (322, 308), (346, 262), (372, 300), (392, 258), (410, 250)]
        poli(d, flequillo + [(410, 230), (190, 230)], pc, 5)
        # gorra militar de campaña
        poli(d, [(170, 245), (175, 150), (215, 105), (300, 88), (385, 105), (425, 150), (430, 245)], P["gorra"])
        poli(d, [(175, 150), (215, 105), (300, 88), (250, 120), (230, 245), (170, 245)], tuple(int(v * 0.8) for v in P["gorra"]), 0, None)
        d.line(S(172, 215, 428, 215), fill=LIN, width=5 * SS)
        poli(d, [(190, 238), (410, 238), (440, 262), (300, 276), (160, 262)], (60, 50, 30))
        sx, sy = 300, 170
        pts = []
        for k in range(10):
            r = 22 if k % 2 == 0 else 9
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((sx + math.cos(a) * r, sy + math.sin(a) * r))
        poli(d, pts, (250, 210, 70), 3)
        if P.get("sucio"):
            d.line(S(380, 120, 400, 180), fill=LIN, width=4 * SS); d.line(S(200, 150, 225, 140), fill=LIN, width=4 * SS)
    else:
        largo = P.get("largo")
        puntas = [(176, 240), (196, 300), (214, 250), (248, 292), (270, 244), (300, 284), (326, 242), (356, 290), (378, 246), (404, 300), (424, 240), (430, 160), (380, 96), (300, 82), (220, 96), (170, 160)]
        poli(d, puntas, pc, 5)
        for x0 in (140, 440):   # mechones laterales
            s = -1 if x0 < 300 else 1
            poli(d, [(x0 - s * 10, 160), (x0 + s * 30, 280), (x0 + s * 6, 260), (x0 + s * 20, 380 if largo else 330), (x0 - s * 20, 240)], pc, 5)
        # brillo del pelo (banda en forma de arco)
        d.arc(S(210, 110, 390, 230), 200, 340, fill=pb, width=14 * SS)
    if lagrima:
        poli(d, [(212, 410), (222, 440), (214, 470), (204, 440)], (150, 210, 255), 3)
    if sudor:
        poli(d, [(440, 220), (456, 260), (440, 276), (426, 258)], (170, 220, 255), 3)
    A[clave] = reducir(im)
    return A[clave]


def silueta(arma=True, k=1.0, col=(16, 12, 24)):
    """Soldado en silueta (pose a contraluz)."""
    clave = ("SIL", arma, k, col)
    if clave in A:
        return A[clave]
    im, d = lienzo(240, 520)
    d.ellipse(S(90, 30, 150, 96), fill=col)
    d.chord(S(80, 18, 160, 80), 180, 360, fill=col); d.rectangle(S(76, 46, 164, 56), fill=col)
    d.polygon(S(70, 110, 170, 110, 180, 290, 60, 290), fill=col)
    d.line(S(80, 280, 70, 500), fill=col, width=38 * SS); d.line(S(160, 280, 175, 500), fill=col, width=38 * SS)
    d.line(S(70, 120, 40, 260), fill=col, width=30 * SS); d.line(S(170, 120, 190, 250), fill=col, width=30 * SS)
    if arma:
        d.line(S(200, 30, 186, 300), fill=col, width=12 * SS)
    im = reducir(im)
    if k != 1:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    A[clave] = im
    return im


# ------------------------------------------------------------- objetos
def katana(largo=760):
    clave = ("KATANA", largo)
    if clave in A:
        return A[clave]
    im, d = lienzo(largo, 120)
    hoja = curva((180, 60), (largo * 0.6, 40), (largo - 10, 30), 20)
    pts = hoja + [(x, y + 26 - 20 * i / len(hoja)) for i, (x, y) in enumerate(hoja)][::-1]
    poli(d, pts, (220, 228, 240), 4)
    d.line([(x * SS, (y + 6) * SS) for x, y in hoja[:-2]], fill=(255, 255, 255), width=4 * SS)
    d.ellipse(S(150, 30, 190, 96), fill=(190, 160, 70), outline=LIN, width=4 * SS)
    d.rounded_rectangle(S(10, 50, 160, 80), radius=10 * SS, fill=(40, 30, 50), outline=LIN, width=4 * SS)
    for x in range(26, 150, 26):
        d.line(S(x, 50, x + 14, 80), fill=(200, 190, 210), width=4 * SS)
    A[clave] = reducir(im)
    return A[clave]


def panda():
    if "PANDA" in A:
        return A["PANDA"]
    im, d = lienzo(400, 400)
    for x in (110, 290):
        d.ellipse(S(x - 50, 40, x + 50, 140), fill=(30, 30, 36), outline=LIN, width=6 * SS)
    d.ellipse(S(60, 70, 340, 350), fill=(250, 250, 250), outline=LIN, width=7 * SS)
    for x, a in ((150, 20), (250, -20)):
        d.ellipse(S(x - 40, 160, x + 40, 250), fill=(30, 30, 36))
        d.ellipse(S(x - 12, 190, x + 12, 214), fill=(255, 255, 255))
    d.ellipse(S(180, 250, 220, 280), fill=(30, 30, 36))
    d.arc(S(170, 260, 230, 310), 20, 160, fill=LIN, width=5 * SS)
    for x in (110, 290):
        d.line(S(x - 10, 262, x + 20, 268), fill=(255, 150, 170), width=5 * SS)
    A["PANDA"] = reducir(im)
    return A["PANDA"]


def yeti():
    if "YETI" in A:
        return A["YETI"]
    im, d = lienzo(400, 460)
    pts = []
    for k in range(28):
        a = k / 28 * 2 * math.pi
        r = 170 + (22 if k % 2 else 0)
        pts.append((200 + math.cos(a) * r * 0.95, 240 + math.sin(a) * r * 1.15))
    poli(d, pts, (236, 240, 252), 6)
    d.ellipse(S(110, 120, 290, 290), fill=(150, 180, 220), outline=LIN, width=5 * SS)
    for x in (165, 235):
        d.ellipse(S(x - 22, 170, x + 22, 214), fill=(255, 255, 255), outline=LIN, width=4 * SS)
        d.ellipse(S(x - 9, 184, x + 9, 206), fill=LIN)
    d.chord(S(160, 222, 240, 280), 0, 180, fill=(90, 40, 60), outline=LIN, width=4 * SS)
    for x in (185, 215):
        d.polygon(S(x - 8, 226, x + 8, 226, x, 244), fill=(255, 255, 255))
    A["YETI"] = reducir(im)
    return A["YETI"]


def folleto():
    if "FOLLETO" in A:
        return A["FOLLETO"]
    im, d = lienzo(150, 200)
    d.rectangle(S(0, 0, 149, 199), fill=(250, 246, 230), outline=LIN, width=4 * SS)
    d.rectangle(S(14, 16, 136, 46), fill=(200, 50, 50))
    for y in range(64, 190, 22):
        d.line(S(16, y, 134, y), fill=(140, 130, 120), width=6 * SS)
    A["FOLLETO"] = reducir(im)
    return A["FOLLETO"]


# ------------------------------------------------------------- fondos pintados
def _grad(c1, c2, w=W, h=H):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(c1)[None, None, :] * (1 - a) + np.array(c2)[None, None, :] * a)
    arr = np.repeat(arr, w, 1).astype(np.uint8)
    return Image.fromarray(np.dstack([arr, np.full((h, w), 255, np.uint8)]), "RGBA")


def nube_anime(d, x, y, r, luz=(255, 255, 255), sombra=(196, 214, 240)):
    bolas = [(-1.4, 0.2, 0.7), (-0.7, -0.3, 0.95), (0.2, -0.55, 1.15), (1.1, -0.2, 0.9), (1.8, 0.25, 0.65)]
    for bx, by, br in bolas:
        d.ellipse((x + (bx * r - br * r), y + (by * r - br * r) + r * 0.25, x + bx * r + br * r, y + by * r + br * r + r * 0.25), fill=sombra)
    for bx, by, br in bolas:
        d.ellipse((x + (bx * r - br * r), y + (by * r - br * r), x + bx * r + br * r, y + by * r + br * r - r * 0.1), fill=luz)
    d.rectangle((x - 2.1 * r, y + r * 0.2, x + 2.5 * r, y + r * 0.85), fill=sombra)


def fondo_cielo():
    im = _grad((40, 110, 220), (170, 220, 255))
    d = ImageDraw.Draw(im)
    for x, y, r in ((220, 1050, 150), (820, 900, 120), (520, 1250, 190), (900, 1300, 130), (150, 600, 70), (760, 450, 60)):
        nube_anime(d, x, y, r)
    return im


def fondo_atardecer():
    im = _grad((70, 40, 120), (255, 150, 90))
    d = ImageDraw.Draw(im)
    d.ellipse((W / 2 - 230, 760, W / 2 + 230, 1220), fill=(255, 230, 150))
    for k in range(5):
        y = 900 + k * 60
        d.rectangle((0, y, W, y + 10 + k * 2), fill=(255, 150, 110, 120))
    selva_capa(d, 1180, (40, 20, 50), 3)
    return im


def palmera(d, x, y, alto, col, ang=0):
    tx, ty = x + math.sin(math.radians(ang)) * alto, y - alto
    d.line([(x, y), ((x + tx) / 2 + 20, (y + ty) / 2), (tx, ty)], fill=col, width=int(alto * 0.07), joint="curve")
    for k in range(7):
        a = math.radians(-170 + k * 28)
        L = alto * 0.55
        pts = [(tx, ty)]
        for i in range(1, 9):
            u = i / 8
            pts.append((tx + math.cos(a) * L * u, ty + math.sin(a) * L * u + (u ** 2) * L * 0.45))
        d.line(pts, fill=col, width=int(alto * 0.05), joint="curve")
        for i in range(2, 9):
            px, py = pts[i]
            d.polygon([(px, py), (px + math.cos(a + 1.3) * 34, py + 34), (px + math.cos(a - 1.3) * 34, py + 34)], fill=col)


def selva_capa(d, y0, col, semilla, densidad=9):
    rng = np.random.default_rng(semilla)
    pts = [(0, H)]
    for x in range(0, W + 60, 60):
        pts.append((x, y0 + rng.uniform(-80, 40)))
    pts.append((W, H))
    d.polygon(pts, fill=col)
    for k in range(densidad):
        palmera(d, rng.uniform(0, W), y0 + 60, rng.uniform(280, 520), col, rng.uniform(-14, 14))


def fondo_selva(noche=False):
    if noche:
        im = _grad((8, 14, 36), (20, 40, 60))
    else:
        im = _grad((120, 200, 170), (40, 110, 80))
    d = ImageDraw.Draw(im)
    capas = [(560, (70, 150, 110)), (820, (40, 110, 80)), (1100, (20, 70, 50))] if not noche else \
            [(560, (20, 40, 60)), (820, (14, 30, 46)), (1100, (8, 18, 30))]
    for i, (y, c) in enumerate(capas):
        selva_capa(d, y, c, i + 3)
    if not noche:   # rayos de luz
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(capa)
        for k in range(5):
            x = 140 + k * 220
            cd.polygon([(x, 0), (x + 90, 0), (x + 380, H), (x + 200, H)], fill=(255, 255, 210, 34))
        im.alpha_composite(capa.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(1)
    for k in range(5):   # hojas grandes en primer plano
        x = rng.choice([-60, W + 60]) + rng.uniform(-40, 40)
        y = rng.uniform(200, 1500)
        col = (10, 40, 30) if not noche else (4, 10, 16)
        lado = 1 if x < W / 2 else -1
        for j in range(6):
            a = math.radians(-40 + j * 16) if lado > 0 else math.radians(180 + 40 - j * 16)
            L = 260 + j * 20
            d.polygon([(x, y), (x + math.cos(a - 0.12) * L, y + math.sin(a - 0.12) * L), (x + math.cos(a) * (L + 60), y + math.sin(a) * (L + 60)),
                       (x + math.cos(a + 0.12) * L, y + math.sin(a + 0.12) * L)], fill=col)
    return im


def fondo_rojo():
    im = _grad((200, 30, 50), (60, 0, 20))
    return im


def fondo_noche_lluvia():
    return fondo_selva(noche=True)


def fondo_libreria():
    im = _grad((120, 80, 50), (60, 36, 24))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    for y in range(260, 1400, 230):
        d.rectangle((0, y + 190, W, y + 214), fill=(70, 44, 28))
        x = 20
        while x < W - 20:
            w = int(rng.integers(28, 60)); h = int(rng.integers(130, 186))
            col = tuple(int(v) for v in rng.integers(60, 220, 3))
            d.rectangle((x, y + 190 - h, x + w, y + 190), fill=col, outline=LIN, width=3)
            x += w + 4
    capa = Image.new("RGBA", (W, H), (30, 16, 10, 110))
    im.alpha_composite(capa)
    return im


FONDOS = dict(cielo=fondo_cielo, atardecer=fondo_atardecer, selva=fondo_selva, noche=fondo_noche_lluvia, rojo=fondo_rojo, libreria=fondo_libreria)


def fondo(nombre):
    k = "AF_" + nombre
    if k not in A:
        A[k] = FONDOS[nombre]()
    return A[k]


# ------------------------------------------------------------- efectos anime
def lineas_foco(fr, tl, col=(255, 255, 255), cx=W / 2, cy=800, r0=360, n=90, alfa=200):
    """Líneas de concentración que parpadean (se regeneran 12 veces por segundo)."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    rng = np.random.default_rng(int(tl * 12))
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r1 = r0 + rng.uniform(0, 260)
        w = rng.uniform(0.004, 0.018)
        p0 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        d.polygon([p0, (cx + math.cos(a - w) * 1700, cy + math.sin(a - w) * 1700), (cx + math.cos(a + w) * 1700, cy + math.sin(a + w) * 1700)],
                  fill=col + (alfa,))
    fr.alpha_composite(capa)


def lineas_velocidad(fr, tl, col=(255, 255, 255), alfa=170, n=40):
    """Líneas horizontales de velocidad."""
    d = ImageDraw.Draw(fr)
    rng = np.random.default_rng(int(tl * 15) + 99)
    for _ in range(n):
        y = rng.uniform(0, H)
        x = rng.uniform(-200, W)
        L = rng.uniform(200, 700)
        d.line((x, y, x + L, y), fill=col + (alfa,), width=int(rng.integers(2, 7)))


def impacto(fr, col1=(0, 0, 0), col2=(255, 255, 255), umbral=110):
    """Fotograma de impacto: la imagen se convierte en dos tonos (como en los momentos clave del anime)."""
    arr = np.asarray(fr.convert("L"))
    m = arr > umbral
    out = np.where(m[..., None], np.array(col2, np.uint8), np.array(col1, np.uint8))
    fr.paste(Image.fromarray(np.dstack([out, np.full(arr.shape, 255, np.uint8)]), "RGBA"))


def petalos(fr, tl, n=26, col=(255, 190, 210), semilla=3):
    d = ImageDraw.Draw(fr)
    rng = np.random.default_rng(semilla)
    for i in range(n):
        x0, v, f = rng.uniform(-100, W), rng.uniform(80, 200), rng.uniform(1, 3)
        x = (x0 + tl * v * 0.8 + 60 * math.sin(tl * f + i)) % (W + 100) - 50
        y = (rng.uniform(0, H) + tl * v) % H
        a = tl * f * 2 + i
        r = 16
        pts = [(x + math.cos(a) * r, y + math.sin(a) * r * 0.5), (x + math.cos(a + 1.6) * r * 0.4, y + math.sin(a + 1.6) * r * 0.4),
               (x - math.cos(a) * r, y - math.sin(a) * r * 0.5), (x - math.cos(a + 1.6) * r * 0.4, y - math.sin(a + 1.6) * r * 0.4)]
        d.polygon(pts, fill=col + (230,))


def lluvia(fr, tl, n=140):
    d = ImageDraw.Draw(fr)
    rng = np.random.default_rng(int(tl * 20))
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        d.line((x, y, x - 18, y + 70), fill=(180, 200, 255, 140), width=3)


def trama(fr, alfa=60, paso=18, col=(0, 0, 0)):
    """Trama de puntos (screentone) sobre toda la escena."""
    k = ("TRAMA", alfa, paso, col)
    if k not in A:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for y in range(0, H, paso):
            for x in range((y // paso % 2) * paso // 2, W, paso):
                d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=col + (alfa,))
        A[k] = im
    fr.alpha_composite(A[k])


def cartel_nombre(fr, nombre, sub, tl, col=(255, 70, 110), y=1210):
    """Banda diagonal con el nombre del personaje que entra deslizándose."""
    u = min(1, max(0, tl / 0.35)) ** 0.5
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    off = (1 - u) * -W
    d.polygon([(off, y - 70), (off + W * 0.92, y - 110), (off + W * 0.92, y + 40), (off, y + 80)], fill=col + (235,))
    d.polygon([(off, y + 80), (off + W * 0.92, y + 40), (off + W * 0.92, y + 62), (off, y + 104)], fill=(20, 16, 28, 235))
    fr.alpha_composite(capa)
    from historia import texto_grande, pegar
    if u > 0.6:
        pegar(fr, texto_grande(nombre, (255, 255, 255), 96), W / 2 - 30, y - 22)
        pegar(fr, texto_grande(sub, (255, 230, 120), 52), W / 2 - 40, y + 76)
