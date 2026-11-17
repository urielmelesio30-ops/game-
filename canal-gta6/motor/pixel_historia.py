# -*- coding: utf-8 -*-
"""Pixel art NATIVO (no pixelado): escenas dibujadas a 360x640 con personajes que
actúan la historia, un objeto grande en el centro y una sola línea de subtítulo.

Personajes originales del canal: la tele (mascota) y «Móvil», un móvil gruñón con patas.
Vídeo: por qué no puedes dejar de deslizar.

Uso:  python3 pixel_historia.py [--muestra]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import render as R
import historia as Hm
import historia_scroll as HS          # textos y algunas ilustraciones que se convierten a pixel
from perfil import mascota_capa, contorno

BW, BH, FPS = 360, 640, 30
RECORTE = (45, 80, 315, 560)   # se acerca la cámara: 270x480 → x4 = 1080x1920 (píxel gordo)
ESC = 4
W, H = (RECORTE[2] - RECORTE[0]) * ESC, (RECORTE[3] - RECORTE[1]) * ESC
SUELO = 392
SLUG = "17-por-que-no-paras-de-deslizar"
SALIDA = os.path.join(Hm.PL.SALIDA, SLUG)
col = R.col


# ------------------------------------------------------------- utilidades pixel
_cache = {}


def a_pixel(img, ancho, clave=None):
    """Convierte una ilustración a sprite pixel: reducción, alfa duro, paleta corta y contorno."""
    k = (clave, ancho)
    if clave and k in _cache:
        return _cache[k]
    alto = max(1, round(img.height * ancho / img.width))
    peq = img.resize((ancho, alto), Image.BOX)
    a = np.array(peq.getchannel("A")) > 110
    rgb = np.array(ImageOps.posterize(peq.convert("RGB"), 3))
    out = np.zeros((alto, ancho, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = a * 255
    im = contorno(Image.fromarray(out))
    if clave:
        _cache[k] = im
    return im


def pegar(c, im, x, y):
    c.alpha_composite(im, (int(round(x - im.width / 2)), int(round(y - im.height / 2))))


def pop(im, tl, dur=0.25):
    """Aparece creciendo a saltos (escala con vecino más cercano)."""
    u = min(1.0, max(0.0, tl / dur))
    k = [0.4, 0.7, 1.15, 1.0][min(3, int(u * 4))]
    return im if k == 1.0 else im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)


def texto(t, tam=16, color="blanco", sombra="negro"):
    return R.txt_img(t, R.fuente("pixel", tam), color, sombra, contorno=sombra is not None)


# ------------------------------------------------------------- fondo: el cuarto
def cuarto():
    im = Image.new("RGBA", (BW, BH), col("noche") + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, BW, SUELO), fill=(26, 30, 58))
    for y in range(3, SUELO, 6):                      # papel pintado de puntos
        for x in range(3 + (y // 6 % 2) * 3, BW, 6):
            d.point((x, y), fill=(40, 46, 84))
    for x in range(0, BW, 60):                         # juntas de los paneles
        d.line((x, 0, x, SUELO), fill=(20, 22, 44), width=2)
    # ventana con la ciudad de noche
    x0, y0, x1, y1 = 12, 26, 128, 152
    d.rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 9), fill=(110, 74, 46))
    d.rectangle((x0 - 8, y1 + 4, x1 + 8, y1 + 12), fill=(130, 90, 56))
    cielo = R.dither_vertical(x1 - x0, y1 - y0, ["negro", "marino", "uva"])
    im.paste(Image.fromarray(cielo), (x0, y0))
    rng = np.random.default_rng(4)
    x = x0
    while x < x1:
        bw_ = int(rng.integers(10, 22)); bh_ = int(rng.integers(30, 80))
        d.rectangle((x, y1 - bh_, min(x1 - 1, x + bw_), y1), fill=(16, 14, 34))
        for wy in range(y1 - bh_ + 5, y1 - 3, 7):
            for wx in range(x + 3, min(x1 - 3, x + bw_ - 2), 5):
                if rng.random() < 0.3:
                    d.rectangle((wx, wy, wx + 1, wy + 1), fill=(255, 210, 90))
        x += bw_ + 2
    d.line(((x0 + x1) // 2, y0, (x0 + x1) // 2, y1), fill=(110, 74, 46), width=4)
    d.line((x0, (y0 + y1) // 2, x1, (y0 + y1) // 2), fill=(110, 74, 46), width=4)
    # cuadro en la pared derecha
    d.rectangle((292, 120, 344, 196), outline=(60, 66, 110), width=3)
    # rodapié y suelo de ladrillo
    d.rectangle((0, SUELO, BW, SUELO + 3), fill=(40, 30, 40))
    for fila, y in enumerate(range(SUELO + 4, BH, 14)):
        osc = min(1.0, (y - SUELO) / 260)
        ladr = tuple(int(c * (1 - 0.45 * osc)) for c in (100, 62, 48))
        mort = tuple(int(c * (1 - 0.45 * osc)) for c in (64, 40, 34))
        d.rectangle((0, y, BW, y + 13), fill=ladr)
        d.line((0, y + 13, BW, y + 13), fill=mort)
        for x in range(-28 + (fila % 2) * 14, BW, 28):
            d.line((x, y, x, y + 13), fill=mort)
    # caja de madera a la derecha (donde se sube Móvil)
    d.rectangle((246, 334, 338, SUELO), fill=(122, 82, 50), outline=(70, 46, 30))
    for yy in (348, 362, 376):
        d.line((247, yy, 337, yy), fill=(96, 64, 40))
    d.line((246, 334, 338, SUELO), fill=(96, 64, 40)); d.line((338, 334, 246, SUELO), fill=(96, 64, 40))
    return im


# ------------------------------------------------------------- personajes
_masc = {}


def mascota(t, hablando=False):
    abierta = hablando and int(t * 8) % 2 == 0
    if abierta not in _masc:
        capa = mascota_capa(("crema", "coral"), "azul", "cian", boca_abierta=abierta)
        _masc[abierta] = capa.crop(capa.getbbox())
    return _masc[abierta]


def movil_pj(t, cara="enfadado", pantalla=(70, 160, 255), andar=0.0):
    """«Móvil»: un móvil gruñón con patas (personaje original)."""
    im = Image.new("RGBA", (34, 58), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    paso = int(math.sin(andar * 10) * 2) if andar else 0
    d.rectangle((9, 46, 12, 55 + paso), fill=(30, 30, 40)); d.rectangle((21, 46, 24, 55 - paso), fill=(30, 30, 40))
    d.rectangle((6, 54 + paso, 13, 57 + paso), fill=(20, 20, 26)); d.rectangle((20, 54 - paso, 27, 57 - paso), fill=(20, 20, 26))
    d.rounded_rectangle((3, 2, 30, 48), radius=4, fill=(34, 34, 44))
    d.rectangle((6, 7, 27, 42), fill=pantalla)
    d.rectangle((14, 4, 19, 5), fill=(70, 70, 90))
    neg = (20, 20, 30)
    if cara == "enfadado":
        d.line((9, 17, 14, 19), fill=neg, width=2); d.line((24, 17, 19, 19), fill=neg, width=2)
        d.rectangle((11, 21, 12, 23), fill=neg); d.rectangle((21, 21, 22, 23), fill=neg)
        d.line((12, 33, 21, 33), fill=neg, width=2); d.point([(11, 34), (22, 34)], fill=neg)
    elif cara == "feliz":
        d.rectangle((11, 20, 12, 23), fill=neg); d.rectangle((21, 20, 22, 23), fill=neg)
        d.line((11, 30, 16, 33), fill=neg, width=2); d.line((16, 33, 22, 30), fill=neg, width=2)
    else:  # sorpresa
        d.rectangle((11, 19, 13, 23), fill=neg); d.rectangle((20, 19, 22, 23), fill=neg)
        d.ellipse((14, 28, 19, 35), fill=neg)
    d.line((3, 26, 0, 32), fill=(34, 34, 44), width=2); d.line((30, 26, 33, 32), fill=(34, 34, 44), width=2)
    return contorno(im)


def brazo(d, x0, y0, x1, y1):
    d.line((x0, y0, x1, y1), fill=(30, 26, 40), width=4)
    d.line((x0, y0, x1, y1), fill=(232, 222, 200), width=2)
    d.rectangle((x1 - 2, y1 - 2, x1 + 2, y1 + 2), fill=(232, 222, 200))


def movil_mano(t, color_idx=0):
    im = Image.new("RGBA", (14, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cols = [(255, 120, 90), (90, 200, 140), (80, 150, 255), (255, 200, 70), (200, 110, 255)]
    d.rounded_rectangle((0, 0, 13, 23), radius=2, fill=(30, 30, 40))
    d.rectangle((2, 3, 11, 20), fill=cols[color_idx % len(cols)])
    return im


def burbuja(t, txt="?"):
    tx = texto(txt, 16)
    c = R.caja(tx.width + 10, tx.height + 8, borde="negro", relleno="blanco", sombra=False)
    c.alpha_composite(tx, (5, 4))
    d = ImageDraw.Draw(c)
    return c


def destellos(d, t, cx, cy, r=40, n=6, color=(255, 240, 160)):
    for k in range(n):
        a = k * 2 * math.pi / n + t * 2
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.6
        if (int(t * 6) + k) % 2:
            d.point([(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=color)


def confeti(d, t, n=50, semilla=1):
    rng = np.random.default_rng(semilla)
    cols = [(255, 90, 140), (80, 220, 255), (255, 214, 80), (120, 230, 140), (200, 120, 255)]
    for i in range(n):
        x0 = rng.uniform(0, BW); v = rng.uniform(140, 260)
        y = -10 + v * t - (i % 7) * 20
        if 0 <= y <= BH:
            x = x0 + math.sin(t * 4 + i) * 10
            d.rectangle((x, y, x + 2, y + 1 + i % 2), fill=cols[i % len(cols)])


# ------------------------------------------------------------- escenas
MX = 110  # posición habitual de la mascota


def de_pie(c, t, x=MX, habla=True, salto=0.0):
    m = mascota(t, habla)
    y = SUELO + 6 - m.height / 2 - salto - (1 if int(t * 3) % 2 else 0)
    pegar(c, m, x, y)
    return x, y, m


def movil_caja(c, t, cara="enfadado", x=292):
    p = movil_pj(t, cara)
    pegar(c, p, x, 334 - p.height / 2 + (1 if int(t * 2.5) % 2 else 0))


def s_hora(c, d, tl, dur):
    x, y, m = de_pie(c, tl)
    brazo(d, x + 30, y + 4, x + 46, y - 6)
    pegar(c, movil_mano(tl, int(tl * 4)), x + 50, y - 12)
    movil_caja(c, tl, "feliz")
    hora = 22 + min(0.999, tl / dur)
    caja = R.caja(150, 54, borde="rojo", relleno="negro")
    pegar(c, caja, BW / 2 + 60, 220)
    pegar(c, texto(f"{int(hora):02d}:{int((hora % 1) * 60):02d}", 24, "rojo", None), BW / 2 + 60, 221)


def s_razon(c, d, tl, dur):
    x, y, m = de_pie(c, tl)
    pegar(c, pop(burbuja(tl, "?"), tl), x + 34, y - 52)
    cer = a_pixel(HS.cerebro(0.3 + 0.3 * math.sin(tl * 4)), 120)
    pegar(c, pop(cer, tl - 0.2), BW / 2 + 40, 210 + 3 * math.sin(tl * 3))
    destellos(d, tl, BW / 2 + 40, 210, 70)
    movil_caja(c, tl, "sorpresa")


def s_cartel(c, d, tl, dur):
    de_pie(c, tl)
    borde = "rosa" if int(tl * 4) % 2 else "cian"
    caja = R.caja(250, 100, borde=borde, relleno="negro")
    pegar(c, pop(caja, tl), BW / 2, 200)
    if tl > 0.2:
        pegar(c, texto("RECOMPENSA", 16, "rosa"), BW / 2, 186)
        pegar(c, texto("VARIABLE", 16, "cian"), BW / 2, 214)
    movil_caja(c, tl, "enfadado")


def s_traga(c, d, tl, dur):
    tg = a_pixel(HS.tragaperras(), 150, "traga")
    cx, cy = BW / 2 + 20, 250
    pegar(c, pop(tg, tl), cx, cy)
    if tl > 0.25:
        x0, y0 = cx - tg.width / 2, cy - tg.height / 2
        for k in range(3):
            gira = tl < dur * (0.5 + 0.12 * k)
            idx = int(tl * 16 + k * 3) % 4 if gira else [0, 0, 3][k]
            rx = x0 + 18 + k * 33
            d.rectangle((rx, y0 + 52, rx + 26, y0 + 112), fill=(250, 250, 250))
            pegar(c, texto(["7", "$", "%", "?"][idx], 16, ["rojo", "verde", "azul", "rosa"][idx], None), rx + 13, y0 + 82 + (int(tl * 30) % 6 if gira else 0))
    x, y, m = de_pie(c, tl, x=88)
    tira = tl < dur * 0.4
    brazo(d, x + 30, y, cx + 82, cy - 40 + (30 if tira else 0))


def s_anzuelo(c, d, tl, dur):
    de_pie(c, tl)
    u = min(1, tl / 0.6)
    yh = 40 + 230 * u - (max(0, tl - 1.0) * 120)
    d.line((292, 0, 292, yh), fill=(220, 220, 230), width=1)
    d.arc((282, yh - 4, 300, yh + 14), 0, 200, fill=(200, 200, 210), width=2)
    if tl > 1.0:
        p = movil_pj(tl, "sorpresa")
        pegar(c, p, 292, yh + 30)
    else:
        movil_caja(c, tl, "enfadado")
    pegar(c, texto("TE ENGANCHA", 16, "rosa"), BW / 2 - 20, 150)


def s_skinner(c, d, tl, dur):
    de_pie(c, tl, x=88)
    d.rectangle((132, 170, 306, 350), fill=(210, 210, 220), outline=(60, 60, 70), width=3)
    d.rectangle((140, 178, 298, 342), fill=(236, 236, 244))
    d.rectangle((274, 230, 288, 244), fill=(230, 50, 70), outline=(60, 20, 30))
    pegar(c, a_pixel(HS.paloma(0), 70, "pal0"), 220, 300)
    pegar(c, texto("AÑOS 50", 24, "amarillo"), BW / 2, 150)


def s_paloma(c, d, tl, dur):
    de_pie(c, tl, x=88)
    d.rectangle((132, 170, 306, 350), fill=(210, 210, 220), outline=(60, 60, 70), width=3)
    d.rectangle((140, 178, 298, 342), fill=(236, 236, 244))
    pico = int(tl * 10) % 2
    d.rectangle((274, 230 + 2 * pico, 288, 244 + 2 * pico), fill=(230, 50, 70), outline=(60, 20, 30))
    pegar(c, a_pixel(HS.paloma(pico), 70, f"pal{pico}"), 240, 300)
    for k in range(4):
        if (int(tl * 3) + k * 2) % 4 == 0:
            d.rectangle((190 + k * 12, 334, 192 + k * 12, 336), fill=(200, 160, 80))
    pegar(c, texto("¡SIN PARAR!", 16, "blanco"), BW / 2, 150)


def s_dedo(c, d, tl, dur):
    x, y, m = de_pie(c, tl)
    fase = (tl * 3) % 1
    brazo(d, x + 30, y + 4, x + 50, y - 6 - int(math.sin(fase * math.pi) * 10))
    pegar(c, movil_mano(tl, int(tl * 3)), x + 54, y - 14)
    p = movil_pj(tl, "enfadado", pantalla=[(255, 120, 90), (90, 200, 140), (80, 150, 255)][int(tl * 3) % 3])
    pegar(c, p.resize((p.width * 3, p.height * 3), Image.NEAREST), BW / 2 + 70, 220)


def s_algoritmo(c, d, tl, dur):
    de_pie(c, tl)
    p = movil_pj(tl, "feliz")
    pegar(c, p.resize((p.width * 3, p.height * 3), Image.NEAREST), BW / 2 + 70, 220)
    cor = R.icono("corazon", "rosa").resize((14, 12), Image.NEAREST)
    for k in range(6):
        yy = 300 - ((tl * 80 + k * 40) % 220)
        pegar(c, cor, BW / 2 + 70 + 40 * math.sin(tl * 3 + k), yy)
    pegar(c, texto("APRENDE DE TI", 16, "cian"), BW / 2, 150)


def s_dopamina(c, d, tl, dur):
    de_pie(c, tl, x=88)
    for i, (txt, alto, colr) in enumerate((("ESPERAR", 190, "rosa"), ("RECIBIR", 80, "cian"))):
        x = 190 + i * 90
        h = int(alto * min(1, max(0, (tl - i * 0.3) / 0.8)))
        h -= h % 6
        d.rectangle((x - 26, SUELO - 20 - h, x + 26, SUELO - 20), fill=col(colr), outline=(20, 20, 30))
        pegar(c, texto(txt, 8), x, SUELO - 10)
    pegar(c, texto("DOPAMINA", 24, "amarillo"), BW / 2, 150)


def s_infinito(c, d, tl, dur):
    de_pie(c, tl)
    for k in range(36):
        a = k / 36 * 2 * math.pi + tl * 2
        x = BW / 2 + 40 + math.sin(a) * 90
        y = 220 + math.sin(2 * a) * 40
        d.rectangle((x - 2, y - 2, x + 2, y + 2), fill=col("rosa") if k % 2 else col("cian"))
    movil_caja(c, tl, "feliz")
    pegar(c, texto("SIN FINAL", 24, "cian"), BW / 2, 150)


def s_raskin(c, d, tl, dur):
    de_pie(c, tl, x=88)
    p = a_pixel(Hm.persona((70, 80, 100), pelo=(60, 40, 30), brazo=(165, 165)), 66, "raskin")
    pegar(c, p, 230, SUELO - p.height / 2 + 6)
    pegar(c, pop(texto("SE ARREPIENTE", 16, "rosa"), tl), BW / 2, 150)


def s_cadena(c, d, tl, dur):
    de_pie(c, tl)
    rota = tl > dur * 0.5
    for k in range(9):
        x = 150 + k * 20 + (8 * (k - 4) if rota and k != 4 else 0)
        y = 220 + (6 if k % 2 else 0) + ((k - 4) ** 2 if rota else 0)
        if rota and k == 4:
            continue
        d.ellipse((x - 9, y - 6, x + 9, y + 6), outline=(190, 190, 200), width=3)
    if rota and tl < dur * 0.5 + 0.3:
        destellos(d, tl, 230, 220, 20, 8)
    pegar(c, texto("3 TRUCOS", 24, "amarillo"), BW / 2, 150)


def s_truco(icono, txt):
    def f(c, d, tl, dur):
        de_pie(c, tl)
        ic = a_pixel(HS.icono_bucle(icono), 110, "ic" + icono)
        pegar(c, pop(ic, tl), BW / 2 + 50, 230)
        pegar(c, texto(txt, 16, "blanco"), BW / 2, 150)
        if icono == "cama":   # Móvil se va andando, lejos de la cama
            p = movil_pj(tl, "enfadado", andar=tl)
            pegar(c, p, 292 + tl * 40, 334 - p.height / 2)
        else:
            movil_caja(c, tl, "sorpresa")
    return f


def s_final(c, d, tl, dur):
    salto = abs(math.sin(tl * 5)) * 16
    de_pie(c, tl, x=BW / 2, salto=salto)
    pegar(c, pop(texto("¿VES? FUNCIONA", 16, "rosa"), tl), BW / 2, 150)
    confeti(d, tl)


ESCENAS = [s_hora, s_razon, s_cartel, s_traga, s_anzuelo, s_skinner, s_paloma, s_dedo, s_algoritmo,
           s_dopamina, s_infinito, s_raskin, s_cadena, s_truco("reloj", "1. TEMPORIZADOR"),
           s_truco("campana", "2. SIN AVISOS"), s_truco("cama", "3. MÓVIL LEJOS"), s_final]
assert len(ESCENAS) == len(HS.BEATS), (len(ESCENAS), len(HS.BEATS))


# ------------------------------------------------------------- subtítulo (una línea, estilo referencia)
def subtitulo(palabras, k):
    f = R.fuente("texto", 30)
    piezas = [R.txt_img(p.upper(), f, "amarillo" if i == k else "blanco", "negro", contorno=True) for i, p in enumerate(palabras[:k + 1])]
    w = sum(p.width for p in piezas) + 8 * (len(piezas) - 1)
    h = max(p.height for p in piezas)
    out = Image.new("RGBA", (w + 16, h + 10), (0, 0, 0, 0))
    ImageDraw.Draw(out).rectangle((0, 0, out.width - 1, out.height - 1), fill=(0, 0, 0, 120))
    x = 8
    for p in piezas:
        out.alpha_composite(p, (x, 5)); x += p.width + 8
    return out


def render():
    os.makedirs(SALIDA, exist_ok=True)
    t = 0.05
    beats, clips, palabras_t = [], [], []
    for b in HS.BEATS:
        a = audio.voz(b["say"])
        d_ = len(a) / audio.VOZ_SR
        beats.append(dict(b, t0=t, dur=d_ + 0.12))
        clips.append((t, a))
        palabras_t.append(Hm.PL.tiempos_palabras(b["say"], t, d_))
        t += d_ + 0.12
    total = t + 0.5
    print(f"[{SLUG}] {total:.1f}s, {len(beats)} escenas", flush=True)
    voz = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR); voz[i:i + len(a)] += a
    wav_voz = os.path.join(SALIDA, "voz.wav"); audio.sf.write(wav_voz, voz, audio.VOZ_SR)
    mus = audio.chiptune(total + 1, semilla=4, bpm=112, tono="C")
    for b in beats:
        if "sfx" in b:
            off, nombre = b["sfx"]
            off = b["dur"] * float(off[:-1]) / 100 if isinstance(off, str) else off
            s = audio.efecto(nombre)
            i = int((b["t0"] + off) * audio.MUS_SR); j = min(len(mus), i + len(s)); mus[i:j] += s[:j - i] * 1.7
        s = audio.blip(0)   # «pop» suave al aparecer cada objeto
        i = int((b["t0"] + 0.05) * audio.MUS_SR); mus[i:i + len(s)] += s[:max(0, min(len(s), len(mus) - i))] * 0.8
    wav_mus = os.path.join(SALIDA, "musica.wav"); audio.sf.write(wav_mus, mus, audio.MUS_SR)
    fondo = cuarto()
    muestra = "--muestra" in sys.argv
    mp4 = os.path.join(SALIDA, "mudo.mp4")
    ff = None if muestra else subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-tune", "animation", "-crf", "18", "-pix_fmt", "yuv420p", mp4],
        stdin=subprocess.PIPE)
    cuadros = range(int(total * FPS)) if not muestra else [int((b["t0"] + b["dur"] * 0.6) * FPS) for b in beats]
    for fi in cuadros:
        tg = fi / FPS
        kb = max(i for i, b in enumerate(beats) if b["t0"] <= tg)
        b = beats[kb]; tl = tg - b["t0"]
        c = fondo.copy()
        d = ImageDraw.Draw(c)
        ESCENAS[kb](c, d, tl, b["dur"])
        pts = palabras_t[kb]
        k_act = max([i for i, (t0, _) in enumerate(pts) if tg >= t0], default=-1)
        if k_act >= 0:
            g0 = (k_act // 3) * 3
            sub = subtitulo([p for _, p in pts[g0:g0 + 3]], k_act - g0)
            pegar(c, sub, BW / 2, 452 + (1 if tg - pts[k_act][0] < 0.07 else 0))
        arr = np.asarray(c.crop(RECORTE).convert("RGB"))
        # temblor y destello en los momentos clave
        temblor, flash = Hm.momento_clave(b, tl)
        if temblor:
            rng = np.random.default_rng(fi)
            arr = np.roll(arr, (int(rng.integers(-3, 4)), int(rng.integers(-3, 4))), (0, 1))
        if flash:
            arr = (arr * (1 - flash) + 255 * flash).astype(np.uint8)
        if kb > 0 and tl < 0.12:   # corte con tramado a negro
            p_ = 1 - tl / 0.12
            arr = arr.copy(); arr[R.BAYER_PANT[:arr.shape[0], :arr.shape[1]] < p_] = (12, 8, 22)
        if muestra:
            Image.fromarray(arr).save(os.path.join(SALIDA, f"muestra_{kb:02d}.png"))
            continue
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
