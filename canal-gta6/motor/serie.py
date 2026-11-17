# -*- coding: utf-8 -*-
"""Caja de herramientas para la serie de 10 vídeos de curiosidades (estilo historia.py: marco neón,
pegatinas, subtítulos pixel). Fondos, iconos dibujados (originales), mapas, globo, contadores y plantillas
de escena reutilizables. Cada vídeo de serie_videos.py se monta con estas piezas."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import historia as Hm
_BASE = Hm.assets   # assets originales (mascota, avión…) antes de que otros módulos los sustituyan
import historia_scroll as HS
import historia_aviones as AV
from historia import A, C, W, H, ease, back, texto_grande, pegar, escalar, anton, persona, suave

CON = (30, 22, 38)
BL, AM, RO, VE, CI, RS, NA = (255, 255, 255), (255, 214, 80), (240, 70, 80), (90, 230, 120), (80, 220, 255), (255, 90, 140), (255, 150, 60)
OK = 8   # grosor de contorno


# ------------------------------------------------------------- fondos
def degradado(c1, c2, estrellas=0, semilla=1):
    im = Image.new("RGBA", (W, H), c1 + (255,))
    d = ImageDraw.Draw(im)
    for i in range(48):
        u = i / 47
        col = tuple(int(c1[k] * (1 - u) + c2[k] * u) for k in range(3))
        d.rectangle((0, H * u, W, H * u + H / 47 + 2), fill=col)
    rng = np.random.default_rng(semilla)
    for _ in range(estrellas):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.choice([2, 3, 4])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 230, int(rng.uniform(110, 255))))
    return im


FONDOS = dict(
    cielo=lambda: degradado((90, 160, 240), (180, 220, 250)),
    noche=lambda: degradado((16, 18, 48), (60, 40, 110), 120),
    espacio=lambda: degradado((8, 6, 24), (30, 16, 60), 260, 3),
    rojo=lambda: degradado((90, 20, 40), (30, 8, 20), 0),
    lab=lambda: degradado((16, 60, 70), (8, 24, 34), 0),
    nieve=lambda: degradado((120, 160, 220), (230, 240, 255), 0),
    papel=lambda: degradado((250, 238, 210), (230, 210, 170), 0),
    atardecer=lambda: degradado((255, 160, 110), (90, 70, 150), 0),
    morado=lambda: degradado((70, 50, 120), (24, 18, 50), 40, 5),
    verde=lambda: degradado((120, 200, 140), (40, 110, 90), 0),
    ciudad=lambda: Hm.fondo_ciudad(),
    ciudad_noche=lambda: Hm.fondo_ciudad(cielo=("cielo2", "noche")),
)


def fondo(nombre):
    k = "F_" + nombre
    if k not in A:
        A[k] = FONDOS[nombre]() if nombre in FONDOS else MAPAS[nombre]()
    return A[k]


def rayos(fr, tl, cx=W / 2, cy=800, col=(255, 255, 255, 40), n=14):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for k in range(n):
        a0 = k * 2 * math.pi / n + tl * 0.5
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + math.cos(a0) * 1600, cy + math.sin(a0) * 1600), (cx + math.cos(a1) * 1600, cy + math.sin(a1) * 1600)], fill=col)
    fr.alpha_composite(capa)


def particulas(fr, tl, col=(255, 255, 255), n=24, semilla=4):
    d = ImageDraw.Draw(fr)
    rng = np.random.default_rng(semilla)
    for i in range(n):
        x = (rng.uniform(0, W) + math.sin(tl + i) * 30) % W
        y = (rng.uniform(0, H) - tl * rng.uniform(40, 120)) % H
        r = rng.choice([3, 5, 7])
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(rng.uniform(80, 200)),))


# ------------------------------------------------------------- iconos (dibujos originales, 400x400)
def _ic(f, w=400, h=400):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        f(d, S, s)
    return suave(w, h, dib)


def ic_cohete(d, S, s):
    d.polygon(S(140, 300, 90, 370, 150, 340), fill=RO, outline=CON, width=OK * s)
    d.polygon(S(260, 300, 310, 370, 250, 340), fill=RO, outline=CON, width=OK * s)
    d.ellipse(S(140, 20, 260, 360), fill=(240, 240, 250), outline=CON, width=OK * s)
    d.ellipse(S(168, 120, 232, 184), fill=CI, outline=CON, width=OK * s)
    d.polygon(S(170, 350, 230, 350, 200, 400), fill=NA)


def ic_satelite(d, S, s):
    for x in (20, 260):
        d.rectangle(S(x, 160, x + 120, 240), fill=(70, 110, 200), outline=CON, width=OK * s)
        for k in range(1, 4):
            d.line(S(x + k * 30, 160, x + k * 30, 240), fill=CON, width=3 * s)
    d.rectangle(S(150, 140, 250, 260), fill=(220, 220, 230), outline=CON, width=OK * s)
    d.line(S(200, 140, 200, 80), fill=CON, width=8 * s); d.ellipse(S(180, 60, 220, 100), fill=RO, outline=CON, width=5 * s)


def ic_kremlin(d, S, s):
    d.rectangle(S(80, 260, 320, 390), fill=(200, 50, 50), outline=CON, width=OK * s)
    d.rectangle(S(150, 120, 250, 270), fill=(210, 60, 60), outline=CON, width=OK * s)
    d.polygon(S(140, 125, 260, 125, 200, 20), fill=(60, 140, 90), outline=CON, width=OK * s)
    d.ellipse(S(170, 160, 230, 220), fill=(250, 240, 220), outline=CON, width=6 * s)
    d.line(S(200, 190, 200, 170), fill=CON, width=5 * s); d.line(S(200, 190, 215, 195), fill=CON, width=5 * s)
    d.polygon(S(200, 0, 208, 18, 228, 18, 212, 30, 218, 50, 200, 38, 182, 50, 188, 30, 172, 18, 192, 18), fill=RO)
    for x in range(95, 320, 40):
        d.rectangle(S(x, 245, x + 20, 262), fill=(200, 50, 50), outline=CON, width=4 * s)
    d.rounded_rectangle(S(170, 310, 230, 390), radius=30 * s, fill=CON)


def ic_robot(d, S, s):
    d.line(S(200, 70, 200, 30), fill=CON, width=8 * s); d.ellipse(S(185, 15, 215, 45), fill=RO)
    d.rounded_rectangle(S(110, 70, 290, 190), radius=30 * s, fill=(190, 200, 215), outline=CON, width=OK * s)
    for x in (160, 240):
        d.ellipse(S(x - 22, 110, x + 22, 154), fill=CI, outline=CON, width=6 * s)
    d.rounded_rectangle(S(120, 200, 280, 340), radius=24 * s, fill=(170, 180, 200), outline=CON, width=OK * s)
    d.rectangle(S(170, 240, 230, 280), fill=VE, outline=CON, width=5 * s)
    d.line(S(120, 230, 60, 300), fill=CON, width=22 * s); d.line(S(280, 230, 340, 170), fill=CON, width=22 * s)
    d.line(S(160, 340, 130, 395), fill=CON, width=24 * s); d.line(S(240, 340, 280, 395), fill=CON, width=24 * s)


def ic_grafico(d, S, s):
    d.rectangle(S(30, 40, 370, 360), fill=(250, 250, 250), outline=CON, width=OK * s)
    for k in range(1, 4):
        d.line(S(30, 40 + k * 80, 370, 40 + k * 80), fill=(210, 210, 220), width=3 * s)
    d.line(S(50, 90, 130, 140, 190, 110, 260, 230, 340, 320), fill=RO, width=16 * s, joint="curve")
    d.polygon(S(340, 340, 360, 280, 300, 300), fill=RO)


def ic_pastillas(d, S, s):
    d.rounded_rectangle(S(40, 180, 230, 260), radius=40 * s, fill=(250, 250, 250), outline=CON, width=OK * s)
    d.rounded_rectangle(S(40, 180, 135, 260), radius=40 * s, fill=RS, outline=CON, width=OK * s)
    d.rectangle(S(250, 60, 300, 300), fill=(220, 240, 255), outline=CON, width=OK * s)
    d.rectangle(S(255, 170, 295, 295), fill=CI)
    d.line(S(275, 300, 275, 380), fill=CON, width=6 * s); d.rectangle(S(240, 40, 310, 60), fill=CON)


def ic_termometro(d, S, s):
    d.rounded_rectangle(S(160, 20, 240, 300), radius=40 * s, fill=(250, 250, 250), outline=CON, width=OK * s)
    d.ellipse(S(130, 260, 270, 400), fill=RO, outline=CON, width=OK * s)
    d.rectangle(S(185, 60, 215, 300), fill=RO)
    for y in range(60, 260, 40):
        d.line(S(240, y, 270, y), fill=CON, width=5 * s)


def ic_fuego(d, S, s):
    d.polygon(S(200, 10, 320, 170, 330, 270, 270, 380, 130, 380, 70, 270, 80, 160, 140, 200), fill=(255, 110, 40), outline=CON, width=OK * s)
    d.polygon(S(200, 160, 265, 270, 240, 360, 160, 360, 135, 280), fill=AM)


def ic_tanque(d, S, s):
    d.rounded_rectangle(S(30, 250, 370, 340), radius=45 * s, fill=(70, 80, 60), outline=CON, width=OK * s)
    for x in range(75, 340, 55):
        d.ellipse(S(x - 22, 272, x + 22, 316), fill=(120, 130, 110), outline=CON, width=5 * s)
    d.rounded_rectangle(S(60, 190, 330, 260), radius=16 * s, fill=(100, 120, 80), outline=CON, width=OK * s)
    d.rounded_rectangle(S(130, 130, 270, 200), radius=30 * s, fill=(110, 130, 90), outline=CON, width=OK * s)
    d.rectangle(S(260, 150, 395, 172), fill=(90, 100, 70), outline=CON, width=5 * s)


def ic_petrolero(d, S, s):
    d.polygon(S(10, 230, 390, 230, 350, 320, 50, 320), fill=(200, 50, 50), outline=CON, width=OK * s)
    d.rectangle(S(290, 150, 360, 232), fill=(240, 240, 240), outline=CON, width=OK * s)
    d.rectangle(S(320, 110, 340, 150), fill=CON)
    for x in range(40, 280, 60):
        d.ellipse(S(x, 200, x + 50, 240), fill=(150, 150, 160), outline=CON, width=5 * s)
    for k in range(6):   # cadena
        x = 30 + k * 60
        d.ellipse(S(x, 330, x + 70, 370), outline=(180, 180, 190), width=12 * s)
    d.rectangle(S(0, 320, 400, 400), fill=(50, 110, 190, 160))


def ic_urna(d, S, s):
    d.rectangle(S(70, 160, 330, 380), fill=(240, 240, 250), outline=CON, width=OK * s)
    d.rectangle(S(150, 150, 250, 170), fill=CON)
    d.polygon(S(170, 40, 260, 60, 240, 160, 150, 140), fill=(250, 250, 240), outline=CON, width=6 * s)
    d.line(S(180, 90, 200, 110, 235, 70), fill=VE, width=10 * s)
    d.rectangle(S(70, 250, 330, 290), fill=CI)


def ic_camara(d, S, s):
    for x in (110, 250):
        d.ellipse(S(x - 70, 30, x + 70, 170), fill=(60, 60, 70), outline=CON, width=OK * s)
        d.ellipse(S(x - 20, 80, x + 20, 120), fill=(150, 150, 160))
    d.rounded_rectangle(S(40, 170, 300, 330), radius=20 * s, fill=(40, 40, 50), outline=CON, width=OK * s)
    d.polygon(S(300, 210, 380, 170, 380, 330, 300, 290), fill=(70, 70, 80), outline=CON, width=OK * s)
    d.ellipse(S(70, 200, 110, 240), fill=RO)


def ic_bola(d, S, s):
    d.polygon(S(110, 330, 290, 330, 330, 390, 70, 390), fill=(150, 100, 60), outline=CON, width=OK * s)
    d.ellipse(S(60, 20, 340, 300), fill=(150, 120, 255), outline=CON, width=OK * s)
    d.ellipse(S(100, 60, 200, 140), fill=(220, 210, 255))
    for x, y in ((240, 150), (180, 210), (270, 230)):
        d.polygon(S(x, y - 18, x + 6, y, x, y + 18, x - 6, y), fill=BL)


def ic_lupa(d, S, s):
    d.line(S(250, 250, 370, 370), fill=(120, 80, 50), width=40 * s)
    d.ellipse(S(30, 30, 290, 290), fill=(200, 235, 255, 160), outline=CON, width=20 * s)
    d.arc(S(70, 70, 250, 250), 200, 260, fill=BL, width=14 * s)


def ic_revista(d, S, s):
    d.rectangle(S(60, 10, 340, 390), fill=(250, 250, 245), outline=CON, width=OK * s)
    d.rectangle(S(80, 30, 320, 80), fill=CON)
    d.text((112 * s, 34 * s), "2027", font=anton(40 * s), fill=BL)
    d.ellipse(S(90, 110, 310, 330), fill=(40, 40, 50))
    for k, (x, y, c) in enumerate(((150, 170, RO), (230, 160, BL), (190, 240, RO), (130, 260, BL), (250, 250, RO), (200, 190, BL))):
        d.rectangle(S(x - 18, y - 18, x + 18, y + 18), fill=c)
    for y in (345, 365):
        d.line(S(90, y, 310, y), fill=(150, 150, 150), width=6 * s)


def ic_atril(d, S, s):
    d.polygon(S(110, 170, 290, 170, 260, 390, 140, 390), fill=(120, 80, 60), outline=CON, width=OK * s)
    d.rectangle(S(90, 150, 310, 180), fill=(140, 100, 70), outline=CON, width=OK * s)
    d.ellipse(S(170, 230, 230, 290), fill=AM, outline=CON, width=6 * s)
    d.line(S(200, 150, 220, 60), fill=CON, width=8 * s); d.ellipse(S(200, 30, 245, 75), fill=(60, 60, 70), outline=CON, width=5 * s)


def ic_molino(d, S, s):
    d.polygon(S(190, 160, 210, 160, 225, 390, 175, 390), fill=(240, 240, 245), outline=CON, width=6 * s)
    for k in range(3):
        a = math.radians(-90 + k * 120)
        d.line(S(200, 160, 200 + math.cos(a) * 150, 160 + math.sin(a) * 150), fill=(240, 240, 245), width=22 * s)
    d.ellipse(S(185, 145, 215, 175), fill=CON)


def ic_sol(d, S, s):
    for k in range(12):
        a = k * math.pi / 6
        d.polygon(S(200 + math.cos(a) * 120, 200 + math.sin(a) * 120, 200 + math.cos(a + 0.2) * 190, 200 + math.sin(a + 0.2) * 190,
                    200 + math.cos(a + 0.4) * 120, 200 + math.sin(a + 0.4) * 120), fill=NA)
    d.ellipse(S(80, 80, 320, 320), fill=AM, outline=CON, width=OK * s)


def ic_gafas(d, S, s):
    d.rounded_rectangle(S(20, 120, 380, 300), radius=40 * s, fill=(250, 250, 250), outline=CON, width=OK * s)
    for x in (50, 220):
        d.ellipse(S(x, 150, x + 130, 270), fill=(30, 30, 40), outline=CON, width=6 * s)
        d.arc(S(x + 20, 165, x + 80, 215), 200, 280, fill=(120, 120, 140), width=8 * s)


def ic_hongo(d, S, s):
    d.rectangle(S(165, 180, 235, 360), fill=(200, 120, 80), outline=CON, width=OK * s)
    for x, y, r in ((120, 130, 80), (200, 100, 100), (280, 130, 80), (200, 160, 90)):
        d.ellipse(S(x - r, y - r, x + r, y + r), fill=(240, 150, 90), outline=CON, width=OK * s)
    for x, y, r in ((140, 120, 40), (220, 90, 50)):
        d.ellipse(S(x - r, y - r, x + r, y + r), fill=(255, 210, 140))
    d.ellipse(S(80, 330, 320, 400), fill=(220, 140, 90), outline=CON, width=OK * s)


def ic_tren(d, S, s):
    d.rounded_rectangle(S(40, 100, 360, 320), radius=40 * s, fill=(60, 110, 200), outline=CON, width=OK * s)
    for x in (80, 230):
        d.rectangle(S(x, 140, x + 90, 210), fill=(200, 230, 255), outline=CON, width=6 * s)
    d.rectangle(S(40, 240, 360, 260), fill=AM)
    for x in (110, 290):
        d.ellipse(S(x - 35, 290, x + 35, 360), fill=(50, 50, 60), outline=CON, width=6 * s)


def ic_barco(d, S, s):
    d.polygon(S(20, 250, 380, 250, 330, 340, 70, 340), fill=(60, 70, 90), outline=CON, width=OK * s)
    d.rectangle(S(120, 170, 300, 252), fill=(240, 240, 240), outline=CON, width=OK * s)
    d.rectangle(S(200, 110, 240, 172), fill=RO, outline=CON, width=6 * s)
    for x in range(140, 290, 40):
        d.ellipse(S(x, 195, x + 20, 215), fill=CI)


def ic_diploma(d, S, s):
    d.rectangle(S(40, 60, 360, 320), fill=(250, 240, 210), outline=CON, width=OK * s)
    for y in (110, 150, 190, 230):
        d.line(S(80, y, 320, y), fill=(170, 150, 120), width=8 * s)
    d.ellipse(S(260, 240, 340, 320), fill=RO, outline=CON, width=6 * s)
    d.polygon(S(270, 310, 290, 390, 300, 330, 320, 390, 330, 310), fill=RO)


def ic_oso(d, S, s):
    d.ellipse(S(60, 160, 340, 340), fill=(248, 248, 250), outline=CON, width=OK * s)
    d.ellipse(S(250, 90, 380, 220), fill=(248, 248, 250), outline=CON, width=OK * s)
    d.ellipse(S(260, 80, 300, 120), fill=(248, 248, 250), outline=CON, width=6 * s)
    d.ellipse(S(320, 135, 336, 151), fill=CON); d.ellipse(S(355, 170, 380, 190), fill=CON)
    for x in (100, 160, 240, 290):
        d.rounded_rectangle(S(x - 22, 300, x + 22, 390), radius=18 * s, fill=(248, 248, 250), outline=CON, width=6 * s)


def ic_tumba(d, S, s):
    d.rounded_rectangle(S(110, 60, 290, 360), radius=80 * s, fill=(170, 170, 185), outline=CON, width=OK * s)
    d.rectangle(S(190, 120, 210, 260), fill=CON); d.rectangle(S(150, 160, 250, 180), fill=CON)
    d.rectangle(S(40, 350, 360, 390), fill=(240, 245, 255), outline=CON, width=6 * s)


def ic_bebe(d, S, s):
    d.ellipse(S(110, 60, 290, 240), fill=C["piel"], outline=CON, width=OK * s)
    d.ellipse(S(155, 130, 175, 150), fill=CON); d.ellipse(S(225, 130, 245, 150), fill=CON)
    d.arc(S(170, 160, 230, 210), 20, 160, fill=CON, width=6 * s)
    d.rounded_rectangle(S(90, 220, 310, 380), radius=60 * s, fill=(150, 200, 255), outline=CON, width=OK * s)
    d.ellipse(S(185, 30, 215, 70), fill=AM)


def ic_virus(d, S, s):
    for k in range(10):
        a = k * math.pi / 5
        d.line(S(200, 200, 200 + math.cos(a) * 170, 200 + math.sin(a) * 170), fill=CON, width=10 * s)
        d.ellipse(S(200 + math.cos(a) * 170 - 20, 200 + math.sin(a) * 170 - 20, 200 + math.cos(a) * 170 + 20, 200 + math.sin(a) * 170 + 20), fill=RS, outline=CON, width=5 * s)
    d.ellipse(S(80, 80, 320, 320), fill=(120, 220, 140), outline=CON, width=OK * s)
    for x, y in ((150, 160), (240, 150), (200, 250)):
        d.ellipse(S(x - 20, y - 20, x + 20, y + 20), fill=(80, 170, 100))


def ic_prohibido(d, S, s):
    d.ellipse(S(20, 20, 380, 380), fill=BL, outline=RO, width=40 * s)
    d.line(S(80, 80, 320, 320), fill=RO, width=40 * s)


def ic_copo(d, S, s):
    for k in range(6):
        a = k * math.pi / 3
        x, y = 200 + math.cos(a) * 170, 200 + math.sin(a) * 170
        d.line(S(200, 200, x, y), fill=(230, 245, 255), width=20 * s)
        for r in (80, 130):
            xm, ym = 200 + math.cos(a) * r, 200 + math.sin(a) * r
            for da in (-0.6, 0.6):
                d.line(S(xm, ym, xm + math.cos(a + da) * 45, ym + math.sin(a + da) * 45), fill=(230, 245, 255), width=14 * s)


def ic_torre_perf(d, S, s):
    d.polygon(S(120, 390, 200, 20, 280, 390), outline=(90, 90, 110), width=14 * s)
    for k in range(1, 7):
        y = 20 + k * 52
        x = 80 * (y - 20) / 370
        d.line(S(200 - x, y, 200 + x, y), fill=(90, 90, 110), width=10 * s)
        d.line(S(200 - x, y, 200 + 80 * (y + 52 - 20) / 370, y + 52), fill=(130, 130, 150), width=5 * s)
    d.ellipse(S(185, 5, 215, 35), fill=RO)
    d.rectangle(S(60, 370, 340, 400), fill=(110, 90, 70))


def ic_tapa(d, S, s):
    d.ellipse(S(30, 200, 370, 330), fill=(90, 70, 50), outline=CON, width=OK * s)
    d.ellipse(S(90, 160, 310, 270), fill=(150, 90, 50), outline=CON, width=OK * s)
    for x, y in ((140, 200), (240, 190), (200, 240), (260, 230)):
        d.ellipse(S(x - 8, y - 8, x + 8, y + 8), fill=(110, 60, 30))
    d.ellipse(S(120, 180, 280, 250), outline=(100, 60, 30), width=6 * s)


def ic_altavoz(d, S, s):
    d.polygon(S(60, 150, 140, 150, 240, 60, 240, 340, 140, 250, 60, 250), fill=(80, 80, 90), outline=CON, width=OK * s)
    for r in (60, 110):
        d.arc(S(240 - r, 200 - r, 240 + r, 200 + r), -45, 45, fill=CON, width=12 * s)


def ic_conejo(d, S, s):
    for x, a in ((160, -10), (230, 10)):
        d.ellipse(S(x - 30, 10, x + 30, 190), fill=(250, 250, 250), outline=CON, width=OK * s)
        d.ellipse(S(x - 14, 40, x + 14, 160), fill=(255, 180, 200))
    d.ellipse(S(80, 220, 330, 390), fill=(250, 250, 250), outline=CON, width=OK * s)
    d.ellipse(S(110, 130, 300, 290), fill=(250, 250, 250), outline=CON, width=OK * s)
    d.ellipse(S(160, 190, 182, 214), fill=CON); d.ellipse(S(228, 190, 250, 214), fill=CON)
    d.ellipse(S(193, 225, 217, 245), fill=RS)
    d.ellipse(S(140, 230, 170, 250), fill=(255, 180, 200)); d.ellipse(S(240, 230, 270, 250), fill=(255, 180, 200))


def ic_fabrica(d, S, s):
    d.rectangle(S(40, 200, 360, 380), fill=(120, 110, 110), outline=CON, width=OK * s)
    d.polygon(S(40, 200, 120, 140, 120, 200, 200, 140, 200, 200, 280, 140, 280, 200), fill=(140, 130, 130), outline=CON, width=6 * s)
    d.rectangle(S(290, 60, 330, 200), fill=(110, 100, 100), outline=CON, width=6 * s)
    for x, y, r in ((320, 40, 30), (350, 10, 24)):
        d.ellipse(S(x - r, y - r, x + r, y + r), fill=(160, 220, 90, 220))
    d.ellipse(S(150, 250, 250, 340), fill=(240, 240, 230), outline=CON, width=5 * s)
    d.ellipse(S(170, 280, 192, 302), fill=CON); d.ellipse(S(208, 280, 230, 302), fill=CON)
    d.rectangle(S(185, 320, 215, 340), fill=CON)


def ic_chicle(d, S, s):
    d.rounded_rectangle(S(40, 120, 360, 280), radius=24 * s, fill=RS, outline=CON, width=OK * s)
    d.rectangle(S(40, 175, 360, 225), fill=BL)
    for x in (110, 200, 290):
        d.rounded_rectangle(S(x - 30, 70, x + 30, 130), radius=12 * s, fill=(255, 200, 220), outline=CON, width=5 * s)


def ic_metro(d, S, s):
    d.rounded_rectangle(S(40, 40, 360, 360), radius=60 * s, fill=(230, 235, 240), outline=CON, width=OK * s)
    d.rectangle(S(80, 90, 320, 200), fill=(120, 190, 240), outline=CON, width=6 * s)
    d.line(S(200, 90, 200, 360), fill=CON, width=8 * s)
    d.rectangle(S(40, 230, 360, 260), fill=RO)
    for x in (110, 290):
        d.ellipse(S(x - 25, 290, x + 25, 330), fill=AM, outline=CON, width=5 * s)


def ic_multa(d, S, s):
    d.polygon(S(80, 30, 330, 30, 330, 370, 300, 350, 270, 370, 240, 350, 210, 370, 180, 350, 150, 370, 120, 350, 80, 370), fill=(250, 250, 240), outline=CON, width=OK * s)
    d.text((115 * s, 60 * s), "MULTA", font=anton(60 * s), fill=RO)
    for y in (170, 210, 250):
        d.line(S(110, y, 300, y), fill=(170, 170, 170), width=8 * s)
    d.text((170 * s, 270 * s), "$$$", font=anton(50 * s), fill=CON)


def ic_farmacia(d, S, s):
    d.rounded_rectangle(S(40, 40, 360, 360), radius=40 * s, fill=(60, 190, 110), outline=CON, width=OK * s)
    d.rectangle(S(160, 90, 240, 310), fill=BL); d.rectangle(S(90, 160, 310, 240), fill=BL)


def ic_cansado(d, S, s):
    d.ellipse(S(60, 40, 340, 360), fill=C["piel"], outline=CON, width=OK * s)
    d.chord(S(60, 30, 340, 240), 180, 360, fill=(120, 80, 50))
    for x in (150, 250):
        d.ellipse(S(x - 36, 170, x + 36, 232), fill=(150, 120, 160))
        d.ellipse(S(x - 30, 160, x + 30, 215), fill=BL, outline=CON, width=5 * s)
        d.chord(S(x - 30, 160, x + 30, 215), 180, 360, fill=C["piel"], outline=CON, width=5 * s)
        d.ellipse(S(x - 8, 192, x + 8, 208), fill=CON)
    d.line(S(160, 290, 240, 290), fill=CON, width=8 * s)


def ic_trofeo(d, S, s):
    d.polygon(S(100, 40, 300, 40, 280, 200, 120, 200), fill=AM, outline=CON, width=OK * s)
    for x in (60, 300):
        d.arc(S(x, 60, x + 60, 160), 0, 360, fill=CON, width=10 * s)
    d.rectangle(S(180, 200, 220, 290), fill=AM, outline=CON, width=6 * s)
    d.rectangle(S(120, 290, 280, 350), fill=(140, 90, 50), outline=CON, width=OK * s)


def ic_agujero(d, S, s):
    for k in range(10):
        r = 190 - k * 8
        col = (255, int(120 + k * 12), 60 + k * 10)
        d.ellipse(S(200 - r, 200 - r * 0.32, 200 + r, 200 + r * 0.32), outline=col, width=10 * s)
    d.ellipse(S(115, 115, 285, 285), fill=(0, 0, 0), outline=(255, 200, 120), width=6 * s)
    d.chord(S(10, 140, 390, 260), 0, 180, outline=(255, 170, 90), width=14 * s)


def ic_astronauta(d, S, s):
    d.rounded_rectangle(S(120, 180, 280, 340), radius=40 * s, fill=(240, 240, 245), outline=CON, width=OK * s)
    d.ellipse(S(110, 40, 290, 210), fill=(240, 240, 245), outline=CON, width=OK * s)
    d.ellipse(S(140, 80, 260, 180), fill=(60, 90, 160), outline=CON, width=6 * s)
    d.arc(S(160, 95, 220, 140), 200, 280, fill=BL, width=8 * s)
    d.line(S(120, 210, 60, 270), fill=(240, 240, 245), width=36 * s); d.line(S(280, 210, 340, 150), fill=(240, 240, 245), width=36 * s)
    d.line(S(160, 330, 140, 390), fill=(240, 240, 245), width=40 * s); d.line(S(240, 330, 260, 390), fill=(240, 240, 245), width=40 * s)
    d.rectangle(S(170, 220, 230, 260), fill=RO)


def ic_puerta(d, S, s):
    d.rectangle(S(80, 20, 320, 400), fill=(120, 80, 50), outline=CON, width=OK * s)
    d.rectangle(S(105, 45, 295, 400), fill=(170, 115, 70), outline=CON, width=6 * s)
    for y in (70, 230):
        d.rectangle(S(130, y, 270, y + 130), outline=(130, 85, 50), width=8 * s)
    d.ellipse(S(255, 215, 285, 245), fill=AM, outline=CON, width=5 * s)


def ic_bombilla(d, S, s):
    d.ellipse(S(90, 20, 310, 240), fill=(255, 230, 110), outline=CON, width=OK * s)
    d.rectangle(S(150, 230, 250, 320), fill=(180, 180, 190), outline=CON, width=OK * s)
    for y in (255, 285):
        d.line(S(150, y, 250, y), fill=CON, width=6 * s)
    d.arc(S(140, 70, 260, 190), 200, 340, fill=NA, width=10 * s)


def ic_carpeta(d, S, s):
    d.polygon(S(30, 90, 160, 90, 190, 130, 370, 130, 370, 350, 30, 350), fill=(255, 190, 80), outline=CON, width=OK * s)
    d.rectangle(S(60, 150, 340, 330), fill=(255, 210, 110), outline=CON, width=5 * s)


def ic_estrella(d, S, s):
    pts = []
    for k in range(10):
        r = 190 if k % 2 == 0 else 80
        a = -math.pi / 2 + k * math.pi / 5
        pts += [200 + math.cos(a) * r, 200 + math.sin(a) * r]
    d.polygon(S(*pts), fill=AM, outline=CON, width=OK * s)


def ic_templo(d, S, s):
    d.polygon(S(30, 120, 200, 30, 370, 120), fill=(230, 200, 140), outline=CON, width=OK * s)
    d.rectangle(S(40, 120, 360, 150), fill=(220, 190, 130), outline=CON, width=6 * s)
    for x in range(60, 360, 60):
        d.rectangle(S(x, 150, x + 34, 350), fill=(235, 205, 150), outline=CON, width=6 * s)
    d.rectangle(S(20, 350, 380, 390), fill=(200, 170, 120), outline=CON, width=6 * s)


def ic_isla(d, S, s):
    d.ellipse(S(0, 250, 400, 380), fill=(60, 140, 220))
    d.ellipse(S(40, 220, 360, 340), fill=(240, 220, 150), outline=CON, width=6 * s)
    d.chord(S(80, 120, 320, 330), 180, 360, fill=(90, 180, 90), outline=CON, width=6 * s)
    d.line(S(260, 230, 290, 100), fill=(130, 90, 50), width=14 * s)
    for a in (-160, -120, -60, -20):
        r = math.radians(a)
        d.line(S(290, 100, 290 + math.cos(r) * 90, 100 + math.sin(r) * 60 + 30), fill=(60, 160, 70), width=16 * s)


ICONOS = {n[3:]: f for n, f in list(globals().items()) if n.startswith("ic_") and callable(f) and n != "ic_"}


def icono(nombre, k=1.0):
    clave = ("ICO", nombre, k)
    if clave not in A:
        if nombre == "cerebro":
            im = HS.cerebro(0.3)
        elif nombre == "avion":
            im = Hm.avion(1.4)
        elif nombre == "reloj" or nombre == "cama":
            im = HS.icono_bucle(nombre)
        elif nombre == "masc":
            im = escalar(A["masc"], 0.45)
        else:
            im = _ic(ICONOS[nombre])
        A[clave] = escalar(im, k) if k != 1 else im
    return A[clave]


def calendario(txt, sub="AGOSTO"):
    clave = ("CAL", txt, sub)
    if clave not in A:
        def f(d, S, s):
            d.rounded_rectangle(S(40, 50, 360, 380), radius=30 * s, fill=BL, outline=CON, width=OK * s)
            d.rounded_rectangle(S(40, 50, 360, 140), radius=30 * s, fill=RO, outline=CON, width=OK * s)
            d.rectangle(S(48, 110, 352, 140), fill=RO)
            for x in (120, 280):
                d.rounded_rectangle(S(x - 12, 20, x + 12, 80), radius=10 * s, fill=CON)
            fs = anton(56 * s)
            d.text(((200 * s - d.textlength(sub, font=fs) / 2), 60 * s), sub, font=fs, fill=BL)
            fb = anton(170 * s)
            d.text(((200 * s - d.textlength(txt, font=fb) / 2), 140 * s), txt, font=fb, fill=CON)
        A[clave] = _ic(f)
    return A[clave]


# ------------------------------------------------------------- mapas
MAPAS = {}


def mapa(nombre, la, lb, lat_ref, y_ref, desplaza=False):
    m = AV.Mapa(la, lb, lat_ref, y_ref, desplaza)
    MAPAS[nombre] = lambda: m.dibujar()
    MAPAS[nombre + "_obj"] = m
    return m


def pin(fr, m, lon, lat, tl, color=RO, etiqueta=None, dy=60):
    x, y = m.xy(lon, lat)
    Hm.chincheta_mapa(fr, x, y, tl, color)
    if etiqueta and tl > 0.3:
        pegar(fr, texto_grande(etiqueta, BL, 58), x, y + dy)


# ------------------------------------------------------------- plantillas de escena
def titulo(fr, txt, tl, col=BL, tam=130, y=320, golpe=0.0):
    if not txt:
        return
    u = back((tl - golpe) / 0.35)
    if tl >= golpe:
        pegar(fr, escalar(texto_grande(txt, col, tam), max(0.05, u)), W / 2, y)


def flota(tl, f=3.0, a=18):
    return a * math.sin(tl * f)


def E_icono(fondo_, ico, txt=None, col=BL, k=1.4, y=820, rayos_=True, extra=None, gira=0, sub=None, sub_col=AM):
    """Fondo + icono grande que entra con rebote y flota + título."""
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        if rayos_:
            rayos(fr, tl, cy=y)
        im = icono(ico) if isinstance(ico, str) else ico
        u = back(tl / 0.45)
        im = escalar(im, k * max(0.05, u))
        if gira:
            im = im.rotate(gira * math.sin(tl * 3), resample=Image.BICUBIC, expand=True)
        pegar(fr, im, W / 2, y + flota(tl))
        titulo(fr, txt, tl, col)
        if sub:
            titulo(fr, sub, tl, sub_col, 90, 1180, 0.4)
        if extra:
            extra(fr, ImageDraw.Draw(fr), tl, dur)
    return f


def E_varios(fondo_, icos, txt=None, col=BL, k=0.85, y=820, sub=None, sub_col=AM, rayos_=True):
    """Varios iconos que aparecen uno tras otro en abanico."""
    n = len(icos)
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        if rayos_:
            rayos(fr, tl, cy=y)
        for i, ico in enumerate(icos):
            t0 = i * min(0.45, dur * 0.5 / n)
            u = back((tl - t0) / 0.35)
            if u <= 0:
                continue
            x = W / 2 + (i - (n - 1) / 2) * min(330, 880 / max(1, n - 1) if n > 1 else 0)
            yy = y + (60 if (i % 2 and n > 2) else 0) + flota(tl + i, 3, 14)
            pegar(fr, escalar(icono(ico) if isinstance(ico, str) else ico, k * max(0.05, u)), x, yy)
        titulo(fr, txt, tl, col)
        if sub:
            titulo(fr, sub, tl, sub_col, 90, 1180, 0.5)
    return f


def E_texto(fondo_, l1, l2=None, c1=AM, c2=BL, temblor=True):
    """Frase en grande que golpea (para momentos clave)."""
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        rayos(fr, tl, col=(255, 255, 255, 30))
        sx = int(8 * math.sin(tl * 40) * max(0, 1 - tl / 0.4)) if temblor else 0
        pegar(fr, escalar(texto_grande(l1, c1, 160), max(0.05, back(tl / 0.35))), W / 2 + sx, 720)
        if l2:
            pegar(fr, escalar(texto_grande(l2, c2, 120), max(0.05, back((tl - 0.3) / 0.35))), W / 2 - sx, 900)
        particulas(fr, tl)
    return f


def E_contador(fondo_, valor, unidad, txt=None, col=AM, ico=None, decimales=0, prefijo=""):
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        rayos(fr, tl)
        if ico:
            pegar(fr, escalar(icono(ico), 0.9 * max(0.05, back(tl / 0.4))), W / 2, 640 + flota(tl))
        u = ease(tl / max(0.6, dur * 0.6))
        v = valor * u
        s = f"{v:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pegar(fr, texto_grande(prefijo + s, col, 190), W / 2, 980)
        pegar(fr, texto_grande(unidad, BL, 90), W / 2, 1150)
        titulo(fr, txt, tl)
    return f


def E_barras(fondo_, items, txt=None, abajo=False):
    """Barras comparativas. items=[(etiqueta, valor, color)]. abajo=True: crecen hacia abajo (profundidad)."""
    vmax = max(v for _, v, _ in items)
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        n = len(items)
        ancho = min(240, 900 / n - 40)
        for i, (et, v, c) in enumerate(items):
            x = W / 2 + (i - (n - 1) / 2) * (ancho + 50)
            h = 620 * v / vmax * ease((tl - i * 0.3) / 0.9)
            if abajo:
                y0 = 470
                d.rounded_rectangle((x - ancho / 2, y0, x + ancho / 2, y0 + max(4, h)), radius=16, fill=c, outline=CON, width=6)
                pegar(fr, texto_grande(et, BL, 50), x, y0 - 50)
                if h > 60:
                    pegar(fr, texto_grande(f"{v:,.0f} m".replace(",", "."), BL, 48), x, y0 + h + 40)
            else:
                y0 = 1180
                d.rounded_rectangle((x - ancho / 2, y0 - max(4, h), x + ancho / 2, y0), radius=16, fill=c, outline=CON, width=6)
                pegar(fr, texto_grande(et, BL, 50), x, y0 + 50)
        if abajo:
            d.rectangle((0, 462, W, 470), fill=(120, 90, 60))
        titulo(fr, txt, tl, y=300)
    return f


def E_vs(fondo_, a, b, la, lb, txt=None, ca=RO, cb=VE):
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        for i, (ico, lab, c) in enumerate(((a, la, ca), (b, lb, cb))):
            u = back((tl - i * 0.35) / 0.35)
            x = 280 + i * 520
            if u > 0:
                pegar(fr, escalar(icono(ico) if isinstance(ico, str) else ico, 0.95 * u), x, 780 + flota(tl + i))
                pegar(fr, escalar(texto_grande(lab, c, 70), u), x, 1060)
        pegar(fr, escalar(texto_grande("VS", AM, 130), max(0.05, back((tl - 0.2) / 0.3))), W / 2, 790)
        titulo(fr, txt, tl)
    return f


def E_persona(fondo_, ropa, txt=None, pelo="pelo", sombrero=None, bigote=False, ico=None, col=BL, anda=False, sub=None):
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        rayos(fr, tl, cy=900)
        br = (20 + 15 * math.sin(tl * 4), -20 - 15 * math.sin(tl * 4)) if not anda else (30 * math.sin(tl * 7), -30 * math.sin(tl * 7))
        p = persona(ropa, pelo=pelo, sombrero=sombrero, bigote=bigote, brazo=br, pierna=math.sin(tl * 7) if anda else 0)
        x = W / 2 - 150 if ico else W / 2
        if anda:
            x = -100 + (W + 200) * min(1, tl / dur)
        u = back(tl / 0.4)
        pegar(fr, escalar(p, 1.15 * max(0.05, u)), x, 900 - abs(math.sin(tl * 4)) * 10)
        if ico:
            pegar(fr, escalar(icono(ico), 0.8 * max(0.05, back((tl - 0.3) / 0.4))), W / 2 + 230, 800 + flota(tl))
        titulo(fr, txt, tl, col)
        if sub:
            titulo(fr, sub, tl, AM, 90, 1250, 0.4)
    return f


def E_mapa(nombre, pins=(), txt=None, ruta=None, col=BL, avion_=False, banda=None, extra=None):
    """Mapa con chinchetas [(lon, lat, etiqueta, color)], ruta [(lon, lat)...] dibujada con avión, o banda (lista de lon, lat, ancho px)."""
    m = MAPAS[nombre + "_obj"]
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(nombre))
        if banda:
            pts = [m.xy(lo, la) for lo, la in banda[0]]
            u = ease(tl / (dur * 0.8))
            n = max(2, int(len(pts) * u))
            capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(capa).line(pts[:n], fill=(10, 10, 30, 150), width=banda[1], joint="curve")
            fr.alpha_composite(capa)
            d.line(pts[:n], fill=AM, width=6, joint="curve")
        if ruta:
            pts = [m.xy(lo, la) for lo, la in ruta]
            u = ease((tl - 0.4) / (dur * 0.7))
            vis = AV.trazo(d, pts, u, AM, 12)
            if avion_ and len(vis) > 1 and tl > 0.4:
                AV.avion_en(fr, *vis[-1], AV.angulo(vis[-2], vis[-1]), 0.8)
        for i, p in enumerate(pins):
            pin(fr, m, p[0], p[1], tl - 0.2 * i, p[3] if len(p) > 3 else RO, p[2] if len(p) > 2 else None)
        if extra:
            extra(fr, d, tl, dur)
        titulo(fr, txt, tl, col)
    return f


GLOBOS = {}


def E_globo(lon, lat, etiqueta, txt=None, col=BL):
    """Globo terráqueo que gira hasta el lugar y lo marca."""
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo("espacio"))
        u = ease(tl / (dur * 0.6))
        lon0 = lon - 90 * (1 - u)
        lat0 = lat * 0.6
        R = 380
        if "globos" not in A:
            A["globos"] = {}
        g = AV.globo_cache(lon0, lat0, R)
        cx, cy = W / 2, 820
        pegar(fr, g, cx, cy)
        x, y, z = AV.orto(lon, lat, lon0, lat0, R)
        if z > 0 and u > 0.6:
            r = 16 + 10 * abs(math.sin(tl * 6))
            d.ellipse((cx + x - r - 14, cy + y - r - 14, cx + x + r + 14, cy + y + r + 14), outline=AM, width=6)
            d.ellipse((cx + x - 14, cy + y - 14, cx + x + 14, cy + y + 14), fill=RO, outline=BL, width=4)
            pegar(fr, texto_grande(etiqueta, AM, 66), cx + x, cy + y - 70)
        titulo(fr, txt, tl, col)
    return f


def E_final(fondo_, parte, txt="SÍGUEME", siguiente=None):
    def f(fr, d, tl, dur):
        fr.alpha_composite(fondo(fondo_))
        rayos(fr, tl, cy=880, col=(255, 255, 255, 45))
        u = back(tl / 0.5)
        pegar(fr, escalar(A["masc"], 0.6 * max(0.05, u)), W / 2, 900 - 20 * abs(math.sin(tl * 4)))
        titulo(fr, txt, tl, RS, 160, 330)
        pegar(fr, escalar(texto_grande("SÍGUEME PARA MÁS", AM, 90), max(0.05, back((tl - 0.3) / 0.35))), W / 2, 1230)
        Hm.confeti(fr, tl, n=60)
    return f


def anim_pulso(ico, x, y, k=0.6, t0=0.3):
    """Extra: un icono pequeño que entra y late en (x, y)."""
    def f(fr, d, tl, dur):
        if tl > t0:
            u = back((tl - t0) / 0.35)
            pegar(fr, escalar(icono(ico), k * max(0.05, u) * (1 + 0.05 * math.sin(tl * 8))), x, y)
    return f


def anim_tachar(t0=0.5, x=W / 2, y=820, r=260):
    def f(fr, d, tl, dur):
        if tl > t0:
            u = ease((tl - t0) / 0.3)
            d.line((x - r, y - r, x - r + 2 * r * u, y - r + 2 * r * u), fill=RO, width=36)
            if u >= 1:
                u2 = ease((tl - t0 - 0.3) / 0.3)
                d.line((x + r, y - r, x + r - 2 * r * u2, y - r + 2 * r * u2), fill=RO, width=36)
    return f


def anim_varios(*fs):
    def f(fr, d, tl, dur):
        for g in fs:
            g(fr, d, tl, dur)
    return f


def zoom(f):
    """Envuelve una escena: acercamiento lento continuo + «golpe» de zoom a mitad de las escenas largas."""
    def g(fr, d, tl, dur):
        tmp = Image.new("RGBA", fr.size, (0, 0, 0, 0))
        f(tmp, ImageDraw.Draw(tmp), tl, dur)
        z = 1.0
        if dur > 4.2 and tl > dur * 0.5:
            z += 0.07 * min(1, (tl - dur * 0.5) / 0.15)
        if z > 1.002:
            w, h = tmp.size
            cw, ch = int(w / z), int(h / z)
            x0, y0 = (w - cw) // 2, int((h - ch) * 0.45)
            tmp = tmp.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.BILINEAR)
        fr.alpha_composite(tmp)
    return g


# ------------------------------------------------------------- lanzar un vídeo
def lanzar(slug, gancho, color, giro, beats, pronuncia=()):
    audio.PRONUNCIA[:0] = list(pronuncia)
    Hm.SALIDA = os.path.join(Hm.PL.SALIDA, slug)
    Hm.BEATS = [dict(b, f=zoom(b["f"])) for b in beats]
    Hm.GANCHO = gancho
    Hm.COLOR_MARCO = color
    Hm.GIRO = giro

    def assets():
        _BASE()
        A["avion"] = Hm.avion(0.9)
        A["globos"] = {}
    Hm.assets = assets
    Hm.render()
