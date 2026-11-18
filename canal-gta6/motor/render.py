# -*- coding: utf-8 -*-
"""Utilidades pixel art compartidas: paleta, fuentes de píxel y texto sin suavizado (subtítulos pixel)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont


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


