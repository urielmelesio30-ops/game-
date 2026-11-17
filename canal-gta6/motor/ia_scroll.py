# -*- coding: utf-8 -*-
"""«Por qué no puedes dejar de deslizar» con arte pixel IA (el cuarto de noche) + los personajes
recortados (la tele y el móvil gruñón) + objetos pixel dibujados a la misma escala de píxel.
Reutiliza el montaje de ia_eiffel.py. Personajes originales del canal."""
import math, os, sys, types
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia_eiffel as IE
import pixel_pro as PP
import historia_scroll as HS
from ia_eiffel import A, W, H, pixelado, texto_px, pegar, escalar, pop, camara, personaje, tinte, recorte9x16, cargar, limpiar

IE.SLUG = "17-por-que-no-paras-de-deslizar"
IE.SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "salida", IE.SLUG)
SUELO = 1230
K = 5   # escala de los objetos pixel (igual que el píxel del arte IA)


def capa_pp(dibujar):
    """Dibuja con las funciones de pixel_pro en una capa transparente 216x384 y la amplía x5."""
    c = Image.new("RGBA", (PP.CW, PP.CH), (0, 0, 0, 0))
    dibujar(c, ImageDraw.Draw(c))
    return pixelado(c, K)


def recursos():
    A["cuarto"] = cargar("escena_prueba_tele_movil.png")
    A["normal"] = limpiar(cargar("recortes/tele_normal.png"))
    A["movil"] = limpiar(cargar("recortes/movil_grunon.png"))
    A["ciudad_noche"] = recorte9x16(A["cuarto"], 860, 330, 380)
    A["estanteria"] = recorte9x16(A["cuarto"], 250, 420, 420)
    A["suelo"] = recorte9x16(A["cuarto"], 540, 1760, 300)


def fondo(c, clave, tl, dur, z0=1.0, z1=1.08, oscuro=60):
    c.paste(camara(A[clave], tl, dur, z0, z1))
    if oscuro:
        tinte(c, (10, 6, 30), oscuro)


def s0(c, tl, dur):
    c.paste(camara(A["cuarto"], tl, dur, 1.0, 1.15, 0.2, 0.2))
    h = 22 + min(0.999, tl / dur)
    pegar(c, pop(pixelado(PP.reloj_digital(f"{int(h):02d}:{int((h % 1) * 60):02d}"), K), tl), W / 2 + 180, 360)


def s1(c, tl, dur):
    fondo(c, "ciudad_noche", tl, dur)
    personaje(c, A["normal"], 300, SUELO, tl, escala=0.8)
    pegar(c, pop(pixelado(PP.cerebro(0.5 + 0.5 * math.sin(tl * 5)), K), tl - 0.15), 700, 760)
    pegar(c, pop(texto_px("?", 24, "amarillo"), tl), 330, 860)


def s2(c, tl, dur):
    fondo(c, "estanteria", tl, dur, oscuro=90)
    borde = PP.ROSA if int(tl * 4) % 2 else PP.CIAN
    caja = Image.new("RGBA", (150, 60), (0, 0, 0, 0))
    cd = ImageDraw.Draw(caja)
    cd.rectangle((0, 0, 149, 59), fill=PP.CON); cd.rectangle((2, 2, 147, 57), fill=borde); cd.rectangle((4, 4, 145, 55), fill=(16, 12, 26))
    for txt, y, col in (("RECOMPENSA", 16, "rosa"), ("VARIABLE", 34, "cian")):
        t = PP.texto(txt, 8, col)
        caja.alpha_composite(t, (75 - t.width // 2, y))
    pegar(c, pop(pixelado(caja, 6), tl), W / 2, 720)
    personaje(c, A["normal"], W / 2, SUELO, tl, escala=0.7)


def s3(c, tl, dur):
    fondo(c, "suelo", tl, dur, oscuro=40)
    tg = pixelado(PP.tragaperras(tl, dur), K)
    pegar(c, pop(tg, tl), 680, SUELO - tg.height / 2 + 40)
    personaje(c, A["normal"], 230, SUELO, tl, escala=0.6)


def s4(c, tl, dur):
    fondo(c, "ciudad_noche", tl, dur)
    d = ImageDraw.Draw(c)
    u = min(1, tl / 0.6)
    yh = 150 + 650 * u - max(0, tl - 1.0) * 300
    d.line((700, 0, 700, yh), fill=(230, 230, 240), width=6)
    d.arc((660, yh - 10, 740, yh + 60), 0, 200, fill=(210, 210, 224), width=10)
    pegar(c, escalar(A["movil"], 0.7), 700, yh + 170)
    personaje(c, A["normal"], 280, SUELO, tl, escala=0.75)
    pegar(c, texto_px("TE ENGANCHA", 16, "rosa"), W / 2, 380)


def caja_paloma(pico):
    def dib(c, d):
        PP.caja_skinner(c, d, pico)
    return capa_pp(dib)


def s5(c, tl, dur):
    fondo(c, "suelo", tl, dur, oscuro=50)
    pegar(c, caja_paloma(0), W / 2 + 60, H / 2 - 80)
    pegar(c, texto_px("AÑOS 50", 24, "amarillo"), W / 2, 380)


def s6(c, tl, dur):
    fondo(c, "suelo", tl, dur, oscuro=50)
    pegar(c, caja_paloma(int(tl * 10) % 2), W / 2 + 60, H / 2 - 80)
    pegar(c, texto_px("¡SIN PARAR!", 16, "blanco"), W / 2, 380)


def s7(c, tl, dur):
    c.paste(camara(A["cuarto"], tl, dur, 1.6, 1.9, 0.55, 0.25))
    col = [(255, 120, 90), (90, 200, 140), (80, 150, 255)][int(tl * 3) % 3]
    tinte(c, col, 40)
    pegar(c, texto_px("TU DEDO, IGUAL", 16, "blanco"), W / 2, 380)


def s8(c, tl, dur):
    fondo(c, "ciudad_noche", tl, dur)
    personaje(c, A["movil"], W / 2, SUELO, tl, escala=1.6)
    cor = pixelado(PP.R.icono("corazon", "rosa"), 7)
    for k in range(6):
        y = 1300 - ((tl * 300 + k * 160) % 900)
        pegar(c, cor, W / 2 + 230 * math.sin(tl * 2 + k), y)
    pegar(c, texto_px("APRENDE DE TI", 16, "cian"), W / 2, 380)


def s9(c, tl, dur):
    fondo(c, "suelo", tl, dur, oscuro=60)
    def dib(cc, d):
        for i, (txt, alto, colr) in enumerate((("ESPERAR", 150, PP.ROSA), ("RECIBIR", 56, PP.CIAN))):
            x = 92 + i * 72
            h = int(alto * min(1, max(0, (tl - i * 0.3) / 0.8))); h -= h % 4
            if h > 4:
                PP.bloque(d, x - 22, 300 - h, x + 22, 300, colr, tuple(min(255, v + 50) for v in colr), tuple(int(v * 0.7) for v in colr))
            t = PP.texto(txt, 8)
            cc.alpha_composite(t, (x - t.width // 2, 306))
    pegar(c, capa_pp(dib), W / 2 + 60, H / 2 - 30)
    personaje(c, A["normal"], 170, SUELO, tl, escala=0.55)
    pegar(c, texto_px("DOPAMINA", 24, "amarillo"), W / 2, 380)


def s10(c, tl, dur):
    fondo(c, "ciudad_noche", tl, dur)
    d = ImageDraw.Draw(c)
    for k in range(36):
        a = k / 36 * 2 * math.pi + tl * 2
        x = W / 2 + math.sin(a) * 300
        y = 800 + math.sin(2 * a) * 120
        d.rectangle((x - 10, y - 10, x + 10, y + 10), fill=PP.ROSA if k % 2 else PP.CIAN)
    personaje(c, A["movil"], W / 2, SUELO, tl, escala=0.8)
    pegar(c, texto_px("SIN FINAL", 24, "cian"), W / 2, 380)


def s11(c, tl, dur):
    fondo(c, "estanteria", tl, dur, oscuro=70)
    p = pixelado(PP.persona_pixel(), 9)
    pegar(c, p, W / 2, SUELO - p.height / 2 + 60)
    pegar(c, pop(texto_px("SE ARREPIENTE", 16, "rosa"), tl), W / 2, 380)


def s12(c, tl, dur):
    fondo(c, "ciudad_noche", tl, dur, oscuro=80)
    rota = tl > dur * 0.5
    def dib(cc, d):
        for k in range(7):
            if rota and k == 3:
                continue
            x = 60 + k * 16 + ((k - 3) * 6 if rota else 0)
            y = 170 + (5 if k % 2 else 0) + (abs(k - 3) * 4 if rota else 0)
            d.ellipse((x - 8, y - 5, x + 8, y + 5), outline=PP.CON, width=4)
            d.ellipse((x - 7, y - 4, x + 7, y + 4), outline=(196, 196, 210), width=2)
    pegar(c, capa_pp(dib), W / 2 + 40, H / 2)
    personaje(c, A["normal"], W / 2, SUELO, tl, escala=0.6)
    pegar(c, texto_px("3 TRUCOS", 24, "amarillo"), W / 2, 380)


def truco(tipo, num, palabra):
    def f(c, tl, dur):
        fondo(c, "estanteria" if tipo != "cama" else "suelo", tl, dur, oscuro=70)
        pegar(c, pop(pixelado(PP.icono(tipo), 7), tl), W / 2, 800)
        pegar(c, texto_px(f"TRUCO {num}/3", 8, "amarillo"), W / 2, 340)
        pegar(c, texto_px(palabra, 16, "blanco"), W / 2, 420)
        if tipo == "cama":
            personaje(c, A["movil"], 560 + tl * 160, SUELO, tl, escala=0.6, corre=True)
        else:
            personaje(c, A["normal"], 220, SUELO, tl, escala=0.55)
    return f


def s16(c, tl, dur):
    c.paste(camara(A["cuarto"], tl, dur, 1.0, 1.06))
    pegar(c, texto_px("¿VES?", 24, "rosa"), W / 2, 330)
    pegar(c, texto_px("FUNCIONA", 24, "rosa"), W / 2, 440)
    d = ImageDraw.Draw(c)
    rng = np.random.default_rng(3)
    cols = [(255, 90, 140), (80, 220, 255), (255, 214, 80), (120, 230, 140)]
    for i in range(50):
        x0 = rng.uniform(0, W); v = rng.uniform(500, 900)
        y = -40 + v * tl - (i % 7) * 60
        if 0 <= y <= H:
            d.rectangle((x0 + math.sin(tl * 4 + i) * 30, y, x0 + math.sin(tl * 4 + i) * 30 + 12, y + 8), fill=cols[i % 4])


IE.ESCENAS = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12,
              truco("reloj", 1, "TEMPORIZADOR"), truco("campana", 2, "SIN AVISOS"), truco("cama", 3, "MÓVIL LEJOS"), s16]
IE.HE = types.SimpleNamespace(BEATS=HS.BEATS)
IE.recursos = recursos
assert len(IE.ESCENAS) == len(HS.BEATS)

if __name__ == "__main__":
    IE.render()
