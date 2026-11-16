# -*- coding: utf-8 -*-
"""Render de los vídeos en vertical 9:16 para TikTok: fondos animados, motion
graphics, subtítulos quemados, voz, música y montaje.

Uso:
  python3 render.py                 # los 10 vídeos
  python3 render.py 01 05           # solo los que empiezan por esos prefijos
  PREVIEW=1 python3 render.py 01    # 540x960, rápido, para revisar
"""
import math, os, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import audio
from guiones import VIDEOS, CANAL, LEMA, AVISO

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SALIDA = os.path.join(RAIZ, "salida")
FUENTES = os.path.join(RAIZ, "fuentes")
PREVIEW = os.environ.get("PREVIEW") == "1"
S = 0.5 if PREVIEW else 1.0
W, H = int(1080 * S), int(1920 * S)  # vertical 9:16 (TikTok)
FPS = 30
MARGEN = int(160 * S)  # margen extra del fondo para el paneo

TEMAS = {
    "rosa":    dict(a=(255, 64, 160), b=(255, 176, 64), cielo=((18, 6, 40), (120, 20, 90), (255, 110, 110))),
    "cian":    dict(a=(40, 220, 255), b=(255, 80, 200), cielo=((4, 8, 30), (20, 40, 110), (60, 170, 220))),
    "dorado":  dict(a=(255, 200, 60), b=(255, 96, 96), cielo=((22, 8, 30), (110, 30, 70), (255, 170, 80))),
    "verde":   dict(a=(70, 255, 160), b=(40, 190, 255), cielo=((4, 14, 24), (10, 60, 80), (40, 180, 160))),
    "rojo":    dict(a=(255, 60, 70), b=(255, 200, 60), cielo=((20, 4, 8), (90, 10, 30), (220, 60, 50))),
    "morado":  dict(a=(176, 100, 255), b=(255, 80, 180), cielo=((10, 4, 30), (60, 20, 110), (220, 90, 200))),
    "naranja": dict(a=(255, 146, 40), b=(255, 60, 140), cielo=((24, 8, 20), (130, 40, 60), (255, 150, 60))),
}
BLANCO = (255, 255, 255)
TINTA = (14, 10, 26)

# ---------------------------------------------------------------- tipografía
_fuentes = {}


def fuente(tipo, tam):
    tam = max(8, int(tam * S))
    k = (tipo, tam)
    if k not in _fuentes:
        if tipo == "display":
            f = ImageFont.truetype(os.path.join(FUENTES, "Anton-Regular.ttf"), tam)
        else:
            f = ImageFont.truetype(os.path.join(FUENTES, "Montserrat-Variable.ttf"), tam)
            f.set_variation_by_name({"bold": "Bold", "semi": "SemiBold", "black": "Black", "med": "Medium"}[tipo])
        _fuentes[k] = f
    return _fuentes[k]


def medir(txt, f):
    l, t, r, b = f.getbbox(txt)
    return r - l, b - t, l, t


def envolver(txt, f, ancho):
    palabras, lineas, act = txt.split(), [], ""
    for p in palabras:
        prueba = (act + " " + p).strip()
        if medir(prueba, f)[0] <= ancho or not act:
            act = prueba
        else:
            lineas.append(act); act = p
    if act: lineas.append(act)
    return lineas


def sprite_texto(txt, f, color=BLANCO, sombra=True, brillo=None, borde=0):
    w, h, l, t = medir(txt, f)
    pad = int(30 * S)
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pos = (pad - l, pad - t)
    if brillo:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text(pos, txt, font=f, fill=brillo + (255,))
        g = g.filter(ImageFilter.GaussianBlur(14 * S))
        im = Image.alpha_composite(im, g)
        d = ImageDraw.Draw(im)
    if sombra:
        d.text((pos[0] + int(5 * S), pos[1] + int(6 * S)), txt, font=f, fill=(0, 0, 0, 150))
    d.text(pos, txt, font=f, fill=color + (255,), stroke_width=borde, stroke_fill=(0, 0, 0, 255))
    return im, pad


def caja(w, h, relleno=(10, 8, 24, 190), radio=22, borde=None, ancho_borde=3):
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, int(w) - 1, int(h) - 1), radius=int(radio * S), fill=relleno,
                        outline=(borde + (255,)) if borde else None, width=int(ancho_borde * S) if borde else 0)
    return im


# ---------------------------------------------------------------- fondos
def gradiente(w, h, paradas):
    y = np.linspace(0, 1, h)[:, None]
    n = len(paradas) - 1
    out = np.zeros((h, 1, 3))
    for i in range(n):
        a, b = np.array(paradas[i], float), np.array(paradas[i + 1], float)
        m = (y >= i / n) & ((y < (i + 1) / n) if i < n - 1 else (y <= 1))
        u = (y - i / n) * n
        out += m[..., None] * (a + (b - a) * u[..., None])
    return np.repeat(out, w, 1)


def palmera(d, x, base, alto, escala, color):
    # tronco curvado
    pts = []
    for i in range(21):
        u = i / 20
        pts.append((x + math.sin(u * 1.6) * 40 * escala, base - u * alto))
    for i in range(len(pts) - 1):
        wdt = (16 - 9 * i / 20) * escala
        d.line([pts[i], pts[i + 1]], fill=color, width=max(2, int(wdt)))
    cx, cy = pts[-1]
    for ang in range(0, 360, 40):
        a = math.radians(ang + 10)
        largo = (170 + 30 * math.sin(ang)) * escala
        hoja = []
        for j in range(12):
            u = j / 11
            hx = cx + math.cos(a) * largo * u
            hy = cy + math.sin(a) * largo * u * 0.55 + (u ** 2) * 90 * escala
            hoja.append((hx, hy))
        for j in range(len(hoja) - 1):
            d.line([hoja[j], hoja[j + 1]], fill=color, width=max(2, int((14 - j) * escala)))


def fondo_base(tipo, tema, semilla):
    rng = np.random.default_rng(semilla)
    bw, bh = W + 2 * MARGEN, H
    c = TEMAS[tema]["cielo"]
    hor = int(bh * 0.64)
    cielo = gradiente(bw, hor, [c[0], c[1], c[2]])
    img = np.zeros((bh, bw, 3))
    img[:hor] = cielo
    suelo = gradiente(bw, bh - hor, [(12, 4, 26), (4, 2, 10)])
    img[hor:] = suelo
    base = Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(base)
    sil = (10, 4, 22, 255)
    if tipo in ("atardecer", "oceano"):
        # sol con franjas
        sol = Image.new("RGBA", base.size, (0, 0, 0, 0))
        r = int(250 * S)
        cx, cy = bw // 2, hor - int(40 * S)
        sg = gradiente(2 * r, 2 * r, [(255, 236, 120), TEMAS[tema]["a"]])
        disco = Image.fromarray(sg.clip(0, 255).astype(np.uint8)).convert("RGBA")
        m = Image.new("L", (2 * r, 2 * r), 0)
        md = ImageDraw.Draw(m)
        md.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        for k in range(7):
            y0 = int(r * 1.05 + k * k * 4 * S + k * 16 * S)
            md.rectangle((0, y0, 2 * r, y0 + int((4 + k * 2.2) * S)), fill=0)
        md.rectangle((0, hor - (cy - r), 2 * r, 2 * r), fill=0)  # el sol se pone tras el horizonte
        sol.paste(disco, (cx - r, cy - r), m)
        glow = sol.filter(ImageFilter.GaussianBlur(60 * S))
        base = Image.alpha_composite(base, glow)
        base = Image.alpha_composite(base, sol)
        d = ImageDraw.Draw(base)
        # montañas lejanas
        pts = [(0, hor)]
        for x in range(0, bw + 40, 40):
            pts.append((x, hor - int((60 + 50 * math.sin(x / 170.0 + semilla) + 30 * math.sin(x / 61.0)) * S)))
        pts.append((bw, hor))
        d.polygon(pts, fill=(30, 10, 50, 255))
    if tipo == "noche":
        # estrellas
        for _ in range(260):
            x, y = rng.integers(0, bw), rng.integers(0, int(hor * 0.8))
            v = int(rng.integers(120, 255))
            d.point((x, y), fill=(v, v, v, 255))
        # luna
        r = int(70 * S)
        d.ellipse((bw * 0.78 - r, hor * 0.22 - r, bw * 0.78 + r, hor * 0.22 + r), fill=(250, 240, 220, 255))
        # skyline en dos capas
        for capa, (col, hmin, hmax) in enumerate([((40, 20, 70, 255), 120, 330), ((14, 6, 30, 255), 80, 260)]):
            x = 0
            while x < bw:
                wdt = int(rng.integers(50, 130) * S)
                alt = int(rng.integers(hmin, hmax) * S)
                d.rectangle((x, hor - alt, x + wdt, hor), fill=col)
                if capa == 1:
                    for wy in range(hor - alt + int(14 * S), hor - int(10 * S), int(22 * S)):
                        for wx in range(x + int(8 * S), x + wdt - int(10 * S), int(18 * S)):
                            if rng.random() < 0.35:
                                cc = TEMAS[tema]["b"] if rng.random() < 0.25 else (255, 214, 140)
                                d.rectangle((wx, wy, wx + int(7 * S), wy + int(9 * S)), fill=cc + (255,))
                x += wdt + int(rng.integers(0, 12) * S)
    if tipo in ("atardecer", "oceano"):
        for (x, esc) in [(int(70 * S), 1.25), (int(260 * S), 0.9), (bw - int(120 * S), 1.35), (bw - int(330 * S), 0.85)]:
            palmera(d, x, bh + 10, (780 if esc > 1 else 560) * S * (esc if esc > 1 else 1), esc * 1.15 * S, sil)
    return base, hor


def bucle_fondo(tipo, tema, semilla, n=30):
    base, hor = fondo_base(tipo, tema, semilla)
    bw, bh = base.size
    marcos = []
    a = TEMAS[tema]["a"]
    for k in range(n):
        f = base.copy()
        d = ImageDraw.Draw(f)
        u = k / n
        if tipo == "atardecer":
            vx = bw // 2
            for i in range(-26, 27):
                d.line([(vx + i * 14 * S, hor), (vx + i * 260 * S, bh)], fill=a + (150,), width=max(1, int(2 * S)))
            for j in range(14):
                z = (j + u) / 14
                y = hor + (bh - hor) * (z ** 2.2)
                d.line([(0, y), (bw, y)], fill=a + (int(60 + 140 * z),), width=max(1, int(2 * S)))
        elif tipo == "oceano":
            rng = np.random.default_rng(7)
            for j in range(70):
                z = rng.random()
                y = hor + (bh - hor) * z ** 1.6
                cx = bw / 2 + math.sin(u * 2 * math.pi + j) * 30 * S
                ancho = (40 + 300 * (1 - abs(cx - bw / 2) / bw)) * S * (0.4 + z)
                ancho *= 0.6 + 0.4 * math.sin(u * 2 * math.pi * 2 + j * 1.7)
                col = (255, 210, 140) if j % 3 else a
                d.line([(cx - ancho, y), (cx + ancho, y)], fill=col + (int(90 + 120 * z),), width=max(1, int(3 * S)))
        elif tipo == "noche":
            # tráfico con estelas en una autopista
            y1, y2 = hor + int(70 * S), hor + int(120 * S)
            d.rectangle((0, y1 - int(20 * S), bw, y2 + int(20 * S)), fill=(18, 10, 34, 255))
            for i in range(18):
                x = ((i * 233 + u * bw) % (bw + 400)) - 200
                d.line([(x, y1), (x + 150 * S, y1)], fill=(255, 70, 70, 230), width=max(2, int(5 * S)))
                x2 = bw - ((i * 311 + u * bw * 1.3) % (bw + 400)) + 200
                d.line([(x2, y2), (x2 - 150 * S, y2)], fill=(255, 240, 200, 230), width=max(2, int(5 * S)))
            for j in range(9):
                z = (j + u) / 9
                y = y2 + int(30 * S) + (bh - y2) * (z ** 2)
                d.line([(0, y), (bw, y)], fill=a + (int(30 + 90 * z),), width=max(1, int(2 * S)))
        marcos.append(np.asarray(f.convert("RGB")).copy())
    return marcos


# ---------------------------------------------------------------- easing
def ease_out(u):
    u = min(max(u, 0), 1)
    return 1 - (1 - u) ** 3


def ease_back(u):
    u = min(max(u, 0), 1)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


# ---------------------------------------------------------------- escenas
class Sprite:
    def __init__(self, img, x, y, t0=0.0, t1=None, anim="up", dur=0.45):
        self.img, self.x, self.y, self.t0, self.t1, self.anim, self.dur = img, int(x), int(y), t0, t1, anim, dur
        self.alpha = img.getchannel("A")

    def pintar(self, frame, t, fin_escena):
        if t < self.t0:
            return
        t1 = self.t1 if self.t1 is not None else fin_escena
        if t > t1:
            return
        u = (t - self.t0) / self.dur
        f = ease_out(u)
        x, y = self.x, self.y
        if self.anim == "up":
            y += int((1 - f) * 60 * S)
        elif self.anim == "left":
            x -= int((1 - f) * 120 * S)
        elif self.anim == "right":
            x += int((1 - f) * 120 * S)
        elif self.anim == "pop":
            pass
        op = min(1.0, u * 1.6) if u < 1 else 1.0
        salida = min(1.0, max(0.0, (t1 - t) / 0.28))
        op *= salida
        img, al = self.img, self.alpha
        if self.anim == "pop" and u < 1:
            k = max(0.05, ease_back(u))
            nw, nh = max(1, int(img.width * k)), max(1, int(img.height * k))
            img = img.resize((nw, nh), Image.BILINEAR)
            al = img.getchannel("A")
            x += (self.img.width - nw) // 2
            y += (self.img.height - nh) // 2
        if op <= 0:
            return
        if op < 0.999:
            al = al.point(lambda v, o=op: int(v * o))
        frame.paste(img, (x, y), al)


# ---------------------------------------------------------------- zonas seguras TikTok
# La interfaz de TikTok tapa la parte de abajo (descripción, música) y la
# columna derecha (botones). Todo lo importante va dentro de este recuadro.
X0 = int(70 * S)
X1 = int(W - 140 * S)
ANCHO = X1 - X0
Y_TOP = int(200 * S)
Y_CONTENIDO_FIN = int(1330 * S)
Y_SUBT = int(1470 * S)


def cabecera(sp, txt, tema, t0=0.0, y=None):
    y = Y_TOP if y is None else y
    f = fuente("display", 96)
    for i, ln in enumerate(envolver(txt, f, ANCHO)):
        im, pad = sprite_texto(ln, f, BLANCO, brillo=TEMAS[tema]["a"])
        sp.append(Sprite(im, X0 - pad, y - pad, t0 + 0.08 * i, anim="left"))
        y += im.height - 2 * pad + 14 * S
    barra = caja(160 * S, 12 * S, relleno=TEMAS[tema]["a"] + (255,), radio=6)
    sp.append(Sprite(barra, X0 + 4 * S, y + 14 * S, t0 + 0.15, anim="left"))
    return y + 70 * S


def ajustar(txt, tipo, tam, ancho, minimo=22):
    f = fuente(tipo, tam)
    while medir(txt, f)[0] > ancho and tam > minimo:
        tam -= 2
        f = fuente(tipo, tam)
    return f


def construir_escena(esc, tema, tiempos, dur):
    """Devuelve (sprites, dinamico) para una escena.
    tiempos: inicio (s, relativo a la escena) de cada frase de locución."""
    T = TEMAS[tema]
    sp, dyn = [], []
    tipo = esc["t"]
    color_b = T["b"] if tema != "rojo" else (255, 220, 120)

    def t_item(k, n):
        idx = len(tiempos) - n + k
        return tiempos[max(0, idx)]

    def t_fin(k, n):
        idx = len(tiempos) - n + k + 1
        return tiempos[idx] if idx < len(tiempos) else dur

    def tarjeta(y, alto, t0, t1, col=None):
        sp.append(Sprite(caja(ANCHO, alto, relleno=(8, 6, 22, 210)), X0, y, t0, anim="left"))
        sp.append(Sprite(caja(ANCHO, alto, relleno=(0, 0, 0, 0), borde=col or T["a"], ancho_borde=5), X0, y, t0, t1, anim="pop", dur=0.3))
        sp.append(Sprite(caja(14 * S, alto, relleno=(col or T["a"]) + (255,), radio=6), X0, y, t0, anim="left"))

    if tipo == "title":
        f = fuente("display", 150)
        lineas = envolver(esc["head"], f, ANCHO)
        y = H * 0.24
        for i, ln in enumerate(lineas):
            im, pad = sprite_texto(ln, f, BLANCO, brillo=T["a"])
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y - pad, 0.1 + i * 0.12, anim="pop", dur=0.6))
            y += im.height - 2 * pad + 26 * S
        fs = fuente("semi", 50)
        y += 20 * S
        for ln in envolver(esc["sub"], fs, ANCHO - 40 * S):
            im, pad = sprite_texto(ln, fs, color_b)
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y - pad, 0.55, anim="up"))
            y += im.height - 2 * pad + 16 * S
        dyn.append(("linea", dict(y=y + 40 * S, t0=0.7, color=T["a"], cx=X0 + ANCHO / 2)))

    elif tipo == "card":
        fl = fuente("bold", 44)
        im, pad = sprite_texto(esc["head"], fl, T["a"])
        y0 = H * 0.22
        sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y0 - pad, 0.05))
        f = fuente("display", 124)
        lineas = envolver(esc["text"], f, ANCHO - 90 * S)
        y = y0 + 120 * S
        alto = len(lineas) * 150 * S + 90 * S
        sp.append(Sprite(caja(ANCHO, alto, relleno=(8, 6, 20, 180), borde=T["a"]), X0, y - 45 * S, 0.0, anim="pop", dur=0.5))
        for i, ln in enumerate(lineas):
            im, pad = sprite_texto(ln, f, BLANCO, brillo=T["b"])
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y - pad, 0.25 + 0.1 * i, anim="up"))
            y += 150 * S

    elif tipo in ("bullets", "warning"):
        aviso = tipo == "warning"
        col = (255, 210, 60) if aviso else T["a"]
        y0 = Y_TOP
        if aviso:
            tri = Image.new("RGBA", (int(150 * S), int(135 * S)), (0, 0, 0, 0))
            dt = ImageDraw.Draw(tri)
            dt.polygon([(75 * S, 4 * S), (146 * S, 130 * S), (4 * S, 130 * S)], fill=(255, 210, 60, 255))
            dt.text((75 * S, 82 * S), "!", font=fuente("display", 92), fill=TINTA + (255,), anchor="mm")
            sp.append(Sprite(tri, X0, y0, 0.2, anim="pop", dur=0.6))
            y0 += 170 * S
        ytop = cabecera(sp, esc["head"], tema, y=y0)
        n = len(esc["items"])
        disponible = Y_CONTENIDO_FIN - ytop
        hueco = min(210 * S, disponible / n)
        alto = hueco - 24 * S
        ytop += max(0, disponible - n * hueco) * 0.3
        for k, it in enumerate(esc["items"]):
            y = ytop + k * hueco
            t0 = t_item(k, n)
            tarjeta(y, alto, t0, t_fin(k, n), col)
            for tam in (50, 46, 42):  # primero intenta que quepa en una línea
                f = fuente("semi", tam)
                lineas = envolver(it, f, ANCHO - 80 * S)
                if len(lineas) == 1:
                    break
            if len(lineas) > 1:
                f = fuente("semi", 44)
                lineas = envolver(it, f, ANCHO - 80 * S)
                if len(lineas) > 2 or len(lineas) * f.size * 1.22 > alto - 20 * S:
                    f = fuente("semi", 38)
                    lineas = envolver(it, f, ANCHO - 80 * S)
            lh = f.size * 1.22
            yt = y + (alto - lh * len(lineas)) / 2
            for j, ln in enumerate(lineas):
                im, pad = sprite_texto(ln, f)
                sp.append(Sprite(im, X0 + 44 * S - pad, yt + j * lh - pad + 4 * S, t0 + 0.08, anim="left"))

    elif tipo == "stat":
        fl = fuente("bold", 46)
        y = H * 0.20
        for ln in envolver(esc["head"], fl, ANCHO):
            im, pad = sprite_texto(ln, fl, T["a"])
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y - pad, 0.05))
            y += 64 * S
        dyn.append(("stat", dict(valor=esc["value"], t0=0.2, y=H * 0.30, cx=X0 + ANCHO / 2)))
        fs = fuente("semi", 44)
        y = H * 0.55
        for ln in envolver(esc["label"], fs, ANCHO - 40 * S):
            im, pad = sprite_texto(ln, fs, BLANCO)
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y - pad, 0.8))
            y += 62 * S

    elif tipo == "table":
        # en vertical, cada fila es una tarjeta: etiqueta arriba, valor grande abajo
        ytop = cabecera(sp, esc["head"], tema)
        rows = esc["rows"]
        n = len(rows)
        hueco = min(200 * S, (Y_CONTENIDO_FIN - ytop) / n)
        alto = hueco - 22 * S
        ytop += max(0, (Y_CONTENIDO_FIN - ytop) - n * hueco) * 0.3
        for k, (a, b) in enumerate(rows):
            y = ytop + k * hueco
            t0 = t_item(k, n)
            tarjeta(y, alto, t0, t_fin(k, n))
            fa = ajustar(a, "semi", 40, ANCHO - 80 * S)
            fb = ajustar(b, "display", 64, ANCHO - 80 * S)
            im, pad = sprite_texto(a, fa, (225, 225, 235))
            ha = im.height - 2 * pad
            im2, pad2 = sprite_texto(b, fb, color_b)
            hb = im2.height - 2 * pad2
            yt = y + (alto - ha - hb - 14 * S) / 2
            sp.append(Sprite(im, X0 + 44 * S - pad, yt - pad, t0 + 0.05, anim="left"))
            sp.append(Sprite(im2, X0 + 44 * S - pad2, yt + ha + 14 * S - pad2, t0 + 0.12, anim="left"))

    elif tipo == "compare":
        ytop = cabecera(sp, esc["head"], tema)
        cols = esc["cols"]
        rows = esc["rows"]
        n = len(rows)
        hueco = min(220 * S, (Y_CONTENIDO_FIN - ytop) / n)
        alto = hueco - 22 * S
        ytop += max(0, (Y_CONTENIDO_FIN - ytop) - n * hueco) * 0.3
        mitad = (ANCHO - 88 * S) / 2
        for k, (feat, l, r) in enumerate(rows):
            y = ytop + k * hueco
            t0 = t_item(k, n)
            tarjeta(y, alto, t0, t_fin(k, n))
            ff = ajustar(feat.upper(), "bold", 34, ANCHO - 80 * S)
            im, pad = sprite_texto(feat.upper(), ff, T["a"], sombra=False)
            sp.append(Sprite(im, X0 + 44 * S - pad, y + 20 * S - pad, t0 + 0.05, anim="left"))
            for c, (et, val) in enumerate(((cols[0], l), (cols[1], r))):
                x = X0 + 44 * S + c * (mitad + 20 * S)
                fe = fuente("med", 28)
                im, pad = sprite_texto(et, fe, (190, 190, 205), sombra=False)
                sp.append(Sprite(im, x - pad, y + 70 * S - pad, t0 + 0.1, anim="left"))
                fv = fuente("semi", 38)
                lineas = envolver(val, fv, mitad - 10 * S)
                if len(lineas) > 2:
                    fv = fuente("semi", 30)
                    lineas = envolver(val, fv, mitad - 10 * S)
                for j, ln in enumerate(lineas[:3]):
                    im, pad = sprite_texto(ln, fv, BLANCO)
                    sp.append(Sprite(im, x - pad, y + 108 * S + j * fv.size * 1.15 - pad, t0 + 0.12, anim="left"))

    elif tipo == "twocol":
        # dos paneles apilados: arriba uno, abajo el otro
        ytop = cabecera(sp, esc["head"], tema)
        gap = 30 * S
        ph = (Y_CONTENIDO_FIN - ytop - gap) / 2
        colores = [T["a"], T["b"]]
        for c in range(2):
            y = ytop + c * (ph + gap)
            sp.append(Sprite(caja(ANCHO, ph, relleno=(8, 6, 22, 200), borde=colores[c]), X0, y, 0.1 + 0.15 * c, anim="up"))
            fh = ajustar(esc["cols"][c].upper(), "bold", 42, ANCHO - 80 * S)
            im, pad = sprite_texto(esc["cols"][c].upper(), fh, colores[c])
            sp.append(Sprite(im, X0 + 40 * S - pad, y + 34 * S - pad, 0.25 + 0.15 * c, anim="up"))
        cuenta = [0, 0]
        n = len(esc["items"])
        f = fuente("semi", 44)
        for k, (c, txt) in enumerate(esc["items"]):
            y = ytop + c * (ph + gap) + 120 * S + cuenta[c] * 110 * S
            cuenta[c] += 1
            t0 = t_item(k, n)
            if c == 0:
                ic = Image.new("RGBA", (int(56 * S), int(56 * S)), (0, 0, 0, 0))
                ImageDraw.Draw(ic).line([(6 * S, 30 * S), (22 * S, 46 * S), (50 * S, 10 * S)], fill=colores[c] + (255,), width=max(2, int(9 * S)), joint="curve")
                sp.append(Sprite(ic, X0 + 36 * S, y + 2 * S, t0, anim="pop", dur=0.4))
            else:
                ic, pad_ = sprite_texto("?", fuente("display", 56), colores[c])
                sp.append(Sprite(ic, X0 + 40 * S - pad_, y - 6 * S - pad_, t0, anim="pop", dur=0.4))
            lineas = envolver(txt, f, ANCHO - 160 * S)
            for j, ln in enumerate(lineas[:2]):
                im, pad = sprite_texto(ln, f)
                sp.append(Sprite(im, X0 + 110 * S - pad, y + j * 54 * S - pad, t0 + 0.05, anim="left"))

    elif tipo == "timeline":
        # línea de tiempo vertical
        ytop = cabecera(sp, esc["head"], tema)
        pts = esc["points"]
        n = len(pts)
        y0, y1 = ytop + 40 * S, Y_CONTENIDO_FIN - 40 * S
        paso = min(300 * S, (y1 - y0) / n)
        ys = [y0 + paso * (k + 0.4) for k in range(n)]
        xl = X0 + 50 * S
        ts = [t_item(k, n) for k in range(n)]
        dyn.append(("timeline", dict(x=xl, y0=y0 - 20 * S, y1=ys[-1] + paso * 0.5, ys=ys, ts=ts, color=T["a"])))
        for k, (anio, et) in enumerate(pts):
            fa = ajustar(anio, "display", 104, ANCHO - 140 * S)
            im, pad = sprite_texto(anio, fa, BLANCO, brillo=T["a"])
            ha = im.height - 2 * pad
            sp.append(Sprite(im, xl + 70 * S - pad, ys[k] - ha * 0.62 - pad, ts[k] + 0.1, anim="right"))
            fb = fuente("semi", 44)
            for j, ln in enumerate(envolver(et, fb, ANCHO - 150 * S)):
                im, pad = sprite_texto(ln, fb, color_b)
                sp.append(Sprite(im, xl + 74 * S - pad, ys[k] + ha * 0.55 + 6 * S + j * 52 * S - pad, ts[k] + 0.2, anim="right"))

    elif tipo == "map":
        ytop = cabecera(sp, esc["head"], tema)
        regs = esc["regions"]
        n = len(regs)
        bx, by, bw_, bh_ = X0, ytop - 20 * S, ANCHO, 560 * S
        pos = {"Mount Kalaga": (0.55, 0.10), "Port Gellhorn": (0.18, 0.22), "Ambrosia": (0.55, 0.40),
               "Grassrivers": (0.42, 0.64), "Vice City": (0.80, 0.68), "Leonida Keys": (0.50, 0.92)}
        P = [(bx + pos[r][0] * bw_, by + pos[r][1] * bh_) for r in regs]
        ts = [t_item(k, n) for k in range(n)]
        tf = [t_fin(k, n) for k in range(n)]
        dyn.append(("mapa", dict(caja=(bx, by, bw_, bh_), P=P, ts=ts, tf=tf, a=T["a"], b=T["b"])))
        nota, pad = sprite_texto("Esquema orientativo · no es el mapa oficial", fuente("med", 26), (220, 220, 230), sombra=False)
        sp.append(Sprite(nota, bx + 20 * S - pad, by + bh_ + 10 * S - pad, 0.5))
        # lista de regiones en 2 columnas bajo el mapa
        yl = by + bh_ + 70 * S
        colw = ANCHO / 2
        filas = (n + 1) // 2
        fh = min(120 * S, (Y_CONTENIDO_FIN + 40 * S - yl) / filas)
        for k, r in enumerate(regs):
            x = X0 + (k % 2) * colw
            y = yl + (k // 2) * fh
            sp.append(Sprite(caja(colw - 16 * S, fh - 14 * S, relleno=(8, 6, 22, 210)), x, y, ts[k], anim="up"))
            sp.append(Sprite(caja(colw - 16 * S, fh - 14 * S, relleno=(0, 0, 0, 0), borde=T["a"], ancho_borde=5), x, y, ts[k], tf[k], anim="pop", dur=0.3))
            num, pad = sprite_texto(str(k + 1), fuente("display", 52), T["a"])
            sp.append(Sprite(num, x + 20 * S - pad, y + (fh - 14 * S - (num.height - 2 * pad)) / 2 - pad, ts[k], anim="up"))
            fr = ajustar(r, "semi", 36, colw - 110 * S)
            im, pad = sprite_texto(r, fr)
            sp.append(Sprite(im, x + 76 * S - pad, y + (fh - 14 * S - (im.height - 2 * pad)) / 2 - pad, ts[k] + 0.05, anim="up"))

    elif tipo == "cta":
        f = fuente("display", 170)
        y = H * 0.20
        for i, ln in enumerate(["¡SÍGUEME!"]):
            im, pad = sprite_texto(ln, f, BLANCO, brillo=T["a"])
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y - pad, 0.1, anim="pop", dur=0.6))
        fs = fuente("semi", 48)
        for j, ln in enumerate(envolver(f"{CANAL} · {LEMA}", fs, ANCHO)):
            im, pad = sprite_texto(ln, fs, color_b)
            sp.append(Sprite(im, X0 + (ANCHO - (im.width - 2 * pad)) / 2 - pad, y + 230 * S + j * 62 * S - pad, 0.4, anim="up"))
        dyn.append(("boton", dict(cx=X0 + ANCHO / 2, y=H * 0.42, t0=0.6, color=T["a"])))
        # iconos de guardar / comentar / compartir
        for i, et in enumerate(["GUARDA", "COMENTA", "COMPARTE"]):
            x = X0 + i * (ANCHO / 3)
            sp.append(Sprite(caja(ANCHO / 3 - 20 * S, 110 * S, relleno=(8, 6, 22, 200), borde=[T["a"], T["b"], (255, 216, 50)][i]), x, H * 0.56, 1.0 + 0.2 * i, anim="pop", dur=0.45))
            fe = ajustar(et, "black", 40, ANCHO / 3 - 50 * S)
            im, pad = sprite_texto(et, fe, BLANCO, sombra=False)
            sp.append(Sprite(im, x + (ANCHO / 3 - 20 * S - (im.width - 2 * pad)) / 2 - pad, H * 0.56 + (110 * S - (im.height - 2 * pad)) / 2 - pad, 1.05 + 0.2 * i, anim="pop", dur=0.45))
    return sp, dyn


def pintar_dinamico(frame, d, items, t, dur, tema):
    for tipo, p in items:
        if tipo == "linea":
            u = ease_out((t - p["t0"]) / 0.8)
            if u > 0:
                w = 420 * S * u
                d.rounded_rectangle((p["cx"] - w / 2, p["y"], p["cx"] + w / 2, p["y"] + 10 * S), radius=int(5 * S), fill=p["color"])
        elif tipo == "stat":
            u = ease_out((t - p["t0"]) / 1.2)
            if u <= 0:
                continue
            v = p["valor"]
            import re as _re
            m = _re.search(r"\d+", v)
            txt = v
            if m:
                num = int(m.group())
                txt = v[:m.start()] + str(int(round(num * u))) + v[m.end():]
            f = ajustar(v, "display", 290, ANCHO)
            tw = medir(v, f)[0]
            x = p["cx"] - tw / 2
            d.text((x + 8 * S, p["y"] + 10 * S), txt, font=f, fill=TEMAS[tema]["a"])
            d.text((x, p["y"]), txt, font=f, fill=BLANCO)
        elif tipo == "timeline":
            u = ease_out((t - 0.1) / max(0.5, p["ts"][-1] + 0.6))
            y1 = p["y0"] + (p["y1"] - p["y0"]) * u
            x = p["x"]
            d.rounded_rectangle((x - 4 * S, p["y0"], x + 4 * S, max(p["y0"] + 1, y1)), radius=int(4 * S), fill=(255, 255, 255))
            for y, t0 in zip(p["ys"], p["ts"]):
                k = ease_back((t - t0) / 0.4)
                if t >= t0:
                    r = 24 * S * max(0, k)
                    d.ellipse((x - r, y - r, x + r, y + r), fill=p["color"], outline=(255, 255, 255), width=max(1, int(4 * S)))
        elif tipo == "mapa":
            bx, by, bw_, bh_ = p["caja"]
            d.rounded_rectangle((bx, by, bx + bw_, by + bh_), radius=int(30 * S), fill=(8, 6, 22, 255), outline=p["a"], width=max(1, int(3 * S)))
            pen = [(0.08, 0.04), (0.92, 0.04), (0.90, 0.30), (0.88, 0.55), (0.93, 0.78), (0.80, 0.86), (0.62, 0.82),
                   (0.40, 0.72), (0.30, 0.52), (0.22, 0.34), (0.06, 0.30)]
            d.polygon([(bx + a * bw_, by + b * bh_) for a, b in pen], fill=(34, 22, 60), outline=(90, 70, 140))
            for i in range(9):
                cx, cy = bx + (0.38 + i * 0.05) * bw_, by + (0.90 + 0.02 * math.sin(i)) * bh_
                d.ellipse((cx - 10 * S, cy - 6 * S, cx + 10 * S, cy + 6 * S), fill=(34, 22, 60), outline=(90, 70, 140))
            for k, ((x, y), t0, t1) in enumerate(zip(p["P"], p["ts"], p["tf"])):
                if t < t0:
                    d.ellipse((x - 9 * S, y - 9 * S, x + 9 * S, y + 9 * S), fill=(90, 70, 140))
                    continue
                activo = t0 <= t < t1
                if activo:
                    ph = ((t - t0) % 1.2) / 1.2
                    r = (30 + 60 * ph) * S
                    a = int(255 * (1 - ph))
                    d.ellipse((x - r, y - r, x + r, y + r), outline=p["a"] + (a,), width=max(1, int(5 * S)))
                r = (26 if activo else 18) * S
                d.ellipse((x - r, y - r, x + r, y + r), fill=p["a"] if activo else p["b"], outline=(255, 255, 255), width=max(1, int(3 * S)))
                d.text((x, y), str(k + 1), font=fuente("bold", 28 if activo else 22), fill=TINTA, anchor="mm")
        elif tipo == "boton":
            u = ease_back((t - p["t0"]) / 0.5)
            if u <= 0:
                continue
            pulso = 1 + 0.04 * math.sin(t * 5)
            w, h = 620 * S * u * pulso, 150 * S * u * pulso
            x, y = p["cx"] - w / 2, p["y"] - h / 2
            d.rounded_rectangle((x, y, x + w, y + h), radius=int(30 * S), fill=(254, 44, 85))
            if u > 0.8:
                d.text((x + w / 2, y + h / 2), "+ SEGUIR", font=fuente("black", 62), fill=BLANCO, anchor="mm")


# ---------------------------------------------------------------- subtítulos quemados
def trocear(texto, max_palabras=3, max_chars=20):
    palabras, trozos, act = texto.split(), [], []
    for p in palabras:
        act.append(p)
        largo = len(" ".join(act))
        if len(act) >= max_palabras or largo >= max_chars or p[-1] in ".,:;?!":
            trozos.append(" ".join(act)); act = []
    if act:
        trozos.append(" ".join(act))
    return trozos


def sprite_subtitulo(txt, acento):
    """Texto grande en mayúsculas con contorno; números y cifras en amarillo."""
    f = fuente("black", 70)
    palabras = txt.upper().split()
    lineas = envolver(" ".join(palabras), f, ANCHO - 20 * S)
    if len(lineas) > 2:
        f = fuente("black", 56)
        lineas = envolver(" ".join(palabras), f, ANCHO - 20 * S)
    lh = f.size * 1.18
    borde = int(8 * S)
    pad = int(20 * S)
    w = int(max(medir(l, f)[0] for l in lineas) + 2 * pad + 2 * borde)
    h = int(lh * len(lineas) + 2 * pad + 2 * borde)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    esp = medir("A A", f)[0] - 2 * medir("A", f)[0]
    for j, ln in enumerate(lineas):
        lw = medir(ln, f)[0]
        x = (w - lw) / 2
        y = pad + borde + j * lh
        for pal in ln.split():
            col = (255, 222, 60) if any(c.isdigit() for c in pal) else BLANCO
            d.text((x, y), pal, font=f, fill=col + (255,), stroke_width=borde, stroke_fill=(0, 0, 0, 255))
            x += medir(pal, f)[0] + esp
    return im


def construir_subtitulos(subt, acento):
    """subt: lista (inicio, fin, frase). Devuelve lista (t0, t1, sprite)."""
    out = []
    for a, b, frase in subt:
        trozos = trocear(frase)
        pesos = [len(x) + 3 for x in trozos]
        tot = sum(pesos)
        cur = a
        for tz, pz in zip(trozos, pesos):
            d_ = (b - a) * pz / tot
            out.append((cur, cur + d_, sprite_subtitulo(tz, acento)))
            cur += d_
    # sin huecos cortos entre trozos para que no parpadee
    for i in range(len(out) - 1):
        if out[i + 1][0] - out[i][1] < 0.45:
            out[i] = (out[i][0], out[i + 1][0], out[i][2])
    return out


def sprites_fijos(tema, video):
    T = TEMAS[tema]
    logo = Image.new("RGBA", (int(230 * S), int(62 * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(logo)
    d.rounded_rectangle((0, 0, logo.width - 1, logo.height - 1), radius=int(14 * S), fill=(10, 8, 24, 200), outline=T["a"] + (255,), width=max(1, int(3 * S)))
    d.text((logo.width / 2, logo.height / 2), CANAL, font=fuente("display", 38), fill=BLANCO, anchor="mm")
    fa = fuente("med", 24)
    lineas = envolver(AVISO, fa, ANCHO)
    aviso = Image.new("RGBA", (int(ANCHO), int(len(lineas) * 32 * S + 10 * S)), (0, 0, 0, 0))
    da = ImageDraw.Draw(aviso)
    for j, ln in enumerate(lineas):
        da.text((aviso.width / 2, j * 32 * S + 16 * S), ln, font=fa, fill=(230, 230, 240, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 255))
    return logo, aviso


# ---------------------------------------------------------------- montaje
GAP, ENTRADA, COLA = 0.25, 0.35, 0.55


def linea_temporal(v):
    """Genera voz y calcula tiempos de cada escena y frase."""
    escenas = []
    t = 0.0
    voz_total = []
    subt = []
    for i, esc in enumerate(v["escenas"]):
        tiempos, cur = [], (0.15 if i == 0 else ENTRADA)  # gancho inmediato
        clips = []
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
    total = t
    pista = np.zeros(int(total * audio.VOZ_SR) + audio.VOZ_SR, np.float32)
    for t0, clips in voz_total:
        for c0, a in clips:
            i = int((t0 + c0) * audio.VOZ_SR)
            pista[i:i + len(a)] += a
    return escenas, total, pista, subt


def fmt_srt(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{int((r % 1) * 1000):03d}"


def render_video(v, idx):
    os.makedirs(SALIDA, exist_ok=True)
    tema, slug = v["tema"], v["slug"]
    T = TEMAS[tema]
    print(f"[{slug}] voz…", flush=True)
    escenas, total, pista_voz, subt = linea_temporal(v)
    base = os.path.join(SALIDA, slug)
    os.makedirs(base, exist_ok=True)
    sufijo = "_preview" if PREVIEW else ""
    wav_voz = os.path.join(base, f"voz{sufijo}.wav")
    audio.sf.write(wav_voz, pista_voz, audio.VOZ_SR)

    print(f"[{slug}] música…", flush=True)
    mus = audio.musica(total + 1, semilla=idx, bpm=[96, 100, 104, 108, 98][idx % 5], tono="ACDEFG"[idx % 6])
    sw = audio.whoosh(idx)
    for e in escenas[1:]:
        i = int((e["t0"] - 0.25) * audio.MUS_SR)
        j = min(len(mus), i + len(sw))
        mus[i:j] += sw[: j - i] * 1.6
    wav_mus = os.path.join(base, f"musica{sufijo}.wav")
    audio.sf.write(wav_mus, mus, audio.MUS_SR)

    # SRT (por si se quiere subir aparte o reutilizar)
    with open(os.path.join(base, f"{slug}.es.srt"), "w", encoding="utf-8") as fsrt:
        for k, (a, b, txt) in enumerate(subt, 1):
            fsrt.write(f"{k}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{txt}\n\n")
    with open(os.path.join(base, "duracion.json"), "w") as fd:
        json.dump(dict(duracion=round(total, 1)), fd)

    print(f"[{slug}] fondo…", flush=True)
    bucle = bucle_fondo(v["fondo"], tema, idx)
    logo, aviso = sprites_fijos(tema, v)
    escena_objs = []
    for e in escenas:
        sp, dyn = construir_escena(e["esc"], tema, e["tiempos"], e["dur"])
        escena_objs.append((e, sp, dyn))
    subs = construir_subtitulos(subt, T["a"])

    mp4_tmp = os.path.join(base, f"video_mudo{sufijo}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "medium", "-crf", "20" if not PREVIEW else "26",
                           "-pix_fmt", "yuv420p", "-threads", "2", mp4_tmp], stdin=subprocess.PIPE)
    nframes = int(total * FPS)
    oscuro = Image.new("RGBA", (W, H), (6, 4, 16, 115))
    k_esc, k_sub = 0, 0
    for fi in range(nframes):
        t = fi / FPS
        while k_esc + 1 < len(escena_objs) and t >= escena_objs[k_esc + 1][0]["t0"]:
            k_esc += 1
        e, sp, dyn = escena_objs[k_esc]
        tl = t - e["t0"]
        off = int(MARGEN + MARGEN * 0.9 * math.sin(2 * math.pi * t / 47.0 + idx))
        bg = bucle[(fi // 2) % len(bucle)][:, off:off + W]
        frame = Image.fromarray(np.ascontiguousarray(bg)).convert("RGBA")
        frame.alpha_composite(oscuro)
        d = ImageDraw.Draw(frame)
        for p in range(22):
            px = (p * 397 + t * (20 + p % 7 * 9) * S) % W
            py = H - ((p * 211 + t * (15 + p % 5 * 7) * S) % H)
            r = (2 + p % 3) * S
            d.ellipse((px - r, py - r, px + r, py + r), fill=(T["a"] if p % 2 else T["b"]) + (140,))
        pintar_dinamico(frame, d, dyn, tl, e["dur"], tema)
        for s_ in sp:
            s_.pintar(frame, tl, e["dur"])
        # subtítulos
        while k_sub + 1 < len(subs) and t >= subs[k_sub + 1][0]:
            k_sub += 1
        s0, s1, simg = subs[k_sub]
        if s0 <= t < s1:
            u = (t - s0) / 0.12
            img = simg
            if u < 1:
                k = 0.85 + 0.15 * ease_back(u)
                img = simg.resize((max(1, int(simg.width * k)), max(1, int(simg.height * k))), Image.BILINEAR)
            frame.alpha_composite(img, (int(X0 + (ANCHO - img.width) / 2), int(Y_SUBT - img.height / 2)))
        # HUD: logo arriba a la izquierda (arriba a la derecha lo tapa la búsqueda de TikTok)
        frame.alpha_composite(logo, (X0, int(110 * S)))
        if t < 6:
            op = min(1, t / 0.4, (6 - t) / 0.4)
            al = aviso.copy()
            al.putalpha(aviso.getchannel("A").point(lambda v_, o=op: int(v_ * o)))
            frame.alpha_composite(al, (X0, int(Y_SUBT + 130 * S)))
        d.rectangle((0, 0, W * t / total, 8 * S), fill=T["a"])
        if k_esc > 0 and tl < 0.42:
            u = tl / 0.42
            x = -W * 0.4 + (W * 1.9) * ease_out(u)
            anchoc = 220 * S
            d.polygon([(x - anchoc, 0), (x + anchoc * 0.4, 0), (x - anchoc * 0.9, H), (x - anchoc * 2.3, H)], fill=T["a"] + (235,))
            d.polygon([(x - anchoc * 2.4, 0), (x - anchoc * 1.9, 0), (x - anchoc * 3.2, H), (x - anchoc * 3.7, H)], fill=T["b"] + (200,))
        ff.stdin.write(frame.convert("RGB").tobytes())
        if fi % (FPS * 30) == 0:
            print(f"[{slug}] {t:6.1f}/{total:.1f}s", flush=True)
    ff.stdin.close(); ff.wait()

    print(f"[{slug}] mezcla…", flush=True)
    final = os.path.join(base, f"{slug}{sufijo}.mp4")
    filtro = ("[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.32[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4_tmp, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    for tmp in (mp4_tmp, wav_voz, wav_mus):
        os.remove(tmp)
    print(f"[{slug}] OK → {final} ({total:.1f}s)", flush=True)
    return total


if __name__ == "__main__":
    filtros = sys.argv[1:]
    for i, v in enumerate(VIDEOS):
        if not filtros or any(v["slug"].startswith(f) for f in filtros):
            render_video(v, i)
