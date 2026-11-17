# -*- coding: utf-8 -*-
"""Historias reales animadas en 2D (ilustración plana) para TikTok / Reels.

Cada frase = una escena de ~3 s con su propia animación; personajes y
decorados ilustrados por código (originales), subtítulos palabra a palabra,
empujones de cámara y efectos solo en los momentos clave.

Uso:  python3 historia.py            → salida/15-robo-mona-lisa/15-robo-mona-lisa.mp4
      python3 historia.py --muestra  → solo algunos fotogramas para revisar
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import plano as PL   # caption(), tiempos_palabras(), anton(), suave()

audio.VELOCIDAD = float(os.environ.get("VELOCIDAD", "1.08"))
audio.PRONUNCIA[:0] = [("Vincenzo Peruggia", "Vinchénso Perúya"), ("Peruggia", "Perúya"),
                       ("Guillaume Apollinaire", "Guiyóm Apoliner"), ("Louvre", "Luvr"), ("Pablo Picasso", "Pablo Picasso")]
W, H, FPS = 1080, 1920, 30
SALIDA = os.path.join(PL.SALIDA, "15-robo-mona-lisa")
anton = PL.anton
suave = PL.suave


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def back(u):
    return PL.ease_back(u)


# ------------------------------------------------------------- paleta
C = dict(
    cielo1=(255, 196, 140), cielo2=(120, 150, 210), noche=(22, 28, 52), pared=(232, 210, 170), pared2=(214, 188, 146),
    suelo=(150, 98, 60), suelo2=(124, 78, 46), oro=(214, 168, 64), oro2=(160, 116, 34), piel=(240, 196, 160),
    pelo=(40, 30, 26), blanco=(248, 246, 240), azul=(46, 70, 130), azul2=(30, 46, 92), rojo=(208, 48, 56),
    negro=(22, 22, 26), gris=(120, 124, 132), verde=(70, 120, 80), crema=(250, 238, 210), sombra=(0, 0, 0, 70),
)


# ------------------------------------------------------------- personajes (originales)
_cache = {}


def persona(ropa, pelo="pelo", sombrero=None, bigote=False, brazo=(10, -10), pierna=0.0, lleva=None, mira=1, escala=1.0):
    """Figura plana: cabeza, pelo, cuerpo y extremidades con ángulos (grados).
    brazo=(izq, der) giro de los brazos; pierna en [-1, 1] para el paso."""
    k = (ropa, pelo, sombrero, bigote, round(brazo[0]), round(brazo[1]), round(pierna, 2), lleva, mira, escala)
    if k in _cache:
        return _cache[k]
    w, h = 320, 620

    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        cx = 160
        # piernas
        for lado, fase in ((-1, pierna), (1, -pierna)):
            ang = math.radians(fase * 22)
            x0, y0 = cx + lado * 26, 400
            x1, y1 = x0 + math.sin(ang) * 170, y0 + math.cos(ang) * 170
            d.line(S(x0, y0, x1, y1), fill=C["azul2"] if ropa != "bata" else (70, 70, 80), width=42 * s)
            xa, xb = sorted((x1 - 30 * mira, x1 + 34 * mira))
            d.ellipse(S(xa, y1 - 14, xb, y1 + 18), fill=C["negro"])
        # cuerpo
        col = {"bata": C["blanco"], "policia": C["azul"], "traje": (90, 70, 60), "pintor": (190, 120, 70),
               "anticuario": (110, 60, 50), "gente": (160, 80, 90)}.get(ropa, ropa if isinstance(ropa, tuple) else C["gris"])
        d.rounded_rectangle(S(cx - 72, 200, cx + 72, 430), radius=48 * s, fill=col)
        if ropa == "bata":
            d.line(S(cx, 210, cx, 425), fill=(205, 205, 200), width=5 * s)
            for yb in (250, 300, 350):
                d.ellipse(S(cx + 6, yb, cx + 16, yb + 10), fill=(190, 190, 190))
        if ropa == "policia":
            for yb in (240, 290, 340):
                d.ellipse(S(cx - 6, yb, cx + 6, yb + 12), fill=C["oro"])
            d.rectangle(S(cx - 72, 380, cx + 72, 398), fill=C["negro"])
        # brazos
        for lado, a in ((-1, brazo[0]), (1, brazo[1])):
            ang = math.radians(a)
            x0, y0 = cx + lado * 64, 228
            x1, y1 = x0 + lado * math.sin(ang) * 150, y0 + math.cos(ang) * 150
            d.line(S(x0, y0, x1, y1), fill=col, width=38 * s)
            d.ellipse(S(x1 - 20, y1 - 20, x1 + 20, y1 + 20), fill=C["piel"])
        # cabeza
        d.ellipse(S(cx - 62, 70, cx + 62, 200), fill=C["piel"])
        pc = C["pelo"] if pelo == "pelo" else pelo
        if pelo:
            d.chord(S(cx - 66, 62, cx + 66, 176), 180, 360, fill=pc)
        ox = 18 * mira
        d.ellipse(S(cx - 30 + ox, 122, cx - 18 + ox, 136), fill=C["negro"])
        d.ellipse(S(cx + 18 + ox, 122, cx + 30 + ox, 136), fill=C["negro"])
        if bigote:
            d.chord(S(cx - 34 + ox, 150, cx + 34 + ox, 182), 180, 360, fill=pc)
        else:
            d.arc(S(cx - 18 + ox, 150, cx + 18 + ox, 176), 20, 160, fill=(150, 80, 70), width=5 * s)
        if sombrero == "boina":
            d.ellipse(S(cx - 74, 50, cx + 70, 110), fill=C["negro"]); d.rectangle(S(cx - 4, 40, cx + 4, 56), fill=C["negro"])
        elif sombrero == "kepi":
            d.rounded_rectangle(S(cx - 60, 30, cx + 60, 100), radius=10 * s, fill=C["azul2"])
            d.rectangle(S(cx - 72 + 20 * mira, 92, cx + 72 + 20 * mira, 106), fill=C["negro"])
            d.ellipse(S(cx - 10, 50, cx + 10, 70), fill=C["oro"])
        elif sombrero == "bombin":
            d.ellipse(S(cx - 80, 86, cx + 80, 108), fill=C["negro"]); d.chord(S(cx - 54, 22, cx + 54, 130), 180, 360, fill=C["negro"])
    im = suave(w, h, dib)
    if escala != 1.0:
        im = im.resize((int(w * escala), int(h * escala)), Image.LANCZOS)
    _cache[k] = im
    return im


def andar(t, vel=7):
    return math.sin(t * vel)


# ------------------------------------------------------------- decorados y objetos
def gioconda(w=360, h=480, marco=True):
    """Retrato renacentista simplificado (la obra original es de dominio público)."""
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        m = 34 if marco else 0
        if marco:
            d.rectangle(S(0, 0, w, h), fill=C["oro2"]); d.rectangle(S(10, 10, w - 10, h - 10), fill=C["oro"])
        # paisaje de fondo
        for i in range(12):
            u = i / 11
            col = (int(110 - 40 * u), int(126 - 40 * u), int(96 - 40 * u))
            y0 = m + (h - 2 * m) * u
            d.rectangle(S(m, y0, w - m, y0 + (h - 2 * m) / 11 + 1), fill=col)
        d.polygon(S(m, h * 0.45, w * 0.3, h * 0.32, w * 0.55, h * 0.42, w - m, h * 0.3, w - m, h * 0.55, m, h * 0.55), fill=(96, 110, 84))
        cx = w / 2
        # vestido, manos, cara, pelo
        d.polygon(S(cx - 120, h - m, cx - 90, h * 0.55, cx + 90, h * 0.55, cx + 120, h - m), fill=(54, 40, 30))
        d.ellipse(S(cx - 46, h * 0.78, cx + 30, h * 0.86), fill=(222, 184, 140))
        d.ellipse(S(cx - 20, h * 0.8, cx + 56, h * 0.88), fill=(222, 184, 140))
        d.ellipse(S(cx - 56, h * 0.2, cx + 56, h * 0.48), fill=(60, 44, 32))
        d.ellipse(S(cx - 40, h * 0.23, cx + 40, h * 0.45), fill=(226, 190, 146))
        d.rectangle(S(cx - 46, h * 0.3, cx - 34, h * 0.56), fill=(60, 44, 32)); d.rectangle(S(cx + 34, h * 0.3, cx + 46, h * 0.56), fill=(60, 44, 32))
        d.ellipse(S(cx - 22, h * 0.31, cx - 12, h * 0.33), fill=(60, 40, 30)); d.ellipse(S(cx + 12, h * 0.31, cx + 22, h * 0.33), fill=(60, 40, 30))
        d.arc(S(cx - 14, h * 0.37, cx + 14, h * 0.41), 15, 165, fill=(140, 80, 60), width=3 * s)
    return suave(w, h, dib)


def fondo_galeria():
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        d.rectangle(S(0, 0, W, 1300), fill=C["pared"])
        for x in range(0, W, 180):
            d.rectangle(S(x, 0, x + 8, 1300), fill=C["pared2"])
        d.rectangle(S(0, 1180, W, 1300), fill=C["pared2"])
        d.rectangle(S(0, 1300, W, H), fill=C["suelo"])
        for y in range(1300, H, 70):
            d.line(S(0, y, W, y), fill=C["suelo2"], width=4 * s)
        for x, y, w_, h_ in ((60, 420, 200, 260), (820, 380, 200, 300)):
            d.rectangle(S(x, y, x + w_, y + h_), fill=C["oro2"]); d.rectangle(S(x + 12, y + 12, x + w_ - 12, y + h_ - 12), fill=(140, 120, 100))
    return suave(W, H, dib)


def fondo_ciudad(cielo=("cielo1", "cielo2"), cupula=False, torre=False):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        c1, c2 = C[cielo[0]], C[cielo[1]]
        for i in range(40):
            u = i / 39
            col = tuple(int(c2[k] * (1 - u) + c1[k] * u) for k in range(3))
            d.rectangle(S(0, 1300 * u, W, 1300 * u + 34), fill=col)
        if torre:
            d.polygon(S(820, 1150, 860, 520, 880, 380, 900, 520, 940, 1150), fill=(70, 70, 90))
            d.rectangle(S(842, 800, 918, 820), fill=(70, 70, 90))
        if cupula:
            d.chord(S(400, 700, 700, 1000), 180, 360, fill=(170, 90, 60)); d.rectangle(S(420, 850, 680, 1150), fill=(200, 170, 130))
            d.rectangle(S(540, 640, 560, 720), fill=(170, 90, 60))
        rng = np.random.default_rng(2 if cupula else 1)
        x = 0
        while x < W:
            bw = int(rng.integers(110, 190)); bh = int(rng.integers(260, 460))
            col = (int(rng.integers(150, 190)), int(rng.integers(140, 170)), int(rng.integers(150, 180)))
            d.rectangle(S(x, 1300 - bh, x + bw, 1300), fill=col)
            d.polygon(S(x - 6, 1300 - bh, x + bw / 2, 1300 - bh - 60, x + bw + 6, 1300 - bh), fill=(90, 96, 120))
            for wy in range(1300 - bh + 40, 1260, 70):
                for wx in range(x + 18, x + bw - 30, 50):
                    d.rectangle(S(wx, wy, wx + 24, wy + 38), fill=(255, 220, 150) if rng.random() < 0.4 else (110, 120, 150))
            x += bw + 6
        d.rectangle(S(0, 1300, W, H), fill=(110, 110, 120))
        d.rectangle(S(0, 1300, W, 1330), fill=(90, 90, 100))
    return suave(W, H, dib)


def periodico(titular):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        d.rectangle(S(0, 0, 640, 820), fill=(242, 236, 220))
        d.rectangle(S(30, 30, 610, 120), fill=(30, 30, 30))
        for y in range(470, 790, 34):
            d.rectangle(S(30, y, 300, y + 14), fill=(170, 165, 150)); d.rectangle(S(340, y, 610, y + 14), fill=(170, 165, 150))
    im = suave(640, 820, dib)
    d = ImageDraw.Draw(im)
    f = anton(64)
    d.text((320 - d.textlength("LE JOURNAL", font=f) / 2, 38), "LE JOURNAL", font=anton(64), fill=(242, 236, 220))
    y = 150
    for ln in titular:
        f = anton(110)
        d.text((320 - d.textlength(ln, font=f) / 2, y), ln, font=f, fill=(20, 20, 20)); y += 120
    return im


def mascota_amable():
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        d.line(S(380, 250, 300, 90), fill=(150, 150, 160), width=14 * s); d.line(S(520, 250, 610, 80), fill=(150, 150, 160), width=14 * s)
        d.ellipse(S(270, 60, 330, 120), fill=(255, 210, 80)); d.ellipse(S(580, 50, 640, 110), fill=(255, 90, 140))
        d.rounded_rectangle(S(130, 240, 770, 860), radius=90 * s, fill=(232, 222, 200))
        d.rounded_rectangle(S(190, 300, 640, 760), radius=60 * s, fill=(30, 60, 110))
        for x0 in (255, 465):
            d.arc(S(x0, 470, x0 + 110, 560), 200, 340, fill=(90, 220, 255), width=16 * s)
        d.arc(S(300, 540, 530, 690), 20, 160, fill=(90, 220, 255), width=16 * s)
        d.ellipse(S(230, 600, 290, 640), fill=(255, 120, 160)); d.ellipse(S(540, 600, 600, 640), fill=(255, 120, 160))
        d.ellipse(S(670, 360, 730, 420), fill=(255, 210, 80)); d.ellipse(S(670, 450, 730, 510), fill=(70, 200, 240))
        d.rounded_rectangle(S(300, 840, 360, 960), radius=20 * s, fill=(60, 64, 74)); d.rounded_rectangle(S(540, 840, 600, 960), radius=20 * s, fill=(60, 64, 74))
    return suave(900, 980, dib)


def texto_grande(txt, color=(255, 214, 80), tam=170):
    f = anton(tam)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while tmp.textlength(txt, font=f) > W - 140:
        f = anton(f.size - 8)
    l, t, r, b = f.getbbox(txt)
    im = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((20 - l + 6, 20 - t + 8), txt, font=f, fill=(0, 0, 0, 170))
    d.text((20 - l, 20 - t), txt, font=f, fill=color, stroke_width=6, stroke_fill=(0, 0, 0))
    return im


def pegar(fr, im, x, y, centro=True):
    if centro:
        x, y = x - im.width / 2, y - im.height / 2
    fr.alpha_composite(im, (int(x), int(y)))


def escalar(im, k):
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.BICUBIC)


def sombra(fr, x, y, w):
    s = Image.new("RGBA", (int(w), int(w * 0.18)), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((0, 0, s.width - 1, s.height - 1), fill=(0, 0, 0, 70))
    pegar(fr, s, x, y)


# ------------------------------------------------------------- adornos para captar la atención
GANCHO = "EL ROBO MÁS FAMOSO DE LA HISTORIA"   # titular fijo arriba (cada vídeo pone el suyo)
COLOR_MARCO = (255, 214, 80)
GIRO = None   # índice de la escena con el giro final: antes sale «OJO A ESTO»


def pegatina(tipo):
    """Pegatinas dibujadas (originales), estilo emoji."""
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        am, neg = (255, 205, 60), (40, 30, 30)
        if tipo in ("sorpresa", "risa", "ojos_cara"):
            d.ellipse(S(10, 10, 230, 230), fill=am, outline=(220, 150, 30), width=6 * s)
            if tipo == "sorpresa":
                d.ellipse(S(70, 75, 100, 115), fill=neg); d.ellipse(S(140, 75, 170, 115), fill=neg)
                d.ellipse(S(95, 140, 145, 200), fill=neg)
            else:
                d.arc(S(60, 80, 110, 120), 200, 340, fill=neg, width=10 * s); d.arc(S(130, 80, 180, 120), 200, 340, fill=neg, width=10 * s)
                d.chord(S(60, 120, 180, 200), 0, 180, fill=neg); d.chord(S(80, 160, 160, 200), 0, 180, fill=(240, 90, 110))
        elif tipo == "fuego":
            d.polygon(S(120, 0, 200, 110, 210, 170, 170, 230, 70, 230, 30, 170, 40, 100, 80, 120), fill=(255, 110, 40))
            d.polygon(S(120, 90, 165, 160, 150, 220, 90, 220, 75, 170), fill=(255, 210, 70))
        elif tipo == "ojos":
            for x in (20, 125):
                d.ellipse(S(x, 40, x + 95, 200), fill=(255, 255, 255), outline=neg, width=6 * s)
                d.ellipse(S(x + 40, 100, x + 85, 160), fill=neg)
        elif tipo == "dinero":
            d.ellipse(S(30, 60, 210, 235), fill=(110, 180, 90)); d.polygon(S(80, 70, 160, 70, 140, 30, 100, 30), fill=(110, 180, 90))
            d.text((92 * s, 95 * s), "$", font=anton(110 * s), fill=(255, 255, 255))
        elif tipo == "alerta":
            d.polygon(S(120, 10, 235, 220, 5, 220), fill=(240, 60, 70)); d.polygon(S(120, 45, 205, 205, 35, 205), fill=(255, 220, 80))
            d.text((100 * s, 70 * s), "!", font=anton(120 * s), fill=(40, 30, 30))
        elif tipo == "corazon":
            d.ellipse(S(10, 30, 125, 145), fill=(255, 80, 120)); d.ellipse(S(115, 30, 230, 145), fill=(255, 80, 120))
            d.polygon(S(15, 110, 225, 110, 120, 230), fill=(255, 80, 120))
    return suave(240, 240, dib)


ADORNOS = {}
CICLO_PEGATINAS = ["sorpresa", "ojos", "fuego", "alerta", "risa", "dinero", "corazon"]


def preparar_adornos():
    for t in CICLO_PEGATINAS:
        ADORNOS[t] = pegatina(t)
    m = mascota_amable()
    ADORNOS["mascota"] = m.resize((m.width // 6, m.height // 6), Image.LANCZOS)
    f = anton(58)
    for clave, txt, col in (("gancho", GANCHO, COLOR_MARCO), ("espera", "👀 ESPERA AL FINAL".replace("👀 ", ""), (255, 255, 255)),
                            ("ojo", "OJO A ESTO", (255, 255, 255))):
        tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        tw = int(tmp.textlength(txt, font=f))
        im = Image.new("RGBA", (tw + 70, 96), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        fondo = (20, 20, 30, 225) if clave == "gancho" else ((230, 40, 70, 240) if clave == "ojo" else (40, 40, 60, 235))
        dd.rounded_rectangle((0, 0, im.width - 1, 95), radius=48, fill=fondo, outline=col + (255,), width=5)
        dd.text((35, 14), txt, font=f, fill=col + (255,))
        ADORNOS[clave] = im


# ------------------------------------------------------------- efectos de vídeo
_rng = np.random.default_rng(11)
GRANO = [(_rng.standard_normal((H // 2, W // 2)) * 7).astype(np.int16).repeat(2, 0).repeat(2, 1) for _ in range(6)]
_yy, _xx = np.mgrid[0:H, 0:W]
_DIAG = (_xx + _yy * 0.6).astype(np.float32)


def transicion(arr, tl, kb):
    """Entrada de escena (0,28 s): barrido, zoom, círculo o glitch, rotando."""
    D = 0.28
    if kb == 0 or tl >= D:
        return arr
    u = ease(tl / D)
    tipo = kb % 4
    if tipo == 0:      # barrido rápido con desenfoque de movimiento
        dx = int((1 - u) * W * 0.4)
        capas = [np.roll(arr, dx + k * int(30 * (1 - u)), axis=1).astype(np.uint16) for k in range(4)]
        return (sum(capas) // 4).astype(np.uint8)
    if tipo == 1:      # zoom de golpe
        z = 1 + 0.35 * (1 - u)
        im = Image.fromarray(arr)
        nw, nh = int(W * z), int(H * z)
        im = im.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        return np.asarray(im)
    if tipo == 2:      # círculo que se abre
        r = u * math.hypot(W, H) / 2
        mask = (_xx - W / 2) ** 2 + (_yy - H / 2) ** 2 <= r * r
        out = np.zeros_like(arr); out[mask] = arr[mask]
        return out
    # glitch: canales RGB desplazados y franjas movidas
    out = arr.copy()
    k = int((1 - u) * 40)
    out[..., 0] = np.roll(arr[..., 0], k, axis=1)
    out[..., 2] = np.roll(arr[..., 2], -k, axis=1)
    rng = np.random.default_rng(int(tl * 1000))
    for _ in range(6):
        y0 = int(rng.integers(0, H - 60)); hh = int(rng.integers(10, 60))
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-80, 80)), axis=1)
    return out


def confeti(fr, t, n=70, semilla=3):
    rng = np.random.default_rng(semilla)
    d = ImageDraw.Draw(fr)
    cols = [(255, 90, 140), (80, 220, 255), (255, 214, 80), (120, 230, 140), (200, 120, 255)]
    for i in range(n):
        x0 = rng.uniform(0, W); v = rng.uniform(500, 900); fase = rng.uniform(0, 6.28)
        y = -60 + v * t - 30 * i % 200
        if y > H:
            continue
        x = x0 + math.sin(t * 3 + fase) * 60
        a = t * 6 + fase
        w_, h_ = 26, 14
        pts = [(x + math.cos(a) * w_ - math.sin(a) * h_, y + math.sin(a) * w_ + math.cos(a) * h_),
               (x - math.cos(a) * w_ - math.sin(a) * h_, y - math.sin(a) * w_ + math.cos(a) * h_),
               (x - math.cos(a) * w_ + math.sin(a) * h_, y - math.sin(a) * w_ - math.cos(a) * h_),
               (x + math.cos(a) * w_ + math.sin(a) * h_, y + math.sin(a) * w_ - math.cos(a) * h_)]
        d.polygon(pts, fill=cols[i % len(cols)])


def destello_luz(arr, tg):
    """Destello de color que cruza la pantalla cada ~7 s."""
    fase = (tg % 7.0) / 1.1
    if fase > 1:
        return arr
    pos = -600 + fase * (W + 2 * H * 0.6 + 600)
    banda = np.clip(1 - np.abs(_DIAG - pos) / 260, 0, 1) * 0.35
    col = np.array(COLOR_MARCO, np.float32)
    return (arr * (1 - banda[..., None]) + col * banda[..., None]).astype(np.uint8)


PIXEL = os.environ.get("PIXEL", "1") == "1"   # estilo pixel art del canal (por defecto)
PW, PH, PESC = 360, 640, 3


def pixelar(arr):
    """Reduce a 360x640 con colores posterizados (paleta retro estable entre fotogramas)."""
    from PIL import ImageOps
    im = Image.fromarray(arr).resize((PW, PH), Image.BOX)
    return ImageOps.posterize(im, 3).convert("RGBA")


def subtitulo_pixel(palabras, k_actual):
    """Subtítulo palabra a palabra con fuente pixel; la última palabra en amarillo."""
    import render as R
    f = R.fuente("texto", 30)
    piezas = [R.txt_img(p.upper(), f, "amarillo" if i == k_actual else "blanco", "negro", contorno=True)
              for i, p in enumerate(palabras[:k_actual + 1])]
    lineas, act, ancho = [], [], 0
    for p in piezas:
        if act and ancho + p.width + 6 > R.ANCHO:
            lineas.append(act); act, ancho = [], 0
        act.append(p); ancho += p.width + 6
    lineas.append(act)
    alto = sum(max(p.height for p in l) for l in lineas) + 2 * (len(lineas) - 1)
    out = Image.new("RGBA", (PW, alto), (0, 0, 0, 0))
    y = 0
    for l in lineas:
        w = sum(p.width for p in l) + 6 * (len(l) - 1)
        x = (PW - w) // 2
        for p in l:
            out.alpha_composite(p, (x, y)); x += p.width + 6
        y += max(p.height for p in l) + 2
    return out


def momento_clave(beat, tl):
    """(temblor_px, destello) si estamos justo en el efecto de sonido de la escena."""
    if "sfx" not in beat:
        return 0, 0.0
    off = beat["sfx"][0]
    off = beat["dur"] * float(off[:-1]) / 100 if isinstance(off, str) else off
    dt = tl - off
    if 0 <= dt < 0.35:
        return int(18 * (1 - dt / 0.35)), 0.35 * (1 - dt / 0.35)
    return 0, 0.0


def adornos(fr, tg, total, kb, tl, beat):
    d = ImageDraw.Draw(fr)
    # marco de neón que late
    a = int(120 + 100 * (0.5 + 0.5 * math.sin(tg * 4)))
    marco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(marco).rounded_rectangle((10, 10, W - 11, H - 11), radius=40, outline=COLOR_MARCO + (a,), width=10)
    fr.alpha_composite(marco)
    # barra de progreso
    d.rounded_rectangle((30, 30, W - 30, 44), radius=7, fill=(0, 0, 0, 140))
    d.rounded_rectangle((30, 30, 30 + (W - 60) * min(1, tg / total), 44), radius=7, fill=COLOR_MARCO)
    # titular gancho fijo arriba (late un poco)
    g = ADORNOS["gancho"]
    k = 1 + 0.03 * math.sin(tg * 5)
    pegar(fr, escalar(g, k), W / 2, 120)
    # «espera al final» al principio y «ojo a esto» antes del giro
    if 0.6 < tg < 4.0:
        pegar(fr, escalar(ADORNOS["espera"], max(0.05, back((tg - 0.6) / 0.3))), W / 2, 222)
    if GIRO is not None and kb == GIRO and tl < 2.2:
        pegar(fr, escalar(ADORNOS["ojo"], max(0.05, back(tl / 0.3)) * (1 + 0.05 * math.sin(tl * 12))), W / 2, 450)
    # pegatina que salta en cada escena (alternando lado), con bamboleo
    tipo = beat.get("pegatina") or CICLO_PEGATINAS[kb % len(CICLO_PEGATINAS)]
    if tipo and 0.25 < tl < beat["dur"] - 0.15:
        u = back((tl - 0.25) / 0.35)
        st = ADORNOS[tipo].rotate(12 * math.sin(tl * 6), resample=Image.BICUBIC, expand=True)
        st = escalar(st, 0.75 * max(0.05, u))
        x = 150 if kb % 2 == 0 else W - 190
        pegar(fr, st, x, 560 + 15 * math.sin(tl * 3))
    # destellos que suben
    for k_ in range(10):
        x = (k_ * 211 + tg * 40) % W
        y = H - ((k_ * 137 + tg * 90) % (H - 300)) - 100
        r = 4 + (k_ % 3) * 2
        d.ellipse((x - r, y - r, x + r, y + r), fill=COLOR_MARCO + (170,))
    # mini mascota en la esquina, botando mientras se habla
    m = ADORNOS["mascota"]
    pegar(fr, m, 110, 1360 - abs(math.sin(tg * 6)) * 14)


# ------------------------------------------------------------- guion (datos verificados, ver FUENTES.md)
A = {}


def assets():
    A["galeria"] = fondo_galeria()
    A["paris"] = fondo_ciudad(torre=True)
    A["paris_noche"] = fondo_ciudad(cielo=("cielo2", "noche"), torre=True)
    A["florencia"] = fondo_ciudad(cielo=("cielo1", "cielo2"), cupula=True)
    A["mona"] = gioconda()
    A["mona_sin"] = gioconda(marco=False)
    A["diario"] = periodico(["¡ROBADA", "LA GIOCONDA!"])
    A["masc"] = mascota_amable()
    A["vidrio"] = suave(420, 540, lambda d, s: d.rectangle([0, 0, 420 * s, 540 * s], fill=(190, 230, 255, 70), outline=(230, 250, 255, 220), width=8 * s))


def esc_paris(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    pegar(fr, texto_grande("1911"), W / 2, 420 + (1 - back(tl / 0.5)) * -300)


def esc_entra(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    pegar(fr, A["mona"], W / 2, 640)
    x = -150 + (W + 300) * (tl / dur) * 0.55
    p = persona("bata", bigote=True, pierna=andar(tl), brazo=(15 * andar(tl), -15 * andar(tl)))
    sombra(fr, x, 1500, 220); pegar(fr, p, x, 1200)


def esc_nombre(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    k = 1.6 + 0.1 * tl / dur
    p = escalar(persona("bata", bigote=True, brazo=(10, -10)), k)
    pegar(fr, p, W / 2, 1050)
    u = back(tl / 0.45)
    tarjeta = Image.new("RGBA", (760, 200), (0, 0, 0, 0))
    td = ImageDraw.Draw(tarjeta)
    td.rounded_rectangle((0, 0, 759, 199), radius=26, fill=(20, 24, 40, 235), outline=(255, 214, 80), width=6)
    f = anton(78); t1 = "VINCENZO PERUGGIA"
    td.text((380 - td.textlength(t1, font=f) / 2, 22), t1, font=f, fill=(255, 255, 255))
    f2 = anton(48); t2 = "EX-EMPLEADO DEL MUSEO"
    td.text((380 - td.textlength(t2, font=f2) / 2, 118), t2, font=f2, fill=(255, 214, 80))
    pegar(fr, escalar(tarjeta, max(0.05, u)), W / 2, 380)


def esc_cristal(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    pegar(fr, A["mona"], W / 2, 640)
    u = ease(tl / 0.9)
    pegar(fr, A["vidrio"], W / 2, 640 - (1 - u) * 900)
    if u >= 1:
        for k in range(3):
            a = tl * 3 + k * 2
            x, y = W / 2 - 140 + 100 * k, 480 + 80 * math.sin(a)
            d.polygon([(x, y - 22), (x + 7, y - 7), (x + 22, y), (x + 7, y + 7), (x, y + 22), (x - 7, y + 7), (x - 22, y), (x - 7, y - 7)], fill=(255, 255, 255))
    p = persona("bata", bigote=True, brazo=(150, 150))
    pegar(fr, p, 230, 1180)


def esc_descuelga(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    for x in (W / 2 - 120, W / 2 + 120):
        for y in (440, 840):
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(60, 60, 60))
    u = ease(tl / 0.7)
    sube = math.sin(min(1, tl / 0.7) * math.pi) * 40
    if tl < dur * 0.55:
        pegar(fr, A["mona"], W / 2 + 160 * u, 640 + 260 * u - sube)
    else:
        v = ease((tl - dur * 0.55) / 0.5)
        marco = Image.new("RGBA", A["mona"].size, (0, 0, 0, 0))
        md = ImageDraw.Draw(marco); md.rectangle((0, 0, marco.width - 1, marco.height - 1), outline=C["oro"], width=34)
        pegar(fr, marco.rotate(-25 * v, expand=True, resample=Image.BICUBIC), W / 2 + 160 - 120 * v, 900 + 500 * v)
        pegar(fr, escalar(A["mona_sin"], 0.8), W / 2 + 200, 860 - 60 * v)
    pegar(fr, persona("bata", bigote=True, brazo=(160, 160), mira=1), W / 2 + 40, 1180)


def esc_sale(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    d.rectangle((W - 260, 700, W - 40, 1300), fill=(90, 60, 40)); d.rectangle((W - 240, 720, W - 60, 1300), fill=(30, 20, 18))
    x = 200 + (W - 400) * ease(tl / (dur * 0.8))
    p = persona("bata", bigote=True, pierna=andar(tl), brazo=(25, -25))
    # el cuadro, escondido bajo la bata (asoma una esquina)
    pegar(fr, p, x, 1200)
    d.rectangle((x - 70, 1040, x - 40, 1080), fill=C["oro"])
    if tl > dur * 0.8:
        d.rectangle((W - 240, 720, W - 60, 1300), fill=(90, 60, 40))


def esc_reloj(fr, d, tl, dur):
    fr.alpha_composite(A["paris_noche"])
    cx, cy, r = W / 2, 720, 260
    d.ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), fill=C["oro2"]); d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=C["crema"])
    for k in range(12):
        a = k * math.pi / 6
        d.line((cx + math.cos(a) * (r - 40), cy + math.sin(a) * (r - 40), cx + math.cos(a) * (r - 10), cy + math.sin(a) * (r - 10)), fill=C["negro"], width=10)
    a1 = tl * 9; a2 = tl * 0.75
    d.line((cx, cy, cx + math.sin(a1) * 210, cy - math.cos(a1) * 210), fill=C["negro"], width=14)
    d.line((cx, cy, cx + math.sin(a2) * 140, cy - math.cos(a2) * 140), fill=C["rojo"], width=22)
    pegar(fr, texto_grande("NADIE SE ENTERA", (255, 255, 255), 120), W / 2, 260)


def esc_hueco(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    for x in (W / 2 - 120, W / 2 + 120):
        for y in (440, 840):
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(60, 60, 60))
    d.rectangle((W / 2 - 180, 400, W / 2 + 180, 880), outline=(205, 180, 140), width=6)
    p = persona("pintor", sombrero="boina", brazo=(30, 160 if tl > dur * 0.4 else 30), mira=-1)
    pegar(fr, p, 860, 1200)
    if tl > dur * 0.4:
        u = back((tl - dur * 0.4) / 0.3)
        pegar(fr, escalar(texto_grande("?!", (255, 80, 80), 200), max(0.05, u)), 800, 760)


def esc_policia(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    luz = (int(tl * 6) % 2)
    tinte = Image.new("RGBA", (W, H), (255, 40, 40, 60) if luz else (40, 80, 255, 60))
    fr.alpha_composite(tinte)
    u = back(tl / 0.5)
    pegar(fr, escalar(A["diario"].rotate(8 - 8 * min(1, tl / 0.5), expand=True, resample=Image.BICUBIC), 0.9 * max(0.05, u)), W / 2, 640)
    for i, x in enumerate((180, 900)):
        p = persona("policia", sombrero="kepi", pierna=andar(tl + i), brazo=(40, -40), mira=1 if i == 0 else -1)
        pegar(fr, p, x, 1230)


def esc_poeta(fr, d, tl, dur):
    fr.alpha_composite(A["paris_noche"])
    p = escalar(persona("traje", sombrero="bombin", brazo=(20, -20)), 1.3)
    pegar(fr, p, W / 2, 1000)
    for k in range(7):
        x = W / 2 - 330 + k * 110
        d.rectangle((x, 480 + (1 - ease(tl / 0.4)) * -700, x + 22, 1380), fill=(70, 70, 80))
    pegar(fr, texto_grande("DETENIDO", (255, 90, 90), 140), W / 2, 330)


def esc_picasso(fr, d, tl, dur):
    fr.alpha_composite(A["paris_noche"])
    cono = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(cono).polygon([(W / 2 - 60, 0), (W / 2 + 60, 0), (W / 2 + 360, 1400), (W / 2 - 360, 1400)], fill=(255, 245, 200, 70))
    fr.alpha_composite(cono)
    p = escalar(persona((40, 40, 50), sombrero=None, brazo=(30, -30)), 1.3)
    pegar(fr, p, W / 2, 1000)
    u = back(tl / 0.4)
    pegar(fr, escalar(texto_grande("?", (255, 214, 80), 260), max(0.05, u)), W / 2 + 280, 560)


def esc_anios(fr, d, tl, dur):
    fr.alpha_composite(A["paris_noche"])
    anio = 1911 + min(2, int(tl / (dur * 0.3)))
    hoja = Image.new("RGBA", (520, 600), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hoja)
    hd.rounded_rectangle((0, 0, 519, 599), radius=30, fill=C["crema"]); hd.rounded_rectangle((0, 0, 519, 150), radius=30, fill=C["rojo"])
    f = anton(200); t = str(anio)
    hd.text((260 - hd.textlength(t, font=f) / 2, 230), t, font=f, fill=C["negro"])
    fase = (tl / (dur * 0.3)) % 1
    k = 1 - 0.25 * math.sin(fase * math.pi) if anio < 1913 else 1
    pegar(fr, escalar(hoja, k), W / 2, 780)
    pegar(fr, texto_grande("NI RASTRO", (255, 255, 255), 130), W / 2, 330)


def esc_florencia(fr, d, tl, dur):
    fr.alpha_composite(A["florencia"])
    x = -120 + 520 * ease(tl / 1.2)
    p = persona("bata" if False else (60, 60, 70), bigote=True, pierna=andar(tl) if tl < 1.2 else 0, brazo=(20, -60))
    pegar(fr, p, x, 1230)
    d.rounded_rectangle((x + 60, 1150, x + 230, 1260), radius=12, fill=(120, 80, 40))
    pegar(fr, persona("anticuario", pelo=(150, 150, 150), brazo=(20, -20), mira=-1), 860, 1230)
    pegar(fr, texto_grande("1913", (255, 214, 80), 170), W / 2, 330)


# --- mapa ilustrado de Francia e Italia (contornos simplificados, lon/lat aproximadas)
FRANCIA = [(-4.8, 48.4), (-1.6, 48.7), (-1.3, 49.6), (1.6, 50.9), (2.5, 51.1), (4.2, 49.9), (6.0, 49.4), (8.2, 48.9),
           (7.6, 47.6), (6.9, 47.4), (6.0, 46.4), (6.8, 45.9), (7.0, 45.0), (6.6, 44.2), (7.5, 43.8), (6.2, 43.1),
           (4.6, 43.4), (3.1, 43.1), (3.1, 42.4), (1.7, 42.5), (-1.8, 43.4), (-1.2, 44.7), (-1.1, 46.0), (-2.2, 47.1), (-4.4, 47.9)]
ITALIA = [(6.8, 45.9), (7.0, 45.0), (6.6, 44.2), (7.5, 43.8), (8.8, 44.4), (10.2, 43.9), (10.5, 42.9), (11.1, 42.4),
          (12.2, 41.8), (13.6, 41.2), (14.3, 40.6), (15.7, 40.0), (15.6, 38.2), (16.0, 38.0), (16.6, 38.4), (17.1, 39.4),
          (16.5, 39.8), (16.9, 40.4), (18.5, 40.2), (18.0, 40.6), (16.0, 41.4), (15.0, 42.1), (14.0, 42.6), (13.6, 43.5),
          (12.4, 44.3), (12.3, 45.3), (13.7, 45.7), (13.7, 46.5), (12.4, 47.0), (10.5, 46.9), (9.0, 46.0), (7.0, 46.2)]
ISLAS = [[(12.4, 37.9), (15.6, 38.3), (15.1, 36.7), (12.4, 37.6)], [(8.2, 41.1), (9.8, 41.0), (9.6, 39.1), (8.4, 38.9)],
         [(8.6, 42.9), (9.5, 43.0), (9.4, 41.4), (8.8, 41.6)]]
PARIS, FLORENCIA = (2.35, 48.86), (11.25, 43.77)


def proy(lon, lat):
    esc = 1000 / (18 * 0.707)   # encuadre centrado en París–Florencia
    return 40 + (lon + 3.0) * 0.707 * esc, 280 + (51.5 - lat) * esc


def fondo_mapa():
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        for i in range(40):
            u = i / 39
            col = (int(70 + 30 * u), int(140 + 30 * u), int(200 + 20 * u))
            d.rectangle(S(0, H * u, W, H * u + 50), fill=col)
        for k in range(0, W, 90):   # olitas
            for y in range(380, 1400, 140):
                d.arc(S(k + (y % 180), y, k + 40 + (y % 180), y + 20), 200, 340, fill=(140, 200, 235), width=3 * s)
        for poli, col in ((FRANCIA, (120, 170, 220)), (ITALIA, (120, 200, 130))):
            pass
        for poli, col, borde in ((FRANCIA, (250, 214, 150), (200, 150, 90)), (ITALIA, (170, 220, 140), (110, 160, 90))):
            pts = [proy(*p) for p in poli]
            d.polygon(S(*sum([(x + 8, y + 10) for x, y in pts], ())), fill=(40, 70, 110))
            d.polygon(S(*sum(pts, ())), fill=col, outline=borde)
        for isla in ISLAS:
            pts = [proy(*p) for p in isla]
            d.polygon(S(*sum(pts, ())), fill=(170, 220, 140) if isla is not ISLAS[2] else (250, 214, 150))
    im = suave(W, H, dib)
    d = ImageDraw.Draw(im)
    for txt, (lon, lat) in (("FRANCIA", (1.0, 46.6)), ("ITALIA", (13.2, 42.6))):
        x, y = proy(lon, lat)
        f = anton(64)
        d.text((x - d.textlength(txt, font=f) / 2, y - 30), txt, font=f, fill=(255, 255, 255, 170))
    return im


def avion(escala=1.0):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        # vista desde arriba, apuntando a la derecha
        d.polygon(S(20, 95, 230, 80, 260, 95, 230, 110), fill=(250, 250, 255))          # fuselaje
        d.polygon(S(110, 88, 150, 10, 175, 10, 160, 88), fill=(230, 60, 70))            # ala superior
        d.polygon(S(110, 102, 150, 180, 175, 180, 160, 102), fill=(230, 60, 70))        # ala inferior
        d.polygon(S(20, 92, 0, 55, 18, 55, 45, 90), fill=(230, 60, 70))                 # cola
        d.polygon(S(20, 98, 0, 135, 18, 135, 45, 100), fill=(230, 60, 70))
        d.ellipse(S(205, 86, 230, 104), fill=(120, 190, 240))                           # cabina
    im = suave(270, 190, dib)
    return im.resize((int(270 * escala), int(190 * escala)), Image.LANCZOS) if escala != 1 else im


def chincheta_mapa(fr, x, y, t, color):
    u = back(t / 0.4)
    if t <= 0:
        return
    caida = (1 - min(1, u)) * -160
    d = ImageDraw.Draw(fr)
    d.ellipse((x - 10, y - 4, x + 10, y + 6), fill=(0, 0, 0, 90))
    d.ellipse((x - 30, y - 92 + caida, x + 30, y - 32 + caida), fill=color)
    d.polygon([(x - 22, y - 52 + caida), (x + 22, y - 52 + caida), (x, y + caida)], fill=color)
    d.ellipse((x - 12, y - 74 + caida, x + 12, y - 50 + caida), fill=(255, 255, 255))


def esc_vuelve(fr, d, tl, dur):
    if "mapa" not in A:
        A["mapa"] = fondo_mapa()
        A["avion"] = avion(1.1)
    fr.alpha_composite(A["mapa"])
    (xp, yp), (xf, yf) = proy(*PARIS), proy(*FLORENCIA)
    chincheta_mapa(fr, xf, yf, tl, (230, 60, 70))
    chincheta_mapa(fr, xp, yp, tl - 0.25, (60, 110, 230))
    for (x, y, t) in ((xf, yf + 70, "FLORENCIA"), (xp, yp - 140, "PARÍS")):
        pegar(fr, texto_grande(t, (255, 255, 255), 74), x, y)

    def ruta(v):   # arco de Florencia a París
        x = xf + (xp - xf) * v
        y = yf + (yp - yf) * v - math.sin(v * math.pi) * 320
        return x, y
    u = ease((tl - 0.5) / max(0.5, dur - 0.9))
    for k in range(40):   # estela de puntos
        v = k / 39
        if v > u:
            break
        x, y = ruta(v)
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 255, 255))
    if tl > 0.5:
        x, y = ruta(u)
        x2, y2 = ruta(min(1, u + 0.01))
        ang = math.degrees(math.atan2(-(y2 - y), x2 - x)) if u < 1 else 140
        av = A["avion"].rotate(ang, expand=True, resample=Image.BICUBIC)
        sombra_av = Image.new("RGBA", av.size, (0, 0, 0, 0))
        sombra_av.putalpha(av.getchannel("A").point(lambda a: int(a * 0.3)))
        pegar(fr, sombra_av, x + 30, y + 50)
        pegar(fr, av, x, y)
        pegar(fr, escalar(A["mona"], 0.22), x - 20, y + 110)   # el cuadro viaja a bordo


def esc_cola(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    for x in (W / 2 - 120, W / 2 + 120):
        for y in (440, 840):
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(60, 60, 60))
    n = 3 + int(tl * 5)
    for i in range(min(n, 14)):
        fila = i % 2
        x = 140 + (i // 2) * 140 + fila * 70
        y = 1260 + fila * 120
        col = [(160, 80, 90), (80, 110, 160), (90, 140, 90), (170, 130, 70)][i % 4]
        sombrero = ["bombin", None, "boina", None][i % 4]
        pegar(fr, escalar(persona(col, sombrero=sombrero, brazo=(10, -10), mira=-1 if x > W / 2 else 1), 0.7), x, y)
    pegar(fr, texto_grande("¡MILES DE PERSONAS!", (255, 214, 80), 110), W / 2, 260)


def esc_famosa(fr, d, tl, dur):
    fr.alpha_composite(A["galeria"])
    rayos = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rayos)
    for k in range(16):
        a = k * math.pi / 8 + tl * 0.5
        rd.polygon([(W / 2, 680), (W / 2 + math.cos(a) * 1500, 680 + math.sin(a) * 1500), (W / 2 + math.cos(a + 0.12) * 1500, 680 + math.sin(a + 0.12) * 1500)], fill=(255, 230, 140, 90))
    fr.alpha_composite(rayos)
    k = 1.0 + 0.15 * back(tl / 0.5)
    pegar(fr, escalar(A["mona"], k), W / 2, 680)
    pegar(fr, texto_grande("LA MÁS FAMOSA", (255, 214, 80), 140), W / 2, 260)


def esc_cta(fr, d, tl, dur):
    fr.alpha_composite(A["paris"])
    u = back(tl / 0.5)
    m = escalar(A["masc"], 0.7 * max(0.05, u))
    pegar(fr, m, W / 2, 900 - 20 * abs(math.sin(tl * 4)))
    pegar(fr, texto_grande("SÍGUEME", (255, 90, 140), 150), W / 2, 330)


BEATS = [
    dict(f=esc_paris, say="21 de agosto de 1911. París. El museo del Louvre está cerrado."),
    dict(f=esc_entra, say="Un hombre vestido de blanco, como los trabajadores del museo, camina tranquilo por las salas."),
    dict(f=esc_nombre, say="Se llama Vincenzo Peruggia, y conoce el museo perfectamente."),
    dict(f=esc_cristal, say="Porque él mismo había ayudado a instalar el cristal que protegía la Mona Lisa.", sfx=(0.9, "golpe")),
    dict(f=esc_descuelga, say="Descuelga el cuadro, le quita el marco…"),
    dict(f=esc_sale, say="lo esconde bajo su bata, y sale por la puerta como si nada."),
    dict(f=esc_reloj, say="Y nadie se da cuenta hasta el día siguiente."),
    dict(f=esc_hueco, say="Un pintor llega para copiarla… y en la pared solo quedan cuatro clavos.", sfx=("40%", "golpe")),
    dict(f=esc_policia, say="La policía se vuelve loca, y la noticia da la vuelta al mundo."),
    dict(f=esc_poeta, say="Detienen al poeta Guillaume Apollinaire…", sfx=(0.3, "golpe")),
    dict(f=esc_picasso, say="y hasta interrogan a un joven pintor llamado Pablo Picasso."),
    dict(f=esc_anios, say="Pasan dos años, y ni rastro del cuadro."),
    dict(f=esc_florencia, say="Hasta que en 1913, en Florencia, alguien intenta vendérsela a un anticuario."),
    dict(f=esc_vuelve, say="Era Peruggia. Lo detienen, y la Mona Lisa vuelve a París.", sfx=(0.2, "subida")),
    dict(f=esc_cola, say="Y lo más increíble: mientras estuvo desaparecida, miles de personas fueron a ver… el hueco vacío."),
    dict(f=esc_famosa, say="Antes del robo ya era famosa. Después, se convirtió en el cuadro más famoso del mundo.", sfx=(0.3, "logro")),
    dict(f=esc_cta, say="¿Conocías esta historia? Sígueme para más historias reales que parecen inventadas."),
]


GIRO = 14   # «Y lo más increíble…» (la cola frente al hueco)


def render():
    os.makedirs(SALIDA, exist_ok=True)
    slug = os.path.basename(SALIDA)
    t = 0.05
    beats, clips, palabras_t = [], [], []
    for b in BEATS:
        a = audio.voz(b["say"])
        d_ = len(a) / audio.VOZ_SR
        beats.append(dict(b, t0=t, dur=d_ + 0.12))
        clips.append((t, a))
        palabras_t.append(PL.tiempos_palabras(b["say"], t, d_))
        t += d_ + 0.12
    total = t + 0.5
    print(f"[{slug}] {total:.1f}s, {len(beats)} escenas ({total / len(beats):.1f}s de media)", flush=True)
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    wav_voz = os.path.join(SALIDA, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    mus = audio.musica(total + 1, semilla=8, bpm=84, tono="A")
    for b in beats:
        if "sfx" in b:
            off, nombre = b["sfx"]
            off = b["dur"] * float(off[:-1]) / 100 if isinstance(off, str) else off
            s = audio.efecto(nombre)
            i = int((b["t0"] + off) * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * 1.7
    wav_mus = os.path.join(SALIDA, "musica.wav"); audio.sf.write(wav_mus, mus, audio.MUS_SR)
    with open(os.path.join(SALIDA, f"{slug}.es.srt"), "w", encoding="utf-8") as fsrt:
        for k, b in enumerate(beats, 1):
            a_, b_ = b["t0"], b["t0"] + b["dur"] - 0.12
            fsrt.write(f"{k}\n{fmt(a_)} --> {fmt(b_)}\n{b['say']}\n\n")
    print(f"[{slug}] ilustraciones…", flush=True)
    assets()
    preparar_adornos()
    muestra = "--muestra" in sys.argv
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    kb = 0
    nfr = int(total * FPS)
    cuadros = range(nfr) if not muestra else [int((b["t0"] + b["dur"] * 0.6) * FPS) for b in beats]
    for fi in cuadros:
        tg = fi / FPS
        while kb + 1 < len(beats) and tg >= beats[kb + 1]["t0"]:
            kb += 1
        if muestra:
            kb = max(i for i, b in enumerate(beats) if b["t0"] <= tg)
        b = beats[kb]; tl = tg - b["t0"]
        escena = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        b["f"](escena, ImageDraw.Draw(escena), tl, b["dur"])
        # cámara: empujón al empezar la escena + acercamiento lento
        z = 1.0 + 0.05 * (tl / b["dur"]) + 0.06 * math.exp(-tl * 9)
        nw, nh = int(W * z), int(H * z)
        escena = escena.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        # transición de entrada (sobre la escena, sin tocar textos ni adornos)
        if kb > 0 and tl < 0.28:
            escena = Image.fromarray(transicion(np.asarray(escena.convert("RGB")), tl, kb)).convert("RGBA")
        # confeti en el giro final y en el cierre
        if (GIRO is not None and kb == GIRO and tl < 3.0) or kb == len(beats) - 1:
            confeti(escena, tl, semilla=kb)
        # viñeta inferior para que los subtítulos se lean siempre
        escena.alpha_composite(VINETA)
        pts = palabras_t[kb]
        k_act = max([i for i, (t0, _) in enumerate(pts) if tg >= t0], default=-1)
        if k_act >= 0 and not PIXEL:
            g0 = (k_act // 4) * 4
            cap = PL.caption([p for _, p in pts[g0:g0 + 4]], k_act - g0, (tg - pts[k_act][0]) / 0.18)
            escena.alpha_composite(cap, (0, 1440))
        adornos(escena, tg, total, kb, tl, b)
        arr = np.asarray(escena.convert("RGB"))
        arr = destello_luz(arr, tg)
        if PIXEL:
            peq = pixelar(arr)
            if k_act >= 0:
                g0 = (k_act // 3) * 3
                cap = subtitulo_pixel([p for _, p in pts[g0:g0 + 3]], k_act - g0)
                salto = 2 if (tg - pts[k_act][0]) < 0.07 else 0
                peq.alpha_composite(cap, (0, 500 - cap.height // 2 + salto))
            arr = np.asarray(peq.convert("RGB")).repeat(PESC, 0).repeat(PESC, 1)
        temblor, flash = momento_clave(b, tl)
        if temblor:
            rng_t = np.random.default_rng(fi)
            paso = PESC if PIXEL else 1
            arr = np.roll(arr, (int(rng_t.integers(-temblor, temblor + 1)) // paso * paso,
                                int(rng_t.integers(-temblor, temblor + 1)) // paso * paso), (0, 1))
        if flash:
            arr = (arr.astype(np.float32) * (1 - flash) + 255 * flash).astype(np.uint8)
        if not PIXEL:
            arr = np.clip(arr.astype(np.int16) + GRANO[fi % len(GRANO)][..., None], 0, 255).astype(np.uint8)
        if muestra:
            Image.fromarray(arr).resize((360, 640), Image.NEAREST).save(os.path.join(SALIDA, f"muestra_{kb:02d}.png"))
        else:
            ff.stdin.write(arr.tobytes())
        if fi % (FPS * 10) == 0 and not muestra:
            print(f"[{slug}] {tg:5.1f}/{total:.1f}s", flush=True)
    if muestra:
        return
    ff.stdin.close(); ff.wait()
    final = os.path.join(SALIDA, f"{slug}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.3[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    "-shortest", final], check=True)
    for f_ in (mp4, wav_voz, wav_mus):
        os.remove(f_)
    print(f"[{slug}] OK → {final} ({total:.1f}s)", flush=True)


def fmt(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{int((r % 1) * 1000):03d}"


VINETA = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_v = np.zeros((H, W, 4), np.uint8)
_alpha = np.clip((np.arange(H) - 1250) / 400, 0, 1) * 200
_v[..., 3] = _alpha[:, None].astype(np.uint8)
VINETA = Image.fromarray(_v)

if __name__ == "__main__":
    render()
