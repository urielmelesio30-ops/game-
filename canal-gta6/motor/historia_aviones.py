# -*- coding: utf-8 -*-
"""Divulgación animada en 2D: por qué los aviones no vuelan en línea recta (rutas de círculo máximo).
Mapas reales a partir de Natural Earth (dominio público), en el estilo de la Mona Lisa (historia.py)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import historia as Hm
from historia import A, W, H, ease, back, texto_grande, pegar, escalar, anton

Hm.SALIDA = os.path.join(Hm.PL.SALIDA, "18-por-que-los-aviones-no-vuelan-recto")
_assets_base = Hm.assets
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAR1, MAR2 = (52, 120, 190), (36, 90, 160)
TIERRA, TIERRA_B, TIERRA_S = (126, 200, 120), (78, 150, 84), (30, 60, 100)
ROJO, VERDE, AMAR, BLANCO = (240, 70, 80), (90, 230, 120), (255, 214, 80), (255, 255, 255)

NY = (-74.0, 40.7)
TOKIO = (139.7, 35.7)
MADRID = (-3.7, 40.4)


# ------------------------------------------------------------- geografía
def _anillos():
    d = json.load(open(os.path.join(RAIZ, "datos", "ne_110m_land.geojson")))
    out = []
    for f in d["features"]:
        g = f["geometry"]
        polis = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for p in polis:
            out.append(p[0])
    return out


ANILLOS = _anillos()


def merc(lat):
    lat = max(-85, min(85, lat))
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


class Mapa:
    """Mapa de Mercator: lon de la0 a lb0 ocupa todo el ancho; lat_ref cae en y_ref."""
    def __init__(self, la, lb, lat_ref, y_ref, desplaza=False):
        self.la, self.lb, self.k = la, lb, W / (lb - la)
        self.cy = y_ref + self.k * merc(lat_ref)
        self.desplaza = desplaza   # centrado en el Pacífico: las longitudes negativas pasan a +360

    def lon(self, lon):
        return lon + 360 if self.desplaza and lon < 0 else lon

    def xy(self, lon, lat):
        return (self.lon(lon) - self.la) * self.k, self.cy - self.k * merc(lat)

    def dibujar(self, rejilla=False, resalta=None):
        SS = 2
        im = Image.new("RGBA", (W * SS, H * SS), MAR1 + (255,))
        d = ImageDraw.Draw(im)
        for i in range(40):
            u = i / 39
            col = tuple(int(MAR1[k] * (1 - u) + MAR2[k] * u) for k in range(3))
            d.rectangle((0, H * SS * u, W * SS, H * SS * u + 60 * SS), fill=col)
        for yy in range(0, H, 150):   # olitas
            for xx in range(-60 + (yy // 150 % 2) * 75, W, 150):
                d.arc((xx * SS, yy * SS, (xx + 46) * SS, (yy + 18) * SS), 200, 340, fill=(110, 170, 225), width=3 * SS)
        if rejilla:
            for lat in range(-60, 90, 15):
                y = self.xy(0, lat)[1] * SS
                d.line((0, y, W * SS, y), fill=(255, 255, 255, 90), width=2 * SS)
            for lon in range(-180, 360, 20):
                x = (lon - self.la) * self.k * SS
                d.line((x, 0, x, H * SS), fill=(255, 255, 255, 90), width=2 * SS)
        for anillo in ANILLOS:
            pts = [self.xy(lo, la) for lo, la in anillo]
            if self.desplaza and max(lo for lo, _ in anillo) > 0 and min(lo for lo, _ in anillo) < 0:
                pts = [((lo - self.la) * self.k, self.cy - self.k * merc(la)) for lo, la in anillo]
            xs = [p[0] for p in pts]
            if max(xs) < -50 or min(xs) > W + 50:
                continue
            d.polygon([((x + 6) * SS, (y + 8) * SS) for x, y in pts], fill=TIERRA_S)
        for anillo in ANILLOS:
            pts = [self.xy(lo, la) for lo, la in anillo]
            if self.desplaza and max(lo for lo, _ in anillo) > 0 and min(lo for lo, _ in anillo) < 0:
                pts = [((lo - self.la) * self.k, self.cy - self.k * merc(la)) for lo, la in anillo]
            xs = [p[0] for p in pts]
            if max(xs) < -50 or min(xs) > W + 50:
                continue
            d.polygon([(x * SS, y * SS) for x, y in pts], fill=TIERRA, outline=TIERRA_B, width=3 * SS)
        return im.resize((W, H), Image.LANCZOS)


def vec(lon, lat):
    lo, la = math.radians(lon), math.radians(lat)
    return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])


def gran_circulo(a, b, n=120):
    """Puntos (lon, lat) de la ruta más corta entre a y b."""
    p, q = vec(*a), vec(*b)
    om = math.acos(float(np.clip(p @ q, -1, 1)))
    out = []
    for i in range(n + 1):
        t = i / n
        v = (math.sin((1 - t) * om) * p + math.sin(t * om) * q) / math.sin(om)
        out.append((math.degrees(math.atan2(v[1], v[0])), math.degrees(math.asin(v[2]))))
    return out


def km_gc(a, b):
    return 6371 * math.acos(float(np.clip(vec(*a) @ vec(*b), -1, 1)))


def km_loxo(a, b, n=400):
    """Distancia siguiendo la línea recta del mapa de Mercator (loxodrómica)."""
    lo0, lo1 = a[0], (b[0] if b[0] - a[0] < 180 else b[0] - 360)
    if a[0] - b[0] > 180:
        lo1 = b[0] + 360
    m0, m1 = merc(a[1]), merc(b[1])
    tot, prev = 0.0, None
    for i in range(n + 1):
        t = i / n
        lon = lo0 + (lo1 - lo0) * t
        my = m0 + (m1 - m0) * t
        lat = math.degrees(2 * math.atan(math.exp(math.radians(my))) - math.pi / 2)
        if prev:
            dl = math.radians(lat - prev[1]); dlo = math.radians(lon - prev[0]) * math.cos(math.radians((lat + prev[1]) / 2))
            tot += 6371 * math.hypot(dl, dlo)
        prev = (lon, lat)
    return tot


KM_CORTO, KM_RECTO = km_gc(NY, TOKIO), km_loxo(NY, TOKIO)


# ------------------------------------------------------------- globo terráqueo
def _mascara():
    SS = 4
    im = Image.new("L", (360 * SS, 180 * SS), 0)
    d = ImageDraw.Draw(im)
    for anillo in ANILLOS:
        d.polygon([((lo + 180) * SS, (90 - la) * SS) for lo, la in anillo], fill=255)
    return np.asarray(im) > 127


MASCARA = _mascara()


def globo(lon0, lat0, R=380):
    """Tierra en proyección ortográfica, con luz lateral, atmósfera y contorno."""
    n = 2 * R
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x = (xx - R + 0.5) / R
    y = (R - yy - 0.5) / R
    rho = np.sqrt(x * x + y * y)
    dentro = rho <= 1
    c = np.arcsin(np.clip(rho, 0, 1))
    la0, lo0 = math.radians(lat0), math.radians(lon0)
    with np.errstate(invalid="ignore", divide="ignore"):
        lat = np.arcsin(np.clip(np.cos(c) * math.sin(la0) + np.where(rho > 0, y * np.sin(c) * math.cos(la0) / rho, 0), -1, 1))
        lon = lo0 + np.arctan2(x * np.sin(c), rho * np.cos(c) * math.cos(la0) - y * np.sin(c) * math.sin(la0))
    lonr = (np.degrees(lon) + 180) % 360
    latr = 90 - np.degrees(lat)
    m = MASCARA.shape[1] / 360
    tierra = MASCARA[np.clip((latr * m).astype(int), 0, MASCARA.shape[0] - 1), np.clip((lonr * m).astype(int), 0, MASCARA.shape[1] - 1)]
    z = np.sqrt(np.clip(1 - rho * rho, 0, 1))
    luz = np.clip(0.45 + 0.75 * (z * 0.75 - x * 0.35 + y * 0.35), 0.35, 1.15)
    base = np.where(tierra[..., None], np.array(TIERRA, np.float32), np.array(MAR1, np.float32))
    rgb = np.clip(base * luz[..., None], 0, 255)
    # brillo especular
    esp = np.clip(1 - np.hypot(x + 0.35, y - 0.4) / 0.35, 0, 1) ** 2
    rgb = np.clip(rgb + esp[..., None] * 90, 0, 255)
    alfa = np.where(dentro, 255, 0).astype(np.uint8)
    borde = (rho > 0.975) & dentro
    rgb[borde] = (20, 40, 80)
    im = Image.fromarray(np.dstack([rgb.astype(np.uint8), alfa]), "RGBA")
    out = Image.new("RGBA", (n + 80, n + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    for k in range(8):
        d.ellipse((40 - k * 4, 40 - k * 4, n + 40 + k * 4, n + 40 + k * 4), outline=(140, 210, 255, 90 - k * 10), width=5)
    out.alpha_composite(im, (40, 40))
    return out


def orto(lon, lat, lon0, lat0, R):
    la, lo, la0, lo0 = map(math.radians, (lat, lon, lat0, lon0))
    x = math.cos(la) * math.sin(lo - lo0)
    y = math.cos(la0) * math.sin(la) - math.sin(la0) * math.cos(la) * math.cos(lo - lo0)
    z = math.sin(la0) * math.sin(la) + math.cos(la0) * math.cos(la) * math.cos(lo - lo0)
    return x * R, -y * R, z


# ------------------------------------------------------------- dibujos
def nube(ancho=360, tormenta=False):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        col = (90, 90, 120) if tormenta else (250, 250, 255)
        som = (60, 60, 90) if tormenta else (200, 215, 235)
        for x, y, r in ((110, 140, 80), (190, 110, 100), (270, 140, 80), (60, 170, 55), (320, 170, 50)):
            d.ellipse(S(x - r, y - r + 12, x + r, y + r + 12), fill=som)
        for x, y, r in ((110, 130, 80), (190, 100, 100), (270, 130, 80), (60, 160, 55), (320, 160, 50)):
            d.ellipse(S(x - r, y - r, x + r, y + r), fill=col)
        d.rectangle(S(60, 150, 320, 215), fill=col)
    im = Hm.suave(380, 240, dib)
    return escalar(im, ancho / 380)


def rayo(d, x, y, k=1.0, col=AMAR):
    pts = [(0, 0), (40, 0), (20, 60), (55, 60), (-10, 170), (8, 90), (-25, 90)]
    d.polygon([(x + px * k, y + py * k) for px, py in pts], fill=col, outline=(0, 0, 0), width=4)


def avion_en(fr, x, y, ang, k=1.0, estela=None):
    av = escalar(A["avion"], k).rotate(ang, expand=True, resample=Image.BICUBIC)
    so = Image.new("RGBA", av.size, (0, 0, 0, 0))
    so.putalpha(av.getchannel("A").point(lambda a: int(a * 0.3)))
    pegar(fr, so, x + 26 * k, y + 44 * k)
    pegar(fr, av, x, y)


def trazo(d, pts, u, col, ancho=12, puntos=False):
    n = max(2, int(len(pts) * max(0, min(1, u))))
    vis = pts[:n]
    if puntos:
        for i, (x, y) in enumerate(vis):
            if i % 3 == 0:
                d.ellipse((x - ancho / 2, y - ancho / 2, x + ancho / 2, y + ancho / 2), fill=col)
    else:
        d.line([(x + 4, y + 6) for x, y in vis], fill=(0, 0, 0, 90), width=ancho, joint="curve")
        d.line(vis, fill=col, width=ancho, joint="curve")
    return vis


def angulo(p, q):
    return math.degrees(math.atan2(-(q[1] - p[1]), q[0] - p[0]))


def etiqueta(fr, txt, x, y, col=BLANCO, tam=64):
    pegar(fr, texto_grande(txt, col, tam), x, y)


# ------------------------------------------------------------- mapas y rutas
PAC = Mapa(115, 305, 50, 800, desplaza=True)
ATL = Mapa(-100, 62, 50, 760)


def ruta_pac():
    return [PAC.xy(lo, la) for lo, la in gran_circulo(NY, TOKIO)][::-1]   # de Nueva York a Tokio


def recta_pac(n=120):
    (x0, y0), (x1, y1) = PAC.xy(*NY), PAC.xy(*TOKIO)
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def assets_extra():
    _assets_base()
    A["avion"] = Hm.avion(0.9)
    A["pac"] = PAC.dibujar()
    A["atl"] = ATL.dibujar()
    A["atl_rejilla"] = ATL.dibujar(rejilla=True)
    A["nube"] = nube(300)
    A["tormenta"] = nube(420, tormenta=True)
    A["ruta"] = ruta_pac()
    A["recta"] = recta_pac()
    A["globos"] = {}
    A["cielo"] = cielo()
    A["espacio"] = espacio()


def cielo():
    def dib(d, s):
        for i in range(40):
            u = i / 39
            col = (int(90 + 80 * u), int(160 + 60 * u), int(240 - 10 * u))
            d.rectangle([0, H * u * s, W * s, (H * u + 60) * s], fill=col)
    return Hm.suave(W, H, dib)


def espacio():
    im = Image.new("RGBA", (W, H), (14, 12, 40, 255))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    for _ in range(220):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.choice([2, 3, 5])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 230, int(rng.uniform(120, 255))))
    return im


def globo_cache(lon0, lat0, R=380):
    clave = (round(lon0 * 2) / 2, round(lat0, 1), R)
    if clave not in A["globos"]:
        if len(A["globos"]) > 200:
            A["globos"].clear()
        A["globos"][clave] = globo(*clave)
    return A["globos"][clave]


def chinchetas(fr, tl, retraso=0.0):
    (xa, ya), (xb, yb) = PAC.xy(*NY), PAC.xy(*TOKIO)
    Hm.chincheta_mapa(fr, xa, ya, tl - retraso, (60, 110, 230))
    Hm.chincheta_mapa(fr, xb, yb, tl - retraso - 0.2, ROJO)
    if tl - retraso > 0.3:
        etiqueta(fr, "NUEVA YORK", xa - 90, ya + 60, tam=52)
        etiqueta(fr, "TOKIO", xb + 40, yb + 60, tam=52)


def avion_ruta(fr, pts, u, k=0.9):
    i = min(len(pts) - 2, int(u * (len(pts) - 1)))
    avion_en(fr, *pts[i], angulo(pts[i], pts[i + 1]), k)


# ------------------------------------------------------------- escenas
def s_gancho(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    for k in range(4):
        x = (k * 330 - tl * 160) % (W + 400) - 200
        pegar(fr, escalar(A["nube"], 0.7 + 0.2 * (k % 2)), x, 420 + k * 230)
    y = 820 + 30 * math.sin(tl * 3)
    avion_en(fr, W / 2 - 40 + 30 * math.sin(tl * 2), y, 8 * math.sin(tl * 3), 2.4)
    pegar(fr, escalar(texto_grande("¿POR QUÉ NO VA RECTO?", AMAR, 120), max(0.05, back(tl / 0.4))), W / 2, 400)


def s_curva(fr, d, tl, dur):
    fr.alpha_composite(A["pac"])
    u = ease(tl / (dur * 0.85))
    trazo(d, A["ruta"], u, BLANCO, 10, puntos=True)
    avion_ruta(fr, A["ruta"], u)
    pegar(fr, escalar(texto_grande("UNA CURVA RARÍSIMA", BLANCO, 110), max(0.05, back(tl / 0.4))), W / 2, 300)


def s_ejemplo(fr, d, tl, dur):
    fr.alpha_composite(A["pac"])
    chinchetas(fr, tl)
    u = ease((tl - 0.6) / (dur - 1.0))
    trazo(d, A["ruta"], u, AMAR, 12)
    if tl > 0.6:
        avion_ruta(fr, A["ruta"], u)
    if u > 0.45:
        x, y = PAC.xy(-152, 64)
        etiqueta(fr, "ALASKA", x, y - 20, AMAR, 70)


def s_rodeo(fr, d, tl, dur):
    fr.alpha_composite(A["pac"])
    chinchetas(fr, 9)
    trazo(d, A["recta"], 1, ROJO, 8, puntos=True)
    trazo(d, A["ruta"], 1, AMAR, 12)
    golpe = dur * 0.55
    if tl < golpe:
        pegar(fr, texto_grande("¿UN RODEO?", ROJO, 140), W / 2, 330)
    else:
        u = back((tl - golpe) / 0.3)
        pegar(fr, escalar(texto_grande("¡EL MÁS CORTO!", VERDE, 140), max(0.05, u)), W / 2, 330)


def s_globo(fr, d, tl, dur):
    fr.alpha_composite(A["espacio"])
    g = globo_cache(-60 + tl * 30, 25)
    pegar(fr, escalar(g, max(0.05, back(tl / 0.5))), W / 2, 820)
    pegar(fr, texto_grande("ES UNA ESFERA", BLANCO, 140), W / 2, 300)


def s_estira(fr, d, tl, dur):
    fr.alpha_composite(A["atl_rejilla"])
    # flechas que tiran hacia los polos
    for k in range(5):
        x = 140 + k * 200
        s = 30 * math.sin(tl * 6)
        for y0, sgn in ((420, -1), (1250, 1)):
            d.line((x, y0, x, y0 + sgn * (90 + s)), fill=AMAR, width=14)
            d.polygon([(x - 26, y0 + sgn * (90 + s)), (x + 26, y0 + sgn * (90 + s)), (x, y0 + sgn * (130 + s))], fill=AMAR)
    pegar(fr, texto_grande("SE ESTIRA", AMAR, 150), W / 2, 300)


GROEN = max((a for a in ANILLOS if -60 < sum(p[0] for p in a) / len(a) < -20 and sum(p[1] for p in a) / len(a) > 65), key=len)
AFRICA_C = (20, 2)


def s_groenlandia(fr, d, tl, dur):
    fr.alpha_composite(A["atl"])
    pts_m = [ATL.xy(lo, la) for lo, la in GROEN]
    lo0 = sum(p[0] for p in GROEN) / len(GROEN); la0 = sum(p[1] for p in GROEN) / len(GROEN)
    cx, cy = ATL.xy(*AFRICA_C)
    k = ATL.k
    pts_r = [(cx + k * (lo - lo0) * math.cos(math.radians(la)), cy - k * (la - la0)) for lo, la in GROEN]
    golpe = dur * 0.6
    u = ease((tl - golpe) / 0.9)
    pts = [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u) for a, b in zip(pts_m, pts_r)]
    parpadeo = 255 if int(tl * 6) % 2 or u > 0 else 160
    d.polygon(pts, fill=(255, 255, 255, parpadeo), outline=(0, 0, 0), width=5)
    if tl < golpe:
        etiqueta(fr, "GROENLANDIA", 520, 330, BLANCO, 80)
        ax, ay = ATL.xy(20, 5)
        etiqueta(fr, "ÁFRICA", ax, ay + 150, BLANCO, 80)
    else:
        pegar(fr, escalar(texto_grande("14 VECES MÁS PEQUEÑA", AMAR, 100), max(0.05, back((tl - golpe) / 0.3))), W / 2, 330)


def s_pelota(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    lon0 = -150 + 20 * ease(tl / dur)
    R = 380
    g = globo_cache(lon0, 50, R)
    cx, cy = W / 2, 840
    pegar(fr, g, cx, cy)
    puntos = gran_circulo(NY, TOKIO, 80)
    u = ease((tl - 0.4) / (dur - 0.8))
    vis = []
    for lo, la in puntos[:max(2, int(len(puntos) * u))]:
        x, y, z = orto(lo, la, lon0, 50, R)
        if z > 0:
            vis.append((cx + x, cy + y))
    if len(vis) > 1:
        d.line(vis, fill=(255, 250, 230), width=8, joint="curve")
    for (lo, la), col in ((NY, (60, 110, 230)), (TOKIO, ROJO)):
        x, y, z = orto(lo, la, lon0, 50, R)
        if z > 0:
            d.ellipse((cx + x - 18, cy + y - 18, cx + x + 18, cy + y + 18), fill=col, outline=BLANCO, width=5)
    pegar(fr, texto_grande("UN HILO TENSO", BLANCO, 130), W / 2, 300)


def s_hilo(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    lon0 = -130
    R = 380
    cx, cy = W / 2, 840
    pegar(fr, globo_cache(lon0, 65, R), cx, cy)
    x, y, _ = orto(0, 90, lon0, 65, R)
    pegar(fr, texto_grande("POLO NORTE", AMAR, 54), cx + x, cy + y - 50)
    d.ellipse((cx + x - 12, cy + y - 12, cx + x + 12, cy + y + 12), fill=AMAR, outline=(0, 0, 0), width=4)
    vis = [(cx + p[0], cy + p[1]) for p in (orto(lo, la, lon0, 65, R) for lo, la in gran_circulo(NY, TOKIO, 80)) if p[2] > 0]
    trazo(d, vis, 1, (255, 250, 230), 9)
    u = ease(tl / dur)
    i = min(len(vis) - 2, int(u * (len(vis) - 1)))
    avion_en(fr, *vis[i], angulo(vis[i], vis[i + 1]), 0.6)
    pegar(fr, texto_grande("SE TUERCE AL POLO", BLANCO, 120), W / 2, 300)


def contador(fr, x, y, valor, col, titulo):
    pegar(fr, texto_grande(titulo, BLANCO, 52), x, y - 60)
    pegar(fr, texto_grande(f"{int(valor):,} KM".replace(",", "."), col, 90), x, y + 10)


def s_comparar(fr, d, tl, dur):
    fr.alpha_composite(A["pac"])
    chinchetas(fr, 9)
    u1 = ease(tl / (dur * 0.6))
    u2 = ease((tl - 0.3) / (dur * 0.6))
    trazo(d, A["recta"], u1, ROJO, 10, puntos=True)
    trazo(d, A["ruta"], u2, VERDE, 14)
    contador(fr, 270, 1230, KM_RECTO * u1, ROJO, "RECTO")
    contador(fr, 810, 1230, KM_CORTO * max(0, u2), VERDE, "CURVA")


def icono_ahorro(tipo):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        if tipo == "gota":
            d.ellipse(S(30, 110, 230, 310), fill=(60, 60, 70)); d.polygon(S(130, 0, 40, 170, 220, 170), fill=(60, 60, 70))
            d.ellipse(S(70, 170, 120, 220), fill=(140, 140, 160))
        elif tipo == "reloj":
            d.ellipse(S(10, 10, 250, 250), fill=(250, 240, 220), outline=(40, 40, 40), width=14 * s)
            d.line(S(130, 130, 130, 60), fill=(40, 40, 40), width=14 * s); d.line(S(130, 130, 190, 160), fill=ROJO, width=14 * s)
        else:
            d.rounded_rectangle(S(10, 60, 250, 200), radius=30 * s, fill=(255, 214, 80), outline=(120, 90, 20), width=10 * s)
            d.text(S(52, 95), "KM", fill=(80, 50, 10), font=anton(80 * s))
    return Hm.suave(260, 320, dib)


def s_ahorro(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    for i, tipo in enumerate(("km", "gota", "reloj")):
        u = back((tl - i * 0.35) / 0.35)
        if u > 0:
            x = 220 + i * 320
            pegar(fr, escalar(A.setdefault("ic_" + tipo, icono_ahorro(tipo)), max(0.05, u)), x, 820 + 15 * math.sin(tl * 4 + i))
            pegar(fr, escalar(texto_grande(["MENOS KM", "GASOIL", "TIEMPO"][i], VERDE, 56), max(0.05, u)), x, 1040)
    pegar(fr, texto_grande("AHORRAN", VERDE, 150), W / 2, 330)
    Hm.confeti(fr, tl, n=40)


def s_ojo(fr, d, tl, dur):
    fr.alpha_composite(A["pac"])
    trazo(d, A["ruta"], 1, AMAR, 12)
    t = abs(math.sin(tl * 5))
    pegar(fr, escalar(texto_grande("NO SIEMPRE", ROJO, 150), 1 + 0.06 * t), W / 2, 760)


def flechas_viento(d, tl, y0, alto, vel=380, col=(220, 245, 255)):
    for fila in range(4):
        y = y0 + fila * alto / 4
        for k in range(6):
            x = (k * 220 + tl * vel + fila * 90) % (W + 300) - 150
            yy = y + 40 * math.sin((x + fila * 50) / 150)
            d.line((x - 90, yy, x + 40, yy), fill=col, width=12)
            d.polygon([(x + 40, yy - 24), (x + 40, yy + 24), (x + 80, yy)], fill=col)


def s_chorro(fr, d, tl, dur):
    fr.alpha_composite(A["atl"])
    banda = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(banda)
    bd.rectangle((0, 560, W, 900), fill=(120, 200, 255, 70))
    fr.alpha_composite(banda)
    flechas_viento(d, tl, 600, 300)
    pegar(fr, texto_grande("CORRIENTE EN CHORRO", AMAR, 100), W / 2, 330)
    pegar(fr, texto_grande("+200 KM/H", BLANCO, 110), W / 2, 1050)


def s_vuelta(fr, d, tl, dur):
    fr.alpha_composite(A["atl"])
    flechas_viento(d, tl, 560, 360, col=(220, 245, 255))
    (xa, ya), (xb, yb) = ATL.xy(*NY), ATL.xy(*MADRID)
    u_rapido = ease(tl / (dur * 0.6))
    u_lento = ease(tl / (dur * 1.5))
    yv = ya - 80
    avion_en(fr, xa + (xb - xa) * u_rapido, yv, 0, 0.9)
    avion_en(fr, xb + (xa - xb) * u_lento, yv + 230, 180, 0.9)
    etiqueta(fr, "IDA: MÁS RÁPIDO", W / 2, 330, VERDE, 90)
    etiqueta(fr, "VUELTA: MÁS LENTO", W / 2, 1180, ROJO, 80)


def s_tormenta(fr, d, tl, dur):
    fr.alpha_composite(A["cielo"])
    pegar(fr, A["tormenta"], 360, 760)
    if int(tl * 5) % 3 == 0:
        rayo(d, 330, 860, 1.4)
    # zona cerrada
    zona = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    zd = ImageDraw.Draw(zona)
    zd.rectangle((0, 0, 359, 359), fill=(240, 60, 70, 90), outline=(240, 60, 70, 255), width=10)
    for k in range(-360, 360, 50):
        zd.line((k, 0, k + 360, 360), fill=(240, 60, 70, 160), width=8)
    pegar(fr, zona, 820, 640)
    zd2 = ImageDraw.Draw(fr)
    zd2.line((760, 580, 880, 700), fill=BLANCO, width=18); zd2.line((880, 580, 760, 700), fill=BLANCO, width=18)
    # el avión los esquiva con una curva en S
    u = ease(tl / dur)
    def p(v):
        return -100 + (W + 200) * v, 1150 - 140 * math.sin(v * 2 * math.pi)
    x, y = p(u); x2, y2 = p(min(1, u + 0.01))
    avion_en(fr, x, y, angulo((x, y), (x2, y2)), 1.1)
    pegar(fr, texto_grande("ESQUIVAN", AMAR, 150), W / 2, 330)


def s_final(fr, d, tl, dur):
    fr.alpha_composite(A["pac"])
    trazo(d, A["ruta"], 1, VERDE, 14)
    u = back(tl / 0.5)
    pegar(fr, escalar(A["masc"], 0.6 * max(0.05, u)), W / 2, 900 - 20 * abs(math.sin(tl * 4)))
    a = tl * 2.2
    avion_en(fr, W / 2 + math.cos(a) * 380, 900 + math.sin(a) * 300, math.degrees(-a) - 90, 0.8)
    pegar(fr, texto_grande("ES UN ATAJO", VERDE, 150), W / 2, 330)
    Hm.confeti(fr, tl, n=50)


BEATS = [
    dict(f=s_gancho, say="¿Por qué los aviones no vuelan en línea recta?"),
    dict(f=s_curva, say="Si miras la ruta de un vuelo en el mapa, verás una curva rarísima."),
    dict(f=s_ejemplo, say="De Nueva York a Tokio, en vez de ir recto, el avión sube hasta Alaska.", sfx=("60%", "zap")),
    dict(f=s_rodeo, say="Parece un rodeo enorme… pero en realidad, es el camino más corto.", sfx=("55%", "golpe")),
    dict(f=s_globo, say="El truco es que la Tierra no es plana: es una esfera."),
    dict(f=s_estira, say="Y para dibujarla en un mapa plano hay que estirarla, sobre todo cerca de los polos."),
    dict(f=s_groenlandia, say="Por eso Groenlandia parece casi tan grande como África… y en realidad es catorce veces más pequeña.", sfx=("60%", "boom")),
    dict(f=s_pelota, say="Haz la prueba: coge una pelota y estira un hilo entre dos ciudades."),
    dict(f=s_hilo, say="Verás que el hilo se tuerce hacia el polo."),
    dict(f=s_comparar, say="Y cuando pasas ese hilo al mapa plano… aparece la curva."),
    dict(f=s_ahorro, say="En este vuelo se ahorran casi dos mil kilómetros, mucho combustible y horas de viaje.", sfx=(0.3, "logro")),
    dict(f=s_ojo, say="Pero ojo: no siempre siguen la ruta más corta.", sfx=(0.2, "golpe")),
    dict(f=s_chorro, say="También aprovechan la corriente en chorro, un viento que sopla a más de doscientos kilómetros por hora."),
    dict(f=s_vuelta, say="Por eso, ir de América a Europa suele ser más rápido que volver."),
    dict(f=s_tormenta, say="Y además esquivan tormentas y zonas cerradas al tráfico aéreo."),
    dict(f=s_final, say="Así que la próxima vez que veas esa curva… ya sabes: es un atajo. Sígueme para más.", sfx=(0.3, "logro")),
]

Hm.BEATS = BEATS
Hm.GANCHO = "EL ATAJO DE LOS AVIONES"
Hm.COLOR_MARCO = (80, 200, 255)
Hm.GIRO = 11
Hm.assets = assets_extra

if __name__ == "__main__":
    print(f"NY-Tokio: curva {KM_CORTO:.0f} km, recta del mapa {KM_RECTO:.0f} km, lat máx "
          f"{max(la for _, la in gran_circulo(NY, TOKIO)):.1f}")
    if "--datos" not in sys.argv:
        Hm.render()
