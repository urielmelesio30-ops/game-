# -*- coding: utf-8 -*-
"""Render en PIXEL ART vertical (TikTok).

Todo se dibuja a 360x640 con primitivas sin suavizado y fuentes de píxel, y se
escala x3 (vecino más cercano) a 1080x1920, así cada "píxel" es un bloque 3x3.

Uso:
  python3 render.py                 # los 10 vídeos
  python3 render.py 01 05           # solo esos
  PREVIEW=1 python3 render.py 01    # sale a 360x640, rápido, para revisar
"""
import math, os, re, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import audio
from guiones import VIDEOS, CANAL, LEMA, AVISO

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SALIDA = os.path.join(RAIZ, "salida")
FUENTES = os.path.join(RAIZ, "fuentes")
PREVIEW = os.environ.get("PREVIEW") == "1"
BW, BH = 360, 640                 # lienzo de píxeles
ESC = 1 if PREVIEW else 3         # escala de salida
W, H = BW * ESC, BH * ESC
FPS = 30
MG = 40                           # margen del fondo para el paneo

# Zonas seguras de TikTok (en píxeles del lienzo)
X0, X1 = 22, 312
ANCHO = X1 - X0
Y_TOP = 62
Y_FIN = 440
Y_SUBT = 494

# ------------------------------------------------------------- paleta
P = dict(
    negro=(12, 8, 22), noche=(24, 15, 46), morado=(56, 28, 92), uva=(92, 36, 120), magenta=(158, 44, 124),
    rosa=(255, 88, 164), coral=(255, 122, 108), naranja=(255, 164, 72), amarillo=(255, 226, 96),
    crema=(255, 242, 206), cian=(70, 222, 255), azul=(46, 78, 168), marino=(20, 30, 80),
    verde=(90, 232, 146), pino=(22, 92, 74), rojo=(232, 54, 74), blanco=(246, 244, 252),
    gris=(160, 150, 182), plomo=(76, 66, 102), caja=(18, 12, 34),
)
TEMAS = {
    "rosa":    dict(cielo=["noche", "morado", "magenta", "coral", "naranja"], a="rosa", b="amarillo"),
    "cian":    dict(cielo=["negro", "marino", "azul", "uva", "magenta"], a="cian", b="rosa"),
    "dorado":  dict(cielo=["noche", "uva", "coral", "naranja", "amarillo"], a="amarillo", b="coral"),
    "verde":   dict(cielo=["negro", "marino", "pino", "azul", "cian"], a="verde", b="cian"),
    "rojo":    dict(cielo=["negro", "noche", "uva", "rojo", "naranja"], a="rojo", b="amarillo"),
    "morado":  dict(cielo=["negro", "noche", "morado", "magenta", "rosa"], a="rosa", b="cian"),
    "naranja": dict(cielo=["noche", "magenta", "coral", "naranja", "amarillo"], a="naranja", b="cian"),
}


def col(nombre_o_rgb):
    return P[nombre_o_rgb] if isinstance(nombre_o_rgb, str) else nombre_o_rgb


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
_b8 = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64.0
BAYER_PANT = np.tile(_b8, (BH // 8, BW // 8))

# ------------------------------------------------------------- tipografía
_f = {}


def fuente(tipo, tam):
    k = (tipo, tam)
    if k not in _f:
        nombre = {"pixel": "PressStart2P-Regular.ttf", "texto": "Jersey10-Regular.ttf"}[tipo]
        _f[k] = ImageFont.truetype(os.path.join(FUENTES, nombre), tam)
    return _f[k]


def ancho_txt(txt, f):
    return int(math.ceil(f.getlength(txt)))


def envolver(txt, f, ancho):
    lineas, act = [], ""
    for p in txt.split():
        prueba = (act + " " + p).strip()
        if ancho_txt(prueba, f) <= ancho or not act:
            act = prueba
        else:
            lineas.append(act); act = p
    if act:
        lineas.append(act)
    return lineas


def txt_img(txt, f, color="blanco", sombra="negro", contorno=False):
    """Texto sin suavizado con sombra o contorno de 1 píxel.
    La caja vertical es fija por fuente, así las palabras con tilde no se descuadran."""
    if f.path.endswith("PressStart2P-Regular.ttf"):
        txt = txt.replace("Í", "I")  # la Í de esta fuente parece minúscula
    l, _, r, _ = f.getbbox(txt)
    _, t, _, b = f.getbbox("ÁÉÑjgpq|")
    w, h = r - l + 4, b - t + 4
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    o = (1 - l, 1 - t)
    if contorno:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    d.text((o[0] + dx, o[1] + dy), txt, font=f, fill=col(sombra) + (255,))
    elif sombra:
        d.text((o[0] + 1, o[1] + 1), txt, font=f, fill=col(sombra) + (255,))
    d.text(o, txt, font=f, fill=col(color) + (255,))
    return im


def caja(w, h, borde="blanco", relleno="caja", sombra=True):
    """Caja estilo RPG: contorno negro, borde de color, esquinas recortadas."""
    w, h = int(w), int(h)
    im = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if sombra:
        d.rectangle((2, 2, w + 1, h + 1), fill=col("negro") + (255,))
    d.rectangle((0, 0, w - 1, h - 1), fill=col("negro") + (255,))
    if borde:
        d.rectangle((1, 1, w - 2, h - 2), fill=col(borde) + (255,))
    d.rectangle((2, 2, w - 3, h - 3), fill=col(relleno) + (255,))
    for (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        im.putpixel((x, y), (0, 0, 0, 0))
    return im


def icono(tipo, color):
    c = col(color) + (255,)
    if tipo == "check":
        m = ["......#", ".....##", "#...##.", "##.##..", ".###...", "..#...."]
    elif tipo == "flecha":
        m = ["#...", "##..", "###.", "####", "###.", "##..", "#..."]
    elif tipo == "aviso":
        m = ["......##......", ".....####.....", ".....#..#.....", "....##..##....", "....#.##.#....",
             "...##.##.##...", "...#..##..#...", "..##..##..##..", "..#........#..", ".##...##...##.",
             ".#....##....#.", "##..........##", "##############"]
    elif tipo == "corazon":
        m = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
    else:
        m = ["#"]
    im = Image.new("RGBA", (len(m[0]), len(m)), (0, 0, 0, 0))
    for y, fila in enumerate(m):
        for x, ch in enumerate(fila):
            if ch == "#":
                im.putpixel((x, y), c)
    return im


# ------------------------------------------------------------- fondos
def dither_vertical(w, h, paradas):
    cs = np.array([col(c) for c in paradas], float)
    y = np.linspace(0, len(cs) - 1 - 1e-6, h)[:, None]
    i = np.floor(y).astype(int)
    frac = y - i
    umbral = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    usar_sig = umbral < frac
    idx = np.where(usar_sig, i + 1, i)
    return cs[idx].astype(np.uint8)


def palmera(d, x, base, alto, color, fase=0.0):
    pts = []
    for i in range(alto // 4 + 1):
        u = i / (alto // 4)
        pts.append((x + int(math.sin(u * 1.5) * alto * 0.12), base - int(u * alto)))
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=color, width=4 if i < len(pts) // 2 else 3)
    cx, cy = pts[-1]
    for k, ang in enumerate([200, 235, 270, 305, 340, 10, 150]):
        a = math.radians(ang)
        largo = alto * 0.42
        prev = (cx, cy)
        for j in range(1, 9):
            u = j / 8
            sway = math.sin(fase + k) * 2 * u
            px = cx + math.cos(a) * largo * u + sway
            py = cy + math.sin(a) * largo * u * 0.5 + (u ** 2) * largo * 0.45
            d.line([prev, (int(px), int(py))], fill=color, width=3 if j < 5 else 2)
            prev = (int(px), int(py))


class Fondo:
    def __init__(self, tipo, tema, semilla):
        self.tipo, self.tema = tipo, TEMAS[tema]
        self.rng = np.random.default_rng(semilla)
        self.w = BW + 2 * MG
        self.hor = int(BH * 0.66)
        self.base = self._estatico()
        r = self.rng
        self.nubes = [(r.integers(0, self.w), r.integers(40, self.hor - 140), r.integers(18, 40), r.random() * 0.6 + 0.3) for _ in range(5)]
        self.estrellas = [(r.integers(0, self.w), r.integers(0, self.hor - 60), r.random() * 6.28) for _ in range(90)]
        self.coches = [(r.random(), r.integers(0, 2), r.choice(["rosa", "cian", "amarillo", "blanco", "verde"])) for _ in range(7)]

    def _estatico(self):
        w, h, hor = self.w, BH, self.hor
        img = np.zeros((h, w, 3), np.uint8)
        img[:hor] = dither_vertical(w, hor, self.tema["cielo"])
        if self.tipo == "noche":
            img[hor:] = dither_vertical(w, h - hor, ["noche", "negro"])
        elif self.tipo == "oceano":
            img[hor:] = dither_vertical(w, h - hor, ["uva", "marino", "noche", "negro"])
        else:
            img[hor:] = dither_vertical(w, h - hor, ["noche", "negro", "negro"])
        im = Image.fromarray(img)
        d = ImageDraw.Draw(im)
        cx = w // 2
        if self.tipo in ("atardecer", "oceano"):
            r = 62
            cy = hor - 16
            sol = dither_vertical(2 * r, 2 * r, ["amarillo", "naranja", col(self.tema["a"])])
            m = Image.new("L", (2 * r, 2 * r), 0)
            md = ImageDraw.Draw(m)
            md.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
            for k in range(6):
                y0 = r + 6 + k * 9
                md.rectangle((0, y0, 2 * r, y0 + 1 + k // 2), fill=0)
            md.rectangle((0, hor - (cy - r), 2 * r, 2 * r), fill=0)
            im.paste(Image.fromarray(sol), (cx - r, cy - r), m)
            # montañas escalonadas
            pts = [(0, hor)]
            for x in range(0, w + 8, 8):
                pts.append((x, hor - int(14 + 12 * math.sin(x / 37.0) + 7 * math.sin(x / 13.0))))
            pts.append((w, hor))
            d.polygon(pts, fill=col("morado"))
            d.line([(0, hor), (w, hor)], fill=col(self.tema["a"]))
        else:
            # luna y ciudad
            d.ellipse((w - 120, 60, w - 92, 88), fill=col("crema"))
            d.point([(w - 110, 70), (w - 104, 78), (w - 101, 69)], fill=col("gris"))
            for capa, (c, hmin, hmax) in enumerate([("uva", 40, 120), ("noche", 28, 92)]):
                x = 0
                while x < w:
                    bw_ = int(self.rng.integers(14, 34))
                    alt = int(self.rng.integers(hmin, hmax))
                    d.rectangle((x, hor - alt, x + bw_, hor), fill=col(c))
                    if capa == 0 and self.rng.random() < 0.3:
                        d.line([(x + bw_ // 2, hor - alt - 8), (x + bw_ // 2, hor - alt)], fill=col(c))
                    if capa == 1:
                        for wy in range(hor - alt + 4, hor - 3, 5):
                            for wx in range(x + 3, x + bw_ - 2, 4):
                                if self.rng.random() < 0.33:
                                    cc = "amarillo" if self.rng.random() < 0.75 else self.tema["b"]
                                    d.rectangle((wx, wy, wx + 1, wy + 1), fill=col(cc))
                    x += bw_ + int(self.rng.integers(0, 4))
            d.rectangle((0, hor + 20, w, hor + 46), fill=col("caja"))
            for x in range(0, w, 16):
                d.line([(x, hor + 33), (x + 7, hor + 33)], fill=col("gris"))
        return im

    def frame(self, t, off):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        w, hor = self.w, self.hor
        a = col(self.tema["a"])
        if self.tipo == "atardecer":
            vx = w // 2
            for i in range(-14, 15):
                d.line([(vx + i * 6, hor), (vx + i * 44, BH)], fill=a)
            for j in range(10):
                z = ((j + (t * 1.2) % 1.0) / 10)
                y = hor + int((BH - hor) * z ** 2.1)
                d.line([(0, y), (w, y)], fill=a)
        elif self.tipo == "oceano":
            for j in range(26):
                z = j / 26
                y = hor + 3 + int((BH - hor - 3) * z ** 1.7)
                fase = math.sin(t * 3 + j * 1.7)
                anch = int((10 + 70 * (1 - z * 0.3)) * (0.6 + 0.4 * fase))
                c = "crema" if j % 3 else self.tema["a"]
                if z < 0.7:
                    d.line([(w // 2 - anch, y), (w // 2 + anch, y)], fill=col(c))
                xs = int((j * 53 + t * 8) % w)
                d.line([(xs, y), (xs + 5, y)], fill=col("azul"))
        else:
            for (x, y, f) in self.estrellas:
                if math.sin(t * 2.2 + f) > -0.3:
                    d.point((int(x), int(y)), fill=col("blanco"))
                if math.sin(t * 1.3 + f) > 0.92:
                    d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=col("cian"))
            for (u, carril, c) in self.coches:
                v = 45 if carril == 0 else -60
                x = int((u * w + t * v) % (w + 40)) - 20
                y = hor + (24 if carril == 0 else 37)
                d.rectangle((x, y, x + 13, y + 4), fill=col(c))
                d.rectangle((x + 3, y - 2, x + 9, y), fill=col(c))
                d.point((x + 13 if carril == 0 else x, y + 2), fill=col("amarillo" if carril == 0 else "rojo"))
            for j in range(6):
                z = ((j + (t * 0.8) % 1.0) / 6)
                y = hor + 50 + int((BH - hor - 50) * z ** 2)
                d.line([(0, y), (w, y)], fill=col("uva"))
        # nubes de píxel
        for (x, y, r, vel) in self.nubes:
            xx = int((x + t * vel * 6) % (w + 80)) - 40
            cn = col("magenta") if self.tipo != "noche" else col("uva")
            d.rectangle((xx, y, xx + r * 2, y + 5), fill=cn)
            d.rectangle((xx + r // 2, y - 4, xx + r + r // 2, y), fill=cn)
        if self.tipo in ("atardecer", "oceano"):
            sil = col("negro")
            palmera(d, 30, BH + 4, 250, sil, t * 1.3)
            palmera(d, 92, BH + 4, 170, sil, t * 1.3 + 1)
            palmera(d, w - 40, BH + 4, 270, sil, t * 1.3 + 2)
            palmera(d, w - 104, BH + 4, 160, sil, t * 1.3 + 3)
        return im.crop((off, 0, off + BW, BH))


# ------------------------------------------------------------- animación
class Sprite:
    """Elemento que aparece en t0 (con deslizamiento en pasos de píxel) y desaparece en t1."""

    def __init__(self, img, x, y, t0=0.0, t1=None, anim="izq", dur=0.22, parpadeo=False):
        self.img, self.x, self.y = img, int(x), int(y)
        self.t0, self.t1, self.anim, self.dur, self.parpadeo = t0, t1, anim, dur, parpadeo

    def pintar(self, frame, t, fin):
        t1 = self.t1 if self.t1 is not None else fin
        if t < self.t0 or t >= t1:
            return
        if self.parpadeo and int(t * 3) % 2:
            return
        u = min(1.0, (t - self.t0) / self.dur)
        u = math.floor(u * 4) / 4  # movimiento a saltos, como en consola
        x, y = self.x, self.y
        if self.anim == "izq":
            x -= int((1 - u) * 24)
        elif self.anim == "der":
            x += int((1 - u) * 24)
        elif self.anim == "arriba":
            y += int((1 - u) * 12)
        elif self.anim == "caer":
            y -= int((1 - u) * 12)
        frame.alpha_composite(self.img, (x, y))


def cabecera(sp, txt, tema, y=None):
    y = Y_TOP if y is None else y
    f = fuente("pixel", 16)
    for i, ln in enumerate(envolver(txt, f, ANCHO)):
        sp.append(Sprite(txt_img(ln, f, "blanco", tema["a"]), X0, y, 0.05 + 0.08 * i, anim="izq"))
        y += 22
    barra = Image.new("RGBA", (48, 3), col(tema["a"]) + (255,))
    sp.append(Sprite(barra, X0, y + 2, 0.15, anim="izq"))
    return y + 16


def centrar(img):
    return X0 + (ANCHO - img.width) // 2


def construir_escena(esc, tema_nombre, tiempos, dur):
    """Devuelve (sprites, dinámicos, efectos) de una escena.
    efectos: lista de (tiempo_relativo, tipo_blip)."""
    tema = TEMAS[tema_nombre]
    A, B = tema["a"], tema["b"]
    sp, dyn, sfx = [], [], []
    tipo = esc["t"]
    ft = fuente("texto", 20)
    fg = fuente("texto", 30)

    def t_item(k, n):
        return tiempos[max(0, len(tiempos) - n + k)]

    def t_fin(k, n):
        i = len(tiempos) - n + k + 1
        return tiempos[i] if i < len(tiempos) else dur

    def fila(y, alto, t0, t1, borde_activo=A):
        sp.append(Sprite(caja(ANCHO, alto, borde="plomo"), X0, y, t0, anim="izq"))
        sp.append(Sprite(caja(ANCHO, alto, borde=borde_activo), X0, y, t0, t1, anim="izq"))
        fl = icono("flecha", "amarillo").resize((6, 10), Image.NEAREST)
        sp.append(Sprite(fl, X0 - 10, y + alto // 2 - 5, t0, t1, anim="izq", parpadeo=True))
        sfx.append((t0, 0))

    if tipo == "title":
        f = fuente("pixel", 24)
        lineas = envolver(esc["head"], f, ANCHO)
        y = 120
        for i, ln in enumerate(lineas):
            im = txt_img(ln, f, "blanco", A)
            sp.append(Sprite(im, centrar(im), y, 0.1 + 0.15 * i, anim="caer", dur=0.3))
            sfx.append((0.1 + 0.15 * i, 0))
            y += 32
        y += 8
        for ln in envolver(esc["sub"], ft, ANCHO - 10):
            im = txt_img(ln, ft, B)
            sp.append(Sprite(im, centrar(im), y, 0.6, anim="arriba"))
            y += 22
        flecha = icono("flecha", "amarillo").rotate(-90, expand=True)
        sp.append(Sprite(flecha, X0 + ANCHO // 2 - 3, y + 12, 0.9, anim="arriba", parpadeo=True))

    elif tipo == "card":
        im = txt_img(esc["head"], fuente("pixel", 8), A)
        sp.append(Sprite(im, centrar(im), 120, 0.05, anim="arriba"))
        f = fuente("pixel", 16)
        lineas = envolver(esc["text"], f, ANCHO - 30)
        alto = len(lineas) * 24 + 30
        sp.append(Sprite(caja(ANCHO, alto, borde=A), X0, 136, 0.0, anim="arriba"))
        dyn.append(("maquina", dict(lineas=lineas, x=X0 + 15, y=151, t0=0.3, cps=26, f=f, fin_y=136 + alto - 12)))
        sfx.append((0.0, 0))

    elif tipo in ("bullets", "warning"):
        aviso = tipo == "warning"
        y0 = Y_TOP
        if aviso:
            ic = icono("aviso", "amarillo").resize((28, 26), Image.NEAREST)
            sp.append(Sprite(ic, X0, y0, 0.1, anim="caer", parpadeo=False))
            y0 += 34
        ytop = cabecera(sp, esc["head"], tema, y=y0)
        n = len(esc["items"])
        hueco = min(64, (Y_FIN - ytop) // n)
        for k, it in enumerate(esc["items"]):
            y = ytop + k * hueco
            t0, t1 = t_item(k, n), t_fin(k, n)
            lineas = envolver(it, ft, ANCHO - 20)
            alto = max(36, min(hueco - 8, 16 + 18 * len(lineas)))
            fila(y, alto, t0, t1, "amarillo" if aviso else A)
            yt = y + (alto - 18 * len(lineas)) // 2 - 1
            for j, ln in enumerate(lineas):
                sp.append(Sprite(txt_img(ln, ft, "blanco"), X0 + 10, yt + j * 18, t0, anim="izq"))
                sp.append(Sprite(txt_img(ln, ft, "amarillo"), X0 + 10, yt + j * 18, t0, t1, anim="izq"))

    elif tipo == "stat":
        y = 110
        for ln in envolver(esc["head"], fuente("pixel", 8), ANCHO):
            im = txt_img(ln, fuente("pixel", 8), A)
            sp.append(Sprite(im, centrar(im), y, 0.05, anim="arriba"))
            y += 12
        dyn.append(("stat", dict(valor=esc["value"], t0=0.3, y=160)))
        sfx.append((1.2, 2))
        y = 240
        for ln in envolver(esc["label"], ft, ANCHO - 10):
            im = txt_img(ln, ft, "blanco")
            sp.append(Sprite(im, centrar(im), y, 1.0, anim="arriba"))
            y += 20

    elif tipo == "table":
        ytop = cabecera(sp, esc["head"], tema)
        n = len(esc["rows"])
        hueco = min(64, (Y_FIN - ytop) // n)
        alto = hueco - 6
        for k, (a, b) in enumerate(esc["rows"]):
            y = ytop + k * hueco
            t0, t1 = t_item(k, n), t_fin(k, n)
            fila(y, alto, t0, t1)
            sp.append(Sprite(txt_img(a, ft, "gris"), X0 + 10, y + 5, t0, anim="izq"))
            fv = fg if ancho_txt(b, fg) < ANCHO - 20 else ft
            sp.append(Sprite(txt_img(b, fv, B), X0 + 10, y + alto - (28 if fv is fg else 22), t0, anim="izq"))

    elif tipo == "compare":
        ytop = cabecera(sp, esc["head"], tema)
        n = len(esc["rows"])
        hueco = min(80, (Y_FIN - ytop) // n)
        alto = hueco - 6
        mitad = (ANCHO - 24) // 2
        for k, (feat, l, r) in enumerate(esc["rows"]):
            y = ytop + k * hueco
            t0, t1 = t_item(k, n), t_fin(k, n)
            fila(y, alto, t0, t1)
            sp.append(Sprite(txt_img(feat.upper(), fuente("pixel", 8), A), X0 + 10, y + 7, t0, anim="izq"))
            for c, (et, val) in enumerate(((esc["cols"][0], l), (esc["cols"][1], r))):
                x = X0 + 10 + c * (mitad + 6)
                sp.append(Sprite(txt_img(et, ft, "gris"), x, y + 18, t0, anim="izq"))
                for j, ln in enumerate(envolver(val, ft, mitad - 4)[:2]):
                    sp.append(Sprite(txt_img(ln, ft, "blanco"), x, y + 34 + j * 16, t0, anim="izq"))

    elif tipo == "twocol":
        ytop = cabecera(sp, esc["head"], tema)
        ph = (Y_FIN - ytop - 10) // 2
        colores = [A, B]
        for c in range(2):
            y = ytop + c * (ph + 10)
            sp.append(Sprite(caja(ANCHO, ph, borde=colores[c]), X0, y, 0.1 + 0.15 * c, anim="arriba"))
            sp.append(Sprite(txt_img(esc["cols"][c].upper(), fuente("pixel", 8), colores[c]), X0 + 10, y + 10, 0.2 + 0.15 * c, anim="arriba"))
        cuenta = [0, 0]
        n = len(esc["items"])
        for k, (c, txt) in enumerate(esc["items"]):
            y = ytop + c * (ph + 10) + 30 + cuenta[c] * 26
            cuenta[c] += 1
            t0 = t_item(k, n)
            ic = icono("check", "verde").resize((14, 12), Image.NEAREST) if c == 0 else txt_img("?", fuente("pixel", 8), B)
            sp.append(Sprite(ic, X0 + 10, y + 3, t0, anim="izq"))
            sp.append(Sprite(txt_img(txt, ft, "blanco"), X0 + 30, y, t0, anim="izq"))
            sfx.append((t0, 0))

    elif tipo == "timeline":
        ytop = cabecera(sp, esc["head"], tema)
        pts = esc["points"]
        n = len(pts)
        y0, y1 = ytop + 8, Y_FIN - 10
        paso = min(100, (y1 - y0) // n)
        ys = [y0 + paso * k + 14 for k in range(n)]
        xl = X0 + 6
        ts = [t_item(k, n) for k in range(n)]
        dyn.append(("timeline", dict(x=xl, y0=y0, y1=ys[-1] + paso // 2, ys=ys, ts=ts, color=A)))
        for k, (anio, et) in enumerate(pts):
            fa = fuente("pixel", 24 if len(anio) <= 4 else 16)
            sp.append(Sprite(txt_img(anio, fa, "blanco", A), xl + 18, ys[k] - (12 if len(anio) <= 4 else 8), ts[k], anim="der"))
            for j, ln in enumerate(envolver(et, ft, ANCHO - 40)):
                sp.append(Sprite(txt_img(ln, ft, B), xl + 18, ys[k] + 16 + j * 18, ts[k] + 0.1, anim="der"))
            sfx.append((ts[k], 0))

    elif tipo == "map":
        ytop = cabecera(sp, esc["head"], tema)
        regs = esc["regions"]
        n = len(regs)
        caja_mapa = (X0, ytop, ANCHO, 188)
        pos = {"Mount Kalaga": (0.55, 0.12), "Port Gellhorn": (0.20, 0.24), "Ambrosia": (0.55, 0.42),
               "Grassrivers": (0.43, 0.64), "Vice City": (0.80, 0.66), "Leonida Keys": (0.52, 0.90)}
        Pp = [(X0 + int(pos[r][0] * ANCHO), ytop + int(pos[r][1] * 188)) for r in regs]
        ts = [t_item(k, n) for k in range(n)]
        tf = [t_fin(k, n) for k in range(n)]
        dyn.append(("mapa", dict(caja=caja_mapa, P=Pp, ts=ts, tf=tf, a=A, b=B)))
        nota = txt_img("Esquema orientativo, no es el mapa oficial", fuente("texto", 20), "gris")
        sp.append(Sprite(nota, X0, ytop + 192, 0.4, anim="arriba"))
        yl = ytop + 214
        colw = ANCHO // 2
        fh = min(34, (Y_FIN + 10 - yl) // 3)
        for k, r in enumerate(regs):
            x = X0 + (k % 2) * colw
            y = yl + (k // 2) * fh
            sp.append(Sprite(caja(colw - 4, fh - 4, borde="plomo"), x, y, ts[k], anim="arriba"))
            sp.append(Sprite(caja(colw - 4, fh - 4, borde=A), x, y, ts[k], tf[k], anim="arriba"))
            sp.append(Sprite(txt_img(f"{k + 1} {r}", ft, "blanco"), x + 6, y + (fh - 4) // 2 - 9, ts[k], anim="arriba"))
            sfx.append((ts[k], 0))

    elif tipo == "cta":
        dyn.append(("cta", dict(a=A, b=B)))
        f = fuente("texto", 20)
        for j, ln in enumerate(envolver(f"{CANAL} · {LEMA}" if CANAL else LEMA, f, ANCHO)):
            im = txt_img(ln, f, B)
            sp.append(Sprite(im, centrar(im), 168 + j * 20, 0.4, anim="arriba"))
        for i, et in enumerate(["GUARDA", "COMENTA", "COMPARTE"]):
            w3 = ANCHO // 3
            x = X0 + i * w3
            borde = [A, B, "amarillo"][i]
            sp.append(Sprite(caja(w3 - 6, 30, borde=borde), x, 300, 1.0 + 0.25 * i, anim="caer"))
            im = txt_img(et, f, "blanco")
            sp.append(Sprite(im, x + (w3 - 6 - im.width) // 2, 306, 1.0 + 0.25 * i, anim="caer"))
            sfx.append((1.0 + 0.25 * i, 0))
    return sp, dyn, sfx


def pintar_dinamico(frame, d, items, t, tema_nombre):
    tema = TEMAS[tema_nombre]
    for tipo, p in items:
        if tipo == "maquina":
            n = int(max(0, t - p["t0"]) * p["cps"])
            y = p["y"]
            for ln in p["lineas"]:
                vis = ln[:max(0, n)]
                n -= len(ln)
                if vis:
                    frame.alpha_composite(txt_img(vis, p["f"], "blanco"), (p["x"], y))
                y += 24
            if n > 0 and int(t * 3) % 2 == 0:
                fl = icono("flecha", "amarillo").rotate(-90, expand=True)
                frame.alpha_composite(fl, (X1 - 18, p["fin_y"] - 2))
        elif tipo == "stat":
            u = min(1.0, max(0.0, (t - p["t0"]) / 0.9))
            v = p["valor"]
            m = re.search(r"\d+", v)
            txt = v[:m.start()] + str(int(round(int(m.group()) * u))) + v[m.end():] if m else v
            f = fuente("pixel", 40 if ancho_txt(v, fuente("pixel", 40)) <= ANCHO else 32)
            im = txt_img(txt, f, "amarillo", tema["a"])
            frame.alpha_composite(im, (X0 + (ANCHO - ancho_txt(v, f)) // 2, p["y"]))
            if u >= 1:
                for k in range(6):
                    ang = k * 1.047 + t * 2
                    rr = 18 + (t * 40) % 30
                    cx = X0 + ANCHO // 2 + int(math.cos(ang) * (ancho_txt(v, f) // 2 + rr))
                    cy = p["y"] + 20 + int(math.sin(ang) * rr)
                    d.point([(cx, cy), (cx + 1, cy), (cx, cy + 1)], fill=col("amarillo"))
        elif tipo == "timeline":
            u = min(1.0, max(0.0, (t - 0.1) / max(0.4, p["ts"][-1] + 0.4)))
            y1 = p["y0"] + int((p["y1"] - p["y0"]) * u)
            d.rectangle((p["x"] - 1, p["y0"], p["x"], y1), fill=col("blanco"))
            for y, t0 in zip(p["ys"], p["ts"]):
                if t >= t0:
                    d.rectangle((p["x"] - 4, y - 4, p["x"] + 3, y + 3), fill=col("negro"))
                    d.rectangle((p["x"] - 3, y - 3, p["x"] + 2, y + 2), fill=col(p["color"]))
        elif tipo == "mapa":
            x0, y0, w, h = p["caja"]
            agua = dither_vertical(w - 4, h - 4, ["marino", "azul"])
            frame.paste(Image.fromarray(agua), (x0 + 2, y0 + 2))
            d.rectangle((x0, y0, x0 + w - 1, y0 + h - 1), outline=col(p["a"]))
            pen = [(0.08, 0.05), (0.92, 0.05), (0.90, 0.30), (0.88, 0.55), (0.93, 0.78), (0.80, 0.86), (0.62, 0.82),
                   (0.40, 0.72), (0.30, 0.52), (0.22, 0.34), (0.06, 0.30)]
            d.polygon([(x0 + int(a * w), y0 + int(b * h)) for a, b in pen], fill=col("pino"), outline=col("verde"))
            for i in range(8):
                cx, cy = x0 + int((0.40 + i * 0.05) * w), y0 + int((0.90 + 0.02 * math.sin(i)) * h)
                d.rectangle((cx - 3, cy - 1, cx + 3, cy + 1), fill=col("pino"), outline=col("verde"))
            for k, ((x, y), t0, t1) in enumerate(zip(p["P"], p["ts"], p["tf"])):
                if t < t0:
                    d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=col("gris"))
                    continue
                activo = t0 <= t < t1
                if activo:
                    rr = 6 + int((t - t0) * 16) % 10
                    d.rectangle((x - rr, y - rr, x + rr, y + rr), outline=col(p["a"]))
                c = p["a"] if activo else p["b"]
                d.rectangle((x - 6, y - 6, x + 6, y + 6), fill=col("negro"))
                d.rectangle((x - 5, y - 5, x + 5, y + 5), fill=col(c))
                n = txt_img(str(k + 1), fuente("pixel", 8), "negro", None)
                frame.alpha_composite(n, (x - 4, y - 4))
        elif tipo == "cta":
            f = fuente("pixel", 24)
            c = "blanco" if int(t * 2) % 2 else "amarillo"
            im = txt_img("¡SÍGUEME!", f, c, p["a"])
            frame.alpha_composite(im, (centrar(im), 120))
            # botón que se pulsa cada 1,5 s
            pul = (t % 1.5) < 0.15 and t > 0.8
            bx, by, bw_, bh_ = X0 + 50, 222 + (2 if pul else 0), ANCHO - 100, 40
            if t > 0.6:
                if not pul:
                    d.rectangle((bx + 2, by + 2, bx + bw_ + 1, by + bh_ + 1), fill=col("negro"))
                d.rectangle((bx, by, bx + bw_, by + bh_), fill=col("negro"))
                d.rectangle((bx + 1, by + 1, bx + bw_ - 1, by + bh_ - 1), fill=col("rojo"))
                d.line([(bx + 2, by + 2), (bx + bw_ - 2, by + 2)], fill=col("coral"))
                im = txt_img("+ SEGUIR", fuente("pixel", 16), "blanco")
                frame.alpha_composite(im, (bx + (bw_ - im.width) // 2, by + 12))
                corazon = icono("corazon", "rosa").resize((14, 12), Image.NEAREST)
                if int(t * 2) % 2:
                    frame.alpha_composite(corazon, (bx + bw_ + 10, by + 14))


# ------------------------------------------------------------- subtítulos
def trocear(texto, max_palabras=4, max_chars=24):
    trozos, act = [], []
    for p in texto.split():
        act.append(p)
        if len(act) >= max_palabras or len(" ".join(act)) >= max_chars or p[-1] in ".,:;?!":
            trozos.append(" ".join(act)); act = []
    if act:
        trozos.append(" ".join(act))
    return trozos


def subtitulo_img(txt):
    f = fuente("texto", 30)
    lineas = envolver(txt.upper(), f, ANCHO)
    capas = []
    for ln in lineas:
        # palabra a palabra para pintar las cifras en amarillo
        piezas = [txt_img(p, f, "amarillo" if any(c.isdigit() for c in p) else "blanco", "negro", contorno=True) for p in ln.split()]
        esp = 6
        w = sum(p.width for p in piezas) + esp * (len(piezas) - 1)
        h = max(p.height for p in piezas)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = 0
        for p in piezas:
            im.alpha_composite(p, (x, 0)); x += p.width + esp
        capas.append(im)
    w = max(c.width for c in capas)
    h = sum(c.height for c in capas) + 2 * (len(capas) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for c in capas:
        out.alpha_composite(c, ((w - c.width) // 2, y)); y += c.height + 2
    return out


def construir_subtitulos(subt):
    out = []
    for a, b, frase in subt:
        trozos = trocear(frase)
        pesos = [len(x) + 3 for x in trozos]
        tot, cur = sum(pesos), a
        for tz, pz in zip(trozos, pesos):
            d_ = (b - a) * pz / tot
            out.append([cur, cur + d_, subtitulo_img(tz)])
            cur += d_
    for i in range(len(out) - 1):
        if out[i + 1][0] - out[i][1] < 0.45:
            out[i][1] = out[i + 1][0]
    return out


# ------------------------------------------------------------- montaje
GAP, ENTRADA, COLA = 0.28, 0.4, 0.55
ENCIMA = {"maquina"}  # elementos dinámicos que se dibujan después de las cajas


def linea_temporal(v):
    escenas, voz_total, subt = [], [], []
    t = 0.0
    for i, esc in enumerate(v["escenas"]):
        tiempos, cur, clips = [], (0.15 if i == 0 else ENTRADA), []
        for frase in esc["say"]:
            a = audio.voz(frase)
            tiempos.append(cur)
            clips.append((cur, a))
            subt.append((t + cur, t + cur + len(a) / audio.VOZ_SR, frase))
            cur += len(a) / audio.VOZ_SR + GAP
        dur = cur - GAP + (2.2 if esc["t"] == "cta" else COLA)
        escenas.append(dict(esc=esc, t0=t, dur=dur, tiempos=tiempos))
        voz_total.append((t, clips))
        t += dur
    pista = np.zeros(int(t * audio.VOZ_SR) + audio.VOZ_SR, np.float32)
    for t0, clips in voz_total:
        for c0, a in clips:
            i = int((t0 + c0) * audio.VOZ_SR)
            pista[i:i + len(a)] += a
    return escenas, t, pista, subt


def fmt_srt(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{int((r % 1) * 1000):03d}"


def logo_img(tema):
    f = fuente("pixel", 8)
    t = txt_img(CANAL, f, "blanco", None)
    c = caja(t.width + 12, 16, borde=tema["a"], sombra=False)
    c.alpha_composite(t, (6, 4))
    return c


def render_video(v, idx):
    tema_n, slug = v["tema"], v["slug"]
    tema = TEMAS[tema_n]
    base = os.path.join(SALIDA, slug)
    os.makedirs(base, exist_ok=True)
    suf = "_preview" if PREVIEW else ""
    print(f"[{slug}] voz…", flush=True)
    escenas, total, pista_voz, subt = linea_temporal(v)
    wav_voz = os.path.join(base, f"voz{suf}.wav")
    audio.sf.write(wav_voz, pista_voz, audio.VOZ_SR)

    escena_objs, efectos = [], []
    for e in escenas:
        sp, dyn, sfx = construir_escena(e["esc"], tema_n, e["tiempos"], e["dur"])
        escena_objs.append((e, sp, dyn))
        efectos += [(e["t0"] + t, k) for t, k in sfx]
        if e["t0"] > 0:
            efectos.append((e["t0"] - 0.05, 1))

    print(f"[{slug}] música…", flush=True)
    mus = audio.chiptune(total + 1, semilla=idx, bpm=[118, 124, 112, 128, 120][idx % 5], tono="ACDEFG"[idx % 6])
    for t, k in efectos:
        s = audio.blip(k)
        i = int(t * audio.MUS_SR)
        j = min(len(mus), i + len(s))
        if 0 <= i < len(mus):
            mus[i:j] += s[: j - i] * 2.2
    wav_mus = os.path.join(base, f"musica{suf}.wav")
    audio.sf.write(wav_mus, mus, audio.MUS_SR)

    with open(os.path.join(base, f"{slug}.es.srt"), "w", encoding="utf-8") as fs:
        for k, (a, b, txt) in enumerate(subt, 1):
            fs.write(f"{k}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{txt}\n\n")
    with open(os.path.join(base, "duracion.json"), "w") as fd:
        json.dump(dict(duracion=round(total, 1)), fd)

    print(f"[{slug}] imagen…", flush=True)
    fondo = Fondo(v["fondo"], tema_n, idx)
    subs = construir_subtitulos(subt)
    logo = logo_img(tema)
    aviso_l = [txt_img(ln, fuente("texto", 20), "gris") for ln in envolver(AVISO, fuente("texto", 20), ANCHO)]
    velo = Image.new("RGBA", (BW, BH), col("negro") + (70,))

    mp4 = os.path.join(base, f"video_mudo{suf}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "medium", "-tune", "animation",
                           "-crf", "26" if PREVIEW else "18", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    k_esc, k_sub = 0, 0
    for fi in range(int(total * FPS)):
        t = fi / FPS
        while k_esc + 1 < len(escena_objs) and t >= escena_objs[k_esc + 1][0]["t0"]:
            k_esc += 1
        e, sp, dyn = escena_objs[k_esc]
        tl = t - e["t0"]
        off = MG + int(round(MG * 0.8 * math.sin(2 * math.pi * t / 40 + idx)))
        frame = fondo.frame(t, off).convert("RGBA")
        frame.alpha_composite(velo)
        d = ImageDraw.Draw(frame)
        pintar_dinamico(frame, d, [x for x in dyn if x[0] not in ENCIMA], tl, tema_n)
        for s_ in sp:
            s_.pintar(frame, tl, e["dur"])
        pintar_dinamico(frame, d, [x for x in dyn if x[0] in ENCIMA], tl, tema_n)  # lo que va encima de sus cajas
        while k_sub + 1 < len(subs) and t >= subs[k_sub + 1][0]:
            k_sub += 1
        s0, s1, simg = subs[k_sub]
        if s0 <= t < s1:
            dy = 2 if (t - s0) < 0.07 else 0
            frame.alpha_composite(simg, (X0 + (ANCHO - simg.width) // 2, Y_SUBT - simg.height // 2 + dy))
        frame.alpha_composite(logo, (X0, 34))
        if t < 6:
            for j, im in enumerate(aviso_l):
                frame.alpha_composite(im, (X0 + (ANCHO - im.width) // 2, 548 + j * 18))
        d.rectangle((0, 0, int(BW * t / total), 1), fill=col(tema["a"]))
        arr = np.asarray(frame.convert("RGB")).copy()
        # transición: tramado a negro al entrar y al salir de escena
        p = None
        if k_esc > 0 and tl < 0.25:
            p = 1 - tl / 0.25
        elif k_esc + 1 < len(escena_objs) and e["dur"] - tl < 0.18:
            p = 1 - (e["dur"] - tl) / 0.18
        if p is not None:
            arr[BAYER_PANT < p] = col("negro")
        if ESC > 1:
            arr = arr.repeat(ESC, 0).repeat(ESC, 1)
        ff.stdin.write(arr.tobytes())
        if fi % (FPS * 30) == 0:
            print(f"[{slug}] {t:6.1f}/{total:.1f}s", flush=True)
    ff.stdin.close(); ff.wait()

    print(f"[{slug}] mezcla…", flush=True)
    final = os.path.join(base, f"{slug}{suf}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.30[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    for tmp in (mp4, wav_voz, wav_mus):
        os.remove(tmp)
    print(f"[{slug}] OK → {final} ({total:.1f}s)", flush=True)
    return total


if __name__ == "__main__":
    filtros = sys.argv[1:]
    for i, v in enumerate(VIDEOS):
        if not filtros or any(v["slug"].startswith(f) for f in filtros):
            render_video(v, i)
