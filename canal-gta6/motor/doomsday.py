# -*- coding: utf-8 -*-
"""Vídeo pixel art: ¿Quién es Víctor von Doom? (Vengadores: Doomsday).

Reutiliza el motor de render.py y añade:
  - sprites de personajes generados por código (originales: evocan a cada
    personaje con colores y rasgos sencillos, sin copiar diseños ni logos),
  - escenas nuevas: "personaje", "duelo", "reparto",
  - fondo "tormenta" (cielo verde con relámpagos y ciudad en ruinas),
  - la mascota del canal narrando, con la boca animada.

Uso:  PREVIEW=1 python3 doomsday.py   |   python3 doomsday.py
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio
import render as R
from perfil import mascota_capa, contorno

# ------------------------------------------------------------- pronunciación extra
audio.PRONUNCIA[:0] = [
    ("Vengadores: Doomsday", "Vengadores, Dúmsdei"), ("Vengadores: Secret Wars", "Vengadores, Sícret Guors"),
    ("Víctor von Doom", "Víctor fon Dum"), ("Doomsday", "Dúmsdei"), ("Doombots", "Dúmbots"), ("Doom", "Dum"),
    ("Robert Downey Jr.", "Róbert Dáuni Yúnior"), ("Iron Man", "Áiron Man"), ("Stan Lee", "Stan Li"),
    ("Jack Kirby", "Yak Kérbi"), ("Reed Richards", "Rid Ríchards"), ("Mister Fantástico", "Míster Fantástico"),
    ("Secret Wars", "Sícret Guors"), ("Chris Hemsworth", "Cris Jémsuorz"), ("Chris Evans", "Cris Évans"),
    ("Steve Rogers", "Estiv Róyers"), ("X-Men", "Équis Men"), ("Patrick Stewart", "Pátrik Estiúart"),
    ("Ian McKellen", "Ían Makélen"), ("Letitia Wright", "Letísia Ráit"), ("Tom Hiddleston", "Tom Jídelston"),
    ("Marvel", "Márvel"), ("Thor", "Tor"), ("Loki", "Lóki"), ("Shuri", "Shúri"),
]

AVISO = "Canal de fans. Sin relación con Marvel ni Disney."

# ------------------------------------------------------------- tema y fondo
R.TEMAS["doom"] = dict(cielo=["negro", "noche", "pino", "verde"], a="verde", b="amarillo")


class FondoTormenta(R.Fondo):
    def _estatico(self):
        w, h, hor = self.w, R.BH, self.hor
        img = np.zeros((h, w, 3), np.uint8)
        img[:hor] = R.dither_vertical(w, hor, ["negro", "noche", "pino", "pino", "verde"])
        img[hor:] = R.dither_vertical(w, h - hor, ["noche", "negro"])
        im = Image.fromarray(img)
        d = ImageDraw.Draw(im)
        rng = self.rng
        # ciudad en ruinas: edificios con la parte de arriba rota
        for capa, (c, hmin, hmax) in enumerate([("plomo", 60, 150), ("negro", 40, 110)]):
            x = 0
            while x < w:
                bw_ = int(rng.integers(16, 36))
                alt = int(rng.integers(hmin, hmax))
                pts = [(x, hor), (x, hor - alt)]
                for k in range(1, 4):
                    pts.append((x + bw_ * k // 4, hor - alt + int(rng.integers(-10, 14))))
                pts += [(x + bw_, hor - alt + int(rng.integers(0, 20))), (x + bw_, hor)]
                d.polygon(pts, fill=R.col(c))
                if capa == 1:
                    for wy in range(hor - alt + 16, hor - 4, 7):
                        for wx in range(x + 3, x + bw_ - 3, 5):
                            if rng.random() < 0.12:
                                d.rectangle((wx, wy, wx + 1, wy + 1), fill=R.col("verde"))
                x += bw_ + int(rng.integers(0, 5))
        return im

    def frame(self, t, off):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        w, hor = self.w, self.hor
        # aurora verde ondulante
        for banda in range(3):
            y0 = 120 + banda * 40
            for x in range(0, w, 2):
                y = y0 + int(10 * math.sin(x / 30 + t * 0.8 + banda))
                if (x // 2 + banda) % 3:
                    c_ = R.col("verde" if banda != 1 else "cian")
                    d.rectangle((x, y, x + 1, y + 1), fill=c_)
        # nubes de tormenta
        for (x, y, r, vel) in self.nubes:
            xx = int((x + t * vel * 5) % (w + 80)) - 40
            d.rectangle((xx, y - 40, xx + r * 3, y - 32), fill=R.col("noche"))
            d.rectangle((xx + r, y - 46, xx + r * 2, y - 40), fill=R.col("noche"))
        # relámpago cada ~5 s
        fase = t % 5.2
        if fase < 0.18:
            rng = np.random.default_rng(int(t // 5.2))
            x = int(rng.integers(40, w - 40))
            y = 0
            pts = [(x, y)]
            while y < hor - 40:
                y += int(rng.integers(10, 24))
                x += int(rng.integers(-12, 13))
                pts.append((x, y))
            d.line(pts, fill=R.col("verde"), width=3)
            d.line(pts, fill=R.col("blanco"), width=1)
        # suelo con rejilla verde
        for j in range(8):
            z = ((j + (t * 0.6) % 1.0) / 8)
            y = hor + int((R.BH - hor) * z ** 2)
            d.line([(0, y), (w, y)], fill=R.col("pino"))
        return im.crop((off, 0, off + R.BW, R.BH))


# ------------------------------------------------------------- sprites de personajes
# Figuras originales de 24x32 px dibujadas por código. Cada personaje se
# reconoce por colores y un rasgo simple (capa, casco, escudo...), no por su diseño oficial.
PERSONAJES = {
    "doom":     dict(piel="crema", traje="plomo", traje2="pino", capa="pino", cabeza="mascara", extra="energia"),
    "reed":     dict(piel="crema", traje="azul", traje2="negro", cabeza="pelo_castano", extra="estirar"),
    "cosa":     dict(piel="naranja", traje="naranja", traje2="azul", cabeza="roca", grande=True),
    "thor":     dict(piel="crema", traje="plomo", traje2="negro", capa="rojo", cabeza="pelo_rubio", extra="hacha"),
    "steve":    dict(piel="crema", traje="azul", traje2="rojo", cabeza="pelo_rubio_corto", extra="escudo"),
    "magneto":  dict(piel="crema", traje="rojo", traje2="morado", capa="morado", cabeza="casco_rojo"),
    "profesor": dict(piel="crema", traje="plomo", traje2="negro", cabeza="calvo", extra="silla"),
    "shuri":    dict(piel="cafe", traje="negro", traje2="uva", cabeza="mascara_negra"),
    "loki":     dict(piel="crema", traje="pino", traje2="amarillo", capa="pino", cabeza="cuernos"),
}
R.P.setdefault("cafe", (122, 78, 52))
R.P.setdefault("castano", (96, 58, 36))


def figura(nombre, t=0.0, pose="quieto"):
    s = PERSONAJES[nombre]
    C = lambda k: R.col(s[k]) if k in s and s[k] else None
    im = Image.new("RGBA", (24, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bob = 1 if int(t * 2.5) % 2 else 0
    g = 2 if s.get("grande") else 0
    sil = s.get("extra") == "silla"
    # capa detrás, ondeando
    if s.get("capa"):
        onda = int(math.sin(t * 5) * 1.5)
        d.polygon([(7 - g, 10 + bob), (16 + g, 10 + bob), (19 + g + onda, 29), (4 - g + onda, 29)], fill=C("capa"))
    # piernas (o silla)
    if sil:
        d.rectangle((6, 20, 17, 22), fill=R.col("gris"))
        d.ellipse((4, 22, 11, 29), outline=R.col("gris"))
        d.ellipse((13, 22, 20, 29), outline=R.col("gris"))
    else:
        paso = int(math.sin(t * 6) * 1) if pose == "andar" else 0
        d.rectangle((8 - g, 21, 10, 28 + paso), fill=C("traje2") or C("traje"))
        d.rectangle((13, 21, 15 + g, 28 - paso), fill=C("traje2") or C("traje"))
        d.rectangle((7 - g, 29 + min(0, paso), 10, 30), fill=R.col("negro"))
        d.rectangle((13, 29, 16 + g, 30), fill=R.col("negro"))
    # torso
    d.rectangle((8 - g, 11 + bob, 15 + g, 21), fill=C("traje"))
    d.rectangle((8 - g, 19, 15 + g, 20), fill=C("traje2"))       # cinturón
    # brazos
    ataque = pose == "ataque"
    if ataque:
        d.rectangle((16 + g, 12 + bob, 22, 14 + bob), fill=C("traje"))   # brazo extendido
        d.rectangle((21, 12 + bob, 23, 14 + bob), fill=C("traje2"))
    elif s.get("extra") == "estirar" and pose == "estirar":
        largo = 6 + int(abs(math.sin(t * 3)) * 6)
        d.rectangle((16, 13 + bob, 16 + largo, 14 + bob), fill=C("traje"))
    else:
        d.rectangle((16 + g, 12 + bob, 17 + g, 19 + bob), fill=C("traje"))
        d.rectangle((16 + g, 19 + bob, 17 + g, 20 + bob), fill=C("traje2"))
    d.rectangle((6 - g, 12 + bob, 7 - g, 19 + bob), fill=C("traje"))
    d.rectangle((6 - g, 19 + bob, 7 - g, 20 + bob), fill=C("traje2"))
    # cabeza
    cab = s.get("cabeza")
    hx0, hy0 = 9, 3 + bob
    piel = C("piel")
    if cab == "roca":
        d.rectangle((7, 3 + bob, 16, 11 + bob), fill=piel)
        for (x, y) in ((8, 5), (12, 4), (14, 8), (9, 9)):
            d.point((x, y + bob), fill=R.col("coral"))
        d.rectangle((9, 6 + bob, 10, 7 + bob), fill=R.col("azul"))
        d.rectangle((13, 6 + bob, 14, 7 + bob), fill=R.col("azul"))
    else:
        d.rectangle((hx0, hy0, hx0 + 5, hy0 + 7), fill=piel)
        ojos = R.col("negro")
        if cab == "mascara":
            d.rectangle((hx0 - 1, hy0 - 1, hx0 + 6, hy0 + 8), fill=R.col("pino"))   # capucha
            d.rectangle((hx0, hy0 + 1, hx0 + 5, hy0 + 7), fill=R.col("gris"))       # máscara de metal
            ojos = R.col("verde")
            d.line([(hx0 + 1, hy0 + 6), (hx0 + 4, hy0 + 6)], fill=R.col("plomo"))
        elif cab == "mascara_negra":
            d.rectangle((hx0, hy0, hx0 + 5, hy0 + 7), fill=R.col("negro"))
            d.point((hx0 + 2, hy0 - 1), fill=R.col("uva")); d.point((hx0 + 4, hy0 - 1), fill=R.col("uva"))
            ojos = R.col("blanco")
        elif cab == "casco_rojo":
            d.rectangle((hx0 - 1, hy0 - 1, hx0 + 6, hy0 + 3), fill=R.col("rojo"))
            d.rectangle((hx0 - 1, hy0 + 3, hx0, hy0 + 6), fill=R.col("rojo"))
            d.rectangle((hx0 + 5, hy0 + 3, hx0 + 6, hy0 + 6), fill=R.col("rojo"))
        elif cab == "cuernos":
            d.rectangle((hx0 - 1, hy0 - 1, hx0 + 6, hy0 + 1), fill=R.col("amarillo"))
            d.line([(hx0, hy0 - 1), (hx0 - 2, hy0 - 5)], fill=R.col("amarillo"))
            d.line([(hx0 + 5, hy0 - 1), (hx0 + 7, hy0 - 5)], fill=R.col("amarillo"))
            d.rectangle((hx0 - 1, hy0, hx0, hy0 + 7), fill=R.col("negro"))
            d.rectangle((hx0 + 5, hy0, hx0 + 6, hy0 + 7), fill=R.col("negro"))
        elif cab == "pelo_rubio":
            d.rectangle((hx0 - 1, hy0 - 1, hx0 + 6, hy0 + 1), fill=R.col("amarillo"))
            d.rectangle((hx0 - 2, hy0, hx0 - 1, hy0 + 9), fill=R.col("amarillo"))
            d.rectangle((hx0 + 6, hy0, hx0 + 7, hy0 + 9), fill=R.col("amarillo"))
        elif cab == "pelo_rubio_corto":
            d.rectangle((hx0 - 1, hy0 - 1, hx0 + 6, hy0 + 1), fill=R.col("amarillo"))
        elif cab == "pelo_castano":
            d.rectangle((hx0 - 1, hy0 - 1, hx0 + 6, hy0 + 1), fill=R.col("castano"))
            d.point((hx0 - 1, hy0 + 2), fill=R.col("gris")); d.point((hx0 + 6, hy0 + 2), fill=R.col("gris"))
        elif cab == "calvo":
            d.point((hx0 + 1, hy0), fill=R.col("blanco"))
        d.point((hx0 + 1, hy0 + 3), fill=ojos)
        d.point((hx0 + 4, hy0 + 3), fill=ojos)
    # accesorios
    ex = s.get("extra")
    if ex == "escudo":
        d.ellipse((1, 12 + bob, 9, 20 + bob), fill=R.col("rojo"))
        d.ellipse((3, 14 + bob, 7, 18 + bob), fill=R.col("blanco"))
        d.point((5, 16 + bob), fill=R.col("azul"))
    elif ex == "hacha":
        d.line([(19, 8 + bob), (19, 21 + bob)], fill=R.col("castano"), width=1)
        d.rectangle((17, 7 + bob, 22, 10 + bob), fill=R.col("gris"))
    elif ex == "energia" and (ataque or int(t * 4) % 2):
        d.point([(5, 20 + bob), (4, 19 + bob), (18, 20 + bob), (19, 19 + bob)], fill=R.col("verde"))
    return contorno(im)


def figura_escalada(nombre, t, escala, pose="quieto", espejo=False):
    im = figura(nombre, t, pose)
    if espejo:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((im.width * escala, im.height * escala), Image.NEAREST)


MASCOTA = {}


def mascota(t, hablando):
    abierta = hablando and int(t * 8) % 2 == 0
    if abierta not in MASCOTA:
        capa = mascota_capa(("crema", "coral"), "azul", "cian", boca_abierta=abierta)
        bbox = capa.getbbox()
        MASCOTA[abierta] = capa.crop(bbox)
    return MASCOTA[abierta]


# ------------------------------------------------------------- escenas nuevas
_construir_base = R.construir_escena
_pintar_base = R.pintar_dinamico


def intervalos_habla(tiempos, dur):
    """Tramos (relativos a la escena) en los que la voz está hablando, aproximados."""
    out = []
    for i, t0 in enumerate(tiempos):
        t1 = tiempos[i + 1] - R.GAP if i + 1 < len(tiempos) else dur - R.COLA
        out.append((t0, t1))
    return out


def construir_escena(esc, tema_n, tiempos, dur):
    tipo = esc["t"]
    tema = R.TEMAS[tema_n]
    habla = intervalos_habla(tiempos, dur)

    def t_item(k, n):
        return tiempos[max(0, len(tiempos) - n + k)]

    def t_fin(k, n):
        i = len(tiempos) - n + k + 1
        return tiempos[i] if i < len(tiempos) else dur

    if tipo in ("title", "cta"):
        sp, dyn, sfx = _construir_base(esc, tema_n, tiempos, dur)
        dyn.append(("mascota", dict(x=R.X0 + R.ANCHO // 2 - 30, y=360 if tipo == "title" else 352, habla=habla)))
        return sp, dyn, sfx

    if tipo == "personaje":
        sp, dyn, sfx = [], [], []
        y = R.cabecera(sp, esc["head"], tema)
        dyn.append(("figura", dict(nombre=esc["quien"], x=R.X0 + (R.ANCHO - 96) // 2, y=y - 6, escala=4, pose="quieto", t0=0.0)))
        sfx.append((0.1, 2))
        n = len(esc["items"])
        ft = R.fuente("texto", 20)
        yy = y + 132
        for k, it in enumerate(esc["items"]):
            t0, t1 = t_item(k, n), t_fin(k, n)
            lineas = R.envolver(it, ft, R.ANCHO - 20)
            alto = 12 + 16 * len(lineas)
            sp.append(R.Sprite(R.caja(R.ANCHO, alto, borde="plomo"), R.X0, yy, t0, anim="izq"))
            sp.append(R.Sprite(R.caja(R.ANCHO, alto, borde=tema["a"]), R.X0, yy, t0, t1, anim="izq"))
            fl = R.icono("flecha", "amarillo").resize((6, 10), Image.NEAREST)
            sp.append(R.Sprite(fl, R.X0 - 10, yy + alto // 2 - 5, t0, t1, anim="izq", parpadeo=True))
            for j, ln in enumerate(lineas):
                sp.append(R.Sprite(R.txt_img(ln, ft, "blanco"), R.X0 + 10, yy + 5 + j * 16, t0, anim="izq"))
                sp.append(R.Sprite(R.txt_img(ln, ft, "amarillo"), R.X0 + 10, yy + 5 + j * 16, t0, t1, anim="izq"))
            sfx.append((t0, 0))
            yy += alto + 8
        return sp, dyn, sfx

    if tipo == "duelo":
        sp, dyn, sfx = [], [], []
        y = R.cabecera(sp, esc["head"], tema)
        dyn.append(("duelo", dict(a=esc["izq"], b=esc["der"], y=y + 30, ts=tiempos, eventos=esc.get("eventos", []))))
        for k, ev in enumerate(esc.get("eventos", [])):
            if ev in ("rayo", "explosion"):
                sfx.append((tiempos[k] + 0.3, 1))
        et_a = R.txt_img(esc["nombres"][0], R.fuente("pixel", 8), tema["a"])
        et_b = R.txt_img(esc["nombres"][1], R.fuente("pixel", 8), "cian")
        sp.append(R.Sprite(et_a, R.X0 + 8, y + 170, 0.2, anim="arriba"))
        sp.append(R.Sprite(et_b, R.X1 - et_b.width - 8, y + 170, 0.35, anim="arriba"))
        vs = R.txt_img("VS", R.fuente("pixel", 24), "amarillo", "rojo")
        sp.append(R.Sprite(vs, R.X0 + (R.ANCHO - vs.width) // 2, y + 60, 0.5, anim="caer"))
        sfx.append((0.5, 2))
        return sp, dyn, sfx

    if tipo == "reparto":
        sp, dyn, sfx = [], [], []
        y = R.cabecera(sp, esc["head"], tema)
        n = len(esc["items"])
        colw = R.ANCHO // 2
        fila_h = min(118, (R.Y_FIN + 20 - y) // ((n + 1) // 2))
        ft = R.fuente("texto", 20)
        celdas = []
        for k, (quien, nombre, actor) in enumerate(esc["items"]):
            t0, t1 = t_item(k, n), t_fin(k, n)
            x = R.X0 + (k % 2) * colw
            yy = y + (k // 2) * fila_h
            sp.append(R.Sprite(R.caja(colw - 6, fila_h - 8, borde="plomo"), x, yy, t0, anim="arriba"))
            sp.append(R.Sprite(R.caja(colw - 6, fila_h - 8, borde=tema["a"]), x, yy, t0, t1, anim="arriba"))
            lineas_n = R.envolver(nombre, ft, colw - 64)
            for j, ln in enumerate(lineas_n):
                sp.append(R.Sprite(R.txt_img(ln, ft, tema["b"]), x + 54, yy + 8 + j * 16, t0, anim="arriba"))
            y_act = yy + 12 + 16 * len(lineas_n)
            for j, ln in enumerate(R.envolver(actor, ft, colw - 64)[:3]):
                sp.append(R.Sprite(R.txt_img(ln, ft, "blanco"), x + 54, y_act + j * 16, t0, anim="arriba"))
            celdas.append(dict(nombre=quien, x=x + 4, y=yy + 8, t0=t0, t1=t1))
            sfx.append((t0, 0))
        dyn.append(("reparto", dict(celdas=celdas)))
        return sp, dyn, sfx

    return _construir_base(esc, tema_n, tiempos, dur)


def pintar_dinamico(frame, d, items, t, tema_n):
    base = []
    for tipo, p in items:
        if tipo == "mascota":
            hablando = any(a <= t < b for a, b in p["habla"])
            m = mascota(t, hablando)
            frame.alpha_composite(m, (int(p["x"]), int(p["y"]) - (1 if hablando and int(t * 8) % 2 else 0)))
        elif tipo == "figura":
            if t >= p["t0"]:
                im = figura_escalada(p["nombre"], t, p["escala"], p["pose"])
                frame.alpha_composite(im, (int(p["x"]), int(p["y"])))
        elif tipo == "duelo":
            ts, ev = p["ts"], p["eventos"]
            k = max([i for i, t0 in enumerate(ts) if t >= t0], default=-1)
            actual = ev[k] if 0 <= k < len(ev) else "quieto"
            dt = t - (ts[k] if k >= 0 else 0)
            y = int(p["y"])
            pose_a = "ataque" if actual in ("rayo", "explosion") else "quieto"
            ia = figura_escalada(p["a"], t, 4, pose_a)
            ib = figura_escalada(p["b"], t + 0.4, 4, "estirar" if actual == "estirar" else "quieto", espejo=True)
            xa, xb = R.X0 + 4, R.X1 - ib.width - 4
            if actual == "explosion" and dt < 1.2:
                # explosión entre los dos: anillos de píxeles
                cx, cy = R.X0 + R.ANCHO // 2, y + 60
                rr = int(dt * 60)
                for ang in range(0, 360, 20):
                    a = math.radians(ang + dt * 90)
                    for r2 in (rr, rr * 0.6):
                        px, py = cx + int(math.cos(a) * r2), cy + int(math.sin(a) * r2 * 0.7)
                        d.rectangle((px - 1, py - 1, px + 1, py + 1), fill=R.col("amarillo" if r2 == rr else "naranja"))
                if dt < 0.08:
                    d.rectangle((0, 0, R.BW, R.BH), fill=R.col("blanco") + (120,))
            if actual == "rayo":
                # rayo verde en zigzag de Doom hacia el otro
                rng = np.random.default_rng(int(t * 12))
                x0, y0 = xa + ia.width - 4, y + 52
                x1 = xb + 20
                pts = [(x0, y0)]
                for s_ in range(1, 8):
                    pts.append((x0 + (x1 - x0) * s_ // 8, y0 + int(rng.integers(-8, 9))))
                pts.append((x1, y0))
                d.line(pts, fill=R.col("verde"), width=4)
                d.line(pts, fill=R.col("blanco"), width=1)
            if actual == "mascara" and int(t * 6) % 2:
                ia = ia.point(lambda v: min(255, v + 60))
            frame.alpha_composite(ia, (xa, y))
            frame.alpha_composite(ib, (xb, y))
        elif tipo == "reparto":
            for c in p["celdas"]:
                if t >= c["t0"]:
                    activo = c["t0"] <= t < c["t1"]
                    im = figura_escalada(c["nombre"], t if activo else 0.0, 2, "ataque" if activo and c["nombre"] == "doom" else "quieto")
                    dy = -2 if activo and int(t * 4) % 2 else 0
                    frame.alpha_composite(im, (c["x"], c["y"] + dy))
        else:
            base.append((tipo, p))
    if base:
        _pintar_base(frame, d, base, t, tema_n)


# Engancha las escenas nuevas en el motor
R.construir_escena = construir_escena
R.pintar_dinamico = pintar_dinamico
R.AVISO = AVISO
R.Fondo = FondoTormenta
R.ENCIMA = R.ENCIMA | {"reparto"}
R.CANAL = ""
R.LEMA = "Cine, juegos y un poco de todo"
R.logo_img = lambda tema: Image.new("RGBA", (1, 1), (0, 0, 0, 0))   # sin logo de canal: la cuenta es de temas variados

VIDEO = dict(
    slug="11-doomsday-victor-von-doom",
    tema="doom", fondo="tormenta",
    titulo="¿Quién es VÍCTOR VON DOOM? El villano de Vengadores: Doomsday explicado",
    miniatura=("¿QUIÉN ES", "VÍCTOR VON DOOM?", "DOOMSDAY"),
    escenas=[
        dict(t="title", head="¿QUIÉN ES VÍCTOR VON DOOM?", sub="El villano de Vengadores: Doomsday",
             say=["Robert Downey Jr. vuelve a Marvel. Pero esta vez, no como Iron Man… sino como el villano.",
                  "Se llama Víctor von Doom, y si no sabes quién es, en dos minutos te lo cuento."]),
        dict(t="personaje", quien="doom", head="VÍCTOR VON DOOM",
             items=["En España: el Doctor Muerte", "Creado por Stan Lee y Jack Kirby", "Debutó en 1962", "Gobierna Latveria"],
             say=["Víctor von Doom. En los cómics en España lo conocemos como el Doctor Muerte.",
                  "Lo crearon Stan Lee y Jack Kirby,",
                  "y apareció por primera vez en 1962, en el número cinco de Los 4 Fantásticos.",
                  "Es el gobernante de Latveria, un pequeño país europeo inventado por Marvel."]),
        dict(t="duelo", head="SU GRAN RIVAL", izq="doom", der="reed", nombres=("DOOM", "REED"),
             eventos=["quieto", "estirar", "explosion", "mascara"],
             say=["Su gran rival es Reed Richards, Mister Fantástico.",
                  "Los dos eran genios y estudiaron juntos.",
                  "Víctor hizo un experimento peligroso, Reed le avisó de un error en sus cálculos, y Víctor no le hizo caso. La máquina explotó.",
                  "Le dejó marcada la cara, desde entonces lleva esa máscara de metal… y culpa a Reed de todo."]),
        dict(t="bullets", head="¿POR QUÉ DA TANTO MIEDO?",
             items=["Genio científico", "Domina la magia", "Armadura y robots dobles", "Un país a sus órdenes"],
             say=["¿Y por qué da tanto miedo?",
                  "Es uno de los mayores genios de Marvel,",
                  "domina también la hechicería,",
                  "tiene una armadura y un ejército de robots que son copias de sí mismo, los Doombots,",
                  "y tiene un país entero a sus órdenes."]),
        dict(t="timeline", head="SECRET WARS", points=[("1984", "Roba el poder de un ser casi todopoderoso"), ("2015", "Se convierte en dios emperador")],
             say=["Y lo más importante para el cine: Secret Wars.",
                  "En el cómic de 1984, Doom llega a robarle el poder a un ser casi todopoderoso.",
                  "Y en el de 2015, se convierte en el dios emperador de un mundo hecho con los restos del multiverso."]),
        dict(t="duelo", head="DOOM CONTRA TODOS", izq="doom", der="thor", nombres=("DOOM", "THOR"),
             eventos=["quieto", "rayo"],
             say=["En los tráileres ya lo hemos visto en acción.",
                  "Incluso frena el ataque de Thor y le responde con su energía verde."]),
        dict(t="reparto", head="QUIÉN SALE EN DOOMSDAY",
             items=[("thor", "Thor", "Chris Hemsworth"), ("steve", "Steve Rogers", "Chris Evans"),
                    ("reed", "Los 4 Fantásticos", "Pedro Pascal y compañía"), ("magneto", "X-Men", "Stewart y McKellen"),
                    ("shuri", "Shuri", "Letitia Wright"), ("loki", "Loki", "Tom Hiddleston")],
             say=["Y enfrente tiene a medio Marvel.",
                  "Thor, con Chris Hemsworth.",
                  "Steve Rogers, con la vuelta de Chris Evans.",
                  "Los 4 Fantásticos, con Pedro Pascal como Reed Richards.",
                  "Los X-Men de las películas de siempre, con Patrick Stewart e Ian McKellen.",
                  "Shuri, la Pantera Negra, con Letitia Wright.",
                  "Y Loki, con Tom Hiddleston."]),
        dict(t="timeline", head="EL CAMINO AL ESTRENO",
             points=[("DIC 2025", "Avances: vuelve Steve Rogers"), ("JUL 2026", "Primer tráiler completo"), ("18 DIC 2026", "Estreno en cines")],
             say=["Las fechas.",
                  "En diciembre de 2025, los primeros avances confirmaron la vuelta de Steve Rogers.",
                  "En julio de 2026 llegó el primer tráiler completo.",
                  "Y la película se estrena el 18 de diciembre de 2026. Ojo, que en algunos países llega un día antes."]),
        dict(t="card", head="Y DESPUÉS...", text="Secret Wars: diciembre de 2027",
             say=["¿Y después? Doomsday prepara el terreno para Vengadores: Secret Wars, prevista para diciembre de 2027.",
                  "Y según varios medios, el tráiler final podría salir esta misma semana."]),
        dict(t="cta", say=["¿Qué te parece Robert Downey Jr. como Doom? Te leo en comentarios.",
                           "Y sígueme para más."]),
    ],
)


def portada():
    out = os.path.join(R.SALIDA, VIDEO["slug"], "portada.png")
    fondo = FondoTormenta("tormenta", "doom", 11)
    img = fondo.frame(0.05, R.MG).convert("RGBA")
    img.alpha_composite(Image.new("RGBA", img.size, R.col("negro") + (60,)))
    y = 150
    for txt, color, tam in (("¿QUIÉN ES", "blanco", 24), ("VÍCTOR", "verde", 32), ("VON DOOM?", "verde", 32)):
        im = R.txt_img(txt, R.fuente("pixel", tam), color, "negro" if color != "blanco" else "verde")
        img.alpha_composite(im, ((R.BW - im.width) // 2, y))
        y += im.height + 6
    doom = figura_escalada("doom", 0.0, 5, "ataque")
    img.alpha_composite(doom, ((R.BW - doom.width) // 2 - 10, y + 10))
    t = R.txt_img("DOOMSDAY", R.fuente("pixel", 16), "negro", None)
    c = R.caja(t.width + 20, t.height + 14, borde="negro", relleno="amarillo")
    c.alpha_composite(t, (10, 7))
    img.alpha_composite(c, ((R.BW - c.width) // 2, y + 180))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").resize((1080, 1920), Image.NEAREST).save(out, optimize=True)
    return out


if __name__ == "__main__":
    if "--portada" in sys.argv:
        print(portada())
    else:
        R.render_video(VIDEO, 11)
        print(portada())
