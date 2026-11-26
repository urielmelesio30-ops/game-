# -*- coding: utf-8 -*-
"""Versión 2D (dibujo plano tipo cartulina) de «¿Cómo cuenta células un equipo de hematología?».
Mismo guion, voz y datos que hematologia3d.py; se dibuja con PIL a 2× y se reduce (bordes suaves).
Uso: python hematologia2d.py [--muestra]"""
import math, os, subprocess, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import hematologia3d as H3
from futbol3d import fuente, etiqueta, texto_arriba
from PIL import Image, ImageDraw

RAIZ = os.path.dirname(AQUI)
SLUG = "40-como-cuenta-celulas-hematologia-2d"
SALIDA = os.path.join(RAIZ, "salida", SLUG)
FPS, W, H, S = 30, 1080, 1920, 2
OL = (46, 34, 70)
PULSOS = []


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def rebote(u):
    u = max(0.0, min(1.0, u))
    return 1 - math.cos(u * math.pi * 2.5) * math.exp(-u * 5) if u < 1 else 1.0


def mezcla(a, b, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(x + (y - x) * u) for x, y in zip(a, b))


# ------------------------------------------------------------- lienzo a 2×
class D:
    def __init__(self, fondo):
        self.im = Image.new("RGB", (W * S, H * S), fondo)
        self.d = ImageDraw.Draw(self.im)

    def circ(self, x, y, r, fill, ol=OL, w=5, ry=None):
        ry = r if ry is None else ry
        self.d.ellipse(((x - r) * S, (y - ry) * S, (x + r) * S, (y + ry) * S), fill=fill, outline=ol, width=w * S if ol else 0)

    def rect(self, x0, y0, x1, y1, fill, r=18, ol=OL, w=5):
        self.d.rounded_rectangle((x0 * S, y0 * S, x1 * S, y1 * S), radius=r * S, fill=fill, outline=ol, width=w * S if ol else 0)

    def linea(self, pts, fill, w=6):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(w * S), joint="curve")
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse(((x - w / 2) * S, (y - w / 2) * S, (x + w / 2) * S, (y + w / 2) * S), fill=fill)

    def poli(self, pts, fill, ol=OL, w=5):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=ol, width=w * S if ol else 0)

    def texto(self, txt, x, y, tam, fill, anchor="mm"):
        self.d.text((x * S, y * S), txt, font=fuente(tam * S), fill=fill, anchor=anchor)

    def check(self, x, y, s, col=(60, 200, 100)):
        pts = [(x - 40 * s, y), (x - 10 * s, y + 32 * s), (x + 46 * s, y - 36 * s)]
        self.linea(pts, OL, 30 * s)
        self.linea(pts, col, 18 * s)


def fondo(d, arriba, abajo, mesa=1480):
    a = np.array(arriba, np.float32); b = np.array(abajo, np.float32)
    g = (a[None, :] + (b - a)[None, :] * np.linspace(0, 1, H * S)[:, None]).astype(np.uint8)
    d.im.paste(Image.fromarray(np.repeat(g[:, None, :], W * S, 1)))
    d.d = ImageDraw.Draw(d.im)
    for k in range(-2, 14):                      # lunares suaves del papel
        for j in range(0, 22):
            x, y = k * 110 + (j % 2) * 55, j * 110
            c = tuple(min(255, v + 10) for v in mezcla(arriba, abajo, y / H))
            d.circ(x, y, 14, c, ol=None)
    d.rect(-40, mesa, W + 40, H + 40, mezcla(abajo, (120, 90, 70), 0.25), r=40, ol=OL, w=5)


# ------------------------------------------------------------- personajes
def ojos(d, x, y, sep, r, t, mira=(1, 0), enfado=False):
    parpadeo = (t * 0.7 + x * 0.001) % 3.1 < 0.12
    for s in (-1, 1):
        ex = x + s * sep
        if parpadeo:
            d.linea([(ex - r, y), (ex + r, y)], OL, max(3, r * 0.35))
            continue
        d.circ(ex, y, r, (255, 255, 255), w=3)
        d.circ(ex + mira[0] * r * 0.35, y + mira[1] * r * 0.35, r * 0.5, (25, 22, 34), ol=None)
        d.circ(ex + mira[0] * r * 0.35 - r * 0.15, y - r * 0.2, r * 0.16, (255, 255, 255), ol=None)
        if enfado:
            d.linea([(ex - s * r * 1.2, y - r * 1.6), (ex + s * r * 0.6, y - r * 0.9)], OL, r * 0.45)


def celula(d, tipo, x, y, t, s=1.0, mira=(1, 0)):
    y = y - abs(math.sin(t * 9 + x * 0.01)) * 8 * s
    if tipo == "rojo":
        r = 52 * s
        d.circ(x, y, r, (228, 62, 72))
        d.circ(x, y + 4 * s, r * 0.55, (196, 40, 54), ol=None, ry=r * 0.45)
        d.circ(x - r * 0.45, y - r * 0.5, r * 0.14, (255, 170, 170), ol=None)
        ojos(d, x, y - r * 0.12, r * 0.3, r * 0.19, t, mira)
    elif tipo == "plaqueta":
        d.circ(x, y, 22 * s, (200, 156, 228), w=4, ry=15 * s)
    elif tipo == "rara":
        r = 78 * s
        pts = []
        for k in range(28):
            a = k / 28 * 2 * math.pi + t * 0.8
            rr = r * (1.3 if k % 2 == 0 else 1.0)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        d.poli(pts, (146, 82, 196))
        d.circ(x, y + r * 0.35, r * 0.45, (90, 40, 130), ol=None, ry=r * 0.3)
        ojos(d, x, y - r * 0.15, r * 0.32, r * 0.2, t, mira, enfado=True)
    else:
        r = 66 * s
        d.circ(x, y, r, (246, 242, 252))
        nuc = (136, 78, 186)
        if tipo == "linfo":
            d.circ(x, y + r * 0.2, r * 0.56, nuc, w=3, ry=r * 0.5)
        elif tipo == "mono":
            d.circ(x, y + r * 0.35, r * 0.6, nuc, w=3, ry=r * 0.32)
        else:
            for dx in (-0.4, 0.0, 0.4):
                d.circ(x + dx * r, y + r * (0.42 if dx else 0.52), r * 0.24, nuc, w=3)
        if tipo == "neutro":
            for k in range(9):
                a = k * 2.4
                d.circ(x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.5 - r * 0.05, 5 * s, (240, 150, 190), ol=None)
        ojos(d, x, y - r * 0.28, r * 0.3, r * 0.18, t, mira)


CEL = 1.35
RADIO = {k: v * CEL for k, v in dict(rojo=52, plaqueta=22, rara=78, blanco=66, neutro=66, linfo=66, mono=66).items()}
ALTO = dict(rojo=70, plaqueta=28, blanco=150, neutro=130, linfo=95, mono=160, rara=175)
COLP = dict(rojo=(228, 62, 72), plaqueta=(200, 156, 228), rara=(146, 82, 196))


def grafica(d, picos, t):
    """Tarjeta de pulsos arriba: picos (tc, tipo) que ya han pasado."""
    d.rect(90, 730, 990, 1000, (252, 250, 242))
    d.texto("PULSOS", 160, 765, 30, (170, 170, 190))
    d.linea([(130, 955), (950, 955)], (90, 90, 110), 5)
    for k, (tc, tipo) in enumerate(picos):
        if t < tc:
            continue
        u = ease((t - tc) / 0.12)
        x = 180 + k * 75
        h = ALTO[tipo] * u
        d.poli([(x - 26, 955), (x, 955 - h), (x + 26, 955)], COLP.get(tipo, (136, 78, 186)), w=4)


def desfile(d, lista, t, y, vel=330, para=None):
    """Dibuja las células de la lista [(tipo, tc)] que cruzan x=540 en tc."""
    for tipo, tc in lista:
        x = 540 + (t - tc) * vel
        if para is not None and tipo == "rara" and t > tc:
            x = 540 + math.sin(t * 40) * 4
        if -120 < x < W + 120:
            celula(d, tipo, x, y - RADIO[tipo] + 52 * CEL, t, s=CEL, mira=(1, 0))


# ------------------------------------------------------------- escenas
class Escenas:
    def __init__(self, T, total):
        self.T, self.total = T, total
        t0 = lambda i: T[i]["t0"]; d = lambda i: T[i]["dur"]
        self.opt0 = [("rojo", 0.0), ("rojo", d(0) * 0.4), ("blanco", d(0) * 0.75)]
        self.opt3 = [("neutro", t0(3) + d(3) * 0.18), ("linfo", t0(3) + d(3) * 0.42), ("mono", t0(3) + d(3) * 0.66), ("rojo", t0(3) + d(3) * 0.86)]
        self.imp = [("rojo", t0(1) + d(1) * 0.3), ("rojo", t0(1) + d(1) * 0.55), ("plaqueta", t0(1) + d(1) * 0.8),
                    ("plaqueta", t0(2) + d(2) * 0.15), ("rojo", t0(2) + d(2) * 0.32), ("blanco", t0(2) + d(2) * 0.55)]
        tg = t0(10) + d(10) * 0.62
        self.tg = tg
        self.alar = [("rojo", t0(10) + d(10) * 0.1), ("blanco", t0(10) + d(10) * 0.32), ("rara", tg - 0.05)]
        for tc, _ in [(tc, ti) for ti, tc in self.opt0 + self.opt3 + self.imp + self.alar]:
            PULSOS.append(max(0.0, tc))
        # corriente de la impedancia: avanza solo cuando el agujero está libre
        n = int(total * FPS) + 2
        s, self.corr = 0.0, np.zeros(n)
        for f in range(n):
            t = f / FPS
            tapado = any(abs((t - tc) * 300) < RADIO[ti] + 30 for ti, tc in self.imp)
            if not tapado:
                s += 260 / FPS
            self.corr[f] = s
        rng = np.random.default_rng(3)
        self.pilaR = [(rng.uniform(-90, 90), rng.uniform(0, 1)) for _ in range(28)]
        self.pilaW = [(rng.uniform(-90, 90), rng.uniform(0, 1)) for _ in range(12)]

    def t0(self, i): return self.T[i]["t0"]
    def d(self, i): return self.T[i]["dur"]

    # --- óptico (0, 3) y alarma (10)
    def optico(self, d, t, lista, rayo=(255, 232, 110), alarma=False):
        fondo(d, (196, 226, 246), (160, 200, 236))
        grafica(d, [(max(0, tc), ti) for ti, tc in lista], t)
        d.rect(40, 1290, 1040, 1400, (126, 178, 232))
        d.rect(40, 1270, 1040, 1295, (98, 150, 214), r=10)
        d.rect(40, 1395, 1040, 1420, (98, 150, 214), r=10)
        cruza = [ti for ti, tc in lista if abs((t - tc) * 330) < RADIO[ti] and t >= 0]
        d.rect(510, 1340, 570, 1356, (60, 220, 120) if cruza or (alarma and t > self.tg) else (40, 100, 70), r=6, w=3)
        d.rect(470, 1030, 610, 1110, (96, 98, 112))
        d.rect(500, 1100, 580, 1122, (255, 238, 140), r=6, w=3)
        d.rect(522, 1122, 558, 1340, rayo, r=8, ol=None)
        d.rect(533, 1122, 547, 1340, (255, 255, 230), r=6, ol=None)
        desfile(d, lista, t, 1350, para=alarma)
        for ti, tc in lista:
            if 0 <= t - max(tc, 0) < 0.35 and ti != "rara":
                n = dict(neutro=6, mono=4, linfo=2, blanco=4).get(ti, 2)
                for k in range(n):
                    a = math.pi * (0.1 + 0.8 * k / max(1, n - 1)) + math.pi
                    for sg in (1, -1):
                        c, s_ = math.cos(a) * sg, math.sin(a)
                        d.linea([(540 + c * 85, 1290 + s_ * 85), (540 + c * 160, 1290 + s_ * 160)], rayo, 10)
        if alarma and t > self.tg:
            on = int((t - self.tg) / 0.2) % 2 == 0
            d.rect(120, 1150, 260, 1200, (70, 70, 84))
            d.circ(190, 1150, 60, (255, 70, 70) if on else (140, 40, 46))
            if on:
                for k in range(5):
                    a = math.pi * (1.1 + 0.2 * k)
                    d.linea([(190 + math.cos(a) * 80, 1150 + math.sin(a) * 80), (190 + math.cos(a) * 125, 1150 + math.sin(a) * 125)], (255, 90, 90), 10)

    def impedancia(self, d, t, fi):
        fondo(d, (226, 214, 246), (200, 186, 238))
        grafica(d, [(tc, ti) for ti, tc in self.imp], t)
        d.rect(40, 1120, 1040, 1500, (100, 166, 236))
        for k in range(6):
            d.linea([(80 + k * 170, 1160 + (k % 2) * 30), (140 + k * 170, 1160 + (k % 2) * 30)], (150, 200, 250), 6)
        s = self.corr[min(fi, len(self.corr) - 1)]
        for k in range(9):
            x = 160 + (s + k * 760 / 9) % 760
            d.circ(x, 1210, 12, (255, 214, 60), w=3)
        desfile(d, self.imp, t, 1380, vel=300)
        d.rect(515, 1080, 565, 1196, (204, 190, 164))
        d.rect(515, 1430, 565, 1520, (204, 190, 164))
        for x, col, sig in ((110, (226, 58, 64), "+"), (970, (60, 60, 72), "–")):
            d.rect(x - 20, 1110, x + 20, 1480, col)
            d.circ(x, 1105, 34, col)
            d.texto(sig, x, 1030, 110, col)

    def muestra(self, d, t):
        fondo(d, (204, 236, 214), (176, 222, 190))
        tl = t - self.t0(4); dd = self.d(4)
        d.rect(250, 780, 950, 1330, (204, 162, 110), r=30)
        d.texto("ANALIZADOR", 600, 840, 64, (120, 84, 52))
        d.rect(560, 930, 900, 1110, (40, 72, 62), r=16)
        if tl > dd * 0.72 or t > self.t0(5):
            d.texto("MEZCLANDO", 730, 1000, 48, (140, 255, 170))
            a = t * 9
            for k in range(3):
                b = a + k * 2.09
                d.linea([(730, 1060), (730 + math.cos(b) * 34, 1060 + math.sin(b) * 34)], (140, 255, 170), 8)
        d.rect(370, 1330, 430, 1350, (150, 150, 160), r=6)
        d.linea([(400, 1350), (400, 1450)], (200, 200, 212), 8)
        sube = ease(tl / (dd * 0.25)) * (1 - ease((tl - dd * 0.82) / (dd * 0.15)))
        top = 1760 - sube * 340
        nivel = 1 - 0.25 * ease((tl - dd * 0.4) / (dd * 0.3))
        d.rect(360, top, 440, top + 320, (230, 240, 246), r=26)
        d.rect(368, top + 320 - 250 * nivel, 432, top + 312, (190, 32, 46), r=22, ol=None)
        d.rect(352, top - 30, 448, top + 30, (160, 100, 214), r=10)

    def frascos(self, d, t, kb):
        fondo(d, (204, 236, 214), (176, 222, 190))
        d.rect(-30, 900, 250, 1240, (204, 162, 110), r=26)
        d.rect(40, 980, 200, 1080, (40, 72, 62), r=10)
        caminos = {"R": [(250, 1110), (470, 1110), (470, 1180)], "W": [(250, 1000), (820, 1000), (820, 1180)]}
        for c in caminos.values():
            d.linea(c, OL, 36); d.linea(c, (160, 210, 244), 24)
        t5, d5 = self.t0(5), self.d(5)
        llegadas = {"R": [], "W": []}

        def punto(c, u):
            L = [math.dist(c[i], c[i + 1]) for i in range(len(c) - 1)]
            s = u * sum(L)
            for i, l in enumerate(L):
                if s <= l:
                    k = s / l
                    return c[i][0] + (c[i + 1][0] - c[i][0]) * k, c[i][1] + (c[i + 1][1] - c[i][1]) * k
                s -= l
            return c[-1]
        viajes = [("R", "rojo" if k < 22 else "plaqueta", t5 + 0.1 + (k % 14) * d5 * 0.05) for k in range(28)]
        viajes += [("W", "rojo", t5 + 0.1 + d5 * 0.45 + k * d5 * 0.04) for k in range(9)]
        viajes += [("W", "blanco", t5 + 0.1 + d5 * 0.5 + k * d5 * 0.12) for k in range(3)]
        for j, ti, ts in viajes:
            u = (t - ts) / 0.9
            if 0 <= u < 1:
                x, y = punto(caminos[j], u)
                r = dict(rojo=15, plaqueta=8, blanco=22)[ti]
                d.circ(x, y - 4, r, COLP.get(ti, (246, 242, 252)), w=3)
            elif u >= 1:
                llegadas[j].append(ti)
        # cuentagotas y gotas
        nivel = {"R": 0.0, "W": 0.0}
        gotas = [("R", self.t0(6) + 0.2 + k * self.d(6) * 0.15, (110, 170, 236)) for k in range(5)]
        gotas += [("W", self.t0(6) + self.d(6) * 0.5, (110, 170, 236)), ("W", self.t0(7) + self.d(7) * 0.08, (110, 210, 130))]
        for j, tgo, col in gotas:
            x = 470 if j == "R" else 820
            u = (t - tgo) / 0.3
            if 0 <= u < 1:
                d.circ(x + 60, 900 + u * u * 300, 13, col, w=3, ry=17)
            if u >= 1 and col[1] == 170:
                nivel[j] += 1
        if kb >= 6:
            for j, x in (("R", 530), ("W", 880)):
                d.rect(x - 14, 760, x + 14, 880, (240, 240, 248), r=8)
                d.circ(x, 750, 30, (110, 170, 236))
        # frascos
        t7, d7 = self.t0(7), self.d(7)
        rojo_W = ease((t - t7 - d7 * 0.3) / (d7 * 0.15))
        for j, x, et in (("R", 470, "ROJOS + PLAQ."), ("W", 820, "BLANCOS")):
            liq = (248, 214, 220) if j == "R" else mezcla((236, 230, 246), (200, 52, 66), rojo_W)
            top = 1270 - nivel[j] * 14
            d.rect(x - 130, 1170, x + 130, 1500, (224, 240, 248), r=30)
            d.rect(x - 116, top, x + 116, 1488, liq, r=24, ol=None)
            pila = self.pilaR if j == "R" else self.pilaW
            for k, ti in enumerate(llegadas[j]):
                if j == "W" and ti == "rojo":
                    tp = t7 + d7 * (0.25 + 0.02 * k)
                    if t > tp + 0.15:
                        continue
                    if t > tp:
                        u = (t - tp) / 0.15
                        px, py = x + pila[k][0], top + 40 + pila[k][1] * 150
                        d.circ(px, py, 15 + u * 30, None, ol=(255, 120, 120), w=4)
                        continue
                px, py = x + pila[k % len(pila)][0], top + 40 + pila[k % len(pila)][1] * 150 + math.sin(t * 3 + k) * 4
                r = dict(rojo=15, plaqueta=8, blanco=22)[ti]
                d.circ(px, py, r, COLP.get(ti, (246, 242, 252)), w=3)
            d.texto(et, x, 1540, 46, OL)
        # fotómetro de hemoglobina
        if kb == 7:
            d.rect(970, 1300, 1060, 1380, (96, 98, 112))
            d.rect(612, 1305, 668, 1375, (40, 100, 70))
            if t > t7 + d7 * 0.55:
                d.rect(668, 1328, 970, 1352, (255, 232, 110), r=8, ol=None)
                d.rect(560, 1180, 720, 1250, (255, 255, 255), r=14)
                d.texto("HB 14", 640, 1215, 44, (200, 40, 54))

    def tablero(self, d, t):
        fondo(d, (252, 236, 180), (246, 220, 150))
        d.rect(130, 740, 950, 1580, (204, 162, 110), r=30)
        t8, d8 = self.t0(8), self.d(8)
        fichas = [("GR 4,8", 0), ("GB 7,2", 0), ("PLQ 250", 0), ("HB 14", 0), ("HCT 42%", 1), ("VCM 88", 1), ("HCM 29", 1), ("CHCM 33", 1)]
        for i, (txt, calc) in enumerate(fichas):
            cx, cy = (340 if i % 2 == 0 else 740), 860 + (i // 2) * 190
            d.rect(cx - 175, cy - 72, cx + 175, cy + 72, (180, 138, 92), r=18, ol=None)
            tl = t8 + (0.05 + i * 0.05 if not calc else 0.3 + (i - 4) * 0.13) * d8
            if t < tl:
                continue
            y = cy - 700 * (1 - rebote((t - tl) / 0.45))
            d.rect(cx - 165, y - 64, cx + 165, y + 64, (250, 220, 110) if calc else (156, 206, 244), r=18)
            d.texto(txt, cx, y, 70, (70, 50, 34))

    def controles(self, d, t):
        fondo(d, (250, 214, 222), (244, 192, 206))
        t9, d9 = self.t0(9), self.d(9)
        for i, (et, liq, tapa) in enumerate((("BAJO", (244, 160, 160), (120, 200, 240)), ("NORMAL", (214, 70, 82), (120, 220, 140)),
                                             ("ALTO", (140, 22, 42), (250, 170, 90)))):
            x = 270 + i * 270
            tj = t9 + d9 * (0.22 + 0.2 * i)
            u = (t - tj) / 0.3
            y = -math.sin(u * math.pi) * 110 if 0 <= u < 1 else 0
            d.rect(x - 85, 1150 + y, x + 85, 1450 + y, (226, 238, 246), r=26)
            d.rect(x - 72, 1250 + y, x + 72, 1438 + y, liq, r=20, ol=None)
            d.rect(x - 95, 1110 + y, x + 95, 1170 + y, tapa, r=12)
            d.texto(et, x, 1530, 56, OL)
            if t > tj + 0.3:
                s = min(1.0, 0.4 + (t - tj - 0.3) / 0.15)
                d.check(x, 980, s * 1.3)

    def frotis(self, d, t):
        fondo(d, (226, 214, 246), (200, 186, 238))
        t11, d11 = self.t0(11), self.d(11)
        tl = t11 if t < t11 else t
        u = lambda a, b: ease((t - t11 - d11 * a) / (d11 * (b - a)))
        # microscopio
        d.rect(600, 1450, 1000, 1510, (240, 240, 248))
        d.linea([(930, 1460), (950, 1200), (900, 980)], OL, 74); d.linea([(930, 1460), (950, 1200), (900, 980)], (240, 240, 248), 60)
        d.rect(590, 1270, 960, 1300, (60, 60, 74), r=8)
        luz = t > t11 + d11 * 0.78
        d.rect(740, 1300, 800, 1330, (255, 236, 120) if luz else (120, 120, 130), r=6)
        d.poli([(720, 1180), (800, 1180), (850, 880), (770, 870)], (240, 240, 248))
        d.rect(762, 820, 862, 880, (60, 60, 74), r=10)
        d.rect(740, 1180, 780, 1240, (150, 150, 160), r=6)
        # portaobjetos con la gota y la extensión
        mueve = u(0.5, 0.74)
        px = 280 + (770 - 280) * mueve
        py = 1540 + (1258 - 1540) * mueve - math.sin(mueve * math.pi) * 200
        d.rect(px - 190, py - 22, px + 190, py + 22, (206, 234, 244), r=8, w=4)
        largo = u(0.18, 0.42)
        if t > t11 + d11 * 0.2:
            d.circ(px + 90 - largo * 110, py, 30 + largo * 120, (230, 118, 146), ol=None, ry=13)
        if t11 + d11 * 0.05 < t < t11 + d11 * 0.25:
            d.circ(px + 110, py - 22, 22, (196, 30, 46), w=4)
        if t < t11 + d11 * 0.5:
            ex = 420 - u(0.18, 0.42) * 300
            d.poli([(ex, 1520), (ex + 14, 1520), (ex + 74, 1380), (ex + 60, 1380)], (206, 234, 244), w=4)
        if t > t11 + d11 * 0.8:
            self.vista(d, 280, 1040, 200 * min(1, (t - t11 - d11 * 0.8) / 0.2), t)

    def vista(self, d, x, y, r, t, rara=True):
        if r < 10:
            return
        d.circ(x, y, r + 22, (60, 60, 74))
        d.circ(x, y, r, (250, 222, 228), ol=None)
        k = r / 200
        for dx, dy in ((-0.5, -0.4), (0.1, -0.6), (0.55, -0.15), (-0.6, 0.25), (0.2, 0.55), (-0.15, 0.1)):
            celula(d, "rojo", x + dx * r, y + dy * r, t, s=0.65 * k)
        if rara:
            celula(d, "rara", x + 0.35 * r, y + 0.2 * r, t, s=0.5 * k)
            d.circ(x + 0.35 * r, y + 0.2 * r, 70 * k, None, ol=(240, 50, 60), w=7)

    def final(self, d, t):
        fondo(d, (204, 236, 214), (176, 222, 190))
        t12, d12 = self.t0(12), self.d(12)
        self.vista(d, 540, 1170, 340, t)
        if t > t12 + d12 * 0.4:
            s = 1 + 0.6 * (1 - ease((t - t12 - d12 * 0.4) / 0.2))
            im = Image.new("RGBA", (560 * S, 170 * S), (0, 0, 0, 0))
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle((6 * S, 6 * S, 554 * S, 164 * S), radius=24 * S, outline=(40, 170, 90), width=14 * S)
            dd.text((280 * S, 86 * S), "VALIDADO", font=fuente(110 * S), fill=(40, 170, 90), anchor="mm")
            im = im.rotate(12, expand=True, resample=Image.BICUBIC)
            im = im.resize((int(im.width * s), int(im.height * s)), Image.BICUBIC)
            d.im.paste(im, (int(540 * S - im.width / 2), int(1380 * S - im.height / 2)), im)

    def dibujar(self, fi, kb):
        t = fi / FPS
        d = D((255, 255, 255))
        if kb in (0, 3):
            self.optico(d, t, self.opt0 if kb == 0 else self.opt3)
        elif kb in (1, 2):
            self.impedancia(d, t, fi)
        elif kb == 4:
            self.muestra(d, t)
        elif kb in (5, 6, 7):
            self.frascos(d, t, kb)
        elif kb == 8:
            self.tablero(d, t)
        elif kb == 9:
            self.controles(d, t)
        elif kb == 10:
            self.optico(d, t, self.alar, rayo=(255, 130, 130), alarma=True)
        elif kb == 11:
            self.frotis(d, t)
        else:
            self.final(d, t)
        return d.im


# ------------------------------------------------------------- montaje
def montar(T, total, muestra=False):
    E = Escenas(T, total)
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    grad = np.zeros((H, W, 4), np.uint8); grad[..., 3] = (np.clip(1 - np.arange(H) / 560, 0, 1) * 160)[:, None].astype(np.uint8)
    grad = Image.fromarray(grad, "RGBA")
    borde = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.minimum.reduce([xx, W - xx, yy, H - yy])
    borde[..., 0] = 240; borde[..., 1] = 40; borde[..., 2] = 50; borde[..., 3] = (np.clip(1 - dist / 90, 0, 1) * 200).astype(np.uint8)
    borde = Image.fromarray(borde, "RGBA")
    golpes = [b["t0"] + b["dur"] * b["golpe"] for b in T if "golpe" in b]
    n = int(total * FPS)
    cuadros = range(n) if not muestra else [int((b["t0"] + b["dur"] * 0.7) * FPS) for b in T]
    for fi in cuadros:
        tg = fi / FPS
        kb = max([i for i, b in enumerate(T) if b["t0"] <= tg], default=0)
        b = T[kb]; tl = tg - b["t0"]
        im = E.dibujar(fi, kb)
        z = 1 + 0.035 * tl / b["dur"] + (0.05 * (1 - ease(tl / 0.2)) if kb else 0)    # acercamiento lento + «pop» al cambiar
        cw, ch = W * S / z, H * S / z
        sx = sy = 0
        if any(0 <= tg - g < 0.3 for g in golpes):
            r = np.random.default_rng(fi); sx, sy = r.integers(-28, 29), r.integers(-28, 29)
        x0, y0 = (W * S - cw) / 2 + sx, (H * S - ch) / 2 + sy
        fr = im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")
        if kb == 10 and tg > E.tg and int((tg - E.tg) / 0.2) % 2 == 0:
            fr.alpha_composite(borde)
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
            if fi == int(T[0]["dur"] * 0.75 * FPS):
                Image.fromarray(arr).save(os.path.join(SALIDA, "_portada_base.png"))
                E.portada_im = im.resize((W, H), Image.LANCZOS)
    if muestra:
        return
    ff.stdin.close(); ff.wait()
    H3.audio_final(T, total, mp4, SALIDA=SALIDA, SLUG=SLUG, PULSOS=PULSOS)
    fr = E.portada_im.convert("RGBA")
    fr.alpha_composite(Image.new("RGBA", (W, H), (20, 10, 30, 80)))
    for txt, y, est, tam in (("¿CÓMO CUENTA", 420, "amarillo", 140), ("TUS CÉLULAS?", 620, "amarillo", 140), ("1 PULSO = 1 CÉLULA", 1580, "rojo", 90)):
        e = etiqueta(txt, est, tam); fr.alpha_composite(e, ((W - e.width) // 2, y))
    fr.convert("RGB").save(os.path.join(SALIDA, "portada.png"))
    os.remove(os.path.join(SALIDA, "_portada_base.png"))


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    T, total = H3.tiempos()
    print(f"[{SLUG}] {total:.1f}s", flush=True)
    montar(T, total, "--muestra" in sys.argv)
