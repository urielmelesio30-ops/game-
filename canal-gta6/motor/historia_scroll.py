# -*- coding: utf-8 -*-
"""Divulgación animada en 2D: por qué no puedes dejar de deslizar en TikTok."""
import math, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import historia as Hm
from historia import (A, C, W, H, persona, andar, ease, back, texto_grande, pegar, escalar, suave, anton)

audio.PRONUNCIA[:0] = [("B. F. Skinner", "Be Efe Eskíner"), ("Skinner", "Eskíner"), ("Aza Raskin", "Ása Ráskin"),
                       ("scroll", "escról"), ("TikTok", "Tik Tok")]
Hm.SALIDA = os.path.join(Hm.PL.SALIDA, "17-por-que-no-paras-de-deslizar")
_assets_base = Hm.assets

MORADO = (60, 40, 110)
ROSA = (255, 90, 140)
CIAN = (80, 220, 255)


def fondo_cuarto(c1=(70, 50, 120), c2=(30, 24, 60)):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        for i in range(40):
            u = i / 39
            col = tuple(int(c1[k] * (1 - u) + c2[k] * u) for k in range(3))
            d.rectangle(S(0, 1350 * u, W, 1350 * u + 36), fill=col)
        d.rectangle(S(0, 1350, W, H), fill=(40, 30, 50))
        d.rounded_rectangle(S(700, 300, 960, 640), radius=20 * s, fill=(30, 40, 90))
        d.line(S(830, 300, 830, 640), fill=(60, 70, 130), width=8 * s); d.line(S(700, 470, 960, 470), fill=(60, 70, 130), width=8 * s)
        d.ellipse(S(860, 340, 920, 400), fill=(250, 240, 200))
    return suave(W, H, dib)


def movil(contenido=None, ancho=420):
    h = int(ancho * 2.05)

    def dib(d, s):
        d.rounded_rectangle([0, 0, ancho * s - 1, h * s - 1], radius=60 * s, fill=(20, 20, 26))
        d.rounded_rectangle([18 * s, 18 * s, (ancho - 18) * s, (h - 18) * s], radius=46 * s, fill=(36, 36, 48))
        d.rounded_rectangle([(ancho / 2 - 50) * s, 30 * s, (ancho / 2 + 50) * s, 52 * s], radius=11 * s, fill=(10, 10, 14))
    return suave(ancho, h, dib)


def tragaperras():
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        d.rounded_rectangle(S(0, 120, 700, 900), radius=50 * s, fill=(200, 40, 60))
        d.rounded_rectangle(S(40, 60, 660, 200), radius=40 * s, fill=(240, 190, 60))
        d.rounded_rectangle(S(60, 260, 640, 620), radius=30 * s, fill=(30, 26, 40))
        d.rectangle(S(700, 300, 730, 600), fill=(150, 150, 160)); d.ellipse(S(690, 230, 770, 310), fill=(240, 60, 80))
    im = suave(780, 920, dib)
    d = ImageDraw.Draw(im)
    f = anton(90); t = "JACKPOT"
    d.text((350 - d.textlength(t, font=f) / 2, 78), t, font=f, fill=(200, 40, 60))
    return im


def paloma(picotea=0.0):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        d.ellipse(S(60, 120, 340, 300), fill=(150, 156, 172))
        d.polygon(S(60, 200, 0, 170, 20, 260), fill=(120, 126, 142))
        ang = math.radians(35 * picotea)
        hx, hy = 300 + math.sin(ang) * 40, 110 + (1 - math.cos(ang)) * 60 + 40 * picotea
        d.ellipse(S(hx - 60, hy - 60, hx + 60, hy + 60), fill=(130, 136, 152))
        d.ellipse(S(hx + 10, hy - 20, hx + 32, hy + 2), fill=(20, 20, 20))
        d.polygon(S(hx + 52, hy - 4, hx + 100, hy + 16, hx + 52, hy + 26), fill=(240, 170, 60))
        d.line(S(170, 290, 160, 360), fill=(220, 120, 90), width=10 * s); d.line(S(230, 290, 240, 360), fill=(220, 120, 90), width=10 * s)
    return suave(440, 380, dib)


def cerebro(brillo=0.0):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        base = (255, 150, 180)
        col = tuple(int(base[k] + (255 - base[k]) * brillo) for k in range(3))
        for (x, y, r) in ((180, 200, 150), (330, 170, 150), (460, 220, 140), (250, 330, 150), (410, 340, 140)):
            d.ellipse(S(x - r, y - r, x + r, y + r), fill=col)
        for k in range(6):
            d.arc(S(120 + k * 60, 140, 260 + k * 60, 300), 200, 330, fill=(220, 100, 140), width=10 * s)
    return suave(640, 520, dib)


def icono_bucle(tipo):
    def dib(d, s):
        def S(*v):
            return [x * s for x in v]
        if tipo == "reloj":
            d.ellipse(S(20, 20, 300, 300), fill=(250, 240, 220)); d.ellipse(S(40, 40, 280, 280), outline=(40, 40, 40), width=10 * s)
            d.line(S(160, 160, 160, 80), fill=(40, 40, 40), width=12 * s); d.line(S(160, 160, 220, 190), fill=ROSA, width=12 * s)
            d.rectangle(S(140, 0, 180, 24), fill=(40, 40, 40))
        elif tipo == "campana":
            d.chord(S(60, 40, 260, 260), 180, 360, fill=(255, 210, 80)); d.rectangle(S(60, 150, 260, 230), fill=(255, 210, 80))
            d.rectangle(S(40, 220, 280, 250), fill=(255, 210, 80)); d.ellipse(S(135, 245, 185, 295), fill=(255, 210, 80))
            d.line(S(30, 290, 290, 30), fill=(230, 40, 60), width=26 * s)
        elif tipo == "cama":
            d.rounded_rectangle(S(20, 160, 300, 260), radius=20 * s, fill=(120, 140, 220))
            d.rounded_rectangle(S(30, 120, 120, 170), radius=20 * s, fill=(250, 250, 250))
            d.rectangle(S(20, 160, 40, 300), fill=(90, 70, 50)); d.rectangle(S(280, 200, 300, 300), fill=(90, 70, 50))
    return suave(320, 320, dib)


def assets_extra():
    _assets_base()
    A["cuarto"] = fondo_cuarto()
    A["cuarto_osc"] = fondo_cuarto((30, 24, 60), (12, 10, 24))
    A["movil"] = movil()
    A["traga"] = tragaperras()
    A["reloj"], A["campana"], A["cama"] = icono_bucle("reloj"), icono_bucle("campana"), icono_bucle("cama")


ICONOS = ["😂", "🐶", "⚽", "🎮", "💄", "🍕"]
COLS = [(255, 120, 90), (90, 200, 140), (80, 150, 255), (255, 200, 70), (200, 110, 255), (255, 90, 140)]


def feed(fr, d, x, y, desliza, ancho=420):
    """Pantalla del móvil con tarjetas de vídeo que suben (scroll)."""
    m = A["movil"]
    pegar(fr, m, x, y)
    h = m.height
    x0, y0 = x - ancho / 2 + 18, y - h / 2 + 70
    alto = h - 140
    capa = Image.new("RGBA", (ancho - 36, alto), (0, 0, 0, 0))
    cd = ImageDraw.Draw(capa)
    off = desliza * alto
    for k in range(-1, 4):
        idx = int(math.floor(off / alto)) + k
        yy = idx * alto - off
        cd.rectangle((0, yy, ancho - 36, yy + alto - 10), fill=COLS[idx % len(COLS)])
        cd.ellipse(((ancho - 36) / 2 - 70, yy + alto / 2 - 70, (ancho - 36) / 2 + 70, yy + alto / 2 + 70), fill=(255, 255, 255, 140))
        cd.polygon([((ancho - 36) / 2 - 20, yy + alto / 2 - 35), ((ancho - 36) / 2 - 20, yy + alto / 2 + 35), ((ancho - 36) / 2 + 40, yy + alto / 2)], fill=COLS[idx % len(COLS)])
    fr.alpha_composite(capa, (int(x0), int(y0)))


def dedo(fr, d, x, y, fase):
    dy = -math.sin(fase * math.pi) * 160
    d.rounded_rectangle((x - 40, y + dy, x + 40, y + dy + 240), radius=40, fill=C["piel"])
    d.ellipse((x - 30, y + dy + 10, x + 30, y + dy + 60), fill=(250, 220, 200))


# ------------------------------------------------------------- escenas
def s_hora(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    pegar(fr, escalar(persona((90, 110, 170), brazo=(150, 150)), 1.2), W / 2 + 260, 1150)
    feed(fr, d, W / 2 - 120, 820, tl * 1.4)
    hora = 22 + min(1.0, tl / dur) * 1.0
    hh, mm = int(hora), int((hora % 1) * 60)
    pegar(fr, texto_grande(f"{hh:02d}:{mm:02d}", (255, 255, 255), 170), W / 2 + 230, 420)


def s_razon(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    pegar(fr, escalar(cerebro(0.3 + 0.3 * math.sin(tl * 4)), 1.2), W / 2, 760)
    pegar(fr, escalar(texto_grande("NO ES SOLO CULPA TUYA", (255, 255, 255), 100), max(0.05, back(tl / 0.4))), W / 2, 300)


def s_nombre(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    for k in range(16):
        a = k * math.pi / 8 + tl * 0.6
        d.line((W / 2 + math.cos(a) * 200, 760 + math.sin(a) * 200, W / 2 + math.cos(a) * 700, 760 + math.sin(a) * 700), fill=(90, 70, 160), width=8)
    pegar(fr, escalar(texto_grande("RECOMPENSA", ROSA, 170), max(0.05, back(tl / 0.35))), W / 2, 680)
    pegar(fr, escalar(texto_grande("VARIABLE", CIAN, 170), max(0.05, back((tl - 0.25) / 0.35))), W / 2, 880)


def s_traga(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    pegar(fr, A["traga"], W / 2, 800)
    x0 = W / 2 - 350 + 60
    for k in range(3):
        para = dur * (0.45 + 0.15 * k)
        gira = tl < para
        idx = int(tl * 14 + k * 3) % 6 if gira else [0, 0, 5][k]
        cx = x0 + 100 + k * 195
        d.rounded_rectangle((cx - 85, 640, cx + 85, 980), radius=20, fill=(250, 250, 250))
        f = anton(130)
        sim = ["7", "$", "%", "#", "!", "?"][idx]
        d.text((cx - d.textlength(sim, font=f) / 2, 720 + (int(tl * 40) % 30 if gira else 0)), sim, font=f, fill=COLS[idx])
    pegar(fr, texto_grande("¿EL PRÓXIMO SERÁ BUENO?", (255, 255, 255), 90), W / 2, 270)


def s_anzuelo(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    y = 300 + 420 * ease(tl / 0.8) + 20 * math.sin(tl * 3)
    d.line((W / 2, 0, W / 2, y), fill=(220, 220, 230), width=6)
    d.arc((W / 2 - 90, y - 10, W / 2 + 30, y + 160), 0, 200, fill=(200, 200, 210), width=18)
    pegar(fr, escalar(A["movil"], 0.35), W / 2 + 40, y + 200)
    pegar(fr, texto_grande("ENGANCHA", ROSA, 170), W / 2, 1150)


def s_skinner(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    d.rounded_rectangle((180, 520, 900, 1250), radius=30, fill=(220, 220, 230)); d.rounded_rectangle((210, 550, 870, 1220), radius=20, fill=(240, 240, 248))
    d.ellipse((700, 700, 780, 780), fill=(230, 50, 70))
    pegar(fr, paloma(0), 470, 1060)
    pegar(fr, texto_grande("AÑOS 50", (255, 214, 80), 150), W / 2, 300)


def s_paloma(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    d.rounded_rectangle((180, 520, 900, 1250), radius=30, fill=(220, 220, 230)); d.rounded_rectangle((210, 550, 870, 1220), radius=20, fill=(240, 240, 248))
    pico = abs(math.sin(tl * 12))
    d.ellipse((700, 700 + 10 * pico, 780, 780 + 10 * pico), fill=(230, 50, 70))
    pegar(fr, paloma(pico), 560, 1060)
    for k in range(5):
        if (int(tl * 3) + k * 7) % 5 == 0:
            d.ellipse((380 + k * 40, 1180, 400 + k * 40, 1200), fill=(200, 160, 80))
    pegar(fr, texto_grande("¡SIN PARAR!", (255, 255, 255), 150), W / 2, 300)


def s_dedo(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    feed(fr, d, W / 2, 760, tl * 2.5)
    dedo(fr, d, W / 2 + 60, 1050, (tl * 2.5) % 1)
    pegar(fr, texto_grande("TU DEDO, IGUAL", (255, 255, 255), 130), W / 2, 260)


def s_algoritmo(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    feed(fr, d, W / 2, 780, tl * 1.2)
    for k in range(8):
        y = 1150 - ((tl * 260 + k * 120) % 700)
        x = W / 2 + 260 + 40 * math.sin(tl * 3 + k)
        r = 34
        d.ellipse((x - r, y - r, x, y), fill=ROSA); d.ellipse((x - 4, y - r, x + r - 4, y), fill=ROSA)
        d.polygon([(x - r, y - r / 2), (x + r - 4, y - r / 2), (x - 2, y + r)], fill=ROSA)
    pegar(fr, texto_grande("APRENDE DE TI", CIAN, 140), W / 2, 260)


def s_dopamina(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    base = 1250
    for i, (txt, alto, col) in enumerate((("ESPERAR", 620, ROSA), ("RECIBIR", 300, CIAN))):
        x = 300 + i * 480
        h = alto * ease((tl - i * 0.3) / 0.8)
        d.rounded_rectangle((x - 120, base - h, x + 120, base), radius=20, fill=col)
        pegar(fr, texto_grande(txt, (255, 255, 255), 80), x, base + 80)
    pegar(fr, texto_grande("DOPAMINA", (255, 214, 80), 160), W / 2, 300)


def s_infinito(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    feed(fr, d, W / 2, 800, tl * 1.8)
    pegar(fr, texto_grande("SIN FINAL", CIAN, 160), W / 2, 260)
    t = tl * 2
    for k in range(40):
        a = k / 40 * 2 * math.pi
        x = W / 2 + math.sin(a + t) * 320
        y = 1370 + math.sin(2 * (a + t)) * 60
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=ROSA)


def s_raskin(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    pegar(fr, escalar(persona((70, 80, 100), pelo=(60, 40, 30), brazo=(165, 165)), 1.3), W / 2, 1050)
    u = back(tl / 0.4)
    pegar(fr, escalar(texto_grande("SE ARREPIENTE", ROSA, 140), max(0.05, u)), W / 2, 300)


def s_romper(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto_osc"])
    t = tl * 2
    for k in range(40):
        a = k / 40 * 2 * math.pi
        if tl > dur * 0.5 and 18 < k < 22:
            continue
        x = W / 2 + math.sin(a + t) * 320
        y = 800 + math.sin(2 * (a + t)) * 140
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=CIAN)
    pegar(fr, texto_grande("3 TRUCOS", (255, 214, 80), 170), W / 2, 300)


def s_truco(icono, txt):
    def f(fr, d, tl, dur):
        fr.alpha_composite(A["cuarto"])
        u = back(tl / 0.4)
        pegar(fr, escalar(A[icono], 1.6 * max(0.05, u)), W / 2, 820)
        pegar(fr, texto_grande(txt, (255, 255, 255), 150), W / 2, 300)
    return f


def s_final(fr, d, tl, dur):
    fr.alpha_composite(A["cuarto"])
    u = back(tl / 0.5)
    pegar(fr, escalar(A["masc"], 0.6 * max(0.05, u)), W / 2, 900 - 20 * abs(math.sin(tl * 4)))
    pegar(fr, texto_grande("¿VES? FUNCIONA", ROSA, 130), W / 2, 300)


BEATS = [
    dict(f=s_hora, say="¿Te ha pasado que abres TikTok cinco minutos… y de repente ha pasado una hora?"),
    dict(f=s_razon, say="No es solo culpa tuya. Hay una razón psicológica."),
    dict(f=s_nombre, say="Se llama recompensa variable.", sfx=(0.2, "golpe")),
    dict(f=s_traga, say="Funciona como una máquina tragaperras: nunca sabes si el próximo vídeo va a ser buenísimo… o un rollo."),
    dict(f=s_anzuelo, say="Y justo esa incertidumbre es lo que te engancha."),
    dict(f=s_skinner, say="En los años cincuenta, el psicólogo B. F. Skinner lo estudió con palomas."),
    dict(f=s_paloma, say="Cuando la comida salía de forma impredecible, picaban el botón sin parar."),
    dict(f=s_dedo, say="Tu dedo hace lo mismo con la pantalla."),
    dict(f=s_algoritmo, say="Y encima, la aplicación aprende lo que te gusta, así que cada vez acierta más."),
    dict(f=s_dopamina, say="Y la dopamina, la química de la motivación, se dispara sobre todo cuando esperas una recompensa… no cuando la recibes."),
    dict(f=s_infinito, say="Además, el scroll infinito no tiene final, así que tu cerebro nunca recibe la señal de parar."),
    dict(f=s_raskin, say="Su inventor, Aza Raskin, ha dicho públicamente que se arrepiente.", sfx=(0.2, "golpe")),
    dict(f=s_romper, say="¿Cómo romper el bucle? Tres trucos rápidos."),
    dict(f=s_truco("reloj", "1. TEMPORIZADOR"), say="Uno: ponte un temporizador."),
    dict(f=s_truco("campana", "2. SIN AVISOS"), say="Dos: quita las notificaciones."),
    dict(f=s_truco("cama", "3. MÓVIL LEJOS"), say="Tres: deja el móvil lejos de la cama."),
    dict(f=s_final, say="Y si has llegado hasta aquí… acabas de demostrar que funciona. Sígueme para más.", sfx=(0.3, "logro")),
]

Hm.BEATS = BEATS
Hm.GANCHO = 'POR QUÉ NO PUEDES DEJAR EL MÓVIL'
Hm.COLOR_MARCO = (255, 90, 140)
Hm.GIRO = 16
Hm.assets = assets_extra

if __name__ == "__main__":
    Hm.render()
