# -*- coding: utf-8 -*-
"""Vídeo en estilo anime: Hiroo Onoda, el soldado que siguió luchando 29 años porque no creyó que la guerra había terminado.
Datos: Onoda (1922-2014) llegó a Lubang (Filipinas) en diciembre de 1944 con orden de no rendirse; creyó que los folletos
de fin de guerra eran propaganda; con tres compañeros (uno se entregó en 1950, los otros murieron en 1954 y 1972);
durante esos años murieron también vecinos de la isla en sus ataques; en febrero de 1974 lo encontró Norio Suzuki
(que decía buscar «a Onoda, un oso panda y el Yeti»); se negó a rendirse sin orden; su antiguo superior, el mayor
Yoshimi Taniguchi (ya librero), viajó en marzo de 1974 a darle la orden; entregó su espada. Murió en 2014 con 91 años."""
import math, os
import numpy as np
from PIL import Image, ImageDraw

os.environ["PIXEL"] = "0"
import serie as S
import historia as Hm
import anime as AN
from historia import A, W, H, ease, back, texto_grande, pegar, escalar

Hm.PIXEL = False
Hm.CICLO_PEGATINAS = [None]

S.mapa("filipinas", 113, 129, 13, 760)
LUBANG, MANILA = (120.12, 13.82), (120.98, 14.6)
BL, AM, RO, RS, CI = (255, 255, 255), (255, 214, 80), (240, 60, 70), (255, 90, 140), (110, 220, 255)


def personaje(fr, quien, expr, tl, x=W / 2, k=1.5, boca=False, lagrima=False, sudor=False, entra=True, yb=1440):
    cerrado = (tl % 3.1) < 0.12 and expr not in ("sorpresa",)
    abre = boca and int(tl * 8) % 2 == 0
    im = AN.busto(quien, expr, abre, cerrado, lagrima, sudor)
    resp = 1 + 0.008 * math.sin(tl * 2.4)
    u = ease(tl / 0.35) if entra else 1
    im = im.resize((int(im.width * k), int(im.height * k * resp)), Image.LANCZOS)
    pegar(fr, im, x, yb - im.height / 2 + (1 - u) * 300)


def titulo(fr, txt, tl, col=BL, tam=120, y=330, t0=0.0):
    if tl >= t0:
        pegar(fr, escalar(texto_grande(txt, col, tam), max(0.05, back((tl - t0) / 0.3))), W / 2, y)


def sacudida_impacto(fr, tl, t0, dur=0.12, col1=(0, 0, 0), col2=(255, 255, 255)):
    if t0 <= tl < t0 + dur:
        AN.impacto(fr, col1, col2)


# ------------------------------------------------------------- escenas
def e_gancho(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("selva"))
    AN.lineas_foco(fr, tl, (255, 255, 255), cy=760, alfa=170)
    personaje(fr, "onoda_selva", "decidido", tl, k=1.55)
    titulo(fr, "29 AÑOS EN LA SELVA", tl, AM, 120)
    sacudida_impacto(fr, tl, dur * 0.82)


def e_nombre(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("cielo"))
    AN.petalos(fr, tl)
    personaje(fr, "onoda", "serio", tl, k=1.5)
    AN.cartel_nombre(fr, "HIROO ONODA", "OFICIAL DEL EJÉRCITO JAPONÉS", tl - 0.2)


def e_mapa(fr, d, tl, dur):
    fr.alpha_composite(S.fondo("filipinas"))
    m = S.MAPAS["filipinas_obj"]
    S.pin(fr, m, *MANILA, tl, (60, 110, 230), "MANILA")
    S.pin(fr, m, *LUBANG, tl - 0.3, RO, None)
    if tl > 0.6:
        x, y = m.xy(*LUBANG)
        pegar(fr, texto_grande("ISLA DE LUBANG", AM, 64), x - 120, y + 170)
    titulo(fr, "1944: FILIPINAS", tl, BL, 120)
    if tl > dur * 0.45:
        u = back((tl - dur * 0.45) / 0.25)
        sello = texto_grande("ORDEN: NO RENDIRSE JAMÁS", RO, 84).rotate(8, expand=True, resample=Image.BICUBIC)
        pegar(fr, escalar(sello, max(0.05, 1.6 - 0.6 * min(1, u))), W / 2, 1120)


def e_fin_guerra(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("cielo"))
    u = ease(tl / dur)
    x = -200 + (W + 400) * u
    pegar(fr, escalar(A["avion"], 1.2), x, 560)
    rng = np.random.default_rng(2)
    for i in range(14):
        t0 = i * 0.18
        if tl > t0:
            px = -200 + (W + 400) * min(1, t0 / dur) + rng.uniform(-60, 60)
            py = 600 + (tl - t0) * 260
            f = AN.folleto().rotate((tl * 200 + i * 40) % 360, expand=True)
            pegar(fr, escalar(f, 0.6), px + 40 * math.sin(tl * 3 + i), py)
    titulo(fr, "1945: LA GUERRA TERMINA", tl, BL, 110)


def e_trampa(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("selva"))
    AN.trama(fr, 50)
    for i in range(6):
        y = (tl * 180 + i * 260) % 1300 + 300
        pegar(fr, escalar(AN.folleto().rotate(i * 50 + tl * 90, expand=True), 0.55), 150 + i * 160, y - 400)
    AN.lineas_foco(fr, tl, (0, 0, 0), cy=700, alfa=150, n=60)
    personaje(fr, "onoda_selva", "decidido", tl, k=1.55, sudor=True)
    titulo(fr, "¿UNA TRAMPA?", tl, RO, 150, 330, t0=dur * 0.5)
    sacudida_impacto(fr, tl, dur * 0.5)


def e_cuatro(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("atardecer"))
    for i in range(4):
        u = back((tl - i * 0.2) / 0.35)
        if u > 0:
            pegar(fr, escalar(AN.silueta(), 1.0 * u), 200 + i * 230, 1060 - (i % 2) * 30)
    titulo(fr, "ESCONDIDOS EN LA SELVA", tl, AM, 105)


def e_anios(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("atardecer"))
    pasos = [("1950", 3), ("1954", 2), ("1972", 1)]
    i = min(len(pasos) - 1, int(tl / (dur / len(pasos))))
    anio, n = pasos[i]
    for k in range(n):
        pegar(fr, AN.silueta(), W / 2 + (k - (n - 1) / 2) * 230, 1060)
    tc = tl - i * dur / len(pasos)
    pegar(fr, escalar(S.calendario("'" + anio[2:], "AÑO"), 0.55 * max(0.05, back(tc / 0.25))), W / 2, 560)
    AN.lineas_velocidad(fr, tl, (255, 230, 200), 90, 20)
    titulo(fr, "PASAN LOS AÑOS", tl, BL, 110, 300)


def e_solo(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("noche"))
    luz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(luz).ellipse((W / 2 - 330, 520, W / 2 + 330, 1180), fill=(190, 210, 240, 255))
    fr.alpha_composite(luz)
    pegar(fr, escalar(AN.silueta(col=(4, 4, 10)), 1.5), W / 2, 1000)
    AN.lluvia(fr, tl)
    if int(tl * 3) % 5 == 0:
        fr.alpha_composite(Image.new("RGBA", (W, H), (200, 220, 255, 60)))
    titulo(fr, "SOLO", tl, CI, 170, 380)


def e_victimas(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("noche"))
    fr.alpha_composite(Image.new("RGBA", (W, H), (120, 0, 20, 90)))
    AN.trama(fr, 70, col=(0, 0, 0))
    personaje(fr, "onoda_selva", "triste", tl, k=1.45)
    titulo(fr, "TAMBIÉN HUBO VÍCTIMAS", tl, RS, 100)


def e_suzuki(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("cielo"))
    AN.lineas_velocidad(fr, tl, (255, 255, 255), 120, 26)
    personaje(fr, "suzuki", "feliz", tl, k=1.5)
    AN.cartel_nombre(fr, "NORIO SUZUKI", "JOVEN AVENTURERO · 1974", tl - 0.2, col=(60, 140, 240))


def e_tres_cosas(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("cielo"))
    cosas = [(escalar(AN.busto("onoda_selva", "decidido"), 0.42), "ONODA"), (AN.panda(), "UN PANDA"), (AN.yeti(), "EL YETI")]
    for i, (im, et) in enumerate(cosas):
        t0 = 0.6 + i * dur * 0.22
        u = back((tl - t0) / 0.3)
        if u > 0:
            y = 520 + i * 330
            pegar(fr, escalar(im, (0.62 if i else 1.0) * u), 330, y)
            pegar(fr, escalar(texto_grande(f"{i + 1}. {et}", AM if i == 2 else BL, 88), u), 720, y)
    titulo(fr, "BUSCABA 3 COSAS", tl, RS, 110, 300)


def e_encuentro(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("rojo"))
    AN.lineas_foco(fr, tl, (255, 255, 255), cy=820, alfa=140, r0=300)
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(capa).polygon([(W * 0.56, 0), (W, 0), (W, H), (W * 0.44, H)], fill=(30, 20, 60, 255))
    fr.alpha_composite(capa)
    personaje(fr, "onoda_selva", "decidido", tl, x=270, k=1.0, yb=1380)
    personaje(fr, "suzuki", "sorpresa", tl, x=W - 270, k=1.0, yb=1380)
    titulo(fr, "¡LO ENCONTRÓ!", tl, AM, 150, 330, t0=0.15)
    sacudida_impacto(fr, tl, 0.15)


def e_no_rinde(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("rojo"))
    AN.lineas_foco(fr, tl, (0, 0, 0), cy=700, alfa=170)
    personaje(fr, "onoda_selva", "enfado", tl, k=1.6, boca=tl < dur * 0.6)
    titulo(fr, "«SOLO CON UNA ORDEN»", tl, BL, 100, 320)


def e_jefe(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("libreria"))
    personaje(fr, "taniguchi", "serio", tl, k=1.5)
    AN.cartel_nombre(fr, "SU ANTIGUO JEFE", "AHORA ERA LIBRERO", tl - 0.2, col=(200, 150, 60))


def e_espada(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("atardecer"))
    AN.petalos(fr, tl, 34)
    personaje(fr, "onoda_selva", "triste", tl, k=1.5, lagrima=tl > dur * 0.4)
    u = ease((tl - 0.3) / 0.8)
    kt = AN.katana()
    pegar(fr, escalar(kt, 1.25), W / 2 + (1 - u) * -900, 1010)
    titulo(fr, "ENTREGA SU ESPADA", tl, AM, 110)


def e_29(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("atardecer"))
    pegar(fr, escalar(AN.silueta(arma=False), 1.3), W / 2, 1060)
    n = int(29 * ease(tl / (dur * 0.6)))
    pegar(fr, texto_grande(f"{n} AÑOS", AM, 200), W / 2, 560)
    titulo(fr, "LUCHANDO EN UNA GUERRA QUE YA NO EXISTÍA", tl, BL, 60, 320)


def e_final(fr, d, tl, dur):
    fr.alpha_composite(AN.fondo("cielo"))
    AN.petalos(fr, tl, 40)
    personaje(fr, "onoda_viejo", "sonrisa", tl, k=1.5)
    titulo(fr, "SÍGUEME PARA MÁS", tl, RS, 120, 320)


BEATS = [
    dict(f=e_gancho, say="Este soldado siguió luchando en la selva durante veintinueve años… porque no se creyó que la guerra había terminado.", sfx=("82%", "boom")),
    dict(f=e_nombre, say="Se llamaba Hiroo Onoda, y era oficial del ejército japonés."),
    dict(f=e_mapa, say="En 1944 lo mandaron a una isla de Filipinas, Lubang, con una orden: no rendirse jamás.", sfx=("45%", "golpe")),
    dict(f=e_fin_guerra, say="En 1945, la guerra terminó, y desde los aviones lanzaron folletos para anunciarlo."),
    dict(f=e_trampa, say="Pero Onoda pensó que eran una trampa del enemigo.", sfx=("50%", "golpe")),
    dict(f=e_cuatro, say="Así que siguió escondido en la selva, con tres compañeros."),
    dict(f=e_anios, say="Pasaron los años. Uno se entregó, y los otros dos murieron."),
    dict(f=e_solo, say="Onoda se quedó solo… pero siguió cumpliendo su misión."),
    dict(f=e_victimas, say="Y en esos ataques, durante todos esos años, también murieron vecinos de la isla."),
    dict(f=e_suzuki, say="Hasta que, en 1974, un joven aventurero japonés fue a buscarlo: Norio Suzuki."),
    dict(f=e_tres_cosas, say="Decía que buscaba tres cosas: a Onoda, un oso panda… y al Yeti."),
    dict(f=e_encuentro, say="Y lo encontró.", sfx=(0.15, "boom")),
    dict(f=e_no_rinde, say="Pero Onoda se negó a rendirse: solo lo haría si se lo ordenaba su comandante.", sfx=(0.2, "golpe")),
    dict(f=e_jefe, say="Así que buscaron a su antiguo jefe, que ya trabajaba de librero, y lo llevaron a la isla."),
    dict(f=e_espada, say="Le leyó la orden… y Onoda, por fin, entregó su espada.", sfx=("45%", "subida")),
    dict(f=e_29, say="Había pasado veintinueve años luchando en una guerra que ya no existía."),
    dict(f=e_final, say="Murió en 2014, con noventa y un años. ¿Conocías su historia? Sígueme para más.", sfx=(0.3, "logro")),
]

if __name__ == "__main__":
    S.lanzar("29-el-soldado-que-no-se-rindio-anime", "EL SOLDADO QUE NO SE RINDIÓ", (255, 90, 140), 12, BEATS,
             [("Hiroo Onoda", "Jiróo Onóda"), ("Onoda", "Onóda"), ("Lubang", "Lubáng"), ("Norio Suzuki", "Nório Suzúki")])
