# -*- coding: utf-8 -*-
"""GTA 6: el chico que lo filtró desde un hotel. Datos (prensa del juicio, 2023):
- 18 sep 2022: se publican unos 90 vídeos del juego en desarrollo en un foro, la mayor filtración de la historia del videojuego.
- El autor, Arion Kurtaj (17 años entonces, miembro de Lapsus$), estaba en libertad bajo fianza por otros hackeos, alojado
  en un hotel y con prohibición de usar internet. Usó la tele del hotel, un móvil y un Amazon Fire Stick; entró en el Slack
  interno de Rockstar y amenazó con publicar el código fuente.
- Rockstar/Take-Two cifró el coste en unos 5 millones de dólares y miles de horas de trabajo.
- El primer tráiler (dic. 2023) también se filtró y Rockstar lo estrenó antes de tiempo; batió récords: unos 90 millones de
  visitas en YouTube en 24 horas.
- Los médicos lo declararon no apto para ser juzgado (autismo grave); el jurado determinó que cometió los hechos y el
  tribunal ordenó internarlo indefinidamente en un hospital de seguridad (dic. 2023).
Iconos y personajes originales: no se usa ningún logo ni imagen del juego."""
import math
from PIL import Image, ImageDraw

import serie as S
import anime as AN
import historia as Hm
from serie import (A, W, H, BL, AM, RO, VE, CI, RS, NA, CON, OK, ease, back, texto_grande, pegar, escalar, icono,
                   E_icono, E_varios, E_texto, E_contador, E_vs, E_persona, E_final, anim_pulso, anim_tachar, titulo, rayos, fondo, flota)

S.FONDOS["vice"] = AN.fondo_atardecer
VIOLETA = (190, 90, 255)


# ------------------------------------------------------------- iconos nuevos (originales)
def ic_hotel(d, S_, s):
    d.rectangle(S_(70, 90, 330, 390), fill=(240, 150, 190), outline=CON, width=OK * s)
    d.rectangle(S_(90, 30, 310, 90), fill=(40, 30, 60), outline=CON, width=OK * s)
    d.text((112 * s, 34 * s), "HOTEL", font=S.anton(48 * s), fill=(255, 230, 120))
    for y in range(120, 330, 60):
        for x in (105, 175, 245):
            d.rectangle(S_(x, y, x + 45, y + 38), fill=(120, 220, 255) if (x + y) % 3 else (255, 230, 120), outline=CON, width=4 * s)
    d.rectangle(S_(170, 330, 230, 390), fill=(90, 60, 50), outline=CON, width=5 * s)


def ic_tele(d, S_, s):
    d.rounded_rectangle(S_(20, 70, 380, 300), radius=20 * s, fill=(30, 30, 40), outline=CON, width=OK * s)
    d.rectangle(S_(40, 90, 360, 280), fill=(80, 200, 255))
    d.polygon(S_(170, 140, 170, 230, 245, 185), fill=BL)
    d.rectangle(S_(180, 300, 220, 350), fill=(30, 30, 40)); d.rectangle(S_(120, 350, 280, 370), fill=(30, 30, 40))


def ic_stick(d, S_, s):
    d.rounded_rectangle(S_(60, 150, 300, 250), radius=24 * s, fill=(30, 30, 40), outline=CON, width=OK * s)
    d.rectangle(S_(300, 170, 360, 230), fill=(170, 170, 180), outline=CON, width=6 * s)
    d.ellipse(S_(90, 185, 120, 215), fill=(80, 200, 255))
    d.text((140 * s, 172 * s), "TV", font=S.anton(48 * s), fill=(200, 200, 210))


def ic_movil(d, S_, s):
    d.rounded_rectangle(S_(120, 20, 280, 380), radius=30 * s, fill=(30, 30, 40), outline=CON, width=OK * s)
    d.rounded_rectangle(S_(135, 50, 265, 340), radius=12 * s, fill=(255, 120, 200))
    for y in (90, 150, 210):
        d.rounded_rectangle(S_(150, y, 250, y + 40), radius=10 * s, fill=BL)


def ic_chat(d, S_, s):
    d.rounded_rectangle(S_(20, 40, 300, 200), radius=40 * s, fill=(120, 220, 255), outline=CON, width=OK * s)
    d.polygon(S_(60, 190, 60, 250, 120, 195), fill=(120, 220, 255), outline=CON)
    d.rounded_rectangle(S_(120, 210, 380, 350), radius=40 * s, fill=(255, 150, 210), outline=CON, width=OK * s)
    for x in (100, 160, 220):
        d.ellipse(S_(x - 14, 106, x + 14, 134), fill=CON)
    d.line(S_(160, 260, 340, 260), fill=CON, width=10 * s); d.line(S_(160, 300, 300, 300), fill=CON, width=10 * s)


def ic_codigo(d, S_, s):
    d.rounded_rectangle(S_(20, 50, 380, 350), radius=20 * s, fill=(20, 24, 40), outline=CON, width=OK * s)
    d.rectangle(S_(20, 50, 380, 90), fill=(60, 60, 90))
    for x, c in ((50, RO), (80, AM), (110, VE)):
        d.ellipse(S_(x - 10, 60, x + 10, 80), fill=c)
    d.text((70 * s, 130 * s), "</>", font=S.anton(140 * s), fill=VE)


def ic_mazo(d, S_, s):
    d.rectangle(S_(40, 330, 360, 380), fill=(140, 90, 50), outline=CON, width=OK * s)
    d.line(S_(140, 240, 320, 100), fill=(160, 100, 60), width=26 * s)
    d.polygon(S_(40, 170, 120, 70, 240, 160, 160, 260), fill=(130, 80, 40), outline=CON)
    d.rectangle(S_(80, 300, 320, 334), fill=(110, 70, 40), outline=CON, width=6 * s)


def ic_hospital(d, S_, s):
    d.rectangle(S_(50, 110, 350, 390), fill=(240, 244, 250), outline=CON, width=OK * s)
    d.rectangle(S_(150, 30, 250, 130), fill=RO, outline=CON, width=6 * s)
    d.rectangle(S_(185, 45, 215, 115), fill=BL); d.rectangle(S_(165, 65, 235, 95), fill=BL)
    for y in (170, 250):
        for x in (80, 170, 260):
            d.rectangle(S_(x, y, x + 60, y + 50), fill=(150, 200, 240), outline=CON, width=4 * s)
    for x in range(80, 330, 40):   # rejas
        d.line(S_(x, 170, x, 300), fill=(90, 90, 100), width=4 * s)


def ic_trailer(d, S_, s):
    d.rounded_rectangle(S_(20, 80, 380, 300), radius=24 * s, fill=(170, 80, 255), outline=CON, width=OK * s)
    d.polygon(S_(160, 130, 160, 250, 265, 190), fill=BL)
    d.rectangle(S_(20, 320, 380, 340), fill=(80, 80, 90)); d.rectangle(S_(20, 320, 300, 340), fill=(255, 90, 200))


def ic_dinero(d, S_, s):
    d.ellipse(S_(60, 120, 340, 390), fill=(120, 190, 90), outline=CON, width=OK * s)
    d.polygon(S_(140, 130, 260, 130, 290, 50, 110, 50), fill=(120, 190, 90), outline=CON)
    d.text((160 * s, 180 * s), "$", font=S.anton(150 * s), fill=BL)


def ic_alarma(d, S_, s):
    d.polygon(S_(200, 20, 390, 360, 10, 360), fill=AM, outline=CON, width=OK * s)
    d.text((168 * s, 110 * s), "!", font=S.anton(200 * s), fill=CON)


for _n, _f in list(globals().items()):
    if _n.startswith("ic_") and callable(_f):
        S.ICONOS[_n[3:]] = _f


def chico(expr_brazos=(20, -20)):
    return Hm.persona((40, 40, 56), pelo=(40, 30, 26), brazo=expr_brazos)


# ------------------------------------------------------------- escenas especiales
def e_gancho(fr, d, tl, dur):
    fr.alpha_composite(fondo("vice"))
    AN.lineas_foco(fr, tl, (255, 255, 255), cy=820, alfa=120)
    pegar(fr, escalar(icono("hotel"), 1.3 * max(0.05, back(tl / 0.4))), W / 2, 820 + flota(tl))
    if tl > 0.6:
        u = back((tl - 0.6) / 0.35)
        pegar(fr, escalar(icono("stick"), 0.6 * max(0.05, u)).rotate(-15 * math.sin(tl * 4), expand=True), 830, 1120)
    titulo(fr, "LO FILTRÓ DESDE UN HOTEL", tl, AM, 100)


def e_noventa(fr, d, tl, dur):
    fr.alpha_composite(fondo("morado"))
    n = int(90 * ease(tl / (dur * 0.7)))
    for i in range(min(n, 30)):
        x = 90 + (i % 6) * 180
        y = 470 + (i // 6) * 140
        pegar(fr, escalar(icono("trailer"), 0.3), x, y)
    pegar(fr, texto_grande(f"{n} VÍDEOS", AM, 180), W / 2, 1220)
    titulo(fr, "SEPTIEMBRE DE 2022", tl, BL, 100, 300)


def e_como(fr, d, tl, dur):
    fr.alpha_composite(fondo("vice"))
    items = [("tele", "LA TELE DEL HOTEL"), ("movil", "UN MÓVIL"), ("stick", "UN FIRE STICK")]
    for i, (ico, et) in enumerate(items):
        t0 = 0.4 + i * dur * 0.22
        u = back((tl - t0) / 0.3)
        if u > 0:
            y = 520 + i * 300
            pegar(fr, escalar(icono(ico), 0.62 * u), 260, y + flota(tl + i, 3, 8))
            pegar(fr, escalar(texto_grande(et, AM if i == 2 else BL, 78), u), 690, y)
    titulo(fr, "¿CON QUÉ LO HIZO?", tl, RS, 110, 300)


def e_hackeo(fr, d, tl, dur):
    fr.alpha_composite(fondo("noche"))
    pegar(fr, escalar(icono("codigo"), 1.5), W / 2, 800)
    rng_y = int(tl * 10)
    for k in range(10):   # «lluvia» de código
        x = (k * 113 + 40) % W
        y = (tl * 500 + k * 170) % 1300 + 250
        pegar(fr, texto_grande("10" if (k + rng_y) % 2 else "01", VE, 50), x, y)
    pegar(fr, escalar(icono("chat"), 0.5 * max(0.05, back((tl - 0.4) / 0.3))), 820, 1150)
    titulo(fr, "SE COLÓ EN SU CHAT INTERNO", tl, VE, 90)


def e_records(fr, d, tl, dur):
    fr.alpha_composite(fondo("vice"))
    AN.lineas_foco(fr, tl, (255, 240, 200), cy=760, alfa=110)
    pegar(fr, escalar(icono("trailer"), 1.0 + 0.05 * math.sin(tl * 6)), W / 2, 700)
    n = int(90 * ease(tl / (dur * 0.6)))
    pegar(fr, texto_grande(f"{n} MILLONES", AM, 160), W / 2, 1020)
    pegar(fr, texto_grande("DE VISITAS EN 24 H", BL, 80), W / 2, 1170)
    titulo(fr, "¡RÉCORD!", tl, RS, 150, 330)


# ------------------------------------------------------------- guion
BEATS = [
    dict(f=e_gancho, say="Antes de que salga GTA 6, tienes que conocer al chico que lo filtró… desde la habitación de un hotel.", sfx=(0.15, "boom")),
    dict(f=e_noventa, say="Septiembre de 2022. Aparecen en internet noventa vídeos del juego, sin terminar."),
    dict(f=E_icono("rojo", "fuego", "LA MAYOR FILTRACIÓN DE LA HISTORIA", AM, 1.3), say="Es la mayor filtración de la historia de los videojuegos.", sfx=(0.3, "golpe")),
    dict(f=E_contador("morado", 17, "AÑOS", "EL CULPABLE TENÍA…", RS), say="Y el culpable tenía solo diecisiete años."),
    dict(f=E_persona("ciudad_noche", (40, 40, 56), "ARION KURTAJ", ico="alarma", sub="YA ESTABA EN LIBERTAD BAJO FIANZA"), say="Se llamaba Arion Kurtaj, y ya estaba en libertad bajo fianza por otros hackeos."),
    dict(f=E_icono("noche", "hotel", "SIN ORDENADOR NI INTERNET", BL, 1.3, extra=anim_pulso("prohibido", 820, 1130, 0.35, 0.5)), say="Lo tenían alojado en un hotel, sin ordenador y con prohibición de usar internet."),
    dict(f=e_como, say="¿Y cómo lo hizo? Con la tele del hotel, un móvil… y un Fire Stick de Amazon.", sfx=("78%", "golpe")),
    dict(f=e_hackeo, say="Así se coló en el chat interno de trabajo de Rockstar, y publicó los vídeos."),
    dict(f=E_icono("rojo", "codigo", "AMENAZÓ CON MÁS", RO, 1.3, gira=6), say="Y amenazó con publicar también el código del juego."),
    dict(f=E_contador("vice", 5, "MILLONES DE DÓLARES", "LO QUE COSTÓ A ROCKSTAR", VE, "dinero"), say="A Rockstar le costó unos cinco millones de dólares, y miles de horas de trabajo."),
    dict(f=E_texto("morado", "PERO OJO", "AÚN HAY MÁS", AM, RS), say="Pero ojo, que la historia no acaba ahí.", sfx=(0.1, "golpe")),
    dict(f=E_icono("vice", "trailer", "EL TRÁILER TAMBIÉN SE FILTRÓ", BL, 1.2), say="Un año después, el primer tráiler también se filtró… y Rockstar tuvo que estrenarlo antes de tiempo."),
    dict(f=e_records, say="Y aun así batió récords: unos noventa millones de visitas en YouTube en veinticuatro horas.", sfx=(0.4, "subida")),
    dict(f=E_vs("noche", chico(), "mazo", "EL CHICO", "EL JUICIO", "¿Y QUÉ LE PASÓ?", BL, AM), say="¿Y el chico? Los médicos dijeron que no estaba en condiciones de ser juzgado."),
    dict(f=E_icono("noche", "hospital", "INTERNADO SIN FECHA DE SALIDA", RO, 1.3), say="Y el tribunal ordenó internarlo en un hospital de seguridad, sin fecha de salida.", sfx=(0.4, "boom")),
    dict(f=E_final("vice", 0, "¿LO JUGARÁS EL DÍA 1?"), say="Y ahora, por fin, llega el juego que él intentó destripar. ¿Lo vas a jugar el primer día? Sígueme para más de GTA 6.", sfx=(0.3, "logro")),
]

if __name__ == "__main__":
    S.lanzar("30-el-chico-que-filtro-gta6", "EL CHICO QUE FILTRÓ GTA 6", (255, 90, 200), 10, BEATS,
             [("Arion Kurtaj", "Árion Kúrtai"), ("Fire Stick", "Fáier Estik"), ("YouTube", "Yutub")])
