# -*- coding: utf-8 -*-
"""Pixel art «de acabado»: lienzo 216x384 ampliado x5 (1080x1920), todo dibujado a mano
por código con volumen (luz/sombra), contornos oscuros, sombras en el suelo, charcos de
luz tramados y personajes grandes. Personajes originales del canal: la tele y «Móvil».

Vídeo: por qué no puedes dejar de deslizar.   Uso: python3 pixel_pro.py [--muestra]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import render as R
import historia as Hm
import historia_scroll as HS

CW, CH, ESC, FPS = 216, 384, 5, 30
W, H = CW * ESC, CH * ESC
SUELO = 252
SLUG = "17-por-que-no-paras-de-deslizar"
SALIDA = os.path.join(Hm.PL.SALIDA, SLUG)
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

# paleta
CON = (30, 22, 38)          # contorno oscuro (no negro)
PARED, PARED2, PUNTO, JUNTA = (34, 40, 78), (28, 32, 66), (50, 58, 102), (22, 24, 50)
MADERA, MADERA_L, MADERA_S = (122, 80, 46), (156, 106, 62), (86, 54, 32)
LADR, LADR_L, MORT = (98, 60, 46), (120, 76, 58), (62, 38, 32)
CREMA, CREMA_L, CREMA_S = (236, 226, 204), (252, 248, 236), (196, 180, 152)
PANT, PANT_L = (34, 58, 112), (52, 86, 150)
CIAN, ROSA, AMAR, ROJO, VERDE = (96, 226, 255), (255, 96, 150), (255, 214, 80), (230, 60, 70), (120, 220, 130)


# ------------------------------------------------------------- utilidades
def bloque(d, x0, y0, x1, y1, base, luz, sombra, borde=CON, r=0):
    """Rectángulo con volumen: luz arriba/izquierda, sombra abajo/derecha y contorno."""
    if r:
        d.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=borde)
        d.rounded_rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), radius=max(0, r - 1), fill=sombra)
        d.rounded_rectangle((x0 + 1, y0 + 1, x1 - 2, y1 - 2), radius=max(0, r - 1), fill=luz)
        d.rounded_rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), radius=max(0, r - 2), fill=base)
    else:
        d.rectangle((x0, y0, x1, y1), fill=borde)
        d.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=sombra)
        d.rectangle((x0 + 1, y0 + 1, x1 - 2, y1 - 2), fill=luz)
        d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), fill=base)


def tramar(arr, mask, color, fuerza):
    """Mezcla un color con tramado ordenado (iluminación pixel art)."""
    h, w = mask.shape
    um = np.tile(B4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    sel = mask & (um < fuerza)
    arr[sel] = color


def sombra_suelo(d, cx, y, ancho):
    d.ellipse((cx - ancho // 2, y - 2, cx + ancho // 2, y + 3), fill=(40, 24, 26))


def pegar(c, im, x, y):
    c.alpha_composite(im, (int(round(x - im.width / 2)), int(round(y - im.height / 2))))


def escalar(im, k):
    return im.resize((max(1, im.width * k), max(1, im.height * k)), Image.NEAREST)


def pop(im, tl, dur=0.25):
    u = min(1.0, max(0.0, tl / dur))
    k = [0.4, 0.75, 1.12, 1.0][min(3, int(u * 4))]
    return im if k == 1.0 else im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)


def texto(t, tam=8, color="blanco", sombra="negro"):
    return R.txt_img(t, R.fuente("pixel", tam), color, sombra, contorno=sombra is not None)


# ------------------------------------------------------------- fondo
def cuarto(luz=(150, 110, 200)):
    im = Image.new("RGB", (CW, CH), PARED)
    d = ImageDraw.Draw(im)
    for y in range(0, SUELO):
        if y % 5 == 2:
            for x in range(2 + (y // 5 % 2) * 2, CW, 4):
                d.point((x, y), fill=PUNTO)
    for x in range(0, CW, 54):
        d.line((x, 0, x, SUELO), fill=JUNTA, width=2)
    # ventana grande con marco, alféizar y ciudad
    x0, y0, x1, y1 = 6, 18, 92, 112
    d.rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), fill=CON)
    d.rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), fill=MADERA)
    d.line((x0 - 4, y0 - 4, x1 + 4, y0 - 4), fill=MADERA_L); d.line((x0 - 4, y0 - 4, x0 - 4, y1 + 4), fill=MADERA_L)
    cielo = R.dither_vertical(x1 - x0, y1 - y0, ["negro", "marino", "uva"])
    im.paste(Image.fromarray(cielo), (x0, y0))
    rng = np.random.default_rng(7)
    x = x0
    while x < x1:
        bw_, bh_ = int(rng.integers(7, 15)), int(rng.integers(22, 60))
        d.rectangle((x, y1 - bh_, min(x1 - 1, x + bw_), y1 - 1), fill=(18, 16, 40))
        for wy in range(y1 - bh_ + 3, y1 - 3, 5):
            for wx in range(x + 2, min(x1 - 2, x + bw_ - 1), 3):
                if rng.random() < 0.3:
                    d.point((wx, wy), fill=(255, 206, 90))
        x += bw_ + 1
    d.ellipse((70, 26, 80, 36), fill=(250, 240, 210))
    d.rectangle(((x0 + x1) // 2 - 2, y0, (x0 + x1) // 2 + 1, y1), fill=MADERA)
    d.rectangle((x0, (y0 + y1) // 2 - 2, x1, (y0 + y1) // 2 + 1), fill=MADERA)
    bloque(d, x0 - 8, y1 + 4, x1 + 8, y1 + 10, MADERA, MADERA_L, MADERA_S)   # alféizar
    # cuadro de la pared
    bloque(d, 168, 70, 206, 116, (60, 66, 110), (80, 88, 140), (44, 48, 84))
    d.rectangle((173, 75, 201, 111), fill=(40, 46, 88))
    # rodapié y suelo de ladrillo (filas más altas cerca de la cámara)
    d.rectangle((0, SUELO - 3, CW, SUELO), fill=(44, 32, 44))
    y, fila = SUELO + 1, 0
    while y < CH:
        alto = 7 + fila * 2
        d.rectangle((0, y, CW, y + alto), fill=LADR)
        d.line((0, y, CW, y), fill=LADR_L)
        d.line((0, y + alto, CW, y + alto), fill=MORT)
        paso = 20 + fila * 6
        for x in range(-paso + (fila % 2) * paso // 2, CW, paso):
            d.line((x, y, x, y + alto), fill=MORT)
        y += alto + 1; fila += 1
    arr = np.array(im)
    # charco de luz en el suelo (tramado) y halo de la ventana
    yy, xx = np.mgrid[0:CH, 0:CW]
    charco = ((xx - CW * 0.62) / 70) ** 2 + ((yy - (SUELO + 22)) / 26) ** 2
    tramar(arr, (charco < 1) & (yy > SUELO), (150, 98, 120), 0.5)
    tramar(arr, (charco < 0.45) & (yy > SUELO), (186, 130, 150), 0.5)
    oscuro = (yy > SUELO + 60)
    tramar(arr, oscuro, (52, 32, 28), np.clip((yy - SUELO - 60) / 160.0, 0, 0.7)[oscuro].mean())
    halo = ((xx - 49) / 70) ** 2 + ((yy - 65) / 70) ** 2
    tramar(arr, (halo < 1) & ~((xx > 1) & (xx < 97) & (yy > 13) & (yy < 117)) & (yy < SUELO), (44, 52, 96), 0.35)
    im = Image.fromarray(arr)
    # planta en primer plano (abajo a la izquierda)
    d = ImageDraw.Draw(im)
    for k, (a, l) in enumerate(((200, 46), (230, 52), (255, 40), (290, 50), (320, 44))):
        ang = math.radians(a)
        bx, by = 10, CH - 6
        for s in range(l):
            px = bx + math.cos(ang) * s + math.sin(s / 7) * 2
            py = by + math.sin(ang) * s
            d.ellipse((px - 4, py - 3, px + 4, py + 3), fill=(26, 70, 52) if s % 6 else (34, 90, 64))
    bloque(d, -4, CH - 16, 26, CH + 2, (150, 70, 50), (180, 90, 62), (110, 50, 36))
    return im.convert("RGBA")


# ------------------------------------------------------------- personajes
def tele(t, cara="feliz", habla=False):
    """La mascota del canal en pixel con volumen. ~44x52."""
    im = Image.new("RGBA", (48, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # antenas
    d.line((17, 12, 11, 2), fill=CON, width=3); d.line((17, 12, 11, 2), fill=(170, 170, 184), width=1)
    d.line((31, 12, 38, 1), fill=CON, width=3); d.line((31, 12, 38, 1), fill=(170, 170, 184), width=1)
    d.rectangle((8, 0, 12, 4), fill=CON); d.rectangle((9, 1, 11, 3), fill=AMAR)
    d.rectangle((36, 0, 40, 4), fill=CON); d.rectangle((37, 1, 39, 3), fill=ROSA)
    # patas
    for x in (13, 31):
        d.rectangle((x, 44, x + 4, 53), fill=CON); d.rectangle((x + 1, 45, x + 3, 52), fill=(70, 72, 86))
    # cuerpo
    bloque(d, 2, 11, 45, 47, CREMA, CREMA_L, CREMA_S, r=6)
    d.rectangle((4, 40, 43, 44), fill=(214, 168, 150))
    # pantalla
    d.rounded_rectangle((6, 15, 34, 39), radius=3, fill=CON)
    d.rounded_rectangle((7, 16, 33, 38), radius=3, fill=PANT)
    for y in range(18, 38, 3):
        d.line((8, y, 32, y), fill=(30, 50, 100))
    d.line((8, 17, 14, 17), fill=PANT_L)
    # botones
    d.rectangle((37, 18, 41, 22), fill=CON); d.rectangle((38, 19, 40, 21), fill=AMAR)
    d.rectangle((37, 25, 41, 29), fill=CON); d.rectangle((38, 26, 40, 28), fill=CIAN)
    # cara
    if cara == "sorpresa":
        d.rectangle((12, 22, 14, 25), fill=CIAN); d.rectangle((25, 22, 27, 25), fill=CIAN)
        d.rectangle((18, 29, 21, 33), fill=CIAN)
    elif cara == "guiño":
        d.line((11, 24, 15, 22), fill=CIAN, width=1); d.line((11, 24, 15, 26), fill=CIAN)
        d.line((24, 23, 28, 23), fill=CIAN)
        d.line((14, 30, 19, 33), fill=CIAN); d.line((19, 33, 25, 30), fill=CIAN)
    else:
        for x in (11, 24):
            d.point([(x, 24), (x + 1, 23), (x + 2, 22), (x + 3, 23), (x + 4, 24)], fill=CIAN)
        if habla and int(t * 8) % 2 == 0:
            d.rectangle((16, 29, 23, 34), fill=CIAN); d.rectangle((17, 30, 22, 33), fill=(20, 24, 50)); d.rectangle((18, 32, 21, 33), fill=ROSA)
        else:
            d.line((14, 30, 19, 33), fill=CIAN); d.line((19, 33, 25, 30), fill=CIAN)
    d.rectangle((8, 30, 10, 31), fill=ROSA); d.rectangle((29, 30, 31, 31), fill=ROSA)
    return im


def movil(t, cara="enfadado", pantalla=(80, 150, 255), andar=0.0):
    """«Móvil», el móvil gruñón (original). ~24x40."""
    im = Image.new("RGBA", (26, 42), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = int(math.sin(andar * 10) * 2) if andar else 0
    for x, dp in ((7, p), (16, -p)):
        d.rectangle((x, 32, x + 3, 40 + dp), fill=CON)
    bloque(d, 2, 1, 23, 34, (44, 44, 58), (70, 70, 90), (30, 30, 40), r=3)
    d.rectangle((5, 5, 20, 29), fill=pantalla)
    d.line((5, 5, 9, 5), fill=tuple(min(255, c + 60) for c in pantalla))
    n = (20, 20, 30)
    if cara == "enfadado":
        d.line((7, 11, 10, 13), fill=n); d.line((18, 11, 15, 13), fill=n)
        d.point([(8, 15), (17, 15)], fill=n); d.line((9, 22, 16, 22), fill=n)
    elif cara == "feliz":
        d.point([(8, 14), (17, 14)], fill=n); d.line((8, 20, 12, 23), fill=n); d.line((12, 23, 17, 20), fill=n)
    else:
        d.rectangle((8, 12, 9, 15), fill=n); d.rectangle((16, 12, 17, 15), fill=n); d.rectangle((11, 19, 14, 23), fill=n)
    d.line((2, 18, 0, 23), fill=CON, width=2); d.line((23, 18, 25, 23), fill=CON, width=2)
    return im


def movil_mini(idx):
    im = Image.new("RGBA", (10, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cols = [(255, 120, 90), (90, 200, 140), (80, 150, 255), (255, 200, 70), (200, 110, 255)]
    d.rectangle((0, 0, 9, 15), fill=CON); d.rectangle((1, 1, 8, 14), fill=(44, 44, 58))
    d.rectangle((2, 2, 7, 12), fill=cols[idx % len(cols)])
    return im


def brazo(d, x0, y0, x1, y1):
    d.line((x0, y0, x1, y1), fill=CON, width=4)
    d.line((x0, y0, x1, y1), fill=CREMA, width=2)
    d.rectangle((x1 - 2, y1 - 2, x1 + 2, y1 + 2), fill=CON); d.rectangle((x1 - 1, y1 - 1, x1 + 1, y1 + 1), fill=CREMA_L)


# ------------------------------------------------------------- objetos grandes (dibujados en pixel)
def reloj_digital(txt):
    im = Image.new("RGBA", (92, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bloque(d, 0, 0, 91, 39, (26, 22, 34), (54, 48, 66), (16, 14, 22), r=3)
    t = texto(txt, 16, "rojo", None)
    im.alpha_composite(t, ((92 - t.width) // 2, (40 - t.height) // 2 + 1))
    return im


def cerebro(brillo):
    im = Image.new("RGBA", (70, 54), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = tuple(int(c + (255 - c) * brillo * 0.4) for c in (240, 140, 170))
    for (x, y, r) in ((20, 22, 17), (36, 17, 18), (51, 24, 16), (28, 36, 16), (46, 37, 15)):
        d.ellipse((x - r - 1, y - r - 1, x + r + 1, y + r + 1), fill=CON)
    for (x, y, r) in ((20, 22, 17), (36, 17, 18), (51, 24, 16), (28, 36, 16), (46, 37, 15)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=base)
    for k in range(5):
        d.arc((10 + k * 10, 12, 26 + k * 10, 30), 200, 330, fill=(200, 90, 130))
    d.arc((18, 30, 40, 46), 200, 330, fill=(200, 90, 130))
    d.line((14, 10, 20, 7), fill=(255, 220, 230))
    return im


def tragaperras(tl, dur):
    im = Image.new("RGBA", (84, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bloque(d, 2, 20, 74, 103, (204, 50, 62), (236, 90, 100), (150, 30, 44), r=6)
    bloque(d, 6, 4, 70, 26, AMAR, (255, 240, 150), (210, 160, 40), r=4)
    t = texto("777", 8, "rojo", None)
    im.alpha_composite(t, ((76 - t.width) // 2, 10))
    d.rectangle((10, 36, 66, 74), fill=CON)
    for k in range(3):
        gira = tl < dur * (0.5 + 0.12 * k)
        idx = int(tl * 16 + k * 3) % 4 if gira else [0, 0, 3][k]
        x = 13 + k * 18
        d.rectangle((x, 39, x + 14, 71), fill=(250, 250, 250))
        d.line((x, 39, x + 14, 39), fill=(200, 200, 210))
        sym = texto(["7", "$", "%", "?"][idx], 8, ["rojo", "verde", "azul", "rosa"][idx], None)
        im.alpha_composite(sym, (x + 4, 51 + (int(tl * 30) % 4 if gira else 0)))
    d.rectangle((24, 82, 52, 90), fill=CON); d.rectangle((25, 83, 51, 89), fill=(40, 20, 30))
    tira = tl < dur * 0.4
    d.line((76, 60, 82, 40 + (14 if tira else 0)), fill=CON, width=3); d.line((76, 60, 82, 40 + (14 if tira else 0)), fill=(180, 180, 190))
    d.ellipse((78, 34 + (14 if tira else 0), 84, 40 + (14 if tira else 0)), fill=ROJO, outline=CON)
    return im


def paloma(picotea):
    im = Image.new("RGBA", (40, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 10, 30, 28), fill=CON); d.ellipse((5, 11, 29, 27), fill=(150, 156, 176))
    d.ellipse((9, 15, 24, 25), fill=(120, 126, 148))
    hx, hy = 28 + 2 * picotea, 8 + 6 * picotea
    d.ellipse((hx - 7, hy - 7, hx + 7, hy + 7), fill=CON); d.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), fill=(140, 146, 166))
    d.point((hx + 2, hy - 2), fill=CON)
    d.polygon([(hx + 6, hy - 1), (hx + 11, hy + 1), (hx + 6, hy + 3)], fill=(240, 170, 60))
    d.polygon([(4, 18), (0, 14), (0, 24)], fill=(120, 126, 148))
    d.line((14, 27, 13, 31), fill=(220, 120, 90)); d.line((20, 27, 21, 31), fill=(220, 120, 90))
    return im


def icono(tipo):
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if tipo == "reloj":
        d.ellipse((4, 6, 60, 62), fill=CON); d.ellipse((5, 7, 59, 61), fill=(232, 220, 196)); d.ellipse((9, 11, 55, 57), fill=(250, 244, 228))
        d.rectangle((28, 0, 36, 7), fill=CON); d.rectangle((29, 1, 35, 6), fill=(110, 110, 120))
        d.line((32, 34, 32, 18), fill=CON, width=3); d.line((32, 34, 44, 40), fill=ROSA, width=3)
        d.arc((12, 14, 52, 54), 200, 250, fill=(255, 255, 255), width=2)
    elif tipo == "campana":
        d.chord((10, 6, 54, 50), 180, 360, fill=CON); d.chord((11, 7, 53, 49), 180, 360, fill=AMAR)
        d.rectangle((11, 28, 53, 44), fill=AMAR); d.rectangle((6, 44, 58, 50), fill=CON); d.rectangle((7, 45, 57, 49), fill=(240, 190, 60))
        d.ellipse((26, 49, 38, 59), fill=CON); d.ellipse((27, 50, 37, 58), fill=AMAR)
        d.line((16, 14, 20, 10), fill=(255, 246, 190), width=2)
        d.line((4, 60, 60, 4), fill=CON, width=7); d.line((4, 60, 60, 4), fill=ROJO, width=4)
    elif tipo == "cama":
        bloque(d, 2, 30, 62, 48, (110, 130, 220), (150, 170, 240), (80, 96, 180))
        bloque(d, 6, 22, 24, 32, (250, 250, 250), (255, 255, 255), (210, 210, 220), r=3)
        d.rectangle((2, 30, 5, 60), fill=MADERA_S); d.rectangle((58, 38, 61, 60), fill=MADERA_S)
    return im


def persona_pixel():
    im = Image.new("RGBA", (30, 58), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((9, 42, 13, 57), fill=CON); d.rectangle((17, 42, 21, 57), fill=CON)
    bloque(d, 5, 20, 25, 45, (70, 82, 110), (96, 110, 140), (50, 58, 82), r=3)
    d.line((5, 24, 9, 8), fill=CON, width=4); d.line((25, 24, 21, 8), fill=CON, width=4)
    d.ellipse((7, 4, 23, 22), fill=CON); d.ellipse((8, 5, 22, 21), fill=(240, 196, 160))
    d.chord((7, 3, 23, 16), 180, 360, fill=(70, 46, 32))
    d.rectangle((9, 9, 21, 12), fill=(240, 196, 160))   # manos tapando los ojos
    return im


# ------------------------------------------------------------- escenas
MX = 52


def de_pie(c, t, x=MX, cara="feliz", salto=0.0, habla=True):
    d = ImageDraw.Draw(c)
    im = tele(t, cara, habla)
    sombra_suelo(d, x, SUELO + 12, 34 - int(salto / 3))
    y = SUELO + 12 - im.height / 2 - salto - (1 if int(t * 3) % 2 else 0)
    pegar(c, im, x, y)
    return x, y


def movil_quieto(c, t, cara="enfadado", x=176):
    d = ImageDraw.Draw(c)
    p = movil(t, cara)
    sombra_suelo(d, x, SUELO + 12, 20)
    pegar(c, p, x, SUELO + 12 - p.height / 2 - (1 if int(t * 2.5) % 2 else 0))


def titulo(c, t, tl, tam=8, color="blanco", y=130):
    pegar(c, pop(texto(t, tam, color), tl), CW / 2, y)


def s_hora(c, d, tl, dur):
    x, y = de_pie(c, tl)
    brazo(d, x + 18, y + 6, x + 30, y - 4)
    pegar(c, movil_mini(int(tl * 4)), x + 34, y - 10)
    movil_quieto(c, tl, "feliz")
    h = 22 + min(0.999, tl / dur)
    pegar(c, pop(reloj_digital(f"{int(h):02d}:{int((h % 1) * 60):02d}"), tl), 140, 150)


def s_razon(c, d, tl, dur):
    x, y = de_pie(c, tl, cara="sorpresa")
    pegar(c, pop(cerebro(0.5 + 0.5 * math.sin(tl * 5)), tl - 0.15), 140, 160 + int(2 * math.sin(tl * 3)))
    b = texto("?", 16, "amarillo")
    pegar(c, pop(b, tl), x + 20, y - 34)
    movil_quieto(c, tl, "sorpresa")


def s_cartel(c, d, tl, dur):
    de_pie(c, tl)
    borde = ROSA if int(tl * 4) % 2 else CIAN
    caja = Image.new("RGBA", (150, 60), (0, 0, 0, 0))
    cd = ImageDraw.Draw(caja)
    cd.rectangle((0, 0, 149, 59), fill=CON); cd.rectangle((2, 2, 147, 57), fill=borde); cd.rectangle((4, 4, 145, 55), fill=(16, 12, 26))
    caja.alpha_composite(texto("RECOMPENSA", 8, "rosa"), (75 - texto("RECOMPENSA", 8).width // 2, 16))
    caja.alpha_composite(texto("VARIABLE", 8, "cian"), (75 - texto("VARIABLE", 8).width // 2, 34))
    pegar(c, pop(caja, tl), CW / 2 + 20, 140)
    movil_quieto(c, tl)


def s_traga(c, d, tl, dur):
    tg = tragaperras(tl, dur)
    sombra_suelo(d, 140, SUELO + 12, 70)
    pegar(c, pop(tg, tl), 136, SUELO + 12 - tg.height / 2)
    x, y = de_pie(c, tl, x=46)


def s_anzuelo(c, d, tl, dur):
    de_pie(c, tl)
    u = min(1, tl / 0.6)
    yh = 30 + 150 * u - max(0, tl - 1.0) * 80
    d.line((176, 0, 176, yh), fill=(220, 220, 230))
    d.arc((170, yh - 2, 182, yh + 10), 0, 200, fill=(200, 200, 214), width=2)
    if tl > 1.0:
        p = movil(tl, "sorpresa")
        pegar(c, p, 176, yh + 26)
    else:
        movil_quieto(c, tl)
    titulo(c, "TE ENGANCHA", tl, 16, "rosa", 100)


def caja_skinner(c, d, pico):
    bloque(d, 92, 112, 206, SUELO + 6, (190, 192, 206), (226, 228, 238), (140, 142, 160))
    d.rectangle((98, 118, 200, SUELO), fill=(232, 232, 242))
    d.rectangle((182, 160 + 2 * pico, 192, 170 + 2 * pico), fill=CON); d.rectangle((183, 161 + 2 * pico, 191, 169 + 2 * pico), fill=ROJO)
    pegar(c, escalar(paloma(pico), 2), 150, SUELO - 26)


def s_skinner(c, d, tl, dur):
    caja_skinner(c, d, 0)
    de_pie(c, tl, x=46)
    titulo(c, "AÑOS 50", tl, 16, "amarillo", 92)


def s_paloma(c, d, tl, dur):
    pico = int(tl * 10) % 2
    caja_skinner(c, d, pico)
    for k in range(4):
        if (int(tl * 3) + k * 2) % 4 == 0:
            d.rectangle((118 + k * 8, SUELO - 4, 119 + k * 8, SUELO - 3), fill=(200, 160, 80))
    de_pie(c, tl, x=46, cara="sorpresa")
    titulo(c, "¡SIN PARAR!", tl, 16, "blanco", 92)


def s_dedo(c, d, tl, dur):
    x, y = de_pie(c, tl)
    f = (tl * 3) % 1
    brazo(d, x + 18, y + 6, x + 30, y - 4 - int(math.sin(f * math.pi) * 6))
    pegar(c, movil_mini(int(tl * 3)), x + 34, y - 12)
    p = movil(tl, "enfadado", [(255, 120, 90), (90, 200, 140), (80, 150, 255)][int(tl * 3) % 3])
    sombra_suelo(d, 150, SUELO + 12, 50)
    pegar(c, escalar(p, 3), 150, SUELO + 12 - p.height * 1.5)


def s_algoritmo(c, d, tl, dur):
    de_pie(c, tl)
    p = movil(tl, "feliz")
    sombra_suelo(d, 150, SUELO + 12, 50)
    pegar(c, escalar(p, 3), 150, SUELO + 12 - p.height * 1.5)
    cor = R.icono("corazon", "rosa")
    for k in range(5):
        yy = 200 - ((tl * 60 + k * 30) % 150)
        pegar(c, escalar(cor, 2), 150 + 26 * math.sin(tl * 3 + k), yy)
    titulo(c, "APRENDE DE TI", tl, 16, "cian", 70)


def s_dopamina(c, d, tl, dur):
    de_pie(c, tl, x=40)
    for i, (txt, alto, colr) in enumerate((("ESPERAR", 130, ROSA), ("RECIBIR", 50, CIAN))):
        x = 104 + i * 74
        h = int(alto * min(1, max(0, (tl - i * 0.3) / 0.8)))
        h -= h % 4
        if h > 4:
            bloque(d, x - 20, SUELO - h, x + 20, SUELO, colr, tuple(min(255, v + 50) for v in colr), tuple(int(v * 0.7) for v in colr))
        pegar(c, texto(txt, 8), x, SUELO + 22)
    titulo(c, "DOPAMINA", tl, 16, "amarillo", 92)


def s_infinito(c, d, tl, dur):
    de_pie(c, tl)
    for k in range(30):
        a = k / 30 * 2 * math.pi + tl * 2
        x = 140 + math.sin(a) * 52
        y = 150 + math.sin(2 * a) * 22
        d.rectangle((x - 2, y - 2, x + 1, y + 1), fill=ROSA if k % 2 else CIAN)
    movil_quieto(c, tl, "feliz")
    titulo(c, "SIN FINAL", tl, 16, "cian", 92)


def s_raskin(c, d, tl, dur):
    de_pie(c, tl, x=46)
    p = persona_pixel()
    sombra_suelo(d, 150, SUELO + 12, 30)
    pegar(c, escalar(p, 2), 150, SUELO + 12 - p.height)
    titulo(c, "SE ARREPIENTE", tl, 16, "rosa", 92)


def s_cadena(c, d, tl, dur):
    de_pie(c, tl)
    rota = tl > dur * 0.5
    for k in range(7):
        if rota and k == 3:
            continue
        x = 100 + k * 16 + ((k - 3) * 6 if rota else 0)
        y = 150 + (5 if k % 2 else 0) + (abs(k - 3) * 4 if rota else 0)
        d.ellipse((x - 8, y - 5, x + 8, y + 5), outline=CON, width=4)
        d.ellipse((x - 7, y - 4, x + 7, y + 4), outline=(196, 196, 210), width=2)
    titulo(c, "3 TRUCOS", tl, 16, "amarillo", 92)


def s_truco(tipo, txt):
    def f(c, d, tl, dur):
        de_pie(c, tl)
        ic = icono(tipo)
        pegar(c, pop(ic, tl), 146, 160)
        num, palabra = txt.split(". ", 1)
        titulo(c, f"TRUCO {num}/3", tl, 8, "amarillo", 84)
        titulo(c, palabra, tl - 0.1, 16, "blanco", 102)
        if tipo == "cama":
            p = movil(tl, "enfadado", andar=tl)
            sombra_suelo(d, 176 + tl * 30, SUELO + 12, 20)
            pegar(c, p, 176 + tl * 30, SUELO + 12 - p.height / 2)
        else:
            movil_quieto(c, tl, "sorpresa")
    return f


def s_final(c, d, tl, dur):
    salto = abs(math.sin(tl * 5)) * 14
    de_pie(c, tl, x=CW / 2, cara="guiño" if int(tl * 2) % 2 else "feliz", salto=salto)
    titulo(c, "¿VES?", tl, 16, "rosa", 96)
    titulo(c, "FUNCIONA", tl - 0.15, 16, "rosa", 118)
    rng = np.random.default_rng(1)
    cols = [ROSA, CIAN, AMAR, VERDE, (200, 120, 255)]
    for i in range(40):
        x0 = rng.uniform(0, CW); v = rng.uniform(80, 150)
        yy = -6 + v * tl - (i % 7) * 12
        if 0 <= yy <= CH:
            xx = x0 + math.sin(tl * 4 + i) * 6
            d.rectangle((xx, yy, xx + 1, yy + 1 + i % 2), fill=cols[i % len(cols)])


ESCENAS = [s_hora, s_razon, s_cartel, s_traga, s_anzuelo, s_skinner, s_paloma, s_dedo, s_algoritmo,
           s_dopamina, s_infinito, s_raskin, s_cadena, s_truco("reloj", "1. TEMPORIZADOR"),
           s_truco("campana", "2. SIN AVISOS"), s_truco("cama", "3. MÓVIL LEJOS"), s_final]
assert len(ESCENAS) == len(HS.BEATS)


def subtitulo(palabras, k):
    f = R.fuente("texto", 20)
    piezas = [R.txt_img(p.upper(), f, "amarillo" if i == k else "blanco", "negro", contorno=True) for i, p in enumerate(palabras[:k + 1])]
    w = sum(p.width for p in piezas) + 5 * (len(piezas) - 1)
    out = Image.new("RGBA", (CW, max(p.height for p in piezas) + 6), (0, 0, 0, 0))
    ImageDraw.Draw(out).rectangle((0, 0, CW, out.height), fill=(10, 8, 18, 130))
    x = (CW - w) // 2
    for p in piezas:
        out.alpha_composite(p, (x, 3)); x += p.width + 5
    return out


def render():
    os.makedirs(SALIDA, exist_ok=True)
    t = 0.05
    beats, clips, palabras_t = [], [], []
    for b in HS.BEATS:
        a = audio.voz(b["say"])
        d_ = len(a) / audio.VOZ_SR
        beats.append(dict(b, t0=t, dur=d_ + 0.12)); clips.append((t, a))
        palabras_t.append(Hm.PL.tiempos_palabras(b["say"], t, d_))
        t += d_ + 0.12
    total = t + 0.5
    print(f"[{SLUG}] {total:.1f}s", flush=True)
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    wav_voz = os.path.join(SALIDA, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    mus = audio.chiptune(total + 1, semilla=4, bpm=108, tono="C")
    for b in beats:
        if "sfx" in b:
            off, nombre = b["sfx"]
            off = b["dur"] * float(off[:-1]) / 100 if isinstance(off, str) else off
            s = audio.efecto(nombre)
            i = int((b["t0"] + off) * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * 1.7
        s = audio.blip(0)
        i = int((b["t0"] + 0.05) * audio.MUS_SR); mus[i:i + len(s)] += s[:max(0, min(len(s), len(mus) - i))] * 0.7
    wav_mus = os.path.join(SALIDA, "musica.wav"); audio.sf.write(wav_mus, mus, audio.MUS_SR)
    fondo = cuarto()
    bayer = np.tile(R._b8, (CH // 8 + 1, CW // 8 + 1))[:CH, :CW]
    muestra = "--muestra" in sys.argv
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-tune", "animation", "-crf", "18", "-pix_fmt", "yuv420p", mp4],
        stdin=subprocess.PIPE)
    cuadros = range(int(total * FPS)) if not muestra else [int((b["t0"] + b["dur"] * 0.6) * FPS) for b in beats]
    for fi in cuadros:
        tg = fi / FPS
        kb = max((i for i, b in enumerate(beats) if b["t0"] <= tg), default=0)
        b = beats[kb]; tl = max(0.0, tg - b["t0"])
        c = fondo.copy()
        d = ImageDraw.Draw(c)
        ESCENAS[kb](c, d, tl, b["dur"])
        pts = palabras_t[kb]
        k_act = max([i for i, (t0, _) in enumerate(pts) if tg >= t0], default=-1)
        if k_act >= 0:
            g0 = (k_act // 3) * 3
            sub = subtitulo([p for _, p in pts[g0:g0 + 3]], k_act - g0)
            c.alpha_composite(sub, (0, 284 + (1 if tg - pts[k_act][0] < 0.07 else 0)))
        arr = np.asarray(c.convert("RGB"))
        temblor, flash = Hm.momento_clave(b, tl)
        if temblor:
            rng = np.random.default_rng(fi)
            arr = np.roll(arr, (int(rng.integers(-2, 3)), int(rng.integers(-2, 3))), (0, 1))
        if flash:
            arr = (arr * (1 - flash) + 255 * flash).astype(np.uint8)
        if kb > 0 and tl < 0.12:
            arr = arr.copy(); arr[bayer < 1 - tl / 0.12] = (12, 8, 22)
        if muestra:
            Image.fromarray(arr).save(os.path.join(SALIDA, f"muestra_{kb:02d}.png")); continue
        ff.stdin.write(arr.repeat(ESC, 0).repeat(ESC, 1).tobytes())
    if muestra:
        return
    ff.stdin.close(); ff.wait()
    final = os.path.join(SALIDA, f"{SLUG}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.3[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    "-shortest", final], check=True)
    for f_ in (mp4, wav_voz, wav_mus):
        os.remove(f_)
    print(f"[{SLUG}] OK → {final} ({total:.1f}s)", flush=True)


if __name__ == "__main__":
    render()
