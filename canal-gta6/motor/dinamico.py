# -*- coding: utf-8 -*-
"""Formato DINÁMICO para retención: una frase corta = un "beat" de ~3 s con su
propia animación. Gancho en el primer segundo, poco texto en pantalla, golpes
de cámara, temblores y efectos en cada cambio. Máximo ~1:30.

Uso:  PREVIEW=1 python3 dinamico.py   |   python3 dinamico.py
"""
import math, os, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import render as R
import doomsday as D   # sprites, mascota, fondo de tormenta y pronunciación

audio.VELOCIDAD = float(os.environ.get("VELOCIDAD", "1.1"))  # algo más de ritmo
BW, BH = R.BW, R.BH
SUELO = 404          # donde apoyan los pies los personajes
GAP_BEAT = 0.12      # silencio entre frases: ritmo rápido
Y_PALABRA = 128

COLORES_PALABRA = ["verde", "amarillo", "blanco", "cian", "rosa"]
D.PERSONAJES["armadura"] = dict(piel="amarillo", traje="rojo", traje2="amarillo", cabeza="liso", extra="energia_azul")


# ------------------------------------------------------------- utilidades
def ease(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def pegar(frame, im, x, y):
    frame.alpha_composite(im, (int(x), int(y)))


def fig(nombre, t, escala, pose="quieto", espejo=False, blanco=False):
    im = D.figura_escalada(nombre, t, escala, pose, espejo)
    if blanco:
        a = im.getchannel("A")
        im = Image.new("RGBA", im.size, R.col("blanco") + (255,))
        im.putalpha(a)
    return im


def palabra_img(txt, color):
    """Palabra de impacto: lo más grande posible, en una o dos líneas."""
    for tam in (32, 24):
        f = R.fuente("pixel", tam)
        lineas = R.envolver(txt, f, R.ANCHO + 20)
        if len(lineas) <= 2 and all(R.ancho_txt(l, f) <= R.ANCHO + 20 for l in lineas):
            break
    else:
        f = R.fuente("pixel", 16)
        lineas = [txt]
    capas = [R.txt_img(l, f, color, "negro", contorno=True) for l in lineas]
    w = max(c.width for c in capas)
    out = Image.new("RGBA", (w, sum(c.height for c in capas) + 6 * (len(capas) - 1)), (0, 0, 0, 0))
    y = 0
    for c in capas:
        out.alpha_composite(c, ((w - c.width) // 2, y))
        y += c.height + 6
    return out


def lineas_velocidad(d, t, color="plomo", cx=BW // 2, cy=260):
    for k in range(18):
        a = k * (2 * math.pi / 18) + t * 0.6
        r0 = 80 + (t * 300 + k * 37) % 120
        x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        x1, y1 = cx + math.cos(a) * (r0 + 40), cy + math.sin(a) * (r0 + 40)
        d.line([(x0, y0), (x1, y1)], fill=R.col(color), width=2)


def polvo(d, x, y, dt):
    if dt > 0.5:
        return
    for k in range(8):
        a = math.pi + k * math.pi / 7
        r = 6 + dt * 70
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.3
        d.rectangle((px - 1, py - 1, px + 1, py + 1), fill=R.col("gris"))


def rayo(d, x0, y0, x1, y1, t, grosor=4):
    rng = np.random.default_rng(int(t * 15))
    pts = [(x0, y0)]
    for s in range(1, 8):
        pts.append((x0 + (x1 - x0) * s / 8, y0 + (y1 - y0) * s / 8 + int(rng.integers(-9, 10))))
    pts.append((x1, y1))
    d.line(pts, fill=R.col("verde"), width=grosor)
    d.line(pts, fill=R.col("blanco"), width=1)


# ------------------------------------------------------------- acciones (una por beat)
def accion(frame, d, b, tl, dur, tg):
    """Dibuja la animación del beat. Devuelve (temblor, destello) para la cámara."""
    a = b["a"]
    temblor, destello = 0, 0
    cx = BW // 2

    if a == "rayo":                       # Doom dispara a un héroe
        objetivo = b.get("objetivo", "thor")
        ida = fig("doom", tg, 4, "ataque")
        pegar(frame, ida, 20, SUELO - ida.height)
        golpe = tl > 0.35
        rec = int(ease((tl - 0.35) / 0.3) * 30) if golpe else 0
        ib = fig(objetivo, tg, 4, "quieto", espejo=True, blanco=golpe and int(tl * 12) % 2 == 0)
        pegar(frame, ib, BW - ib.width - 20 + rec, SUELO - ib.height)
        if 0.25 < tl < dur - 0.2:
            rayo(d, 20 + ida.width - 6, SUELO - 82, BW - ib.width + rec, SUELO - 82, tg, 5)
            temblor = 2
        if 0.25 < tl < 0.4:
            destello = 140

    elif a == "zoom":                     # primer plano de Doom subiendo
        u = ease(tl / 0.6)
        im = fig("doom", tg, 8)
        y = SUELO + 40 - im.height * u
        pegar(frame, im, cx - im.width // 2, y)
        if int(tl * 3) % 2 and u >= 1:
            ojo_y = int(y + 6 * 8 * 1.0 + 3 * 8)
            d.rectangle((cx - 24, ojo_y, cx + 24, ojo_y + 2), fill=R.col("verde"))

    elif a == "palabra":                  # palabra gigante + personaje pequeño + líneas de velocidad
        lineas_velocidad(d, tg, "pino")
        quien = b.get("quien", "doom")
        im = fig(quien, tg, 4, b.get("pose", "quieto"))
        pegar(frame, im, cx - im.width // 2, SUELO - im.height)

    elif a == "cambio":                   # el héroe de armadura se transforma en Doom
        mitad = dur * 0.45
        quien = "armadura" if tl < mitad else "doom"
        im = fig(quien, tg, 5, blanco=abs(tl - mitad) < 0.12)
        pegar(frame, im, cx - im.width // 2, SUELO - im.height)
        if quien == "armadura":
            d.rectangle((cx - 4, SUELO - im.height + 70, cx + 4, SUELO - im.height + 78), fill=R.col("cian"))
        if abs(tl - mitad) < 0.1:
            destello, temblor = 200, 5
        if tl > mitad:
            for i in range(12):
                ang = i * math.pi / 6 + tl * 3
                r = 60 + (tl - mitad) * 120
                d.rectangle((cx + math.cos(ang) * r - 2, 300 + math.sin(ang) * r * 0.6 - 2,
                             cx + math.cos(ang) * r + 2, 300 + math.sin(ang) * r * 0.6 + 2), fill=R.col("verde"))

    elif a == "comic":                    # Doom sale de las páginas de un cómic
        u = ease(tl / 0.5)
        x0, y0, w, h = cx - 80, 200, 160, 200
        d.rectangle((x0 + 4, y0 + 4, x0 + w + 4, y0 + h + 4), fill=R.col("negro"))
        d.rectangle((x0, y0, x0 + w, y0 + h), fill=R.col("crema"))
        for i in range(3):
            d.rectangle((x0 + 8, y0 + 10 + i * 62, x0 + w - 8, y0 + 64 + i * 62), outline=R.col("negro"), width=2)
        im = fig("doom", tg, 4, "ataque")
        pegar(frame, im, cx - im.width // 2, y0 + h - im.height * u - 10)
        if tl < 0.15:
            destello = 100

    elif a == "castillo":                 # rey de Latveria
        x0 = cx - 110
        d.rectangle((x0, 240, x0 + 220, SUELO), fill=R.col("plomo"))
        for k in range(0, 220, 20):
            d.rectangle((x0 + k, 228, x0 + k + 10, 240), fill=R.col("plomo"))
        for tx in (x0 - 20, x0 + 200):
            d.rectangle((tx, 190, tx + 40, SUELO), fill=R.col("uva"))
            d.polygon([(tx - 4, 190), (tx + 20, 160), (tx + 44, 190)], fill=R.col("pino"))
        onda = int(math.sin(tg * 6) * 3)
        d.line([(cx, 178), (cx, 230)], fill=R.col("gris"), width=2)
        d.polygon([(cx + 1, 180), (cx + 36, 188 + onda), (cx + 1, 198)], fill=R.col("verde"))
        im = fig("doom", tg, 4)
        pegar(frame, im, cx - im.width // 2, SUELO - im.height)

    elif a == "versus":                   # pantalla partida Doom vs rival
        rival = b.get("rival", "reed")
        d.polygon([(0, 150), (BW // 2 + 30, 150), (BW // 2 - 30, SUELO + 20), (0, SUELO + 20)], fill=R.col("pino"))
        d.polygon([(BW // 2 + 30, 150), (BW, 150), (BW, SUELO + 20), (BW // 2 - 30, SUELO + 20)], fill=R.col("marino"))
        u = ease(tl / 0.35)
        ia = fig("doom", tg, 4)
        ib = fig(rival, tg + 0.3, 4, "estirar", espejo=True)
        pegar(frame, ia, -ia.width + (ia.width + 20) * u, SUELO - ia.height)
        pegar(frame, ib, BW - (ib.width + 20) * u, SUELO - ib.height)
        if tl > 0.35:
            k = max(1.0, 3 - (tl - 0.35) * 12)
            vs = R.txt_img("VS", R.fuente("pixel", 32), "amarillo", "rojo")
            vs = vs.resize((int(vs.width * k), int(vs.height * k)), Image.NEAREST)
            pegar(frame, vs, cx - vs.width // 2, 250 - vs.height // 2)
            if tl < 0.5:
                temblor = 4

    elif a == "explosion":                # el experimento explota
        ia = fig("doom", tg, 4, "ataque")
        pegar(frame, ia, 30 - int(ease((tl - 0.4) / 0.3) * 20), SUELO - ia.height)
        d.rectangle((cx + 10, 300, cx + 70, SUELO), fill=R.col("plomo"))
        d.rectangle((cx + 20, 310, cx + 60, 340), fill=R.col("verde") if int(tg * 10) % 2 else R.col("pino"))
        if tl > 0.4:
            dt = tl - 0.4
            rr = dt * 160
            for ang in range(0, 360, 15):
                aa = math.radians(ang + dt * 120)
                for f_, c in ((1.0, "amarillo"), (0.7, "naranja"), (0.4, "rojo")):
                    px, py = cx + 40 + math.cos(aa) * rr * f_, 325 + math.sin(aa) * rr * f_ * 0.8
                    d.rectangle((px - 2, py - 2, px + 2, py + 2), fill=R.col(c))
            if dt < 0.12:
                destello = 230
            temblor = max(0, int(6 - dt * 8))

    elif a == "mascara":                  # la máscara cae sobre la cara
        im = fig("doom", tg, 8)
        x, y = cx - im.width // 2, SUELO + 40 - im.height
        pegar(frame, im, x, y)
        u = ease(tl / 0.4)
        mx0, my0 = x + 9 * 8, y + (3 + 1) * 8
        caida = int((1 - u) * -160)
        d.rectangle((mx0, my0 + caida, mx0 + 6 * 8 - 8, my0 + caida + 6 * 8), fill=R.col("gris"))
        d.rectangle((mx0 + 8, my0 + caida + 16, mx0 + 16, my0 + caida + 22), fill=R.col("verde"))
        d.rectangle((mx0 + 26, my0 + caida + 16, mx0 + 34, my0 + caida + 22), fill=R.col("verde"))
        if 0.38 < tl < 0.5:
            destello, temblor = 160, 4

    elif a == "magia":                    # círculos mágicos girando
        for k, (r, c, vel) in enumerate(((70, "verde", 1.5), (52, "cian", -2.2), (34, "amarillo", 3))):
            for i in range(24):
                ang = i * 2 * math.pi / 24 + tg * vel
                px, py = cx + math.cos(ang) * r, 280 + math.sin(ang) * r * 0.45
                if i % 3 != 1:
                    d.rectangle((px - 1, py - 1, px + 1, py + 1), fill=R.col(c))
        im = fig("doom", tg, 4, "ataque")
        pegar(frame, im, cx - im.width // 2, SUELO - im.height - int(math.sin(tg * 3) * 6) - 10)
        for i in range(10):
            ang = tg * 4 + i
            px, py = cx + math.cos(ang) * (40 + i * 6), 250 + math.sin(ang * 1.3) * 60
            d.point((px, py), fill=R.col("verde"))

    elif a == "robots":                   # ejército de Doombots marchando
        n = 3 + int(tl * 6)
        for fila, (yb, esc) in enumerate(((SUELO - 70, 2), (SUELO, 3))):
            for i in range(min(n, 9)):
                x = BW - ((tl * 70 + i * 52 + fila * 26) % (BW + 80))
                im = fig("doom", tg + i * 0.2, esc, "andar", espejo=True)
                pegar(frame, im, x, yb - im.height)
        temblor = 1 if int(tg * 4) % 2 else 0

    elif a == "dios":                     # dios emperador con corona y rayos de luz
        for k in range(12):
            ang = k * math.pi / 6 + tg * 0.8
            d.line([(cx, 270), (cx + math.cos(ang) * 260, 270 + math.sin(ang) * 260)], fill=R.col("amarillo" if k % 2 else "naranja"), width=3)
        im = fig("doom", tg, 5)
        x, y = cx - im.width // 2, SUELO - im.height
        pegar(frame, im, x, y)
        u = ease(tl / 0.5)
        cy = y + 6 - int((1 - u) * 120)
        d.polygon([(cx - 22, cy + 10), (cx - 22, cy - 6), (cx - 11, cy + 2), (cx, cy - 12), (cx + 11, cy + 2), (cx + 22, cy - 6), (cx + 22, cy + 10)], fill=R.col("amarillo"), outline=R.col("negro"))
        if 0.45 < tl < 0.6:
            destello = 150

    elif a == "desfile":                  # héroes que caen uno a uno con su nombre
        heroes = b["heroes"]
        n = len(heroes)
        for i, (h, nombre) in enumerate(heroes):
            t0 = i * (dur - 0.3) / n
            if tl < t0:
                continue
            dt = tl - t0
            esc = 3
            im = fig(h, tg + i * 0.3, esc)
            x = 18 + (i % 4) * 78
            ybase = SUELO if i < 4 else SUELO - 112
            y = ybase - im.height - int((1 - ease(dt / 0.25)) * 200)
            pegar(frame, im, x, y)
            polvo(d, x + im.width // 2, ybase, dt - 0.25)
            et = R.txt_img(nombre, R.fuente("texto", 20), "amarillo", "negro", contorno=True)
            pegar(frame, et, x + im.width // 2 - et.width // 2, ybase + 4)
            if dt < 0.1:
                temblor = 3

    elif a == "fecha":                    # calendario que pasa páginas hasta el 18
        x0, y0 = cx - 70, 190
        d.rectangle((x0 + 4, y0 + 4, x0 + 144, y0 + 174), fill=R.col("negro"))
        d.rectangle((x0, y0, x0 + 140, y0 + 170), fill=R.col("crema"))
        d.rectangle((x0, y0, x0 + 140, y0 + 40), fill=R.col("rojo"))
        mes = R.txt_img("DIC", R.fuente("pixel", 24), "blanco", None)
        pegar(frame, mes, cx - mes.width // 2, y0 + 8)
        u = ease(tl / 0.9)
        dia = max(1, int(1 + 17 * u))
        num = R.txt_img(str(dia), R.fuente("pixel", 40), "negro", None)
        pegar(frame, num, cx - num.width // 2, y0 + 80)
        if u < 1 and int(tl * 20) % 2:
            d.line([(x0, y0 + 105), (x0 + 140, y0 + 105)], fill=R.col("gris"), width=2)
        if u >= 1:
            for i in range(14):
                px = (i * 47 + tl * 60) % BW
                py = 150 + ((i * 83 + tl * 140) % 260)
                d.rectangle((px, py, px + 2, py + 2), fill=R.col(["verde", "amarillo", "rosa", "cian"][i % 4]))

    elif a == "multiverso":               # portales girando
        for k in range(6):
            r = (tl * 90 + k * 30) % 180
            c = ["verde", "cian", "uva", "rosa", "amarillo", "verde"][k]
            d.ellipse((cx - r, 270 - r * 0.6, cx + r, 270 + r * 0.6), outline=R.col(c), width=2)
        im = fig("doom", tg, 4, "ataque")
        pegar(frame, im, cx - im.width // 2, SUELO - im.height - int(ease(tl / 1.5) * 40))

    elif a == "pregunta":                 # la mascota pregunta, botones SÍ / NO
        m = D.mascota(tg, True)
        m = m.resize((m.width * 2, m.height * 2), Image.NEAREST)
        pegar(frame, m, cx - m.width // 2, SUELO - m.height - int(abs(math.sin(tg * 5)) * 10))
        for i, (txt, c) in enumerate((("SI", "verde"), ("NO", "rojo"))):
            k = 1 + 0.15 * (int(tg * 3 + i) % 2)
            bx = 40 + i * 190
            c_ = R.caja(int(90 * k), int(36 * k), borde=c)
            pegar(frame, c_, bx, 214)
            t = R.txt_img(txt, R.fuente("pixel", 16), "blanco", None)
            pegar(frame, t, bx + c_.width // 2 - t.width // 2, 214 + c_.height // 2 - 8)

    elif a == "seguir":                   # botón seguir + corazones
        m = D.mascota(tg, tl < dur - 0.6)
        m = m.resize((m.width * 2, m.height * 2), Image.NEAREST)
        pegar(frame, m, cx - m.width // 2, SUELO - m.height)
        pul = int(tg * 2) % 2 == 0
        bx, by = cx - 90, 175 + (2 if pul else 0)
        d.rectangle((bx, by, bx + 180, by + 44), fill=R.col("negro"))
        d.rectangle((bx + 1, by + 1, bx + 179, by + 43), fill=R.col("rojo"))
        t = R.txt_img("+ SEGUIR", R.fuente("pixel", 16), "blanco", None)
        pegar(frame, t, cx - t.width // 2, by + 14)
        cor = R.icono("corazon", "rosa").resize((14, 12), Image.NEAREST)
        for i in range(6):
            py = by - ((tl * 60 + i * 25) % 120)
            pegar(frame, cor, bx + 10 + i * 30, py)
    return temblor, destello


# ------------------------------------------------------------- guion por beats (máx. ~1:30)
VIDEO = dict(
    slug="12-doom-ritmo",
    titulo="Robert Downey Jr. es el VILLANO: ¿quién es Víctor von Doom? #Doomsday",
    beats=[
        dict(a="rayo", objetivo="thor", palabra="¡VILLANO!", say="Robert Downey Jr. vuelve a Marvel… ¡como el villano!"),
        dict(a="cambio", palabra="DE HÉROE A VILLANO", say="Fue Iron Man durante once años… y ahora se cambia de bando."),
        dict(a="zoom", palabra="VÍCTOR VON DOOM", say="Se llama Víctor von Doom."),
        dict(a="palabra", quien="doom", pose="ataque", palabra="NO ES UNO MÁS", say="Y ojo, que no es un villano cualquiera."),
        dict(a="palabra", palabra="DOCTOR MUERTE", say="En España, en los cómics, le llamábamos el Doctor Muerte."),
        dict(a="comic", palabra="1962", say="Nació en los cómics en 1962,"),
        dict(a="palabra", quien="doom", pose="ataque", palabra="LEE + KIRBY", say="de la mano de Stan Lee y Jack Kirby."),
        dict(a="castillo", palabra="LATVERIA", say="Es el rey de su propio país: Latveria."),
        dict(a="versus", rival="reed", palabra="SU ENEMIGO", say="Su gran enemigo: Reed Richards."),
        dict(a="explosion", palabra="¡BOOM!", say="Un experimento salió mal… y le explotó en la cara."),
        dict(a="mascara", palabra="LA MÁSCARA", say="Desde entonces, esa máscara de metal."),
        dict(a="rayo", objetivo="reed", palabra="VENGANZA", say="Y desde entonces, culpa a Reed de todo."),
        dict(a="magia", palabra="CIENCIA + MAGIA", say="Es un genio… y además, hechicero."),
        dict(a="robots", palabra="DOOMBOTS", say="Tiene un ejército de robots que son copias de sí mismo."),
        dict(a="dios", palabra="DIOS EMPERADOR", say="Y en los cómics, llegó a convertirse en un dios."),
        dict(a="palabra", quien="doom", pose="ataque", palabra="EL MEJOR VILLANO", say="Por eso muchos fans dicen que es el mejor villano de Marvel."),
        dict(a="desfile", heroes=[("thor", "Thor"), ("steve", "Steve"), ("reed", "Reed"), ("cosa", "La Cosa"),
                                   ("magneto", "Magneto"), ("profesor", "Xavier"), ("shuri", "Shuri"), ("loki", "Loki")],
             palabra="CONTRA TODOS", say="En Doomsday se enfrenta a medio Marvel: Thor, Steve Rogers, los 4 Fantásticos, los X-Men…"),
        dict(a="palabra", quien="magneto", palabra="VUELVEN LOS X-MEN", say="Incluso vuelven los X-Men de siempre, con Patrick Stewart e Ian McKellen."),
        dict(a="rayo", objetivo="thor", palabra="1 VS THOR", say="Y en el tráiler, frena a Thor con un solo gesto."),
        dict(a="fecha", palabra="ESTRENO", say="Se estrena el 18 de diciembre."),
        dict(a="multiverso", palabra="SECRET WARS 2027", say="Y prepara Secret Wars, en 2027."),
        dict(a="pregunta", palabra="¿TE CONVENCE?", say="¿Te convence Downey como Doom? Te leo."),
        dict(a="seguir", palabra="SÍGUEME", say="Y sígueme para más."),
    ],
)


def render(v):
    slug = v["slug"]
    base = os.path.join(R.SALIDA, slug)
    os.makedirs(base, exist_ok=True)
    suf = "_preview" if R.PREVIEW else ""
    # ---- voz y tiempos
    t = 0.05
    beats, subt, clips = [], [], []
    for b in v["beats"]:
        a = audio.voz(b["say"])
        d_ = len(a) / audio.VOZ_SR
        beats.append(dict(b, t0=t, dur=d_ + GAP_BEAT))
        subt.append((t, t + d_, b["say"]))
        clips.append((t, a))
        t += d_ + GAP_BEAT
    total = t + 0.6
    print(f"[{slug}] duración {total:.1f}s, {len(beats)} beats, media {total / len(beats):.1f}s/beat", flush=True)
    pista = np.zeros(int(total * audio.VOZ_SR) + 100, np.float32)
    for t0, a in clips:
        i = int(t0 * audio.VOZ_SR)
        pista[i:i + len(a)] += a
    wav_voz = os.path.join(base, f"voz{suf}.wav")
    audio.sf.write(wav_voz, pista, audio.VOZ_SR)
    # ---- música + efectos por beat
    mus = audio.chiptune(total + 1, semilla=7, bpm=132, tono="D")
    impacto = {"rayo", "explosion", "mascara", "versus", "dios", "comic"}
    for b in beats:
        for t_ef, k in [(b["t0"], 1), (b["t0"] + 0.1, 2 if b["a"] in impacto else 0)]:
            s = audio.blip(k)
            i = int(t_ef * audio.MUS_SR)
            j = min(len(mus), i + len(s))
            mus[i:j] += s[: j - i] * 2.0
        if b["a"] == "desfile":
            for k_ in range(len(b["heroes"])):
                s = audio.blip(0)
                i = int((b["t0"] + k_ * (b["dur"] - 0.3) / len(b["heroes"])) * audio.MUS_SR)
                mus[i:i + len(s)] += s[: max(0, min(len(s), len(mus) - i))] * 2.0
    wav_mus = os.path.join(base, f"musica{suf}.wav")
    audio.sf.write(wav_mus, mus, audio.MUS_SR)
    with open(os.path.join(base, f"{slug}.es.srt"), "w", encoding="utf-8") as fs:
        for k, (a_, b_, txt) in enumerate(subt, 1):
            fs.write(f"{k}\n{R.fmt_srt(a_)} --> {R.fmt_srt(b_)}\n{txt}\n\n")
    with open(os.path.join(base, "duracion.json"), "w") as fd:
        json.dump(dict(duracion=round(total, 1), beats=len(beats)), fd)
    # ---- imagen
    fondo = D.FondoTormenta("tormenta", "doom", 12)
    R.trocear.__defaults__ = (3, 18)  # subtítulos de 2-3 palabras: cambian más a menudo
    subs = R.construir_subtitulos(subt)
    palabras = [palabra_img(b["palabra"], COLORES_PALABRA[i % len(COLORES_PALABRA)]) for i, b in enumerate(beats)]
    aviso = [R.txt_img(ln, R.fuente("texto", 20), "gris") for ln in R.envolver(D.AVISO, R.fuente("texto", 20), R.ANCHO)]
    velo = Image.new("RGBA", (BW, BH), R.col("negro") + (60,))
    mp4 = os.path.join(base, f"video_mudo{suf}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{R.W}x{R.H}", "-r", str(R.FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if R.PREVIEW else "medium", "-tune", "animation",
                           "-crf", "26" if R.PREVIEW else "18", "-pix_fmt", "yuv420p", mp4], stdin=subprocess.PIPE)
    kb, ks = 0, 0
    for fi in range(int(total * R.FPS)):
        tg = fi / R.FPS
        while kb + 1 < len(beats) and tg >= beats[kb + 1]["t0"]:
            kb += 1
        b = beats[kb]
        tl = tg - b["t0"]
        off = R.MG + int(round(R.MG * 0.8 * math.sin(2 * math.pi * tg / 30)))
        frame = fondo.frame(tg, off).convert("RGBA")
        frame.alpha_composite(velo)
        d = ImageDraw.Draw(frame)
        temblor, destello = accion(frame, d, b, tl, b["dur"], tg)
        # palabra gigante: entra a golpe (escala 2 -> 1)
        pal = palabras[kb]
        k = max(1.0, 2.0 - tl * 8)
        im = pal if k == 1.0 else pal.resize((int(pal.width * k), int(pal.height * k)), Image.NEAREST)
        pegar(frame, im, BW // 2 - im.width // 2, Y_PALABRA - (im.height - pal.height) // 2)
        # subtítulos
        while ks + 1 < len(subs) and tg >= subs[ks + 1][0]:
            ks += 1
        s0, s1, simg = subs[ks]
        if s0 <= tg < s1:
            pegar(frame, simg, R.X0 + (R.ANCHO - simg.width) // 2, R.Y_SUBT - simg.height // 2 + (2 if tg - s0 < 0.06 else 0))
        if tg < 3:
            for j, ima in enumerate(aviso):
                pegar(frame, ima, R.X0 + (R.ANCHO - ima.width) // 2, 548 + j * 18)
        d.rectangle((0, 0, int(BW * tg / total), 2), fill=R.col("verde"))
        # cámara: golpe de zoom al empezar cada beat + temblor
        zoom = 1 + 0.07 * math.exp(-tl * 9)
        if zoom > 1.003:
            nw, nh = int(BW * zoom), int(BH * zoom)
            frame = frame.resize((nw, nh), Image.NEAREST).crop(((nw - BW) // 2, (nh - BH) // 2, (nw - BW) // 2 + BW, (nh - BH) // 2 + BH))
        arr = np.asarray(frame.convert("RGB")).copy()
        if temblor:
            rng = np.random.default_rng(fi)
            arr = np.roll(arr, (int(rng.integers(-temblor, temblor + 1)), int(rng.integers(-temblor, temblor + 1))), (0, 1))
        if destello:
            arr = (arr.astype(np.int16) + destello * (255 - arr.astype(np.int16)) // 255).clip(0, 255).astype(np.uint8)
        if R.ESC > 1:
            arr = arr.repeat(R.ESC, 0).repeat(R.ESC, 1)
        ff.stdin.write(arr.tobytes())
        if fi % (R.FPS * 20) == 0:
            print(f"[{slug}] {tg:5.1f}/{total:.1f}s", flush=True)
    ff.stdin.close(); ff.wait()
    final = os.path.join(base, f"{slug}{suf}.mp4")
    filtro = (f"[1:a]aresample=48000,{audio.CADENA_VOZ},pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];"
              "[2:a]volume=0.33[m];[m][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=300[md];"
              "[md][v2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-i", wav_voz, "-i", wav_mus, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    for f_ in (mp4, wav_voz, wav_mus):
        os.remove(f_)
    print(f"[{slug}] OK → {final} ({total:.1f}s)", flush=True)


def portada():
    fondo = D.FondoTormenta("tormenta", "doom", 12)
    img = fondo.frame(0.05, R.MG).convert("RGBA")
    d = ImageDraw.Draw(img)
    lineas_velocidad(d, 0.4, "pino", BW // 2, 330)
    for y, (txt, c) in zip((150, 190), (("RDJ ES EL", "blanco"), ("VILLANO", "verde"))):
        im = palabra_img(txt, c)
        pegar(img, im, BW // 2 - im.width // 2, y)
    ia = fig("doom", 0.0, 5, "ataque")
    pegar(img, ia, 10, SUELO + 20 - ia.height)
    ib = fig("thor", 0.0, 4, espejo=True, blanco=True)
    pegar(img, ib, BW - ib.width - 10, SUELO + 20 - ib.height)
    rayo(d, 10 + ia.width - 8, SUELO + 20 - 100, BW - ib.width, SUELO + 20 - 90, 1.0, 6)
    t = R.txt_img("¿QUIÉN ES DOOM?", R.fuente("pixel", 16), "negro", None)
    c = R.caja(t.width + 20, t.height + 14, borde="negro", relleno="amarillo")
    c.alpha_composite(t, (10, 7))
    pegar(img, c, BW // 2 - c.width // 2, SUELO + 40)
    out = os.path.join(R.SALIDA, VIDEO["slug"], "portada.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").resize((1080, 1920), Image.NEAREST).save(out, optimize=True)
    return out


if __name__ == "__main__":
    if "--portada" in sys.argv:
        print(portada())
    else:
        render(VIDEO)
        print(portada())
